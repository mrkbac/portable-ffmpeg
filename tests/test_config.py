"""Tests for the project-owned common TAR.XZ download configuration."""

import re

import pytest

from portable_ffmpeg.config import DOWNLOAD_URLS
from portable_ffmpeg.enums import Architectures, OperatingSystems

SUPPORTED_PLATFORMS = [
    (OperatingSystems.WINDOWS, Architectures.AMD64),
    (OperatingSystems.LINUX, Architectures.AMD64),
    (OperatingSystems.LINUX, Architectures.ARM64),
    (OperatingSystems.OSX, Architectures.AMD64),
    (OperatingSystems.OSX, Architectures.ARM64),
]


def test_platform_coverage() -> None:
    """Keep all five supported platforms with one release artifact per platform."""
    assert {
        (system, arch) for system, architectures in DOWNLOAD_URLS.items() for arch in architectures
    } == set(SUPPORTED_PLATFORMS)


@pytest.mark.parametrize(("system", "architecture"), SUPPORTED_PLATFORMS)
def test_common_tar_is_pinned_and_verified(
    system: OperatingSystems, architecture: Architectures
) -> None:
    """Every platform uses a checksum-pinned TAR.XZ from the same owned release."""
    config = DOWNLOAD_URLS[system][architecture]
    assert config.url == (
        "https://github.com/mrkbac/portable-ffmpeg/releases/download/ffmpeg-9.0.2-1/"
        f"ffmpeg-9.0.2-{system.value}-{architecture.value}.tar.xz"
    )
    assert re.fullmatch("[0-9a-f]{64}", config.sha256)
    suffix = ".exe" if system == OperatingSystems.WINDOWS else ""
    assert config.ffmpeg_name == f"ffmpeg{suffix}"
    assert config.ffprobe_name == f"ffprobe{suffix}"

    assert set(config.binary_sha256) == {config.ffmpeg_name, config.ffprobe_name}
    assert all(re.fullmatch("[0-9a-f]{64}", digest) for digest in config.binary_sha256.values())
