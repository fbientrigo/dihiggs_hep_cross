"""R9 sensitivity-threshold arithmetic around the validated R8 benchmark.

Pure functions only: no I/O, no matplotlib, no subprocess.  Everything the R9
result depends on numerically is computed here so ``tests/test_r9_threshold.py``
and ``scripts/r9_recompute_check.py`` can re-derive every published number from
the frozen primary inputs.

Conventions
-----------
``sigma`` is the H2H2 production cross section, ``br_bb_squared`` the square of
BR(H2 -> b bbar) (both H2 must decay to b bbar for the 4b final state), and
``a_eff`` the recast A x eff for the region.  The visible cross section is

    sigma_vis = sigma * BR(H2->bb)^2 * (A x eff)

and the expected selected yield is ``sigma_vis * L``.

The production coupling enters only through ``GHphiphi``.  In the shipped UFO
that parameter appears in exactly one coupling, which appears in exactly one
vertex, which appears once in the single diagram of ``g g > H > h2 h2``; the
mediator width is an external constant.  The amplitude is therefore strictly
linear in the coupling and ``sigma`` scales with the exact power
``SIGMA_COUPLING_EXPONENT``.  See ``docs/R9_H2_SENSITIVITY_THRESHOLD_RESULT.md``
for the full evidence chain.
"""

from __future__ import annotations

from dataclasses import dataclass

PB_TO_FB = 1000.0

#: Exact exponent p in sigma/sigma0 = kappa_g**p, established structurally.
SIGMA_COUPLING_EXPONENT = 2.0

#: Event counts used as illustrative rate scales (NOT discovery/exclusion).
ILLUSTRATIVE_EVENT_TARGETS = (1.0, 3.0, 5.0, 10.0)


def pb_to_fb(sigma_pb: float) -> float:
    """Convert a cross section from pb to fb."""
    return sigma_pb * PB_TO_FB


def sigma_4b_fb(sigma_pb: float, br_bb_squared: float) -> float:
    """4b-level cross section in fb: sigma(H2H2) * BR(H2->bb)^2."""
    return pb_to_fb(sigma_pb) * br_bb_squared


def visible_sigma_fb(sigma_pb: float, br_bb_squared: float, a_eff: float) -> float:
    """Visible cross section in fb after the recast acceptance x efficiency."""
    return sigma_4b_fb(sigma_pb, br_bb_squared) * a_eff


def expected_events(visible_sigma_fb_value: float, luminosity_fb_inverse: float) -> float:
    """Expected selected events for a visible cross section in fb."""
    return visible_sigma_fb_value * luminosity_fb_inverse


def rate_multiplier_for_events(target_events: float, baseline_events: float) -> float:
    """Visible-rate multiplier needed to move ``baseline_events`` to ``target_events``.

    Because BR, acceptance and luminosity are held fixed, this is also the
    required multiplier on sigma(pp -> H2H2).
    """
    if baseline_events <= 0.0:
        raise ValueError("baseline_events must be positive")
    return target_events / baseline_events


def kappa_from_rate(rate_multiplier: float, exponent: float = SIGMA_COUPLING_EXPONENT) -> float:
    """Coupling multiplier kappa_g giving a requested cross-section multiplier."""
    if rate_multiplier < 0.0:
        raise ValueError("rate_multiplier must be non-negative")
    if exponent <= 0.0:
        raise ValueError("exponent must be positive")
    return rate_multiplier ** (1.0 / exponent)


def rate_from_kappa(kappa_g: float, exponent: float = SIGMA_COUPLING_EXPONENT) -> float:
    """Cross-section multiplier produced by a coupling multiplier kappa_g."""
    return abs(kappa_g) ** exponent


def required_coupling_gev(kappa_g: float, baseline_abs_coupling_gev: float) -> float:
    """|g_hH2H2| required for a given kappa_g, in GeV."""
    return abs(kappa_g) * abs(baseline_abs_coupling_gev)


def kappa_from_coupling(coupling_gev: float, baseline_abs_coupling_gev: float) -> float:
    """kappa_g = |g| / |g0|.

    The sign of ``g_hH2H2`` flips as M^2 crosses the cancellation point, but
    sigma depends only on the squared coupling, so kappa_g is defined on
    magnitudes.
    """
    if baseline_abs_coupling_gev == 0.0:
        raise ValueError("baseline coupling must be non-zero")
    return abs(coupling_gev) / abs(baseline_abs_coupling_gev)


@dataclass(frozen=True)
class YieldThreshold:
    """One illustrative event-count threshold and what it costs in coupling."""

    target_events: float
    rate_multiplier: float
    kappa_g: float
    required_abs_coupling_gev: float
    required_sigma_pb: float
    required_visible_sigma_fb: float

    def as_row(self) -> dict[str, float]:
        return {
            "target_events": self.target_events,
            "rate_multiplier": self.rate_multiplier,
            "kappa_g": self.kappa_g,
            "required_abs_g_hH2H2_GeV": self.required_abs_coupling_gev,
            "required_sigma_H2H2_pb": self.required_sigma_pb,
            "required_visible_sigma_fb": self.required_visible_sigma_fb,
        }


def yield_threshold(
    target_events: float,
    *,
    baseline_events: float,
    baseline_sigma_pb: float,
    baseline_visible_sigma_fb: float,
    baseline_abs_coupling_gev: float,
    exponent: float = SIGMA_COUPLING_EXPONENT,
) -> YieldThreshold:
    """Build one :class:`YieldThreshold` from the frozen baseline."""
    multiplier = rate_multiplier_for_events(target_events, baseline_events)
    kappa = kappa_from_rate(multiplier, exponent)
    return YieldThreshold(
        target_events=target_events,
        rate_multiplier=multiplier,
        kappa_g=kappa,
        required_abs_coupling_gev=required_coupling_gev(kappa, baseline_abs_coupling_gev),
        required_sigma_pb=baseline_sigma_pb * multiplier,
        required_visible_sigma_fb=baseline_visible_sigma_fb * multiplier,
    )


def yield_thresholds(
    targets=ILLUSTRATIVE_EVENT_TARGETS,
    **baseline,
) -> list[YieldThreshold]:
    """Build the full illustrative threshold table."""
    return [yield_threshold(t, **baseline) for t in targets]


def scaled_sigma_pb(baseline_sigma_pb: float, kappa_g: float, exponent: float = SIGMA_COUPLING_EXPONENT) -> float:
    """sigma(kappa_g) under the exact structural scaling law."""
    return baseline_sigma_pb * rate_from_kappa(kappa_g, exponent)


def expected_events_at_kappa(
    kappa_g: float,
    *,
    baseline_sigma_pb: float,
    br_bb_squared: float,
    a_eff: float,
    luminosity_fb_inverse: float,
    exponent: float = SIGMA_COUPLING_EXPONENT,
) -> float:
    """Expected selected events at a coupling multiplier, BR and A x eff fixed."""
    sigma = scaled_sigma_pb(baseline_sigma_pb, kappa_g, exponent)
    return expected_events(
        visible_sigma_fb(sigma, br_bb_squared, a_eff), luminosity_fb_inverse
    )


def model_point_expected_events(
    *,
    sigma_pb: float,
    br_bb_squared: float,
    a_eff: float,
    luminosity_fb_inverse: float,
) -> float:
    """Expected events for a model-derived point using its own sigma and BR.

    Distinct from :func:`expected_events_at_kappa` on purpose: a model-derived
    point must never inherit the baseline BR.
    """
    return expected_events(
        visible_sigma_fb(sigma_pb, br_bb_squared, a_eff), luminosity_fb_inverse
    )


CTAU_REUSE_TOLERANCE = 0.10

ACCEPTANCE_REUSED = "ACCEPTANCE_REUSED_AT_FIXED_MASS_AND_NEARBY_LIFETIME"
RECAST_REQUIRED = "RECAST_REQUIRED_FOR_EXACT_YIELD"


def acceptance_reuse_label(
    ctau_mm: float,
    baseline_ctau_mm: float,
    tolerance: float = CTAU_REUSE_TOLERANCE,
) -> str:
    """Label whether the validated R8 acceptance may be reused as a rate-only value."""
    if baseline_ctau_mm <= 0.0:
        raise ValueError("baseline_ctau_mm must be positive")
    relative_change = abs(ctau_mm - baseline_ctau_mm) / baseline_ctau_mm
    return ACCEPTANCE_REUSED if relative_change <= tolerance else RECAST_REQUIRED


def relative_ctau_change(ctau_mm: float, baseline_ctau_mm: float) -> float:
    """Signed fractional change of ctau relative to the baseline."""
    if baseline_ctau_mm <= 0.0:
        raise ValueError("baseline_ctau_mm must be positive")
    return (ctau_mm - baseline_ctau_mm) / baseline_ctau_mm
