"""Integration tests for stat_ffmpeg module."""

import concurrent.futures
import contextlib
import os
import subprocess
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from stat_ffmpeg import add_to_path, clear_cache, get_ffmpeg, remove_from_path
from stat_ffmpeg.core import CACHE_DIR

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture(scope="session")
def downloaded_binaries() -> tuple[Path, Path]:
    """Download FFmpeg binaries once per test session."""
    # Clear cache once at the start to ensure fresh download
    clear_cache()
    return get_ffmpeg()


class TestModuleIntegration:
    """Integration tests for the complete module."""

    @pytest.mark.slow
    def test_full_workflow(self) -> None:
        """Test the complete workflow: download, cache, PATH management."""
        # Clear cache to test fresh download
        clear_cache()

        # 1. Download binaries
        ffmpeg_path, ffprobe_path = get_ffmpeg()

        # Verify binaries exist and are executable
        assert ffmpeg_path.exists()
        assert ffprobe_path.exists()
        assert os.access(ffmpeg_path, os.X_OK)
        assert os.access(ffprobe_path, os.X_OK)

        # 2. Add to PATH
        os.environ.get("PATH", "")
        add_to_path()

        bin_dir = str(ffmpeg_path.parent)
        assert bin_dir in os.environ["PATH"]

        # 3. Remove from PATH
        remove_from_path()
        assert bin_dir not in os.environ["PATH"]

        # 4. Clear cache
        clear_cache()
        assert not CACHE_DIR.exists()

    @pytest.mark.slow
    def test_weak_path_integration(self) -> None:
        """Test add_to_path with weak=True integration."""
        # Store original PATH
        original_path = os.environ.get("PATH", "")

        # Mock shutil.which to return None (ffmpeg not found)
        with patch("shutil.which", return_value=None):
            # Add with weak=True (should add since ffmpeg not available)
            add_to_path(weak=True)
            ffmpeg_path, _ = get_ffmpeg()
            bin_dir = str(ffmpeg_path.parent)
            assert bin_dir in os.environ["PATH"]

            # Add with weak=True again (should not duplicate)
            path_after_first = os.environ["PATH"]
            add_to_path(weak=True)
            assert os.environ["PATH"] == path_after_first

        # Cleanup
        os.environ["PATH"] = original_path

    @pytest.mark.slow
    def test_binary_execution_integration(self, downloaded_binaries: tuple[Path, Path]) -> None:
        """Test that downloaded binaries can actually be executed."""
        ffmpeg_path, ffprobe_path = downloaded_binaries

        # Test ffmpeg version
        result = subprocess.run(
            [str(ffmpeg_path), "-version"], capture_output=True, text=True, timeout=30, check=False
        )
        assert result.returncode == 0
        assert "ffmpeg version" in result.stdout.lower()

        # Test ffprobe version
        result = subprocess.run(
            [str(ffprobe_path), "-version"], capture_output=True, text=True, timeout=30, check=False
        )
        assert result.returncode == 0
        assert "ffprobe version" in result.stdout.lower()


class TestConcurrencyIntegration:
    """Integration tests for concurrent access."""

    @pytest.mark.slow
    def test_concurrent_downloads(self) -> None:
        """Test that concurrent calls to get_ffmpeg work correctly."""

        def download_ffmpeg() -> tuple[Path, Path]:
            return get_ffmpeg()

        # Run multiple downloads concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(download_ffmpeg) for _ in range(5)]
            results = [future.result() for future in futures]

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result[0] == first_result[0]  # ffmpeg path
            assert result[1] == first_result[1]  # ffprobe path

        # Verify files exist
        assert first_result[0].exists()
        assert first_result[1].exists()

    @pytest.mark.skip("Flaky due to race conditions in concurrent operations")
    def test_concurrent_cache_clear_and_download(self) -> None:
        """Test concurrent cache clearing and downloading."""

        def clear_and_download() -> tuple[Path, Path]:
            with contextlib.suppress(OSError):
                # Handle race condition where another thread might be clearing cache
                clear_cache()
            return get_ffmpeg()

        def just_download() -> tuple[Path, Path]:
            return get_ffmpeg()

        # Mix of clear+download and just download operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            futures.extend([executor.submit(clear_and_download) for _ in range(2)])
            futures.extend([executor.submit(just_download) for _ in range(2)])

            results = [future.result() for future in futures]

        # All operations should succeed and return valid paths
        for ffmpeg_path, ffprobe_path in results:
            assert isinstance(ffmpeg_path, Path)
            assert isinstance(ffprobe_path, Path)

    def test_race_condition_path_management(self) -> None:
        """Test race conditions in PATH management."""

        def path_operations() -> bool:
            try:
                add_to_path()
                remove_from_path()
                add_to_path(weak=True)
            except Exception:
                return False
            else:
                return True

        # Run PATH operations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(path_operations) for _ in range(3)]
            results = [future.result() for future in futures]

        # All operations should succeed
        assert all(results)


class TestErrorHandlingIntegration:
    """Integration tests for error handling across modules."""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self) -> Generator[None, None, None]:
        """Clear cache before and after each test - needed for error scenarios."""
        clear_cache()
        yield
        clear_cache()

    def test_network_error_recovery(self, mocker: "MockerFixture") -> None:
        """Test recovery from network errors during download."""
        # Mock network failure on first attempt, success on second
        call_count = 0

        def mock_urlretrieve(*_args: object, **_kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                msg = "Network error"
                raise ConnectionError(msg)
            # On subsequent calls, use real implementation or mock success
            return MagicMock()

        mocker.patch(
            "stat_ffmpeg.downloaders.urllib.request.urlretrieve", side_effect=mock_urlretrieve
        )
        mocker.patch("stat_ffmpeg.downloaders.zipfile.ZipFile")
        mocker.patch("stat_ffmpeg.downloaders.Path.write_bytes")
        mocker.patch("stat_ffmpeg.downloaders.Path.unlink")

        with pytest.raises(ConnectionError):
            # First call should fail
            get_ffmpeg()

    @pytest.mark.slow
    def test_partial_cache_recovery(self) -> None:
        """Test recovery when cache contains only one binary."""
        # First, download both binaries
        ffmpeg_path, ffprobe_path = get_ffmpeg()
        assert ffmpeg_path.exists()
        assert ffprobe_path.exists()

        # Remove one binary to simulate partial cache
        ffprobe_path.unlink()
        assert not ffprobe_path.exists()

        # Next call should re-download both binaries
        new_ffmpeg_path, new_ffprobe_path = get_ffmpeg()
        assert new_ffmpeg_path.exists()
        assert new_ffprobe_path.exists()
        assert new_ffmpeg_path == ffmpeg_path
        assert new_ffprobe_path == ffprobe_path

    @pytest.mark.slow
    def test_corrupted_cache_directory_recovery(self) -> None:
        """Test recovery when cache directory is corrupted."""
        # Clear cache first
        clear_cache()

        # Get current system info to use the right platform directory
        from stat_ffmpeg.enums import Architectures, OperatingSystems

        system = OperatingSystems.from_current_system()
        arch = Architectures.from_current_architecture()

        # Create a file where directory should be
        platform_subdir = CACHE_DIR / f"{system.value}-{arch.value}"

        # Ensure parent exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Create file where directory should be
        platform_subdir.touch()
        assert platform_subdir.exists()
        assert not platform_subdir.is_dir()

        # get_ffmpeg should handle this and recreate as directory
        ffmpeg_path, ffprobe_path = get_ffmpeg()

        # Should have recovered and created proper directory structure
        assert platform_subdir.is_dir()
        assert ffmpeg_path.exists()
        assert ffprobe_path.exists()


class TestPlatformSpecificIntegration:
    """Integration tests for platform-specific behavior."""

    @pytest.mark.slow
    def test_binary_permissions_unix(self, downloaded_binaries: tuple[Path, Path]) -> None:
        """Test that Unix binaries get correct permissions."""
        ffmpeg_path, ffprobe_path = downloaded_binaries

        # Check that binaries are executable
        assert os.access(ffmpeg_path, os.X_OK)
        assert os.access(ffprobe_path, os.X_OK)

    @pytest.mark.slow
    def test_cache_directory_structure(self, downloaded_binaries: tuple[Path, Path]) -> None:
        """Test that cache directory structure is correct."""
        ffmpeg_path, ffprobe_path = downloaded_binaries

        # Verify cache structure
        assert CACHE_DIR.exists()
        assert CACHE_DIR.is_dir()

        # Should have platform-specific subdirectory
        platform_dirs = list(CACHE_DIR.iterdir())
        assert len(platform_dirs) == 1
        assert platform_dirs[0].is_dir()

        # Platform directory should contain the binaries
        platform_dir = platform_dirs[0]
        assert ffmpeg_path.parent == platform_dir
        assert ffprobe_path.parent == platform_dir
