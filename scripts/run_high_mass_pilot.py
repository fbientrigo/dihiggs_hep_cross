#!/usr/bin/env python3
"""Direct MadGraph pilot: historical 150 GeV control + two high-mass points
from the science/high-mass-valid-point-atlas search (dihiggs repo).

Runs pp -> H2 H2 directly via the existing validated proc_output process
directory (see scripts/run_physical_point_madgraph.py), two seeds per point,
10000 events per seed. Writes full provenance (cards, banner hashes, cross
sections, uncertainties) to results/high_mass_pilot/pilot_results.json.

Mandatory closure requirement: the 150 GeV control point's sigma_production_fb
must match the previously established value (0.230291 fb, rel_tol=0.03, per
tests/test_run_physical_point_madgraph.py::test_benchmark_closure_execution).
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from run_physical_point_madgraph import (  # noqa: E402
    DEFAULT_PROC_DIR,
    run_single_physical_point_madgraph,
)

OUT_DIR = REPO_ROOT / "results" / "high_mass_pilot"
CARDS_DIR = OUT_DIR / "cards"

# Historical control point (canonical 150 GeV anchor, tan_beta=300000 near-decoupling).
CONTROL_POINT = {
    "point_id": "H2scan_mH150_tb300000",
    "mh_input_GeV": 125.13,
    "mH_input_GeV": 150.0,
    "g_hH2H2_GeV": 63.59142520075966,
    "ctau_mm": 4.326221529733112,
    "br_bb": 0.7567374858085787,
    "total_width_GeV": 4.56118529862185e-14,
    "tan_beta_input": 300000.0,
    "lambda6_input": 1e-10,
    "M2_input_GeV2": 22499.9999995,
    "source": "historical anchor, docs/pilots/high_mass_h2_v1 (dihiggs repo) / prior validated MadGraph closure",
}

# From dihiggs-point-search PHYSICAL_POINT_SCAN search (theory-valid,
# HBHS_BLOCKED, see docs/campaigns/high_mass_h2_physical_point_scan_v1/
# high_mass_valid_points.csv in the dihiggs repo, commit fa19d06). Selected
# as the first accepted point per region sorted by point_id (deterministic,
# not cherry-picked for a favorable cross section).
INTERMEDIATE_POINT = {
    "point_id": "point_011af49c15561f96",
    "mh_input_GeV": 125.13,
    "mH_input_GeV": 200.0,
    "g_hH2H2_GeV": 260.89501608064444,
    "ctau_mm": 1.3642978031208773e-11,  # physical ctau; NOT used for the fixed-response-ctau ATLAS pilot
    "br_bb": 0.04288432725378132,
    "total_width_GeV": 0.014463629564498886,
    "tan_beta_input": 2.0,
    "lambda6_input": 1e-10,
    "M2_input_GeV2": 10000.0,
    "source": "dihiggs-point-search R200_below_hh, science/high-mass-valid-point-atlas commit fa19d06",
}

HIGHEST_POINT = {
    "point_id": "point_0960bd688a662562",
    "mh_input_GeV": 125.13,
    "mH_input_GeV": 250.0,
    "g_hH2H2_GeV": 253.3363616900449,
    "ctau_mm": 4.916438169370716e-12,  # physical ctau; NOT used for the fixed-response-ctau ATLAS pilot
    "br_bb": 0.018529097265771073,
    "total_width_GeV": 0.04013616638755717,
    "tan_beta_input": 2.0,
    "lambda6_input": 0.0,
    "M2_input_GeV2": 36300.0,
    "source": "dihiggs-point-search R250_near_hh_threshold, science/high-mass-valid-point-atlas commit fa19d06",
}

POINTS = [CONTROL_POINT, INTERMEDIATE_POINT, HIGHEST_POINT]
NEVENTS = 10000
SEEDS = [101, 107]
CLOSURE_TARGET_FB = 0.230291
CLOSURE_REL_TOL = 0.03


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)

    mg5_version = ""
    version_file = DEFAULT_PROC_DIR / "MGMEVersion.txt"
    if version_file.exists():
        mg5_version = version_file.read_text().strip()

    results = []
    for point in POINTS:
        print(f"=== running {point['point_id']} (mH2={point['mH_input_GeV']} GeV) ===", file=sys.stderr)
        t0 = time.time()
        res = run_single_physical_point_madgraph(
            point,
            proc_dir=DEFAULT_PROC_DIR,
            cards_out_dir=CARDS_DIR,
            nevents=NEVENTS,
            seeds=SEEDS,
        )
        res["wall_time_seconds"] = round(time.time() - t0, 1)
        res["source"] = point.get("source", "")
        res["mg5_version"] = mg5_version
        res["nevents_per_seed"] = NEVENTS
        results.append(res)
        print(
            f"    status={res['madgraph_status']} sigma_fb={res.get('sigma_production_fb')} "
            f"unc_fb={res.get('sigma_production_unc_fb')} wall={res['wall_time_seconds']}s",
            file=sys.stderr,
        )

    # --- mandatory closure check on the control point ---
    control_res = results[0]
    closure_ok = False
    if control_res["madgraph_status"] == "VALID":
        sigma = control_res["sigma_production_fb"]
        closure_ok = math.isfinite(sigma) and math.isclose(sigma, CLOSURE_TARGET_FB, rel_tol=CLOSURE_REL_TOL)
    control_res["closure_check"] = {
        "target_fb": CLOSURE_TARGET_FB,
        "rel_tol": CLOSURE_REL_TOL,
        "observed_fb": control_res.get("sigma_production_fb"),
        "passed": closure_ok,
    }

    manifest = {
        "schema": "dihiggs_hep_cross.high_mass_pilot.v1",
        "proc_dir": str(DEFAULT_PROC_DIR),
        "mg5_version": mg5_version,
        "nevents_per_seed": NEVENTS,
        "seeds": SEEDS,
        "control_point_closure_check": control_res["closure_check"],
        "results": results,
    }
    out_path = OUT_DIR / "pilot_results.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    print(f"Wrote {out_path}", file=sys.stderr)
    print(f"CLOSURE_OK={closure_ok}", file=sys.stderr)
    return 0 if closure_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
