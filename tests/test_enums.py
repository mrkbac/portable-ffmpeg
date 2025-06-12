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

    def test_from_current_system_windows(self, mocker: "MockerFixture") -> None:
        """Test detection of Windows system."""
        mocker.patch("platform.system", return_value="Windows")
        result = OperatingSystems.from_current_system()
        assert result == OperatingSystems.WINDOWS

    def test_from_current_system_darwin(self, mocker: "MockerFixture") -> None:
        """Test detection of macOS (Darwin) system."""
        mocker.patch("platform.system", return_value="Darwin")
        result = OperatingSystems.from_current_system()
        assert result == OperatingSystems.OSX

    def test_from_current_system_linux(self, mocker: "MockerFixture") -> None:
        """Test detection of Linux system."""
        mocker.patch("platform.system", return_value="Linux")
        result = OperatingSystems.from_current_system()
        assert result == OperatingSystems.LINUX

    def test_from_current_system_case_insensitive(self, mocker: "MockerFixture") -> None:
        """Test that system detection is case insensitive."""
        test_cases = [
            ("windows", OperatingSystems.WINDOWS),
            ("WINDOWS", OperatingSystems.WINDOWS),
            ("darwin", OperatingSystems.OSX),
            ("DARWIN", OperatingSystems.OSX),
            ("linux", OperatingSystems.LINUX),
            ("LINUX", OperatingSystems.LINUX),
        ]

        for system_name, expected in test_cases:
            mocker.patch("platform.system", return_value=system_name)
            result = OperatingSystems.from_current_system()
            assert result == expected

    def test_from_current_system_unsupported(self, mocker: "MockerFixture") -> None:
        """Test that unsupported systems raise ValueError."""
        mocker.patch("platform.system", return_value="FreeBSD")

        with pytest.raises(ValueError, match="Unsupported operating system: freebsd"):
            OperatingSystems.from_current_system()


class TestArchitectures:
    """Tests for Architectures enum."""

    def test_enum_values(self) -> None:
        """Test that enum values are correct."""
        assert Architectures.AMD64.value == "amd64"
        assert Architectures.ARM64.value == "arm64"

    def test_from_current_architecture_x86_64(self, mocker: "MockerFixture") -> None:
        """Test detection of x86_64 architecture."""
        mocker.patch("platform.machine", return_value="x86_64")
        result = Architectures.from_current_architecture()
        assert result == Architectures.AMD64

    def test_from_current_architecture_amd64(self, mocker: "MockerFixture") -> None:
        """Test detection of amd64 architecture."""
        mocker.patch("platform.machine", return_value="amd64")
        result = Architectures.from_current_architecture()
        assert result == Architectures.AMD64

    def test_from_current_architecture_aarch64(self, mocker: "MockerFixture") -> None:
        """Test detection of aarch64 architecture."""
        mocker.patch("platform.machine", return_value="aarch64")
        result = Architectures.from_current_architecture()
        assert result == Architectures.ARM64

    def test_from_current_architecture_arm64(self, mocker: "MockerFixture") -> None:
        """Test detection of arm64 architecture."""
        mocker.patch("platform.machine", return_value="arm64")
        result = Architectures.from_current_architecture()
        assert result == Architectures.ARM64

    def test_from_current_architecture_case_insensitive(self, mocker: "MockerFixture") -> None:
        """Test that architecture detection is case insensitive."""
        test_cases = [
            ("x86_64", Architectures.AMD64),
            ("X86_64", Architectures.AMD64),
            ("amd64", Architectures.AMD64),
            ("AMD64", Architectures.AMD64),
            ("aarch64", Architectures.ARM64),
            ("AARCH64", Architectures.ARM64),
            ("arm64", Architectures.ARM64),
            ("ARM64", Architectures.ARM64),
        ]

        for machine_name, expected in test_cases:
            mocker.patch("platform.machine", return_value=machine_name)
            result = Architectures.from_current_architecture()
            assert result == expected

    def test_from_current_architecture_unsupported(self, mocker: "MockerFixture") -> None:
        """Test that unsupported architectures raise ValueError."""
        mocker.patch("platform.machine", return_value="sparc")

        with pytest.raises(ValueError, match="Unsupported architecture: sparc"):
            Architectures.from_current_architecture()
