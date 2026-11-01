"""Check source-complete release preparation with small, local inputs."""

import hashlib
import json
import lzma
import tarfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from portable_ffmpeg.enums import Architectures, OperatingSystems
from scripts import prepare_release
from scripts.upstream import Archive, UpstreamDownload

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def read_member(package: tarfile.TarFile, name: str) -> bytes:
    """Read a required regular member with an explicit assertion for type narrowing."""
    source = package.extractfile(name)
    assert source is not None
    with source:
        return source.read()


@pytest.fixture
def source_inputs(tmp_path: Path, mocker: "MockerFixture") -> Path:
    """Supply synthetic reviewed source inputs and verified local binaries."""
    archive = tmp_path / "upstream.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("bin/ffmpeg", b"encoder")
        package.writestr("bin/ffprobe", b"probe")
    config = UpstreamDownload(
        (Archive(archive.as_uri(), hashlib.sha256(archive.read_bytes()).hexdigest()),)
    )
    mocker.patch.object(
        prepare_release, "DOWNLOAD_URLS", {OperatingSystems.LINUX: {Architectures.AMD64: config}}
    )
    sources = tmp_path / "sources"
    sources.mkdir()
    with zipfile.ZipFile(sources / "sources.zip", "w") as package:
        package.writestr("README", "Synthetic source fixture, not a real distribution")
    (sources / "notices.txt").write_text("Synthetic license and copyright fixture")
    manifest = {
        "ffmpeg_version": "9.0.2",
        "review_complete": True,
        "files": [
            {"filename": path.name, "sha256": prepare_release.sha256(path)}
            for path in sorted(sources.iterdir())
        ],
        "platforms": {
            "linux-amd64": {
                "source_files": ["sources.zip"],
                "notice_file": "notices.txt",
                "binary_sha256": {
                    "ffmpeg": hashlib.sha256(b"encoder").hexdigest(),
                    "ffprobe": hashlib.sha256(b"probe").hexdigest(),
                },
            }
        },
    }
    (sources / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest))
    return sources


def test_common_archive_contract(tmp_path: Path, source_inputs: Path) -> None:
    """Keep binaries, notices and source pointers together; cover every release asset by SHA."""
    output = tmp_path / "release"
    prepare_release.prepare_release(output, source_inputs)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["publication_ready"] is True
    artifact = manifest["artifacts"][0]
    archive = output / artifact["filename"]
    assert artifact["sha256"] == prepare_release.sha256(archive)
    checksums = dict(
        line.split()[::-1] for line in (output / "SHA256SUMS").read_text().splitlines()
    )
    assert set(checksums) == {path.name for path in output.iterdir()} - {"SHA256SUMS"}
    assert all(
        prepare_release.sha256(output / name) == digest for name, digest in checksums.items()
    )
    with tarfile.open(archive) as package:
        assert set(package.getnames()) == {
            "ffmpeg",
            "ffprobe",
            "FFmpeg-GPL-3.0.txt",
            "PROVENANCE.json",
            "SOURCE.txt",
            "THIRD_PARTY_NOTICES.txt",
        }
        assert read_member(package, "ffmpeg") == b"encoder"
        assert read_member(package, "ffprobe") == b"probe"
        assert package.getmember("ffmpeg").mode == 0o755
        assert b"sources.zip" in read_member(package, "SOURCE.txt")
        assert (
            read_member(package, "THIRD_PARTY_NOTICES.txt")
            == (source_inputs / "notices.txt").read_bytes()
        )
        assert (
            json.loads(read_member(package, "PROVENANCE.json"))["binary_sha256"]
            == artifact["binary_sha256"]
        )
    other = tmp_path / "second-release"
    prepare_release.prepare_release(other, source_inputs)
    assert (other / archive.name).read_bytes() == archive.read_bytes()
    with pytest.raises(lzma.LZMAError, match="Memory usage limit"):
        lzma.decompress(archive.read_bytes(), memlimit=128 * 1024**2)


def test_existing_output_is_preserved(tmp_path: Path) -> None:
    """Never replace previously prepared or user-owned artifacts."""
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep"
    sentinel.write_text("existing artifact")
    with pytest.raises(FileExistsError, match="Output already exists"):
        prepare_release.prepare_release(output, tmp_path / "absent")
    assert sentinel.read_text() == "existing artifact"


@pytest.mark.parametrize(
    "problem", ["review", "source-hash", "binary-hash", "missing-source", "unsafe-path"]
)
def test_incomplete_inputs_never_produce_a_release(
    tmp_path: Path, source_inputs: Path, problem: str
) -> None:
    """Publication requires reviewed sources and exact source/binary identities."""
    path = source_inputs / "SOURCE_MANIFEST.json"
    manifest = json.loads(path.read_text())
    if problem == "review":
        manifest["review_complete"] = False
    elif problem == "source-hash":
        manifest["files"][0]["sha256"] = "0" * 64
    elif problem == "binary-hash":
        manifest["platforms"]["linux-amd64"]["binary_sha256"]["ffmpeg"] = "0" * 64
    elif problem == "missing-source":
        manifest["platforms"]["linux-amd64"]["source_files"] = []
    else:
        manifest["files"][0]["filename"] = "../outside"
    path.write_text(json.dumps(manifest))
    output = tmp_path / "release"
    with pytest.raises(ValueError):
        prepare_release.prepare_release(output, source_inputs)
    assert not output.exists()
    assert not list(tmp_path.glob(".ffmpeg-release-*"))
