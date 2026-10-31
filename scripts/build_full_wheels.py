"""Build platform-specific offline wheels from a reviewed FFmpeg release."""

import argparse
import base64
import hashlib
import json
import stat
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

from portable_ffmpeg.config import _RELEASE_BASE, DOWNLOAD_URLS

_VERSION = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())[
    "project"
]["version"]
_DISTRIBUTION = "portable_ffmpeg_full"
_PLATFORMS = {
    "windows-amd64": "win_amd64",
    "linux-amd64": "manylinux_2_28_x86_64",
    "linux-arm64": "manylinux_2_28_aarch64",
    "osx-amd64": "macosx_12_0_x86_64",
    "osx-arm64": "macosx_12_0_arm64",
}
_LICENSES = ("FFmpeg-GPL-3.0.txt", "THIRD_PARTY_NOTICES.txt", "SOURCE.txt")


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _license_files(archive: Path) -> dict[str, bytes]:
    licenses = {}
    with tarfile.open(archive, "r|xz") as package:
        for member in package:
            if member.name in _LICENSES:
                if member.name in licenses or not member.isfile() or member.size == 0:
                    msg = f"Invalid or duplicate license member: {member.name}"
                    raise ValueError(msg)
                source = package.extractfile(member)
                if source is None:
                    msg = f"Cannot read license member: {member.name}"
                    raise ValueError(msg)
                with source:
                    licenses[member.name] = source.read()
    if set(licenses) != set(_LICENSES):
        msg = f"Archive is missing required license/source notices: {archive.name}"
        raise ValueError(msg)
    return licenses


def _zip_info(name: str, compression: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = compression
    return info


def _record(name: str, digest: bytes, size: int) -> str:
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"{name},sha256={encoded},{size}\n"


def _build_wheel(archive: Path, expected_digest: str, tag: str, output: Path) -> Path:
    licenses = _license_files(archive)
    prefix = f"{_DISTRIBUTION}-{_VERSION}.dist-info"
    metadata = (
        "Metadata-Version: 2.4\n"
        "Name: portable-ffmpeg-full\n"
        f"Version: {_VERSION}\n"
        "Summary: Offline FFmpeg binaries for portable-ffmpeg\n"
        "Requires-Python: >=3.11\n"
        f"Requires-Dist: portable-ffmpeg=={_VERSION}\n"
        "Project-URL: Homepage, https://github.com/mrkbac/portable-ffmpeg\n"
        f"Project-URL: Corresponding Source, {_RELEASE_BASE.replace('/download/', '/tag/')}\n"
        "License-Expression: GPL-3.0-or-later\n"
        + "".join(f"License-File: {name}\n" for name in _LICENSES)
        + "\nFFmpeg binaries are GPLv3-or-later; included components retain their own "
        "license terms and copyright notices. See the bundled licenses and SOURCE.txt.\n"
    )
    files = {
        f"{_DISTRIBUTION}/__init__.py": b'"""Offline binary resources for portable-ffmpeg."""\n',
        f"{prefix}/METADATA": metadata.encode(),
        f"{prefix}/WHEEL": (
            f"Wheel-Version: 1.0\nGenerator: portable-ffmpeg\nRoot-Is-Purelib: false\nTag: {tag}\n"
        ).encode(),
        **{f"{prefix}/licenses/{name}": data for name, data in licenses.items()},
    }
    wheel = output / f"{_DISTRIBUTION}-{_VERSION}-{tag}.whl"
    records = []
    with zipfile.ZipFile(wheel, "x", compression=zipfile.ZIP_STORED) as package:
        resource = f"{_DISTRIBUTION}/ffmpeg.tar.xz"
        digest = hashlib.sha256()
        size = 0
        with (
            archive.open("rb") as source,
            package.open(_zip_info(resource, zipfile.ZIP_STORED), "w") as target,
        ):
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        if digest.hexdigest() != expected_digest:
            msg = f"Archive changed while building wheel: {archive.name}"
            raise ValueError(msg)
        records.append(_record(resource, digest.digest(), size))
        for name, data in files.items():
            package.writestr(_zip_info(name, zipfile.ZIP_DEFLATED), data)
            records.append(_record(name, hashlib.sha256(data).digest(), len(data)))
        package.writestr(
            _zip_info(f"{prefix}/RECORD", zipfile.ZIP_DEFLATED),
            "".join(records) + f"{prefix}/RECORD,,\n",
        )
    return wheel


def build_full_wheels(release: Path, output: Path) -> list[Path]:
    """Build all five offline wheels without changing reviewed input archives."""
    manifest = json.loads((release / "manifest.json").read_text())
    if manifest.get("publication_ready") is not True:
        msg = "Release must be source-complete and marked publication_ready"
        raise ValueError(msg)
    entries = manifest["artifacts"]
    platforms = {entry["platform"] for entry in entries}
    if len(entries) != len(_PLATFORMS) or platforms != set(_PLATFORMS):
        msg = "Release must contain exactly the five supported platform archives"
        raise ValueError(msg)
    client_builds = {
        f"{system.value}-{architecture.value}": config
        for system, architectures in DOWNLOAD_URLS.items()
        for architecture, config in architectures.items()
    }
    inputs = []
    targets = []
    for entry in entries:
        filename = f"ffmpeg-{manifest['ffmpeg_version']}-{entry['platform']}.tar.xz"
        if entry["filename"] != filename or Path(filename).name != filename or "\\" in filename:
            msg = f"Unexpected release archive filename: {entry['filename']}"
            raise ValueError(msg)
        config = client_builds[entry["platform"]]
        if (
            filename != config.url.rsplit("/", 1)[-1]
            or entry["sha256"] != config.sha256
            or entry.get("binary_sha256") != config.binary_sha256
        ):
            msg = f"Release does not match portable-ffmpeg client pins: {entry['platform']}"
            raise ValueError(msg)
        archive = release / filename
        if not archive.is_file() or archive.is_symlink() or _digest(archive) != entry["sha256"]:
            msg = f"Archive checksum mismatch or invalid input: {filename}"
            raise ValueError(msg)
        tag = f"py3-none-{_PLATFORMS[entry['platform']]}"
        target = output / f"{_DISTRIBUTION}-{_VERSION}-{tag}.whl"
        if target.exists() or target.is_symlink():
            msg = f"Output already exists: {target}"
            raise FileExistsError(msg)
        inputs.append((archive, entry["sha256"], tag))
        targets.append(target)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output, prefix=".full-wheels-") as tmp_dir:
        staging = Path(tmp_dir)
        wheels = [_build_wheel(archive, digest, tag, staging) for archive, digest, tag in inputs]
        for wheel, target in zip(wheels, targets, strict=True):
            wheel.rename(target)
    for target in targets:
        print(f"Built {target} ({target.stat().st_size} bytes)")
    return targets


def main() -> None:
    """Build offline wheels from the requested reviewed release directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_full_wheels(args.release, args.output)


if __name__ == "__main__":
    main()
