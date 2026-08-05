"""Contract tests for the committed R9 artifacts.

These assert the *claims* the artifacts make, not just their shape: the scan
budget, the coordinate-selection evidence, the absence of an invented ATLAS
threshold, and the consistency of the manifest.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"

pytestmark = pytest.mark.skipif(
    not (OUTDIR / "result_summary.json").exists(), reason="R9 results not built"
)


def load(name):
    return json.loads((OUTDIR / name).read_text())


def rows(name):
    with open(OUTDIR / name, newline="") as fh:
        return list(csv.DictReader(fh))


def test_result_summary_is_valid_json_and_complete():
    s = load("result_summary.json")
    assert s["status"] == "COMPLETE"
    assert s["next_step"] in {
        "PRESENT_RESULT", "ONE_TARGETED_RECAST_REQUIRED", "THRESHOLD_NOT_MODEL_REACHABLE"
    }
    for key in ("baseline", "q1_sigma_scaling", "q2_q3_illustrative_thresholds",
                "q4_official_atlas_threshold", "q5_model_reachability",
                "q6_rate_limitation_cause", "interpretation", "additional_recast"):
        assert key in s, f"result_summary.json is missing {key}"


def test_scaling_exponent_is_two_and_justified():
    fit = load("madgraph_scaling_fit.json")
    assert fit["fitted_exponent_p"] == 2.0
    assert fit["quadratic_scaling"] == "PASS"
    assert fit["structural_verification"]["all_passed"] is True
    assert len(fit["structural_verification"]["checks"]) >= 7
    for check in fit["structural_verification"]["checks"]:
        assert check["passed"] is True, check["step"]
    # changing GHphiphi must be an overall normalisation and nothing else
    effects = fit["changing_GHphiphi_affects"]
    assert effects["overall_matrix_element_normalization"] is True
    assert not any(v for k, v in effects.items() if k != "overall_matrix_element_normalization")


def test_unexecuted_madgraph_rows_carry_no_invented_cross_sections():
    for row in rows("madgraph_coupling_scaling.csv"):
        if row["status"] == "NOT_EXECUTED_MADGRAPH_UNAVAILABLE_EGRESS_BLOCKED":
            assert row["sigma_pb"] == ""
            assert row["integration_error_pb"] == ""
            assert row["sigma_over_sigma_baseline"] == ""
            assert row["relative_residual"] == ""
            # the analytic prediction must still be present and non-empty
            assert float(row["analytic_sigma_pb"]) > 0.0


def test_thresholds_are_labelled_illustrative():
    table = rows("yield_thresholds.csv")
    assert [float(r["target_events"]) for r in table] == [1.0, 3.0, 5.0, 10.0]
    for row in table:
        assert row["interpretation"] == "ILLUSTRATIVE_RATE_SCALE_NOT_DISCOVERY_OR_EXCLUSION"


def test_atlas_threshold_invents_nothing():
    atlas = load("atlas_threshold.json")
    assert atlas["region_mapping"]["region_mapping_status"] == "UNAMBIGUOUS"
    if atlas["status"] == "OFFICIAL_THRESHOLD_MAPPING_UNRESOLVED":
        nt = atlas["numerical_threshold"]
        assert nt["observed_S95"] is None
        assert nt["expected_S95"] is None
        assert nt["model_independent_visible_sigma_limit_fb"] is None
        assert nt["model_independent_limit_tables_found"] == []
        assert atlas["required_kappa_g"] is None
        assert atlas["required_visible_sigma_fb"] is None
        assert nt["official_sources_attempted"]


def test_model_scan_respects_the_seven_point_budget_and_one_coordinate():
    scan = rows("model_reachability_scan.csv")
    meta = load("model_scan_provenance.json")
    assert len(scan) <= 7
    assert meta["scan_points"] == len(scan)
    assert meta["scan_budget"] == 7
    assert meta["varied_coordinate"].startswith("m12_sq")
    # exactly one coordinate varied: every fixed input is a scalar, not a list
    for value in meta["fixed_inputs"].values():
        assert not isinstance(value, list)


def test_coordinate_was_selected_by_measurement():
    coord = load("coordinate_selection.json")
    cands = coord["candidates"]
    # lambda6 must be shown not to move the coupling at all
    assert cands["lambda6"]["enters_g_hH2H2"] is False
    assert cands["lambda6"]["kappa_g_span_over_10_decades"] < 1e-9
    # lambda1 must be shown to be a re-parameterisation with a negligible span
    assert cands["lambda1_target"]["kappa_g_span_over_full_perturbative_window"] < 1e-6
    # m12_sq must be the one with a non-vanishing derivative
    assert cands["m12_sq"]["enters_g_hH2H2"] is True
    assert abs(cands["m12_sq"]["d_abs_g_d_m12sq_GeV_per_GeV2"]) > 0.0
    assert "m12_sq" in coord["selected_coordinate"]


def test_scan_never_inherits_the_baseline_br_or_lifetime():
    scan = rows("model_reachability_scan.csv")
    brs = {row["BR_bb"] for row in scan if row.get("BR_bb")}
    ctaus = {row["ctau_mm"] for row in scan if row.get("ctau_mm")}
    assert len(brs) == len(scan), "every point must carry its own BR"
    assert len(ctaus) == len(scan), "every point must carry its own ctau"


def test_theory_invalid_points_are_not_presented_as_physics():
    for row in rows("model_reachability_scan.csv"):
        if row["theory_ok_v1"] != "1":
            assert row["yield_status"] == "THEORY_INVALID_DERIVED_OBSERVABLES_NOT_PHYSICAL"


def test_baseline_gate_passed_for_the_rebuilt_evaluator():
    meta = load("model_scan_provenance.json")
    for name, entry in meta["baseline_gate"].items():
        assert entry["relative_difference"] <= 1e-14, name


def test_recomputation_gate_passes():
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "r9_recompute_check.py")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_artifact_manifest_verifies():
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "verify_r9_artifacts.py")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_figures_exist_and_are_manifested():
    manifest = load("artifact_manifest.json")["files"]
    for name in ("expected_events_vs_kappa_g.png", "model_reachability_vs_threshold.png"):
        path = OUTDIR / name
        assert path.exists()
        assert path.stat().st_size > 10_000
        assert str(path.relative_to(REPO_ROOT)) in manifest


def test_reports_are_manifested():
    manifest = load("artifact_manifest.json")["files"]
    for rel in ("docs/R9_H2_SENSITIVITY_THRESHOLD_RESULT.md",
                "docs/R9_PRESENTATION_INSERT_ES.md"):
        assert (REPO_ROOT / rel).exists()
        assert rel in manifest


def test_spanish_insert_has_at_most_three_slides():
    text = (REPO_ROOT / "docs" / "R9_PRESENTATION_INSERT_ES.md").read_text()
    slides = [line for line in text.splitlines() if line.startswith("## ")]
    assert 1 <= len(slides) <= 3, f"expected at most 3 slides, found {len(slides)}"


def test_ingest_script_fits_p_equals_two_on_a_synthetic_quadratic_sample(tmp_path):
    """The ingest path must recover p = 2 from ideal quadratic input."""
    sigma0 = 0.000230291167568
    csv_path = tmp_path / "measured.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["kappa_g", "sigma_pb", "integration_error_pb", "log"])
        for kappa in (0.5, 1.0, 2.0, 4.0):
            sigma = sigma0 * kappa**2
            writer.writerow([kappa, f"{sigma:.17e}", f"{sigma * 3e-3:.17e}", ""])

    work = tmp_path / "out"
    work.mkdir()
    for name in ("madgraph_coupling_scaling.csv", "madgraph_scaling_fit.json"):
        (work / name).write_bytes((OUTDIR / name).read_bytes())

    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "r9_ingest_madgraph_scaling.py"),
         "--results", str(csv_path), "--outdir", str(work)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    fit = json.loads((work / "madgraph_scaling_fit.json").read_text())["empirical_fit"]
    assert fit["fitted_exponent_p"] == pytest.approx(2.0, abs=1e-9)
    assert fit["quadratic_scaling"] == "PASS"
    assert fit["all_residuals_compatible"] is True
    # and the committed artifacts must be untouched by the tmp-dir run
    assert "NOT_EXECUTED" in json.loads(
        (OUTDIR / "madgraph_scaling_fit.json").read_text()
    )["empirical_fit_status"]
