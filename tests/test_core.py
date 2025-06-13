"""Unit tests for core module functionality."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from portable_ffmpeg.core import get_ffmpeg, run_ffmpeg, run_ffprobe
from portable_ffmpeg.enums import FFmpegVersions

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unsupported_platform_real_error(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported operating system with real error path."""
        # Mock to return an unsupported OS that reaches the error in core.py
        mocker.patch(
            "portable_ffmpeg.enums.OperatingSystems.from_current_system",
            return_value=mocker.Mock(value="FreeBSD"),
        )
        mocker.patch(
            "portable_ffmpeg.enums.Architectures.from_current_architecture",
            return_value=mocker.Mock(value="sparc"),
        )

        with pytest.raises(ValueError, match="Unsupported operating system"):
            get_ffmpeg()

    def test_unsupported_architecture_real_error(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported architecture with real error path."""
        from portable_ffmpeg.enums import OperatingSystems

        # Mock to return supported OS but unsupported architecture
        fake_os = OperatingSystems.OSX
        fake_arch = mocker.Mock(value="sparc")

        mocker.patch(
            "portable_ffmpeg.enums.OperatingSystems.from_current_system", return_value=fake_os
        )
        mocker.patch(
            "portable_ffmpeg.enums.Architectures.from_current_architecture", return_value=fake_arch
        )

        with pytest.raises(ValueError, match="Unsupported OperatingSystems.OSX architecture"):
            get_ffmpeg()

    def test_unsupported_platform(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported operating system with enum error."""
        mocker.patch(
            "portable_ffmpeg.enums.OperatingSystems.from_current_system",
            side_effect=ValueError("Unsupported"),
        )

        with pytest.raises(ValueError, match="Unsupported"):
            get_ffmpeg()

    def test_unsupported_architecture(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported architecture with enum error."""
        mocker.patch(
            "portable_ffmpeg.enums.Architectures.from_current_architecture",
            side_effect=ValueError("Unsupported"),
        )

        with pytest.raises(ValueError, match="Unsupported"):
            get_ffmpeg()

    def test_unsupported_version(self, mocker: "MockerFixture") -> None:
        """Test behavior with unsupported FFmpeg version."""
        from portable_ffmpeg.enums import Architectures, OperatingSystems

        # Mock to return a supported platform but empty version config
        mocker.patch(
            "portable_ffmpeg.core.DOWNLOAD_URLS",
            {
                OperatingSystems.from_current_system(): {
                    Architectures.from_current_architecture(): {}
                }
            },
        )

        with pytest.raises(ValueError, match="Unsupported FFmpeg version"):
            get_ffmpeg(FFmpegVersions.LATEST)


class TestCliEntryPoints:
    """Test CLI entry point functions."""

    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("subprocess.run")
    def test_run_ffmpeg(self, mock_subprocess_run: MagicMock, mock_get_ffmpeg: MagicMock) -> None:
        """Test run_ffmpeg entry point."""
        mock_path = Path("/cache/ffmpeg")
        mock_get_ffmpeg.return_value = (mock_path, Path("/cache/ffprobe"))

        with patch.object(sys, "argv", ["script", "-version"]):
            run_ffmpeg()

        mock_subprocess_run.assert_called_once_with([str(mock_path), "-version"], check=False)

    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("subprocess.run")
    def test_run_ffprobe(self, mock_subprocess_run: MagicMock, mock_get_ffmpeg: MagicMock) -> None:
        """Test run_ffprobe entry point."""
        mock_path = Path("/cache/ffprobe")
        mock_get_ffmpeg.return_value = (Path("/cache/ffmpeg"), mock_path)

        with patch.object(sys, "argv", ["script", "-version"]):
            run_ffprobe()

        mock_subprocess_run.assert_called_once_with([str(mock_path), "-version"], check=False)
