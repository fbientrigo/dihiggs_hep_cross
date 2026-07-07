"""End-to-end smoke test for the full 2HDMC-to-diphoton pipeline.

Runs a synthetic 2HDMC scan (tests/fixtures/synthetic_2hdmc_scan.csv) and a
synthetic MadGraph deliverable (tests/fixtures/synthetic_madgraph_xsec_runs.csv)
through all four stages (bridge -> madgraph-prepare -> madgraph-sigma ->
sigma-apply) so the chain is proven correct before any real 2HDMC scan exists.
All inputs/outputs are redirected into a temp dir; nothing here touches the
real outputs/ or data/manual/ directories.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SYNTHETIC_SCAN = FIXTURES / "synthetic_2hdmc_scan.csv"
SYNTHETIC_MADGRAPH_XSEC = FIXTURES / "synthetic_madgraph_xsec_runs.csv"

EXPECTED_RANK_ORDER = [
    "syn_0002", "syn_0008", "syn_0004", "syn_0017", "syn_0006", "syn_0001",
    "syn_0016", "syn_0003", "syn_0005", "syn_0007", "syn_0009", "syn_0010",
    "syn_0014", "syn_0015",
]

SUPPLIED_POINT_IDS = {"syn_0002", "syn_0008", "syn_0004", "syn_0017", "syn_0006"}

EXPECTED_NEAREST = {
    "syn_0002": {"nearest_mass_GeV": 500, "nearest_width_hypothesis": "NWA", "observed_limit_fb": 0.945830, "expected_limit_fb": 0.640152},
    "syn_0008": {"nearest_mass_GeV": 2000, "nearest_width_hypothesis": "10pct", "observed_limit_fb": 0.121571, "expected_limit_fb": 0.115118},
    "syn_0004": {"nearest_mass_GeV": 700, "nearest_width_hypothesis": "2pct", "observed_limit_fb": 0.612038, "expected_limit_fb": 0.570755},
    "syn_0017": {"nearest_mass_GeV": 2800, "nearest_width_hypothesis": "10pct", "observed_limit_fb": 0.037335, "expected_limit_fb": 0.057306},
    "syn_0006": {"nearest_mass_GeV": 1200, "nearest_width_hypothesis": "6pct", "observed_limit_fb": 0.190591, "expected_limit_fb": 0.317095},
}

EXPECTED_SIGMA_TOTAL_FB = {
    "syn_0002": 18.0,
    "syn_0008": 2.0,
    "syn_0004": 5.0,
    "syn_0017": 0.6,
    "syn_0006": 10.0,
}

EXPECTED_RATIOS = {
    "syn_0002": {"ratio_to_observed_limit_context_only": 1.522472, "ratio_to_expected_limit_context_only": 2.249466, "ratio_observed_ge1_context_only": "TRUE_CONTEXT_ONLY", "ratio_expected_ge1_context_only": "TRUE_CONTEXT_ONLY"},
    "syn_0008": {"ratio_to_observed_limit_context_only": 0.987078, "ratio_to_expected_limit_context_only": 1.042409, "ratio_observed_ge1_context_only": "FALSE_CONTEXT_ONLY", "ratio_expected_ge1_context_only": "TRUE_CONTEXT_ONLY"},
    "syn_0004": {"ratio_to_observed_limit_context_only": 0.408471, "ratio_to_expected_limit_context_only": 0.438016, "ratio_observed_ge1_context_only": "FALSE_CONTEXT_ONLY", "ratio_expected_ge1_context_only": "FALSE_CONTEXT_ONLY"},
    "syn_0017": {"ratio_to_observed_limit_context_only": 0.723180, "ratio_to_expected_limit_context_only": 0.471157, "ratio_observed_ge1_context_only": "FALSE_CONTEXT_ONLY", "ratio_expected_ge1_context_only": "FALSE_CONTEXT_ONLY"},
    "syn_0006": {"ratio_to_observed_limit_context_only": 2.098735, "ratio_to_expected_limit_context_only": 1.261452, "ratio_observed_ge1_context_only": "TRUE_CONTEXT_ONLY", "ratio_expected_ge1_context_only": "TRUE_CONTEXT_ONLY"},
}


def _run(args: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [sys.executable, *args], cwd=ROOT, env=env, text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr
    return result


@pytest.fixture(scope="module")
def chain_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("2hdmc_chain")


@pytest.fixture(scope="module")
def bridge_dir(chain_dir: Path) -> Path:
    outdir = chain_dir / "bridge"
    _run(
        [
            "scripts/09_link_2hdmc_to_diphoton.py",
            "--scan-root", str(SYNTHETIC_SCAN),
            "--outdir", str(outdir),
            "--write-discovery-report",
        ]
    )
    return outdir


@pytest.fixture(scope="module")
def deck_dir(chain_dir: Path, bridge_dir: Path) -> Path:
    deck_root = chain_dir / "madgraph_runs"
    _run(
        [
            "scripts/12_prepare_madgraph_runs.py",
            "--priority", str(bridge_dir / "priority_points_for_sigma.csv"),
            "--deck-root", str(deck_root),
            "--skeleton-out", str(deck_root / "madgraph_xsec_runs_skeleton.csv"),
        ]
    )
    return deck_root


@pytest.fixture(scope="module")
def sigma_input_csv(chain_dir: Path, bridge_dir: Path, deck_dir: Path) -> Path:
    sigma_output = chain_dir / "diphoton_sigma_inputs.csv"
    _run(
        [
            "scripts/11_ingest_madgraph_xsec.py",
            "--madgraph-table", str(SYNTHETIC_MADGRAPH_XSEC),
            "--priority", str(bridge_dir / "priority_points_for_sigma.csv"),
            "--sigma-output", str(sigma_output),
            "--report-dir", str(chain_dir / "madgraph_sigma_ingest"),
            "--strict-point-ids",
        ]
    )
    return sigma_output


@pytest.fixture(scope="module")
def sigma_applied_csv(chain_dir: Path, bridge_dir: Path, sigma_input_csv: Path) -> Path:
    outdir = chain_dir / "sigma_applied"
    _run(
        [
            "scripts/10_apply_sigma_inputs.py",
            "--priority", str(bridge_dir / "priority_points_for_sigma.csv"),
            "--comparison", str(bridge_dir / "diphoton_comparison_needs_xsec.csv"),
            "--sigma-input", str(sigma_input_csv),
            "--outdir", str(outdir),
        ]
    )
    return outdir / "diphoton_sigma_applied.csv"


def test_bridge_produces_expected_priority_ranking(bridge_dir: Path):
    theory = pd.read_csv(bridge_dir / "theory_side_from_2hdmc.csv")
    assert len(theory) == 14
    assert set(theory["point_id"].astype(str)) == set(EXPECTED_RANK_ORDER)

    priority = pd.read_csv(bridge_dir / "priority_points_for_sigma.csv")
    assert priority["point_id"].astype(str).tolist() == EXPECTED_RANK_ORDER
    assert priority["priority_rank"].tolist() == list(range(1, 15))

    inside = priority["atlas_mass_range_status"] == "INSIDE_ATLAS_SCALAR_RANGE_160_3000_GEV"
    assert inside.sum() == 12
    assert set(priority.loc[~inside, "point_id"].astype(str)) == {"syn_0014", "syn_0015"}
    assert set(priority["nearest_atlas_width_hypothesis"]) == {"NWA", "2pct", "6pct", "10pct"}

    report = (bridge_dir / "discovery_report.md").read_text(encoding="utf-8")
    assert "synthetic_2hdmc_scan.csv" in report
    assert "## Rejected Files" in report


def test_comparison_join_matches_real_atlas_limits(bridge_dir: Path):
    comparison = pd.read_csv(bridge_dir / "diphoton_comparison_needs_xsec.csv")
    comparison = comparison.set_index(comparison["point_id"].astype(str))

    for point_id, expected in EXPECTED_NEAREST.items():
        row = comparison.loc[point_id]
        assert row["nearest_mass_GeV"] == expected["nearest_mass_GeV"]
        assert row["nearest_width_hypothesis"] == expected["nearest_width_hypothesis"]
        assert row["observed_limit_fb"] == pytest.approx(expected["observed_limit_fb"], rel=1e-5)
        assert row["expected_limit_fb"] == pytest.approx(expected["expected_limit_fb"], rel=1e-5)


def test_madgraph_prepare_creates_one_deck_per_priority_point(deck_dir: Path):
    skeleton = pd.read_csv(deck_dir / "madgraph_xsec_runs_skeleton.csv")
    assert len(skeleton) == 14
    for col in ("xsec_pb", "xsec_fb", "xsec_unc_pb"):
        assert skeleton[col].fillna("").astype(str).eq("").all()

    deck_names = {f"mg_{point_id}" for point_id in EXPECTED_RANK_ORDER}
    actual_decks = {p.name for p in deck_dir.iterdir() if p.is_dir()}
    assert deck_names == actual_decks

    proc_card = (deck_dir / "mg_syn_0002" / "proc_card.dat").read_text(encoding="utf-8")
    assert "{{" not in proc_card


def test_madgraph_sigma_ingest_matches_expected_totals(sigma_input_csv: Path):
    sigma = pd.read_csv(sigma_input_csv).set_index(pd.read_csv(sigma_input_csv)["point_id"].astype(str))
    assert set(sigma.index) == SUPPLIED_POINT_IDS
    for point_id, expected_total in EXPECTED_SIGMA_TOTAL_FB.items():
        assert sigma.loc[point_id, "sigma_total_fb"] == pytest.approx(expected_total, rel=1e-9)


def test_sigma_applied_has_sensible_ratios_and_status_flags(sigma_applied_csv: Path):
    applied = pd.read_csv(sigma_applied_csv)
    assert len(applied) == 14
    applied = applied.set_index(applied["point_id"].astype(str))

    for point_id in SUPPLIED_POINT_IDS:
        row = applied.loc[point_id]
        expected = EXPECTED_RATIOS[point_id]
        assert row["sigma_status"] == "SIGMA_SUPPLIED_RATIO_CONTEXT_ONLY"
        assert row["comparison_status"] == "RATIO_COMPUTED_NOT_EXCLUSION"
        assert row["ratio_to_observed_limit_context_only"] == pytest.approx(expected["ratio_to_observed_limit_context_only"], rel=1e-5)
        assert row["ratio_to_expected_limit_context_only"] == pytest.approx(expected["ratio_to_expected_limit_context_only"], rel=1e-5)
        assert row["ratio_observed_ge1_context_only"] == expected["ratio_observed_ge1_context_only"]
        assert row["ratio_expected_ge1_context_only"] == expected["ratio_expected_ge1_context_only"]

    waiting_ids = set(EXPECTED_RANK_ORDER) - SUPPLIED_POINT_IDS
    for point_id in waiting_ids:
        row = applied.loc[point_id]
        assert row["sigma_status"] == "MISSING_PRODUCTION_XSEC"
        assert row["comparison_status"] == "WAITING_FOR_SIGMA_OR_LIMIT_CONTEXT"
        assert pd.isna(row["ratio_to_observed_limit_context_only"])
        assert pd.isna(row["ratio_to_expected_limit_context_only"])

    assert applied["quality_flags"].str.contains("NOT_EXCLUSION_ACCEPTANCE_AND_SIGNAL_MODEL_REQUIRED").all()
