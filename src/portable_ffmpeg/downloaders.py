"""Download classes for different FFmpeg binary formats."""

import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


def _download_file(url: str, file_path: Path | str) -> None:
    """Download a file from a URL."""
    print(f"🔽 Downloading from {url}")
    last_value = 0

    def reporthook(block_num: int, block_size: int, total_size: int) -> None:
        nonlocal last_value
        if total_size > 0:
            downloaded = block_num * block_size
            percent = downloaded * 100 // total_size
            if percent != last_value:
                last_value = percent
                if percent == 100:
                    sys.stdout.write("\r✅ Download complete!\n")
                else:
                    sys.stdout.write(f"\r🔽 {percent:3d}%")
                sys.stdout.flush()
        else:
            total = block_num * block_size
            if last_value != total:
                last_value = total
                sys.stdout.write(f"\r🔽 {block_num * block_size} bytes")
                sys.stdout.flush()

    # Kick off download
    urllib.request.urlretrieve(url, file_path, reporthook)


def _extract_zip_files(zip_file: Path, outfolder: Path, target_names: list[str]) -> list[Path]:
    """Extract specific files from a zip archive."""
    extracted_files = []
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        for member in zip_ref.namelist():
            filename = Path(member).name
            if filename in target_names:
                # Extract the file to outfolder with just the filename
                member_data = zip_ref.read(member)
                output_path = outfolder / filename
                output_path.write_bytes(member_data)
                # Set executable permissions on Unix systems
                if sys.platform != "win32":
                    output_path.chmod(0o755)
                extracted_files.append(output_path)
    return extracted_files


def _extract_tar_files(tar_file: Path, outfolder: Path, target_names: list[str]) -> list[Path]:
    """Extract specific files from a tar archive."""
    extracted_files = []
    with tarfile.open(tar_file, "r:*") as tar_ref:
        for member in tar_ref.getmembers():
            if member.isfile():
                filename = Path(member.name).name
                if filename in target_names:
                    # Extract the file to outfolder with just the filename
                    extracted_file = tar_ref.extractfile(member)
                    if extracted_file:
                        output_path = outfolder / filename
                        output_path.write_bytes(extracted_file.read())
                        # Set executable permissions on Unix systems
                        if sys.platform != "win32":
                            output_path.chmod(0o755)
                        extracted_files.append(output_path)
    return extracted_files


@dataclass
class BaseFFmpegDownloader(ABC):
    """Base class for downloading FFmpeg binaries."""

    ffmpeg_name: str
    ffprobe_name: str

    @abstractmethod
    def download_files(self, outfolder: Path) -> tuple[Path, Path]:
        """Download and extract the FFmpeg and FFprobe binaries."""


@dataclass
class FFmpegDownloadSingleZip(BaseFFmpegDownloader):
    """Configuration for downloading ffmpeg and ffprobe binaries."""

    url: str

    def download_files(self, outfolder: Path) -> tuple[Path, Path]:
        """Download and extract zip archive containing both binaries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = Path(tmp_dir) / "download.zip"
            _download_file(self.url, tmp_file)

            _extract_zip_files(
                zip_file=tmp_file,
                outfolder=outfolder,
                target_names=[self.ffmpeg_name, self.ffprobe_name],
            )

        return outfolder / self.ffmpeg_name, outfolder / self.ffprobe_name


@dataclass
class FFmpegDownloadSingleTar(BaseFFmpegDownloader):
    """Configuration for downloading ffmpeg and ffprobe binaries as a single tar archive."""

    url: str

    def download_files(self, outfolder: Path) -> tuple[Path, Path]:
        """Download and extract tar archive containing both binaries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file = Path(tmp_dir) / "download.tar.xz"
            _download_file(self.url, tmp_file)

            _extract_tar_files(
                tar_file=tmp_file,
                outfolder=outfolder,
                target_names=[self.ffmpeg_name, self.ffprobe_name],
            )

        return outfolder / self.ffmpeg_name, outfolder / self.ffprobe_name


@dataclass
class FFmpegDownloadTwoZips(BaseFFmpegDownloader):
    """Configuration for downloading ffmpeg and ffprobe binaries as separate zip files."""

    ffmpeg_url: str
    ffprobe_url: str

    def download_files(self, outfolder: Path) -> tuple[Path, Path]:
        """Download and extract two separate zip files for ffmpeg and ffprobe."""
        target_binaries = {self.ffmpeg_url: self.ffmpeg_name, self.ffprobe_url: self.ffprobe_name}

        for url, target_name in target_binaries.items():
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_file = Path(tmp_dir) / f"{target_name}.zip"
                _download_file(url, tmp_file)

                _extract_zip_files(
                    zip_file=tmp_file,
                    outfolder=outfolder,
                    target_names=[target_name],
                )

        return outfolder / self.ffmpeg_name, outfolder / self.ffprobe_name
