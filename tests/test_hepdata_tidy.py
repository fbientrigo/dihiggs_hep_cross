from pathlib import Path

from llp_recast.hepdata_yaml import tidy_rows

ROOT = Path("data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml")


def test_cutflow_trackless_ewk_recovers_ten_selections():
    rows = tidy_rows(ROOT / "cutflow_trackless_ewk.yaml")
    selections = {r["Selections"] for r in rows}
    assert len(selections) == 10


def test_acceptance_trackless_ewk_identifies_dv_selection_labels():
    rows = tidy_rows(ROOT / "acceptance_trackless_ewk.yaml")
    selections = {r["Selections"] for r in rows}
    dv_selections = {s for s in selections if "DV" in s}
    assert len(dv_selections) >= 4
    assert any("m_{DV}" in s for s in selections)


def test_tidy_rows_preserve_qualifiers_and_source():
    rows = tidy_rows(ROOT / "cutflow_trackless_ewk.yaml")
    assert all(r["source_yaml"] == "cutflow_trackless_ewk.yaml" for r in rows)
    assert all(r["qualifiers"] for r in rows)
    assert any("GeV" in r["qualifiers"] for r in rows)
