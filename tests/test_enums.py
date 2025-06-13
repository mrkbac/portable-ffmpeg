"""Tests for the enums module."""

from typing import TYPE_CHECKING

import pytest

from portable_ffmpeg.enums import Architectures, OperatingSystems

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestOperatingSystems:
    """Tests for OperatingSystems enum."""

    def test_enum_values(self) -> None:
        """Test that enum values are correct."""
        assert OperatingSystems.WINDOWS.value == "windows"
        assert OperatingSystems.OSX.value == "osx"
        assert OperatingSystems.LINUX.value == "linux"

    @pytest.mark.parametrize(
        ("platform_name", "expected"),
        [
            ("Windows", OperatingSystems.WINDOWS),
            ("windows", OperatingSystems.WINDOWS),
            ("Darwin", OperatingSystems.OSX),
            ("darwin", OperatingSystems.OSX),
            ("Linux", OperatingSystems.LINUX),
            ("linux", OperatingSystems.LINUX),
        ],
    )
    def test_from_current_system(
        self, platform_name: str, expected: OperatingSystems, mocker: "MockerFixture"
    ) -> None:
        """Test OS detection works for various platform names."""
        mocker.patch("platform.system", return_value=platform_name)
        result = OperatingSystems.from_current_system()
        assert result == expected

    def test_from_current_system_unsupported(self, mocker: "MockerFixture") -> None:
        """Test that unsupported OS raises ValueError."""
        mocker.patch("platform.system", return_value="FreeBSD")
        with pytest.raises(ValueError, match="Unsupported operating system"):
            OperatingSystems.from_current_system()


class TestArchitectures:
    """Tests for Architectures enum."""

    def test_enum_values(self) -> None:
        """Test that enum values are correct."""
        assert Architectures.AMD64.value == "amd64"
        assert Architectures.ARM64.value == "arm64"

    @pytest.mark.parametrize(
        ("arch_name", "expected"),
        [
            ("x86_64", Architectures.AMD64),
            ("amd64", Architectures.AMD64),
            ("X86_64", Architectures.AMD64),
            ("AMD64", Architectures.AMD64),
            ("aarch64", Architectures.ARM64),
            ("arm64", Architectures.ARM64),
            ("AARCH64", Architectures.ARM64),
            ("ARM64", Architectures.ARM64),
        ],
    )
    def test_from_current_architecture(
        self, arch_name: str, expected: Architectures, mocker: "MockerFixture"
    ) -> None:
        """Test architecture detection works for various arch names."""
        mocker.patch("platform.machine", return_value=arch_name)
        result = Architectures.from_current_architecture()
        assert result == expected

    def test_from_current_architecture_unsupported(self, mocker: "MockerFixture") -> None:
        """Test that unsupported architecture raises ValueError."""
        mocker.patch("platform.machine", return_value="sparc")
        with pytest.raises(ValueError, match="Unsupported architecture"):
            Architectures.from_current_architecture()
