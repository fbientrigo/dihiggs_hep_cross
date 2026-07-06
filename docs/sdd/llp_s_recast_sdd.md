# SDD — Minimal LLP scalar recast against ATLAS DV+jets HEPData

## Goal

Build a small, auditable analysis layer that connects a scalar-like LLP signal to public ATLAS DV+jets HEPData products.

This is not a full ATLAS reproduction. It is a staged phenomenological recast scaffold.

## Context

The working physics case is a neutral scalar-like LLP `S`, motivated by the paper workflow `pp -> h* -> S S`, but intended to be reusable for our own BSM scalar-pair topology generated through FeynRules/UFO/MadGraph/Pythia.

## Inputs

1. Local HEPData YAML bundle:

```text
data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml/
```

2. Future signal MC:

```text
FeynRules -> UFO -> MadGraph5_aMC@NLO -> Pythia -> truth-level recast
```

3. Current or future 2HDM scan outputs with at least:

```text
mass, total_width, partial_widths, branching ratios, production cross section or proxy
```

## Non-goals

- Do not claim an official ATLAS exclusion.
- Do not emulate LRT or material maps beyond public efficiency proxies.
- Do not treat prompt Delphes output as a valid displaced-object reconstruction.
- Do not identify the paper's effective `lambda` with `lambda6` or `lambda7` without a model matching.

## Requirements

### R1 — HEPData inventory

The analysis must discover and classify local YAML tables into:

- yields;
- exclusion limits;
- cross-section limits;
- acceptance;
- event efficiency;
- vertex efficiency;
- cutflow.

### R2 — Toy scalar proxy

The analysis must support a toy scalar `S` benchmark grid:

```text
mS = 100, 170, 250 GeV
ctau = configurable
sigma = configurable
BR_had = configurable
```

### R3 — Geometry proxy

For each benchmark, compute:

```text
P(4 mm < R < 300 mm)
P(at least one of two LLPs decays in ID)
```

### R4 — Yield proxy

For each benchmark, compute:

```text
Nsig = L * sigma * BR_factor * Aepsilon_proxy
```

with explicit quality flags.

### R5 — Future MC interface

A future MadGraph/Pythia stage must provide:

```text
mS, beta_gamma distribution, LLP decay position, truth jets, charged multiplicity proxy, DV mass proxy
```

## Acceptance criteria

- `pytest` passes.
- `scripts/01_hepdata_inventory.py` writes CSV and Markdown inventory.
- `scripts/02_toy_s_recast.py` writes a toy benchmark summary CSV.
- Outputs explicitly state they are proxies, not exclusions.

## R6 — HEPData tidy extraction

`scripts/02_hepdata_tidy_extract.py` must flatten the acceptance, cutflow,
event-efficiency, vertex-efficiency, yields, and cross-section-limit YAML
tables into tidy CSVs under `outputs/hepdata_tidy/`, preserving
`source_yaml`, `observable`, `qualifiers` (mass/lifetime/luminosity/energy),
every independent-variable column, `value`, and any published uncertainty.
See `src/llp_recast/hepdata_yaml.py::tidy_rows`.

## R7 — Paper-aware scalar-S benchmark proxy

`scripts/03_paper_s_benchmark_proxy.py` must combine:

- the scalar-S benchmark grid (`llp_recast.paper_model`),
- the ID decay-probability geometry (`llp_recast.recast_math`),
- and HEPData-tidy-derived numbers where robustly extractable, explicit named
  placeholders where not,

into `outputs/paper_s_proxy/paper_s_benchmark_proxy.csv` and a markdown
report that states plainly it is not a reproduction and not an exclusion.
Every row must carry `quality_flag` and `missing_inputs`.

## R8 — Model-point contract

Any future 2HDM (or other extended-Higgs) scan point must be translated into
the recast layer only via the column contract in
`docs/contracts/model_point_to_llp_recast_contract.md`. The paper's
`lambda_eff`/`sin_theta` must never be silently identified with a 2HDM
`lambda6`/`lambda7`/`sin(beta-alpha)`.

## Updated acceptance criteria (R6-R8)

- `scripts/02_hepdata_tidy_extract.py` writes the 7 required tidy CSVs.
- `scripts/03_paper_s_benchmark_proxy.py` writes CSV + markdown, markdown
  contains the "not a reproduction" / "not an exclusion" disclaimer.
- `make all` runs test -> inventory -> tidy -> toy -> paper-proxy and passes.
