# Contract — 2HDM (or other extended-Higgs) model point -> LLP recast input

This document specifies how a future 2HDM (or other BSM scalar-pair) scan
point must be packaged before it can enter the recast layer in
`src/llp_recast/` and `scripts/03_paper_s_benchmark_proxy.py`. It exists so
that model-specific physics (2HDMC, HDECAY, MadGraph) stays decoupled from
the generic geometry/efficiency math in `recast_math.py`.

## Required columns per model point

| Column | Meaning | Notes |
|---|---|---|
| `model` | model tag, e.g. `2HDM_typeII` | free text, must be stable across a scan |
| `point_id` | unique id within the scan | e.g. row index or hash of input parameters |
| `m_scalar_GeV` | mass of the long-lived scalar | this is the `mS_GeV` used downstream |
| `total_width_GeV` | total decay width of the scalar | from 2HDMC or your width calculator |
| `ctau_mm` | proper decay length | must equal `HBAR_C_GEV_MM / total_width_GeV`; do not supply an independently-guessed value |
| `sigma_production_fb` | production cross section for the relevant process | generated or supplied, see "Forbidden mappings" below |
| `BR_bb`, `BR_WW`, `BR_ZZ`, `BR_gg`, `BR_tautau` | exclusive branching ratios | must sum to <= 1 across all channels you track |
| `BR_hadronic_proxy` | hadronic-final-state proxy BR used by the recast | computed consistently from the BRs above, see below |
| `beta_gamma_source` | how `beta_gamma` was obtained | one of `assumed_flat`, `mg5_pythia_truth`, `analytic_kinematics` |
| `recast_channel_hint` | which ATLAS DV+jets SR this point is expected to land in | e.g. `trackless_sr`, `highpt_sr`, or `unknown` |

## `BR_hadronic_proxy` consistency rule

`BR_hadronic_proxy` must be computed from the exclusive BRs you already have
(e.g. `BR_bb + BR_gg + (hadronic fraction of BR_WW) + (hadronic fraction of
BR_ZZ)`), not asserted independently. If you only have a subset of exclusive
BRs, say so explicitly in a `br_source` free-text column rather than silently
filling the rest with the paper's placeholder logic in
`llp_recast.paper_model.br_hadronic_proxy`.

## Forbidden / ambiguous mappings

- **`paper lambda_eff != 2HDM lambda6 / lambda7`.** The paper's effective hSS
  coupling is defined for its specific scalar-mixing setup. Do not plug a
  2HDM `lambda6`/`lambda7` value into `PaperScalarPoint.lambda_eff` and
  assume it means the same thing — a model-matching calculation is required
  first, and does not exist in this codebase yet.
- **`paper sin_theta != 2HDM sin(beta - alpha)`.** The paper's `sin_theta`
  controls scalar mixing and hence the LLP lifetime in its model. `sin(beta -
  alpha)` in a 2HDM controls SM-Higgs-coupling alignment. They are different
  physical objects; do not substitute one for the other when setting
  `ctau_mm`.
- **`sigma_production_fb` must be generated or supplied, never inferred from
  width.** A total width fixes the lifetime, not the production rate. Do not
  back out a cross section from `total_width_GeV`.
- **BRs must be computed consistently.** `BR_hadronic_proxy` must trace back
  to actual exclusive branching ratios (or be explicitly flagged as a
  placeholder mode), never hand-picked to hit a target yield.

## How this flows into the recast layer

```text
2HDM scan point (this contract)
  -> m_scalar_GeV, ctau_mm            -> llp_recast.recast_math (geometry, P_decay)
  -> BR_hadronic_proxy                -> br_factor = BR_hadronic_proxy ** 2 (two LLPs)
  -> sigma_production_fb              -> expected_yield(lumi, sigma, br_factor, aeff_proxy)
  -> recast_channel_hint              -> which HEPData tidy tables (outputs/hepdata_tidy/*.csv)
                                          are the relevant efficiency/limit anchors
```

`PaperScalarPoint` in `src/llp_recast/paper_model.py` intentionally does not
have a `from_2hdm_point()` constructor yet — building one before a real
model-matching calculation exists would silently launder an unvalidated
`lambda_eff`/`sin_theta` mapping into the recast. Add it only once that
matching is worked out.
