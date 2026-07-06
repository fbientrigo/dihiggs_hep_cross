"""Structured data behind the interpretation docs/figures/JSON exports.

Single source of truth for the paper-vs-2HDM bridge table and the efficiency
quantity semantics, so `docs/recast/paper_vs_our_2hdm_bridge.md`,
`scripts/05_make_interpretation_figures.py` (Figure D), and
`scripts/06_export_chat_summaries.py` cannot silently drift apart. If you
edit the bridge table, update `docs/recast/paper_vs_our_2hdm_bridge.md` to
match by hand -- the prose doc is not auto-generated from this module.
"""
from __future__ import annotations

# Status vocabulary shared with docs/recast/paper_vs_our_2hdm_bridge.md
STATUS_READY = "READY"
STATUS_PROXY_ONLY = "PROXY_ONLY"
STATUS_HEPDATA_BENCHMARK_ONLY = "HEPDATA_BENCHMARK_ONLY"
STATUS_NEEDS_SIGNAL_MC = "NEEDS_SIGNAL_MC"
STATUS_NEEDS_2HDM_MAPPING = "NEEDS_2HDM_MAPPING"
STATUS_NOT_DIRECTLY_TRANSFERABLE = "NOT_DIRECTLY_TRANSFERABLE"

BRIDGE_LAYERS: list[dict[str, str]] = [
    {
        "layer": "mass",
        "paper_scalar_S": "benchmark grid mS = 100, 170, 250 GeV",
        "atlas_hepdata": "not model-specific; tables indexed by neutralino mass, not mS",
        "current_proxy": "PAPER_BENCHMARK_MASSES_GEV copied from paper grid",
        "our_2hdm_need": "2HDM scan m_scalar_GeV per point",
        "status": STATUS_READY,
    },
    {
        "layer": "lifetime / total width",
        "paper_scalar_S": "sin_theta sets ctau in the paper's own model",
        "atlas_hepdata": "tables indexed by tau for the EWK benchmark, not derived from any width",
        "current_proxy": "generic ctau_mm_from_width_gev conversion",
        "our_2hdm_need": "total_width_GeV from 2HDMC/width calculator -> ctau_mm",
        "status": STATUS_NEEDS_2HDM_MAPPING,
    },
    {
        "layer": "production cross-section",
        "paper_scalar_S": "sigma(gg -> h* -> SS), not yet digitized here",
        "atlas_hepdata": "none (no scalar-S production info)",
        "current_proxy": "sigma_fb_assumed = 1.0 flat placeholder",
        "our_2hdm_need": "MadGraph or analytic 2HDM calculation; NOT derivable from width",
        "status": STATUS_NEEDS_SIGNAL_MC,
    },
    {
        "layer": "boost beta_gamma",
        "paper_scalar_S": "set by mS, sqrt(s), h* kinematics -- a distribution, not one number",
        "atlas_hepdata": "none",
        "current_proxy": "beta_gamma_assumed = 1.0 flat placeholder",
        "our_2hdm_need": "truth-level beta_gamma distribution per 2HDM point from Pythia",
        "status": STATUS_NEEDS_SIGNAL_MC,
    },
    {
        "layer": "branching fractions",
        "paper_scalar_S": "BR_bb/WW/ZZ/gg tables likely exist, not yet digitized",
        "atlas_hepdata": "none",
        "current_proxy": "br_hadronic_proxy step function (0.8 below 140 GeV, 0.5 above); no citation",
        "our_2hdm_need": "2HDMC exclusive BRs, BR_hadronic_proxy computed consistently from those",
        "status": STATUS_PROXY_ONLY,
    },
    {
        "layer": "hadronic final state",
        "paper_scalar_S": "S -> qq/gg dominant channels assumed",
        "atlas_hepdata": "generic; efficiencies tuned to EWK decay products, not DV parent multiplicity",
        "current_proxy": "not modeled beyond the BR step function",
        "our_2hdm_need": "truth-level jet multiplicity/kinematics from 2HDM S decay MC",
        "status": STATUS_NEEDS_SIGNAL_MC,
    },
    {
        "layer": "DV radius",
        "paper_scalar_S": "not published as a table here",
        "atlas_hepdata": "acceptance/cutflow/efficiency tables binned by radius (4mm, 1150mm, 3870mm, ID edge 300mm)",
        "current_proxy": "decay_probability_between_radii -- real, model-agnostic geometry",
        "our_2hdm_need": "same math, fed with 2HDM ctau, beta_gamma",
        "status": STATUS_READY,
    },
    {
        "layer": "DV mass (m_DV)",
        "paper_scalar_S": "not applicable (paper-level, not detector-level)",
        "atlas_hepdata": "vertex_efficiency_grid.csv -- 12 radial bins x m_DV x n_tracks, EWK decay products",
        "current_proxy": "not used; flat eff_vertex_proxy averaged over EWK cutflow final step",
        "our_2hdm_need": "truth-level m_DV per simulated DV from 2HDM S decay MC",
        "status": STATUS_NEEDS_SIGNAL_MC,
    },
    {
        "layer": "n_tracks",
        "paper_scalar_S": "not applicable (paper-level)",
        "atlas_hepdata": "same vertex_efficiency_grid.csv",
        "current_proxy": "not used",
        "our_2hdm_need": "truth-level charged-track multiplicity per DV",
        "status": STATUS_NEEDS_SIGNAL_MC,
    },
    {
        "layer": "event activity / Sumpt",
        "paper_scalar_S": "not applicable (paper-level)",
        "atlas_hepdata": "event_efficiency_trackless/_highpt.csv, 13 Sumpt bins x 3 radial categories; "
        "R<1150mm bin peaks at 1.1851, not a bounded probability",
        "current_proxy": "not used; flat eff_event_proxy = 0.5 placeholder",
        "our_2hdm_need": "truth-level event Sumpt per 2HDM event",
        "status": STATUS_NEEDS_SIGNAL_MC,
    },
    {
        "layer": "event efficiency",
        "paper_scalar_S": "not applicable",
        "atlas_hepdata": "HEPData reinterpretation-material weight, EWK-specific, can exceed 1",
        "current_proxy": "eff_event_proxy = 0.5 flat placeholder",
        "our_2hdm_need": "Sumpt-matched lookup in the ATLAS table, still borrowed",
        "status": STATUS_HEPDATA_BENCHMARK_ONLY,
    },
    {
        "layer": "vertex efficiency",
        "paper_scalar_S": "not applicable",
        "atlas_hepdata": "vertex_efficiency_grid.csv, bounded [0,1] in this data, gated by m_DV/n_tracks/radius",
        "current_proxy": "mean of EWK cutflow final A x eps step, not an m_DV/n_tracks lookup",
        "our_2hdm_need": "cell-by-cell lookup once truth m_DV/n_tracks exist",
        "status": STATUS_HEPDATA_BENCHMARK_ONLY,
    },
    {
        "layer": "cutflow (A x epsilon)",
        "paper_scalar_S": "not applicable",
        "atlas_hepdata": "cutflow_trackless_ewk.csv, 4 EWK mass/lifetime points, full selection chain",
        "current_proxy": "only the final step's value used, averaged, as eff_vertex_proxy input",
        "our_2hdm_need": "our own cutflow requires detector-level simulation (Delphes or similar), not built here",
        "status": STATUS_NOT_DIRECTLY_TRANSFERABLE,
    },
    {
        "layer": "limits",
        "paper_scalar_S": "paper likely has its own exclusion curves, not yet digitized",
        "atlas_hepdata": "excl_xsec_ewk.csv, observed/expected 95% CL limits vs. neutralino mass and tau",
        "current_proxy": "nearest_public_limit_fb: nearest EWK-benchmark limit by mass/tau, illustrative anchor only",
        "our_2hdm_need": "our own A x epsilon (all rows above) and our own cross section, not a borrowed EWK number",
        "status": STATUS_NOT_DIRECTLY_TRANSFERABLE,
    },
]

# Matches the summary table at the bottom of docs/recast/efficiency_semantics.md
EFFICIENCY_SEMANTICS: list[dict] = [
    {
        "name": "P_decay_ID",
        "type": "geometric_probability",
        "can_exceed_one": False,
        "depends_on_particle": ["ctau", "beta_gamma"],
        "depends_on_atlas_data": False,
        "transfer_to_2hdm": "yes_if_ctau_and_beta_gamma_known",
        "caveat": "Model-agnostic geometry; ignores eta/z acceptance and detector/reconstruction effects.",
    },
    {
        "name": "event_efficiency_trackless",
        "type": "hepdata_reinterpretation_weight",
        "can_exceed_one": True,
        "depends_on_particle": ["Sumpt", "DV radius"],
        "depends_on_atlas_data": True,
        "transfer_to_2hdm": "shape_only_not_the_number",
        "caveat": "Published >1 (max 1.1851, R<1150mm, Sumpt in [0.6,0.8) GeV). ATLAS's own"
        " chargino/neutralino EWK benchmark, not scalar-S. Not a bounded pass/total probability"
        " despite the column header 'Efficiency'.",
    },
    {
        "name": "vertex_efficiency",
        "type": "hepdata_detector_efficiency",
        "can_exceed_one": False,
        "depends_on_particle": ["m_DV", "n_tracks", "DV radius"],
        "depends_on_atlas_data": True,
        "transfer_to_2hdm": "cell_by_cell_needs_signal_mc",
        "caveat": "Bounded [0,1] in the published data, but for EWK decay products, not scalar-S/2HDM ones.",
    },
    {
        "name": "cutflow_Aepsilon",
        "type": "cumulative_detector_efficiency",
        "can_exceed_one": False,
        "depends_on_particle": ["full event reconstruction chain"],
        "depends_on_atlas_data": True,
        "transfer_to_2hdm": "shape_only_not_the_number",
        "caveat": "EWK-benchmark cutflow; only the per-step loss shape is a transferable lesson.",
    },
    {
        "name": "cross_section_limit",
        "type": "physical_cross_section_fb",
        "can_exceed_one": True,
        "depends_on_particle": ["production mode", "A x epsilon"],
        "depends_on_atlas_data": True,
        "transfer_to_2hdm": "no_until_own_Aepsilon_computed",
        "caveat": "Not a probability at all -- a cross-section upper limit in fb, computed for the EWK"
        " benchmark's own A x epsilon.",
    },
    {
        "name": "scalarS_proxy_Nsig",
        "type": "placeholder_heavy_proxy_yield",
        "can_exceed_one": True,
        "depends_on_particle": ["mS", "ctau (paper grid only)"],
        "depends_on_atlas_data": True,
        "transfer_to_2hdm": "no",
        "caveat": "Expected event count, not a probability. Built from flat sigma/BR/beta_gamma/"
        "efficiency placeholders -- NOT_EXCLUSION_GRADE.",
    },
]

NEXT_DECISION: dict = {
    "recommended_next_step": "generate_mg5_pythia_signal_first",
    "options": [
        {
            "option": "digitize_paper_curves_first",
            "pros": [
                "Fast -- no MC generation needed, just plot digitization",
                "Gives a direct sanity check against the paper's own published exclusion/BR curves",
            ],
            "cons": [
                "Does not produce the truth-level Sumpt/m_DV/n_tracks needed to use the ATLAS"
                " tables correctly",
                "Still leaves beta_gamma and sigma as placeholders",
            ],
        },
        {
            "option": "generate_mg5_pythia_signal_first",
            "pros": [
                "Unblocks every NEEDS_SIGNAL_MC row in the bridge table at once (sigma, beta_gamma,"
                " m_DV, n_tracks, Sumpt)",
                "Replaces the four flat placeholders (sigma_fb_assumed, beta_gamma_assumed,"
                " eff_event_proxy, eff_vertex_proxy) with real truth-level lookups into the"
                " existing HEPData tables",
                "Directly serves the 2HDM use case, which needs the same MC chain",
            ],
            "cons": [
                "Requires a FeynRules/UFO model for the scalar S, MadGraph, and Pythia -- setup"
                " and validation time before any new number appears",
            ],
        },
    ],
    "recommended_choice": "generate_mg5_pythia_signal_first",
    "reason": "Digitizing paper curves only checks our geometry against the paper's own numbers;"
    " it does not unblock the ATLAS-table lookups or the 2HDM use case, both of which need real"
    " truth-level kinematics. MC generation serves both goals at once.",
}
