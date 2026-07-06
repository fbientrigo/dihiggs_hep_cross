#!/usr/bin/env python3
"""Compact JSON summaries for pasting into a web chat.

At most 5 files, all derived from the same structured data used by the docs
and figures (llp_recast.interpretation) so nothing drifts. Not exclusion
grade -- see docs/recast/current_limitations.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from llp_recast.interpretation import BRIDGE_LAYERS, EFFICIENCY_SEMANTICS, NEXT_DECISION

FIGURE_AUDIT = [
    {
        "file": "outputs/figures_v2/figA_decay_geometry_transferable.png",
        "title": "Decay-geometry transferable layer",
        "uses": ["understanding the ID decay-probability window", "sanity-checking ctau/beta_gamma choices"],
        "main_message": "P(4mm < R < 300mm) vs ctau for several beta_gamma values; transferable to any"
        " model if ctau and beta_gamma are known.",
        "limitations": [
            "assumes one fixed beta_gamma per curve, not a real event-by-event distribution",
            "no ATLAS efficiency applied -- geometry only",
        ],
        "quality_flags": ["GEOMETRIC_PROBABILITY", "NEEDS_2HDM_MAPPING(ctau only)"],
    },
    {
        "file": "outputs/figures_v2/figB_trackless_event_efficiency_audited.png",
        "title": "Trackless event efficiency, audited",
        "uses": ["seeing the Sumpt/radius dependence of ATLAS's published event-level weight"],
        "main_message": "Published ATLAS EWK-benchmark efficiency; radius- and Sumpt-dependent; the"
        " R<1150mm curve peaks at 1.1851, confirmed identical from raw YAML to tidy CSV to plot.",
        "limitations": [
            "not scalar-S's efficiency -- ATLAS's own chargino/neutralino EWK benchmark",
            "not bounded by 1 despite the 'Efficiency' column name; treat as a reinterpretation weight",
        ],
        "quality_flags": ["HEPDATA_BENCHMARK_PARAMETRIZATION", "NOT_UNIVERSAL_EFFICIENCY", "EWK_BENCHMARK_NOT_SCALAR_S"],
    },
    {
        "file": "outputs/figures_v2/figC_vertex_efficiency_requirements.png",
        "title": "Vertex efficiency requirements",
        "uses": ["showing that radius alone is not sufficient for vertex efficiency"],
        "main_message": "Vertex efficiency is gated by m_DV and n_tracks, not lifetime/radius alone, and"
        " the gate shape changes with radius.",
        "limitations": [
            "EWK-benchmark decay products, not scalar-S/2HDM ones",
            "cannot be looked up without truth-level m_DV/n_tracks from signal MC",
        ],
        "quality_flags": ["HEPDATA_BENCHMARK_PARAMETRIZATION", "NEEDS_SIGNAL_MC"],
    },
    {
        "file": "outputs/figures_v2/figD_paper_vs_our_case_pipeline.png",
        "title": "Paper S -> HEPData -> current proxy -> 2HDM missing inputs",
        "uses": ["one-page meeting reference for what is READY vs. placeholder vs. missing"],
        "main_message": "14-layer bridge table color-coded by transfer status; only mass-as-a-label and"
        " decay geometry are READY today.",
        "limitations": ["a compressed view -- see docs/recast/paper_vs_our_2hdm_bridge.md for full text"],
        "quality_flags": ["SEE_BRIDGE_TABLE"],
    },
    {
        "file": "outputs/figures_v2/figE_scalarS_proxy_with_missing_inputs.png",
        "title": "Scalar-S proxy map with missing-input overlay",
        "uses": ["prioritizing which (mS, ctau) benchmark point to validate first with real MC"],
        "main_message": "Shows where in (mS, ctau) space the current placeholder-heavy pipeline predicts"
        " the most proxy signal, with every placeholder input listed alongside.",
        "limitations": [
            "sigma, BR, beta_gamma, and both efficiencies are flat placeholders or borrowed EWK numbers",
            "NOT EXCLUSION GRADE -- not comparable to any ATLAS or paper result",
        ],
        "quality_flags": ["PAPER_AWARE_PROXY", "NOT_EXCLUSION_GRADE", "NEEDS_SIGNAL_MC"],
    },
]

ANOMALIES = [
    {
        "name": "trackless_event_efficiency_above_one",
        "observed": "R<1150mm trackless event-efficiency curve peaks at 1.1851 at Sumpt in [0.6,0.8) GeV;"
        " a second table (highpt, R<1150mm) peaks at 1.0149.",
        "source": "data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml/"
        "event_efficiency_trackless_r_1150_mm.yaml, line 12",
        "raw_value": 1.1851,
        "plotted_value": 1.1851,
        "status": "raw_hepdata_confirmed_not_a_bug",
        "interpretation": "HEPData's 'Efficiency' column on this table is explicitly labeled"
        " 'Reinterpretation Material' in the submission metadata -- a published reinterpretation"
        " weight/parameterization for the ATLAS SUSY EWK benchmark, not a bounded pass/total"
        " probability. The mechanism producing values >1 is not stated in the local metadata and"
        " is not asserted here.",
        "action_taken": "No clipping; raw value preserved through tidy CSV and figure. Figure B"
        " annotates the point explicitly. See docs/recast/efficiency_audit_event_efficiency_gt1.md"
        " for the full raw-YAML -> tidy -> plot trace.",
    },
    {
        "name": "requested_value_1_52_not_found",
        "observed": "The audit request referenced a plotted value of ~1.52 in the trackless"
        " event-efficiency figure.",
        "source": "full sweep of all 6 event_efficiency_*.yaml files and every outputs/hepdata_tidy/*.csv"
        " column named 'value'",
        "raw_value": None,
        "plotted_value": None,
        "status": "unresolved_discrepancy_with_request",
        "interpretation": "No value of 1.52 exists anywhere in this pipeline's HEPData tables or"
        " tidy/plotted outputs. The maximum value found (any table) is 1.1851. This may reflect a"
        " stale run, a different figure, or a misremembered number -- flagged here rather than"
        " silently substituted.",
        "action_taken": "None -- documented as a discrepancy for the user to reconcile.",
    },
]


def _validate(name: str, obj, required_keys: set[str]) -> None:
    items = obj if isinstance(obj, list) else next(iter(obj.values()))
    for item in items:
        missing = required_keys - set(item)
        if missing:
            raise ValueError(f"{name}: item missing keys {missing}: {item}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Export compact JSON summaries for web-chat transfer")
    ap.add_argument("--outdir", default="outputs/chat_summaries")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    payloads = {
        "figure_audit_summary.json": {"figures": FIGURE_AUDIT},
        "efficiency_semantics_summary.json": {"quantities": EFFICIENCY_SEMANTICS},
        "paper_vs_2hdm_bridge.json": {"layers": BRIDGE_LAYERS},
        "next_decision_summary.json": NEXT_DECISION,
        "anomalies_and_caveats.json": {"anomalies": ANOMALIES},
    }

    _validate("figure_audit_summary", FIGURE_AUDIT, {"file", "title", "uses", "main_message", "limitations", "quality_flags"})
    _validate("efficiency_semantics_summary", EFFICIENCY_SEMANTICS, {"name", "type", "can_exceed_one", "depends_on_particle", "depends_on_atlas_data", "transfer_to_2hdm", "caveat"})
    _validate("paper_vs_2hdm_bridge", BRIDGE_LAYERS, {"layer", "paper_scalar_S", "atlas_hepdata", "current_proxy", "our_2hdm_need", "status"})
    _validate("anomalies_and_caveats", ANOMALIES, {"name", "observed", "source", "raw_value", "plotted_value", "status", "interpretation", "action_taken"})

    # Keep this directory paste-ready: it is intentionally capped at these five
    # LLP interpretation summaries, even if older runs left unrelated JSON here.
    for stale in outdir.glob("*.json"):
        if stale.name not in payloads:
            stale.unlink()

    for fname, payload in payloads.items():
        path = outdir / fname
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote {path}")

    print(f"[NOTE] {len(payloads)} compact JSON summaries. Not exclusion grade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
