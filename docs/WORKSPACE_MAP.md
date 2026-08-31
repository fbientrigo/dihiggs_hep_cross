# DiHiggs Analysis Workspace Map

## Workspace Overview & Data Authority Rule

This workspace is a DiHiggs (Two-Higgs-Doublet Model Type-I) particle physics analysis environment constructed from 6 independent Git repositories, vendored C++ physics libraries ([`2HDMC-1.8.0`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_boundary/lib/2HDMC-1.8.0) and [`higgstools-v1.2`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_boundary/lib/higgstools-v1.2)), and a dedicated MadGraph5_aMC@NLO event generator installation. As part of a comprehensive workspace reset, the historical container at `/home/fabian/atlas_dihiggs` is retired, all historical campaign outputs and pilot runs are archived to `/home/fabian/atlas_dihiggs_archive/20260831_pre_madgraph_reset/`, and a fresh, clean container is provisioned at `/home/fabian/atlas_dihiggs_clean/` containing solely canonical repository checkouts from `origin/main` with zero unreviewed generated output.

> [!IMPORTANT]
> **Cardinal Authority Rule:** Before citing any cross-section, event yield, branching ratio, exclusion limit, or sensitivity number as current, any agent or researcher MUST first inspect [`dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md) and [`dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml); no other file, script, run directory, or historical report carries authority for current scientific claims.

---

## Workspace Path Map & Authority Matrix

| Path | Role | Generates | Consumes | Tracked? | Current authority? | Safe for LLM current claims? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dihiggs_clean/dihiggs/` | Canonical 2HDM theory point evaluators and scan core | 2HDM point evaluation tables, decay widths, BRs, `ctau_mm`, theoretical validity flags | Model parameter points, scan grid configurations | YES | NO | NO |
| `dihiggs_clean/dihiggs_boundary/` | Boundary and handoff layer between theory evaluators and ATLAS interpretation | Enriched boundary datasets, visible cross sections ($\sigma_{\text{visible}}$), expected yields ($N_{\text{exp}}$) | Evaluator points (`dihiggs.point.v2`), MadGraph production cross sections, LLP response maps | YES | NO | NO |
| `dihiggs_clean/dihiggs_boundary/lib/2HDMC-1.8.0/` | Vendored C++ 2HDMC physics calculation library | Compiled static/shared libraries for 2HDM tree-level decay widths and theory constraints | C++ source, compiler configuration | NO | NO | NO |
| `dihiggs_clean/dihiggs_boundary/lib/higgstools-v1.2/` | Vendored C++ HiggsTools (HiggsBounds + HiggsSignals) library | Compiled experimental Higgs exclusion limits and signal likelihood evaluations | Experimental limit tables, Higgs couplings | NO | NO | NO |
| `dihiggs_clean/dihiggs_hep_cross/` | MadGraph production driver, cross-section ingestion, and campaign data-authority registry | Cross sections ($\sigma_{\text{prod}}$), MadGraph cards, LHE event samples, data-authority specifications | UFO model files, 2HDM benchmark parameters, run cards | YES | NO | NO |
| `dihiggs_clean/dihiggs_hep_cross/scripts/` | MadGraph generation driver ([`run_physical_point_madgraph.py`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/scripts/run_physical_point_madgraph.py)) and ingestion tooling | Generated process directories, cross-section CSVs, run logs | UFO models, param cards, run configurations | YES | NO | NO |
| `dihiggs_clean/dihiggs_hep_cross/docs/` | Cross-section documentation, process regeneration guides, and authority specifications | Documentation, contract specifications, process notes | Analysis results, workflow specifications | YES | NO | NO |
| `dihiggs_clean/dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md` | Single authoritative data-authority contract governing valid scientific claim sources | Rules defining authoritative vs non-authoritative results, citation prerequisites | Campaign status metadata | YES | YES | YES (defines validity rules; currently declares no active campaign) |
| `dihiggs_clean/dihiggs_hep_cross/state/` | Campaign state registry and active data pointer directory | Machine-readable campaign registry metadata | Campaign manifests, execution logs | YES | NO | NO |
| `dihiggs_clean/dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml` | Active campaign pointer and authoritative dataset registry file | Identification of currently active authoritative campaign, baseline parameters, and lock state | Validated campaign manifests | YES | YES | YES (registry pointer; currently states no active campaign post-reset) |
| `dihiggs_clean/dihiggs_llp_recast/` | ATLAS displaced-vertex plus jets LLP recasting and response modeling (`dvrecast`) | Detector acceptance and efficiency maps ($A_{\text{eff}}$), cutflows, response curves | LHE/Pythia event samples, analysis card definitions | YES | NO | NO |
| `dihiggs_clean/dihiggs_ufo/` | Authoritative UFO model repository, packaging, and validation suites | Verified UFO model archives (`Pack A`, `Pack AA`), decay mechanics, validation reports | FeynRules source exports, Pythia decay configurations | YES | NO | NO |
| `dihiggs_clean/dihiggs_ufo/models/` | Sensitive, immutable UFO model source directories consumed by MadGraph (`releases/pack_a/`, `pack_aa/`) | Validated UFO parameter cards, vertices, couplings | Theoretical model parameters | YES | NO | NO |
| `dihiggs_clean/recast_viewer/` | Static web viewer and pedagogical explorer for ATLAS LLP recast results | Preprocessed JSON datasets, static HTML/JS web bundle | Recast LHE inputs, event telemetry, cutflow summaries | YES | NO | NO |
| `.venv/` | Local Python virtual environments across repos | Installed Python packages, executable CLI wrappers | Project `pyproject.toml`, `requirements.txt` | NO | NO | NO |
| `__pycache__/` | Python bytecode cache across repos | Compiled `.pyc` bytecode files | Python source `.py` files | NO | NO | NO |
| `.pytest_cache/` | Pytest test execution cache across repos | Test outcome cache, failure tracking state | Test execution runs | NO | NO | NO |
| `/home/fabian/atlas_dihiggs_archive/20260831_pre_madgraph_reset/` | Historical pre-reset archive root storing all superseded runs, pilots, and campaign outputs | Preserved historical scientific provenance, checksummed artifacts | Archived workspace state | NO | NO | NO |

---

## Core Repositories and Physics Libraries

### 1. `dihiggs`
**WHAT IT IS:** C++ and Python core implementing canonical 2HDM theory evaluators ([`DihiggsPointV2Evaluator`](file:///home/fabian/atlas_dihiggs_clean/dihiggs/src/DihiggsPointV2Evaluator.cpp), [`Lambda1EvaluatorV2`](file:///home/fabian/atlas_dihiggs_clean/dihiggs/src/Lambda1EvaluatorV2.cpp)), parameter grid scans, and a benchmark search daemon.  
**WHY IT EXISTS:** Owns theoretical 2HDM parameter-point construction, stability predicates (positivity, unitarity, perturbativity), decay widths, branching ratios, and lifetime calculation (`ctau_mm`) without coupling to detector response or cross-section generation.  
**SHOULD AGENTS READ IT:** Yes, agents working on 2HDM parameter space definition, point validity criteria, or scan mechanics should read its contract documentation ([`canonical_evaluators_v2.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs/docs/contracts/canonical_evaluators_v2.md)), but they must never cite raw evaluator outputs as final physical yields.

### 2. `dihiggs_boundary`
**WHAT IT IS:** Python integration package (`dhb`) that enriches theoretical 2HDM points with HiggsBounds/HiggsSignals exclusion checks and combines them with external LLP response maps and direct production cross sections.  
**WHY IT EXISTS:** Serves as the boundary and handoff layer between theoretical model evaluation and ATLAS experimental interpretation, calculating visible cross sections ($\sigma_{\text{visible}} = \sigma_{\text{prod}} \times \text{BR}^2 \times A_{\text{eff}}$) and expected event yields without recalculating 2HDM physics or running MadGraph internally.  
**SHOULD AGENTS READ IT:** Yes, agents should read its integration contracts ([`llp_signal_contract.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_boundary/docs/llp_signal_contract.md), [`boundary_atlas_v1_contract.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_boundary/docs/boundary_atlas_v1_contract.md)) when assembling boundary datasets or interpreting signal yields.

### 3. `2HDMC-1.8.0`
**WHAT IT IS:** Vendored and built C++ library for calculating Two-Higgs-Doublet Model tree-level decay widths, theoretical validity constraints, and loop corrections.  
**WHY IT EXISTS:** Supplies the underlying C++ physics calculation engine compiled under [`dihiggs_boundary/lib/2HDMC-1.8.0/`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_boundary/lib/2HDMC-1.8.0) and used by boundary evaluation routines.  
**SHOULD AGENTS READ IT:** No, agents should treat it as an external compiled dependency and interact solely through the Python/C++ interfaces in `dihiggs` and `dihiggs_boundary`.

### 4. `higgstools-v1.2`
**WHAT IT IS:** Vendored and built C++ framework (per its own README, "a complete rewrite and unification of HiggsBounds-5 and HiggsSignals-2 in modern C++") incorporating experimental Higgs exclusion limit databases and $\chi^2$ likelihood calculations.  
**WHY IT EXISTS:** Determines whether specific 2HDM parameter points are excluded by LEP, Tevatron, and LHC searches or remain consistent with observed 125 GeV Higgs boson measurements.  
**SHOULD AGENTS READ IT:** No, agents should treat it as a compiled third-party physics library and invoke it via `dihiggs_boundary` enrichment scripts rather than inspecting its internal C++ source.

### 5. `dihiggs_hep_cross`
**WHAT IT IS:** Production orchestration repository containing MadGraph run drivers ([`run_physical_point_madgraph.py`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/scripts/run_physical_point_madgraph.py)), cross-section ingestion pipelines, and the workspace data-authority contract files ([`CURRENT_DATA_AUTHORITY.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md), [`CURRENT_CAMPAIGN.yaml`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml)).  
**WHY IT EXISTS:** Executes heavy MadGraph5_aMC@NLO matrix-element cross-section generation and acts as the sole authoritative registry defining which simulation campaigns and numbers are currently valid.  
**SHOULD AGENTS READ IT:** Yes, this is mandatory reading: every agent must check [`docs/CURRENT_DATA_AUTHORITY.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md) and [`state/CURRENT_CAMPAIGN.yaml`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml) before citing or using any cross-section, yield, or sensitivity value.

### 6. `dihiggs_llp_recast`
**WHAT IT IS:** Recasting framework wrapping the public ATLAS displaced-vertex plus jets search (`ATLAS-SUSY-2018-13`) via the `dvrecast` package and external recasting submodules.  
**WHY IT EXISTS:** Evaluates ATLAS detector acceptance and efficiency maps ($A \times \epsilon$) for long-lived scalar decays ($H_2 \to b\bar{b}$) across lifetime and kinematic benchmarks.  
**SHOULD AGENTS READ IT:** Yes, agents working on detector response, displaced vertex efficiencies, or recasting contracts should read its documentation ([`docs/CANONICAL_TRACKLESS_STATUS_20260807.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_llp_recast/docs/CANONICAL_TRACKLESS_STATUS_20260807.md)), ensuring they distinguish the frozen published Trackless analysis from exploratory modified selections.

### 7. `dihiggs_ufo`
**WHAT IT IS:** Authoritative repository housing Universal FeynRules Output (UFO) model files (e.g., `Pack A`, `Pack AA`), Pythia decay configurations, and Monte Carlo integration stability studies.  
**WHY IT EXISTS:** Serves as the immutable physics-model source consumed by MadGraph, maintaining cryptographic SHA-256 checksums and verification suites to prevent silent model corruption.  
**SHOULD AGENTS READ IT:** Yes, agents modifying model parameters or verifying vertex couplings should inspect [`ARTIFACT_REGISTRY.json`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_ufo/ARTIFACT_REGISTRY.json) and [`README.md`](file:///home/fabian/atlas_dihiggs_clean/dihiggs_ufo/README.md), but they must never edit frozen releases in place.

### 8. `recast_viewer`
**WHAT IT IS:** Web frontend and preprocessing pipeline for interactive 3D and 2D visualization of ATLAS displaced-vertex events, cutflows, and counterfactual selections.  
**WHY IT EXISTS:** Provides pedagogical and diagnostic visual inspection of reconstructed tracks, displaced vertices, and jet selections for reference and $H_2$ benchmark events without executing heavy simulations.  
**SHOULD AGENTS READ IT:** Optional; agents interested in event display schemas, pedagogical presentation, or frontend cutflow verification can read its contracts, but it does not generate primary physics numbers.

---

## What is NOT in this table

The historical scientific outputs, intermediate runs, and legacy artifacts listed below have been retired from the active container and relocated to the archive root at `/home/fabian/atlas_dihiggs_archive/20260831_pre_madgraph_reset/`:

- `mission_runs/`: Eight dated mission directories containing raw event cross sections, yields, reviews, and handoffs from historical campaign milestones.
- `runs/`: Eight campaign directories holding multi-phase scan points, boundary refinements, and validation tables.
- `search_runs/`: Diagnostic, dry-run, Monte Carlo, nightly, and smoke search directories superseded by newer structured campaigns.
- `_handoff_out/`: Frozen delivery snapshots of coordinate-explainer and document-integration tables, plots, and manifests.
- `presentations/`: Dated collaboration presentation slides, rendered Markdown/HTML decks, figures, and build scripts.
- `figures/`: Rendered PDF, PNG, and SVG diagnostic plots from past recast and cross-section studies.
- `meeting_signal_table/`: Benchmark yield tables, closure reports, and review packages created for historical collaboration meetings.
- `operator/`: Standalone physical-search operator code and tests migrated into canonical repository modules.
- MadGraph_aMC v3.5.3 install tree: 167MB standalone generator installation, process directories, and pre-compiled libraries.
- Git full-history mirrors: Full mirror bundles of all 6 repositories preserving all historical and unmerged feature branches.
- `graphify-out/`: Regenerable code-knowledge-graph visual cache, index summaries, and query memories.
- Scratch and temporary files: Ephemeral scratch CSVs in `tmp/`, empty placeholder files, and container root logs.

For a complete cryptographic inventory of every archived file, refer to `ARCHIVE_MANIFEST.tsv` in the archive root (cataloged in [`SCIENTIFIC_ARTIFACT_INDEX.tsv`](file:///home/fabian/atlas_dihiggs_cleanup_20260831/SCIENTIFIC_ARTIFACT_INDEX.tsv) and [`WORKSPACE_INVENTORY.tsv`](file:///home/fabian/atlas_dihiggs_cleanup_20260831/WORKSPACE_INVENTORY.tsv)).

> [!CAUTION]
> For every item in the archive: `current_use_allowed = NO`. Archived data must never be cited or used as current scientific evidence.
