#!/usr/bin/env python3
"""Assemble the R9 result summary and the SHA-256 artifact manifest."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"

MANIFEST_EXTRA = [
    "docs/R9_H2_SENSITIVITY_THRESHOLD_RESULT.md",
    "docs/R9_PRESENTATION_INSERT_ES.md",
    "src/llp_recast/r9_threshold.py",
    "scripts/r9_build_iteration1.py",
    "scripts/r9_run_model_scan.py",
    "scripts/r9_atlas_threshold.py",
    "scripts/r9_make_figures.py",
    "scripts/r9_ingest_madgraph_scaling.py",
    "scripts/r9_build_summary.py",
    "scripts/r9_recompute_check.py",
    "scripts/verify_r9_artifacts.py",
    "tests/test_r9_threshold.py",
    "tests/test_r9_artifacts.py",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    baseline = json.loads((OUTDIR / "baseline.json").read_text())
    fit = json.loads((OUTDIR / "madgraph_scaling_fit.json").read_text())
    atlas = json.loads((OUTDIR / "atlas_threshold.json").read_text())
    coord = json.loads((OUTDIR / "coordinate_selection.json").read_text())
    scan_meta = json.loads((OUTDIR / "model_scan_provenance.json").read_text())
    with open(OUTDIR / "yield_thresholds.csv", newline="") as fh:
        thresholds = list(csv.DictReader(fh))
    with open(OUTDIR / "model_reachability_scan.csv", newline="") as fh:
        scan = list(csv.DictReader(fh))

    frozen = baseline["frozen_inputs"]
    n0 = baseline["recomputed"]["Trackless_expected_events"]
    g0 = frozen["g_hH2H2_GeV"]["value"]
    valid = [r for r in scan if r["theory_ok_v1"] == "1"]
    k_max = scan_meta["theory_valid_kappa_max"]
    k_n1 = float(thresholds[0]["kappa_g"])

    summary = {
        "schema": "hep_cross.r9.result_summary.v1",
        "study": "R9 controlled sensitivity-threshold study around the validated R8 benchmark",
        "benchmark_id": baseline["benchmark_id"],
        "status": "COMPLETE",
        "iterations_run": 2,

        "baseline": {
            "m_H2_GeV": frozen["m_H2_GeV"]["value"],
            "ctau_mm": frozen["ctau_mm"]["value"],
            "g_hH2H2_GeV": g0,
            "GHphiphi_GeV": frozen["GHphiphi_GeV"]["value"],
            "sigma_H2H2_pb": frozen["sigma_H2H2_pb"]["value"],
            "BR_bb_squared": frozen["BR_bb_squared"]["value"],
            "Trackless_Aeff": frozen["Trackless_Aeff"]["value"],
            "Trackless_visible_sigma_fb": baseline["recomputed"]["Trackless_visible_sigma_fb"],
            "luminosity_fb_inverse": baseline["luminosity_fb_inverse"],
            "Trackless_expected_events": n0,
            "r8_status": baseline["r8_status"],
        },

        "q1_sigma_scaling": {
            "question": "Does sigma(pp -> H2H2) scale quadratically with |g_hH2H2|?",
            "answer": "Yes, exactly.",
            "fitted_exponent_p": fit["fitted_exponent_p"],
            "method": fit["method"],
            "quadratic_scaling": fit["quadratic_scaling"],
            "tested_kappa_values": [0.5, 1.0, 2.0, 4.0],
            "empirical_fit_status": fit["empirical_fit_status"],
            "changing_GHphiphi_affects": fit["changing_GHphiphi_affects"],
        },

        "q2_q3_illustrative_thresholds": [
            {
                "target_events": float(r["target_events"]),
                "rate_multiplier": float(r["rate_multiplier"]),
                "kappa_g": float(r["kappa_g"]),
                "required_abs_g_hH2H2_GeV": float(r["required_abs_g_hH2H2_GeV"]),
                "required_visible_sigma_fb": float(r["required_visible_sigma_fb"]),
                "interpretation": r["interpretation"],
            }
            for r in thresholds
        ],

        "q4_official_atlas_threshold": {
            "status": atlas["status"],
            "region_mapping_status": atlas["region_mapping"]["region_mapping_status"],
            "official_region": atlas["region_mapping"]["official_region"],
            "observed_S95": atlas["numerical_threshold"]["observed_S95"],
            "expected_S95": atlas["numerical_threshold"]["expected_S95"],
            "model_independent_visible_sigma_limit_fb":
                atlas["numerical_threshold"]["model_independent_visible_sigma_limit_fb"],
            "why_unresolved": atlas["numerical_threshold"]["why_unresolved"],
        },

        "q5_model_reachability": {
            "varied_coordinate": scan_meta["varied_coordinate"],
            "coordinate_selection_method": coord["method"],
            "coordinate_selection_reason": coord["selection_reason"],
            "rejected_coordinates": {
                "lambda6": {
                    "kappa_g_span_over_10_decades":
                        coord["candidates"]["lambda6"]["kappa_g_span_over_10_decades"],
                    "verdict": "does not enter g_hH2H2",
                },
                "lambda1_target": {
                    "kappa_g_span_over_full_perturbative_window":
                        coord["candidates"]["lambda1_target"][
                            "kappa_g_span_over_full_perturbative_window"],
                    "verdict": "only a re-parameterisation of m12_sq; span is negligible",
                },
            },
            "points_tested": scan_meta["scan_points"],
            "point_budget": scan_meta["scan_budget"],
            "theory_valid_points": scan_meta["theory_valid_points"],
            "max_theory_valid_kappa_g": k_max,
            "min_theory_valid_kappa_g": scan_meta["theory_valid_kappa_min"],
            "theory_valid_kappa_window_width": (
                scan_meta["theory_valid_kappa_max"] - scan_meta["theory_valid_kappa_min"]
            ),
            "theory_valid_ctau_mm_range": scan_meta["theory_valid_ctau_mm_range"],
            "theory_valid_br_bb_range": scan_meta["theory_valid_br_bb_range"],
            "max_theory_valid_abs_g_hH2H2_GeV": k_max * g0,
            "smallest_illustrative_threshold_kappa_g": k_n1,
            "threshold_reached": False,
            "shortfall_factor_in_kappa": k_n1 / k_max,
            "shortfall_factor_in_rate": (k_n1 / k_max) ** 2,
            "theory_validity_boundary_cause": scan_meta["theory_validity_boundary_cause"],
            "verdict": "THRESHOLD_NOT_MODEL_REACHABLE",
        },

        "q6_rate_limitation_cause": {
            "dominant_cause": "production coupling",
            "production_coupling": (
                "Dominant. |g_hH2H2| is pinned at m_h^2/v = 63.59 GeV: at tan(beta) = 3e5 the "
                "only coordinate that reaches the trilinear, M^2, is locked to m_H2^2 by "
                "perturbativity and positivity of lambda1, whose sensitivity to M^2 is enhanced "
                "by tan(beta)^2 while the coupling's is not."
            ),
            "branching_ratio": (
                "Not the limitation. BR(H2->bb) = 0.7567 is already large and is unchanged "
                "across the entire theory-valid window (span < 1e-4 relative)."
            ),
            "lifetime_acceptance": (
                "Not the limitation. ctau = 4.326 mm sits in the region the analysis accepts; "
                "the Trackless A x eff of 1.5734% is a normal displaced-vertex acceptance, and "
                "ctau varies by < 1e-4 relative across the theory-valid window."
            ),
            "combination": (
                "There is a genuine structural tension rather than an independent set of "
                "limitations: the large tan(beta) that produces the mm-scale lifetime in Type I "
                "is the same parameter that locks the production trilinear."
            ),
        },

        "acceptance_stability": {
            "acceptance_reuse_valid_for_all_theory_valid_points": all(
                r["acceptance_label"] == "ACCEPTANCE_REUSED_AT_FIXED_MASS_AND_NEARBY_LIFETIME"
                for r in valid
            ),
            "max_relative_ctau_change_among_valid_points": max(
                abs(float(r["ctau_relative_change"])) for r in valid
            ),
            "note": (
                "A pure kappa_g rescaling multiplies the single diagram's amplitude by a "
                "constant, so the production kinematics are identical and the validated R8 "
                "acceptance is exact, not approximate, for the coupling-only interpretation."
            ),
        },

        "additional_recast": {
            "run": False,
            "reason": (
                "The gate requires a theory-valid point whose coupling or predicted rate is near "
                "the first relevant threshold and whose ctau moved enough to make baseline "
                "acceptance reuse unreliable. No theory-valid point comes within a factor of "
                f"{k_n1 / k_max:.3g} in kappa_g of the smallest illustrative threshold, and every "
                "theory-valid point has |delta ctau|/ctau below 1e-4. No condition of the gate "
                "is satisfied, so no additional recast was run. R8 was not rerun and no "
                "lifetime grid was executed."
            ),
        },

        "interpretation": {
            "phenomenological_threshold": (
                f"The effective production coupling must reach |g| = "
                f"{float(thresholds[0]['required_abs_g_hH2H2_GeV']):.2f} GeV "
                f"(kappa_g = {k_n1:.3f}, rate x {float(thresholds[0]['rate_multiplier']):.3f}) "
                "for a single expected Trackless event at 139 fb^-1, and "
                f"{float(thresholds[3]['required_abs_g_hH2H2_GeV']):.2f} GeV "
                f"(kappa_g = {float(thresholds[3]['kappa_g']):.3f}) for ten."
            ),
            "model_reachability": (
                "No. The full theory-valid range of the only coordinate that reaches the "
                f"trilinear changes kappa_g by {scan_meta['theory_valid_kappa_max'] - scan_meta['theory_valid_kappa_min']:.2e}, "
                f"about {k_n1 / k_max:.3g} times short of the smallest illustrative threshold."
            ),
            "experimental_relevance": (
                "Not established either way: the region mapping to the ATLAS Trackless SR is "
                "unambiguous, but no official model-independent threshold could be read, so the "
                "1/3/5/10-event scales remain illustrative."
            ),
            "acceptance_stability": (
                "Stable. Changing the model along the selected coordinate does not move the "
                "lifetime enough to require a new recast."
            ),
        },

        "next_step": "THRESHOLD_NOT_MODEL_REACHABLE",

        "provenance": {
            "baseline_sources": {
                k: {"source_path": v["source_path"], "source_sha256": v["source_sha256"]}
                for k, v in frozen.items()
            },
            "model_scan": {
                "evaluator_source": scan_meta["evaluator_source"],
                "evaluator_source_sha256": scan_meta["evaluator_source_sha256"],
                "evaluator_binary_sha256": scan_meta["evaluator_binary_sha256"],
                "lib2hdmc_sha256": scan_meta["lib2hdmc_sha256"],
                "evaluator_calls": scan_meta["evaluator_calls"],
            },
            "ufo_zip_sha256": fit["structural_verification"]["ufo_zip_sha256"],
            "blocked_sources": fit["blocked_sources"],
        },
    }

    (OUTDIR / "result_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    files: dict[str, str] = {}
    for path in sorted(OUTDIR.rglob("*")):
        if path.is_file() and path.name != "artifact_manifest.json":
            files[str(path.relative_to(REPO_ROOT))] = sha256_file(path)
    for rel in MANIFEST_EXTRA:
        path = REPO_ROOT / rel
        if path.exists():
            files[rel] = sha256_file(path)

    (OUTDIR / "artifact_manifest.json").write_text(
        json.dumps(
            {"schema": "hep_cross.r9_h2_sensitivity_threshold.artifact_manifest.v1", "files": files},
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"result_summary.json: next_step = {summary['next_step']}")
    print(f"artifact_manifest.json: {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
