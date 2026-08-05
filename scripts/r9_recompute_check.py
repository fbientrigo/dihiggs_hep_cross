#!/usr/bin/env python3
"""Independently recompute every published R9 number from primary inputs.

This is a gate, not a report: it re-derives the baseline yield chain, all four
illustrative thresholds, the per-point yields of the model scan and the summary
cross-references straight from the primary artifacts, and exits non-zero on the
first mismatch.  It shares no arithmetic path with the builder scripts beyond
``llp_recast.r9_threshold``.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = REPO_ROOT.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"
PRODUCTION_MANIFEST = REPO_ROOT / "artifacts" / "h2_first_physical" / "production_manifest.json"
R8_NORMALIZATION = (
    WORKSPACE / "dihiggs_llp_recast" / "results" / "r8_h2_model_derived_4b" / "normalization.json"
)
COUPLING_ARTIFACT = (
    WORKSPACE / "dihiggs" / "benchmarks" / "H2scan_mH150_tb300000_production_coupling.json"
)

LUMI = 139.0
RTOL = 1e-12

# The task's frozen baseline, restated here so drift in either direction fails.
FROZEN = {
    "m_H2_GeV": 150.0,
    "ctau_mm": 4.32622152973311191,
    "g_hH2H2_GeV": 63.5914252007596588,
    "GHphiphi_GeV": -63.5914252007596588,
    "sigma_H2H2_pb": 0.000230291167568,
    "BR_bb_squared": 0.5726516224278888,
    "sigma_4b_fb": 0.131876610738628,
    "Trackless_Aeff": 0.01573386,
    "Trackless_visible_sigma_fb": 0.0020749281306360694,
    "luminosity_fb_inverse": 139,
    "Trackless_expected_events": 0.28841501015841364,
}

failures: list[str] = []


def check(name: str, got: float, want: float, rtol: float = RTOL) -> None:
    if want == 0.0:
        ok = got == 0.0
        rel = 0.0 if ok else math.inf
    else:
        rel = abs(got - want) / abs(want)
        ok = rel <= rtol
    if not ok:
        failures.append(f"{name}: got {got!r}, expected {want!r} (relative {rel:.3e} > {rtol:.1e})")


def main() -> int:
    # ---- 0. resolve the primary inputs -------------------------------------
    # sigma and BR always come from this repo's own production manifest. The
    # Trackless acceptance lives in dihiggs_llp_recast and the coupling in
    # dihiggs; when those sibling checkouts are present (a full workspace) they
    # are the source of truth and baseline.json is cross-checked against them.
    # In a single-repo checkout (CI) the snapshot recorded in baseline.json --
    # which carries each value together with its source path and SHA-256 -- is
    # used instead, and the cross-repo check is reported as skipped. Every
    # derived number is re-derived either way; nothing is waived.
    baseline_doc = json.loads((OUTDIR / "baseline.json").read_text())
    snapshot = baseline_doc["frozen_inputs"]

    production = json.loads(PRODUCTION_MANIFEST.read_text())
    siblings_available = R8_NORMALIZATION.exists() and COUPLING_ARTIFACT.exists()

    sigma_pb = production["madgraph"]["combined_sigma_pb"]
    br_sq = production["normalization"]["BR_bb_squared"]

    if siblings_available:
        normalization = json.loads(R8_NORMALIZATION.read_text())
        coupling = json.loads(COUPLING_ARTIFACT.read_text())
        a_eff = normalization["regions"]["Trackless"]["a_eff_acc_x_eff"]
        g_abs = coupling["coupling"]["g_hH2H2_GeV"]
        ghphiphi = coupling["coupling"]["converted_GHphiphi_GeV"]
        ctau = coupling["replay"]["ctau_mm"]
        source_mode = "SIBLING_REPOSITORIES"
        # the committed snapshot must agree with the live sibling artifacts
        check("snapshot vs sibling Trackless_Aeff", snapshot["Trackless_Aeff"]["value"], a_eff)
        check("snapshot vs sibling g_hH2H2_GeV", snapshot["g_hH2H2_GeV"]["value"], g_abs)
        check("snapshot vs sibling GHphiphi_GeV", snapshot["GHphiphi_GeV"]["value"], ghphiphi)
        check("snapshot vs sibling ctau_mm", snapshot["ctau_mm"]["value"], ctau)
    else:
        a_eff = snapshot["Trackless_Aeff"]["value"]
        g_abs = snapshot["g_hH2H2_GeV"]["value"]
        ghphiphi = snapshot["GHphiphi_GeV"]["value"]
        ctau = snapshot["ctau_mm"]["value"]
        source_mode = "BASELINE_SNAPSHOT (sibling checkouts absent; cross-repo check skipped)"

    # the snapshot must always agree with this repo's own production manifest
    check("snapshot vs local sigma_H2H2_pb", snapshot["sigma_H2H2_pb"]["value"], sigma_pb)
    check("snapshot vs local BR_bb_squared", snapshot["BR_bb_squared"]["value"], br_sq)

    # ---- 1. primary inputs still equal the frozen baseline -----------------
    check("primary sigma_H2H2_pb", sigma_pb, FROZEN["sigma_H2H2_pb"])
    check("primary BR_bb_squared", br_sq, FROZEN["BR_bb_squared"])
    check("primary Trackless_Aeff", a_eff, FROZEN["Trackless_Aeff"])
    check("primary g_hH2H2_GeV", g_abs, FROZEN["g_hH2H2_GeV"])
    check("primary GHphiphi_GeV", ghphiphi, FROZEN["GHphiphi_GeV"])
    check("primary ctau_mm", ctau, FROZEN["ctau_mm"])
    check("GHphiphi = -g_hH2H2", ghphiphi, -g_abs)

    # ---- 2. yield chain, recomputed from scratch ---------------------------
    sigma_fb = sigma_pb * 1000.0
    sigma4b = sigma_fb * br_sq
    vis = sigma4b * a_eff
    n0 = vis * LUMI
    check("sigma_4b_fb", sigma4b, FROZEN["sigma_4b_fb"])
    check("Trackless_visible_sigma_fb", vis, FROZEN["Trackless_visible_sigma_fb"])
    check("Trackless_expected_events", n0, FROZEN["Trackless_expected_events"])

    # ---- 3. baseline.json agrees with the recomputation --------------------
    recomputed = baseline_doc["recomputed"]
    check("baseline.json visible sigma", recomputed["Trackless_visible_sigma_fb"], vis)
    check("baseline.json expected events", recomputed["Trackless_expected_events"], n0)
    check("baseline.json sigma_4b_fb", recomputed["sigma_4b_fb"], sigma4b)

    # ---- 4. every illustrative threshold, recomputed -----------------------
    with open(OUTDIR / "yield_thresholds.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if [float(r["target_events"]) for r in rows] != [1.0, 3.0, 5.0, 10.0]:
        failures.append("yield_thresholds.csv targets are not 1/3/5/10")
    for row in rows:
        target = float(row["target_events"])
        mult = target / n0
        kappa = math.sqrt(mult)
        check(f"N={target:g} rate_multiplier", float(row["rate_multiplier"]), mult)
        check(f"N={target:g} kappa_g", float(row["kappa_g"]), kappa)
        check(f"N={target:g} |g|", float(row["required_abs_g_hH2H2_GeV"]), kappa * g_abs)
        check(f"N={target:g} GHphiphi", float(row["required_GHphiphi_GeV"]), -kappa * g_abs)
        check(f"N={target:g} sigma", float(row["required_sigma_H2H2_pb"]), sigma_pb * mult)
        check(f"N={target:g} visible sigma", float(row["required_visible_sigma_fb"]), vis * mult)
        # closure: the required visible sigma must give back the target yield
        check(f"N={target:g} closure", float(row["required_visible_sigma_fb"]) * LUMI, target)

    # ---- 5. the four kappa scan rows ---------------------------------------
    with open(OUTDIR / "madgraph_coupling_scaling.csv", newline="") as fh:
        scaling = list(csv.DictReader(fh))
    if [float(r["kappa_g"]) for r in scaling] != [0.5, 1.0, 2.0, 4.0]:
        failures.append("madgraph_coupling_scaling.csv kappa values are not 0.5/1/2/4")
    for row in scaling:
        kappa = float(row["kappa_g"])
        check(f"kappa={kappa} GHphiphi", float(row["GHphiphi_GeV"]), kappa * ghphiphi)
        check(f"kappa={kappa} |g|", float(row["abs_g_hH2H2_GeV"]), kappa * g_abs)
        check(f"kappa={kappa} expected ratio", float(row["expected_kappa_g_squared"]), kappa ** 2)
        check(f"kappa={kappa} analytic sigma", float(row["analytic_sigma_pb"]), sigma_pb * kappa ** 2)
        if row["status"] == "NOT_EXECUTED_MADGRAPH_UNAVAILABLE_EGRESS_BLOCKED":
            if row["sigma_pb"] or row["integration_error_pb"] or row["relative_residual"]:
                failures.append(
                    f"kappa={kappa}: measured columns must stay empty while unexecuted"
                )

    # ---- 6. every model-scan point's yield ---------------------------------
    with open(OUTDIR / "model_reachability_scan.csv", newline="") as fh:
        scan = list(csv.DictReader(fh))
    if len(scan) > 7:
        failures.append(f"model scan exceeded the 7-point budget: {len(scan)}")
    for row in scan:
        if not row.get("kappa_g"):
            continue
        pid = row["point_id"]
        kappa = float(row["kappa_g"])
        g = float(row["g_hH2H2_GeV"])
        br = float(row["BR_bb"])
        check(f"{pid} kappa from |g|", kappa, abs(g) / g_abs)
        check(f"{pid} BR_bb_squared", float(row["BR_bb_squared"]), br * br)
        sig = sigma_pb * kappa * kappa
        check(f"{pid} sigma", float(row["sigma_H2H2_pb"]), sig)
        vis_p = sig * 1000.0 * br * br * a_eff
        check(f"{pid} visible sigma", float(row["visible_sigma_fb"]), vis_p)
        check(f"{pid} expected events", float(row["expected_trackless_events_139fb"]), vis_p * LUMI)
        rel_ctau = (float(row["ctau_mm"]) - FROZEN["ctau_mm"]) / FROZEN["ctau_mm"]
        check(f"{pid} ctau relative change", float(row["ctau_relative_change"]), rel_ctau, 1e-5)
        expected_label = (
            "ACCEPTANCE_REUSED_AT_FIXED_MASS_AND_NEARBY_LIFETIME" if abs(rel_ctau) <= 0.10
            else "RECAST_REQUIRED_FOR_EXACT_YIELD"
        )
        if row["acceptance_label"] != expected_label:
            failures.append(f"{pid}: acceptance label {row['acceptance_label']} != {expected_label}")
        if row["theory_ok_v1"] != "1" and row["yield_status"] == "PHYSICAL":
            failures.append(f"{pid}: theory-invalid point is labelled PHYSICAL")

    # ---- 7. summary cross-references ---------------------------------------
    summary = json.loads((OUTDIR / "result_summary.json").read_text())
    check("summary baseline events", summary["baseline"]["Trackless_expected_events"], n0)
    check("summary visible sigma", summary["baseline"]["Trackless_visible_sigma_fb"], vis)
    if summary["q1_sigma_scaling"]["fitted_exponent_p"] != 2.0:
        failures.append("summary exponent p is not 2.0")
    for i, row in enumerate(rows):
        s = summary["q2_q3_illustrative_thresholds"][i]
        check(f"summary threshold {i} kappa", s["kappa_g"], float(row["kappa_g"]))
        check(f"summary threshold {i} |g|",
              s["required_abs_g_hH2H2_GeV"], float(row["required_abs_g_hH2H2_GeV"]))

    valid = [r for r in scan if r["theory_ok_v1"] == "1"]
    k_max = max(float(r["kappa_g"]) for r in valid)
    check("summary max valid kappa", summary["q5_model_reachability"]["max_theory_valid_kappa_g"], k_max)
    check("summary max valid |g|",
          summary["q5_model_reachability"]["max_theory_valid_abs_g_hH2H2_GeV"], k_max * g_abs)
    k_n1 = float(rows[0]["kappa_g"])
    check("summary shortfall in kappa", summary["q5_model_reachability"]["shortfall_factor_in_kappa"], k_n1 / k_max)
    check("summary shortfall in rate", summary["q5_model_reachability"]["shortfall_factor_in_rate"], (k_n1 / k_max) ** 2)
    if summary["q5_model_reachability"]["threshold_reached"] is not False:
        failures.append("summary claims the threshold was reached")
    if k_max >= k_n1:
        failures.append("a theory-valid point reaches the first threshold; the verdict must change")

    atlas = json.loads((OUTDIR / "atlas_threshold.json").read_text())
    if atlas["status"] == "OFFICIAL_THRESHOLD_MAPPING_UNRESOLVED":
        for field in ("observed_S95", "expected_S95", "model_independent_visible_sigma_limit_fb"):
            if atlas["numerical_threshold"][field] is not None:
                failures.append(f"atlas_threshold.json: {field} must stay null while unresolved")
        if atlas["required_kappa_g"] is not None:
            failures.append("atlas_threshold.json: required_kappa_g must stay null while unresolved")

    if failures:
        print("R9 RECOMPUTATION CHECK: FAILED")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("R9 RECOMPUTATION CHECK: PASSED (all values re-derived from primary inputs)")
    print(f"  primary-input source: {source_mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
