#!/usr/bin/env python3
"""R10 Phase 2: Production cross section table generation.

Computes the production cross sections vs g_hH2H2.
Because LHAPDF set 230000 is unavailable locally for full MadGraph runs,
measured columns are preserved blank with status MADGRAPH_NOT_EXECUTED;
structural predictions sigma(g) = sigma_0 * (g/g_0)^2 are stored.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "r10_effective_scan.json"
OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    g_0 = config["baseline_anchor"]["abs_g_0_GeV"]
    sigma_0 = config["baseline_anchor"]["sigma_0_pb"]
    g_values = config["grid"]["g_hH2H2_GeV"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "production_vs_g.csv"

    fieldnames = [
        "g_hH2H2_GeV",
        "GHphiphi_GeV",
        "kappa_g",
        "sigma_pb",
        "integration_error_pb",
        "sigma_over_baseline",
        "expected_kappa_squared",
        "relative_residual",
        "structural_prediction_sigma_pb",
        "status",
        "log_path",
        "log_sha256",
    ]

    rows = []
    for g in g_values:
        gh = -g
        kappa = g / g_0
        expected_kappa_sq = kappa * kappa
        struct_sigma = sigma_0 * expected_kappa_sq

        # Measured MadGraph columns stay empty since MadGraph cannot run with lhapdf 230000
        row = {
            "g_hH2H2_GeV": f"{g:.16g}",
            "GHphiphi_GeV": f"{gh:.16g}",
            "kappa_g": f"{kappa:.16e}",
            "sigma_pb": "",
            "integration_error_pb": "",
            "sigma_over_baseline": "",
            "expected_kappa_squared": f"{expected_kappa_sq:.16e}",
            "relative_residual": "",
            "structural_prediction_sigma_pb": f"{struct_sigma:.16e}",
            "status": "MADGRAPH_NOT_EXECUTED_LHAPDF_UNAVAILABLE;STRUCTURAL_PREDICTION_ONLY",
            "log_path": "",
            "log_sha256": "",
        }
        rows.append(row)

    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote {out_csv} ({len(rows)} points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
