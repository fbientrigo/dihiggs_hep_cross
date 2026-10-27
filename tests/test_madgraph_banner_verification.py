"""Unit tests for convention-aware banner verification."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from madgraph_banner_verification import banner_checks, checks_pass, compatible


def make_banner(tmp_path, coupling=-63.5914252007596588, mh=125.13, mH2=150.0):
    path = tmp_path / "banner.txt"
    path.write_text(f"""generate g g > H > h2 h2
6500 = ebeam1
6500 = ebeam2
nn23lo1 = pdlabel
230000 = lhaid
False = fixed_ren_scale
False = fixed_fac_scale
-1 = dynamical_scale_choice
 25 {mh} # MH
 9000006 {mH2} # Mh2
 3 {coupling} # GHphiphi
DECAY 9000006 4.561185e-14
""")
    return path


LEGACY_POINT = {
    "mh_input_GeV": 125.13,
    "mH_input_GeV": 150.0,
    "g_hH2H2_GeV": 63.5914252007596588,
    "total_width_GeV": 4.561185e-14,
    "historical_replay": True,
    "mass_convention_id": "mh_125p13_high_mass_v1",
}


def test_banner_checks_all_required_fields(tmp_path):
    banner = make_banner(tmp_path)
    checks = banner_checks(banner, LEGACY_POINT)
    assert checks == {name: True for name in checks}
    assert checks_pass(banner, LEGACY_POINT)


def test_legacy_replay_keeps_magnitude_compatibility(tmp_path):
    banner = make_banner(tmp_path)
    malformed_magnitude = dict(LEGACY_POINT, g_hH2H2_GeV=-63.5914252007596588)
    assert banner_checks(banner, malformed_magnitude)["convention_provenance"] is False
    mismatched = dict(LEGACY_POINT, g_hH2H2_GeV=1.0)
    checks = banner_checks(banner, mismatched)
    assert checks["coupling"] is False
    assert not checks_pass(banner, mismatched)


def test_banner_checks_catches_a_wrong_mass(tmp_path):
    checks = banner_checks(make_banner(tmp_path), dict(LEGACY_POINT, mH_input_GeV=999.0))
    assert checks["mH2"] is False
    assert not checks_pass(make_banner(tmp_path), dict(LEGACY_POINT, mH_input_GeV=999.0))


def _v3_point(signed):
    return {
        "m_h_GeV": "125.20", "m_phi_GeV": 150.0,
        "g_physical_hphiphi_GeV": signed,
        "g_physical_hphiphi_abs_GeV": abs(signed), "g_hH2H2_GeV": abs(signed),
        "two_hdmc_hphiphi_real_GeV": 0.0,
        "two_hdmc_hphiphi_imag_GeV": -signed,
        "coupling_prescription": "physical_2HDM",
        "mass_convention_id": "mh_125p20_active_2026", "m_h_GeV_text": "125.20",
        "physics_conventions_schema": "physics_conventions_v3",
        "physics_conventions_commit": "087ba246e9a9fa34b16249b52629a62703893b5c",
        "physics_conventions_sha256": "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6",
        "total_width_GeV": 4.561185e-14,
    }


def test_v3_signed_physical_coupling_is_used_with_its_sign(tmp_path):
    point = _v3_point(63.5914252007596588)
    checks = banner_checks(make_banner(tmp_path, mh=125.20), point)
    assert checks["convention_provenance"] is True
    assert checks["coupling"] is True

    point = _v3_point(-63.5914252007596588)
    checks = banner_checks(make_banner(tmp_path, coupling=63.5914252007596588, mh=125.20), point)
    assert checks["convention_provenance"] is True
    assert checks["coupling"] is True


def test_v3_banner_rejects_stale_numeric_mh_despite_active_text(tmp_path):
    point = _v3_point(5.0)
    point["m_h_GeV"] = "125.13"
    checks = banner_checks(make_banner(tmp_path, coupling=-5.0, mh=125.13), point)
    assert checks["convention_provenance"] is False
    assert checks["mh"] is False
    assert not checks_pass(make_banner(tmp_path, coupling=-5.0, mh=125.13), point)


@pytest.mark.parametrize("missing", ["m_h_GeV", "m_phi_GeV"])
def test_v3_banner_requires_canonical_mass_fields(tmp_path, missing):
    point = _v3_point(5.0)
    del point[missing]
    checks = banner_checks(make_banner(tmp_path, coupling=-5.0, mh=125.20), point)
    assert checks["convention_provenance"] is False
    assert not checks_pass(make_banner(tmp_path, coupling=-5.0, mh=125.20), point)


def test_v3_banner_rejects_conflicting_h2_mass_alias(tmp_path):
    point = _v3_point(5.0)
    point["mH_input_GeV"] = 151.0
    checks = banner_checks(make_banner(tmp_path, coupling=-5.0, mh=125.20), point)
    assert checks["convention_provenance"] is False
    assert checks["mH2"] is False
    assert not checks_pass(make_banner(tmp_path, coupling=-5.0, mh=125.20), point)


def test_v3_signed_coupling_rejects_magnitude_mismatch():
    from run_physical_point_madgraph import resolve_ghphiphi_GeV

    point = _v3_point(63.0)
    point["g_physical_hphiphi_abs_GeV"] = 64.0
    point["g_hH2H2_GeV"] = 64.0
    with pytest.raises(ValueError, match="inconsistent"):
        resolve_ghphiphi_GeV(point)


def test_compatible_agrees_within_3_sigma():
    agreement, difference, combined = compatible(1.000, 0.010, 1.005, 0.010)
    assert agreement is True
    assert difference == abs(1.000 - 1.005)
    assert combined > 0.0


def test_compatible_flags_seed_disagreement():
    agreement, difference, combined = compatible(1.000, 0.001, 1.500, 0.001)
    assert agreement is False
    assert difference > 3.0 * combined
