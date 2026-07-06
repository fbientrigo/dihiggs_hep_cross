# Meeting: next steps

## Status

The recast scaffold now runs end-to-end (`make all`: test -> inventory ->
tidy -> toy -> paper-proxy -> figures) and produces a paper-aware scalar-S
proxy grid (3 masses x 7 lifetimes) anchored to real HEPData numbers where
possible, with every placeholder/borrowed number named explicitly per row.
Six paper-aware figures (`outputs/figures/`) now make the displaced-decay
geometry, the ATLAS selection structure, and the proxy/real-MC gap visible —
see `docs/recast/paper_aware_figures_interpretation.md`. See also
`docs/recast/paper_2606_01681_operational_notes.md` and
`docs/recast/current_limitations.md` for the honest accounting of what is
and isn't physical yet.

## Decisions needed

1. Confirm the trackless SR (vs. high-pT SR) is still the right first
   validation channel — it's the one with the most complete tidy tables
   locally.
2. Decide whether the next milestone is (a) a FeynRules/UFO model for the
   paper's scalar S, or (b) digitizing the paper's own BR/sigma tables first
   and deferring MC.
3. Decide whether to build the `PaperScalarPoint.from_2hdm_point()` bridge
   now (with an explicit, reviewed lambda/sin_theta matching) or wait until a
   concrete 2HDM benchmark point needs it.

## Immediate next analysis work

1. Get a FeynRules/UFO model (or an existing one) for `pp -> gg -> h* -> S S`
   into MadGraph, generate a handful of `(mS, ctau)` points, and replace
   `sigma_fb_assumed` / `beta_gamma_assumed` with real numbers for at least
   one benchmark.
2. Once truth Pythia kinematics exist for one point, wire up a real lookup
   into `outputs/hepdata_tidy/event_efficiency_trackless.csv` and
   `vertex_efficiency_grid.csv` (by Sumpt / m_DV / n_tracks) instead of the
   flat `eff_event_proxy` / borrowed `eff_vertex_proxy`. Figures 2 and 3 in
   `outputs/figures/` already show the shape of these tables — this item is
   about looking values up per benchmark point instead of reading the shape.
3. Track down whether arXiv:2606.01681 publishes its own BR(S) table or
   digitized exclusion curves we can compare against directly, instead of
   the EWK cross-section-limit stand-in currently used for
   `nearest_public_limit_fb`.
