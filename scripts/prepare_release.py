"""Prepare source-complete FFmpeg release assets without publishing them."""

import argparse
import hashlib
import json
import lzma
import shutil
import tarfile
import tempfile
from dataclasses import asdict
from pathlib import Path

from portable_ffmpeg.config import _RELEASE_BASE
from scripts.upstream import DOWNLOAD_URLS

_LICENSE = Path(__file__).resolve().parents[1] / "licenses" / "FFmpeg-GPL-3.0.txt"
_VERSION = "9.0.2"
_XZ_DICTIONARY = 256 * 1024 * 1024
_ASSET_LIMIT = 2 * 1024**3


def sha256(path: Path) -> str:
    """Hash a file without reading it all into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _write_tar_xz(path: Path, files: list[Path]) -> None:
    """Write one solid XZ stream, with fixed TAR metadata and a 256 MiB dictionary."""
    filters = [{"id": lzma.FILTER_LZMA2, "preset": 6, "dict_size": _XZ_DICTIONARY}]
    with (
        lzma.open(path, "xb", format=lzma.FORMAT_XZ, filters=filters) as compressed,
        tarfile.open(fileobj=compressed, mode="w|", format=tarfile.USTAR_FORMAT) as package,
    ):
        for source_path in files:
            info = tarfile.TarInfo(source_path.name)
            info.mode = 0o755 if source_path.name.startswith(("ffmpeg", "ffprobe")) else 0o644
            info.size = source_path.stat().st_size
            with source_path.open("rb") as source:
                package.addfile(info, source)


def _input_file(directory: Path, name: str) -> Path:
    if name != Path(name).name or name in {".", ".."}:
        msg = f"Source manifest contains an unsafe filename: {name}"
        raise ValueError(msg)
    path = directory / name
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size < _ASSET_LIMIT:
        msg = f"Source asset must be a non-empty regular file smaller than 2 GiB: {name}"
        raise ValueError(msg)
    return path


def _copy_source_files(sources: Path, release: Path, files: list[dict[str, str]]) -> None:
    """Keep reviewed source assets distinct and verify the exact copied bytes."""
    names = [entry["filename"] for entry in files]
    if len(names) != len(set(names)) or set(names) & {
        "manifest.json",
        "SHA256SUMS",
        "SOURCE_MANIFEST.json",
    }:
        msg = "Source assets contain duplicate or reserved release filenames"
        raise ValueError(msg)
    for entry in files:
        path = _input_file(sources, entry["filename"])
        target = release / path.name
        shutil.copyfile(path, target)
        if sha256(target) != entry["sha256"]:
            msg = f"Source or notice checksum mismatch: {path.name}"
            raise ValueError(msg)


def prepare_release(output: Path, sources: Path) -> None:
    """Verify sources and binaries, then atomically prepare all assets in a new directory."""
    if output.exists():
        msg = f"Output already exists: {output}"
        raise FileExistsError(msg)
    source_manifest = json.loads((sources / "SOURCE_MANIFEST.json").read_text())
    if (
        source_manifest.get("review_complete") is not True
        or source_manifest.get("ffmpeg_version") != _VERSION
    ):
        msg = "Corresponding source and license review must be complete for this FFmpeg version"
        raise ValueError(msg)
    output.parent.mkdir(parents=True, exist_ok=True)
    artifacts = []
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".ffmpeg-release-") as tmp_dir:
        staging = Path(tmp_dir)
        release = staging / "release"
        release.mkdir()
        _copy_source_files(sources, release, source_manifest["files"])
        shutil.copyfile(sources / "SOURCE_MANIFEST.json", release / "SOURCE_MANIFEST.json")
        for system, architectures in DOWNLOAD_URLS.items():
            for architecture, config in architectures.items():
                platform = f"{system.value}-{architecture.value}"
                review = source_manifest["platforms"][platform]
                source_files = review["source_files"]
                if not source_files or any(
                    name not in {entry["filename"] for entry in source_manifest["files"]}
                    for name in [*source_files, review["notice_file"]]
                ):
                    msg = f"Missing corresponding-source or notice assets for {platform}"
                    raise ValueError(msg)
                binaries = staging / platform
                binaries.mkdir()
                config.download_files(binaries)
                executables = [binaries / config.ffmpeg_name, binaries / config.ffprobe_name]
                hashes = {path.name: sha256(path) for path in executables}
                if hashes != review["binary_sha256"]:
                    msg = f"Source review does not match the actual {platform} executables"
                    raise ValueError(msg)
                provenance = {
                    "ffmpeg_version": _VERSION,
                    "platform": platform,
                    "upstream": asdict(config),
                    "binary_sha256": hashes,
                    "source_files": source_files,
                    "source_manifest_sha256": sha256(release / "SOURCE_MANIFEST.json"),
                }
                metadata = binaries / "PROVENANCE.json"
                metadata.write_text(json.dumps(provenance, indent=2) + "\n")
                source_pointer = binaries / "SOURCE.txt"
                source_pointer.write_text(
                    "FFmpeg reports GNU GPL version 3 or later. Included components retain "
                    "their own license and copyright notices in THIRD_PARTY_NOTICES.txt.\n\n"
                    "Complete corresponding source, dependency sources, patches, build scripts "
                    "and source identities are supplied with this release:\n"
                    + "\n".join(f"{_RELEASE_BASE}/{name}" for name in source_files)
                    + f"\n{_RELEASE_BASE}/SOURCE_MANIFEST.json\n"
                )
                notices = binaries / "THIRD_PARTY_NOTICES.txt"
                shutil.copyfile(release / review["notice_file"], notices)
                filename = f"ffmpeg-{_VERSION}-{platform}.tar.xz"
                archive = release / filename
                print(
                    f"Compressing {platform} with one 256 MiB-dictionary XZ stream...", flush=True
                )
                _write_tar_xz(archive, [*executables, _LICENSE, notices, source_pointer, metadata])
                artifacts.append({"filename": filename, "sha256": sha256(archive), **provenance})
        manifest = {
            "ffmpeg_version": _VERSION,
            "release_tag": _RELEASE_BASE.rsplit("/", 1)[1],
            "publication_ready": True,
            "compression": {"format": "tar.xz", "lzma2_dictionary_bytes": _XZ_DICTIONARY},
            "artifacts": artifacts,
        }
        (release / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (release / "SHA256SUMS").write_text(
            "".join(f"{sha256(path)}  {path.name}\n" for path in sorted(release.iterdir()))
        )
        release.rename(output)
    print(f"Prepared source-complete assets in {output}; nothing has been published")


def main() -> None:
    """Prepare assets from reviewed source bundles in the requested new directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New release output directory")
    parser.add_argument("sources", type=Path, help="Reviewed sources with SOURCE_MANIFEST.json")
    args = parser.parse_args()
    prepare_release(args.output, args.sources)


if __name__ == "__main__":
    main()
