# Operational notes — arXiv:2606.01681 (`pp -> gg -> h* -> S S`)

## 1. What exactly are we trying to reproduce?

The paper's workflow, not (yet) its numeric exclusion curves:

```text
scalar model point (mS, lifetime/ctau, coupling)
  -> branching fractions of S
  -> displaced decay probability in the ATLAS ID
  -> DV+jets acceptance and efficiencies
  -> expected signal yield at 139 fb^-1
  -> comparison with ATLAS public DV+jets limits
```

`pp -> gg -> h* -> S S` is a pair-production topology through an off-shell
SM-like Higgs. ATLAS's public DV+jets search (HEPData ins2628398) is the
detector-side tool the paper recasts; it was not run on the paper's own
signal model by ATLAS, so there is no ATLAS-published exclusion curve for
this exact model in the local HEPData bundle. What we currently have is
ATLAS's own SUSY EWK (chargino/neutralino) and SUSY strong benchmark
efficiencies/limits, used here as scale anchors.

## 2. Which parts are currently proxy-only?

- `sigma_gg_hstar_SS_fb` / `sigma_fb_assumed`: flat placeholder (1 fb), not
  from MadGraph.
- `beta_gamma_assumed`: flat placeholder (1.0), not from truth kinematics.
- `BR_hadronic_proxy`: `paper_placeholder` mode in
  `llp_recast.paper_model.br_hadronic_proxy` — a documented mS<140/>=140 GeV
  step function, not read from the paper's own branching-fraction tables.
- `eff_event_proxy`: flat placeholder (0.5) — the HEPData event-efficiency
  tables are indexed by summed track pT in the DV, which we don't have
  without truth-level tracks.
- `eff_vertex_proxy`: HEPData-derived (`HEPDATA_TABLE_PARSED`), but from the
  ATLAS EWK benchmark's cutflow final step, not from any table indexed by our
  scalar S — a scale anchor, not a mapped efficiency.
- `nearest_public_limit_fb`: nearest published *observed* EWK cross-section
  limit by lifetime/mass — same caveat, illustrative anchor only.

Every one of these is enumerated per-row in
`outputs/paper_s_proxy/paper_s_benchmark_proxy.csv`'s `missing_inputs`
column.

## 3. Which parts require UFO/MadGraph/Pythia?

- A real `sigma_gg_hstar_SS_fb` for the paper's process.
- A real `beta_gamma` distribution for S (currently a flat placeholder).
- Truth-level DV kinematics (decay position, track multiplicity, DV
  invariant mass, jet activity) so that
  `outputs/hepdata_tidy/event_efficiency_trackless.csv` and
  `outputs/hepdata_tidy/vertex_efficiency_grid.csv` can be looked up per
  benchmark point instead of averaged/placeholder.

## 4. Which HEPData tables are used?

From `data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml/`,
tidied by `scripts/02_hepdata_tidy_extract.py` into `outputs/hepdata_tidy/`:

- `acceptance_trackless_ewk.yaml`
- `cutflow_trackless_ewk.yaml`
- `event_efficiency_trackless_r_{1150,1150_3870,3870}_mm.yaml`
- `vertex_efficiency_r_*_mm.yaml` (12 radius bins)
- `yields_trackless_sr_observed.yaml`, `yields_trackless_sr_expected_ewk.yaml`
- `excl_xsec_ewk.yaml`

All of these are indexed by the ATLAS SUSY EWK benchmark (chargino/neutralino
mass, tau), not by a scalar mass — see `docs/recast/current_limitations.md`.

Six paper-aware figures built from these tables (plus the analytic decay
geometry and the scalar-S proxy grid) live in `outputs/figures/`, generated
by `scripts/04_make_paper_aware_figures.py` (`make figures`). See
`docs/recast/paper_aware_figures_interpretation.md` for what each one does
and does not show.

## 5. What would count as a meaningful next milestone?

In order of increasing rigor:

1. A real `sigma_gg_hstar_SS_fb(mS)` curve from MadGraph, replacing the flat
   placeholder — removes `USES_PLACEHOLDER_SIGMA`.
2. A real `BR_hadronic_proxy(mS)` from a width calculator or digitized paper
   table, replacing the step-function placeholder — removes
   `USES_PLACEHOLDER_BR`.
3. Truth-level Pythia kinematics (beta_gamma, DV position, track count, DV
   mass) for at least one benchmark point, letting `eff_event_proxy` and
   `eff_vertex_proxy` be looked up from the HEPData tidy tables instead of
   placeholders/EWK-borrowed anchors — removes `NEEDS_MG5_PYTHIA_SIGNAL`.
4. A side-by-side comparison against the paper's own published benchmark
   curves (once we have them digitized) instead of the EWK cross-section
   limit used here as a stand-in — removes
   `NEEDS_VALIDATION_AGAINST_PAPER_CURVES`.

Only after all four would it be honest to describe results from this repo as
approaching a validated recast.
