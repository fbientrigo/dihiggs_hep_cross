# SM-like Higgs mass convention in `dihiggs_hep_cross`

## Owner

`m_h` has exactly one owner across the ecosystem:
`conventions/physics_conventions.yaml`, key `sm_like_higgs.m_h_GeV`, currently
`"125.20"` (PDG 2026 listing). The file is values-only and byte-identical across
`dihiggs`, `dihiggs_boundary` and `dihiggs_hep_cross`; `tests/test_external_tools.py`
md5-pins it so drift in any repo fails that repo's CI.

This repo reads it through `src/llp_recast/constants.py`
(`M_H_GEV_TEXT` / `M_H_GEV`), pinned-fallback style, cross-asserted by
`tests/test_constants.py`.

## Rule

**Read `m_h` off the point. Never default it.**

`scripts/run_physical_point_madgraph.py::resolve_m_h_GeV` resolves
`m_h_GeV` -> `mh_input_GeV` -> `mh` from the incoming point and raises if none is
present. It used to fall back to a hard-coded `125.13`, which meant a point
produced under a different mass convention was silently rewritten to this repo's
assumption when its `param_card.dat` was generated. The convention travels on the
point; a point that does not carry it is a contract violation, not a defaulting
case.

`constants.M_H_GEV` is only for code that generates *new* points and therefore
has no point to read from (e.g. `scripts/run_scale_campaign.py`, which drives the
evaluator directly).

## Active sites

| Site | Role |
|---|---|
| `src/llp_recast/constants.py` | reads the convention (`M_H_GEV`, `M_H_GEV_TEXT`) |
| `scripts/run_physical_point_madgraph.py` | reads `m_h` off the point; writes SLHA `Block MASS` entry 25 |
| `scripts/run_scale_campaign.py` | generates new points at the canonical convention |
| `contracts/model_point_to_llp_recast*.yaml` | the v2 contract carries `m_h_GeV` as a required column |

## Historical / frozen sites — deliberately NOT migrated

| Site | Value | Why |
|---|---|---|
| `scripts/r9_run_model_scan.py` (`MH_GEV = 125.13`) | 125.13 | **sha256-locked frozen artifact.** Its hash is pinned in `results/r9_h2_sensitivity_threshold/artifact_manifest.json` and enforced by `scripts/verify_r9_artifacts.py` / `tests/test_r9_artifacts.py`. It is the frozen reconstruction of benchmark `H2scan_mH150_tb300000`. Editing the file at all — even to add a comment — breaks the lock. Its historical status is recorded here instead. |
| `results/canonical_benchmark_point.json` (`mh_input_GeV: 125.13`) | 125.13 | the validated 150 GeV benchmark point as produced |
| `results/pilot_points_input.json` | 125.13 | generated pilot data |
| `data/manual/h2_benchmark_handoff.json` (`ufo.external_defaults.MH: 125.0`) | 125.0 | a *record* of the un-patched upstream UFO default, not a convention |
| `tests/test_run_physical_point_madgraph.py` benchmark cases | 125.13 | exact regression of the 150 GeV closure; `mh_GeV` now has no default, so the historical value is necessarily explicit |

Recalculating the 150 GeV benchmark at 125.20 shifts `g_hH2H2` by roughly
+0.11% and changes its `point_id` (`m_h` is hashed into the canonical point
identity). Such a point is a **different point**, not a relabelling. Do not mix
results across conventions in a single plot or table.

## False positives

`data/hepdata/atlas_dvjets_139fb/yaml_raw/*` contains `125.02`, `125.03`,
`125.07` — these are ATLAS exclusion-curve values, not Higgs masses.
