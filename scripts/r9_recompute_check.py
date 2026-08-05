#!/usr/bin/env python3
"""Recompute the R9 baseline, illustrative thresholds and official ATLAS threshold."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"
RTOL = 1e-11


def close(a: float, b: float, name: str) -> None:
    if not math.isclose(a, b, rel_tol=RTOL, abs_tol=1e-14):
        raise SystemExit(f"{name}: {a} != {b}")


def main() -> int:
    baseline = json.loads((OUTDIR / "baseline.json").read_text())
    atlas = json.loads((OUTDIR / "atlas_threshold.json").read_text())
    summary = json.loads((OUTDIR / "result_summary.json").read_text())

    f = baseline["frozen_inputs"]
    sigma_pb = f["sigma_H2H2_pb"]["value"]
    br2 = f["BR_bb_squared"]["value"]
    aeff = f["Trackless_Aeff"]["value"]
    g0 = f["g_hH2H2_GeV"]["value"]
    lumi = baseline["luminosity_fb_inverse"]

    sigma4b = sigma_pb * 1000.0 * br2
    visible = sigma4b * aeff
    n0 = visible * lumi
    close(visible, baseline["recomputed"]["Trackless_visible_sigma_fb"], "visible")
    close(n0, baseline["recomputed"]["Trackless_expected_events"], "baseline events")

    with open(OUTDIR / "yield_thresholds.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        target = float(row["target_events"])
        rate = target / n0
        kappa = math.sqrt(rate)
        close(float(row["rate_multiplier"]), rate, f"N={target} rate")
        close(float(row["kappa_g"]), kappa, f"N={target} kappa")
        close(
            float(row["required_abs_g_hH2H2_GeV"]),
            kappa * g0,
            f"N={target} g",
        )

    if atlas["status"] != "OFFICIAL_THRESHOLD_RESOLVED":
        raise SystemExit("official ATLAS threshold is not resolved")
    nt = atlas["numerical_threshold"]
    if nt["observed_S95"] != 3.0:
        raise SystemExit("unexpected observed S95")
    exact_limit = nt["observed_S95"] / nt["integrated_luminosity_fb_inverse"]
    official_rate = nt["observed_S95"] / n0
    official_kappa = math.sqrt(official_rate)
    close(atlas["required_visible_sigma_fb"], exact_limit, "official visible sigma")
    close(atlas["required_rate_multiplier"], official_rate, "official rate")
    close(atlas["required_kappa_g"], official_kappa, "official kappa")
    close(atlas["required_abs_g_hH2H2_GeV"], official_kappa * g0, "official g")
    if round(exact_limit, 3) != nt["published_model_independent_visible_sigma_limit_fb"]:
        raise SystemExit("published 0.022 fb rounding cross-check failed")

    q4 = summary["q4_official_atlas_threshold"]
    close(q4["required_kappa_g"], official_kappa, "summary official kappa")
    if summary["scope_status"] != "THRESHOLD_NOT_REACHABLE_IN_THE_TESTED_FIXED_SLICE":
        raise SystemExit("scope verdict is not slice-qualified")
    if summary["q5_model_reachability"]["official_threshold_reached"] is not False:
        raise SystemExit("summary claims official threshold reached")

    print("R9 RECOMPUTATION CHECK: PASSED")
    print(f"  baseline events: {n0:.15g}")
    print(f"  official observed S95: {nt['observed_S95']}")
    print(f"  required kappa_g: {official_kappa:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
