#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from llp_recast.hepdata_yaml import find_yaml_tables, summarize_table


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory local ATLAS DV+jets HEPData YAML tables")
    ap.add_argument("--yaml-root", default="data/hepdata/atlas_dvjets_139fb/yaml_raw")
    ap.add_argument("--outdir", default="outputs/hepdata_inventory")
    args = ap.parse_args()

    root = Path(args.yaml_root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    tables = find_yaml_tables(root)
    summaries = [summarize_table(p, root=root) for p in tables]
    counts = Counter(s.group for s in summaries)

    csv_path = outdir / "atlas_dvjets_table_inventory.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(summaries[0]).keys()) if summaries else ["path"])
        writer.writeheader()
        for s in summaries:
            writer.writerow(asdict(s))

    md_path = outdir / "atlas_dvjets_table_inventory.md"
    lines = []
    lines.append("# ATLAS DV+jets HEPData inventory\n")
    lines.append(f"YAML root: `{root}`\n")
    lines.append(f"Total YAML files: **{len(tables)}**\n")
    lines.append("## Counts by group\n")
    for group, n in sorted(counts.items()):
        lines.append(f"- `{group}`: {n}")
    lines.append("\n## Candidate tables for first recast\n")
    for s in summaries:
        if s.group in {"yields", "cross_section_limits", "acceptance", "event_efficiency", "vertex_efficiency", "cutflow"}:
            lines.append(f"- `{s.path}` — {s.group}")
            if s.dependent_headers:
                lines.append(f"  - dependent: {s.dependent_headers[:220]}")
            if s.independent_headers:
                lines.append(f"  - independent: {s.independent_headers[:220]}")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {md_path}")
    print("[COUNTS]")
    for group, n in sorted(counts.items()):
        print(f"  {group:24s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
