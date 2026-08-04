"""Configuration for FFmpeg download URLs by platform and architecture."""

from .downloaders import (
    BaseFFmpegDownloader,
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
)
from .enums import Architectures, FFmpegVersions, OperatingSystems

_BTBN_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest"
_GYAN_V9_WINDOWS_AMD64 = (
    "https://github.com/GyanD/codexffmpeg/releases/download/9.0/ffmpeg-9.0-essentials_build.zip"
)
_MARTIN_RIEDL_MACOS_AMD64_V9 = "https://ffmpeg.martin-riedl.de/download/macos/amd64/1785871427_9.0"
_MARTIN_RIEDL_MACOS_ARM64_V9 = "https://ffmpeg.martin-riedl.de/download/macos/arm64/1785863997_9.0"

# Download URLs for different platforms, architectures, and versions
DOWNLOAD_URLS: dict[
    OperatingSystems,
    dict[Architectures, dict[FFmpegVersions, BaseFFmpegDownloader]],
] = {
    OperatingSystems.WINDOWS: {
        Architectures.AMD64: {
            FFmpegVersions.LATEST: FFmpegDownloadSingleZip(
                url=f"{_BTBN_BASE}/ffmpeg-master-latest-win64-gpl.zip",
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
            FFmpegVersions.V9: FFmpegDownloadSingleZip(
                url=_GYAN_V9_WINDOWS_AMD64,
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
            FFmpegVersions.V8: FFmpegDownloadSingleZip(
                url=f"{_BTBN_BASE}/ffmpeg-n8.1-latest-win64-gpl-8.1.zip",
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleZip(
                url=f"{_BTBN_BASE}/ffmpeg-n7.1-latest-win64-gpl-7.1.zip",
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
        },
    },
    OperatingSystems.OSX: {
        Architectures.AMD64: {
            FFmpegVersions.LATEST: FFmpegDownloadTwoZips(
                ffmpeg_url=f"{_MARTIN_RIEDL_MACOS_AMD64_V9}/ffmpeg.zip",
                ffprobe_url=f"{_MARTIN_RIEDL_MACOS_AMD64_V9}/ffprobe.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V9: FFmpegDownloadTwoZips(
                ffmpeg_url=f"{_MARTIN_RIEDL_MACOS_AMD64_V9}/ffmpeg.zip",
                ffprobe_url=f"{_MARTIN_RIEDL_MACOS_AMD64_V9}/ffprobe.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V8: FFmpegDownloadTwoZips(
                ffmpeg_url="https://www.osxexperts.net/ffmpeg80intel.zip",
                ffprobe_url="https://www.osxexperts.net/ffprobe80intel.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadTwoZips(
                ffmpeg_url="https://www.osxexperts.net/ffmpeg71intel.zip",
                ffprobe_url="https://www.osxexperts.net/ffprobe71intel.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
        },
        Architectures.ARM64: {
            FFmpegVersions.LATEST: FFmpegDownloadTwoZips(
                ffmpeg_url=f"{_MARTIN_RIEDL_MACOS_ARM64_V9}/ffmpeg.zip",
                ffprobe_url=f"{_MARTIN_RIEDL_MACOS_ARM64_V9}/ffprobe.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V9: FFmpegDownloadTwoZips(
                ffmpeg_url=f"{_MARTIN_RIEDL_MACOS_ARM64_V9}/ffmpeg.zip",
                ffprobe_url=f"{_MARTIN_RIEDL_MACOS_ARM64_V9}/ffprobe.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V8: FFmpegDownloadTwoZips(
                ffmpeg_url="https://www.osxexperts.net/ffmpeg80arm.zip",
                ffprobe_url="https://www.osxexperts.net/ffprobe80arm.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadTwoZips(
                ffmpeg_url="https://www.osxexperts.net/ffmpeg711arm.zip",
                ffprobe_url="https://www.osxexperts.net/ffprobe711arm.zip",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
        },
    },
    OperatingSystems.LINUX: {
        Architectures.AMD64: {
            FFmpegVersions.LATEST: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-master-latest-linux64-gpl.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V8: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V6: FFmpegDownloadSingleTar(
                url="https://johnvansickle.com/ffmpeg/old-releases/ffmpeg-6.0.1-amd64-static.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V5: FFmpegDownloadSingleTar(
                url="https://johnvansickle.com/ffmpeg/old-releases/ffmpeg-5.1.1-amd64-static.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
        },
        Architectures.ARM64: {
            FFmpegVersions.LATEST: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-master-latest-linuxarm64-gpl.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V8: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n8.1-latest-linuxarm64-gpl-8.1.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n7.1-latest-linuxarm64-gpl-7.1.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V6: FFmpegDownloadSingleTar(
                url="https://johnvansickle.com/ffmpeg/old-releases/ffmpeg-6.0.1-arm64-static.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V5: FFmpegDownloadSingleTar(
                url="https://johnvansickle.com/ffmpeg/old-releases/ffmpeg-5.1.1-arm64-static.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
        },
    },
}
