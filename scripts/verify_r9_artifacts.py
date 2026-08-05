#!/usr/bin/env python3
"""Verify every R9 artifact against the SHA-256 manifest.

Fails on a hash mismatch, on a missing file, and on any file inside the R9
results directory that the manifest does not cover.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"
MANIFEST = OUTDIR / "artifact_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if not MANIFEST.exists():
        print(f"MISSING MANIFEST: {MANIFEST}")
        return 1
    manifest = json.loads(MANIFEST.read_text())
    files = manifest["files"]

    problems: list[str] = []
    for rel, expected in sorted(files.items()):
        path = REPO_ROOT / rel
        if not path.exists():
            problems.append(f"missing: {rel}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            problems.append(f"hash mismatch: {rel}\n    expected {expected}\n    actual   {actual}")

    covered = set(files)
    for path in sorted(OUTDIR.rglob("*")):
        if path.is_file() and path.name != "artifact_manifest.json":
            rel = str(path.relative_to(REPO_ROOT))
            if rel not in covered:
                problems.append(f"uncovered result file: {rel}")

    if problems:
        print("R9 ARTIFACT VERIFICATION: FAILED")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"R9 ARTIFACT VERIFICATION: PASSED ({len(files)} files hashed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
