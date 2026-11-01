"""Upstream archive handling used only while preparing releases."""

import hashlib
import shutil
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from portable_ffmpeg.downloaders import _download_file
from portable_ffmpeg.enums import Architectures, OperatingSystems


def _extract_zip_files(archive: Path, outfolder: Path, target_names: tuple[str, str]) -> None:
    """Copy only the executables, discarding archive directory paths."""
    with zipfile.ZipFile(archive) as package:
        for member in package.infolist():
            name = Path(member.filename).name
            if not member.is_dir() and name in target_names:
                with package.open(member) as source, (outfolder / name).open("wb") as output:
                    shutil.copyfileobj(source, output)


def _extract_tar_files(archive: Path, outfolder: Path, target_names: tuple[str, str]) -> None:
    """Copy regular executables without following archive links or directory paths."""
    with tarfile.open(archive) as package:
        for member in package:
            name = Path(member.name).name
            if member.isfile() and name in target_names:
                source = package.extractfile(member)
                if source is not None:
                    with source, (outfolder / name).open("wb") as output:
                        shutil.copyfileobj(source, output)


@dataclass
class Archive:
    """A pinned archive with a mandatory SHA-256 digest."""

    url: str
    sha256: str


@dataclass
class UpstreamDownload:
    """The archives and executable names for one platform."""

    archives: tuple[Archive, ...]
    ffmpeg_name: str = "ffmpeg"
    ffprobe_name: str = "ffprobe"

    @property
    def cache_id(self) -> str:
        """Invalidate the cache when URLs, digests, or executable names change."""
        return hashlib.sha256(repr(self).encode()).hexdigest()[:16]

    def download_files(self, outfolder: Path) -> None:
        """Download verified archives and extract both platform executables."""
        names = (self.ffmpeg_name, self.ffprobe_name)
        with tempfile.TemporaryDirectory() as tmp_dir:
            for archive in self.archives:
                path = Path(tmp_dir) / "archive"
                _download_file(archive.url, path, archive.sha256)
                if archive.url.endswith(".zip"):
                    _extract_zip_files(path, outfolder, names)
                else:
                    _extract_tar_files(path, outfolder, names)
        for name in names:
            path = outfolder / name
            if not path.is_file() or not path.stat().st_size:
                msg = f"FFmpeg archive is missing a non-empty {name} executable"
                raise ValueError(msg)
            if sys.platform != "win32":
                path.chmod(0o755)


_BTBN_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-10-31-12-59"
_BTBN_BUILD = "ffmpeg-n9.0.2-39-g7adfbe40dc"
_MACOS_AMD64 = "https://ffmpeg.martin-riedl.de/download/macos/amd64/1789931006_9.0.2"
_MACOS_ARM64 = "https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2"

DOWNLOAD_URLS: dict[OperatingSystems, dict[Architectures, UpstreamDownload]] = {
    OperatingSystems.WINDOWS: {
        Architectures.AMD64: UpstreamDownload(
            archives=(
                Archive(
                    f"{_BTBN_BASE}/{_BTBN_BUILD}-win64-gpl-9.0.zip",
                    "693f3e224bc184b40524a62ca47526cfebaf2504414021b92fe75f677ad868b9",
                ),
            ),
            ffmpeg_name="ffmpeg.exe",
            ffprobe_name="ffprobe.exe",
        ),
    },
    OperatingSystems.OSX: {
        Architectures.AMD64: UpstreamDownload(
            archives=(
                Archive(
                    f"{_MACOS_AMD64}/ffmpeg.zip",
                    "7c6b4125b191cbf773832dc51f424cf2b6bb7da43007d1e066f95909e47cacd4",
                ),
                Archive(
                    f"{_MACOS_AMD64}/ffprobe.zip",
                    "2322438ed2f6319a691291b247d09c69dcaa3a982460d1f269a7e1af335cfdfd",
                ),
            ),
        ),
        Architectures.ARM64: UpstreamDownload(
            archives=(
                Archive(
                    f"{_MACOS_ARM64}/ffmpeg.zip",
                    "c8ed4c4e6978a03c485edbfe4e0a5dc2380f8a30bba5150531b31b094492d924",
                ),
                Archive(
                    f"{_MACOS_ARM64}/ffprobe.zip",
                    "fcbe839537485eaee7a7a8bc5cbc0f90d53617e80943e8a5b2e31cb851197ea6",
                ),
            ),
        ),
    },
    OperatingSystems.LINUX: {
        Architectures.AMD64: UpstreamDownload(
            archives=(
                Archive(
                    f"{_BTBN_BASE}/{_BTBN_BUILD}-linux64-gpl-9.0.tar.xz",
                    "73e29a56974ae5a651133a04584c7483b21afe941e17dc91d79814a758b608d3",
                ),
            ),
        ),
        Architectures.ARM64: UpstreamDownload(
            archives=(
                Archive(
                    f"{_BTBN_BASE}/{_BTBN_BUILD}-linuxarm64-gpl-9.0.tar.xz",
                    "6cad88ae5bcec356cfc5d7979a036cc4007128201928a0cf243df3db483276cc",
                ),
            ),
        ),
    },
}
