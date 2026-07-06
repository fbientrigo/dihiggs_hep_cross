import pytest

from llp_recast.hepdata_yaml import classify_table_name, parse_bin_label


def test_classify_core_tables():
    assert classify_table_name("yields_trackless_sr_observed.yaml") == "yields"
    assert classify_table_name("excl_xsec_ewk.yaml") == "cross_section_limits"
    assert classify_table_name("event_efficiency_trackless_r_1150_mm.yaml") == "event_efficiency"
    assert classify_table_name("vertex_efficiency_r_180_300_mm.yaml") == "vertex_efficiency"
    assert classify_table_name("cutflow_trackless_ewk.yaml") == "cutflow"


def test_parse_bin_label_basic():
    assert parse_bin_label("[0.0, 0.2)") == (0.0, 0.2)


def test_parse_bin_label_scientific_notation():
    assert parse_bin_label("[1.0e-01, 2.0e+01)") == (0.1, 20.0)


def test_parse_bin_label_rejects_non_bin_string():
    with pytest.raises(ValueError):
        parse_bin_label("Multijet trigger")
