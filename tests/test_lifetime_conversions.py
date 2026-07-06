import math

from llp_recast.recast_math import (
    ctau_mm_to_tau_ns,
    ctau_mm_to_width_gev,
    tau_ns_to_ctau_mm,
    width_gev_to_ctau_mm,
)


def test_width_ctau_roundtrip():
    for x in (0.5, 1.0, 3.7, 1000.0):
        assert math.isclose(ctau_mm_to_width_gev(width_gev_to_ctau_mm(x)), x, rel_tol=1e-12)


def test_tau_ns_to_ctau_mm_one_ns():
    assert math.isclose(tau_ns_to_ctau_mm(1.0), 299.792458, rel_tol=1e-9)


def test_ctau_mm_to_tau_ns_roundtrip():
    for tau in (0.01, 0.1, 1.0, 10.0):
        assert math.isclose(ctau_mm_to_tau_ns(tau_ns_to_ctau_mm(tau)), tau, rel_tol=1e-12)
