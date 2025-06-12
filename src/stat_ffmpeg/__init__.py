"""Static FFmpeg binaries for Windows, macOS, and Linux.

This package automatically downloads and manages static FFmpeg binaries
for cross-platform use without requiring system installation.
"""

from .core import add_to_path, clear_cache, get_ffmpeg, remove_from_path, run_ffmpeg, run_ffprobe
from .enums import Architectures, OperatingSystems

__all__ = [
    "Architectures",
    "OperatingSystems",
    "add_to_path",
    "clear_cache",
    "get_ffmpeg",
    "remove_from_path",
    "run_ffmpeg",
    "run_ffprobe",
]
