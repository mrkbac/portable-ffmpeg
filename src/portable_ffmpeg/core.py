"""Core functionality for managing FFmpeg binaries."""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from importlib.resources import as_file, files
from pathlib import Path

from .config import DOWNLOAD_URLS
from .enums import Architectures, FFmpegVersions, OperatingSystems

CACHE_DIR = Path(__file__).parent / "binaries"
_download_lock = threading.Lock()
_path_lock = threading.Lock()


def get_ffmpeg(version: FFmpegVersions = FFmpegVersions.LATEST) -> tuple[Path, Path]:
    """Download and return paths to static ffmpeg and ffprobe binaries.

    Args:
        version: FFmpeg major version to download (default: latest).

    Returns:
        Tuple containing paths to ffmpeg and ffprobe binaries.

    """
    system = OperatingSystems.from_current_system()
    arch = Architectures.from_current_architecture()

    # Create cache directory inside the package
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Get platform-specific configuration
    if system not in DOWNLOAD_URLS:
        msg = f"Unsupported operating system: {system}"
        raise ValueError(msg)

    if arch not in DOWNLOAD_URLS[system]:
        msg = f"Unsupported {system} architecture: {arch}"
        raise ValueError(msg)

    if version not in {FFmpegVersions.LATEST, FFmpegVersions.V9}:
        msg = f"Unsupported FFmpeg version {version} for {system} {arch}"
        raise ValueError(msg)

    config = DOWNLOAD_URLS[system][arch]

    # Check if binaries already exist in cache
    cache_subdir = f"{system.value}-{arch.value}-{config.cache_id}"
    platform_cache_dir = CACHE_DIR / cache_subdir
    ffmpeg_path = platform_cache_dir / config.ffmpeg_name
    ffprobe_path = platform_cache_dir / config.ffprobe_name

    with _download_lock:
        if not all(path.is_file() and path.stat().st_size for path in (ffmpeg_path, ffprobe_path)):
            print(f"Downloading FFmpeg {version.value} binaries for {system} {arch}...")

            # Handle corrupted cache (file exists where directory should be)
            if platform_cache_dir.exists() and not platform_cache_dir.is_dir():
                platform_cache_dir.unlink()

            if platform_cache_dir.is_dir():
                shutil.rmtree(platform_cache_dir)

            # Publish both binaries together so failed extraction cannot poison the cache.
            with tempfile.TemporaryDirectory(dir=CACHE_DIR) as tmp_dir:
                staging = Path(tmp_dir) / "binaries"
                staging.mkdir()
                try:
                    bundle = files("portable_ffmpeg_full").joinpath("ffmpeg.tar.xz")
                except ModuleNotFoundError as error:
                    if error.name != "portable_ffmpeg_full":
                        raise
                    config.download_files(staging)
                else:
                    with as_file(bundle) as archive:
                        config.download_files(staging, archive_url=archive.resolve().as_uri())
                staging.rename(platform_cache_dir)

    return ffmpeg_path, ffprobe_path


def clear_cache() -> None:
    """Clear the cached FFmpeg binaries.

    This removes all downloaded binaries from the cache directory,
    forcing them to be re-downloaded on the next call to get_ffmpeg().
    """
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)


def add_to_path(*, weak: bool = False, version: FFmpegVersions = FFmpegVersions.LATEST) -> None:
    """Add FFmpeg binaries to system PATH.

    Args:
        weak: If True, only add to PATH if ffmpeg is not already available.
              If False, always add to PATH (taking precedence).
        version: FFmpeg major version to use (default: latest).

    """
    with _path_lock:
        if weak and shutil.which("ffmpeg") is not None:
            return  # ffmpeg already available, don't override

        ffmpeg_path, _ = get_ffmpeg(version)
        bin_dir = str(ffmpeg_path.parent)

        current_path = os.environ.get("PATH", "")
        if bin_dir not in current_path:
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{current_path}"


def remove_from_path(version: FFmpegVersions = FFmpegVersions.LATEST) -> None:
    """Remove FFmpeg binaries from system PATH.

    Args:
        version: FFmpeg major version to use (default: latest).

    """
    with _path_lock:
        ffmpeg_path, _ = get_ffmpeg(version)
        bin_dir = str(ffmpeg_path.parent)

        current_path = os.environ.get("PATH", "")
        path_parts = current_path.split(os.pathsep)

        # Remove our binary directory from PATH
        new_path_parts = [part for part in path_parts if part != bin_dir]
        os.environ["PATH"] = os.pathsep.join(new_path_parts)


def run_ffmpeg(version: FFmpegVersions = FFmpegVersions.LATEST) -> None:
    """Entry point to run ffmpeg binary directly.

    Args:
        version: FFmpeg major version to use (default: latest).

    """
    ffmpeg_path, _ = get_ffmpeg(version)
    subprocess.run([str(ffmpeg_path), *sys.argv[1:]], check=False)


def run_ffprobe(version: FFmpegVersions = FFmpegVersions.LATEST) -> None:
    """Entry point to run ffprobe binary directly.

    Args:
        version: FFmpeg major version to use (default: latest).

    """
    _, ffprobe_path = get_ffmpeg(version)
    subprocess.run([str(ffprobe_path), *sys.argv[1:]], check=False)


def print_paths() -> None:
    """Print the paths to the FFmpeg and FFprobe binaries."""
    ffmpeg_path, ffprobe_path = get_ffmpeg()
    print(f"FFmpeg: {ffmpeg_path}")
    print(f"FFprobe: {ffprobe_path}")
