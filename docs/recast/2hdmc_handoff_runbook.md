# 2HDMC scan handoff runbook

The single page to read the moment a real 2HDMC scan CSV/parquet file exists.
It only indexes the detailed contracts below — read those for schema
specifics.

## TL;DR

```bash
# 0. Drop the scan file here (or use --scan-root for anything elsewhere)
cp /path/to/real_scan.csv data/2hdmc_scans/

# 1. Bridge: physical 2HDMC points -> priority list + ATLAS context
make diphoton-2hdmc-bridge DIPHOTON_2HDMC_ARGS="--write-discovery-report"

# 2. Render MadGraph decks for the priority points
make madgraph-prepare

# 3. External, manual: run MadGraph yourself, fill in
#    data/manual/madgraph_xsec_runs.csv (or skip to Option B below)

# 4. Convert MadGraph runs into sigma inputs
make madgraph-sigma MADGRAPH_SIGMA_ARGS="--strict-point-ids"

# 5. Compute context-only sigma*BR ratios against ATLAS limits
make sigma-apply
```

## Step 0 — where to put the file

Drop it in [`data/2hdmc_scans/`](../../data/2hdmc_scans/README.md) — it's the
first entry in the bridge's default search roots, so a plain
`make diphoton-2hdmc-bridge` with no extra flags finds it. The filename must
match one of the bridge's scan globs (`scan_tb_*.csv`, `*scan*.csv`,
`*.parquet`, etc.) — see the README there for the full list, or use
`--scan-root /path/to/file_or_dir` if the file lives elsewhere or is named
differently. Required columns (`m_phi, total_width, br_gaga,
positivity_ok, unitarity_ok, perturbativity_ok`, optional `tanbeta`,
`point_id`) and the full column mapping are in
[`diphoton_minimum_recast_contract.md`](diphoton_minimum_recast_contract.md).

## Step 1 — `make diphoton-2hdmc-bridge`

Produces, under `outputs/diphoton_2hdmc_bridge/`: `2hdmc_scan_inventory.csv`
(which files were accepted/rejected and why), `theory_side_from_2hdmc.csv`
(physical points only), `priority_points_for_sigma.csv` (the compact ranked
list needing a cross section), `diphoton_comparison_needs_xsec.csv` (nearest
ATLAS limit context), and — with `--write-discovery-report` — a
`discovery_report.md` showing exactly what was searched/found/rejected. If it
reports zero accepted files, the report's "Next Command If Zero Accepted"
section gives the exact `--scan-root` invocation to try next.

## Step 2 — `make madgraph-prepare`

Renders one input deck per priority point under `outputs/madgraph_runs/`
from the committed templates and writes a blank-cross-section run skeleton.
No UFO/model is shipped and no cross section is invented. Details:
[`madgraph_run_preparation_contract.md`](../contracts/madgraph_run_preparation_contract.md).

## Step 3 — external, manual: run MadGraph yourself

This is the one non-automatable step. Run MadGraph per each deck's
`run_commands.sh`, record the cross sections, and fill in
`data/manual/madgraph_xsec_runs.csv` (or copy/edit the generated skeleton).
Schema: [`madgraph_xsec_output_contract.md`](../contracts/madgraph_xsec_output_contract.md).

**Option B — skip MadGraph entirely:** if you already have production cross
sections from another tool (SusHi, an HXSWG table, etc.), hand-fill
`data/manual/diphoton_sigma_inputs.csv` directly instead, following
[`diphoton_sigma_input_contract.md`](../contracts/diphoton_sigma_input_contract.md),
and skip straight to Step 5.

## Step 4 — `make madgraph-sigma`

Converts `data/manual/madgraph_xsec_runs.csv` into
`data/manual/diphoton_sigma_inputs.csv`. Use
`MADGRAPH_SIGMA_ARGS="--strict-point-ids"` to require every row match a real
priority point, and `--apply-k-factor` only if you intend the recorded
k-factor to actually scale the cross section (off by default).

## Step 5 — `make sigma-apply`

Joins everything into `outputs/diphoton_sigma_applied/diphoton_sigma_applied.csv`
— `sigma * BR(gamma gamma)` and its ratio to the nearest ATLAS observed/expected
limit, per point. See
[`data/manual/README.md`](../../data/manual/README.md) for the two entry
paths into this step side by side.

**Non-exclusion policy**: every row in every output above carries
`NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED` / `NOT_EXCLUSION_ACCEPTANCE_AND_SIGNAL_MODEL_REQUIRED`.
A ratio at or above one is a triage signal, never an exclusion claim.

## How do I know the pipeline actually works?

`tests/test_2hdmc_end_to_end.py` runs all five stages above against a
committed synthetic scan (`tests/fixtures/synthetic_2hdmc_scan.csv`) and a
synthetic MadGraph deliverable
(`tests/fixtures/synthetic_madgraph_xsec_runs.csv`), and asserts the final
ratios/status flags come out correctly — proof the chain works before any
real 2HDMC data exists:

```bash
python3 -m pytest tests/test_2hdmc_end_to_end.py -v
```

To see it work against the real drop-in directory by hand:

```bash
cp tests/fixtures/synthetic_2hdmc_scan.csv data/2hdmc_scans/
make diphoton-2hdmc-bridge
cat outputs/diphoton_2hdmc_bridge/README.md   # expect 14 priority points
rm data/2hdmc_scans/synthetic_2hdmc_scan.csv  # restore the placeholder-only dir
```

## Troubleshooting

- **Zero accepted files**: read `discovery_report.md`'s "Rejected Files"
  section for the reason (usually `MISSING_REQUIRED_COLUMNS`), and its "Next
  Command If Zero Accepted" for the exact `--scan-root` retry.
- **Parquet read errors**: install `pyarrow` or `fastparquet`.
- **Duplicate `point_id` errors** in `madgraph-sigma`/`sigma-apply`: each
  point must appear at most once in `madgraph_xsec_runs.csv` /
  `diphoton_sigma_inputs.csv`.

## Cross-reference index

| Doc | Covers |
|---|---|
| [`diphoton_minimum_recast_contract.md`](diphoton_minimum_recast_contract.md) | 2HDMC scan column mapping, experiment-side schema |
| [`madgraph_run_preparation_contract.md`](../contracts/madgraph_run_preparation_contract.md) | Deck rendering, skeleton schema |
| [`madgraph_xsec_output_contract.md`](../contracts/madgraph_xsec_output_contract.md) | `madgraph_xsec_runs.csv` schema, k-factor policy |
| [`diphoton_sigma_input_contract.md`](../contracts/diphoton_sigma_input_contract.md) | `diphoton_sigma_inputs.csv` schema (Option B) |
| [`data/manual/README.md`](../../data/manual/README.md) | Both entry paths into `sigma-apply`, side by side |
| [`data/madgraph/templates/README.md`](../../data/madgraph/templates/README.md) | Deck template placeholder contract |
| [`data/2hdmc_scans/README.md`](../../data/2hdmc_scans/README.md) | Drop-in directory details |
