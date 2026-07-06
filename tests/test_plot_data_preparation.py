import math

import pandas as pd
import pytest

from llp_recast.plots import (
    prepare_fig1_sweetspot,
    prepare_fig2_event_efficiency,
    prepare_fig3_vertex_heatmap,
    prepare_fig4_cutflow,
    prepare_fig5_inventory,
    prepare_fig6_proxy_map,
)


def test_fig1_sweetspot_shape_and_bounds():
    df = prepare_fig1_sweetspot([1.0, 10.0, 100.0], [0.5, 1.0, 2.0])
    assert df.shape == (9, 3)
    assert (df["P_decay_in_ID"] >= 0.0).all()
    assert (df["P_decay_in_ID"] <= 1.0).all()


def test_fig1_sweetspot_short_ctau_has_low_probability():
    df = prepare_fig1_sweetspot([0.001], [1.0])
    assert df["P_decay_in_ID"].iloc[0] < 0.01


def test_fig2_event_efficiency_maps_radial_category():
    df = pd.DataFrame(
        {
            "source_yaml": [
                "event_efficiency_trackless_r_1150_mm.yaml",
                "event_efficiency_trackless_r_1150_3870_mm.yaml",
                "event_efficiency_trackless_r_3870_mm.yaml",
            ],
            "Sumpt [GeV]": ["[0.0, 0.2)", "[0.2, 0.4)", "[0.4, 0.6)"],
            "value": [0.0, 0.5, 1.1],
        }
    )
    out = prepare_fig2_event_efficiency(df)
    assert set(out["radial_category"]) == {"R < 1150 mm", "1150 < R < 3870 mm", "R > 3870 mm"}
    for _, group in out.groupby("radial_category"):
        assert list(group["sumpt_lo_gev"]) == sorted(group["sumpt_lo_gev"])


def test_fig2_event_efficiency_rejects_unknown_filename():
    df = pd.DataFrame({"source_yaml": ["unknown_file.yaml"], "Sumpt [GeV]": ["[0.0, 0.2)"], "value": [0.1]})
    with pytest.raises(ValueError):
        prepare_fig2_event_efficiency(df)


def test_fig3_vertex_heatmap_pivots_per_radius_bin():
    df = pd.DataFrame(
        {
            "radius_bin_label": ["22_25_mm", "22_25_mm", "84_111_mm"],
            "m_DV [GeV]": ["[10.0, 15.0)", "[15.0, 20.0)", "[10.0, 15.0)"],
            "n_tracks": ["[5.0, 6.0)", "[5.0, 6.0)", "[6.0, 7.0)"],
            "value": [0.1, 0.2, 0.3],
        }
    )
    grids = prepare_fig3_vertex_heatmap(df, radius_bin_labels=("22_25_mm", "84_111_mm"))
    assert set(grids) == {"22_25_mm", "84_111_mm"}
    assert grids["22_25_mm"].shape == (2, 1)


def test_fig3_vertex_heatmap_rejects_missing_radius_bin():
    df = pd.DataFrame(
        {
            "radius_bin_label": ["22_25_mm"],
            "m_DV [GeV]": ["[10.0, 15.0)"],
            "n_tracks": ["[5.0, 6.0)"],
            "value": [0.1],
        }
    )
    with pytest.raises(ValueError):
        prepare_fig3_vertex_heatmap(df, radius_bin_labels=("does_not_exist",))


def test_fig4_cutflow_step_index_and_legend_label():
    quals = "Luminosity=139 fb$^{-1}$; Energy=13 TeV; $m(\\tilde{\\chi}^0_1)$=500 GeV; $\\tau$=0.1 ns"
    df = pd.DataFrame(
        {
            "qualifiers": [quals] * 10,
            "Selections": [f"step{i}" for i in range(10)],
            "value": [1.0 - 0.05 * i for i in range(10)],
        }
    )
    out = prepare_fig4_cutflow(df)
    assert list(out["step_index"]) == list(range(10))
    assert out["legend_label"].iloc[0] == "m=500 GeV, tau=0.1 ns"


def test_fig4_cutflow_rejects_wrong_step_count():
    df = pd.DataFrame({"qualifiers": ["a", "a", "b"], "Selections": ["s1", "s2", "s1"], "value": [1.0, 0.9, 1.0]})
    with pytest.raises(ValueError):
        prepare_fig4_cutflow(df)


def test_fig5_inventory_counts_by_group_including_other():
    df = pd.DataFrame({"group": ["acceptance", "acceptance", "other", "cutflow"]})
    counts = prepare_fig5_inventory(df)
    assert counts["acceptance"] == 2
    assert counts["other"] == 1


def test_fig6_proxy_map_pivots_dense_grid():
    df = pd.DataFrame(
        {
            "mS_GeV": [100.0, 100.0, 170.0, 170.0],
            "ctau_mm": [3.0, 10.0, 3.0, 10.0],
            "Nsig_139fb": [1.0, 2.0, 3.0, 4.0],
        }
    )
    grid = prepare_fig6_proxy_map(df, value_col="Nsig_139fb")
    assert grid.shape == (2, 2)
    assert math.isclose(grid.loc[100.0, 3.0], 1.0)


def test_fig6_proxy_map_rejects_sparse_grid():
    df = pd.DataFrame({"mS_GeV": [100.0, 170.0], "ctau_mm": [3.0, 10.0], "Nsig_139fb": [1.0, 2.0]})
    with pytest.raises(ValueError):
        prepare_fig6_proxy_map(df, value_col="Nsig_139fb")


def test_fig6_proxy_map_rejects_missing_column():
    df = pd.DataFrame({"mS_GeV": [100.0], "ctau_mm": [3.0]})
    with pytest.raises(ValueError):
        prepare_fig6_proxy_map(df, value_col="does_not_exist")
