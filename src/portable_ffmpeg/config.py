"""Configuration for FFmpeg download URLs by platform and architecture."""

from .downloaders import (
    BaseFFmpegDownloader,
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
)
from .enums import Architectures, FFmpegVersions, OperatingSystems

# Download URLs for different platforms, architectures, and versions
DOWNLOAD_URLS: dict[
    OperatingSystems,
    dict[Architectures, dict[FFmpegVersions, BaseFFmpegDownloader]],
] = {
    OperatingSystems.WINDOWS: {
        Architectures.AMD64: {
            FFmpegVersions.LATEST: FFmpegDownloadSingleZip(
                url="https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleZip(
                url="https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-7.1.1-essentials_build.zip",
                ffmpeg_name="ffmpeg.exe",
                ffprobe_name="ffprobe.exe",
            ),
        },
    },
    OperatingSystems.OSX: {
        Architectures.AMD64: {
            FFmpegVersions.LATEST: FFmpegDownloadTwoZips(
                ffmpeg_url="https://www.osxexperts.net/ffmpeg71intel.zip",
                ffprobe_url="https://www.osxexperts.net/ffprobe71intel.zip",
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
                ffmpeg_url="https://www.osxexperts.net/ffmpeg711arm.zip",
                ffprobe_url="https://www.osxexperts.net/ffprobe711arm.zip",
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
                url="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleTar(
                url="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
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
                url="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
                ffmpeg_name="ffmpeg",
                ffprobe_name="ffprobe",
            ),
            FFmpegVersions.V7: FFmpegDownloadSingleTar(
                url="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
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
