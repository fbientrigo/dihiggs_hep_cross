#!/usr/bin/env python3
"""R10 Phase 4: Build the 240-point Cartesian effective phenomenological grid.

Cartesian product of:
  6 production points (g_hH2H2_GeV)
  8 lifetime points (ctau_mm)
  5 branching fraction points (BR_H2_to_bb)
= 240 effective combinations.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "r10_effective_scan.json"
OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"


def make_point_id(ctau: float, g: float, br: float) -> str:
    def fmt(val: float) -> str:
        # 4.326221529733112 -> 4p326, 63.59142520075966 -> 63p591, 0.7567374858085787 -> 0p7567
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


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    g_0 = config["baseline_anchor"]["abs_g_0_GeV"]
    sigma_0 = config["baseline_anchor"]["sigma_0_pb"]
    obs_S95 = config["official_limits"]["observed_S95"]
    lumi = config["process"]["luminosity_fb_inverse"]
    hbar_c = config["hbar_c_GeV_mm"]

    # Load Phase 2 (production_vs_g)
    prod_csv = OUT_DIR / "production_vs_g.csv"
    with open(prod_csv, newline="", encoding="utf-8") as fh:
        prod_data = list(csv.DictReader(fh))

    # Load Phase 3 (efficiency_vs_ctau)
    eff_csv = OUT_DIR / "efficiency_vs_ctau.csv"
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
    ]

    rows = []
    for g in g_grid:
        gh = -g
        kappa = g / g_0
        sigma_prod = sigma_0 * kappa * kappa
        prod_err = 0.0

        for ctau in ctau_grid:
            eff_info = eff_by_ctau[round(ctau, 6)]
            aeff = eff_info["aeff"]
            aeff_err = eff_info["aeff_err"]
            eff_status = eff_info["status"]
            width = eff_info["total_width"]

            for br in br_grid:
                pid = make_point_id(ctau, g, br)

                sigma_4b = sigma_prod * 1000.0 * (br * br)
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
                        "sigma_production_pb": f"{sigma_prod:.16e}",
                        "sigma_production_error_pb": f"{prod_err:.16e}",
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
                        "production_status": "STRUCTURAL_PREDICTION_ONLY",
                        "efficiency_status": eff_status,
                    }
                )

    out_csv = OUT_DIR / "effective_grid.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote {out_csv} ({len(rows)} effective grid points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
