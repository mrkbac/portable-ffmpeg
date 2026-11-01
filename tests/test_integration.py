"""Integration tests for portable_ffmpeg module."""

import concurrent.futures
import os
import re
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from portable_ffmpeg import add_to_path, clear_cache, get_ffmpeg, remove_from_path
from portable_ffmpeg.core import CACHE_DIR
from portable_ffmpeg.enums import FFmpegVersions


@pytest.fixture(autouse=True)
def release_downloads(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Use exact unpublished TAR.XZ archives with a cache isolated from the checkout."""
    from portable_ffmpeg import core
    from portable_ffmpeg.config import DOWNLOAD_URLS
    from portable_ffmpeg.enums import Architectures, OperatingSystems

    cache = tmp_path / "binaries"
    monkeypatch.setattr(core, "CACHE_DIR", cache)
    monkeypatch.setattr("tests.test_integration.CACHE_DIR", cache)
    release_dir = request.config.getoption("release_dir")
    if release_dir is not None:
        assert isinstance(release_dir, Path)
        config = DOWNLOAD_URLS[OperatingSystems.from_current_system()][
            Architectures.from_current_architecture()
        ]
        archive = (release_dir / config.url.rsplit("/", 1)[1]).resolve(strict=True)
        monkeypatch.setattr(config, "url", archive.as_uri())


class TestModuleIntegration:
    """Comprehensive integration tests for the complete module."""

    @pytest.mark.slow
    def test_v9_download_current_platform(self) -> None:
        """Download V9 on supported current platforms and verify both executables."""
        from portable_ffmpeg.enums import Architectures, OperatingSystems

        system = OperatingSystems.from_current_system()
        architecture = Architectures.from_current_architecture()
        from portable_ffmpeg.config import DOWNLOAD_URLS

        if system not in DOWNLOAD_URLS or architecture not in DOWNLOAD_URLS[system]:
            pytest.skip("V9 is not configured for this platform")

        clear_cache()
        ffmpeg_path, ffprobe_path = get_ffmpeg(FFmpegVersions.V9)

        # BtbN builds report "version n9.0.2-...", other sources "version 9.0.2".
        for executable, expected in [
            (ffmpeg_path, r"ffmpeg version n?9\."),
            (ffprobe_path, r"ffprobe version n?9\."),
        ]:
            assert executable.exists()
            assert os.access(executable, os.X_OK)
            result = subprocess.run(
                [str(executable), "-version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            assert result.returncode == 0
            assert re.match(expected, result.stdout.splitlines()[0])

        for flag, required in [
            ("-encoders", {"libx264", "libx265", "libvpx-vp9", "libaom-av1"}),
            ("-decoders", {"h264", "hevc", "vp9", "av1"}),
        ]:
            result = subprocess.run(
                [str(ffmpeg_path), "-hide_banner", flag],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            names = {
                line.split()[1]
                for line in result.stdout.splitlines()
                if re.match(r"^ [VAS.][A-Z.]{5} ", line)
            }
            assert required <= names, f"Missing {flag}: {required - names}"

        result = subprocess.run(
            [str(ffmpeg_path), "-hide_banner", "-hwaccels"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        required_hw = (
            {"videotoolbox"} if system == OperatingSystems.OSX else {"cuda", "vulkan", "amf"}
        )
        if system == OperatingSystems.LINUX:
            required_hw.add("vaapi")
        if system != OperatingSystems.OSX and architecture == Architectures.AMD64:
            required_hw.add("qsv")
        assert required_hw <= set(result.stdout.split())

        assert architecture in {Architectures.AMD64, Architectures.ARM64}
        clear_cache()

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
        with patch("portable_ffmpeg.downloaders.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = ConnectionError("Network error")

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
        from portable_ffmpeg.config import DOWNLOAD_URLS

        config = DOWNLOAD_URLS[system][arch]
        platform_subdir = CACHE_DIR / f"{system.value}-{arch.value}-{config.cache_id}"

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

        system = OperatingSystems.from_current_system()
        arch = Architectures.from_current_architecture()
        assert arch in DOWNLOAD_URLS[system]
        clear_cache()
        paths = get_ffmpeg(FFmpegVersions.V9)
        assert all(path.is_file() and os.access(path, os.X_OK) for path in paths)
        assert get_ffmpeg(FFmpegVersions.LATEST) == paths
