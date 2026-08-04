"""Tests for platform and version download configuration."""

import pytest

from portable_ffmpeg.config import DOWNLOAD_URLS
from portable_ffmpeg.downloaders import (
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
)
from portable_ffmpeg.enums import Architectures, FFmpegVersions, OperatingSystems

V9_URLS = {
    (OperatingSystems.OSX, Architectures.AMD64): (
        "https://ffmpeg.martin-riedl.de/download/macos/amd64/1785871427_9.0/ffmpeg.zip",
        "https://ffmpeg.martin-riedl.de/download/macos/amd64/1785871427_9.0/ffprobe.zip",
    ),
    (OperatingSystems.OSX, Architectures.ARM64): (
        "https://ffmpeg.martin-riedl.de/download/macos/arm64/1785863997_9.0/ffmpeg.zip",
        "https://ffmpeg.martin-riedl.de/download/macos/arm64/1785863997_9.0/ffprobe.zip",
    ),
}

BTBN_V8_URLS = {
    (OperatingSystems.WINDOWS, Architectures.AMD64): (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
        "ffmpeg-n8.1-latest-win64-gpl-8.1.zip",
        FFmpegDownloadSingleZip,
    ),
    (OperatingSystems.LINUX, Architectures.AMD64): (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
        "ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz",
        FFmpegDownloadSingleTar,
    ),
    (OperatingSystems.LINUX, Architectures.ARM64): (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
        "ffmpeg-n8.1-latest-linuxarm64-gpl-8.1.tar.xz",
        FFmpegDownloadSingleTar,
    ),
}


@pytest.mark.parametrize("platform", V9_URLS)
def test_v9_uses_verified_two_zip_configuration(
    platform: tuple[OperatingSystems, Architectures],
) -> None:
    """V9 maps each supported platform and architecture to its exact release assets."""
    operating_system, architecture = platform
    config = DOWNLOAD_URLS[operating_system][architecture][FFmpegVersions.V9]

    assert isinstance(config, FFmpegDownloadTwoZips)
    assert (config.ffmpeg_url, config.ffprobe_url) == V9_URLS[platform]
    assert (config.ffmpeg_name, config.ffprobe_name) == ("ffmpeg", "ffprobe")


@pytest.mark.parametrize("architecture", [Architectures.AMD64, Architectures.ARM64])
def test_macos_latest_uses_the_same_stable_v9_assets(architecture: Architectures) -> None:
    """MacOS LATEST points at the same stable 9.0 assets as explicit V9."""
    configs = DOWNLOAD_URLS[OperatingSystems.OSX][architecture]

    assert configs[FFmpegVersions.LATEST] == configs[FFmpegVersions.V9]


@pytest.mark.parametrize("platform", BTBN_V8_URLS)
def test_btb_n_v8_uses_current_8_1_assets(
    platform: tuple[OperatingSystems, Architectures],
) -> None:
    """BtbN V8 maps to the currently published 8.1 release assets."""
    operating_system, architecture = platform
    expected_url, downloader_type = BTBN_V8_URLS[platform]
    config = DOWNLOAD_URLS[operating_system][architecture][FFmpegVersions.V8]

    if downloader_type is FFmpegDownloadSingleZip:
        assert isinstance(config, FFmpegDownloadSingleZip)
        assert config.url == expected_url
    else:
        assert isinstance(config, FFmpegDownloadSingleTar)
        assert config.url == expected_url


def test_windows_v9_uses_gyand_release_asset() -> None:
    """Windows V9 maps to the verified GyanD 9.0 essentials release."""
    config = DOWNLOAD_URLS[OperatingSystems.WINDOWS][Architectures.AMD64][FFmpegVersions.V9]

    assert isinstance(config, FFmpegDownloadSingleZip)
    assert config.url == (
        "https://github.com/GyanD/codexffmpeg/releases/download/9.0/ffmpeg-9.0-essentials_build.zip"
    )
    assert (config.ffmpeg_name, config.ffprobe_name) == ("ffmpeg.exe", "ffprobe.exe")


@pytest.mark.parametrize("architecture", [Architectures.AMD64, Architectures.ARM64])
def test_linux_v9_is_not_configured_without_redistributable_assets(
    architecture: Architectures,
) -> None:
    """Linux V9 remains absent until a suitable redistributable release is available."""
    assert FFmpegVersions.V9 not in DOWNLOAD_URLS[OperatingSystems.LINUX][architecture]


@pytest.mark.parametrize(
    ("operating_system", "architecture"),
    [
        (OperatingSystems.WINDOWS, Architectures.AMD64),
        (OperatingSystems.LINUX, Architectures.AMD64),
        (OperatingSystems.LINUX, Architectures.ARM64),
    ],
)
def test_non_macos_latest_semantics_are_preserved(
    operating_system: OperatingSystems, architecture: Architectures
) -> None:
    """Windows and Linux LATEST mappings continue to use BtbN rolling master builds."""
    config = DOWNLOAD_URLS[operating_system][architecture][FFmpegVersions.LATEST]

    assert isinstance(config, (FFmpegDownloadSingleZip, FFmpegDownloadSingleTar))
    assert "github.com/BtbN/FFmpeg-Builds/releases/download/latest" in config.url
    assert "ffmpeg-master-latest" in config.url
