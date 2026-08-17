"""test_mass_jet_campaign.py -- Unit tests for the overnight mass-vs-jet campaign runner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_mass_jet_control_campaign import (
    ACTIVE_MH_CONVENTION_GEV,
    ALL_MASSES,
    CANONICAL_POINTS,
    CONTROL_CTAU_MM,
    CORE_MASSES,
    build_final_reports,
    combine_point_shards,
    format_cmnd_card_text,
    format_param_card_text,
    format_run_card_text,
    update_heartbeat,
)


def test_canonical_points_completeness():
    """Verify all 8 masses are present and carry valid physics coordinates."""
    expected_masses = [150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, 800.0]
    assert sorted(CANONICAL_POINTS.keys()) == expected_masses
    for m in expected_masses:
        pt = CANONICAL_POINTS[m]
        assert pt["mH_GeV"] == m
        assert pt["point_id"].startswith("point_")
        assert pt["tan_beta"] == 300000.0
        assert pt["sin_beta_minus_alpha"] == 1.0
        assert pt["yukawa_type"] == 1
        assert pt["g_hH2H2_GeV"] > 0
        assert pt["ctau_mm"] > 0
        assert pt["total_width_GeV"] > 0


def test_param_card_generation(tmp_path: Path):
    """Verify param_card text replaces masses, widths, couplings accurately."""
    template = """Block mass
    25 1.250000e+02 # MH
    9000006 1.500000e+02 # Mh2
Block frblock
    2 4.326222e-03 # ctauh2
    3 -6.359143e+01 # GHphiphi
DECAY 9000006 4.561185e-14 # h2
"""
    formatted = format_param_card_text(
        template_text=template,
        mh_GeV=ACTIVE_MH_CONVENTION_GEV,
        mH2_GeV=350.0,
        g_hH2H2_GeV=63.6625935,
        ctau_mm=CONTROL_CTAU_MM,
    )
    assert "1.252000e+02" in formatted
    assert "3.500000e+02" in formatted
    assert "3.000000e-02" in formatted
    assert "-6.366259e+01" in formatted


def test_run_card_generation():
    """Verify run_card text specifies events, seeds, PDF."""
    rc = format_run_card_text(nevents=2000, seed=105)
    assert "2000 = nevents" in rc
    assert "105 = iseed" in rc
    assert "230000 = lhaid" in rc


def test_cmnd_card_generation():
    """Verify Pythia8 card contains forced bb and fixed ctau."""
    cmnd = format_cmnd_card_text(
        nevents=2000,
        seed=81005,
        mH2_GeV=500.0,
        ctau_mm=30.0,
        relabelled_lhe_rel_path="data/relabelled.lhe.gz",
        force_bb=True,
    )
    assert "Main:numberOfEvents = 2000" in cmnd
    assert "Random:seed = 81005" in cmnd
    assert "35:m0 = 500.0" in cmnd
    assert "35:tau0 = 30.0000" in cmnd
    assert "35:onIfMatch = 5 -5" in cmnd
    assert "Recast:llpTau0 = 30.0000" in cmnd


def test_heartbeat_update(tmp_path: Path):
    """Verify heartbeat writes valid JSON with timestamp and pid."""
    hb_file = tmp_path / "heartbeat.json"
    update_heartbeat(
        hb_file,
        campaign_id="test_camp",
        stage="TEST_STAGE",
        mass=250.0,
        shard=1,
        attempt=1,
        action="Testing heartbeat",
    )
    assert hb_file.is_file()
    data = json.loads(hb_file.read_text())
    assert data["campaign_id"] == "test_camp"
    assert data["current_mass_GeV"] == 250.0
    assert data["current_shard"] == 1
    assert data["current_stage"] == "TEST_STAGE"


def test_combine_point_shards(tmp_path: Path):
    """Verify shard aggregation sums event counts and computes efficiencies."""
    shards_data = [
        {
            "status": "COMPLETE",
            "mH_GeV": 250.0,
            "shard_index": 0,
            "n_events": 2000,
            "ctau_mm": 30.0,
            "force_bb": True,
            "trackless_acc": 100,
            "trackless_acc_x_eff": 75.0,
            "trackless_cutflow": {
                "jet_selection_pct": 140, "fiducial_pct": 140, "r_vertex_gt_4mm_pct": 135,
                "track_d0_gt_2mm_pct": 130, "selected_decay_products_ge5_pct": 120,
                "invariant_mass_gt_10gev_pct": 110,
            },
            "highpt_acc": 10,
            "highpt_acc_x_eff": 8.0,
            "highpt_cutflow": {
                "jet_selection_pct": 15, "fiducial_pct": 15, "r_vertex_gt_4mm_pct": 14,
                "track_d0_gt_2mm_pct": 14, "selected_decay_products_ge5_pct": 12,
                "invariant_mass_gt_10gev_pct": 11,
            },
            "geometry": {
                "mean_leading_jet_pt_GeV": 45.0,
                "mean_n_jets_pt20": 2.5,
                "mean_rxy_mm": 28.0,
                "mean_l3d_mm": 40.0,
                "frac_rxy_gt_4mm": 0.88,
            },
        },
        {
            "status": "COMPLETE",
            "mH_GeV": 250.0,
            "shard_index": 1,
            "n_events": 2000,
            "ctau_mm": 30.0,
            "force_bb": True,
            "trackless_acc": 110,
            "trackless_acc_x_eff": 85.0,
            "trackless_cutflow": {
                "jet_selection_pct": 160, "fiducial_pct": 160, "r_vertex_gt_4mm_pct": 155,
                "track_d0_gt_2mm_pct": 150, "selected_decay_products_ge5_pct": 140,
                "invariant_mass_gt_10gev_pct": 130,
            },
            "highpt_acc": 12,
            "highpt_acc_x_eff": 10.0,
            "highpt_cutflow": {
                "jet_selection_pct": 18, "fiducial_pct": 18, "r_vertex_gt_4mm_pct": 16,
                "track_d0_gt_2mm_pct": 16, "selected_decay_products_ge5_pct": 14,
                "invariant_mass_gt_10gev_pct": 13,
            },
            "geometry": {
                "mean_leading_jet_pt_GeV": 47.0,
                "mean_n_jets_pt20": 2.6,
                "mean_rxy_mm": 29.0,
                "mean_l3d_mm": 42.0,
                "frac_rxy_gt_4mm": 0.90,
            },
        },
    ]

    pt_sum = combine_point_shards(250.0, tmp_path, shards_data)
    assert pt_sum["total_events"] == 4000
    assert pt_sum["trackless"]["acc_total"] == 210
    assert pt_sum["trackless"]["acc_x_eff_total"] == 160.0
    assert pt_sum["trackless"]["Trackless_Aeff"] == 160.0 / 4000
    assert pt_sum["trackless"]["cutflow"]["jet_selection_pct"] == 300
    assert pt_sum["trackless"]["incremental_efficiencies"]["jet_selection_eff"] == 300 / 4000


def test_build_final_reports(tmp_path: Path):
    """Verify summary JSON, CSV, and markdown tables are correctly constructed."""
    dummy_summary = [
        {
            "mH_GeV": 150.0,
            "point_id": "point_98c841e915d3605a",
            "total_events": 2000,
            "trackless": {
                "acc_total": 40,
                "Trackless_Aeff": 0.0157,
                "cutflow": {
                    "jet_selection_pct": 48,
                    "fiducial_pct": 48,
                    "r_vertex_gt_4mm_pct": 46,
                },
                "incremental_efficiencies": {
                    "jet_selection_eff": 0.024,
                    "fiducial_given_jet": 1.0,
                    "r_vertex_gt4_given_fid": 0.958,
                    "track_d0_gt2_given_r": 0.95,
                    "ntracks_ge5_given_d0": 0.92,
                    "mass_gt10_given_ntrk": 0.91,
                },
            },
            "highpt": {
                "acc_total": 5,
                "HighPt_Aeff": 0.002,
                "cutflow": {"jet_selection_pct": 8},
            },
            "geometry_aggregates": {
                "mean_leading_jet_pt_GeV": 32.5,
                "mean_n_jets_pt20": 1.8,
                "mean_rxy_mm": 25.4,
                "frac_rxy_gt_4mm": 0.85,
            },
        }
    ]
    build_final_reports("test_camp", tmp_path, dummy_summary, CANONICAL_POINTS, "completed")
    assert (tmp_path / "campaign_summary.json").is_file()
    assert (tmp_path / "campaign_summary.csv").is_file()
    assert (tmp_path / "campaign_summary.md").is_file()
    md_text = (tmp_path / "campaign_summary.md").read_text()
    assert "CAMPAIGN STATUS" in md_text
    assert "150" in md_text
