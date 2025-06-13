"""Run tests with coverage and generate summary for GitHub Actions."""

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run tests and generate summary based on arguments."""
    print("Running tests with coverage...")

    # Run pytest with coverage, capturing output
    result = subprocess.run(
        [  # noqa: S607
            "pytest",
            "--cov=src/portable_ffmpeg",
            "--cov-report=term-missing",
            "--cov-fail-under=95",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    # Print output to console
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Write summary to GitHub Actions if environment variable is set
    if summary_file := os.environ.get("GITHUB_STEP_SUMMARY"):
        print(f"Writing summary to {summary_file}")
        with Path(summary_file).open("w") as f:
            f.write("# Test Coverage Summary\n\n")
            f.write("```text\n")
            if result.stdout:
                f.write(result.stdout)
            else:
                f.write("No coverage data available\n")
            f.write("```\n")

    # Exit with the same code as pytest
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
