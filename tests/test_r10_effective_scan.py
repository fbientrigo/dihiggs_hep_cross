"""Comprehensive Pytest test suite for R10 effective phenomenological scan."""

import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "r10_effective_scan.json"
OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"


@pytest.fixture(scope="module")
def config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def grid_rows():
    csv_path = OUT_DIR / "effective_grid.csv"
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def eff_rows():
    csv_path = OUT_DIR / "efficiency_vs_ctau.csv"
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_gamma_total_formula(config):
    hbar_c = config["hbar_c_GeV_mm"]
    ctau = 4.326221529733112
    width = hbar_c / ctau
    assert width == pytest.approx(4.56118529862185e-14, rel=1e-10)


def test_sigma_4b_formula():
    sigma_prod_pb = 0.000230291167568
    br_bb = 0.7567374858085787
    sigma_4b_fb = sigma_prod_pb * 1000.0 * (br_bb**2)
    assert sigma_4b_fb == pytest.approx(0.131876610738628, rel=1e-10)


def test_visible_sigma_formula():
    sigma_4b_fb = 0.131876610738628
    aeff = 0.01573386
    vis_sigma = sigma_4b_fb * aeff
    assert vis_sigma == pytest.approx(0.0020749281306360694, rel=1e-10)


def test_n_expected_formula():
    vis_sigma = 0.0020749281306360694
    lumi = 139.0
    n_exp = vis_sigma * lumi
    assert n_exp == pytest.approx(0.28841501015841364, rel=1e-10)


def test_n_over_s95_formula():
    n_exp = 0.28841501015841364
    s95 = 3.0
    assert n_exp / s95 == pytest.approx(0.09613833671947121, rel=1e-10)


def test_exact_preservation_of_baseline_anchor(grid_rows, config):
    anchor = config["baseline_anchor"]
    anchor_row = next(
        (
            r
            for r in grid_rows
            if abs(float(r["ctau_mm"]) - anchor["ctau_0_mm"]) < 1e-5
            and abs(float(r["g_hH2H2_GeV"]) - anchor["abs_g_0_GeV"]) < 1e-5
            and abs(float(r["BR_H2_to_bb"]) - anchor["BR_bb_0"]) < 1e-5
        ),
        None,
    )
    assert anchor_row is not None, "Baseline anchor point missing from effective grid!"

    assert float(anchor_row["sigma_production_pb"]) == pytest.approx(anchor["sigma_0_pb"], rel=1e-10)
    assert float(anchor_row["Trackless_Aeff"]) == pytest.approx(anchor["Trackless_Aeff_0"], rel=1e-6)
    assert float(anchor_row["visible_sigma_fb"]) == pytest.approx(anchor["visible_sigma_0_fb"], rel=1e-6)
    assert float(anchor_row["N_expected_139fb"]) == pytest.approx(anchor["N_expected_0"], rel=1e-6)
    assert anchor_row["above_observed_S95"] == "False"


def test_no_br_double_counting(eff_rows):
    for r in eff_rows:
        assert int(r["generated_events"]) == 2000
        aeff = float(r["Trackless_Aeff"])
        assert 0.0 <= aeff <= 1.0


def test_all_240_grid_points_present(grid_rows):
    assert len(grid_rows) == 240
    pids = {r["point_id"] for r in grid_rows}
    assert len(pids) == 240, "Point IDs in effective grid must be unique!"


def test_no_model_derived_interpretation_labels(grid_rows):
    for r in grid_rows:
        assert r["interpretation"] == "EFFECTIVE_PHENOMENOLOGICAL"
        assert "MODEL_DERIVED" not in r["interpretation"]
        assert "2HDM" not in r["interpretation"]


def test_blocker3_regression_counts_and_maximums(grid_rows, config):
    n_ge_1 = sum(1 for r in grid_rows if float(r["N_expected_139fb"]) >= 1.0)
    n_ge_3 = sum(1 for r in grid_rows if float(r["N_expected_139fb"]) >= 3.0)
    max_N = max(float(r["N_expected_139fb"]) for r in grid_rows)

    assert n_ge_1 == 54, f"Expected 54 points with N>=1, got {n_ge_1}"
    assert n_ge_3 == 23, f"Expected 23 points with N>=3, got {n_ge_3}"
    assert max_N == pytest.approx(13.269202801224393, rel=1e-8)

    # Structural cross section at g = 150 GeV
    g_0 = config["baseline_anchor"]["abs_g_0_GeV"]
    sigma_0 = config["baseline_anchor"]["sigma_0_pb"]
    sigma_g150 = sigma_0 * (150.0 / g_0) ** 2
    assert sigma_g150 == pytest.approx(0.001281334981474172, rel=1e-8)


def test_no_stale_summary_numbers_in_artifacts():
    stale_tokens = [
        "42 points",
        "21 points",
        "25.8",
        "18.6",
        "0.01280 pb",
    ]
    files_to_check = [
        REPO_ROOT / "docs" / "R10_EFFECTIVE_CTAU_G_BR_RESULT.md",
        REPO_ROOT / "docs" / "R10_PRESENTATION_INSERT_ES.md",
        OUT_DIR / "result_summary.json",
    ]
    for file_path in files_to_check:
        assert file_path.exists(), f"Missing file: {file_path}"
        text = file_path.read_text(encoding="utf-8")
        for token in stale_tokens:
            assert token not in text, f"Stale incorrect number '{token}' found in {file_path}"


def test_required_figures_exist():
    required_figures = [
        OUT_DIR / "efficiency_vs_ctau.png",
        OUT_DIR / "nexpected_3d_ctau_g_br.png",
        OUT_DIR / "nexpected_ctau_vs_g_br_baseline.png",
        OUT_DIR / "nexpected_g_vs_br_ctau_baseline.png",
        OUT_DIR / "nexpected_ctau_vs_br_g_atlas.png",
        OUT_DIR / "nexpected_3d_interactive.html",
    ]
    for fig_path in required_figures:
        assert fig_path.exists(), f"Missing required figure: {fig_path}"
        assert fig_path.stat().st_size > 0, f"Figure file is empty: {fig_path}"


def test_manifest_hashes_verify_and_clean_checkout():
    manifest_path = OUT_DIR / "artifact_manifest.json"
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "hep_cross.r10.artifact_manifest.v1"

    for rel_path, expected_hash in payload["artifacts"].items():
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"Clean checkout assertion failed: missing file {rel_path}"
        digest = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert digest == expected_hash, f"Hash mismatch for {rel_path}"


def test_verifier_default_mode_does_not_modify_manifest():
    manifest_path = OUT_DIR / "artifact_manifest.json"
    mtime_before = manifest_path.stat().st_mtime_ns
    proc = subprocess.run(
        [sys.executable, "scripts/verify_r10_effective_scan.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    mtime_after = manifest_path.stat().st_mtime_ns
    assert proc.returncode == 0, f"Verifier failed: {proc.stderr}\n{proc.stdout}"
    assert mtime_before == mtime_after, "Verifier in default mode modified artifact_manifest.json!"


def test_recomputation_gate_passes():
    proc = subprocess.run(
        [sys.executable, "scripts/r10_recompute_grid.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"r10_recompute_grid failed: {proc.stderr}\n{proc.stdout}"
    assert "PASS" in proc.stdout
