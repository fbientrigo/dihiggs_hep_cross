#!/usr/bin/env python3
"""Banner-authoritative verification for a physical-point MadGraph run.

This is the mechanism that makes a MadGraph banner *authoritative over any
copied summary value* (see docs/CURRENT_DATA_AUTHORITY.md): given the point
that was supposedly generated and the banner MadGraph actually wrote, confirm
the banner really encodes that point's process, kinematics, and coupling
prescription -- not just that a run happened.

Migrated from mission_runs/20260826_h2_table_v2_requalification/work/
run_madgraph_v2.py (banner_checks, compatible) during the 2026-08-31 workspace
reset. That script also hardcoded one campaign's specific benchmark points and
its own archival bookkeeping; those parts are campaign-specific and were left
behind in the archive (see /home/fabian/atlas_dihiggs_archive/
20260831_pre_madgraph_reset/). Only the reusable, campaign-agnostic
verification logic below was lifted into tracked source.

The generic per-point MadGraph run driver lives in
run_physical_point_madgraph.py, already tracked in this repo -- this module
does not duplicate it, only adds the banner-consistency check that was
missing.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Dict


def banner_checks(banner_path: Path, point: Dict[str, Any]) -> Dict[str, bool]:
    """Verify a MadGraph banner is internally consistent with the point it
    claims to have produced.

    ``point`` must supply ``g_hH2H2_GeV``, ``mh_input_GeV`` (or ``mh_GeV``),
    ``mH_input_GeV`` (or ``mH2_GeV``), and ``total_width_GeV``. Returns one
    bool per check; a run is trustworthy only if every value is True --
    checking ``all(banner_checks(...).values())`` (or the ``checks_pass``
    convenience below) before treating its sigma as authoritative.

    Checks the process string, sqrt(s), PDF set, dynamic-scale settings, the
    SM-like Higgs and H2 masses, the mediator width, and -- the check with no
    prior tracked-source equivalent -- that the banner's GHphiphi coupling
    matches the point's coupling-prescription value with the sign convention
    ``GHphiphi = -abs(g_hH2H2_GeV)`` (see run_physical_point_madgraph.py's
    ``generate_param_card_text``, which writes the card with this same
    convention).
    """
    text = banner_path.read_text(encoding="utf-8", errors="replace")

    def number(pattern: str) -> float:
        match = re.search(pattern, text, re.I | re.M)
        return float(match.group(1)) if match else float("nan")

    mh_GeV = float(point.get("mh_input_GeV", point.get("mh_GeV")))
    mH2_GeV = float(point.get("mH_input_GeV", point.get("mH2_GeV")))
    expected_g = -abs(float(point["g_hH2H2_GeV"]))

    return {
        "process": bool(re.search(r"^generate g g > H > h2 h2\s*$", text, re.M)),
        "sqrt_s_13_TeV": number(r"^\s*([\d.eE+\-]+)\s*=\s*ebeam1") == 6500.0
        and number(r"^\s*([\d.eE+\-]+)\s*=\s*ebeam2") == 6500.0,
        "pdf": bool(re.search(r"^\s*nn23lo1\s*=\s*pdlabel", text, re.M))
        and bool(re.search(r"^\s*230000\s*=\s*lhaid", text, re.M)),
        "dynamic_scales": bool(re.search(r"^\s*False\s*=\s*fixed_ren_scale", text, re.I | re.M))
        and bool(re.search(r"^\s*False\s*=\s*fixed_fac_scale", text, re.I | re.M))
        and bool(re.search(r"^\s*-1\s*=\s*dynamical_scale_choice", text, re.M)),
        "mh": math.isclose(number(r"^\s*25\s+([\d.eE+\-]+)\s+#\s*MH\s*$"), mh_GeV, rel_tol=1e-6),
        "mH2": math.isclose(number(r"^\s*9000006\s+([\d.eE+\-]+)\s+#\s*Mh2\s*$"), mH2_GeV, rel_tol=1e-6),
        "coupling": math.isclose(
            number(r"^\s*3\s+([\d.eE+\-]+)\s+#\s*GHphiphi\s*$"), expected_g, rel_tol=1e-6
        ),
        "width": math.isclose(
            number(r"^DECAY\s+9000006\s+([\d.eE+\-]+)"), float(point["total_width_GeV"]), rel_tol=1e-6
        ),
    }


def checks_pass(banner_path: Path, point: Dict[str, Any]) -> bool:
    """Convenience wrapper: True only if every banner_checks() value is True."""
    return all(banner_checks(banner_path, point).values())


def compatible(sigma_a_fb: float, unc_a_fb: float, sigma_b_fb: float, unc_b_fb: float) -> tuple[bool, float, float]:
    """3-sigma agreement check between two independent-seed cross sections.

    Returns (agreement, |difference|, combined_uncertainty). Use this to
    confirm two seeds of the same point are statistically consistent before
    averaging them into a single sigma_used_fb -- silent disagreement between
    seeds is exactly the kind of thing a copied summary value would hide.
    """
    difference = abs(float(sigma_a_fb) - float(sigma_b_fb))
    combined = math.hypot(float(unc_a_fb), float(unc_b_fb))
    return difference <= 3.0 * combined, difference, combined
