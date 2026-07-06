# Paper scalar S vs. ATLAS HEPData vs. current proxy vs. our 2HDM case

This table is the single-page answer to "what do we actually have, and what
is still missing, layer by layer." Status values are defined at the bottom.
See `docs/recast/efficiency_semantics.md` for the underlying quantity-type
reasoning and `docs/contracts/model_point_to_llp_recast_contract.md` for the
forbidden-mapping rules this table assumes.

| Layer | Paper scalar S (arXiv:2606.01681) | ATLAS HEPData provides | Current proxy (this repo) | Our 2HDM requirement | Status |
|---|---|---|---|---|---|
| Mass | benchmark grid `mS = 100, 170, 250 GeV` | not model-specific; efficiency tables indexed by neutralino mass, not mS | `PAPER_BENCHMARK_MASSES_GEV` copied from paper grid | 2HDM scan `m_scalar_GeV` per point | READY (mass itself is just a number) |
| Lifetime / total width | `sin_theta` sets `ctau` in paper's own model | not provided (HEPData tables indexed by `tau` for the EWK benchmark, not derived from any width) | `ctau_mm_from_width_gev` / inverse, generic conversion | `total_width_GeV` from 2HDMC/width calculator -> `ctau_mm` | READY (conversion math); NEEDS_2HDM_MAPPING (the width itself) |
| Production cross-section | `sigma(gg -> h* -> SS)` is a real paper quantity, not currently digitized here | none (HEPData has no scalar-S production info) | `sigma_fb_assumed = 1.0` flat placeholder | must come from MadGraph or an analytic 2HDM calculation; **not derivable from width** | NEEDS_SIGNAL_MC |
| Boost beta_gamma (βγ) | set by `mS`, `sqrt(s)`, and `h*` kinematics — a distribution, not one number | none | `beta_gamma_assumed = 1.0` flat placeholder | truth-level βγ distribution per 2HDM point from Pythia | NEEDS_SIGNAL_MC |
| Branching fractions | paper likely has `BR_bb/WW/ZZ/gg` tables (not yet digitized into this repo) | none | `br_hadronic_proxy`: step function (0.8 below 140 GeV, 0.5 above) — documented guess, no citation | 2HDM exclusive BRs from 2HDMC, then `BR_hadronic_proxy` computed consistently from those (see contract doc) | PROXY_ONLY |
| Hadronic final state | `S -> qq/gg` dominant channels assumed | generic — ATLAS's DV+jets selection is agnostic to DV parent multiplicity within its cutflow but efficiencies were tuned to EWK decay products | not modeled beyond the BR step function above | truth-level jet multiplicity/kinematics from 2HDM `S` decay MC | NEEDS_SIGNAL_MC |
| DV radius | not published by paper as a table here; geometry only from our own math | acceptance/cutflow/efficiency tables are binned by radius (fiducial region boundaries at 4mm, 1150mm, 3870mm, 300mm ID edge etc.) | `decay_probability_between_radii` — real, model-agnostic geometry | same math, fed with 2HDM `ctau`, `beta_gamma` | READY |
| DV mass (`m_DV`) | not applicable (paper-level, not detector-level) | `vertex_efficiency_grid.csv` — 12 radial bins x `m_DV` x `n_tracks` grid, EWK benchmark decay products | not used (flat `eff_vertex_proxy`, averaged over EWK cutflow's final step, not looked up by `m_DV`) | truth-level `m_DV` per simulated DV from 2HDM `S` decay MC | NEEDS_SIGNAL_MC |
| `n_tracks` | not applicable (paper-level) | same `vertex_efficiency_grid.csv` | not used | truth-level charged-track multiplicity per DV | NEEDS_SIGNAL_MC |
| Event activity / Sumpt | not applicable (paper-level) | `event_efficiency_trackless.csv` / `_highpt.csv`, 13 Sumpt bins x 3 radial categories; **note: `R<1150mm` bin peaks at 1.1851, not a bounded probability** (see `docs/recast/efficiency_audit_event_efficiency_gt1.md`) | not used (flat `eff_event_proxy = 0.5` placeholder) | truth-level event `Sumpt` per 2HDM event | NEEDS_SIGNAL_MC |
| Event efficiency | not applicable | HEPData "reinterpretation material" weight, EWK-benchmark-specific, radius+Sumpt dependent, can exceed 1 | `eff_event_proxy = 0.5` flat placeholder | Sumpt-matched lookup in the ATLAS table above, still borrowed | HEPDATA_BENCHMARK_ONLY |
| Vertex efficiency | not applicable | `vertex_efficiency_grid.csv`, bounded [0,1] in this data, gated by `m_DV`/`n_tracks`/radius | `eff_vertex_proxy` — mean of EWK cutflow's final `A x eps` step across 4 benchmark points, not an `m_DV`/`n_tracks` lookup | cell-by-cell lookup once truth `m_DV`/`n_tracks` exist | HEPDATA_BENCHMARK_ONLY |
| Cutflow (`A x epsilon`) | not applicable | `cutflow_trackless_ewk.csv`, 4 EWK mass/lifetime points, full selection chain | only the final step's value used, averaged, as `eff_vertex_proxy` input | our own cutflow requires detector-level simulation (Delphes or similar) — not built here | NOT_DIRECTLY_TRANSFERABLE |
| Cross-section limits | not applicable (paper likely has its own exclusion curves, not yet digitized) | `excl_xsec_ewk.csv`, observed/expected 95% CL limits vs. neutralino mass and `tau` | `nearest_public_limit_fb`: nearest EWK-benchmark limit by mass/tau, illustrative anchor only, `ratio_to_limit_proxy` uses the flat placeholder sigma | a real limit comparison requires our own `A x epsilon` (all rows above) and our own cross section, not a borrowed EWK number | NOT_DIRECTLY_TRANSFERABLE |

## Status definitions

- **READY** — the math/conversion is model-agnostic and already implemented and tested.
- **PROXY_ONLY** — a documented placeholder stands in; not physical, but the pipeline slot exists.
- **HEPDATA_BENCHMARK_ONLY** — a real ATLAS number exists, but it is for the EWK benchmark, not our model; usable only as an order-of-magnitude/shape anchor.
- **NEEDS_SIGNAL_MC** — requires FeynRules/UFO -> MadGraph -> Pythia truth-level output that does not exist yet.
- **NEEDS_2HDM_MAPPING** — requires 2HDMC (or equivalent) output mapped through the contract in `docs/contracts/model_point_to_llp_recast_contract.md`.
- **NOT_DIRECTLY_TRANSFERABLE** — the ATLAS number is detector/model-coupled enough that no simple lookup or rescaling makes it ours; a full independent estimate is required.

## Bottom line

Only the pure-geometry layers (mass-as-a-label, lifetime-conversion math,
DV-radius decay probability) are `READY` today. Everything downstream of
"what does the ATLAS detector do to this specific final state" is either a
flat placeholder (`PROXY_ONLY`) or an EWK-benchmark number borrowed as a
shape/order-of-magnitude anchor (`HEPDATA_BENCHMARK_ONLY`), and the deepest
layers (cutflow, cross-section limits) are not transferable at all without
independent signal MC and detector-level modeling.
