"""Shared test helpers."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_script(args: list[str]) -> subprocess.CompletedProcess:
    """Run a repo script as a subprocess with src/ on PYTHONPATH, asserting success."""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [sys.executable, *args], cwd=ROOT, env=env, text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr
    return result
