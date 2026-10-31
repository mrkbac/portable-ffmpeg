"""Download and verify the common FFmpeg release TAR.XZ."""

import hashlib
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

_DOWNLOAD_CHUNK_SIZE = 1024 * 1024
_DOWNLOAD_USER_AGENT = "portable-ffmpeg/0.5 (+https://github.com/mrkbac/portable-ffmpeg)"


def _download_file(url: str, file_path: Path, sha256: str) -> None:
    """Stream an archive to disk and require its expected checksum."""
    print(f"Downloading {url}")
    request = urllib.request.Request(url, headers={"User-Agent": _DOWNLOAD_USER_AGENT})
    digest = hashlib.sha256()
    downloaded = 0
    with urllib.request.urlopen(request, timeout=30) as response, file_path.open("wb") as output:
        content_length = response.headers.get("Content-Length")
        while chunk := response.read(_DOWNLOAD_CHUNK_SIZE):
            output.write(chunk)
            digest.update(chunk)
            downloaded += len(chunk)
    if content_length is not None and downloaded != int(content_length):
        msg = f"Incomplete download from {url}: expected {content_length} bytes, got {downloaded}"
        raise ValueError(msg)
    if digest.hexdigest() != sha256:
        msg = f"SHA-256 mismatch for {url}"
        raise ValueError(msg)


@dataclass
class FFmpegDownload:
    """One checksum-verified TAR.XZ with executables at its root."""

    url: str
    sha256: str
    binary_sha256: dict[str, str]
    ffmpeg_name: str = "ffmpeg"
    ffprobe_name: str = "ffprobe"

    @property
    def cache_id(self) -> str:
        """Invalidate the cache when the release artifact changes."""
        return hashlib.sha256(repr(self).encode()).hexdigest()[:16]

    def download_files(self, outfolder: Path, *, archive_url: str | None = None) -> None:
        """Verify the archive and executable bytes, retaining root notices and source references."""
        executables = (self.ffmpeg_name, self.ffprobe_name)
        if set(self.binary_sha256) != set(executables):
            msg = "Expected SHA-256 digests for both ffmpeg and ffprobe"
            raise ValueError(msg)
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive = Path(tmp_dir) / "archive.tar.xz"
            _download_file(archive_url or self.url, archive, self.sha256)
            seen: set[str] = set()
            with tarfile.open(archive, "r|xz") as package:
                for member in package:
                    name = member.name
                    if (
                        not member.isfile()
                        or name != Path(name).name
                        or "/" in name
                        or "\\" in name
                        or name in {"", ".", ".."}
                    ):
                        continue
                    if name in seen:
                        msg = f"Duplicate root file in FFmpeg TAR.XZ: {name}"
                        raise ValueError(msg)
                    seen.add(name)
                    source = package.extractfile(member)
                    if source is None:
                        msg = f"Cannot read FFmpeg TAR.XZ member: {name}"
                        raise ValueError(msg)
                    with source, (outfolder / name).open("wb") as output:
                        shutil.copyfileobj(source, output)
            for name in executables:
                path = outfolder / name
                if name not in seen or not path.stat().st_size:
                    msg = f"FFmpeg TAR.XZ must contain one non-empty root-level {name} executable"
                    raise ValueError(msg)
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if digest != self.binary_sha256[name]:
                    msg = f"SHA-256 mismatch for {name} executable"
                    raise ValueError(msg)
                if sys.platform != "win32":
                    path.chmod(0o755)
