"""Unit tests for the minimal physical-point MadGraph runner."""

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_physical_point_madgraph import (
    DEFAULT_PROC_DIR,
    generate_param_card_text,
    generate_run_card_text,
    run_single_physical_point_madgraph,
)


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
        "mh_input_GeV": 125.13,
        "mH_input_GeV": 150.0,
        "g_hH2H2_GeV": 63.59142520075966,
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
