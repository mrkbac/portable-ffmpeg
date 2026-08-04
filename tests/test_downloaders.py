"""Tests for the downloaders module."""

import tempfile
import urllib.request
from pathlib import Path
from types import TracebackType
from unittest.mock import MagicMock, patch

import pytest

from portable_ffmpeg.downloaders import (
    _DOWNLOAD_CHUNK_SIZE,
    _DOWNLOAD_USER_AGENT,
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
    _download_file,
    _extract_tar_files,
    _extract_zip_files,
)


class FakeResponse:
    """Small streamed response fake for download tests."""

    def __init__(self, chunks: list[bytes], headers: dict[str, str]) -> None:
        """Initialize response chunks and HTTP headers."""
        self._chunks = chunks
        self.headers = headers
        self.read_sizes: list[int] = []

    def __enter__(self) -> "FakeResponse":
        """Enter the response context."""
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        """Exit the response context."""
        return

    def read(self, size: int = -1) -> bytes:
        """Return one chunk at a time and record the requested read size."""
        self.read_sizes.append(size)
        if self._chunks:
            return self._chunks.pop(0)
        return b""


class TestFFmpegDownloadSingleZip:
    """Tests for FFmpegDownloadSingleZip downloader."""

    @patch("portable_ffmpeg.downloaders._extract_zip_files")
    @patch("portable_ffmpeg.downloaders._download_file")
    def test_download_files_integration(
        self, mock_download: MagicMock, mock_extract: MagicMock
    ) -> None:
        """Test that download_files works with mocked dependencies."""
        downloader = FFmpegDownloadSingleZip(
            url="https://example.com/test.zip", ffmpeg_name="ffmpeg.exe", ffprobe_name="ffprobe.exe"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            outfolder = Path(temp_dir)

            # Mock the extraction to create the expected files
            ffmpeg_path = outfolder / "ffmpeg.exe"
            ffprobe_path = outfolder / "ffprobe.exe"
            ffmpeg_path.touch()
            ffprobe_path.touch()

            result = downloader.download_files(outfolder)

            mock_download.assert_called_once()
            mock_extract.assert_called_once()
            # Should return correct paths
            assert result == (ffmpeg_path, ffprobe_path)


class TestDownloadHelpers:
    """Test helper functions for downloading."""

    @patch("portable_ffmpeg.downloaders.urllib.request.urlopen")
    def test_download_file_streams_known_size_and_sets_user_agent(
        self, mock_urlopen: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test streamed writes, known-size progress, and the explicit User-Agent."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = Path(tmp_dir) / "known.txt"
            response = FakeResponse([b"first", b"second"], {"Content-Length": "11"})
            mock_urlopen.return_value = response

            _download_file("http://example.com/test.txt", str(tmp_file))

            assert tmp_file.read_bytes() == b"firstsecond"
            assert response.read_sizes == [_DOWNLOAD_CHUNK_SIZE] * 3
            request = mock_urlopen.call_args.args[0]
            assert isinstance(request, urllib.request.Request)
            assert request.get_header("User-agent") == _DOWNLOAD_USER_AGENT

            captured = capsys.readouterr()
            assert "Download complete!" in captured.out

    @patch("portable_ffmpeg.downloaders.urllib.request.urlopen")
    def test_download_file_progress_unknown_size(
        self, mock_urlopen: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test download progress reporting with an unknown content length."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = Path(tmp_dir) / "unknown.txt"
            mock_urlopen.return_value = FakeResponse([b"test", b" content"], {})

            _download_file("http://example.com/test.txt", tmp_file)

            assert tmp_file.read_text() == "test content"
            captured = capsys.readouterr()
            assert "4 bytes" in captured.out
            assert "12 bytes" in captured.out

    @patch("portable_ffmpeg.downloaders.urllib.request.urlopen")
    def test_download_file_propagates_download_errors(self, mock_urlopen: MagicMock) -> None:
        """Test that download exceptions are not swallowed."""
        mock_urlopen.side_effect = ConnectionError("Network error")

        with pytest.raises(ConnectionError, match="Network error"):
            _download_file("http://example.com/test.txt", Path("test.txt"))

    @patch("portable_ffmpeg.downloaders.tarfile.open")
    @patch("portable_ffmpeg.downloaders.sys.platform", "linux")
    def test_extract_tar_files(self, mock_tar_open: MagicMock) -> None:
        """Test TAR file extraction."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            tar_file = tmp_dir_path / "test.tar"
            output_dir = tmp_dir_path / "output"
            output_dir.mkdir()

            # Mock tar file behavior
            mock_tar = MagicMock()
            mock_tar_open.return_value.__enter__ = lambda _: mock_tar
            mock_tar_open.return_value.__exit__ = lambda *_: None

            mock_member = MagicMock()
            mock_member.isfile.return_value = True
            mock_member.name = "subdir/ffmpeg"
            mock_tar.getmembers.return_value = [mock_member]

            mock_extracted = MagicMock()
            mock_extracted.read.return_value = b"test ffmpeg content"
            mock_tar.extractfile.return_value = mock_extracted

            result = _extract_tar_files(tar_file, output_dir, ["ffmpeg"])

            assert len(result) == 1
            assert result[0].name == "ffmpeg"

    @patch("portable_ffmpeg.downloaders.zipfile.ZipFile")
    @patch("portable_ffmpeg.downloaders.sys.platform", "linux")
    def test_extract_zip_files(self, mock_zip_open: MagicMock) -> None:
        """Test ZIP file extraction."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            zip_file = tmp_dir_path / "test.zip"
            output_dir = tmp_dir_path / "output"
            output_dir.mkdir()

            # Mock zip file behavior
            mock_zip = MagicMock()
            mock_zip_open.return_value.__enter__ = lambda _: mock_zip
            mock_zip_open.return_value.__exit__ = lambda *_: None

            mock_zip.namelist.return_value = ["subdir/ffmpeg", "other/file.txt"]
            mock_zip.read.return_value = b"test ffmpeg content"

            result = _extract_zip_files(zip_file, output_dir, ["ffmpeg"])

            assert len(result) == 1
            assert result[0].name == "ffmpeg"


class TestFFmpegDownloadSingleTar:
    """Tests for FFmpegDownloadSingleTar downloader."""

    def test_init(self) -> None:
        """Test initialization of FFmpegDownloadSingleTar."""
        downloader = FFmpegDownloadSingleTar(
            url="https://example.com/test.tar.xz", ffmpeg_name="ffmpeg", ffprobe_name="ffprobe"
        )
        assert downloader.url == "https://example.com/test.tar.xz"
        assert downloader.ffmpeg_name == "ffmpeg"
        assert downloader.ffprobe_name == "ffprobe"

    @patch("portable_ffmpeg.downloaders._extract_tar_files")
    @patch("portable_ffmpeg.downloaders._download_file")
    def test_download_files(self, mock_download: MagicMock, mock_extract: MagicMock) -> None:
        """Test TAR downloader download_files method."""
        downloader = FFmpegDownloadSingleTar(
            url="https://example.com/test.tar.xz", ffmpeg_name="ffmpeg", ffprobe_name="ffprobe"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            outfolder = Path(temp_dir)

            # Mock the extraction to return the expected files
            ffmpeg_path = outfolder / "ffmpeg"
            ffprobe_path = outfolder / "ffprobe"
            mock_extract.return_value = [ffmpeg_path, ffprobe_path]

            result = downloader.download_files(outfolder)

            # Verify download was called
            mock_download.assert_called_once()
            # Verify extraction was called with correct parameters
            mock_extract.assert_called_once()
            # Should return correct paths
            assert result == (ffmpeg_path, ffprobe_path)


class TestFFmpegDownloadTwoZips:
    """Tests for FFmpegDownloadTwoZips downloader."""

    def test_init(self) -> None:
        """Test initialization of FFmpegDownloadTwoZips."""
        downloader = FFmpegDownloadTwoZips(
            ffmpeg_url="https://example.com/ffmpeg.zip",
            ffprobe_url="https://example.com/ffprobe.zip",
            ffmpeg_name="ffmpeg",
            ffprobe_name="ffprobe",
        )
        assert downloader.ffmpeg_url == "https://example.com/ffmpeg.zip"
        assert downloader.ffprobe_url == "https://example.com/ffprobe.zip"
        assert downloader.ffmpeg_name == "ffmpeg"
        assert downloader.ffprobe_name == "ffprobe"

    @patch("portable_ffmpeg.downloaders._extract_zip_files")
    @patch("portable_ffmpeg.downloaders._download_file")
    def test_download_files(self, mock_download: MagicMock, mock_extract: MagicMock) -> None:
        """Test TwoZips downloader download_files method."""
        downloader = FFmpegDownloadTwoZips(
            ffmpeg_url="https://example.com/ffmpeg.zip",
            ffprobe_url="https://example.com/ffprobe.zip",
            ffmpeg_name="ffmpeg",
            ffprobe_name="ffprobe",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            outfolder = Path(temp_dir)

            # Mock the extraction to return the expected files
            ffmpeg_path = outfolder / "ffmpeg"
            ffprobe_path = outfolder / "ffprobe"
            mock_extract.return_value = [ffmpeg_path, ffprobe_path]

            result = downloader.download_files(outfolder)

            # Verify download was called twice (once for each binary)
            assert mock_download.call_count == 2
            # Verify extraction was called twice
            assert mock_extract.call_count == 2
            # Should return correct paths
            assert result == (ffmpeg_path, ffprobe_path)
