# `data/2hdmc_scans/` — drop-in directory for a real 2HDMC scan

Put a real 2HDMC scan file here and run:

```bash
make diphoton-2hdmc-bridge
```

with **no extra arguments** — this directory is the first entry in the
bridge's default search roots (`scripts/09_link_2hdmc_to_diphoton.py`), so
anything valid placed here is discovered automatically.

## Filename pattern

The file must match one of the bridge's scan filename globs (`SCAN_PATTERNS`
in `scripts/09_link_2hdmc_to_diphoton.py`): `scan_tb_*.csv`,
`scan_tb_*.csv.gz`, `*.parquet`, `silver_all.parquet`, `*scan*.csv`, or
`*scan*.parquet`. If your file is named differently, or lives outside this
repo entirely, point at it directly instead:

```bash
make diphoton-2hdmc-bridge DIPHOTON_2HDMC_ARGS="--scan-root /path/to/file_or_dir --write-discovery-report"
```

## Required columns

`m_phi, total_width, br_gaga, positivity_ok, unitarity_ok, perturbativity_ok`
(optional: `tanbeta`, `point_id`). See
[`docs/recast/diphoton_minimum_recast_contract.md`](../../docs/recast/diphoton_minimum_recast_contract.md)
for the full column mapping, and
[`docs/recast/2hdmc_handoff_runbook.md`](../../docs/recast/2hdmc_handoff_runbook.md)
for the complete step-by-step handoff.

## Nothing here is committed

This directory is gitignored except this README — any scan file you drop
here stays local and is never pushed.
