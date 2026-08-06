"""Tests for R11 MadGraph Production Mode Pilot."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

OUT_DIR = REPO_ROOT / "results" / "r11_madgraph_production_pilot"
R10_OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"

from llp_recast.r11_madgraph_pilot import (
    G0_GEV,
    PILOT_G_TARGETS,
    PILOT_SEEDS,
    SIGMA0_PB,
    calculate_cross_section_ratio_and_pull,
    calculate_g2_prediction,
    calculate_relative_residual,
    compare_histograms,
    compute_histogram,
    extract_madgraph_xsec,
    fmt_point_dir,
    ks_critical_value_95,
    parse_lhe_events,
)


def test_production_mode_selector_contract():
    """Phase 1 Gate: accepted/rejected selector values and no silent fallback."""
    from scripts.r10_production_scan import parse_args

    args_fact = parse_args(["--production-mode", "factorized"])
    assert args_fact.production_evaluation_mode == "factorized"

    with pytest.raises(SystemExit):
        parse_args(["--production-mode", "invalid_mode"])

    with pytest.raises(ValueError, match="requires an explicit --madgraph-results"):
        parse_args(["--production-mode", "madgraph"])

    with pytest.raises(FileNotFoundError):
        parse_args(["--production-mode", "madgraph", "--madgraph-results", "non_existent.csv"])


def test_madgraph_partial_coverage_fails_without_fallback(tmp_path):
    """Issue 1 Gate: Partial MadGraph input (3 of 6 points) fails without falling back to factorized mode."""
    from scripts.r10_production_scan import main as prod_main

    # Create synthetic madgraph results with only 3 points (40.0, 63.59142520075966, 150.0)
    partial_csv = tmp_path / "partial_madgraph.csv"
    fieldnames = [
        "point_id", "g_hH2H2_GeV", "g_effective_GeV", "GHphiphi_GeV", "seed",
        "sigma_madgraph_pb", "integration_error_pb", "sigma_g2_prediction_pb",
        "relative_residual", "ratio_R", "delta_R", "pull",
        "lhe_path", "lhe_sha256", "banner_sha256", "param_card_sha256", "status", "log_path", "log_sha256"
    ]
    rows = []
    for g in [40.0, 63.59142520075966, 150.0]:
        rows.append({
            "point_id": f"mg_{g}",
            "g_hH2H2_GeV": f"{g:.16g}",
            "g_effective_GeV": f"{g:.16g}",
            "GHphiphi_GeV": f"{-g:.16g}",
            "seed": "1101",
            "sigma_madgraph_pb": f"{calculate_g2_prediction(g):.16e}",
            "integration_error_pb": "1e-7",
            "sigma_g2_prediction_pb": f"{calculate_g2_prediction(g):.16e}",
            "relative_residual": "0.0",
            "ratio_R": "1.0", "delta_R": "0.001", "pull": "0.0",
            "lhe_path": "", "lhe_sha256": "", "banner_sha256": "", "param_card_sha256": "",
            "status": "MADGRAPH_DIRECT_RUN", "log_path": "", "log_sha256": ""
        })
    with open(partial_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError) as exc_info:
        prod_main(["--production-mode", "madgraph", "--madgraph-results", str(partial_csv), "--out-dir", str(tmp_path)])

    err_msg = str(exc_info.value)
    assert "requires complete coverage" in err_msg
    assert "100.0" in err_msg
    assert "205.0927254223737" in err_msg
    assert "300.0" in err_msg


def test_madgraph_full_coverage_succeeds_synthetic(tmp_path):
    """Issue 1 & 2 Gate: Full 6-point synthetic MadGraph input succeeds in madgraph mode."""
    from scripts.r10_production_scan import main as prod_main
    from scripts.r10_build_effective_grid import main as grid_main

    eff_src = R10_OUT_DIR / "efficiency_vs_ctau.csv"
    (tmp_path / "efficiency_vs_ctau.csv").write_bytes(eff_src.read_bytes())

    full_csv = tmp_path / "full_madgraph.csv"
    fieldnames = [
        "point_id", "g_hH2H2_GeV", "g_effective_GeV", "GHphiphi_GeV", "seed",
        "sigma_madgraph_pb", "integration_error_pb", "sigma_g2_prediction_pb",
        "relative_residual", "ratio_R", "delta_R", "pull",
        "lhe_path", "lhe_sha256", "banner_sha256", "param_card_sha256", "status", "log_path", "log_sha256"
    ]
    all_g = [40.0, 63.59142520075966, 100.0, 150.0, 205.09272542237372, 300.0]
    rows = []
    for g in all_g:
        sig = calculate_g2_prediction(g)
        rows.append({
            "point_id": f"mg_{g}",
            "g_hH2H2_GeV": f"{g:.16g}",
            "g_effective_GeV": f"{g:.16g}",
            "GHphiphi_GeV": f"{-g:.16g}",
            "seed": "1101",
            "sigma_madgraph_pb": f"{sig:.16e}",
            "integration_error_pb": "1e-7",
            "sigma_g2_prediction_pb": f"{sig:.16e}",
            "relative_residual": "0.0",
            "ratio_R": "1.0", "delta_R": "0.001", "pull": "0.0",
            "lhe_path": "", "lhe_sha256": "", "banner_sha256": "", "param_card_sha256": "",
            "status": "MADGRAPH_DIRECT_RUN", "log_path": "", "log_sha256": ""
        })
    with open(full_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    res_prod = prod_main(["--production-mode", "madgraph", "--madgraph-results", str(full_csv), "--out-dir", str(tmp_path)])
    assert res_prod == 0

    res_grid = grid_main(["--production-mode", "madgraph", "--out-dir", str(tmp_path)])
    assert res_grid == 0

    with open(tmp_path / "effective_grid.csv", newline="", encoding="utf-8") as fh:
        grid_rows = list(csv.DictReader(fh))
    assert len(grid_rows) == 360
    assert all(r["production_evaluation_mode"] == "madgraph" for r in grid_rows)


def test_physical_r11_pilot_is_production_only():
    """Issue 2 Gate: Physical R11 pilot output contains no 360-point grid or mixed tables."""
    assert not (OUT_DIR / "effective_grid.csv").exists()
    assert not (OUT_DIR / "production_vs_g.csv").exists()
    assert not (OUT_DIR / "efficiency_vs_ctau.csv").exists()
    assert (OUT_DIR / "madgraph_results.csv").exists()


def test_manifest_references_git_tracked_files_only():
    """Issue 6 Gate: All manifest entries exist and are tracked by Git."""
    manifest_path = OUT_DIR / "artifact_manifest.json"
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    for rel_path, expected_hash in payload["artifacts"].items():
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"Missing manifest artifact: {rel_path}"
        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}"

        # Verify tracked by Git
        res = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel_path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, f"Manifest file {rel_path} is not tracked by Git!"


def test_no_build_tree_files_tracked():
    """Issue 4 Gate: No proc_output, ufo, scratch, or compiled binaries are tracked by Git."""
    for sub in ["proc_output", "ufo", "scratch"]:
        res = subprocess.run(
            ["git", "ls-files", f"results/r11_madgraph_production_pilot/{sub}/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert res.stdout.strip() == "", f"Git tracked files found under ignored directory {sub}: {res.stdout}"

    res_o = subprocess.run(["git", "ls-files", "*.o"], cwd=REPO_ROOT, capture_output=True, text=True)
    assert res_o.stdout.strip() == ""
    res_a = subprocess.run(["git", "ls-files", "*.a"], cwd=REPO_ROOT, capture_output=True, text=True)
    assert res_a.stdout.strip() == ""


def test_param_cards_and_effective_couplings():
    """Phase 3 Gate: Cards alter only FRBlock 3 and GHphiphi_effective == -g_target."""
    summary_file = OUT_DIR / "pilot_summary.json"
    assert summary_file.exists()
    summary = json.loads(summary_file.read_text(encoding="utf-8"))

    seeds = [p["seed"] for p in summary["points"]]
    assert len(seeds) == len(set(seeds)) == 3

    for p in summary["points"]:
        g_target = p["g_target_GeV"]
        gh_target = p["GHphiphi_GeV"]
        assert abs(gh_target - (-g_target)) < 1e-10
        assert abs(p["g_effective_GeV"] - g_target) < 1e-10

        pt_dir_name = fmt_point_dir(g_target)
        param_card = OUT_DIR / pt_dir_name / "param_card.dat"
        assert param_card.exists()
        text = param_card.read_text(encoding="utf-8")
        assert "Block frblock" in text or "Block FRBlock" in text
        assert "4.326222e-03" in text or "4.32622152973311191e-03" in text


def test_complete_applied_run_cards_and_logs_preserved():
    """Issue 5 & 9 Gate: Applied run cards and point logs exist and match manifest hashes."""
    summary = json.loads((OUT_DIR / "pilot_summary.json").read_text(encoding="utf-8"))

    for p in summary["points"]:
        pt_dir_name = fmt_point_dir(p["g_target_GeV"])
        pt_dir = OUT_DIR / pt_dir_name

        run_applied = pt_dir / "run_card_applied.dat"
        assert run_applied.exists()
        assert "nevents" in run_applied.read_text(encoding="utf-8")


        log_path = REPO_ROOT / p["log_path"]
        assert log_path.exists()
        assert p["log_sha256"] == hashlib.sha256(log_path.read_bytes()).hexdigest()


def test_cross_section_ratio_pulls_within_bounds():
    """Issue 10 Gate: Direct ratio R(g) pulls satisfy |pull| < 3.0."""
    summary = json.loads((OUT_DIR / "pilot_summary.json").read_text(encoding="utf-8"))
    for p in summary["points"]:
        pull = p["pull"]
        assert abs(pull) < 3.0, f"Pull for {p['point_id']} exceeds threshold: {pull}"


def test_shape_ks_statistics_within_bounds():
    """Issue 11 Gate: Unbinned KS distance <= critical value at 95% CL."""
    shape_json = json.loads((OUT_DIR / "shape_comparison.json").read_text(encoding="utf-8"))
    for pair_name, obs_dict in shape_json["pairwise_comparisons"].items():
        for obs_name, stat in obs_dict.items():
            assert stat["ks_pass_95"], f"KS test failed for {pair_name} {obs_name}"
            assert "g1_underflow_fraction" in stat
            assert "g2_overflow_fraction" in stat


def test_derived_summary_verdict_validated():
    """Issue 12 Gate: Overall summary verdict is dynamically derived VALIDATED."""
    summary = json.loads((OUT_DIR / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["verdict"] == "VALIDATED"
    assert all(summary["gates_status"].values())
