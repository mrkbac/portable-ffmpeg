"""Tests for the core module."""

import os
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

from portable_ffmpeg.core import (
    CACHE_DIR,
    add_to_path,
    clear_cache,
    get_ffmpeg,
    remove_from_path,
    run_ffmpeg,
    run_ffprobe,
)
from portable_ffmpeg.enums import Architectures, OperatingSystems


class TestGetFFmpeg:
    """Tests for get_ffmpeg function."""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self) -> Generator[None, None, None]:
        """Clear cache before and after each test."""
        clear_cache()
        yield
        clear_cache()

    @pytest.mark.slow
    def test_get_ffmpeg_returns_paths(self) -> None:
        """Test that get_ffmpeg returns Path objects."""
        ffmpeg_path, ffprobe_path = get_ffmpeg()

        assert isinstance(ffmpeg_path, Path)
        assert isinstance(ffprobe_path, Path)
        assert ffmpeg_path.exists()
        assert ffprobe_path.exists()

    @pytest.mark.slow
    def test_get_ffmpeg_caching_behavior(self) -> None:
        """Test that get_ffmpeg uses cached binaries when available."""
        # First call - should download
        ffmpeg_path1, ffprobe_path1 = get_ffmpeg()

        # Verify files exist
        assert ffmpeg_path1.exists()
        assert ffprobe_path1.exists()

        # Second call - should use cache
        ffmpeg_path2, ffprobe_path2 = get_ffmpeg()

        # Paths should be identical
        assert ffmpeg_path1 == ffmpeg_path2
        assert ffprobe_path1 == ffprobe_path2

    def test_get_ffmpeg_unsupported_os(self, mocker: "MockerFixture") -> None:
        """Test that unsupported OS raises ValueError."""
        mocker.patch(
            "portable_ffmpeg.core.OperatingSystems.from_current_system",
            side_effect=ValueError("Unsupported operating system: freebsd"),
        )

        with pytest.raises(ValueError, match="Unsupported operating system: freebsd"):
            get_ffmpeg()

    def test_get_ffmpeg_unsupported_arch(self, mocker: "MockerFixture") -> None:
        """Test that unsupported architecture raises ValueError."""
        mocker.patch(
            "portable_ffmpeg.core.OperatingSystems.from_current_system",
            return_value=OperatingSystems.LINUX,
        )
        mocker.patch(
            "portable_ffmpeg.core.Architectures.from_current_architecture",
            side_effect=ValueError("Unsupported architecture: sparc"),
        )

        with pytest.raises(ValueError, match="Unsupported architecture: sparc"):
            get_ffmpeg()

    @pytest.mark.slow
    def test_get_ffmpeg_handles_corrupted_cache(self, mocker: "MockerFixture") -> None:
        """Test that get_ffmpeg handles corrupted cache directory."""
        mocker.patch(
            "portable_ffmpeg.core.OperatingSystems.from_current_system",
            return_value=OperatingSystems.LINUX,
        )
        mocker.patch(
            "portable_ffmpeg.core.Architectures.from_current_architecture",
            return_value=Architectures.AMD64,
        )

        # Clear cache first
        clear_cache()

        # Create a file where the platform cache directory should be
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        platform_dir = CACHE_DIR / "linux-amd64"
        platform_dir.touch()  # Create file instead of directory

        assert platform_dir.exists()
        assert not platform_dir.is_dir()

        # This should handle the corruption and recreate as directory
        ffmpeg_path, ffprobe_path = get_ffmpeg()

        # Should have created proper directory structure
        assert platform_dir.is_dir()
        assert ffmpeg_path.exists()
        assert ffprobe_path.exists()


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clear_cache_removes_directory(self) -> None:
        """Test that clear_cache removes the cache directory."""
        # First, create some cached files
        get_ffmpeg()

        # Verify cache exists
        assert CACHE_DIR.exists()

        # Clear cache
        clear_cache()

        # Verify cache is gone
        assert not CACHE_DIR.exists()

    def test_clear_cache_when_no_cache_exists(self) -> None:
        """Test that clear_cache works when no cache exists."""
        # Ensure no cache exists
        clear_cache()

        # Should not raise an error
        clear_cache()


class TestAddToPath:
    """Tests for add_to_path function."""

    def setUp(self) -> None:
        """Store original PATH."""
        self.original_path = os.environ.get("PATH", "")

    def tearDown(self) -> None:
        """Restore original PATH."""
        os.environ["PATH"] = self.original_path

    def test_add_to_path_weak_ffmpeg_exists(self, mocker: "MockerFixture") -> None:
        """Test weak=True when ffmpeg already exists."""
        mock_which = mocker.patch("shutil.which", return_value="/usr/bin/ffmpeg")

        original_path = os.environ.get("PATH", "")
        add_to_path(weak=True)

        # PATH should not have changed
        assert os.environ["PATH"] == original_path
        mock_which.assert_called_once_with("ffmpeg")

    def test_add_to_path_weak_ffmpeg_not_exists(self, mocker: "MockerFixture") -> None:
        """Test weak=True when ffmpeg doesn't exist."""
        mock_which = mocker.patch("shutil.which", return_value=None)

        with patch("portable_ffmpeg.core.get_ffmpeg") as mock_get_ffmpeg:
            mock_path = Path("/cache/ffmpeg")
            mock_get_ffmpeg.return_value = (mock_path, Path("/cache/ffprobe"))

            _original_path = os.environ.get("PATH", "")
            add_to_path(weak=True)

            # PATH should include the binary directory
            expected_bin_dir = str(mock_path.parent)
            assert expected_bin_dir in os.environ["PATH"]
            mock_which.assert_called_once_with("ffmpeg")

    def test_add_to_path_strong(self) -> None:
        """Test add_to_path without weak flag."""
        with patch("portable_ffmpeg.core.get_ffmpeg") as mock_get_ffmpeg:
            mock_path = Path("/cache/ffmpeg")
            mock_get_ffmpeg.return_value = (mock_path, Path("/cache/ffprobe"))

            _original_path = os.environ.get("PATH", "")
            add_to_path(weak=False)

            # PATH should include the binary directory at the beginning
            expected_bin_dir = str(mock_path.parent)
            assert os.environ["PATH"].startswith(expected_bin_dir)

    def test_add_to_path_already_in_path(self) -> None:
        """Test that add_to_path doesn't duplicate entries."""
        with patch("portable_ffmpeg.core.get_ffmpeg") as mock_get_ffmpeg:
            mock_path = Path("/cache/ffmpeg")
            mock_get_ffmpeg.return_value = (mock_path, Path("/cache/ffprobe"))

            # Add to PATH first time
            add_to_path()
            first_path = os.environ["PATH"]

            # Add to PATH second time
            add_to_path()
            second_path = os.environ["PATH"]

            # PATH should be the same
            assert first_path == second_path


class TestRemoveFromPath:
    """Tests for remove_from_path function."""

    def test_remove_from_path(self) -> None:
        """Test that remove_from_path removes the binary directory."""
        with patch("portable_ffmpeg.core.get_ffmpeg") as mock_get_ffmpeg:
            mock_path = Path("/cache/ffmpeg")
            mock_get_ffmpeg.return_value = (mock_path, Path("/cache/ffprobe"))

            # Add to PATH first
            add_to_path()
            expected_bin_dir = str(mock_path.parent)
            assert expected_bin_dir in os.environ["PATH"]

            # Remove from PATH
            remove_from_path()
            assert expected_bin_dir not in os.environ["PATH"]

    def test_remove_from_path_not_in_path(self) -> None:
        """Test remove_from_path when directory not in PATH."""
        with patch("portable_ffmpeg.core.get_ffmpeg") as mock_get_ffmpeg:
            mock_path = Path("/cache/ffmpeg")
            mock_get_ffmpeg.return_value = (mock_path, Path("/cache/ffprobe"))

            _original_path = os.environ.get("PATH", "")

            # Remove from PATH (shouldn't be there)
            remove_from_path()

            # PATH should be unchanged
            assert os.environ["PATH"] == _original_path


class TestRunFFmpeg:
    """Tests for run_ffmpeg function."""

    @patch("portable_ffmpeg.core.subprocess.run")
    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("portable_ffmpeg.core.sys.argv", ["stat_ffmpeg", "-version"])
    def test_run_ffmpeg(self, mock_get_ffmpeg: MagicMock, mock_subprocess_run: MagicMock) -> None:
        """Test that run_ffmpeg calls subprocess with correct arguments."""
        mock_ffmpeg_path = Path("/cache/ffmpeg")
        mock_get_ffmpeg.return_value = (mock_ffmpeg_path, Path("/cache/ffprobe"))

        run_ffmpeg()

        mock_subprocess_run.assert_called_once_with(
            [str(mock_ffmpeg_path), "-version"], check=False
        )

    @patch("portable_ffmpeg.core.subprocess.run")
    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("portable_ffmpeg.core.sys.argv", ["stat_ffmpeg"])
    def test_run_ffmpeg_no_args(
        self, mock_get_ffmpeg: MagicMock, mock_subprocess_run: MagicMock
    ) -> None:
        """Test run_ffmpeg with no additional arguments."""
        mock_ffmpeg_path = Path("/cache/ffmpeg")
        mock_get_ffmpeg.return_value = (mock_ffmpeg_path, Path("/cache/ffprobe"))

        run_ffmpeg()

        mock_subprocess_run.assert_called_once_with([str(mock_ffmpeg_path)], check=False)


class TestRunFFprobe:
    """Tests for run_ffprobe function."""

    @patch("portable_ffmpeg.core.subprocess.run")
    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("portable_ffmpeg.core.sys.argv", ["stat_ffmpeg", "-version"])
    def test_run_ffprobe(self, mock_get_ffmpeg: MagicMock, mock_subprocess_run: MagicMock) -> None:
        """Test that run_ffprobe calls subprocess with correct arguments."""
        mock_ffprobe_path = Path("/cache/ffprobe")
        mock_get_ffmpeg.return_value = (Path("/cache/ffmpeg"), mock_ffprobe_path)

        run_ffprobe()

        mock_subprocess_run.assert_called_once_with(
            [str(mock_ffprobe_path), "-version"], check=False
        )

    @patch("portable_ffmpeg.core.subprocess.run")
    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("portable_ffmpeg.core.sys.argv", ["stat_ffmpeg"])
    def test_run_ffprobe_no_args(
        self, mock_get_ffmpeg: MagicMock, mock_subprocess_run: MagicMock
    ) -> None:
        """Test run_ffprobe with no additional arguments."""
        mock_ffprobe_path = Path("/cache/ffprobe")
        mock_get_ffmpeg.return_value = (Path("/cache/ffmpeg"), mock_ffprobe_path)

        run_ffprobe()

        mock_subprocess_run.assert_called_once_with([str(mock_ffprobe_path)], check=False)
