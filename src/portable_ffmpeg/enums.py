"""Operating system and architecture enums for FFmpeg binary selection."""

import platform
from enum import Enum


class OperatingSystems(Enum):
    """Supported operating systems for ffmpeg binaries."""

    WINDOWS = "windows"
    OSX = "osx"
    LINUX = "linux"

    @classmethod
    def from_current_system(cls) -> "OperatingSystems":
        """Get the current operating system."""
        system = platform.system().lower()
        if system == "windows":
            return cls.WINDOWS
        if system == "darwin":
            return cls.OSX
        if system == "linux":
            return cls.LINUX

        msg = f"Unsupported operating system: {system}"
        raise ValueError(msg)


class Architectures(Enum):
    """Supported architectures for ffmpeg binaries."""

    AMD64 = "amd64"
    ARM64 = "arm64"

    @classmethod
    def from_current_architecture(cls) -> "Architectures":
        """Get the current architecture."""
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            return cls.AMD64
        if machine in ["aarch64", "arm64"]:
            return cls.ARM64

        msg = f"Unsupported architecture: {machine}"
        raise ValueError(msg)


class FFmpegVersions(Enum):
    """Supported FFmpeg major versions."""

    LATEST = "latest"
    V7 = "7"
    V6 = "6"
    V5 = "5"
