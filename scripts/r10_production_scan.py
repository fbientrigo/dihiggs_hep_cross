#!/usr/bin/env python3
"""R10 Phase 2: Production cross section table generation.

Computes the production cross sections vs g_hH2H2.
Because LHAPDF set 230000 is unavailable locally for full MadGraph runs,
measured columns are preserved blank with status MADGRAPH_NOT_EXECUTED;
structural predictions sigma(g) = sigma_0 * (g/g_0)^2 are stored.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "r10_effective_scan.json"
DEFAULT_OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"

ALLOWED_MODES = ("factorized", "madgraph")



def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate R10 production cross section table.")
    parser.add_argument(
        "--production-mode",
        "--production-evaluation-mode",
        dest="production_evaluation_mode",
        choices=ALLOWED_MODES,
        default="factorized",
        help="Production evaluation mode: 'factorized' (default) or 'madgraph'.",
    )
    parser.add_argument(
        "--madgraph-results",
        type=Path,
        default=None,
        help="Path to MadGraph results CSV (required when production-mode is 'madgraph').",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for production_vs_g.csv.",
    )
    parsed = parser.parse_args(args)
    if parsed.production_evaluation_mode not in ALLOWED_MODES:
        raise ValueError(f"Invalid production_evaluation_mode '{parsed.production_evaluation_mode}'. Must be one of {ALLOWED_MODES}")

    if parsed.production_evaluation_mode == "madgraph":
        if parsed.madgraph_results is None:
            raise ValueError("MadGraph mode requires an explicit --madgraph-results path.")
        if not parsed.madgraph_results.exists():
            raise FileNotFoundError(f"MadGraph results file not found: {parsed.madgraph_results}")

    return parsed


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    eval_mode = parsed.production_evaluation_mode
    out_dir = parsed.out_dir

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    g_0 = config["baseline_anchor"]["abs_g_0_GeV"]
    sigma_0 = config["baseline_anchor"]["sigma_0_pb"]
    g_values = config["grid"]["g_hH2H2_GeV"]

    mg_data_by_g = {}
    if eval_mode == "madgraph":
        with open(parsed.madgraph_results, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                g_val = float(r["g_hH2H2_GeV"])
                mg_data_by_g[round(g_val, 6)] = r

        missing_g = [g for g in g_values if round(g, 6) not in mg_data_by_g]
        if missing_g:
            raise ValueError(
                f"MadGraph mode requires complete coverage of all configured coupling points. "
                f"Missing values: {missing_g}"
            )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "production_vs_g.csv"

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
        "production_evaluation_mode",
        "production_mechanism",
    ]

    rows = []
    for g in g_values:
        gh = -g
        kappa = g / g_0
        expected_kappa_sq = kappa * kappa
        struct_sigma = sigma_0 * expected_kappa_sq

        g_key = round(g, 6)
        if eval_mode == "madgraph":
            mg_row = mg_data_by_g[g_key]
            sigma_mg = float(mg_row["sigma_madgraph_pb"])
            err_mg = float(mg_row["integration_error_pb"])
            sigma_over_base = sigma_mg / sigma_0
            rel_res = (sigma_mg / struct_sigma) - 1.0

            row = {
                "g_hH2H2_GeV": f"{g:.16g}",
                "GHphiphi_GeV": f"{gh:.16g}",
                "kappa_g": f"{kappa:.16e}",
                "sigma_pb": f"{sigma_mg:.16e}",
                "integration_error_pb": f"{err_mg:.16e}",
                "sigma_over_baseline": f"{sigma_over_base:.16e}",
                "expected_kappa_squared": f"{expected_kappa_sq:.16e}",
                "relative_residual": f"{rel_res:.16e}",
                "structural_prediction_sigma_pb": f"{struct_sigma:.16e}",
                "status": mg_row.get("status", "MADGRAPH_DIRECT_RUN"),
                "log_path": mg_row.get("log_path", ""),
                "log_sha256": mg_row.get("log_sha256", ""),
                "production_evaluation_mode": "madgraph",
                "production_mechanism": "ggF",
            }
        else:
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
                "production_evaluation_mode": "factorized",
                "production_mechanism": "ggF",
            }
        rows.append(row)

    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote {out_csv} ({len(rows)} points, mode={eval_mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
