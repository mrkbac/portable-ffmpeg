"""Verify the single release-TAR.XZ contract without network access."""

import hashlib
import io
import os
import tarfile
import urllib.request
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from portable_ffmpeg.downloaders import _DOWNLOAD_USER_AGENT, FFmpegDownload, _download_file

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class Response(io.BytesIO):
    """An HTTP response with optional length metadata."""

    def __init__(self, data: bytes, headers: dict[str, str]) -> None:
        """Initialize the response body and headers."""
        super().__init__(data)
        self.headers = headers


def make_tar(path: Path, entries: list[tuple[str, bytes]]) -> FFmpegDownload:
    """Create an archive fixture with pinned archive and executable bytes."""
    with tarfile.open(path, "w:xz") as package:
        for name, data in entries:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            package.addfile(info, io.BytesIO(data))
    files = dict(entries)
    suffix = ".exe" if "ffmpeg.exe" in files else ""
    names = (f"ffmpeg{suffix}", f"ffprobe{suffix}")
    hashes = {name: hashlib.sha256(files.get(name, b"expected")).hexdigest() for name in names}
    return FFmpegDownload(
        path.as_uri(), hashlib.sha256(path.read_bytes()).hexdigest(), hashes, *names
    )


def test_streamed_download(tmp_path: Path, mocker: "MockerFixture") -> None:
    """Preserve streamed writes, the User-Agent, and bounded socket waits."""
    urlopen = mocker.patch("portable_ffmpeg.downloaders.urllib.request.urlopen")
    mocker.patch("portable_ffmpeg.downloaders._DOWNLOAD_CHUNK_SIZE", 2)
    urlopen.return_value = Response(b"abcdef", {"Content-Length": "6"})
    output = tmp_path / "archive"
    _download_file(
        "https://example.com/archive.tar.xz", output, hashlib.sha256(b"abcdef").hexdigest()
    )
    assert output.read_bytes() == b"abcdef"
    request = urlopen.call_args.args[0]
    assert isinstance(request, urllib.request.Request)
    assert request.get_header("User-agent") == _DOWNLOAD_USER_AGENT
    assert urlopen.call_args.kwargs["timeout"] == 30


@pytest.mark.parametrize("headers", [{}, {"Content-Length": "3"}])
def test_checksum_is_required(
    tmp_path: Path, mocker: "MockerFixture", headers: dict[str, str]
) -> None:
    """Reject modified downloads whether or not the server supplies a length."""
    mocker.patch(
        "portable_ffmpeg.downloaders.urllib.request.urlopen", return_value=Response(b"bad", headers)
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _download_file("https://example.com/archive.tar.xz", tmp_path / "archive", "0" * 64)


def test_truncated_response(tmp_path: Path, mocker: "MockerFixture") -> None:
    """An early EOF must not be treated as a complete archive."""
    mocker.patch(
        "portable_ffmpeg.downloaders.urllib.request.urlopen",
        return_value=Response(b"short", {"Content-Length": "100"}),
    )
    with pytest.raises(ValueError, match="Incomplete download"):
        _download_file("https://example.com/archive.tar.xz", tmp_path / "archive", "0" * 64)


def test_network_error(tmp_path: Path, mocker: "MockerFixture") -> None:
    """Preserve network errors rather than creating a successful-looking download."""
    mocker.patch(
        "portable_ffmpeg.downloaders.urllib.request.urlopen", side_effect=ConnectionError("offline")
    )
    with pytest.raises(ConnectionError, match="offline"):
        _download_file("https://example.com/archive.tar.xz", tmp_path / "archive", "0" * 64)


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_extract_only_root_regular_files(
    tmp_path: Path, mocker: "MockerFixture", platform: str
) -> None:
    """Retain root notices without copying nested or unsafe paths."""
    suffix = ".exe" if platform == "win32" else ""
    files = {f"ffmpeg{suffix}": b"encoder", f"ffprobe{suffix}": b"probe"}
    entries = [
        *files.items(),
        ("../outside", b"ignored"),
        ("bin/ffmpeg", b"ignored"),
        ("..\\outside", b"ignored"),
        ("LICENSE.txt", b"notice"),
    ]
    config = make_tar(tmp_path / "release.tar.xz", entries)
    output = tmp_path / "output"
    output.mkdir()
    mocker.patch("portable_ffmpeg.downloaders.sys.platform", platform)
    config.download_files(output)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        **files,
        "LICENSE.txt": b"notice",
    }
    assert not (tmp_path / "outside").exists()
    if platform != "win32":
        assert all(os.access(output / name, os.X_OK) for name in files)
        assert not (output / "LICENSE.txt").stat().st_mode & 0o111


@pytest.mark.parametrize("probe", [None, b""])
def test_incomplete_tar(tmp_path: Path, probe: bytes | None) -> None:
    """Do not install an archive with a missing or empty executable."""
    entries = [("ffmpeg", b"encoder")]
    if probe is not None:
        entries.append(("ffprobe", probe))
    config = make_tar(tmp_path / "incomplete.tar.xz", entries)
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="one non-empty root-level ffprobe"):
        config.download_files(output)


def test_nested_executables_are_rejected(tmp_path: Path) -> None:
    """Do not silently support upstream directory layouts in the common format."""
    config = make_tar(
        tmp_path / "nested.tar.xz", [("bin/ffmpeg", b"encoder"), ("bin/ffprobe", b"probe")]
    )
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="one non-empty root-level ffmpeg"):
        config.download_files(output)
    assert not list(output.iterdir())


@pytest.mark.parametrize("name", ["ffmpeg", "LICENSE.txt"])
def test_duplicate_root_file_is_rejected(tmp_path: Path, name: str) -> None:
    """Reject ambiguous duplicate root entries rather than picking one."""
    config = make_tar(
        tmp_path / "duplicate.tar.xz",
        [("ffmpeg", b"encoder"), ("ffprobe", b"probe"), (name, b"notice"), (name, b"replacement")],
    )
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="Duplicate root file"):
        config.download_files(output)


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.DIRTYPE])
def test_tar_links_cannot_supply_executable(tmp_path: Path, kind: bytes) -> None:
    """Never follow a TAR link, even when it has an expected executable name."""
    archive = tmp_path / "links.tar.xz"
    with tarfile.open(archive, "w:xz") as package:
        entry = tarfile.TarInfo("ffmpeg")
        entry.type = kind
        entry.linkname = "../outside"
        package.addfile(entry)
    config = FFmpegDownload(
        archive.as_uri(),
        hashlib.sha256(archive.read_bytes()).hexdigest(),
        {"ffmpeg": "0" * 64, "ffprobe": "0" * 64},
    )
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="one non-empty root-level ffmpeg"):
        config.download_files(output)
    assert not list(output.iterdir())


def test_unreadable_tar_member(tmp_path: Path, mocker: "MockerFixture") -> None:
    """An unreadable member must fail instead of installing a partial executable."""
    config = make_tar(tmp_path / "bad.tar.xz", [("ffmpeg", b"encoder"), ("ffprobe", b"probe")])
    mocker.patch("tarfile.TarFile.extractfile", return_value=None)
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="Cannot read"):
        config.download_files(output)


def test_archive_checksum_failure_prevents_extraction(tmp_path: Path) -> None:
    """Do not copy any executable from a modified download."""
    config = make_tar(tmp_path / "release.tar.xz", [("ffmpeg", b"encoder"), ("ffprobe", b"probe")])
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        replace(config, sha256="0" * 64).download_files(output)
    assert not list(output.iterdir())


def test_executable_checksum_is_independent_of_archive_checksum(tmp_path: Path) -> None:
    """A valid archive digest cannot authorize unexpected executable bytes."""
    config = make_tar(tmp_path / "release.tar.xz", [("ffmpeg", b"encoder"), ("ffprobe", b"probe")])
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="SHA-256 mismatch for ffprobe executable"):
        replace(config, binary_sha256={**config.binary_sha256, "ffprobe": "0" * 64}).download_files(
            output
        )


def test_missing_executable_digest_is_rejected(tmp_path: Path) -> None:
    """Every executable needs an explicit digest, with no unchecked mode."""
    config = FFmpegDownload("https://example.com/release.tar.xz", "0" * 64, {"ffmpeg": "0" * 64})
    with pytest.raises(ValueError, match="digests for both"):
        config.download_files(tmp_path)


def test_cache_identity_tracks_build_changes() -> None:
    """Archive or executable identity changes invalidate the old cache."""
    config = FFmpegDownload(
        "https://example.com/build.tar.xz", "a" * 64, {"ffmpeg": "b" * 64, "ffprobe": "c" * 64}
    )
    assert config.cache_id == replace(config).cache_id
    assert config.cache_id != replace(config, sha256="d" * 64).cache_id
    assert config.cache_id != replace(config, url="https://example.com/new.tar.xz").cache_id
    assert config.cache_id != replace(config, binary_sha256={"ffmpeg": "e" * 64}).cache_id
