"""Unit tests for the R9 threshold arithmetic."""

import math

import pytest

from llp_recast.r9_threshold import (
    ACCEPTANCE_REUSED,
    RECAST_REQUIRED,
    SIGMA_COUPLING_EXPONENT,
    acceptance_reuse_label,
    expected_events,
    expected_events_at_kappa,
    kappa_from_coupling,
    kappa_from_rate,
    model_point_expected_events,
    rate_from_kappa,
    rate_multiplier_for_events,
    relative_ctau_change,
    required_coupling_gev,
    scaled_sigma_pb,
    sigma_4b_fb,
    visible_sigma_fb,
    yield_threshold,
    yield_thresholds,
)

# Frozen R8 baseline (task specification; mirrored by scripts/r9_recompute_check.py).
SIGMA_PB = 0.000230291167568
BR_BB_SQ = 0.5726516224278888
A_EFF = 0.01573386
G0 = 63.5914252007596588
LUMI = 139.0
N0 = 0.28841501015841364
SIGMA_4B_FB = 0.131876610738628
VIS_FB = 0.0020749281306360694
CTAU0 = 4.32622152973311191


def test_baseline_yield_chain_reproduces_frozen_values():
    assert sigma_4b_fb(SIGMA_PB, BR_BB_SQ) == pytest.approx(SIGMA_4B_FB, rel=1e-14)
    vis = visible_sigma_fb(SIGMA_PB, BR_BB_SQ, A_EFF)
    assert vis == pytest.approx(VIS_FB, rel=1e-14)
    assert expected_events(vis, LUMI) == pytest.approx(N0, rel=1e-14)


def test_exponent_is_exactly_two():
    assert SIGMA_COUPLING_EXPONENT == 2.0


@pytest.mark.parametrize("kappa", [0.5, 1.0, 2.0, 4.0])
def test_rate_and_kappa_are_inverse(kappa):
    assert kappa_from_rate(rate_from_kappa(kappa)) == pytest.approx(kappa, rel=1e-14)


def test_rate_from_kappa_is_quadratic():
    assert rate_from_kappa(2.0) == 4.0
    assert rate_from_kappa(0.5) == 0.25
    # sigma depends on the magnitude only, so a sign flip is invisible
    assert rate_from_kappa(-3.0) == rate_from_kappa(3.0)


@pytest.mark.parametrize(
    "target,mult,kappa,g_req",
    [
        (1.0, 3.4672, 1.86205, 118.410),
        (3.0, 10.4017, 3.22516, 205.093),
        (5.0, 17.3361, 4.16367, 264.774),
        (10.0, 34.6723, 5.88832, 374.446),
    ],
)
def test_illustrative_thresholds_match_independent_values(target, mult, kappa, g_req):
    t = yield_threshold(
        target,
        baseline_events=N0,
        baseline_sigma_pb=SIGMA_PB,
        baseline_visible_sigma_fb=VIS_FB,
        baseline_abs_coupling_gev=G0,
    )
    assert t.rate_multiplier == pytest.approx(mult, rel=1e-4)
    assert t.kappa_g == pytest.approx(kappa, rel=1e-5)
    assert t.required_abs_coupling_gev == pytest.approx(g_req, rel=1e-5)


def test_threshold_closes_back_to_the_target_yield():
    for t in yield_thresholds(
        baseline_events=N0,
        baseline_sigma_pb=SIGMA_PB,
        baseline_visible_sigma_fb=VIS_FB,
        baseline_abs_coupling_gev=G0,
    ):
        assert t.required_visible_sigma_fb * LUMI == pytest.approx(t.target_events, rel=1e-12)
        # and the required sigma reproduces the required visible sigma
        assert visible_sigma_fb(t.required_sigma_pb, BR_BB_SQ, A_EFF) == pytest.approx(
            t.required_visible_sigma_fb, rel=1e-12
        )


def test_expected_events_at_kappa_is_consistent_with_thresholds():
    for target in (1.0, 3.0, 5.0, 10.0):
        kappa = kappa_from_rate(rate_multiplier_for_events(target, N0))
        got = expected_events_at_kappa(
            kappa,
            baseline_sigma_pb=SIGMA_PB,
            br_bb_squared=BR_BB_SQ,
            a_eff=A_EFF,
            luminosity_fb_inverse=LUMI,
        )
        assert got == pytest.approx(target, rel=1e-12)


def test_scaled_sigma_and_required_coupling_are_consistent():
    kappa = 1.86204885
    assert scaled_sigma_pb(SIGMA_PB, kappa) == pytest.approx(SIGMA_PB * kappa**2, rel=1e-15)
    assert required_coupling_gev(kappa, G0) == pytest.approx(kappa * G0, rel=1e-15)
    assert kappa_from_coupling(kappa * G0, G0) == pytest.approx(kappa, rel=1e-15)


def test_kappa_from_coupling_uses_magnitudes():
    # the trilinear flips sign as M^2 crosses the cancellation point
    assert kappa_from_coupling(-118.41, G0) == pytest.approx(kappa_from_coupling(118.41, G0))


def test_model_point_never_silently_reuses_the_baseline_br():
    halved = model_point_expected_events(
        sigma_pb=SIGMA_PB, br_bb_squared=BR_BB_SQ / 2.0,
        a_eff=A_EFF, luminosity_fb_inverse=LUMI,
    )
    assert halved == pytest.approx(N0 / 2.0, rel=1e-12)


def test_acceptance_reuse_label_boundary():
    # Exactly +-10% is not representable in binary, so probe just inside and
    # just outside the declared 10% window rather than on it.
    assert acceptance_reuse_label(CTAU0, CTAU0) == ACCEPTANCE_REUSED
    assert acceptance_reuse_label(CTAU0 * 1.0999, CTAU0) == ACCEPTANCE_REUSED
    assert acceptance_reuse_label(CTAU0 * 1.1001, CTAU0) == RECAST_REQUIRED
    assert acceptance_reuse_label(CTAU0 * 0.9001, CTAU0) == ACCEPTANCE_REUSED
    assert acceptance_reuse_label(CTAU0 * 0.8999, CTAU0) == RECAST_REQUIRED
    assert acceptance_reuse_label(CTAU0 * 0.5, CTAU0) == RECAST_REQUIRED
    # the comparison is inclusive at the tolerance itself (0.5 is exact in binary)
    assert acceptance_reuse_label(1.5, 1.0, tolerance=0.5) == ACCEPTANCE_REUSED


def test_relative_ctau_change_is_signed():
    assert relative_ctau_change(CTAU0 * 1.05, CTAU0) == pytest.approx(0.05, rel=1e-12)
    assert relative_ctau_change(CTAU0 * 0.95, CTAU0) == pytest.approx(-0.05, rel=1e-12)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        rate_multiplier_for_events(1.0, 0.0)
    with pytest.raises(ValueError):
        kappa_from_rate(-1.0)
    with pytest.raises(ValueError):
        kappa_from_rate(4.0, exponent=0.0)
    with pytest.raises(ValueError):
        kappa_from_coupling(1.0, 0.0)
    with pytest.raises(ValueError):
        acceptance_reuse_label(1.0, 0.0)


def test_a_ten_percent_rate_change_needs_a_five_percent_coupling_change():
    """Sanity anchor for the square-root relation used throughout the report."""
    assert kappa_from_rate(1.10) == pytest.approx(math.sqrt(1.10), rel=1e-15)
    assert kappa_from_rate(1.10) == pytest.approx(1.0488, rel=1e-4)
