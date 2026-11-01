"""Options for checking unpublished release artifacts locally."""

from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Allow integration tests to consume exact local release TAR.XZ archives before publication."""
    parser.addoption(
        "--release-dir",
        type=Path,
        help="Directory of prepared FFmpeg TAR.XZ archives",
    )
