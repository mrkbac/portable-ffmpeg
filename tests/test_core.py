"""Unit tests for core module functionality."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from portable_ffmpeg.core import get_ffmpeg, print_paths, run_ffmpeg, run_ffprobe
from portable_ffmpeg.enums import FFmpegVersions

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unsupported_platform_real_error(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported operating system with real error path."""
        # Mock to return an unsupported OS that reaches the error in core.py
        mocker.patch(
            "portable_ffmpeg.enums.OperatingSystems.from_current_system",
            return_value=mocker.Mock(value="FreeBSD"),
        )
        mocker.patch(
            "portable_ffmpeg.enums.Architectures.from_current_architecture",
            return_value=mocker.Mock(value="sparc"),
        )

        with pytest.raises(ValueError, match="Unsupported operating system"):
            get_ffmpeg()

    def test_unsupported_architecture_real_error(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported architecture with real error path."""
        from portable_ffmpeg.enums import OperatingSystems

        # Mock to return supported OS but unsupported architecture
        fake_os = OperatingSystems.OSX
        fake_arch = mocker.Mock(value="sparc")

        mocker.patch(
            "portable_ffmpeg.enums.OperatingSystems.from_current_system", return_value=fake_os
        )
        mocker.patch(
            "portable_ffmpeg.enums.Architectures.from_current_architecture", return_value=fake_arch
        )

        with pytest.raises(ValueError, match=r"Unsupported OperatingSystems\.OSX architecture"):
            get_ffmpeg()

    def test_unsupported_platform(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported operating system with enum error."""
        mocker.patch(
            "portable_ffmpeg.enums.OperatingSystems.from_current_system",
            side_effect=ValueError("Unsupported"),
        )

        with pytest.raises(ValueError, match="Unsupported"):
            get_ffmpeg()

    def test_unsupported_architecture(self, mocker: "MockerFixture") -> None:
        """Test behavior on unsupported architecture with enum error."""
        mocker.patch(
            "portable_ffmpeg.enums.Architectures.from_current_architecture",
            side_effect=ValueError("Unsupported"),
        )

        with pytest.raises(ValueError, match="Unsupported"):
            get_ffmpeg()

    def test_unsupported_version(self, mocker: "MockerFixture") -> None:
        """Test behavior with unsupported FFmpeg version."""
        unsupported_version = mocker.Mock(value="8")
        with pytest.raises(ValueError, match="Unsupported FFmpeg version"):
            get_ffmpeg(unsupported_version)


class TestCliEntryPoints:
    """Test CLI entry point functions."""

    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("subprocess.run")
    def test_run_ffmpeg(self, mock_subprocess_run: MagicMock, mock_get_ffmpeg: MagicMock) -> None:
        """Test run_ffmpeg entry point."""
        mock_path = Path("/cache/ffmpeg")
        mock_get_ffmpeg.return_value = (mock_path, Path("/cache/ffprobe"))

        with patch.object(sys, "argv", ["script", "-version"]):
            run_ffmpeg()

        mock_subprocess_run.assert_called_once_with([str(mock_path), "-version"], check=False)

    @patch("portable_ffmpeg.core.get_ffmpeg")
    @patch("subprocess.run")
    def test_run_ffprobe(self, mock_subprocess_run: MagicMock, mock_get_ffmpeg: MagicMock) -> None:
        """Test run_ffprobe entry point."""
        mock_path = Path("/cache/ffprobe")
        mock_get_ffmpeg.return_value = (Path("/cache/ffmpeg"), mock_path)

        with patch.object(sys, "argv", ["script", "-version"]):
            run_ffprobe()

        mock_subprocess_run.assert_called_once_with([str(mock_path), "-version"], check=False)

    @patch("portable_ffmpeg.core.get_ffmpeg")
    def test_print_paths(
        self, mock_get_ffmpeg: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test print_paths entry point."""
        ffmpeg_path = Path("/cache/ffmpeg")
        ffprobe_path = Path("/cache/ffprobe")
        mock_get_ffmpeg.return_value = (ffmpeg_path, ffprobe_path)

        print_paths()

        captured = capsys.readouterr()
        assert f"FFmpeg: {ffmpeg_path}" in captured.out
        assert f"FFprobe: {ffprobe_path}" in captured.out


@pytest.mark.parametrize("error", [ValueError, ConnectionError])
def test_failed_install_never_enters_cache(
    tmp_path: Path, mocker: "MockerFixture", error: type[Exception]
) -> None:
    """A failed download or validation leaves no reusable partial installation."""
    from portable_ffmpeg import core
    from portable_ffmpeg.config import DOWNLOAD_URLS
    from portable_ffmpeg.enums import Architectures, OperatingSystems

    config = DOWNLOAD_URLS[OperatingSystems.OSX][Architectures.ARM64]
    mocker.patch.object(core, "CACHE_DIR", tmp_path)
    mocker.patch.object(OperatingSystems, "from_current_system", return_value=OperatingSystems.OSX)
    mocker.patch.object(
        Architectures, "from_current_architecture", return_value=Architectures.ARM64
    )

    def extract(folder: Path) -> None:
        (folder / "ffmpeg").write_bytes(b"partial")
        msg = "installation failed"
        raise error(msg)

    mocker.patch.object(config, "download_files", side_effect=extract)
    with pytest.raises(error):
        get_ffmpeg()
    assert not list(tmp_path.iterdir())


def test_empty_cached_binary_is_replaced(tmp_path: Path, mocker: "MockerFixture") -> None:
    """An empty cached executable triggers a complete replacement of both files."""
    from portable_ffmpeg import core
    from portable_ffmpeg.config import DOWNLOAD_URLS
    from portable_ffmpeg.enums import Architectures, OperatingSystems

    config = DOWNLOAD_URLS[OperatingSystems.OSX][Architectures.ARM64]
    mocker.patch.object(core, "CACHE_DIR", tmp_path)
    mocker.patch.object(OperatingSystems, "from_current_system", return_value=OperatingSystems.OSX)
    mocker.patch.object(
        Architectures, "from_current_architecture", return_value=Architectures.ARM64
    )
    cache = tmp_path / f"osx-arm64-{config.cache_id}"
    cache.mkdir()
    (cache / "ffmpeg").touch()
    (cache / "ffprobe").write_bytes(b"old")

    def extract(folder: Path) -> None:
        assert not cache.exists()
        for name in ("ffmpeg", "ffprobe"):
            (folder / name).write_bytes(b"new")

    download = mocker.patch.object(config, "download_files", side_effect=extract)
    paths = get_ffmpeg()
    assert all(path.read_bytes() == b"new" for path in paths)
    assert get_ffmpeg(FFmpegVersions.V9) == paths
    download.assert_called_once()
    assert list(tmp_path.iterdir()) == [cache]


@pytest.mark.parametrize("failure", ["none", "archive", "binary", "missing"])
def test_bundled_payload_never_uses_network(
    tmp_path: Path, mocker: "MockerFixture", failure: str
) -> None:
    """Prefer an offline payload, verify both identities, and never fall back on a bad bundle."""
    import urllib.error
    import urllib.request

    from portable_ffmpeg import core
    from portable_ffmpeg.enums import Architectures, OperatingSystems
    from tests.test_downloaders import make_tar

    bundle = tmp_path / "full"
    bundle.mkdir()
    archive = bundle / "ffmpeg.tar.xz"
    config = make_tar(
        archive, [("ffmpeg", b"encoder"), ("ffprobe", b"probe"), ("SOURCE.txt", b"sources")]
    )
    config.url = "https://must-not-download.invalid/release.tar.xz"
    cache = tmp_path / "cache"
    mocker.patch.object(core, "CACHE_DIR", cache)
    mocker.patch.object(
        core, "DOWNLOAD_URLS", {OperatingSystems.OSX: {Architectures.ARM64: config}}
    )
    mocker.patch.object(core, "files", return_value=bundle)
    mocker.patch.object(OperatingSystems, "from_current_system", return_value=OperatingSystems.OSX)
    mocker.patch.object(
        Architectures, "from_current_architecture", return_value=Architectures.ARM64
    )
    if failure == "archive":
        archive.write_bytes(b"changed archive")
    elif failure == "binary":
        config.binary_sha256["ffprobe"] = "0" * 64
    elif failure == "missing":
        archive.unlink()
    urlopen = mocker.patch(
        "portable_ffmpeg.downloaders.urllib.request.urlopen", wraps=urllib.request.urlopen
    )
    if failure == "none":
        paths = get_ffmpeg()
        assert paths[0].read_bytes() == b"encoder"
        assert paths[1].read_bytes() == b"probe"
        assert (paths[0].parent / "SOURCE.txt").read_bytes() == b"sources"
        assert get_ffmpeg(FFmpegVersions.V9) == paths
        urlopen.assert_called_once()
    else:
        error = urllib.error.URLError if failure == "missing" else ValueError
        with pytest.raises(error):
            get_ffmpeg()
        assert not list(cache.iterdir())
    assert all(call.args[0].full_url.startswith("file:") for call in urlopen.call_args_list)


def test_broken_bundle_import_never_falls_back(tmp_path: Path, mocker: "MockerFixture") -> None:
    """An installed package with an import failure must not silently use the network."""
    from portable_ffmpeg import core
    from portable_ffmpeg.config import DOWNLOAD_URLS
    from portable_ffmpeg.enums import Architectures, OperatingSystems

    config = DOWNLOAD_URLS[OperatingSystems.OSX][Architectures.ARM64]
    mocker.patch.object(core, "CACHE_DIR", tmp_path)
    mocker.patch.object(OperatingSystems, "from_current_system", return_value=OperatingSystems.OSX)
    mocker.patch.object(
        Architectures, "from_current_architecture", return_value=Architectures.ARM64
    )
    mocker.patch.object(
        core, "files", side_effect=ModuleNotFoundError("broken bundle", name="missing_bundle_code")
    )
    download = mocker.patch.object(config, "download_files")
    with pytest.raises(ModuleNotFoundError, match="broken bundle"):
        get_ffmpeg()
    download.assert_not_called()
    assert not list(tmp_path.iterdir())
