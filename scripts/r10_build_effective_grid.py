#!/usr/bin/env python3
"""R10 Phase 4: Build the 360-point Cartesian effective phenomenological grid.

Cartesian product of:
  6 production points (g_hH2H2_GeV)
  12 lifetime points (ctau_mm)
  5 branching fraction points (BR_H2_to_bb)
= 360 effective combinations.
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


def make_point_id(ctau: float, g: float, br: float) -> str:
    def fmt(val: float) -> str:
        s = f"{val:.4f}".rstrip("0").rstrip(".") if abs(val - round(val, 4)) < 1e-5 else f"{val:.4f}"
        if abs(val - 4.326221529733112) < 1e-6:
            s = "4p326"
        elif abs(val - 63.59142520075966) < 1e-6:
            s = "63p591"
        elif abs(val - 205.09272542237372) < 1e-6:
            s = "205p093"
        elif abs(val - 0.7567374858085787) < 1e-6:
            s = "0p7567"
        else:
            s = s.replace(".", "p")
        return s

    return f"eff_ctau{fmt(ctau)}_g{fmt(g)}_br{fmt(br)}"


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Cartesian effective grid consuming production results.")
    parser.add_argument(
        "--production-mode",
        "--production-evaluation-mode",
        dest="production_evaluation_mode",
        choices=["factorized", "madgraph"],
        default=None,
        help="Optional expected production evaluation mode. If omitted, mode is inferred from production_vs_g.csv.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory containing production_vs_g.csv and efficiency_vs_ctau.csv.",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    out_dir = parsed.out_dir

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    obs_S95 = config["official_limits"]["observed_S95"]
    lumi = config["process"]["luminosity_fb_inverse"]

    # Load Phase 2 (production_vs_g)
    prod_csv = out_dir / "production_vs_g.csv"
    if not prod_csv.exists():
        raise FileNotFoundError(f"Production CSV file not found: {prod_csv}")

    with open(prod_csv, newline="", encoding="utf-8") as fh:
        prod_data = list(csv.DictReader(fh))

    # Validate production rows
    prod_by_g: dict[float, dict] = {}
    for row in prod_data:
        g_val = float(row["g_hH2H2_GeV"])
        g_key = round(g_val, 6)
        if g_key in prod_by_g:
            raise ValueError(f"Duplicate production row for g={g_val} in {prod_csv}")
        prod_by_g[g_key] = row

    # Determine default evaluation mode if explicitly passed via CLI
    explicit_mode = parsed.production_evaluation_mode

    # Load Phase 3 (efficiency_vs_ctau)
    eff_csv = out_dir / "efficiency_vs_ctau.csv"
    if not eff_csv.exists():
        raise FileNotFoundError(f"Efficiency CSV file not found: {eff_csv}")

    with open(eff_csv, newline="", encoding="utf-8") as fh:
        eff_data = list(csv.DictReader(fh))

    eff_by_ctau = {}
    for row in eff_data:
        c = float(row["ctau_mm"])
        eff_by_ctau[round(c, 6)] = {
            "aeff": float(row["Trackless_Aeff"]),
            "aeff_err": float(row["Trackless_Aeff_stat_uncertainty"]),
            "status": row["Trackless_status"],
            "total_width": float(row["total_width_GeV"]),
        }

    br_grid = config["grid"]["BR_H2_to_bb"]
    g_grid = config["grid"]["g_hH2H2_GeV"]
    ctau_grid = config["grid"]["ctau_mm"]

    fieldnames = [
        "point_id",
        "ctau_mm",
        "total_width_GeV",
        "g_hH2H2_GeV",
        "GHphiphi_GeV",
        "BR_H2_to_bb",
        "sigma_production_pb",
        "sigma_production_error_pb",
        "Trackless_Aeff",
        "Trackless_Aeff_error",
        "sigma_4b_fb",
        "visible_sigma_fb",
        "N_expected_139fb",
        "N_expected_error",
        "observed_S95",
        "N_over_observed_S95",
        "above_observed_S95",
        "interpretation",
        "production_status",
        "efficiency_status",
        "production_evaluation_mode",
    ]

    rows = []
    for g in g_grid:
        g_key = round(g, 6)
        if g_key not in prod_by_g:
            raise ValueError(f"Configured g={g} has no production row in {prod_csv}")

        p_row = prod_by_g[g_key]
        row_mode = p_row.get("production_evaluation_mode", "factorized")

        if explicit_mode and explicit_mode != row_mode and p_row.get("sigma_pb"):
            raise ValueError(
                f"Requested production mode '{explicit_mode}' conflicts with row mode '{row_mode}' for g={g}"
            )

        if row_mode == "madgraph" and p_row.get("sigma_pb"):
            val_str = p_row["sigma_pb"]
            sigma_selected_pb = float(val_str)
            err_str = p_row.get("integration_error_pb", "0.0")
            sigma_selected_error_pb = float(err_str) if err_str else 0.0
            prod_status = p_row.get("status", "MADGRAPH_DIRECT_RUN")
            row_eval_mode = "madgraph"
        else:
            val_str = p_row.get("structural_prediction_sigma_pb", "")
            if not val_str:
                raise ValueError(f"Missing structural_prediction_sigma_pb for g={g} in factorized mode")
            sigma_selected_pb = float(val_str)
            sigma_selected_error_pb = 0.0
            prod_status = "STRUCTURAL_PREDICTION_ONLY"
            row_eval_mode = "factorized"


        if not math.isfinite(sigma_selected_pb) or sigma_selected_pb <= 0:
            raise ValueError(f"Non-finite or non-positive sigma_selected_pb={sigma_selected_pb} for g={g}")

        gh = -g

        for ctau in ctau_grid:
            eff_info = eff_by_ctau[round(ctau, 6)]
            aeff = eff_info["aeff"]
            aeff_err = eff_info["aeff_err"]
            eff_status = eff_info["status"]
            width = eff_info["total_width"]

            for br in br_grid:
                pid = make_point_id(ctau, g, br)

                sigma_4b = sigma_selected_pb * 1000.0 * (br * br)
                vis_sigma = sigma_4b * aeff
                n_exp = vis_sigma * lumi
                n_over_s95 = n_exp / obs_S95
                above_s95 = (n_exp >= obs_S95 - 1e-12)

                if aeff > 0:
                    n_exp_err = n_exp * (aeff_err / aeff)
                else:
                    n_exp_err = lumi * sigma_4b * aeff_err

                rows.append(
                    {
                        "point_id": pid,
                        "ctau_mm": f"{ctau:.16g}",
                        "total_width_GeV": f"{width:.16e}",
                        "g_hH2H2_GeV": f"{g:.16g}",
                        "GHphiphi_GeV": f"{gh:.16g}",
                        "BR_H2_to_bb": f"{br:.16g}",
                        "sigma_production_pb": f"{sigma_selected_pb:.16e}",
                        "sigma_production_error_pb": f"{sigma_selected_error_pb:.16e}",
                        "Trackless_Aeff": f"{aeff:.16g}",
                        "Trackless_Aeff_error": f"{aeff_err:.16g}",
                        "sigma_4b_fb": f"{sigma_4b:.16e}",
                        "visible_sigma_fb": f"{vis_sigma:.16e}",
                        "N_expected_139fb": f"{n_exp:.16e}",
                        "N_expected_error": f"{n_exp_err:.16e}",
                        "observed_S95": f"{obs_S95:.1f}",
                        "N_over_observed_S95": f"{n_over_s95:.16e}",
                        "above_observed_S95": str(above_s95),
                        "interpretation": "EFFECTIVE_PHENOMENOLOGICAL",
                        "production_status": prod_status,
                        "efficiency_status": eff_status,
                        "production_evaluation_mode": row_eval_mode,
                    }

                )

    out_csv = out_dir / "effective_grid.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote {out_csv} ({len(rows)} effective grid points, mode={explicit_mode or 'mixed'})")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
