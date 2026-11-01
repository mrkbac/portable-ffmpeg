"""Check draft-only uploads and publication integrity guards."""

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from portable_ffmpeg.downloaders import FFmpegDownload
from portable_ffmpeg.enums import Architectures, OperatingSystems
from scripts import publish_release
from scripts.prepare_release import sha256

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def refresh_inventory(directory: Path) -> None:
    """Regenerate the transport inventory without changing reviewed source or client pins."""
    (directory / "SHA256SUMS").write_text(
        "".join(
            f"{sha256(path)}  {path.name}\n"
            for path in sorted(directory.iterdir())
            if path.name != "SHA256SUMS"
        )
    )


@pytest.fixture
def clean_git(mocker: "MockerFixture") -> MagicMock:
    """Supply a clean checkout and a specific immutable commit without invoking Git."""
    mocker.patch(
        "scripts.publish_release.shutil.which", side_effect=lambda name: f"/usr/bin/{name}"
    )
    check_output = MagicMock(side_effect=["", "a" * 40 + "\n"])
    mocker.patch("scripts.publish_release.subprocess.check_output", new=check_output)
    return check_output


@pytest.fixture
def release(tmp_path: Path, mocker: "MockerFixture") -> Path:
    """Provide a tiny reviewed release with matching client pins."""
    directory = tmp_path / "release"
    directory.mkdir()
    filename = "ffmpeg-9.0.2-linux-amd64.tar.xz"
    (directory / filename).write_bytes(b"test payload")
    (directory / "sources.zip").write_bytes(b"test source fixture")
    (directory / "notices.txt").write_text("Copyright fixture")
    hashes = {"ffmpeg": "a" * 64, "ffprobe": "b" * 64}
    digest = sha256(directory / filename)
    source_manifest = {
        "review_complete": True,
        "files": [
            {"filename": name, "sha256": sha256(directory / name)}
            for name in ("sources.zip", "notices.txt")
        ],
        "platforms": {
            "linux-amd64": {
                "binary_sha256": hashes,
                "source_files": ["sources.zip"],
                "notice_file": "notices.txt",
            }
        },
    }
    review_path = tmp_path / "reviewed-source.json"
    review_path.write_text(json.dumps(source_manifest))
    mocker.patch.object(publish_release, "_SOURCE_REVIEW", review_path)
    manifest = {
        "publication_ready": True,
        "release_tag": "ffmpeg-9.0.2-1",
        "artifacts": [
            {
                "platform": "linux-amd64",
                "filename": filename,
                "sha256": digest,
                "binary_sha256": hashes,
                "source_manifest_sha256": sha256(review_path),
            }
        ],
    }
    (directory / "SOURCE_MANIFEST.json").write_text(json.dumps(source_manifest))
    (directory / "manifest.json").write_text(json.dumps(manifest))
    refresh_inventory(directory)
    base = "https://github.com/mrkbac/portable-ffmpeg/releases/download/ffmpeg-9.0.2-1"
    config = FFmpegDownload(
        f"{base}/{filename}",
        digest,
        hashes,
    )
    mocker.patch.object(
        publish_release, "DOWNLOAD_URLS", {OperatingSystems.LINUX: {Architectures.AMD64: config}}
    )
    return directory


def test_draft_upload_is_explicit(
    release: Path, mocker: "MockerFixture", clean_git: MagicMock
) -> None:
    """Verification does not upload; the separate upload command always creates a draft."""
    run = mocker.patch("scripts.publish_release.subprocess.run")
    assert publish_release.validate_release(release) == sorted(release.iterdir())
    run.assert_not_called()
    publish_release.create_draft(release)
    command = run.call_args.args[0]
    assert command[:3] == ["/usr/bin/gh", "release", "create"]
    assert "--draft" in command
    assert command[command.index("--target") + 1] == "a" * 40
    assert clean_git.call_args_list[0].args[0] == [
        "/usr/bin/git",
        "status",
        "--porcelain",
        "--untracked-files=all",
    ]
    assert clean_git.call_args_list[1].args[0] == [
        "/usr/bin/git",
        "rev-parse",
        "--verify",
        "HEAD^{commit}",
    ]
    assert run.call_args.kwargs["check"] is True
    assert str(release / "sources.zip") in command
    assert str(release / "notices.txt") in command


@pytest.mark.parametrize("problem", ["damaged", "extra", "missing", "unreviewed", "client-pin"])
def test_invalid_release_cannot_upload(
    release: Path, mocker: "MockerFixture", problem: str
) -> None:
    """Reject byte changes, incomplete inventory, stale pins, and missing source review."""
    run = mocker.patch("scripts.publish_release.subprocess.run")
    if problem == "damaged":
        (release / "sources.zip").write_bytes(b"changed source")
    elif problem == "extra":
        (release / "unlisted").write_bytes(b"unexpected")
    elif problem == "missing":
        (release / "sources.zip").unlink()
    elif problem == "unreviewed":
        path = release / "SOURCE_MANIFEST.json"
        data = json.loads(path.read_text())
        data["review_complete"] = False
        path.write_text(json.dumps(data))
    else:
        publish_release.DOWNLOAD_URLS[OperatingSystems.LINUX][Architectures.AMD64].sha256 = "0" * 64
    with pytest.raises(ValueError):
        publish_release.create_draft(release)
    run.assert_not_called()


@pytest.mark.parametrize("changed", ["binary", "source", "review", "archive-review", "binary-pin"])
def test_recomputed_inventory_cannot_authorize_changed_assets(
    release: Path, mocker: "MockerFixture", changed: str
) -> None:
    """Transport checksums cannot replace reviewed input identities or client pins."""
    run = mocker.patch("scripts.publish_release.subprocess.run")
    if changed == "binary":
        (release / "ffmpeg-9.0.2-linux-amd64.tar.xz").write_bytes(b"changed executable payload")
    elif changed == "source":
        (release / "sources.zip").write_bytes(b"changed dependency source")
    elif changed == "review":
        path = release / "SOURCE_MANIFEST.json"
        manifest = json.loads(path.read_text())
        manifest["unreviewed_change"] = True
        path.write_text(json.dumps(manifest))
    else:
        path = release / "manifest.json"
        manifest = json.loads(path.read_text())
        entry = manifest["artifacts"][0]
        if changed == "archive-review":
            entry["source_manifest_sha256"] = "0" * 64
        else:
            entry["binary_sha256"]["ffmpeg"] = "0" * 64
        path.write_text(json.dumps(manifest))
    refresh_inventory(release)
    with pytest.raises(ValueError):
        publish_release.create_draft(release)
    run.assert_not_called()


@pytest.mark.parametrize("status", [" M scripts/publish_release.py\n", "?? untracked.py\n"])
def test_dirty_checkout_cannot_create_draft(
    release: Path, mocker: "MockerFixture", clean_git: MagicMock, status: str
) -> None:
    """Tracked and untracked changes must be committed before selecting the release target."""
    clean_git.side_effect = [status]
    run = mocker.patch("scripts.publish_release.subprocess.run")
    with pytest.raises(ValueError, match="Commit all tracked and untracked changes"):
        publish_release.create_draft(release)
    clean_git.assert_called_once()
    run.assert_not_called()


def test_invalid_git_commit_cannot_create_draft(
    release: Path, mocker: "MockerFixture", clean_git: MagicMock
) -> None:
    """Do not fall back to the default branch when an exact target commit is unavailable."""
    clean_git.side_effect = ["", "unexpected revision"]
    run = mocker.patch("scripts.publish_release.subprocess.run")
    with pytest.raises(ValueError, match="valid release commit"):
        publish_release.create_draft(release)
    run.assert_not_called()
