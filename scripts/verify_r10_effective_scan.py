#!/usr/bin/env python3
"""R10 Phase 7: Auditability and manifest verification script.

In default mode (no arguments), verifies that every file listed in
results/r10_effective_ctau_g_br_scan/artifact_manifest.json exists and
matches its recorded SHA-256 digest. Fails with non-zero exit code on missing
files or mismatches. Does NOT modify artifact_manifest.json unless --write is set.

When --write is passed, regenerates artifact_manifest.json from current repository files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"
MANIFEST_PATH = OUT_DIR / "artifact_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_artifacts() -> dict[str, str]:
    files_to_hash = [
        REPO_ROOT / "schemas" / "effective_h2_scan_point.schema.json",
        REPO_ROOT / "configs" / "r10_effective_scan.json",
        REPO_ROOT / "scripts" / "r10_production_scan.py",
        REPO_ROOT / "scripts" / "r10_ctau_efficiency_scan.py",
        REPO_ROOT / "scripts" / "r10_build_effective_grid.py",
        REPO_ROOT / "scripts" / "r10_recompute_grid.py",
        REPO_ROOT / "scripts" / "r10_make_figures.py",
        REPO_ROOT / "scripts" / "verify_r10_effective_scan.py",
        OUT_DIR / "production_vs_g.csv",
        OUT_DIR / "efficiency_vs_ctau.csv",
        OUT_DIR / "effective_grid.csv",
        OUT_DIR / "result_summary.json",
        OUT_DIR / "efficiency_vs_ctau.png",
        OUT_DIR / "nexpected_3d_ctau_g_br.png",
        OUT_DIR / "nexpected_ctau_vs_g_br_baseline.png",
        OUT_DIR / "nexpected_g_vs_br_ctau_baseline.png",
        OUT_DIR / "nexpected_ctau_vs_br_g_atlas.png",
        OUT_DIR / "nexpected_3d_interactive.html",
        REPO_ROOT / "docs" / "R10_EFFECTIVE_CTAU_G_BR_RESULT.md",
        REPO_ROOT / "docs" / "R10_PRESENTATION_INSERT_ES.md",
    ]

    # Include all generated cards and logs
    if (OUT_DIR / "cards").exists():
        files_to_hash.extend(sorted((OUT_DIR / "cards").glob("*.cmnd")))
    if (OUT_DIR / "logs").exists():
        files_to_hash.extend(sorted((OUT_DIR / "logs").glob("*.log")))
        files_to_hash.extend(sorted((OUT_DIR / "logs").glob("*.json")))

    manifest = {}
    missing_files = []
    for p in sorted(files_to_hash):
        if p.exists():
            rel_path = str(p.relative_to(REPO_ROOT))
            manifest[rel_path] = sha256_file(p)
        else:
            missing_files.append(str(p.relative_to(REPO_ROOT)))

    if missing_files:
        raise FileNotFoundError(f"Missing required artifact files for manifest generation: {missing_files}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate artifact_manifest.json")
    args = parser.parse_args()

    if args.write:
        manifest = collect_artifacts()
        manifest_payload = {
            "schema": "hep_cross.r10.artifact_manifest.v1",
            "study_id": "r10_effective_ctau_g_br_scan",
            "interpretation": "EFFECTIVE_PHENOMENOLOGICAL",
            "n_files": len(manifest),
            "artifacts": manifest,
        }
        MANIFEST_PATH.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] Wrote {MANIFEST_PATH} with {len(manifest)} file hashes.")
        return 0

    # Verification mode: check existing committed manifest strictly
    if not MANIFEST_PATH.exists():
        print(f"[FAIL] Manifest file does not exist: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    try:
        manifest_payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        print(f"[FAIL] Malformed manifest JSON: {err}", file=sys.stderr)
        return 1

    artifacts = manifest_payload.get("artifacts", {})
    if not artifacts:
        print(f"[FAIL] Manifest contains no artifacts", file=sys.stderr)
        return 1

    errors = []
    for rel_path, expected_hash in artifacts.items():
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            errors.append(f"Missing file: {rel_path}")
            continue
        actual_hash = sha256_file(full_path)
        if actual_hash != expected_hash:
            errors.append(f"Hash mismatch for {rel_path}: actual {actual_hash} vs expected {expected_hash}")

    if errors:
        print(f"[FAIL] Manifest verification failed ({len(errors)} errors):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"[PASS] verify_r10_effective_scan: all {len(artifacts)} manifest hashes verified successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
