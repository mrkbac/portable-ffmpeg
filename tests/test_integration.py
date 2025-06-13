"""Integration tests for portable_ffmpeg module."""

import concurrent.futures
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from portable_ffmpeg import add_to_path, clear_cache, get_ffmpeg, remove_from_path
from portable_ffmpeg.core import CACHE_DIR
from portable_ffmpeg.enums import FFmpegVersions


class TestModuleIntegration:
    """Comprehensive integration tests for the complete module."""

    def test_complete_workflow(self) -> None:
        """Test the complete workflow: download, cache, PATH management, execution."""
        # Clear cache to ensure fresh download
        clear_cache()

        # 1. Download binaries and verify caching
        ffmpeg_path, ffprobe_path = get_ffmpeg()

        # Verify binaries exist and are executable
        assert ffmpeg_path.exists()
        assert ffprobe_path.exists()
        assert os.access(ffmpeg_path, os.X_OK)
        assert os.access(ffprobe_path, os.X_OK)

        # Verify cache structure
        assert CACHE_DIR.exists()
        platform_dirs = list(CACHE_DIR.iterdir())
        assert len(platform_dirs) == 1
        assert platform_dirs[0].is_dir()
        assert ffmpeg_path.parent == platform_dirs[0]

        # 2. Test caching - second call should use cached binaries
        ffmpeg_path2, ffprobe_path2 = get_ffmpeg()
        assert ffmpeg_path == ffmpeg_path2
        assert ffprobe_path == ffprobe_path2

        # 3. Test binary execution
        result = subprocess.run(
            [str(ffmpeg_path), "-version"], capture_output=True, text=True, timeout=30, check=False
        )
        assert result.returncode == 0
        assert "ffmpeg version" in result.stdout.lower()

        result = subprocess.run(
            [str(ffprobe_path), "-version"], capture_output=True, text=True, timeout=30, check=False
        )
        assert result.returncode == 0
        assert "ffprobe version" in result.stdout.lower()

        # 4. Test PATH management
        original_path = os.environ.get("PATH", "")

        # Add to PATH
        add_to_path()
        bin_dir = str(ffmpeg_path.parent)
        assert bin_dir in os.environ["PATH"]

        # Test weak add (should not duplicate)
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            add_to_path(weak=True)  # Should not add since ffmpeg exists
            assert os.environ["PATH"].count(bin_dir) == 1

        # Remove from PATH
        remove_from_path()
        assert bin_dir not in os.environ["PATH"]

        # Restore original PATH
        os.environ["PATH"] = original_path

        # 5. Test cache clearing
        clear_cache()
        assert not CACHE_DIR.exists()

    def test_concurrent_operations(self) -> None:
        """Test concurrent downloads and PATH operations work correctly."""
        clear_cache()

        def download_ffmpeg() -> tuple[Path, Path]:
            return get_ffmpeg()

        def path_operations() -> bool:
            try:
                add_to_path()
                remove_from_path()
            except Exception:
                return False
            else:
                return True

        # Test concurrent downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            download_futures = [executor.submit(download_ffmpeg) for _ in range(3)]
            path_futures = [executor.submit(path_operations) for _ in range(2)]

            results = [future.result() for future in download_futures]
            path_results = [future.result() for future in path_futures]

        # All downloads should return identical paths
        first_result = results[0]
        for result in results[1:]:
            assert result[0] == first_result[0]
            assert result[1] == first_result[1]

        # All PATH operations should succeed
        assert all(path_results)

        # Verify files exist
        assert first_result[0].exists()
        assert first_result[1].exists()

    def test_error_handling(self) -> None:
        """Test error handling scenarios."""
        clear_cache()

        # Test network error handling
        with patch("portable_ffmpeg.downloaders.urllib.request.urlretrieve") as mock_urlretrieve:
            mock_urlretrieve.side_effect = ConnectionError("Network error")

            with pytest.raises(ConnectionError):
                get_ffmpeg()

        # Test partial cache recovery
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

        # Test corrupted cache directory recovery
        clear_cache()
        from portable_ffmpeg.enums import Architectures, OperatingSystems

        system = OperatingSystems.from_current_system()
        arch = Architectures.from_current_architecture()
        platform_subdir = CACHE_DIR / f"{system.value}-{arch.value}-latest"

        # Create file where directory should be
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        platform_subdir.touch()
        assert platform_subdir.exists()
        assert not platform_subdir.is_dir()

        # get_ffmpeg should handle this and recreate as directory
        ffmpeg_path, ffprobe_path = get_ffmpeg()
        assert platform_subdir.is_dir()
        assert ffmpeg_path.exists()
        assert ffprobe_path.exists()

    def test_version_support(self) -> None:
        """Test version support and validation."""
        from portable_ffmpeg.config import DOWNLOAD_URLS
        from portable_ffmpeg.enums import Architectures, OperatingSystems

        # Test that all enum versions have configurations
        enum_versions = set(FFmpegVersions)
        configured_versions = set()

        for os_configs in DOWNLOAD_URLS.values():
            for arch_configs in os_configs.values():
                configured_versions.update(arch_configs.keys())

        missing_versions = enum_versions - configured_versions
        assert not missing_versions, (
            f"Versions {missing_versions} are in enum but have no configurations"
        )

        # Test current platform support
        system = OperatingSystems.from_current_system()
        arch = Architectures.from_current_architecture()

        if system in DOWNLOAD_URLS and arch in DOWNLOAD_URLS[system]:
            available_versions = list(DOWNLOAD_URLS[system][arch].keys())
            assert len(available_versions) > 0

            # Test at least one version works
            test_version = available_versions[0]
            clear_cache()
            ffmpeg_path, ffprobe_path = get_ffmpeg(test_version)

            assert ffmpeg_path.exists()
            assert ffprobe_path.exists()
            assert os.access(ffmpeg_path, os.X_OK)
            assert os.access(ffprobe_path, os.X_OK)

            # Test version-specific caching
            if len(available_versions) > 1:
                version2 = available_versions[1]
                ffmpeg_path2, _ = get_ffmpeg(version2)

                # Different versions should be in different cache directories
                assert ffmpeg_path.parent != ffmpeg_path2.parent
                assert test_version.value in str(ffmpeg_path.parent)
                assert version2.value in str(ffmpeg_path2.parent)
