# Contract — normalized MadGraph cross-section output

This contract defines the **stable interface expected from future MadGraph runs**.
It exists so the analysis pipeline can be prepared before the UFO/model and full
MG5 command chain are finalized.

The pipeline deliberately does **not** parse fragile MadGraph log files directly.
Instead, each MadGraph run should be summarized into one row of a normalized CSV.
That CSV is converted into the existing diphoton sigma-input contract by:

```bash
make madgraph-sigma
```

## Default input

```text
data/manual/madgraph_xsec_runs.csv
```

## Default output

```text
data/manual/diphoton_sigma_inputs.csv
```

That output can then be consumed by:

```bash
make sigma-apply
```

## Running before vs after the MadGraph model exists

This layer is intentionally usable **today**, before any UFO/model or MG5 process
chain exists.

- **Before** `data/manual/madgraph_xsec_runs.csv` exists: `make madgraph-sigma` still
  runs. It writes a fill-in template at
  `outputs/madgraph_sigma_ingest/madgraph_xsec_template.csv` and a schema-stable, empty
  `data/manual/diphoton_sigma_inputs.csv` (header only). Nothing is fabricated: with no
  runs table, zero sigma rows are produced. `make sigma-apply` then produces an
  empty-but-correctly-shaped `diphoton_sigma_applied.csv`. This is the expected state
  until real MadGraph output is available.
- **After** `data/manual/madgraph_xsec_runs.csv` exists (one row per MadGraph run, columns
  below): `make madgraph-sigma MADGRAPH_SIGMA_ARGS="--strict-point-ids"` converts it into
  `data/manual/diphoton_sigma_inputs.csv`, and `make sigma-apply` computes the
  context-only `sigma * BR(gamma gamma)` ratios.

## Required columns

| Column | Meaning |
|---|---|
| `point_id` | Must match a row in `outputs/diphoton_2hdmc_bridge/priority_points_for_sigma.csv` |
| `xsec_pb` or `xsec_fb` | Cross section from MadGraph; at least one must be supplied |

If both `xsec_fb` and `xsec_pb` are supplied, `xsec_fb` takes precedence.

## Recommended provenance columns

| Column | Meaning |
|---|---|
| `mg_run_name` | MadGraph run tag, e.g. `run_01` |
| `process` | Process string or short description |
| `sqrt_s_TeV` | Collider energy |
| `xsec_unc_pb` | MadGraph-reported uncertainty if available |
| `k_factor` | Optional K-factor; recorded but not applied unless `--apply-k-factor` is used |
| `production_mode` | `ggF`, `VBF`, `ggF+VBF`, or `unknown` |
| `madgraph_version` | MG5_aMC version string |
| `model_name` | UFO/model tag |
| `param_card_path` | Path to the param card used for this run |
| `run_card_path` | Path to the run card used for this run |
| `banner_path` | Path to the MG banner file |
| `lhe_path` | Path to the LHE file, if generated |
| `notes` | Free-text caveats |

## Generated sigma-input mapping

| Output column | Rule |
|---|---|
| `sigma_total_fb` | `xsec_fb` if present, otherwise `1000 * xsec_pb` |
| `sigma_ggF_fb` | set equal to `sigma_total_fb` only when `production_mode == ggF` |
| `sigma_VBF_fb` | set equal to `sigma_total_fb` only when `production_mode == VBF` |
| `sigma_source` | includes `MadGraph_normalized_table`, version, and run name if supplied |
| `sigma_notes` | carries process/model/cards/banner/LHE metadata |

## K-factor policy

By default, `k_factor` is only recorded in `sigma_notes`; it is not applied.  To
apply it explicitly:

```bash
make madgraph-sigma MADGRAPH_SIGMA_ARGS="--apply-k-factor"
```

This avoids silently mixing LO MadGraph output with higher-order corrections.

## Strict validation

To require that every MadGraph row corresponds to an existing priority point:

```bash
make madgraph-sigma MADGRAPH_SIGMA_ARGS="--strict-point-ids"
```

## Minimal example

```csv
point_id,mg_run_name,process,sqrt_s_TeV,xsec_pb,xsec_fb,xsec_unc_pb,k_factor,production_mode,madgraph_version,model_name,param_card_path,run_card_path,banner_path,lhe_path,notes
scan_tb_10000:row42,run_01,g g > h2 > a a,13,0.012,,,1.0,ggF,MG5_aMC_vX.Y,2HDM_UFO,cards/param_card.dat,cards/run_card.dat,Events/run_01/run_01_tag_1_banner.txt,Events/run_01/unweighted_events.lhe.gz,example only
```

## Non-exclusion policy

This contract only supplies production-rate inputs.  It does not validate
fiducial acceptance, detector acceptance, width interpolation, or signal model
compatibility.  Downstream outputs must remain marked as context-only until
those checks are performed.
