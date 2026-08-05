#!/usr/bin/env python3
"""R10 Phase 7: Recompute and audit the 240-point effective grid.

Reconstructs every row of results/r10_effective_ctau_g_br_scan/effective_grid.csv
algebraically from:
  - production_vs_g.csv
  - efficiency_vs_ctau.csv
  - configs/r10_effective_scan.json

Fails with non-zero exit code if any value or row mismatches.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "r10_effective_scan.json"
OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"


def float_equal(a_str: str, b_val: float, tol: float = 1e-12) -> bool:
    try:
        a_val = float(a_str)
        if math.isnan(a_val) and math.isnan(b_val):
            return True
        if a_val == 0.0 and b_val == 0.0:
            return True
        rel_diff = abs(a_val - b_val) / max(abs(b_val), 1e-15)
        return rel_diff <= tol
    except ValueError:
        return a_str == str(b_val)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    g_0 = config["baseline_anchor"]["abs_g_0_GeV"]
    sigma_0 = config["baseline_anchor"]["sigma_0_pb"]
    obs_S95 = config["official_limits"]["observed_S95"]
    lumi = config["process"]["luminosity_fb_inverse"]

    grid_csv = OUT_DIR / "effective_grid.csv"
    if not grid_csv.exists():
        print(f"[FAIL] Missing {grid_csv}", file=sys.stderr)
        return 1

    with open(grid_csv, newline="", encoding="utf-8") as fh:
        existing_rows = list(csv.DictReader(fh))

    if len(existing_rows) != 240:
        print(f"[FAIL] Expected 240 grid rows, found {len(existing_rows)}", file=sys.stderr)
        return 1

    # Load efficiency_vs_ctau.csv
    eff_csv = OUT_DIR / "efficiency_vs_ctau.csv"
    with open(eff_csv, newline="", encoding="utf-8") as fh:
        eff_rows = list(csv.DictReader(fh))
    eff_by_ctau = {round(float(r["ctau_mm"]), 6): r for r in eff_rows}

    errors = []
    for i, row in enumerate(existing_rows):
        pid = row["point_id"]
        ctau = float(row["ctau_mm"])
        g = float(row["g_hH2H2_GeV"])
        br = float(row["BR_H2_to_bb"])

        eff_info = eff_by_ctau.get(round(ctau, 6))
        if not eff_info:
            errors.append(f"Row {i} ({pid}): ctau {ctau} not in efficiency_vs_ctau.csv")
            continue

        aeff = float(eff_info["Trackless_Aeff"])
        aeff_err = float(eff_info["Trackless_Aeff_stat_uncertainty"])
        eff_status = eff_info["Trackless_status"]

        kappa = g / g_0
        expected_sigma_prod = sigma_0 * (kappa * kappa)
        expected_sigma_4b = expected_sigma_prod * 1000.0 * (br * br)
        expected_vis_sigma = expected_sigma_4b * aeff
        expected_n_exp = expected_vis_sigma * lumi
        expected_n_over_s95 = expected_n_exp / obs_S95
        expected_above_s95 = (expected_n_exp >= obs_S95 - 1e-12)

        # Check values
        if not float_equal(row["sigma_production_pb"], expected_sigma_prod):
            errors.append(f"Row {i} ({pid}): sigma_production_pb mismatch {row['sigma_production_pb']} vs {expected_sigma_prod}")

        if not float_equal(row["sigma_4b_fb"], expected_sigma_4b):
            errors.append(f"Row {i} ({pid}): sigma_4b_fb mismatch {row['sigma_4b_fb']} vs {expected_sigma_4b}")

        if not float_equal(row["visible_sigma_fb"], expected_vis_sigma):
            errors.append(f"Row {i} ({pid}): visible_sigma_fb mismatch {row['visible_sigma_fb']} vs {expected_vis_sigma}")

        if not float_equal(row["N_expected_139fb"], expected_n_exp):
            errors.append(f"Row {i} ({pid}): N_expected_139fb mismatch {row['N_expected_139fb']} vs {expected_n_exp}")

        if not float_equal(row["N_over_observed_S95"], expected_n_over_s95):
            errors.append(f"Row {i} ({pid}): N_over_observed_S95 mismatch {row['N_over_observed_S95']} vs {expected_n_over_s95}")

        if row["above_observed_S95"] != str(expected_above_s95):
            errors.append(f"Row {i} ({pid}): above_observed_S95 mismatch {row['above_observed_S95']} vs {expected_above_s95}")

        if row["interpretation"] != "EFFECTIVE_PHENOMENOLOGICAL":
            errors.append(f"Row {i} ({pid}): interpretation label must be EFFECTIVE_PHENOMENOLOGICAL")

        if row["efficiency_status"] != eff_status:
            errors.append(f"Row {i} ({pid}): efficiency_status mismatch {row['efficiency_status']} vs {eff_status}")

    if errors:
        print(f"[FAIL] Recomputation found {len(errors)} mismatches:", file=sys.stderr)
        for err in errors[:10]:
            print(f"  - {err}", file=sys.stderr)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors", file=sys.stderr)
        return 1

    print("[PASS] r10_recompute_grid: all 240 effective grid rows reconstructed and verified with zero mismatches!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
