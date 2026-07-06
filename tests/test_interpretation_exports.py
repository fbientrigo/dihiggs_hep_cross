import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from llp_recast.hepdata_yaml import tidy_rows
from llp_recast.interpretation import BRIDGE_LAYERS, EFFICIENCY_SEMANTICS, NEXT_DECISION
from llp_recast.plots import values_above_one

ROOT = Path("data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml")

REQUIRED_BRIDGE_LAYERS = {
    "mass",
    "lifetime / total width",
    "production cross-section",
    "boost beta_gamma",
    "branching fractions",
    "hadronic final state",
    "DV radius",
    "DV mass (m_DV)",
    "n_tracks",
    "event activity / Sumpt",
    "event efficiency",
    "vertex efficiency",
    "cutflow (A x epsilon)",
    "limits",
}

VALID_STATUSES = {
    "READY",
    "PROXY_ONLY",
    "HEPDATA_BENCHMARK_ONLY",
    "NEEDS_SIGNAL_MC",
    "NEEDS_2HDM_MAPPING",
    "NOT_DIRECTLY_TRANSFERABLE",
}


# --- event efficiency >1 audit logic ---

def test_values_above_one_flags_only_rows_over_one():
    df = pd.DataFrame({"value": [0.0, 0.5, 1.0, 1.1851, 1.0149]})
    over = values_above_one(df)
    assert sorted(over["value"]) == [1.0149, 1.1851]


def test_values_above_one_empty_when_all_bounded():
    df = pd.DataFrame({"value": [0.0, 0.5, 1.0]})
    assert values_above_one(df).empty


def test_raw_hepdata_trackless_r1150_has_known_above_one_value():
    """Regression check for the audited anomaly: raw YAML must still say 1.1851, not 1.52 or anything else."""
    rows = tidy_rows(ROOT / "event_efficiency_trackless_r_1150_mm.yaml")
    df = pd.DataFrame(rows)
    over = values_above_one(df)
    assert len(over) == 1
    assert over["value"].iloc[0] == pytest.approx(1.1851)


def test_no_event_efficiency_table_reaches_1_52():
    """The audit found no 1.52 anywhere; this pins that finding against future data changes."""
    max_value = 0.0
    for path in sorted(ROOT.glob("event_efficiency_*.yaml")):
        rows = tidy_rows(path)
        df = pd.DataFrame(rows)
        max_value = max(max_value, df["value"].max())
    assert max_value < 1.52
    assert max_value == pytest.approx(1.1851)


# --- JSON schema validity ---

@pytest.fixture(scope="module")
def chat_summaries(tmp_path_factory):
    outdir = tmp_path_factory.mktemp("chat_summaries")
    subprocess.run(
        [sys.executable, "scripts/06_export_chat_summaries.py", "--outdir", str(outdir)],
        check=True,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"},
    )
    return outdir


def _load(outdir: Path, name: str):
    with open(outdir / name) as f:
        return json.load(f)


def test_figure_audit_summary_schema(chat_summaries):
    data = _load(chat_summaries, "figure_audit_summary.json")
    assert 1 <= len(data["figures"]) <= 6
    for fig in data["figures"]:
        for key in ("file", "title", "uses", "main_message", "limitations", "quality_flags"):
            assert key in fig


def test_efficiency_semantics_summary_schema(chat_summaries):
    data = _load(chat_summaries, "efficiency_semantics_summary.json")
    names = {q["name"] for q in data["quantities"]}
    assert names == {
        "P_decay_ID",
        "event_efficiency_trackless",
        "vertex_efficiency",
        "cutflow_Aepsilon",
        "cross_section_limit",
        "scalarS_proxy_Nsig",
    }
    for q in data["quantities"]:
        assert isinstance(q["can_exceed_one"], bool)
    trackless = next(q for q in data["quantities"] if q["name"] == "event_efficiency_trackless")
    assert trackless["can_exceed_one"] is True


def test_paper_vs_2hdm_bridge_json_schema_and_layers(chat_summaries):
    data = _load(chat_summaries, "paper_vs_2hdm_bridge.json")
    layer_names = {row["layer"] for row in data["layers"]}
    assert REQUIRED_BRIDGE_LAYERS <= layer_names
    for row in data["layers"]:
        assert row["status"] in VALID_STATUSES


def test_next_decision_summary_schema(chat_summaries):
    data = _load(chat_summaries, "next_decision_summary.json")
    assert "recommended_next_step" in data
    assert len(data["options"]) >= 2
    for opt in data["options"]:
        assert opt["pros"]
        assert opt["cons"]


def test_anomalies_and_caveats_includes_event_efficiency_audit(chat_summaries):
    data = _load(chat_summaries, "anomalies_and_caveats.json")
    names = {a["name"] for a in data["anomalies"]}
    assert "trackless_event_efficiency_above_one" in names


def test_at_most_five_json_files_written(chat_summaries):
    assert len(list(chat_summaries.glob("*.json"))) <= 5


# --- bridge doc/module consistency ---

def test_bridge_module_contains_required_layers():
    layer_names = {row["layer"] for row in BRIDGE_LAYERS}
    assert REQUIRED_BRIDGE_LAYERS <= layer_names


def test_bridge_module_statuses_are_valid():
    for row in BRIDGE_LAYERS:
        assert row["status"] in VALID_STATUSES


def test_bridge_doc_mentions_every_layer():
    doc = Path("docs/recast/paper_vs_our_2hdm_bridge.md").read_text().lower()
    for layer in REQUIRED_BRIDGE_LAYERS:
        # doc uses singular/short forms (e.g. "DV mass" not "DV mass (m_DV)")
        key = layer.split(" (")[0].lower()
        assert key in doc, f"bridge doc missing layer: {key}"


def test_next_decision_module_matches_export():
    assert NEXT_DECISION["recommended_choice"] in {opt["option"] for opt in NEXT_DECISION["options"]}
