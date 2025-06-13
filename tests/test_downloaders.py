"""Tests for the downloaders module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from portable_ffmpeg.downloaders import (
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
    _download_file,
    _extract_tar_files,
    _extract_zip_files,
)


class TestFFmpegDownloadSingleZip:
    """Tests for FFmpegDownloadSingleZip downloader."""

    @patch("portable_ffmpeg.downloaders._extract_zip_files")
    @patch("portable_ffmpeg.downloaders.urllib.request.urlretrieve")
    def test_download_files_integration(
        self,
        mock_urlretrieve: MagicMock,  # noqa: ARG002
        mock_extract: MagicMock,  # noqa: ARG002
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

            # Should return correct paths
            assert result == (ffmpeg_path, ffprobe_path)


class TestDownloadHelpers:
    """Test helper functions for downloading."""

    def test_download_file_progress_unknown_size(self) -> None:
        """Test download progress reporting with unknown size."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = Path(tmp_dir) / "test.txt"

            # Mock urllib.request.urlretrieve to call reporthook with unknown size
            def mock_urlretrieve(_url: str, _file_path: Path, reporthook) -> None:  # noqa: ANN001
                # Simulate download with unknown total size (total_size = -1)
                reporthook(0, 1024, -1)  # This should trigger the unknown size branch
                reporthook(1, 1024, -1)
                tmp_file.write_text("test content")

            with patch("portable_ffmpeg.downloaders.urllib.request.urlretrieve", mock_urlretrieve):
                _download_file("http://example.com/test.txt", tmp_file)

            assert tmp_file.exists()

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
