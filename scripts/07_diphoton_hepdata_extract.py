#!/usr/bin/env python3
"""Inventory + tidy-extract the ATLAS HIGG-2018-27 diphoton HEPData bundle.

Reuses src/llp_recast/hepdata_yaml.py (already generic across HEPData
submissions) rather than writing a second parser.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from llp_recast.hepdata_yaml import find_yaml_tables, summarize_table, tidy_rows

# Tables directly relevant to the spin-0 (2HDM H2) sigma*BR(gamma gamma) limit.
SCALAR_LIMIT_TABLES = {
    "Limit1D_NW_Scalar.yaml": "width_hypothesis=NWA",
    "Limit1D_LW002_Scalar.yaml": "width_hypothesis=2pct",
    "Limit1D_LW006_Scalar.yaml": "width_hypothesis=6pct",
    "Limit1D_LW01_Scalar.yaml": "width_hypothesis=10pct",
    "Limit2D_Scalar.yaml": "width_hypothesis=2D_grid",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory + tidy ATLAS HIGG-2018-27 diphoton HEPData tables")
    ap.add_argument("--yaml-root", default="data/hepdata/atlas_diphoton_higg_2018_27/yaml_raw")
    ap.add_argument("--inventory-outdir", default="outputs/diphoton_higg_2018_27_inventory")
    ap.add_argument("--tidy-outdir", default="data/hepdata/atlas_diphoton_higg_2018_27/tables_tidy")
    args = ap.parse_args()

    root = Path(args.yaml_root)
    inv_outdir = Path(args.inventory_outdir)
    tidy_outdir = Path(args.tidy_outdir)
    inv_outdir.mkdir(parents=True, exist_ok=True)
    tidy_outdir.mkdir(parents=True, exist_ok=True)

    tables = find_yaml_tables(root)
    summaries = [summarize_table(p, root=root) for p in tables]
    counts = Counter(s.group for s in summaries)

    csv_path = inv_outdir / "table_inventory.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(summaries[0]).keys()))
        writer.writeheader()
        for s in summaries:
            writer.writerow(asdict(s))

    md_path = inv_outdir / "table_inventory.md"
    lines = [
        "# ATLAS HIGG-2018-27 (arXiv:2102.13405) HEPData inventory",
        "",
        f"YAML root: `{root}`",
        f"Total YAML tables: **{len(tables)}**",
        "",
        "## Counts by group",
        "",
    ]
    for group, n in sorted(counts.items()):
        lines.append(f"- `{group}`: {n}")
    lines += [
        "",
        "## Spin-0 (scalar) sigma*BR(gamma gamma) limit tables — primary recast target",
        "",
    ]
    for fname, note in SCALAR_LIMIT_TABLES.items():
        match = [s for s in summaries if s.filename == fname]
        if not match:
            lines.append(f"- `{fname}` — NOT FOUND ({note})")
            continue
        s = match[0]
        lines.append(f"- `{fname}` ({note})")
        lines.append(f"  - independent: {s.independent_headers}")
        lines.append(f"  - dependent: {s.dependent_headers[:300]}")
        lines.append(f"  - n rows (first dep series): {s.n_values_first_dep}")
    lines += [
        "",
        "## All other tables",
        "",
    ]
    for s in summaries:
        if s.filename in SCALAR_LIMIT_TABLES:
            continue
        lines.append(f"- `{s.path}` — {s.group}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Tidy-extract just the spin-0 scalar limit tables (the diphoton recast contract's experiment side).
    for fname in SCALAR_LIMIT_TABLES:
        matches = [p for p in tables if p.name == fname]
        if not matches:
            continue
        rows = tidy_rows(matches[0])
        out_csv = tidy_outdir / (Path(fname).stem + "_tidy.csv")
        if rows:
            fieldnames = sorted({k for r in rows for k in r})
            with out_csv.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"[OK] wrote {out_csv} ({len(rows)} rows)")

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {md_path}")
    print("[COUNTS]")
    for group, n in sorted(counts.items()):
        print(f"  {group:24s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
