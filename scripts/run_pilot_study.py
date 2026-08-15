#!/usr/bin/env python3
"""Run the physical point MadGraph pilot campaign and save results."""

import csv
import json
import os
import sys
from pathlib import Path

# Add scripts directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from run_physical_point_madgraph import DEFAULT_PROC_DIR, run_single_physical_point_madgraph
from llp_recast.data_contract import REQUIRED_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_JSON = RESULTS_DIR / "canonical_model_points.json"
OUTPUT_CSV = RESULTS_DIR / "physical_point_madgraph_pilot.csv"
CARDS_DIR = RESULTS_DIR / "pilot_cards"


def run_pilot():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        points = json.load(f)

    results = []
    print(f"[PILOT] Starting evaluation of {len(points)} physical points...", flush=True)

    for i, pt in enumerate(points):
        pid = pt.get("point_id", f"point_{i}")
        tb = pt.get("tan_beta")
        g = pt["g_hH2H2_GeV"]
        print(f"[{i+1}/{len(points)}] {pid} (tan_beta={tb}, g={float(g):.2f}) ... ", end="", flush=True)
        res = run_single_physical_point_madgraph(
            pt,
            proc_dir=DEFAULT_PROC_DIR,
            cards_out_dir=CARDS_DIR,
            nevents=10000,
            seeds=[101, 107],
        )
        results.append(res)
        status = res["madgraph_status"]
        sigma = res["sigma_production_fb"]
        unc = res["sigma_production_unc_fb"]
        print(f"{status} | sigma = {sigma:.6f} +/- {unc:.6f} fb", flush=True)

    fieldnames = list(dict.fromkeys(list(REQUIRED_COLUMNS) + [
        "point_id",
        "m_h_GeV",
        "m_H2_GeV",
        "tan_beta",
        "lambda6",
        "M2_GeV2",
        "g_hH2H2_GeV",
        "ctau_physical_mm",
        "ctau_response_mm",
        "model_variant",
        "lifetime_mode",
        "BR_bb",
        "sigma_production_fb",
        "sigma_production_unc_fb",
        "sigma_source",
        "sigma_provenance",
        "madgraph_status",
        "madgraph_run_id_or_path",
    ]))

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"[PILOT] SUCCESS: Saved {len(results)} rows to {OUTPUT_CSV}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_pilot())
