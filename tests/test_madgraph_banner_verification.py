"""Unit tests for the banner-authoritative verification helpers.

Migrated from mission_runs/20260826_h2_table_v2_requalification/work/
run_madgraph_v2.py during the 2026-08-31 workspace reset; see
scripts/madgraph_banner_verification.py for the migration note.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from madgraph_banner_verification import banner_checks, checks_pass, compatible

REAL_BANNER = REPO_ROOT / "artifacts/h2_first_physical/madgraph/run_01/run_01_tag_1_banner.txt"

# Matches REAL_BANNER exactly (mh=125.13 -- this benchmark predates the
# 125.20 GeV convention; see docs/MH_CONVENTION.md).
REAL_BANNER_POINT = {
    "mh_input_GeV": 125.13,
    "mH_input_GeV": 150.0,
    "g_hH2H2_GeV": 63.5914252007596588,
    "total_width_GeV": 4.561185e-14,
}


def test_banner_checks_all_pass_on_a_real_tracked_banner():
    checks = banner_checks(REAL_BANNER, REAL_BANNER_POINT)
    assert checks == {name: True for name in checks}
    assert checks_pass(REAL_BANNER, REAL_BANNER_POINT)


def test_banner_checks_coupling_uses_the_ghphiphi_sign_convention():
    """GHphiphi must equal -abs(g_hH2H2_GeV). Passing in the point's coupling
    with the opposite sign must still pass (-abs() normalizes it away), but a
    genuinely different magnitude must fail the coupling check even though
    every other field still matches."""
    opposite_sign_point = dict(REAL_BANNER_POINT, g_hH2H2_GeV=-63.5914252007596588)
    assert banner_checks(REAL_BANNER, opposite_sign_point)["coupling"] is True

    mismatched_point = dict(REAL_BANNER_POINT, g_hH2H2_GeV=1.0)
    checks = banner_checks(REAL_BANNER, mismatched_point)
    assert checks["coupling"] is False
    assert not checks_pass(REAL_BANNER, mismatched_point)
    # Sanity: everything else about the same banner still checks out.
    assert checks["mh"] is True
    assert checks["mH2"] is True


def test_banner_checks_catches_a_wrong_mass():
    wrong_mass_point = dict(REAL_BANNER_POINT, mH_input_GeV=999.0)
    checks = banner_checks(REAL_BANNER, wrong_mass_point)
    assert checks["mH2"] is False
    assert not checks_pass(REAL_BANNER, wrong_mass_point)


def test_compatible_agrees_within_3_sigma():
    agreement, difference, combined = compatible(1.000, 0.010, 1.005, 0.010)
    assert agreement is True
    assert difference == abs(1.000 - 1.005)
    assert combined > 0.0


def test_compatible_flags_seed_disagreement():
    agreement, difference, combined = compatible(1.000, 0.001, 1.500, 0.001)
    assert agreement is False
    assert difference > 3.0 * combined
