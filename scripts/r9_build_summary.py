#!/usr/bin/env python3
"""Build the compact machine-readable R9 summary.

All threshold arithmetic is re-derived from committed primary artifacts.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"


def load_csv(name: str) -> list[dict[str, str]]:
    with open(OUTDIR / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    baseline = json.loads((OUTDIR / "baseline.json").read_text())
    fit = json.loads((OUTDIR / "madgraph_scaling_fit.json").read_text())
    atlas = json.loads((OUTDIR / "atlas_threshold.json").read_text())
    scan_meta = json.loads((OUTDIR / "model_scan_provenance.json").read_text())
    thresholds = load_csv("yield_thresholds.csv")
    scan = load_csv("model_reachability_scan.csv")

    frozen = baseline["frozen_inputs"]
    n0 = baseline["recomputed"]["Trackless_expected_events"]
    g0 = frozen["g_hH2H2_GeV"]["value"]
    valid = [row for row in scan if row["theory_ok_v1"] == "1"]
    k_min = min(float(row["kappa_g"]) for row in valid)
    k_max = max(float(row["kappa_g"]) for row in valid)

    official = atlas["numerical_threshold"]
    required_kappa = atlas["required_kappa_g"]

    summary = {
        "schema": "hep_cross.r9.result_summary.v2",
        "study": "R9 controlled sensitivity-threshold study",
        "benchmark_id": baseline["benchmark_id"],
        "status": "COMPLETE",
        "scope_status": "THRESHOLD_NOT_REACHABLE_IN_THE_TESTED_FIXED_SLICE",
        "tested_fixed_slice": {
            "m_H2_GeV": 150.0,
            "m_A_GeV": 450.0,
            "m_Hp_GeV": 450.0,
            "tan_beta": 300000.0,
            "sin_beta_minus_alpha": 1.0,
            "lambda6": 1e-10,
            "lambda7": 0.0,
            "varied_coordinate": "m12_sq / M2 only",
        },
        "baseline": {
            "g_hH2H2_GeV": g0,
            "Trackless_visible_sigma_fb": baseline["recomputed"][
                "Trackless_visible_sigma_fb"
            ],
            "Trackless_expected_events": n0,
            "Trackless_Aeff": frozen["Trackless_Aeff"]["value"],
            "ctau_mm": frozen["ctau_mm"]["value"],
            "BR_bb_squared": frozen["BR_bb_squared"]["value"],
        },
        "q1_sigma_scaling": {
            "answer": "Yes, within the frozen UFO/process/width contract.",
            "fitted_exponent_p": 2.0,
            "method": "STRUCTURAL_EXACT_WITHIN_FROZEN_UFO_AND_PROCESS",
            "empirical_fit_status": fit["empirical_fit_status"],
            "quadratic_scaling": "PASS",
        },
        "q2_q3_illustrative_thresholds": [
            {
                "target_events": float(row["target_events"]),
                "rate_multiplier": float(row["rate_multiplier"]),
                "kappa_g": float(row["kappa_g"]),
                "required_abs_g_hH2H2_GeV": float(
                    row["required_abs_g_hH2H2_GeV"]
                ),
                "required_visible_sigma_fb": float(
                    row["required_visible_sigma_fb"]
                ),
                "interpretation": row["interpretation"],
            }
            for row in thresholds
        ],
        "q4_official_atlas_threshold": {
            "status": atlas["status"],
            "region_mapping_status": atlas["region_mapping"][
                "region_mapping_status"
            ],
            "observed_events": official["observed_events"],
            "expected_background": official["expected_background"],
            "expected_background_up": official["expected_background_up"],
            "expected_background_down": official["expected_background_down"],
            "observed_S95": official["observed_S95"],
            "expected_S95": official["expected_S95"],
            "published_visible_sigma_limit_fb": official[
                "published_model_independent_visible_sigma_limit_fb"
            ],
            "required_visible_sigma_fb": atlas["required_visible_sigma_fb"],
            "required_rate_multiplier": atlas["required_rate_multiplier"],
            "required_kappa_g": required_kappa,
            "required_abs_g_hH2H2_GeV": atlas[
                "required_abs_g_hH2H2_GeV"
            ],
        },
        "q5_model_reachability": {
            "points_tested": len(scan),
            "theory_valid_points": len(valid),
            "varied_coordinate": "m12_sq (equivalently M2)",
            "min_theory_valid_kappa_g": k_min,
            "max_theory_valid_kappa_g": k_max,
            "theory_valid_kappa_window_width": k_max - k_min,
            "max_theory_valid_abs_g_hH2H2_GeV": k_max * g0,
            "official_threshold_kappa_g": required_kappa,
            "official_threshold_reached": False,
            "shortfall_factor_in_kappa": required_kappa / k_max,
            "shortfall_factor_in_rate": (required_kappa / k_max) ** 2,
            "theory_validity_boundary_cause": scan_meta[
                "theory_validity_boundary_cause"
            ],
            "verdict": "THRESHOLD_NOT_REACHABLE_IN_THE_TESTED_FIXED_SLICE",
        },
        "q6_rate_limitation_cause": {
            "dominant_cause": "production coupling",
            "branching_ratio": "not limiting across the valid M2 window",
            "lifetime_acceptance": (
                "not limiting across the valid M2 window; A×eff is nonzero "
                "and MC-statistically resolved"
            ),
            "safe_lifetime_statement": (
                "At this benchmark, large tan(beta) suppresses Type-I "
                "fermionic widths and enables a millimetre-scale lifetime; "
                "no global ctau scaling law is established."
            ),
        },
        "additional_recast": {
            "run": False,
            "reason": (
                "No theory-valid point approaches the official coupling "
                "threshold and ctau remains stable in the tested slice."
            ),
        },
        "presentation": {
            "insert": "docs/R9_PRESENTATION_INSERT_ES.md",
            "canonical_threshold_figure": (
                "results/r9_h2_sensitivity_threshold/"
                "expected_events_vs_kappa_g_official.svg"
            ),
        },
        "next_step": "PRESENT_RESULT",
    }

    (OUTDIR / "result_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print("result_summary.json: COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
