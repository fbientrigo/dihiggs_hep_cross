import math

from llp_recast.constants import HBAR_C_GEV_MM
from llp_recast.recast_math import (
    ctau_mm_from_width_gev,
    decay_probability_between_radii,
    event_probability_at_least_one,
    expected_yield,
)


def test_ctau_width_roundtrip_for_one_mm():
    width = HBAR_C_GEV_MM / 1.0
    assert math.isclose(ctau_mm_from_width_gev(width), 1.0, rel_tol=1e-12)


def test_decay_probability_between_radii_is_bounded():
    p = decay_probability_between_radii(100.0, 4.0, 300.0)
    assert 0.0 <= p <= 1.0
    assert p > 0.0


def test_event_probability_at_least_one_two_llps():
    assert math.isclose(event_probability_at_least_one(0.5, 2), 0.75)


def test_expected_yield_units_fb():
    assert math.isclose(expected_yield(139.0, 1.0, 1.0, 0.1), 13.9)
