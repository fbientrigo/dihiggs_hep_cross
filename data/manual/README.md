# `data/manual/` — hand-supplied and generated cross-section inputs

This directory holds the **external inputs** for the diphoton sigma-input triage
layer. Nothing here is downloaded automatically and nothing here is a physical
cross section produced by this repository — the MadGraph model/UFO does not exist
yet, so any real numbers must be supplied by you.

There are two supported entry points into the pipeline.

## Option A — via normalized MadGraph runs (recommended)

Create `madgraph_xsec_runs.csv` with one row per MadGraph run, following
[`docs/contracts/madgraph_xsec_output_contract.md`](../../docs/contracts/madgraph_xsec_output_contract.md)
(required key: `point_id`; at least one of `xsec_pb` / `xsec_fb`). Then:

```bash
make madgraph-sigma MADGRAPH_SIGMA_ARGS="--strict-point-ids"   # add --apply-k-factor only if intended
make sigma-apply
```

`make madgraph-sigma` writes `diphoton_sigma_inputs.csv` here (it is **generated**;
do not hand-edit it if you use this path — it will be overwritten). Conversions:
`xsec_fb` takes precedence over `xsec_pb`; otherwise `sigma_total_fb = 1000 * xsec_pb`.
A `k_factor` is recorded in `sigma_notes` but **not** applied unless `--apply-k-factor`
is passed.

## Option B — hand-filled sigma inputs directly

If you already have production cross sections from another tool (SusHi, an HXSWG
table, etc.), skip MadGraph and fill `diphoton_sigma_inputs.csv` by hand, following
[`docs/contracts/diphoton_sigma_input_contract.md`](../../docs/contracts/diphoton_sigma_input_contract.md)
(key `point_id`; supply `sigma_total_fb` or the `sigma_ggF_fb` / `sigma_VBF_fb`
components). Then:

```bash
make sigma-apply
```

## Before either input exists

Both `make` targets run today with no input files present: they produce
schema-stable **empty** outputs (correct headers, zero rows) plus fill-in
templates. That is the expected state until real inputs are available — it is not
an error.

## Non-exclusion reminder

The downstream `sigma * BR(gamma gamma)` ratios against ATLAS diphoton limits are
**context-only triage**, never exclusions. A ratio above one only flags a point for
careful treatment of production rate, fiducial-vs-total acceptance, width
hypothesis, and signal model. See the contract docs for the full policy.
