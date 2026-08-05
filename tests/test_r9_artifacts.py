"""Contract tests for the committed R9 threshold result."""

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"


def load(name):
    return json.loads((OUTDIR / name).read_text())


def test_official_atlas_trackless_threshold_is_resolved():
    atlas = load("atlas_threshold.json")
    assert atlas["status"] == "OFFICIAL_THRESHOLD_RESOLVED"
    assert atlas["region_mapping"]["region_mapping_status"] == "UNAMBIGUOUS"
    n = atlas["numerical_threshold"]
    assert n["observed_events"] == 0
    assert n["expected_background"] == 0.83
    assert n["observed_S95"] == 3.0
    assert n["expected_S95"] == 3.4
    assert n["published_model_independent_visible_sigma_limit_fb"] == 0.022
    assert math.isclose(atlas["required_visible_sigma_fb"], 3.0 / 139.0)
    assert n["published_rounding_check_pass"] is True


def test_official_threshold_matches_three_event_row():
    atlas = load("atlas_threshold.json")
    with open(OUTDIR / "yield_thresholds.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    row = next(row for row in rows if float(row["target_events"]) == 3.0)
    assert math.isclose(atlas["required_rate_multiplier"], float(row["rate_multiplier"]))
    assert math.isclose(atlas["required_kappa_g"], float(row["kappa_g"]))
    assert math.isclose(
        atlas["required_abs_g_hH2H2_GeV"],
        float(row["required_abs_g_hH2H2_GeV"]),
    )


def test_scope_is_limited_to_the_tested_fixed_slice():
    summary = load("result_summary.json")
    assert summary["scope_status"] == (
        "THRESHOLD_NOT_REACHABLE_IN_THE_TESTED_FIXED_SLICE"
    )
    fixed = summary["tested_fixed_slice"]
    assert fixed["m_H2_GeV"] == 150.0
    assert fixed["tan_beta"] == 300000.0
    assert fixed["varied_coordinate"] == "m12_sq / M2 only"
    assert summary["q5_model_reachability"]["official_threshold_reached"] is False


def test_madgraph_runner_applies_each_run_card_key_once():
    runner = (
        OUTDIR / "madgraph_deck" / "run_commands.sh"
    ).read_text(encoding="utf-8")
    assert "cat run_card_fragment.dat >>" not in runner
    assert "run_card.r9_base.dat" in runner
    assert 'cp "$BASE_CARD" "$RUN_CARD"' in runner
    assert "does not occur exactly once" in runner

    keys = []
    for line in (
        OUTDIR / "madgraph_deck" / "run_card_fragment.dat"
    ).read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            keys.append(line.split("=", 1)[1].split("#", 1)[0].strip().split()[0])
    assert len(keys) == len(set(keys))


def test_recompute_and_manifest_gates_pass():
    for script in ("r9_recompute_check.py", "verify_r9_artifacts.py"):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / script)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


def test_presentation_has_exactly_three_slides_and_safe_wording():
    text = (REPO_ROOT / "docs" / "R9_PRESENTATION_INSERT_ES.md").read_text()
    assert len([line for line in text.splitlines() if line.startswith("## ")]) == 3
    assert "205.09 GeV" in text
    assert "slice fija" in text
    assert "cτ ∝ tan²β" not in text
    assert "completamente normal" not in text
