"""Pinned common TAR.XZ archives for the project-owned FFmpeg binary release."""

from .downloaders import FFmpegDownload
from .enums import Architectures, OperatingSystems

_RELEASE_BASE = "https://github.com/mrkbac/portable-ffmpeg/releases/download/ffmpeg-9.0.2-1"

DOWNLOAD_URLS: dict[OperatingSystems, dict[Architectures, FFmpegDownload]] = {
    OperatingSystems.WINDOWS: {
        Architectures.AMD64: FFmpegDownload(
            url=f"{_RELEASE_BASE}/ffmpeg-9.0.2-windows-amd64.tar.xz",
            sha256="0e9e40b1e0305c84904163de7215b9c879f9a6aa74196045a5060cd1ca093e73",
            binary_sha256={
                "ffmpeg.exe": "c930b63cb1ee8b7e2eaf9c15161160edd5c9acad34f0303b5855c8eb142a7e8d",
                "ffprobe.exe": "075848c1bbb8b4e2e0b0ecba06e8ad06c889a8902ed219d6a9f5758c417ca108",
            },
            ffmpeg_name="ffmpeg.exe",
            ffprobe_name="ffprobe.exe",
        ),
    },
    OperatingSystems.OSX: {
        Architectures.AMD64: FFmpegDownload(
            url=f"{_RELEASE_BASE}/ffmpeg-9.0.2-osx-amd64.tar.xz",
            sha256="8b28cf14b576fa4485fe50d9f2fbc5d8fdafa14ca4d2adff85a6e52af84f4597",
            binary_sha256={
                "ffmpeg": "b25689cf2211c0582d317e849912769a1f1c93904fe102c485b5364a425633d1",
                "ffprobe": "b5df9964b0c2048318fafedcd4e3bbafbc561033cee77de8da1840685d8a9d0d",
            },
        ),
        Architectures.ARM64: FFmpegDownload(
            url=f"{_RELEASE_BASE}/ffmpeg-9.0.2-osx-arm64.tar.xz",
            sha256="38436f085276ba1325d82481aaa5d9818645fbfb3e4078c8938c06cdb8160512",
            binary_sha256={
                "ffmpeg": "2e11c6f90993cdb79fff84d3f90044d28316b310e75b3e030cfc9a54f2c9d384",
                "ffprobe": "2738aa46a7f9acbc8ab09a6715554c90f7de603171ac403726765685df6a0059",
            },
        ),
    },
    OperatingSystems.LINUX: {
        Architectures.AMD64: FFmpegDownload(
            url=f"{_RELEASE_BASE}/ffmpeg-9.0.2-linux-amd64.tar.xz",
            sha256="f78d9e9833dc773cd45ef03f20368b8cd67fd353fd8e85bb61c6aabb69ef0148",
            binary_sha256={
                "ffmpeg": "384742b75419584d065bbf372613f9f7e8ccf22525b421c16a2ee679a78ee748",
                "ffprobe": "ae9051af68f52e7ad5706b442577689c74c02da618ca1590caf1ac7199f2931c",
            },
        ),
        Architectures.ARM64: FFmpegDownload(
            url=f"{_RELEASE_BASE}/ffmpeg-9.0.2-linux-arm64.tar.xz",
            sha256="3caedf22f31b4fbd53e394ec0127d3ba7cae6b891ee5fe7b1c511015dd123077",
            binary_sha256={
                "ffmpeg": "091fe4df4902fedd20f4d5accab14d02947a531d14d789cc7e8f18b0a808e6d1",
                "ffprobe": "8e967d51f1e9e7d1c84423417e68625d267128c5014e0c20ae470f53506631ef",
            },
        ),
    },
}
