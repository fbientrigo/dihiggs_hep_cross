"""Paper-aware (arXiv:2606.01681) scalar-S model semantics.

This module isolates parameters and assumptions that are specific to the
pp -> gg -> h* -> S S benchmark from the generic geometry/lifetime math in
recast_math.py. Nothing here should be treated as validated against the
paper's actual tables unless the docstring says so explicitly.

WARNING: the paper's lambda_eff / sin_theta are NOT the same objects as a
2HDM lambda6, lambda7, or sin(beta-alpha). See
docs/contracts/model_point_to_llp_recast_contract.md before mapping points
from an extended-Higgs-sector scan into this module.
"""
from __future__ import annotations

from dataclasses import dataclass

from .recast_math import ctau_mm_to_tau_ns

PAPER_BENCHMARK_MASSES_GEV = [100.0, 170.0, 250.0]
PAPER_BENCHMARK_CTAU_MM = [3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0]

BR_MODE_PAPER_PLACEHOLDER = "paper_placeholder"
BR_MODE_USER_TABLE = "user_table"

# ponytail: single flat threshold, not a fitted curve. Replace when HDECAY /
# HiggsBounds-style partial widths for S are ingested.
BR_HADRONIC_PLACEHOLDER_LOW_MASS = 0.8
BR_HADRONIC_PLACEHOLDER_HIGH_MASS = 0.5
BR_HADRONIC_MASS_THRESHOLD_GEV = 140.0


def br_hadronic_proxy(
    mass_gev: float,
    mode: str = BR_MODE_PAPER_PLACEHOLDER,
    user_table: dict[float, float] | None = None,
) -> float:
    """Approximate hadronic branching fraction for the scalar S.

    mode="paper_placeholder": documented placeholder, NOT read from the paper.
        mS < 140 GeV -> bb-dominated, BR_had ~ 0.8
        mS >= 140 GeV -> WW/ZZ open up, BR_had ~ 0.5 (still counts qqqq as hadronic)
    mode="user_table": nearest-mass lookup in a caller-supplied {mass_gev: BR} table,
        e.g. digitized from the paper, HDECAY, or a dedicated width calculator.
    """
    if mode == BR_MODE_USER_TABLE:
        if not user_table:
            raise ValueError("user_table mode requires a non-empty user_table")
        nearest = min(user_table, key=lambda m: abs(m - mass_gev))
        return user_table[nearest]
    if mode == BR_MODE_PAPER_PLACEHOLDER:
        return (
            BR_HADRONIC_PLACEHOLDER_LOW_MASS
            if mass_gev < BR_HADRONIC_MASS_THRESHOLD_GEV
            else BR_HADRONIC_PLACEHOLDER_HIGH_MASS
        )
    raise ValueError(f"unknown BR mode: {mode!r}")


@dataclass(frozen=True)
class PaperScalarPoint:
    """One pp -> gg -> h* -> S S benchmark point (arXiv:2606.01681 semantics).

    sin_theta and lambda_eff are the paper's scalar-mixing/lifetime control and
    effective hSS coupling respectively. They are model parameters of THIS paper
    only -- do not equate them with a 2HDM sin(beta-alpha) or lambda6/lambda7.
    """

    mS_GeV: float
    ctau_mm: float
    sin_theta: float | None = None
    lambda_eff: float | None = None
    sigma_gg_hstar_SS_fb: float | None = None
    BR_bb: float | None = None
    BR_WW: float | None = None
    BR_ZZ: float | None = None
    BR_gg: float | None = None
    BR_hadronic_proxy: float | None = None

    @property
    def tau_ns(self) -> float:
        return ctau_mm_to_tau_ns(self.ctau_mm)
