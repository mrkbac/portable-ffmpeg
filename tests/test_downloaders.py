"""Tests for the downloaders module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from portable_ffmpeg.downloaders import (
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
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
