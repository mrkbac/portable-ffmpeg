"""Verify prepared assets and upload a draft GitHub release; never publish it live."""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from portable_ffmpeg.config import _RELEASE_BASE, DOWNLOAD_URLS
from scripts.prepare_release import sha256

_REPOSITORY = "mrkbac/portable-ffmpeg"
_SOURCE_REVIEW = Path(__file__).resolve().parents[1] / "licenses" / "release-sources.json"


def _verify_inventory(directory: Path) -> dict[str, str]:
    """Verify every upload against the complete checksum inventory."""
    expected = {}
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        if not re.fullmatch("[0-9a-f]{64}", digest) or Path(name).name != name or name in expected:
            msg = f"Invalid or duplicate checksum entry: {name}"
            raise ValueError(msg)
        expected[name] = digest
    actual = {path.name for path in directory.iterdir()}
    if actual != set(expected) | {"SHA256SUMS"}:
        msg = "Release directory and checksum inventory differ"
        raise ValueError(msg)
    for name, digest in expected.items():
        path = directory / name
        if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size < 2 * 1024**3:
            msg = f"Invalid GitHub release asset: {name}"
            raise ValueError(msg)
        if sha256(path) != digest:
            msg = f"Release asset checksum mismatch: {name}"
            raise ValueError(msg)
    return expected


def _verify_source_pins(expected: dict[str, str]) -> str:
    """Bind source assets and review metadata to the version-controlled source review."""
    reviewed_source_digest = sha256(_SOURCE_REVIEW)
    if expected["SOURCE_MANIFEST.json"] != reviewed_source_digest:
        msg = "Release source review differs from the version-controlled reviewed inputs"
        raise ValueError(msg)
    for source in json.loads(_SOURCE_REVIEW.read_text())["files"]:
        if expected.get(source["filename"]) != source["sha256"]:
            msg = f"Reviewed source or notice pin differs: {source['filename']}"
            raise ValueError(msg)
    return reviewed_source_digest


def validate_release(directory: Path) -> list[Path]:
    """Require reviewed sources, complete checksums, and matching installed-client pins."""
    manifest = json.loads((directory / "manifest.json").read_text())
    sources = json.loads((directory / "SOURCE_MANIFEST.json").read_text())
    tag = _RELEASE_BASE.rsplit("/", 1)[1]
    if manifest.get("publication_ready") is not True or sources.get("review_complete") is not True:
        msg = "Source and license review is incomplete"
        raise ValueError(msg)
    if manifest["release_tag"] != tag:
        msg = "Release tag differs from the installed client's pinned release"
        raise ValueError(msg)
    expected = _verify_inventory(directory)
    reviewed_source_digest = _verify_source_pins(expected)
    platforms = {
        f"{system.value}-{architecture.value}": config
        for system, architectures in DOWNLOAD_URLS.items()
        for architecture, config in architectures.items()
    }
    entries = {entry["platform"]: entry for entry in manifest["artifacts"]}
    if set(entries) != set(platforms) or len(entries) != len(manifest["artifacts"]):
        msg = "Release must contain every supported platform exactly once"
        raise ValueError(msg)
    for platform, config in platforms.items():
        entry = entries[platform]
        if (
            entry["sha256"] != config.sha256
            or expected.get(entry["filename"]) != config.sha256
            or entry["filename"] != config.url.rsplit("/", 1)[1]
        ):
            msg = f"Client archive pins differ for {platform}"
            raise ValueError(msg)
        if entry["source_manifest_sha256"] != reviewed_source_digest:
            msg = f"Archive source-review identity differs for {platform}"
            raise ValueError(msg)
        if (
            entry["binary_sha256"] != config.binary_sha256
            or sources["platforms"][platform]["binary_sha256"] != config.binary_sha256
        ):
            msg = f"Client executable pins differ for {platform}"
            raise ValueError(msg)
        review = sources["platforms"][platform]
        if not review["source_files"] or not {
            *review["source_files"],
            review["notice_file"],
        } <= set(expected):
            msg = f"Missing source or notice assets for {platform}"
            raise ValueError(msg)
    return sorted(directory.iterdir())


def create_draft(directory: Path) -> None:
    """Upload verified binaries and corresponding sources into a new draft release."""
    assets = validate_release(directory)
    tag = _RELEASE_BASE.rsplit("/", 1)[1]
    gh = shutil.which("gh")
    if gh is None:
        msg = "The GitHub CLI (gh) is required to upload a draft"
        raise FileNotFoundError(msg)
    git = shutil.which("git")
    if git is None:
        msg = "Git is required to identify the reviewed release commit"
        raise FileNotFoundError(msg)
    repository = Path(__file__).resolve().parents[1]
    status = subprocess.check_output(
        [git, "status", "--porcelain", "--untracked-files=all"], cwd=repository, text=True
    )
    if status.strip():
        msg = "Commit all tracked and untracked changes before creating the release draft"
        raise ValueError(msg)
    revision = subprocess.check_output(
        [git, "rev-parse", "--verify", "HEAD^{commit}"], cwd=repository, text=True
    ).strip()
    if not re.fullmatch("[0-9a-f]{40}", revision):
        msg = "Git did not return a valid release commit"
        raise ValueError(msg)
    with tempfile.TemporaryDirectory() as temporary:
        notes = Path(temporary) / "notes.md"
        notes.write_text(
            "FFmpeg 9.0.2 GPL builds for Windows x86-64, Linux x86-64/ARM64, "
            "and macOS Intel/Apple Silicon.\n\n"
            "Each binary TAR.XZ has both executables at its root, license notices, "
            "source pointers, and archive/executable SHA-256 provenance. XZ decoding "
            "needs approximately 256 MiB of dictionary memory.\n\n"
            "Complete corresponding sources, dependency sources, build recipes, "
            "and notices accompany the binaries. SOURCE_MANIFEST.json records "
            "source identities and review evidence; SHA256SUMS covers all assets.\n\n"
            "Review this draft before publishing. Publish these binary/source assets "
            "before releasing portable-ffmpeg 0.5.0 or portable-ffmpeg-full 0.5.0.\n"
        )
        subprocess.run(
            [
                gh,
                "release",
                "create",
                tag,
                "--repo",
                _REPOSITORY,
                "--draft",
                "--target",
                revision,
                "--title",
                "FFmpeg 9.0.2 GPL binaries and corresponding source",
                "--notes-file",
                str(notes),
                *map(str, assets),
            ],
            check=True,
        )


def main() -> None:
    """Validate a prepared release, or upload it as a draft when explicitly requested."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--draft", action="store_true", help="Upload a new draft, without publishing"
    )
    args = parser.parse_args()
    if args.draft:
        create_draft(args.directory)
    else:
        assets = validate_release(args.directory)
        print(f"Verified {len(assets)} release assets; nothing uploaded")


if __name__ == "__main__":
    main()
