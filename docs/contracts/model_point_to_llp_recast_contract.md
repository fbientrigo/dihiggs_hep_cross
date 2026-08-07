# Contract — 2HDM (or other extended-Higgs) model point -> LLP recast input

This document specifies how a future 2HDM (or other BSM scalar-pair) scan
point must be packaged before it can enter the recast layer in
`src/llp_recast/` and downstream boundary/signal tools. It exists so that
model-specific physics (2HDMC, UFO, MadGraph) stays decoupled from generic
geometry/efficiency math.

## Required columns per model point

| Column | Meaning | Notes |
|---|---|---|
| `model` | model tag, e.g. `2HDM_typeI` | free text, must be stable across a scan |
| `point_id` | unique id within the scan | must stay stable across 2HDMC, cards, MadGraph and recast artifacts |
| `m_scalar_GeV` | mass of the long-lived scalar | this is the scalar mass used downstream |
| `total_width_GeV` | total decay width of the scalar | from 2HDMC or the canonical width producer |
| `ctau_mm` | proper decay length | must equal `HBAR_C_GEV_MM / total_width_GeV`; do not supply an independently-guessed value |
| `sigma_production_fb` | production cross section for the relevant process | direct MadGraph result for this physical point |
| `sigma_production_unc_fb` | MadGraph integration uncertainty | integration/statistical uncertainty only; keep scale/PDF theory uncertainties separate |
| `BR_bb`, `BR_WW`, `BR_ZZ`, `BR_gg`, `BR_tautau` | exclusive branching ratios | must be internally consistent with the same physical point |
| `BR_hadronic_proxy` | hadronic-final-state proxy BR used by legacy recast tooling | compute from actual BRs; do not tune it to hit a target yield |
| `beta_gamma_source` | how `beta_gamma` was obtained | one of `assumed_flat`, `mg5_pythia_truth`, `analytic_kinematics` |
| `recast_channel_hint` | which ATLAS DV+jets SR this point is expected to land in | e.g. `trackless_sr`, `highpt_sr`, or `unknown` |

## Production policy for new physical scans

For a scan in which full 2HDM points change, production is evaluated with
MadGraph **per physical point**:

```text
canonical dihiggs.point.v2 row
  -> validated UFO / parameter mapping
  -> MadGraph process
  -> sigma_production_fb + sigma_production_unc_fb
  -> join back to the same point_id
```

Do not make `sigma = sigma0 * (g/g0)^2` the default production law for a
multi-parameter physical scan. When the point changes, additional couplings,
widths, interference contributions, coupling orders or normalized kinematics
may also change. MadGraph is sufficiently light for the intended workflow that
direct evaluation is the safer default.

A quadratic coupling relation may still be tested and documented as a
**controlled diagnostic** when exactly one relevant coupling is varied and the
rest of the production amplitude is demonstrated to be fixed. Historical R9/R10
or reduced coupling scans remain useful evidence in that restricted context;
they are not a substitute for per-point production in a general 2HDM scan.

## MadGraph provenance required upstream

The production artifact for each point must preserve, directly or by a linked
run manifest:

```text
point_id
UFO name/version/checksum
MadGraph version
process definition
sqrt(s)
PDF set
renormalization/factorization-scale setup
param-card checksum
run-card checksum
seed
number of generated/accepted events
sigma_LO
integration uncertainty
K factor or other rescaling in a separate field
banner/log/LHE paths or checksums
```

The downstream boundary layer consumes `sigma_production_fb` and
`sigma_production_unc_fb`; it should not duplicate or reinterpret the production
calculation.

## `BR_hadronic_proxy` consistency rule

`BR_hadronic_proxy` must be computed from the exclusive BRs you already have
(e.g. `BR_bb + BR_gg + (hadronic fraction of BR_WW) + (hadronic fraction of
BR_ZZ)`), not asserted independently. If you only have a subset of exclusive
BRs, say so explicitly in a `br_source` free-text column rather than silently
filling the rest with placeholder logic.

For the active H2 -> bb Trackless interpretation, the physical normalization is
instead kept explicitly as `BR_bb^2`, because the recast sample forces both H2
decays to bb.

## Forbidden / ambiguous mappings

- **`paper lambda_eff != 2HDM lambda6 / lambda7`.** The paper's effective hSS
  coupling is defined for its specific scalar-mixing setup. Do not plug a
  2HDM `lambda6`/`lambda7` value into `PaperScalarPoint.lambda_eff` and
  assume it means the same thing — a model-matching calculation is required.
- **`paper sin_theta != 2HDM sin(beta - alpha)`.** The paper's `sin_theta`
  controls scalar mixing and hence the LLP lifetime in its model. `sin(beta -
  alpha)` in a 2HDM controls SM-Higgs-coupling alignment. They are different
  physical objects; do not substitute one for the other when setting
  `ctau_mm`.
- **`sigma_production_fb` must be a direct production result for new physical
  scans.** Do not infer it from total width, lifetime or a generic `g/g0`
  rescaling. A one-coupling scaling law is allowed only as an explicitly scoped
  validation diagnostic.
- **BRs must be computed consistently.** `BR_hadronic_proxy` and `BR_bb` must
  trace back to actual same-point widths/branching ratios, never hand-picked to
  hit a target yield.

## How this flows into the recast / boundary layer

```text
2HDM scan point
  -> m_scalar_GeV, ctau_mm
  -> sigma_production_fb               [MadGraph, same point_id]
  -> BR_bb or other physical BRs        [canonical model point]
  -> Trackless Aeff                     [separate recast calibration]
  -> expected visible yield
```

For the active pair-produced H2 -> bb signal:

```text
sigma_4b      = sigma_production_fb * BR_bb^2
sigma_visible = sigma_4b * Trackless_Aeff
N_expected    = luminosity * sigma_visible
```

Production, decay and acceptance remain separate quantities with separate
scientific ownership.

`PaperScalarPoint` in `src/llp_recast/paper_model.py` intentionally does not
have a `from_2hdm_point()` constructor yet — building one before a real
model-matching calculation exists would silently launder an unvalidated
`lambda_eff`/`sin_theta` mapping into the recast. Add it only once that matching
is worked out.
