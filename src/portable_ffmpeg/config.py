"""Configuration for FFmpeg download URLs by platform and architecture."""

from .downloaders import (
    BaseFFmpegDownloader,
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
)
from .enums import Architectures, FFmpegVersions, OperatingSystems

_BTBN_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest"
# BtbN only keeps the two newest release branches in "latest"; 7.1 is pinned to its last build.
_BTBN_V7_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-07-31-14-10"
_BTBN_V7_TAG = "n7.1.5-12-g1fdbca85aa"
_MARTIN_RIEDL_MACOS_AMD64_V9 = (
    "https://ffmpeg.martin-riedl.de/download/macos/amd64/1789931006_9.0.2"
)
_MARTIN_RIEDL_MACOS_ARM64_V9 = (
    "https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2"
)

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
                url=f"{_BTBN_BASE}/ffmpeg-n9.0-latest-win64-gpl-9.0.zip",
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
            FFmpegVersions.V8: FFmpegDownloadSingleZip(
                url=f"{_BTBN_BASE}/ffmpeg-n8.1-latest-win64-gpl-8.1.zip",
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleZip(
                url=f"{_BTBN_V7_BASE}/ffmpeg-{_BTBN_V7_TAG}-win64-gpl-7.1.zip",
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
            FFmpegVersions.V9: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n9.0-latest-linux64-gpl-9.0.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V8: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleTar(
                url=f"{_BTBN_V7_BASE}/ffmpeg-{_BTBN_V7_TAG}-linux64-gpl-7.1.tar.xz",
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
            FFmpegVersions.V9: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n9.0-latest-linuxarm64-gpl-9.0.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V8: FFmpegDownloadSingleTar(
                url=f"{_BTBN_BASE}/ffmpeg-n8.1-latest-linuxarm64-gpl-8.1.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleTar(
                url=f"{_BTBN_V7_BASE}/ffmpeg-{_BTBN_V7_TAG}-linuxarm64-gpl-7.1.tar.xz",
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
