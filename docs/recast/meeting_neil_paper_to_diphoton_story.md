# Meeting story: Neil's paper -> our 2HDM diphoton target

## The pivot in one line

We validated a HEPData recast pipeline on Neil's LLP paper (arXiv:2606.01681,
ATLAS DV+jets), and are now pointing that same pipeline at the dataset that
actually matches our 2HDM Type I target: prompt `H2 -> gamma gamma` via
ATLAS HIGG-2018-27 (arXiv:2102.13405).

## Neil's paper -> method

`h* -> S S`, `S` a long-lived scalar decaying to displaced hadrons/jets.
ATLAS DV+jets (Trackless SR) is the matching search: it needs decay-vertex
reconstruction, lifetime/`beta*gamma` kinematics, and trackless-vertex
efficiencies. This gave us a first working pipeline: HEPData YAML ->
tidy CSV -> mass/lifetime scan -> compare to published limits, with an
honesty discipline (explicit `quality_flag`/placeholder columns for every
number we didn't actually derive).

## DV+jets exercise -> method validation

What it proved: the pipeline works end to end (18+ HEPData tables parsed,
45 tests passing, figures generated). What it could **not** do: give us an
exclusion for our actual 2HDM model, because the only detailed local
HEPData tables in that record are for ATLAS's own SUSY EWK benchmark
(chargino/neutralino), not any scalar-S model — see
`docs/recast/current_limitations.md`.

## Our H2 target -> prompt diphoton

Our model is 2HDM Type I: a neutral heavy scalar `H2` with `m_H2 > m_h =
125 GeV`. The relevant search channel is **prompt** resonant diphoton
production, `sigma(pp -> H2) * BR(H2 -> gamma gamma)`, not anything
displaced. Jets only enter via VBF-tagged or associated-production
diphoton categories, which are out of scope for this first pivot (see
`docs/recast/dvjets_methodology_carryover.md`).

## Dataset pivot -> ATLAS HIGG-2018-27

Chosen dataset: ATLAS HIGG-2018-27, arXiv:2102.13405, 139 fb^-1,
HEPData DOI `10.17182/hepdata.100161` (target DOI verified against the
downloaded bundle's `table_doi` fields — see
`docs/recast/atlas_higg_2018_27_dataset_card.md`). It directly reports
95% CL upper limits on fiducial `sigma x BR(gamma gamma)` vs resonance
mass, for spin-0 (scalar) hypotheses at 4 width points (NWA, 2%, 6%, 10%
of `m_X`), over 160-3000 GeV.

## Next recast contract -> sigma*BR comparison

We now have the full **experiment side** of the contract
(`outputs/diphoton_recast_contract/experiment_side.csv`, 727 rows: 4 width
hypotheses x mass grid, observed + expected +-1/2 sigma). We do **not**
yet have the **theory side** (`sigma_ggF`, `sigma_VBF` from our 2HDM
scan + a cross-section tool) — see
`docs/recast/diphoton_minimum_recast_contract.md` for the exact join
contract and the placeholder rows that stand in for it today.

## What to say tomorrow

- We pivoted the recast pipeline from Neil's DV+jets exercise to the
  correct channel for our model: prompt `H2 -> gamma gamma`.
- Primary dataset is locked: ATLAS HIGG-2018-27, 139 fb^-1, HEPData DOI
  `10.17182/hepdata.100161` — downloaded, verified, and parsed locally.
- We already have the full experimental side of the contract: observed
  and expected sigma*BR limits vs mass, for 4 width hypotheses, 160-3000 GeV.
- We do not have a theory-side cross section yet, so **no exclusion claim
  today** — next concrete step is `2HDMC BR output -> cross-section tool
  (ggF/VBF) -> sigma*BR`.
- The DV+jets work was not wasted: the extraction pipeline, honesty
  conventions, and comparison-contract shape all reused directly, unchanged.
