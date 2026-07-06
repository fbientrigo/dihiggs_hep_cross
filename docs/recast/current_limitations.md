# Current limitations

This is a scaffold for a recast, not a recast. Read this before quoting any
number from `outputs/`.

## Model mismatch in the HEPData anchors

The only local HEPData tables with efficiencies/cutflows/limits (trackless
EWK series) were published by ATLAS for their own SUSY EWK
(chargino/neutralino) benchmark: pair-produced charginos/neutralinos with a
long-lived neutralino decaying to a displaced vertex + jets. Our physics case
is a pair of scalar LLPs `S` from `pp -> gg -> h* -> S S`. Different
production mode, different mass parameter (neutralino mass, not mS),
different decay-product multiplicity model. Using these tables as
placeholders/anchors is explicitly flagged (`HEPDATA_TABLE_PARSED` +
`missing_inputs`), never presented as a validated mapping.

## No signal MC yet

There is no FeynRules/UFO model, no MadGraph run, no Pythia shower for this
scalar S. `beta_gamma`, the production cross section, and the DV track/mass
kinematics used to look up event/vertex efficiencies are all flat
placeholders. Nothing downstream of these placeholders (`aeff_proxy`,
`Nsig_139fb`, `ratio_to_limit_proxy`) should be treated as physical.

## Branching fractions are a step function, not physics

`llp_recast.paper_model.br_hadronic_proxy` in `paper_placeholder` mode
returns 0.8 below 140 GeV and 0.5 above it. This is a documented guess to
keep the pipeline runnable end-to-end, not a width calculation. It has no
citation.

## Figures 2-4 visualize the EWK benchmark, not scalar-S

`outputs/figures/fig2_event_efficiency_vs_sumpt.png`,
`fig3_vertex_efficiency_heatmap.png`, and `fig4_trackless_cutflow.png`
(see `scripts/04_make_paper_aware_figures.py`) plot the same borrowed ATLAS
SUSY EWK tables described above. They are useful for understanding the
*shape* of the public selection logic (efficiency vs Sumpt, vertex
mass/track-count gating, per-step cutflow losses) but every number on those
three figures is a chargino/neutralino number, not a scalar-S number. Each
carries an explicit `EWK_BENCHMARK_NOT_SCALAR_S` flag on the figure and in
`outputs/figures/README.md`. See
`docs/recast/paper_aware_figures_interpretation.md` for the full per-figure
caveats.

## No detector-level modeling beyond public tables

We do not run Delphes, do not model the ATLAS material map veto, and do not
model tracking/vertexing algorithms. Any efficiency number that isn't
directly copied from a published ATLAS table (and even those are for the
wrong model, see above) is a placeholder.

## What this scaffold IS good for

- Confirming the plumbing is dimensionally and numerically sane (probability
  bounds, yield formula, unit conversions all under test).
- Making explicit, per-row, exactly which physics inputs are still missing
  (`missing_inputs` column) so the next work session has a concrete list
  rather than a vague "need more physics" note.
- Giving a stable target schema (`docs/contracts/recast_output_schema.md`,
  `docs/contracts/model_point_to_llp_recast_contract.md`) that a real 2HDM
  scan or a MadGraph/Pythia signal chain can be plugged into later without
  restructuring the analysis code.

## Do not say

- "We reproduced the paper."
- "We excluded [any point]."
- "We reproduced ATLAS."

## OK to say

- "Paper-aware proxy."
- "Truth-level recast scaffold."
- "HEPData-backed recast preparation."
- "First operational bridge between scalar-S benchmarks and ATLAS DV+jets
  public products."
