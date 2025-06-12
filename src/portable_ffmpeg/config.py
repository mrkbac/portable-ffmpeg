"""Configuration for FFmpeg download URLs by platform and architecture."""

from .downloaders import (
    BaseFFmpegDownloader,
    FFmpegDownloadSingleTar,
    FFmpegDownloadSingleZip,
    FFmpegDownloadTwoZips,
)
from .enums import Architectures, OperatingSystems

# Download URLs for different platforms and architectures
DOWNLOAD_URLS: dict[
    OperatingSystems,
    dict[Architectures, BaseFFmpegDownloader],
] = {
    OperatingSystems.WINDOWS: {
        Architectures.AMD64: FFmpegDownloadSingleZip(
            url="https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
            ffmpeg_name="ffmpeg.exe",
            ffprobe_name="ffprobe.exe",
        ),
    },
    OperatingSystems.OSX: {
        Architectures.AMD64: FFmpegDownloadTwoZips(
            ffmpeg_url="https://www.osxexperts.net/ffmpeg71intel.zip",
            ffprobe_url="https://www.osxexperts.net/ffprobe71intel.zip",
            ffmpeg_name="ffmpeg",
            ffprobe_name="ffprobe",
        ),
        Architectures.ARM64: FFmpegDownloadTwoZips(
            ffmpeg_url="https://www.osxexperts.net/ffmpeg711arm.zip",
            ffprobe_url="https://www.osxexperts.net/ffprobe711arm.zip",
            ffmpeg_name="ffmpeg",
            ffprobe_name="ffprobe",
        ),
    },
    OperatingSystems.LINUX: {
        Architectures.AMD64: FFmpegDownloadSingleTar(
            url="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
            ffmpeg_name="ffmpeg",
            ffprobe_name="ffprobe",
        ),
        Architectures.ARM64: FFmpegDownloadSingleTar(
            url="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
            ffmpeg_name="ffmpeg",
            ffprobe_name="ffprobe",
        ),
    },
}
