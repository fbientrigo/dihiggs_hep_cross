You are a senior HEP phenomenology + research software engineer working inside a local folder, not necessarily a git repo.

Goal:
Build a minimal but useful SDD/TDD analysis scaffold for a scalar-like LLP recast using local ATLAS DV+jets HEPData YAML files.

Context:
- The local folder is `~/code/dihiggs_jets`.
- The official HEPData YAML bundle is already extracted under:
  `data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml/`
- Automated download was blocked by Cloudflare, so do not download from HEPData.
- Use only the local YAML files.
- This is not a full ATLAS reproduction and must not claim official exclusions.
- The physics target is inspired by `pp -> h* -> S S`, where S is a long-lived neutral scalar, but the scaffold must be reusable for our own UFO/MadGraph/Pythia signal.

Engineering requirements:
- Follow SDD/TDD.
- Keep modules small.
- Keep outputs explicit about proxy quality.
- Use Python, PyYAML, pandas, pytest.
- Do not add heavy frameworks.

Immediate tasks:
1. Run `pytest` and fix failures.
2. Run `scripts/01_hepdata_inventory.py` and inspect outputs.
3. Run `scripts/02_toy_s_recast.py` and inspect outputs.
4. Improve the HEPData parser enough to extract selected tables into tidy CSV:
   - `yields_trackless_sr_observed.yaml`
   - `yields_trackless_sr_expected_ewk.yaml`
   - `excl_xsec_ewk.yaml`
   - `cutflow_trackless_ewk.yaml`
   - `acceptance_trackless_ewk.yaml`
   - `event_efficiency_trackless_r_1150_mm.yaml`
   - `vertex_efficiency_r_180_300_mm.yaml`
5. Add tests for the tidy-table extractor.
6. Create a short `outputs/recast_readiness_report.md` summarizing what can be used now and what still requires MadGraph/Pythia.

Scientific constraints:
- Separate BR, geometric acceptance, reconstruction efficiency and event efficiency.
- Do not confuse the paper's effective hSS coupling lambda with 2HDM lambda6/lambda7.
- Use `ctau_mm = 1.973269804e-13 / Gamma_GeV`.
- For the first proxy, use `P(4 mm < R < 300 mm) = exp(-4/L) - exp(-300/L)`, where `L = beta_gamma * ctau_mm`.
- Use `Nsig = L_fb * sigma_fb * BR_factor * Aepsilon`.

Definition of done:
- Tests pass.
- Inventory output exists.
- Toy S recast CSV exists.
- Report states that this is a proxy, not an official exclusion.
- The next step toward accuracy is clearly listed as UFO/MadGraph/Pythia signal generation and validation against paper benchmarks.
