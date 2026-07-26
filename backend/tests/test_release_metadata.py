"""Repository-level v1.0 release metadata checks."""

import subprocess
import sys
from pathlib import Path


def test_release_metadata_and_documentation_are_consistent() -> None:
    project_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts" / "check_release.py"),
            "--allow-pending",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
