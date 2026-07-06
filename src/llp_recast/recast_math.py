from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import C_MM_PER_NS, HBAR_C_GEV_MM


def ctau_mm_from_width_gev(total_width_gev: float) -> float:
    """Convert total width in GeV to c*tau in mm."""
    if total_width_gev <= 0 or not math.isfinite(total_width_gev):
        return math.inf
    return HBAR_C_GEV_MM / total_width_gev


def width_gev_from_ctau_mm(ctau_mm: float) -> float:
    """Convert c*tau in mm to total width in GeV."""
    if ctau_mm <= 0 or not math.isfinite(ctau_mm):
        return math.inf
    return HBAR_C_GEV_MM / ctau_mm


# ponytail: SDD-requested names are aliases of the two functions above, not new math.
width_gev_to_ctau_mm = ctau_mm_from_width_gev
ctau_mm_to_width_gev = width_gev_from_ctau_mm


def tau_ns_to_ctau_mm(tau_ns: float) -> float:
    """Convert proper lifetime in ns to c*tau in mm."""
    return C_MM_PER_NS * tau_ns


def ctau_mm_to_tau_ns(ctau_mm: float) -> float:
    """Convert c*tau in mm to proper lifetime in ns."""
    return ctau_mm / C_MM_PER_NS


def decay_probability_between_radii(lab_decay_length_mm: float, r_min_mm: float, r_max_mm: float) -> float:
    """Probability for an LLP with exponential lab decay length to decay between two radii.

    This is a geometric proxy. It ignores eta/z acceptance and detector/reconstruction effects.
    """
    if lab_decay_length_mm <= 0 or not math.isfinite(lab_decay_length_mm):
        return 0.0
    if r_max_mm <= r_min_mm:
        return 0.0
    p = math.exp(-r_min_mm / lab_decay_length_mm) - math.exp(-r_max_mm / lab_decay_length_mm)
    return max(0.0, min(1.0, p))


def decay_probability_between(r_min_mm: float, r_max_mm: float, lab_decay_length_mm: float) -> float:
    """Same as decay_probability_between_radii with the SDD-requested (Rmin, Rmax, L) argument order."""
    return decay_probability_between_radii(lab_decay_length_mm, r_min_mm, r_max_mm)


def event_probability_at_least_one(single_llp_probability: float, n_llp: int = 2) -> float:
    """Event probability that at least one of n LLPs satisfies a condition."""
    p = max(0.0, min(1.0, single_llp_probability))
    if n_llp <= 0:
        return 0.0
    return 1.0 - (1.0 - p) ** n_llp


def event_probability_two(single_llp_probability: float) -> float:
    """Event probability that both of two independent LLPs satisfy a condition."""
    p = max(0.0, min(1.0, single_llp_probability))
    return p * p


def expected_yield(lumi_fb: float, xsec_fb: float, br_factor: float, acceptance_efficiency: float) -> float:
    """Expected event yield for cross section in fb and luminosity in fb^-1."""
    vals = [lumi_fb, xsec_fb, br_factor, acceptance_efficiency]
    if any((v < 0 or not math.isfinite(v)) for v in vals):
        return math.nan
    return lumi_fb * xsec_fb * br_factor * acceptance_efficiency


@dataclass(frozen=True)
class ToyScalarPoint:
    mass_gev: float
    ctau_mm: float
    beta_gamma: float
    xsec_fb: float
    br_had: float
    eps_reco_proxy: float

    @property
    def total_width_gev(self) -> float:
        return width_gev_from_ctau_mm(self.ctau_mm)

    @property
    def lab_decay_length_mm(self) -> float:
        return self.beta_gamma * self.ctau_mm
