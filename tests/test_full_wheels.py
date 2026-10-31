"""Verify offline wheels using small, reviewed release fixtures."""

import base64
import csv
import hashlib
import io
import json
import lzma
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

import pytest

from portable_ffmpeg.downloaders import FFmpegDownload
from portable_ffmpeg.enums import Architectures, OperatingSystems
from scripts import build_full_wheels as full_wheels
from scripts.build_full_wheels import _PLATFORMS, _VERSION, build_full_wheels


@pytest.fixture
def release(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create one tiny source-complete TAR.XZ for each supported platform."""
    directory = tmp_path / "release"
    directory.mkdir()
    artifacts = []
    client_builds: dict[OperatingSystems, dict[Architectures, FFmpegDownload]] = {}
    for platform in _PLATFORMS:
        suffix = ".exe" if platform.startswith("windows") else ""
        archive = directory / f"ffmpeg-9.0.2-{platform}.tar.xz"
        with tarfile.open(archive, "w:xz") as package:
            for name, data in {
                f"ffmpeg{suffix}": b"encoder",
                f"ffprobe{suffix}": b"probe",
                "FFmpeg-GPL-3.0.txt": b"GNU GENERAL PUBLIC LICENSE Version 3",
                "THIRD_PARTY_NOTICES.txt": b"Component license and copyright notices",
                "SOURCE.txt": b"https://example.com/corresponding-source.zip",
            }.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                package.addfile(member, io.BytesIO(data))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        binary_hashes = {
            f"ffmpeg{suffix}": hashlib.sha256(b"encoder").hexdigest(),
            f"ffprobe{suffix}": hashlib.sha256(b"probe").hexdigest(),
        }
        artifacts.append(
            {
                "platform": platform,
                "filename": archive.name,
                "sha256": digest,
                "binary_sha256": binary_hashes,
            }
        )
        system, architecture = platform.split("-")
        client_builds.setdefault(OperatingSystems(system), {})[Architectures(architecture)] = (
            FFmpegDownload(
                f"https://example.com/{archive.name}",
                digest,
                binary_hashes,
                ffmpeg_name=f"ffmpeg{suffix}",
                ffprobe_name=f"ffprobe{suffix}",
            )
        )
    (directory / "manifest.json").write_text(
        json.dumps({"publication_ready": True, "ffmpeg_version": "9.0.2", "artifacts": artifacts})
    )
    monkeypatch.setattr(full_wheels, "DOWNLOAD_URLS", client_builds)
    return directory


def test_offline_wheels(release: Path, tmp_path: Path) -> None:
    """Preserve the XZ payload, tags, dependency, notices, and every RECORD hash."""
    output = tmp_path / "python"
    output.mkdir()
    base_wheel = output / "portable_ffmpeg-0.5.0-py3-none-any.whl"
    base_wheel.write_bytes(b"existing base wheel")
    wheels = build_full_wheels(release, output)
    assert len(wheels) == 5
    assert base_wheel.read_bytes() == b"existing base wheel"
    for platform, platform_tag in _PLATFORMS.items():
        wheel = output / f"portable_ffmpeg_full-{_VERSION}-py3-none-{platform_tag}.whl"
        assert wheel in wheels
        prefix = f"portable_ffmpeg_full-{_VERSION}.dist-info"
        with zipfile.ZipFile(wheel) as package:
            resource = "portable_ffmpeg_full/ffmpeg.tar.xz"
            assert (
                package.read(resource) == (release / f"ffmpeg-9.0.2-{platform}.tar.xz").read_bytes()
            )
            assert package.getinfo(resource).compress_type == zipfile.ZIP_STORED
            assert (
                package.getinfo(f"{prefix}/licenses/THIRD_PARTY_NOTICES.txt").compress_type
                == zipfile.ZIP_DEFLATED
            )
            assert not any(name.startswith("portable_ffmpeg/") for name in package.namelist())
            assert b"import " not in package.read("portable_ffmpeg_full/__init__.py")
            metadata = BytesParser().parsebytes(package.read(f"{prefix}/METADATA"))
            assert metadata["Name"] == "portable-ffmpeg-full"
            assert metadata["Version"] == _VERSION
            assert metadata["Requires-Python"] == ">=3.11"
            assert metadata["Requires-Dist"] == f"portable-ffmpeg=={_VERSION}"
            assert metadata["License-Expression"] == "GPL-3.0-or-later"
            assert "Root-Is-Purelib: false" in package.read(f"{prefix}/WHEEL").decode()
            assert f"Tag: py3-none-{platform_tag}" in package.read(f"{prefix}/WHEEL").decode()
            assert package.read(f"{prefix}/licenses/SOURCE.txt").startswith(b"https://")
            assert b"GNU GENERAL PUBLIC LICENSE" in package.read(
                f"{prefix}/licenses/FFmpeg-GPL-3.0.txt"
            )
            records = list(csv.reader(io.StringIO(package.read(f"{prefix}/RECORD").decode())))
            assert {record[0] for record in records} == set(package.namelist())
            for name, digest, size in records:
                if name.endswith("/RECORD"):
                    assert (digest, size) == ("", "")
                else:
                    data = package.read(name)
                    encoded = (
                        base64.urlsafe_b64encode(hashlib.sha256(data).digest())
                        .rstrip(b"=")
                        .decode()
                    )
                    assert digest == f"sha256={encoded}"
                    assert int(size) == len(data)


def test_refuse_overwrite(release: Path, tmp_path: Path) -> None:
    """An existing full wheel is never replaced."""
    output = tmp_path / "python"
    output.mkdir()
    sentinel = output / f"portable_ffmpeg_full-{_VERSION}-py3-none-win_amd64.whl"
    sentinel.write_bytes(b"keep")
    with pytest.raises(FileExistsError, match="Output already exists"):
        build_full_wheels(release, output)
    assert sentinel.read_bytes() == b"keep"
    assert list(output.iterdir()) == [sentinel]


def test_reject_modified_archive(release: Path, tmp_path: Path) -> None:
    """Tampered input cannot enter a full wheel or leave partial output."""
    archive = next(release.glob("*.tar.xz"))
    archive.write_bytes(archive.read_bytes() + b"tampering")
    output = tmp_path / "python"
    with pytest.raises(ValueError, match="Archive checksum mismatch"):
        build_full_wheels(release, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "failure",
    ["not-reviewed", "missing-platform", "duplicate-platform", "unsafe-path", "unsafe-version"],
)
def test_reject_invalid_manifest(release: Path, tmp_path: Path, failure: str) -> None:
    """Require review, exactly five distinct platforms, and canonical archive names."""
    path = release / "manifest.json"
    manifest = json.loads(path.read_text())
    if failure == "not-reviewed":
        manifest["publication_ready"] = False
    elif failure == "missing-platform":
        manifest["artifacts"].pop()
    elif failure == "duplicate-platform":
        manifest["artifacts"][-1] = manifest["artifacts"][0]
    elif failure == "unsafe-path":
        manifest["artifacts"][0]["filename"] = "../outside.tar.xz"
    else:
        manifest["ffmpeg_version"] = "../../outside"
        first = manifest["artifacts"][0]
        first["filename"] = f"ffmpeg-../../outside-{first['platform']}.tar.xz"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        build_full_wheels(release, tmp_path / "python")


def test_missing_license_leaves_no_partial_wheels(release: Path, tmp_path: Path) -> None:
    """A later platform missing notices cannot publish earlier staged wheels."""
    path = release / "manifest.json"
    manifest = json.loads(path.read_text())
    last = manifest["artifacts"][-1]
    archive = release / last["filename"]
    with tarfile.open(archive, "w:xz") as package:
        member = tarfile.TarInfo("ffmpeg")
        member.size = 7
        package.addfile(member, io.BytesIO(b"encoder"))
    last["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    system, architecture = last["platform"].split("-")
    full_wheels.DOWNLOAD_URLS[OperatingSystems(system)][Architectures(architecture)].sha256 = last[
        "sha256"
    ]
    path.write_text(json.dumps(manifest))
    output = tmp_path / "python"
    with pytest.raises(ValueError, match="missing required license"):
        build_full_wheels(release, output)
    assert list(output.iterdir()) == []


@pytest.mark.parametrize("change", ["ffmpeg-version", "archive-digest", "binary-digest"])
def test_release_must_match_client_pins(release: Path, tmp_path: Path, change: str) -> None:
    """An editable manifest cannot bind an incompatible payload to the base package version."""
    path = release / "manifest.json"
    manifest = json.loads(path.read_text())
    if change == "ffmpeg-version":
        manifest["ffmpeg_version"] = "10.0.0"
        for entry in manifest["artifacts"]:
            old = release / entry["filename"]
            entry["filename"] = entry["filename"].replace("9.0.2", "10.0.0")
            old.rename(release / entry["filename"])
    elif change == "archive-digest":
        entry = manifest["artifacts"][0]
        archive = release / entry["filename"]
        archive.write_bytes(lzma.compress(lzma.decompress(archive.read_bytes()), preset=0))
        entry["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    else:
        entry = manifest["artifacts"][0]
        entry["binary_sha256"]["ffmpeg.exe"] = "0" * 64
    path.write_text(json.dumps(manifest))
    output = tmp_path / "python"
    with pytest.raises(ValueError, match="does not match portable-ffmpeg client pins"):
        build_full_wheels(release, output)
    assert not output.exists()
