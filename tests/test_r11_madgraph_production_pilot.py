import csv
import hashlib
import json
import math
import shutil
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
    calculate_g2_prediction,
    calculate_relative_residual,
    compare_histograms,
    compute_histogram,
    extract_madgraph_xsec,
    fmt_point_dir,
    parse_lhe_events,
)


def test_production_mode_selector_contract():
    """Phase 1 Gate: accepted/rejected selector values and no silent fallback."""
    from scripts.r10_production_scan import parse_args

    # Valid values
    args_fact = parse_args(["--production-mode", "factorized"])
    assert args_fact.production_evaluation_mode == "factorized"

    # Invalid value
    with pytest.raises(SystemExit):
        parse_args(["--production-mode", "invalid_mode"])

    # Missing file for madgraph mode raises ValueError
    with pytest.raises(ValueError, match="requires an explicit --madgraph-results"):
        parse_args(["--production-mode", "madgraph"])

    with pytest.raises(FileNotFoundError):
        parse_args(["--production-mode", "madgraph", "--madgraph-results", "non_existent.csv"])


def test_factorized_mode_numerical_regression(tmp_path):
    """Phase 2 Gate: Factorized mode reproduces exact baseline results."""
    from scripts.r10_production_scan import main as prod_main
    from scripts.r10_build_effective_grid import main as grid_main


    # Copy efficiency_vs_ctau to tmp_path
    shutil_copy = True
    eff_src = R10_OUT_DIR / "efficiency_vs_ctau.csv"
    eff_dst = tmp_path / "efficiency_vs_ctau.csv"
    eff_dst.write_bytes(eff_src.read_bytes())

    # Run in factorized mode
    prod_main(["--production-mode", "factorized", "--out-dir", str(tmp_path)])
    grid_main(["--out-dir", str(tmp_path)])

    # Check 360 points generated
    with open(tmp_path / "effective_grid.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 360

    # Baseline anchor check: g = 63.59142520075966, ctau = 4.326221529733112, BR = 0.7567374858085787
    anchor_rows = [
        r for r in rows
        if abs(float(r["g_hH2H2_GeV"]) - 63.59142520075966) < 1e-4
        and abs(float(r["ctau_mm"]) - 4.326221529733112) < 1e-4
        and abs(float(r["BR_H2_to_bb"]) - 0.7567374858085787) < 1e-4
    ]
    assert len(anchor_rows) == 1
    anchor = anchor_rows[0]
    assert abs(float(anchor["sigma_production_pb"]) - SIGMA0_PB) < 1e-12
    assert anchor["production_evaluation_mode"] == "factorized"


def test_grid_builder_consumes_selected_sigma(tmp_path):
    """Phase 2 Gate: Synthetic MadGraph result updates grid normalization."""
    from scripts.r10_production_scan import main as prod_main
    from scripts.r10_build_effective_grid import main as grid_main


    # Copy efficiency_vs_ctau to tmp_path
    eff_src = R10_OUT_DIR / "efficiency_vs_ctau.csv"
    (tmp_path / "efficiency_vs_ctau.csv").write_bytes(eff_src.read_bytes())

    # Create synthetic madgraph_results.csv with modified sigma
    synthetic_csv = tmp_path / "synthetic_madgraph.csv"
    fieldnames = [
        "point_id", "g_hH2H2_GeV", "g_effective_GeV", "GHphiphi_GeV", "seed",
        "sigma_madgraph_pb", "integration_error_pb", "sigma_g2_prediction_pb",
        "relative_residual", "lhe_path", "lhe_sha256", "banner_sha256",
        "param_card_sha256", "status", "log_path", "log_sha256"
    ]
    synthetic_sigma = 0.0005  # double the baseline
    rows = [{
        "point_id": "mg_synthetic",
        "g_hH2H2_GeV": f"{G0_GEV:.16g}",
        "g_effective_GeV": f"{G0_GEV:.16g}",
        "GHphiphi_GeV": f"{-G0_GEV:.16g}",
        "seed": "1101",
        "sigma_madgraph_pb": f"{synthetic_sigma:.16e}",
        "integration_error_pb": "1e-6",
        "sigma_g2_prediction_pb": f"{SIGMA0_PB:.16e}",
        "relative_residual": "1.0",
        "lhe_path": "", "lhe_sha256": "", "banner_sha256": "", "param_card_sha256": "",
        "status": "MADGRAPH_DIRECT_RUN", "log_path": "", "log_sha256": ""
    }]
    with open(synthetic_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    prod_main(["--production-mode", "madgraph", "--madgraph-results", str(synthetic_csv), "--out-dir", str(tmp_path)])
    grid_main(["--out-dir", str(tmp_path)])

    with open(tmp_path / "effective_grid.csv", newline="", encoding="utf-8") as fh:
        grid_rows = list(csv.DictReader(fh))

    # Verify g0 rows consume synthetic_sigma instead of structural prediction
    g0_rows = [r for r in grid_rows if abs(float(r["g_hH2H2_GeV"]) - G0_GEV) < 1e-4]
    for r in g0_rows:
        assert abs(float(r["sigma_production_pb"]) - synthetic_sigma) < 1e-12
        assert r["production_evaluation_mode"] == "madgraph"


def test_param_cards_and_effective_couplings():
    """Phase 3 Gate: Cards alter only FRBlock 3 and GHphiphi_effective == -g_target."""
    summary_file = OUT_DIR / "pilot_summary.json"
    assert summary_file.exists()
    summary = json.loads(summary_file.read_text(encoding="utf-8"))

    # Check distinct seeds
    seeds = [p["seed"] for p in summary["points"]]
    assert len(seeds) == len(set(seeds)) == 3

    for p in summary["points"]:
        g_target = p["g_target_GeV"]
        gh_target = p["GHphiphi_GeV"]
        assert abs(gh_target - (-g_target)) < 1e-10
        assert abs(p["g_effective_GeV"] - g_target) < 1e-10

        # Check param card contents
        pt_dir_name = fmt_point_dir(g_target)
        param_card = OUT_DIR / pt_dir_name / "param_card.dat"
        assert param_card.exists()
        text = param_card.read_text(encoding="utf-8")
        assert "Block frblock" in text or "Block FRBlock" in text
        # FRBlock 2 preserved
        assert "4.326222e-03" in text or "4.32622152973311191e-03" in text


def test_lhe_event_counts_and_particles():
    """Phase 4 Gate: 1000 complete events per LHE, 2 stable H2 PDG 9000006 per event."""
    summary = json.loads((OUT_DIR / "pilot_summary.json").read_text(encoding="utf-8"))

    for p in summary["points"]:
        lhe_path = REPO_ROOT / p["lhe_path"]
        assert lhe_path.exists()
        events = parse_lhe_events(lhe_path)
        assert len(events) == 1000

        for ev in events:
            h2 = ev["h2_particles"]
            assert len(h2) == 2
            for particle in h2:
                assert particle["pdg"] == 9000006
                assert particle["status"] == 1
                assert abs(particle["m"] - 150.0) < 1.0


def test_quadratic_residual_bounds():
    """Phase 4 Gate: relative residual |sigma_mg / sigma_pred - 1| < 0.01."""
    summary = json.loads((OUT_DIR / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["max_cross_section_relative_residual"] < 0.005  # < 0.5%


def test_histogram_normalization_closure():
    """Phase 5 Gate: Normalized histogram counts sum to 1.0."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    edges = [0.0, 25.0, 50.0, 75.0]
    hist = compute_histogram(values, edges)
    assert abs(sum(hist["normalized_counts"]) - 1.0) < 1e-12

    # Compare self
    cmp_self = compare_histograms(hist["normalized_counts"], hist["normalized_counts"])
    assert cmp_self["max_abs_diff"] == 0.0
    assert cmp_self["ks_stat"] == 0.0
    assert cmp_self["chi2_stat"] == 0.0


def test_manifest_integrity():
    """Phase 7 Gate: Artifact manifest contains all files and valid SHA-256 digests."""
    manifest_path = OUT_DIR / "artifact_manifest.json"
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "hep_cross.r11.artifact_manifest.v1"
    assert payload["n_files"] > 0

    for rel_path, expected_hash in payload["artifacts"].items():
        if rel_path.endswith("artifact_manifest.json"):
            continue
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"Missing artifact: {rel_path}"
        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}"

