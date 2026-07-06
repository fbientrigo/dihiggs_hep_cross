#!/usr/bin/env python3
"""Flatten selected ATLAS DV+jets HEPData YAML tables into tidy CSVs.

These are analysis products (acceptance, efficiencies, cutflows, yields,
cross-section limits) published by ATLAS for their own SUSY EWK/strong
benchmarks. Flattening them does not give us reconstructed events, and most
of these tables are indexed by a chargino/neutralino mass and lifetime, not
by our scalar-S mass grid -- see docs/recast/current_limitations.md.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from llp_recast.hepdata_yaml import tidy_rows

RADIUS_RE = re.compile(r"vertex_efficiency_r_(\d+)(?:_(\d+))?_mm")

SIMPLE_TABLES = {
    "acceptance_trackless_ewk.yaml": "acceptance_trackless_ewk.csv",
    "cutflow_trackless_ewk.yaml": "cutflow_trackless_ewk.csv",
    "yields_trackless_sr_observed.yaml": "yields_trackless_sr_observed.csv",
    "yields_trackless_sr_expected_ewk.yaml": "yields_trackless_sr_expected_ewk.csv",
    "excl_xsec_ewk.yaml": "excl_xsec_ewk.csv",
}

EVENT_EFFICIENCY_FILES = [
    "event_efficiency_trackless_r_1150_mm.yaml",
    "event_efficiency_trackless_r_1150_3870_mm.yaml",
    "event_efficiency_trackless_r_3870_mm.yaml",
]


def radius_bin_from_filename(name: str) -> tuple[str, float | None, float]:
    m = RADIUS_RE.match(name)
    if not m:
        return name, None, float("nan")
    lo_str, hi_str = m.group(1), m.group(2)
    if hi_str is None:
        # ponytail: single-number filenames are the innermost bin, "< hi".
        return f"{lo_str}_mm", None, float(lo_str)
    return f"{lo_str}_{hi_str}_mm", float(lo_str), float(hi_str)


def write_table(root: Path, filename: str, out_path: Path) -> int:
    rows = tidy_rows(root / filename)
    pd.DataFrame.from_records(rows).to_csv(out_path, index=False)
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="Tidy-extract selected ATLAS DV+jets HEPData tables")
    ap.add_argument(
        "--yaml-root",
        default="data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml",
    )
    ap.add_argument("--outdir", default="outputs/hepdata_tidy")
    args = ap.parse_args()

    root = Path(args.yaml_root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for filename, out_name in SIMPLE_TABLES.items():
        n = write_table(root, filename, outdir / out_name)
        print(f"[OK] {filename} -> {out_name} ({n} rows)")

    event_eff_rows = []
    for filename in EVENT_EFFICIENCY_FILES:
        event_eff_rows.extend(tidy_rows(root / filename))
    pd.DataFrame.from_records(event_eff_rows).to_csv(outdir / "event_efficiency_trackless.csv", index=False)
    print(f"[OK] {len(EVENT_EFFICIENCY_FILES)} event_efficiency files -> event_efficiency_trackless.csv ({len(event_eff_rows)} rows)")

    vertex_files = sorted(root.glob("vertex_efficiency_r_*_mm.yaml"))
    vertex_rows = []
    for f in vertex_files:
        bin_label, radius_lo_mm, radius_hi_mm = radius_bin_from_filename(f.name)
        for row in tidy_rows(f):
            row["radius_bin_label"] = bin_label
            row["radius_lo_mm"] = radius_lo_mm
            row["radius_hi_mm"] = radius_hi_mm
            vertex_rows.append(row)
    pd.DataFrame.from_records(vertex_rows).to_csv(outdir / "vertex_efficiency_grid.csv", index=False)
    print(f"[OK] {len(vertex_files)} vertex_efficiency files -> vertex_efficiency_grid.csv ({len(vertex_rows)} rows)")

    print("[NOTE] These are ATLAS analysis products (acceptance/efficiency/cutflow/yields/limits),")
    print("[NOTE] not reconstructed events, and mostly indexed by SUSY EWK benchmark mass/lifetime, not scalar-S mass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
