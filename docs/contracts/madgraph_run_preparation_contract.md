# Contract — MadGraph run preparation (the basis)

This contract defines the **MadGraph basis**: how 2HDMC diphoton priority points
become MadGraph input decks and a normalized run-table *skeleton*, before any
UFO/model or MadGraph install exists.

It sits between the priority bridge and the cross-section ingest:

```text
09_link_2hdmc_to_diphoton  ->  priority_points_for_sigma.csv
        |
        v
12_prepare_madgraph_runs   ->  input decks + madgraph_xsec_runs_skeleton.csv   (this contract)
        |   (run MadGraph externally, fill in the cross sections)
        v
data/manual/madgraph_xsec_runs.csv
        |
        v
11_ingest_madgraph_xsec    ->  data/manual/diphoton_sigma_inputs.csv           (make madgraph-sigma)
        |
        v
10_apply_sigma_inputs      ->  context-only sigma * BR ratios                  (make sigma-apply)
```

## What it does — and does not — do

It **does**: render one input deck per priority point from the committed templates
in `data/madgraph/templates/`, and write a normalized run-table skeleton with the
process, placeholder model, and card paths filled in.

It **does not**: ship or generate a UFO/model, install or run MadGraph, or invent
any cross section. Every skeleton cross-section field (`xsec_pb`, `xsec_fb`,
`xsec_unc_pb`, `madgraph_version`, `banner_path`, `lhe_path`) is left blank on
purpose. Preparing decks is not an exclusion and produces no physical result.

## Run it

```bash
make madgraph-prepare
# or, with options:
make madgraph-prepare MADGRAPH_PREPARE_ARGS="--model-name MY_2HDM_UFO --sqrt-s-tev 13 --process 'g g > h2'"
```

## Default inputs / outputs

| Path | Role |
|---|---|
| `outputs/diphoton_2hdmc_bridge/priority_points_for_sigma.csv` | input priority points |
| `data/madgraph/templates/*.tmpl` | committed deck templates (the basis) |
| `outputs/madgraph_runs/<run_tag>/` | rendered per-point deck (proc/run/param cards + `run_commands.sh`) |
| `outputs/madgraph_runs/madgraph_xsec_runs_skeleton.csv` | normalized run-table skeleton (blank cross sections) |

`outputs/` is gitignored; the templates under `data/madgraph/templates/` are the
committed, version-controlled part.

## Skeleton schema

The skeleton uses the fill-in template schema of
[`madgraph_xsec_output_contract.md`](madgraph_xsec_output_contract.md)
(`llp_recast.madgraph.MADGRAPH_TEMPLATE_COLUMNS`). Pre-filled by this step:
`mg_run_name`, `process`, `sqrt_s_TeV`, `production_mode`, `model_name`,
`param_card_path`, `run_card_path`, and `notes` = `PREPARED_DECK_AWAITING_MADGRAPH_RUN;NO_XSEC_FABRICATED`.

## Empty-input behavior

With no priority points (no local 2HDMC scan), the step still runs: it writes a
schema-stable empty skeleton (header only) and no decks. This is the expected
state until a real scan is available; it is not an error.

## After a real MadGraph run exists

1. Replace the `TODO_SUPPLY_UFO_MODEL` placeholder with a real UFO/model.
2. Run MadGraph per `<run_tag>/proc_card.dat` (see each deck's `run_commands.sh`).
3. Record each cross section (pb or fb) into the skeleton rows.
4. Copy the filled skeleton to `data/manual/madgraph_xsec_runs.csv`, then:

```bash
make madgraph-sigma MADGRAPH_SIGMA_ARGS="--strict-point-ids"
make sigma-apply
```

## Non-exclusion policy

Everything downstream stays context-only until acceptance, fiducial-vs-total
treatment, width interpolation, and signal model are validated. This preparation
layer never makes an exclusion statement.
