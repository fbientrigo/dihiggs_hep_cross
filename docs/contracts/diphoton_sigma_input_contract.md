# Contract — external production cross-section input for diphoton triage

This contract defines the minimal table needed to turn the existing diphoton
priority list into a `sigma * BR(gamma gamma)` triage table.

This is **not** an exclusion contract.  It only computes ratios against the
nearest public ATLAS scalar diphoton limit-context row.

## Input file

Default path:

```text
data/manual/diphoton_sigma_inputs.csv
```

The file is consumed by:

```bash
make sigma-apply SIGMA_APPLY_ARGS="--sigma-input data/manual/diphoton_sigma_inputs.csv"
```

## Required key

| Column | Meaning |
|---|---|
| `point_id` | Must match `outputs/diphoton_2hdmc_bridge/priority_points_for_sigma.csv` |

## Cross-section columns

Supply either `sigma_total_fb` or one/both production-mode components.

| Column | Meaning | Rule |
|---|---|---|
| `sigma_ggF_fb` | gluon-fusion production cross section in fb | optional |
| `sigma_VBF_fb` | VBF production cross section in fb | optional |
| `sigma_total_fb` | total production cross section in fb | optional; if present, it overrides the component sum |

All sigma values must be non-negative.

## Provenance columns

| Column | Meaning |
|---|---|
| `sigma_source` | e.g. `SusHi`, `MadGraph`, `HXSWG_table`, `manual_test` |
| `production_mode` | e.g. `ggF`, `VBF`, `ggF+VBF` |
| `sigma_notes` | free-text provenance/caveat note |

## Output interpretation

The generated table contains:

| Column | Meaning |
|---|---|
| `sigma_times_br_gaga_fb` | `sigma_total_fb * br_gaga` |
| `ratio_to_observed_limit_context_only` | context-only ratio to nearest observed limit row |
| `ratio_to_expected_limit_context_only` | context-only ratio to nearest expected limit row |
| `ratio_observed_ge1_context_only` | `TRUE_CONTEXT_ONLY`, `FALSE_CONTEXT_ONLY`, or `UNKNOWN` |
| `quality_flags` | includes `NOT_EXCLUSION_ACCEPTANCE_AND_SIGNAL_MODEL_REQUIRED` on every row |

A ratio above one is a triage signal only.  Before any exclusion statement, the
production-rate source, fiducial-vs-total treatment, acceptance, signal model,
and width hypothesis must be validated.
