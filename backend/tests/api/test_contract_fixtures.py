"""Shared API v1 fixture drift check."""

import subprocess
import sys
from pathlib import Path


def test_shared_api_contract_fixtures_are_current() -> None:
    project_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts" / "api_contract_fixtures.py"),
            "--check",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
