import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "11_ingest_madgraph_xsec.py"

spec = importlib.util.spec_from_file_location("ingest_madgraph_xsec", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _priority() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"priority_rank": 1, "point_id": "p1", "m_H_GeV": 500.0, "Gamma_over_m": 0.02, "br_gaga": 0.05},
            {"priority_rank": 2, "point_id": "p2", "m_H_GeV": 700.0, "Gamma_over_m": 0.06, "br_gaga": 0.01},
        ]
    )


def test_template_exposes_expected_madgraph_columns():
    template = mod.build_madgraph_template(_priority(), max_rows=1)

    assert template["point_id"].tolist() == ["p1"]
    assert list(template.columns) == mod.TEMPLATE_COLUMNS
    assert template.loc[0, "xsec_pb"] == ""
    assert template.loc[0, "banner_path"] == ""


def test_pb_cross_section_is_converted_to_fb_and_ggf_component():
    table = pd.DataFrame(
        [
            {
                "point_id": "p1",
                "mg_run_name": "run_01",
                "process": "g g > h2 > a a",
                "xsec_pb": 0.012,
                "madgraph_version": "MG5_aMC_test",
                "model_name": "future_ufo",
            }
        ]
    )

    sigma = mod.madgraph_to_sigma_input(table, priority=_priority(), strict_point_ids=True)
    row = sigma.iloc[0]

    assert row["point_id"] == "p1"
    assert row["production_mode"] == "ggF"
    assert row["sigma_total_fb"] == 12.0
    assert row["sigma_ggF_fb"] == 12.0
    assert pd.isna(row["sigma_VBF_fb"])
    assert "MadGraph_normalized_table" in row["sigma_source"]
    assert "model_name=future_ufo" in row["sigma_notes"]


def test_fb_cross_section_takes_precedence_over_pb():
    table = pd.DataFrame(
        [
            {
                "point_id": "p1",
                "process": "p p > h2 j j",
                "xsec_pb": 10.0,
                "xsec_fb": 3.0,
                "production_mode": "VBF",
            }
        ]
    )

    sigma = mod.madgraph_to_sigma_input(table)
    row = sigma.iloc[0]

    assert row["production_mode"] == "VBF"
    assert row["sigma_total_fb"] == 3.0
    assert row["sigma_VBF_fb"] == 3.0
    assert pd.isna(row["sigma_ggF_fb"])


def test_k_factor_is_recorded_but_not_applied_by_default():
    table = pd.DataFrame([{"point_id": "p1", "xsec_fb": 10.0, "k_factor": 2.0}])

    sigma = mod.madgraph_to_sigma_input(table, apply_k_factor=False)
    row = sigma.iloc[0]

    assert row["sigma_total_fb"] == 10.0
    assert "k_factor_recorded_not_applied=2.0" in row["sigma_notes"]


def test_k_factor_can_be_applied_explicitly():
    table = pd.DataFrame([{"point_id": "p1", "xsec_fb": 10.0, "k_factor": 2.0}])

    sigma = mod.madgraph_to_sigma_input(table, apply_k_factor=True)
    row = sigma.iloc[0]

    assert row["sigma_total_fb"] == 20.0
    assert "k_factor_applied=2.0" in row["sigma_notes"]


def test_strict_point_ids_reject_unknown_priority_point():
    table = pd.DataFrame([{"point_id": "not_in_priority", "xsec_fb": 1.0}])

    try:
        mod.madgraph_to_sigma_input(table, priority=_priority(), strict_point_ids=True)
    except ValueError as exc:
        assert "not present in priority" in str(exc)
    else:
        raise AssertionError("unknown point_id should fail in strict mode")


def test_duplicate_madgraph_point_ids_are_rejected():
    table = pd.DataFrame([{"point_id": "p1", "xsec_fb": 1.0}, {"point_id": "p1", "xsec_fb": 2.0}])

    try:
        mod.madgraph_to_sigma_input(table)
    except ValueError as exc:
        assert "duplicate point_id" in str(exc)
    else:
        raise AssertionError("duplicate point_id should fail")
