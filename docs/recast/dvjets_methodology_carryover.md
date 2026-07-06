# DV+jets methodology carryover

What survives the pivot from Neil's LLP paper to our 2HDM diphoton target,
and what does not.

## Why DV+jets is not the right final dataset

Our target observable is `sigma(pp -> H2) * BR(H2 -> gamma gamma)` for a
**prompt** resonance. DV+jets searches (ATLAS Trackless SR and similar)
are built for **displaced** signatures: decay-vertex reconstruction,
lifetime (`ctau`, `beta*gamma`) kinematics, trackless-vertex
efficiencies. A prompt diphoton resonance never produces a displaced
vertex, so none of that machinery applies. Jets are not central to
`H2 -> gamma gamma` at all, except in VBF-tagged or associated-production
diphoton categories — a separate, later pivot, not this one.

## What we learned from the DV+jets exercise (kept)

- **Pipeline shape**: HEPData YAML -> tidy CSV -> comparison table works
  and is dataset-agnostic. `src/llp_recast/hepdata_yaml.py` was reused
  *unmodified* for HIGG-2018-27 (see `scripts/07_diphoton_hepdata_extract.py`).
- **Honesty discipline**: every placeholder/unavailable number gets an
  explicit `quality_flag` and stays visibly `None`/`NOT_YET_AVAILABLE`
  rather than a silently-invented value. Directly reused in
  `docs/recast/diphoton_minimum_recast_contract.md`.
- **Mass-scan structure**: comparing a theory curve against an
  observed+expected limit curve as a function of resonance mass is the
  same shape of problem in both channels — only the underlying physics
  (efficiency chain vs cross-section chain) differs.
- **Local-download-first workflow**: both HEPData bundles were supplied
  by the user as local tarballs because automated fetches were blocked;
  the same extract-and-inventory pattern applies to both.

## What does NOT carry over (physics)

```text
paper hSS coupling / lambda_eff   !=  2HDM lambda6 or lambda7
paper sin(theta)                  !=  2HDM sin(beta-alpha)
DV+jets efficiencies (vertex/track) !=  diphoton reco/selection efficiencies
LLP lifetime/decay-probability math !=  prompt resonance production x BR
Trackless SR                      !=  gamma gamma resonance search
```

None of the DV+jets recast math (`src/llp_recast/recast_math.py`,
lifetime/decay-probability functions, radial-bin acceptance tables) is
used or referenced by the diphoton pipeline. They stay in place for the
original LLP exercise but are out of scope here.

## Net effect

The DV+jets exercise bought us a validated *extraction and contract*
pipeline at close to zero marginal cost for this pivot — script 07/08
for HIGG-2018-27 took a fraction of the time script 01-06 took for the
DV+jets record, precisely because the shared module needed no changes.
