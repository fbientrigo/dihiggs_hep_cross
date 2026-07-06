# Efficiency semantics — what each number in this pipeline actually is

This document exists because the words "efficiency" and "probability" are
used loosely across HEP papers, HEPData, and casual conversation, and mixing
them up is exactly how a recast becomes wrong quietly. Read this before
quoting any `outputs/` number as if it were a probability.

## The five quantity types

### 1. Geometric decay probability (`P_decay_ID`, `P_single_ID_4_300`)

- **What it is:** `P(4mm < R < 300mm) = exp(-r_min/L) - exp(-r_max/L)`,
  `L = beta_gamma * ctau`. Pure exponential-decay geometry.
  (`recast_math.decay_probability_between_radii`.)
- **Bounded in [0,1]?** Yes, by construction (clamped in code, and
  analytically bounded since it's a difference of two survival probabilities).
- **Depends on ATLAS/detector data?** No.
- **Depends on particle model?** Only through `ctau` and `beta_gamma`.
- **Reusable for scalar S?** Yes, directly — it's model-agnostic geometry.
- **Reusable for 2HDM?** Yes, directly, same reasoning.
- **What our MC must supply:** `ctau_mm` (from `total_width_GeV`) and a
  `beta_gamma` distribution (from production kinematics — NOT derivable from
  width alone).

### 2. Event-level efficiency / weight (`event_efficiency_trackless.csv`,
   `event_efficiency_highpt_*.csv`)

- **What it is:** ATLAS-published tables explicitly labeled in the HEPData
  submission metadata as **"Reinterpretation Material: Event-level
  Efficiency for Trackless/HighPt SR selections"**, binned by radial DV
  category and `Sumpt` (summed track pT in the event). Despite the column
  header `Efficiency`, this is a **published reinterpretation weight/
  parameterization**, not a bounded pass/total probability.
- **Bounded in [0,1]?** No. The trackless `R < 1150 mm` table peaks at
  **1.1851** (Sumpt bin [0.6, 0.8) GeV) and the highpt `R < 1150 mm` table
  peaks at **1.0149**. Confirmed identical from raw YAML → tidy CSV →
  plotted figure (see `docs/recast/efficiency_audit_event_efficiency_gt1.md`
  for the full trace). This is a genuine published value, not a parsing or
  plotting bug on our side.
- **Depends on ATLAS/detector data?** Yes — trigger, reconstruction,
  material-veto, and SR-selection behavior baked in for ATLAS's own
  chargino/neutralino EWK benchmark.
- **Depends on particle model?** Yes — it is specific to the EWK benchmark's
  production mode and decay-product multiplicity (reactions listed in the
  HEPData submission: gluino/chargino/neutralino pair production).
- **Reusable for scalar S / 2HDM?** Only as an **order-of-magnitude anchor**
  for the *shape* of the Sumpt dependence (efficiency rises then falls with
  event activity, and differs strongly by radial shell). Not directly
  transferable as a number, because our LLP's `Sumpt` distribution comes from
  `h* -> S S -> hadrons`, not chargino/neutralino decay products.
- **What our MC must supply:** truth-level `Sumpt` per event and the DV
  radial category, so the correct bin of *this specific* ATLAS table can be
  looked up — still borrowing an EWK-benchmark number, but a Sumpt-matched
  one instead of an average.

### 3. Vertex efficiency (`vertex_efficiency_grid.csv`)

- **What it is:** ATLAS's own DV reconstruction/selection efficiency as a
  function of `m_DV` (vertex mass) and `n_tracks`, in 12 published radial
  bins.
- **Bounded in [0,1]?** Yes in the data we have (no row exceeds 1 across all
  768 tidy rows) — but treat this as an empirical observation of this table,
  not a name-implied guarantee for every HEPData "Efficiency" column (see
  point 2).
- **Depends on ATLAS/detector data?** Yes — DV reconstruction, tracking,
  vertex-fit quality baked in.
- **Depends on particle model?** Yes — `m_DV` and `n_tracks` are set by the
  LLP's decay-product multiplicity and kinematics (chargino/neutralino decay
  products here, not `S -> qq/gg`).
- **Reusable for scalar S / 2HDM?** Only conditionally, cell-by-cell, and
  only once our signal MC gives truth-level `m_DV` and `n_tracks` for the `S`
  decay. Cannot be looked up from mass/lifetime alone.
- **What our MC must supply:** truth-level `m_DV`, `n_tracks`, and decay
  radius per simulated vertex.

### 4. Cutflow `A x epsilon` (`cutflow_trackless_ewk.csv`)

- **What it is:** cumulative acceptance-times-efficiency after each selection
  step (trigger -> filter -> jet selection -> DV geometry -> material veto ->
  track-count -> DV-mass -> selected-tracks), for 4 published EWK
  mass/lifetime points.
- **Bounded in [0,1]?** Yes, monotonically non-increasing by construction of
  a cutflow.
- **Depends on ATLAS/detector data?** Yes, entirely — full analysis chain.
- **Depends on particle model?** Yes — EWK benchmark production and decay
  topology.
- **Reusable for scalar S / 2HDM?** Only the *shape* (which steps lose the
  most signal, and how that shape changes with lifetime) is a transferable
  lesson. The absolute numbers are EWK-specific.
- **What our MC must supply:** a full reconstructed-event chain (trigger,
  jets, DV, tracks) to build our own cutflow — not available without
  detector-level simulation (Delphes or ATLAS's own software), which this
  scaffold does not run.

### 5. Cross-section limit (`excl_xsec_ewk.csv`)

- **What it is:** ATLAS's published observed/expected 95% CL cross-section
  upper limits, indexed by neutralino mass and proper lifetime `tau`.
- **Bounded in [0,1]?** No — this is a cross section in fb, not a
  probability. Values up to ~300 fb are expected and correct.
- **Depends on ATLAS/detector data?** Yes, it's the final analysis output.
- **Depends on particle model?** Yes — computed assuming the EWK benchmark's
  production cross section, decay topology, and `A x epsilon`.
- **Reusable for scalar S / 2HDM?** Only after we compute our own model's
  `A x epsilon` and compare our own predicted cross section to a limit
  derived *for our model* — the published number is a limit on the EWK
  benchmark's cross section, not on ours. Using it as-is (as the current
  `nearest_public_limit_fb` proxy does) is an illustrative anchor only.
- **What our MC must supply:** a full model-specific `A x epsilon` (steps
  1-4 above, done for `S` or the 2HDM scalar) before this number means
  anything for our model.

## Can we use ATLAS DV+jets HEPData for a 2HDM scalar?

**Yes, only conditionally.** We can use the public analysis products as a
recast scaffold if our 2HDM point produces a similar displaced hadronic
DV+jets signature, and if we can map our signal onto the required variables:
`ctau`, `beta_gamma`, decay radius, jets, `Sumpt`, `m_DV`, `n_tracks`, and
branching ratios. We cannot directly apply the benchmark efficiencies
(event-level, vertex, or cutflow) as universal scalar efficiencies — every
one of them is baked for ATLAS's own chargino/neutralino EWK topology. See
`docs/contracts/model_point_to_llp_recast_contract.md` for the forbidden
mappings (paper `lambda_eff`/`sin_theta` != 2HDM `lambda6`/`lambda7`/
`sin(beta-alpha)`) that apply with equal force here.

## Summary table

| Quantity | Type | Bounded [0,1]? | Detector-dependent? | Model-dependent? | Directly reusable for 2HDM? |
|---|---|---|---|---|---|
| `P_decay_ID` | geometric probability | yes | no | only via ctau, beta_gamma | yes |
| `event_efficiency_trackless` / `_highpt` | HEPData reinterpretation weight | **no** (up to 1.1851) | yes | yes (EWK benchmark) | shape only |
| `vertex_efficiency_grid` | detector efficiency | yes (in this data) | yes | yes (EWK benchmark) | cell-by-cell, needs m_DV/n_tracks |
| `cutflow A x epsilon` | cumulative efficiency | yes | yes | yes (EWK benchmark) | shape only |
| `excl_xsec_ewk` (cross-section limit) | physical cross section [fb] | no (not a probability) | yes | yes (EWK benchmark) | only after own A x epsilon |
| `scalarS_proxy_Nsig` | placeholder-heavy proxy yield | no (a count) | indirectly (borrows EWK numbers) | partially (uses paper mS/ctau grid) | no — placeholder-heavy, not exclusion-grade |
