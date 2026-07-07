import importlib.util
from pathlib import Path

import pandas as pd

from llp_recast import madgraph as mg

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "12_prepare_madgraph_runs.py"
TEMPLATE_DIR = ROOT / "data" / "madgraph" / "templates"

spec = importlib.util.spec_from_file_location("prepare_madgraph_runs", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _priority() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"priority_rank": 1, "point_id": "scan_tb_10000:row42", "m_H_GeV": 500.0, "Gamma_H_GeV": 10.0, "Gamma_over_m": 0.02, "br_gaga": 0.05},
            {"priority_rank": 2, "point_id": "p2", "m_H_GeV": 700.0, "Gamma_H_GeV": 42.0, "Gamma_over_m": 0.06, "br_gaga": 0.01},
        ]
    )


def test_sanitize_run_name_is_filesystem_safe():
    assert mg.sanitize_run_name("scan_tb_10000:row42") == "mg_scan_tb_10000_row42"
    assert mg.sanitize_run_name("") == "mg_run"


def test_infer_production_mode_prefers_explicit_then_process():
    assert mg.infer_production_mode(existing="VBF") == "VBF"
    assert mg.infer_production_mode(process="g g > h2") == "ggF"
    assert mg.infer_production_mode(process="p p > h2 j j") == "VBF"
    assert mg.infer_production_mode() == "unknown"


def test_render_template_replaces_known_and_keeps_unknown():
    out = mg.render_template("m={{MH_GEV}} x={{UNSET}}", {"MH_GEV": 500.0})
    assert out == "m=500.0 x={{UNSET}}"


def test_empty_priority_yields_schema_stable_empty_skeleton():
    skeleton = mg.build_run_skeleton(pd.DataFrame())
    assert list(skeleton.columns) == mg.MADGRAPH_TEMPLATE_COLUMNS
    assert skeleton.empty


def test_skeleton_fills_metadata_but_leaves_cross_sections_blank():
    skeleton = mg.build_run_skeleton(_priority(), deck_root=Path("outputs/madgraph_runs"))

    assert list(skeleton.columns) == mg.MADGRAPH_TEMPLATE_COLUMNS
    row = skeleton.iloc[0]
    assert row["point_id"] == "scan_tb_10000:row42"
    assert row["mg_run_name"] == "mg_scan_tb_10000_row42"
    assert row["process"] == mg.DEFAULT_PROCESS
    assert row["production_mode"] == "ggF"
    assert row["model_name"] == mg.MODEL_PLACEHOLDER
    assert row["param_card_path"].endswith("mg_scan_tb_10000_row42/param_card_fragment.dat")
    assert row["notes"] == mg.UNRUN_NOTE
    # No fabricated physics: every cross-section field is blank.
    for col in ("xsec_pb", "xsec_fb", "xsec_unc_pb", "madgraph_version", "banner_path", "lhe_path"):
        assert (skeleton[col] == "").all()


def test_render_decks_writes_substituted_files(tmp_path):
    priority = _priority()
    deck_root = tmp_path / "runs"
    skeleton = mg.build_run_skeleton(priority, deck_root=deck_root)
    templates = mod.load_templates(TEMPLATE_DIR)

    dirs = mod.render_decks(skeleton, templates, deck_root=deck_root, model_name=mg.MODEL_PLACEHOLDER)

    assert len(dirs) == 2
    proc = (deck_root / "mg_scan_tb_10000_row42" / "proc_card.dat").read_text()
    assert "scan_tb_10000:row42" in proc
    assert "g g > h2" in proc
    assert "{{" not in proc  # every known placeholder was substituted
    param = (deck_root / "mg_scan_tb_10000_row42" / "param_card_fragment.dat").read_text()
    assert "500.0" in param  # m_H
    run_sh = deck_root / "mg_scan_tb_10000_row42" / "run_commands.sh"
    assert run_sh.stat().st_mode & 0o111  # executable


def test_load_templates_reports_missing_directory(tmp_path):
    try:
        mod.load_templates(tmp_path / "nope")
    except FileNotFoundError as exc:
        assert "template directory not found" in str(exc)
    else:
        raise AssertionError("missing template dir should raise")
