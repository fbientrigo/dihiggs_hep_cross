"""Unit tests for the minimal physical-point MadGraph runner."""

import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_physical_point_madgraph import (
    DEFAULT_PROC_DIR,
    generate_param_card_text,
    generate_run_card_text,
    run_single_physical_point_madgraph,
)
import run_physical_point_madgraph as mg_runner


def test_param_card_generation_substitutes_all_blocks():
    template = """Block mass
    25 1.250000e+02 # MH
    9000006 2.000000e+02 # Mh2
Block frblock
    2 1.000000e-01 # ctauh2
    3 -1.000000e+01 # GHphiphi
Block decay
    9000006 1.000000e-13 # Wh2
"""
    rendered = generate_param_card_text(
        template,
        # HISTORICAL 150 GeV benchmark: pinned to the superseded mh=125.13 it was
        # validated at, not the canonical 125.20. mh_GeV now has no default, so
        # this value is necessarily explicit.
        mh_GeV=125.13,
        mH2_GeV=150.0,
        g_hH2H2_GeV=63.5914252,
        ctau_mm=4.3262215,
        total_width_GeV=4.561185e-14,
    )
    assert "25 1.251300e+02" in rendered
    assert "9000006 1.500000e+02" in rendered
    assert "2 4.326221e-03" in rendered  # in meters
    assert "3 -6.359143e+01" in rendered  # GHphiphi = -g
    assert "9000006 4.561185e-14" in rendered


def test_run_card_generation():
    text = generate_run_card_text(nevents=5000, seed=101, ebeam_GeV=6500.0)
    assert "5000 = nevents" in text
    assert "101 = iseed" in text
    assert "6500.0 = ebeam1" in text
    assert "6500.0 = ebeam2" in text
    assert "nn23lo1 = pdlabel" in text
    assert "230000 = lhaid" in text


@pytest.mark.skipif(not DEFAULT_PROC_DIR.exists(), reason="MadGraph proc_output required")
def test_benchmark_closure_execution(tmp_path):
    point = {
        "point_id": "H2scan_mH150_tb300000",
        # HISTORICAL benchmark convention; see scripts/r9_run_model_scan.py.
        "mh_input_GeV": 125.13,
        "historical_replay": True,
        "mass_convention_id": "mh_125p13_high_mass_v1",
        "mH_input_GeV": 150.0,
        "g_hH2H2_GeV": 63.59142520075966,
        "tan_beta": 300000.0,
        "lambda6_input": 1e-10,
        "M2_input_GeV2": 22499.9999995,
        "ctau_mm": 4.326221529733112,
        "br_bb": 0.7567374858085787,
        "total_width_GeV": 4.56118529862185e-14,
    }
    res = run_single_physical_point_madgraph(
        point,
        proc_dir=DEFAULT_PROC_DIR,
        cards_out_dir=tmp_path / "cards",
        nevents=10000,
        seeds=[101, 107],
    )
    assert res["madgraph_status"] == "VALID"
    sigma_fb = res["sigma_production_fb"]
    assert math.isclose(sigma_fb, 0.230291, rel_tol=0.03)
    assert res["sigma_production_unc_fb"] > 0.0
    assert (tmp_path / "cards" / "H2scan_mH150_tb300000_param_card.dat").exists()


# --- mass-convention contract ------------------------------------------------

def test_resolver_reads_m_h_from_the_point():
    """m_h_GeV / mh_input_GeV / mh, newest name first."""
    from run_physical_point_madgraph import resolve_m_h_GeV

    assert resolve_m_h_GeV({"m_h_GeV": "125.20"}) == 125.20
    assert resolve_m_h_GeV({"mh_input_GeV": 125.13}) == 125.13
    assert resolve_m_h_GeV({"mh": 125.09}) == 125.09
    assert resolve_m_h_GeV({"m_h_GeV": "125.20", "mh": 125.20}) == 125.20
    with pytest.raises(ValueError, match="aliases.*disagree"):
        resolve_m_h_GeV({"m_h_GeV": "125.20", "mh": 125.09})


def test_resolver_refuses_to_default_a_missing_mass():
    """Regression: this used to silently fall back to a hard-coded 125.13, which
    rewrote a point produced under a different convention to this repo's
    assumption. The convention travels on the point; a point without it is a
    contract violation, not a defaulting case."""
    from run_physical_point_madgraph import resolve_m_h_GeV

    with pytest.raises(KeyError) as excinfo:
        resolve_m_h_GeV({"point_id": "p_no_mass", "mH_input_GeV": 150.0})
    assert "p_no_mass" in str(excinfo.value)


def test_param_card_mass_25_comes_from_the_point():
    """The SLHA Block MASS entry 25 must track the point, not a module default."""
    from run_physical_point_madgraph import generate_param_card_text

    template = "Block MASS\n    25 1.000000e+02 # MH\n    9000006 2.000000e+02 # Mh2\n"
    assert "25 1.252000e+02" in generate_param_card_text(template, mh_GeV=125.20)
    assert "25 1.251300e+02" in generate_param_card_text(template, mh_GeV=125.13)


def test_param_card_does_not_clobber_decay_25_width():
    """Regression: the unanchored MASS-block substitution for pdgid 25 used to
    also match the unrelated "DECAY  25  <width>" line (both start with the
    token "25"), silently overwriting the SM Higgs total width with the SM
    Higgs mass value. Confirmed in real pre-fix output:
    results/pilot_cards/*_param_card.dat contains "DECAY  25 1.251300e+02 # WH"
    -- 125.13 GeV is not a valid decay width. Two campaign scripts
    (mission_runs/20260825_h2_event_yields_v1/scripts/run_200gev_pilot.py and
    mission_runs/20260826_h2_table_v2_requalification/work/run_madgraph_v2.py)
    had to monkeypatch this function externally to restore the value; this
    test guards the upstream fix so neither workaround is needed again."""
    from run_physical_point_madgraph import generate_param_card_text

    template = (
        "Block MASS\n"
        "    25 1.000000e+02 # MH\n"
        "    9000006 2.000000e+02 # Mh2\n"
        "DECAY  25  4.070000e-03 # WH\n"
        "DECAY  9000006  1.000000e-13 # Wh2\n"
    )
    rendered = generate_param_card_text(
        template, mh_GeV=125.20, mH2_GeV=150.0, total_width_GeV=1.0e-13
    )
    assert "25 1.252000e+02" in rendered  # MASS block: updated to the point's mh
    assert "DECAY  25  4.070000e-03" in rendered  # decay block: untouched


def test_v3_signed_coupling_controls_ghphiphi():
    from run_physical_point_madgraph import resolve_ghphiphi_GeV

    point = {
        "physics_conventions_schema": "physics_conventions_v3",
        "physics_conventions_commit": "087ba246e9a9fa34b16249b52629a62703893b5c",
        "physics_conventions_sha256": "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6",
        "coupling_prescription": "physical_2HDM",
        "mass_convention_id": "mh_125p20_active_2026", "m_h_GeV_text": "125.20",
        "g_physical_hphiphi_GeV": 5.0, "g_physical_hphiphi_abs_GeV": 5.0, "g_hH2H2_GeV": 5.0,
        "two_hdmc_hphiphi_real_GeV": 0.0, "two_hdmc_hphiphi_imag_GeV": -5.0,
    }
    assert resolve_ghphiphi_GeV(point) == -5.0
    point.update(g_physical_hphiphi_GeV=-5.0, two_hdmc_hphiphi_imag_GeV=5.0)
    assert resolve_ghphiphi_GeV(point) == 5.0


def test_new_production_rejects_unlabelled_magnitude_only_points():
    from run_physical_point_madgraph import resolve_ghphiphi_GeV

    with pytest.raises(ValueError, match="requires complete"):
        resolve_ghphiphi_GeV({"g_hH2H2_GeV": 5.0, "mh_input_GeV": 125.20})


def v3_point():
    return {
        "point_id": "v3-entrypoint",
        "physics_conventions_schema": "physics_conventions_v3",
        "physics_conventions_commit": "087ba246e9a9fa34b16249b52629a62703893b5c",
        "physics_conventions_sha256": "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6",
        "coupling_prescription": "physical_2HDM",
        "mass_convention_id": "mh_125p20_active_2026",
        "m_h_GeV_text": "125.20",
        "m_h_GeV": "125.20",
        "m_phi_GeV": 175.0,
        "tan_beta": 1000.0,
        "lambda6_input": 0.01,
        "M2_input_GeV2": 22500.0,
        "g_physical_hphiphi_GeV": 5.0,
        "g_physical_hphiphi_abs_GeV": 5.0,
        "g_hH2H2_GeV": 5.0,
        "two_hdmc_hphiphi_real_GeV": 0.0,
        "two_hdmc_hphiphi_imag_GeV": -5.0,
        "ctau_mm": 4.93317451,
        "br_bb": 0.7,
        "total_width_GeV": 4.0e-14,
    }


def test_v3_entrypoint_generates_card_and_runs_with_mock_madgraph(tmp_path, monkeypatch):
    proc_dir = tmp_path / "proc"
    cards = proc_dir / "Cards"
    cards.mkdir(parents=True)
    (cards / "param_card_default.dat").write_text(
        "Block MASS\n 25 125.0 # MH\n 9000006 150.0 # Mh2\n"
        "Block frblock\n 2 0.1 # ctauh2\n 3 -5.0 # GHphiphi\n"
        "DECAY 9000006 1e-13\n"
    )

    def fake_madgraph(command, *, cwd, **kwargs):
        run_tag = command[-1]
        run_dir = Path(cwd) / "Events" / run_tag
        run_dir.mkdir(parents=True)
        (run_dir / f"{run_tag}_tag_1_banner.txt").write_text(
            "# Integrated weight (pb) : 2.0e-3\n"
        )
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(mg_runner.subprocess, "run", fake_madgraph)
    result = mg_runner.run_single_physical_point_madgraph(
        v3_point(), proc_dir=proc_dir, cards_out_dir=tmp_path / "out", seeds=[101]
    )

    assert result["madgraph_status"] == "VALID"
    assert result["mH2_GeV"] == 175.0
    assert result["GHphiphi_GeV"] == -5.0
    card = (tmp_path / "out" / "v3-entrypoint_param_card.dat").read_text()
    assert "25 1.252000e+02" in card
    assert "9000006 1.750000e+02" in card
    assert "9000006 4.000000e-14" in card


@pytest.mark.parametrize(
    "missing", ["m_phi_GeV", "ctau_mm", "total_width_GeV", "tan_beta", "lambda6_input", "M2_input_GeV2"]
)
def test_v3_entrypoint_rejects_missing_inputs_before_madgraph(missing, tmp_path):
    point = v3_point()
    del point[missing]
    with pytest.raises(KeyError):
        run_single_physical_point_madgraph(point, proc_dir=tmp_path)


@pytest.mark.parametrize("field", ["m_h_GeV", "m_phi_GeV", "ctau_mm", "total_width_GeV", "tan_beta"])
def test_v3_entrypoint_rejects_nonfinite_inputs_before_madgraph(field, tmp_path):
    point = v3_point()
    point[field] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        run_single_physical_point_madgraph(point, proc_dir=tmp_path)


def test_v3_entrypoint_rejects_conflicting_mass_aliases(tmp_path):
    point = v3_point()
    point["mH_input_GeV"] = 150.0
    with pytest.raises(ValueError, match="aliases.*disagree"):
        run_single_physical_point_madgraph(point, proc_dir=tmp_path)
