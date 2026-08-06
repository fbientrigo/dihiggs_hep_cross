"""R12 Mission: Six-g MadGraph Production helpers and pure functions."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from llp_recast.r11_madgraph_pilot import (
    G0_GEV,
    SIGMA0_PB,
    calculate_g2_prediction,
    calculate_relative_residual,
    extract_madgraph_xsec,
    extract_run_card_applied_from_banner,
    parse_lhe_events,
)

R12_G_TARGETS: list[float] = [
    40.0,
    63.59142520075966,
    100.0,
    150.0,
    205.09272542237372,
    300.0,
]

R12_SEEDS: list[int] = [101, 107]


def fmt_g_dir(g: float) -> str:
    """Format coupling directory name.

    40.0 -> g40
    63.59142520075966 -> g63p591425
    100.0 -> g100
    150.0 -> g150
    205.09272542237372 -> g205p092725
    300.0 -> g300
    """
    if abs(g - 63.59142520075966) < 1e-5:
        return "g63p591425"
    if abs(g - 205.09272542237372) < 1e-5:
        return "g205p092725"
    s = f"{g:.6g}".replace(".", "p")
    return f"g{s}"


def combine_inverse_variance(s1: float, e1: float, s2: float, e2: float) -> tuple[float, float]:
    """Combine two cross-section measurements using inverse-variance weighting.

    w_i = 1 / delta_sigma_i^2
    sigma_combined = sum(w_i * sigma_i) / sum(w_i)
    delta_sigma_combined = sqrt(1 / sum(w_i))
    """
    if e1 <= 0 or e2 <= 0:
        s_comb = 0.5 * (s1 + s2)
        e_comb = 0.5 * math.hypot(e1, e2)
        return s_comb, e_comb

    w1 = 1.0 / (e1**2)
    w2 = 1.0 / (e2**2)
    w_sum = w1 + w2

    s_comb = (w1 * s1 + w2 * s2) / w_sum
    e_comb = math.sqrt(1.0 / w_sum)

    return s_comb, e_comb


def validate_lhe_file(lhe_path: Path, expected_events: int = 1000) -> dict[str, Any]:
    """Validate LHE file for completeness and expected particle structure."""
    if not lhe_path.exists():
        return {"valid": False, "event_count": 0, "error": f"File does not exist: {lhe_path}"}

    events = parse_lhe_events(lhe_path)
    n_events = len(events)
    if n_events != expected_events:
        return {
            "valid": False,
            "event_count": n_events,
            "error": f"Expected {expected_events} events, found {n_events}",
        }

    for ev in events:
        h2_parts = ev["h2_particles"]
        if len(h2_parts) != 2:
            return {
                "valid": False,
                "event_count": n_events,
                "error": f"Event {ev['event_index']} has {len(h2_parts)} H2 particles (expected 2)",
            }
        for h2 in h2_parts:
            if h2["pdg"] != 9000006:
                return {
                    "valid": False,
                    "event_count": n_events,
                    "error": f"Event {ev['event_index']} H2 has PDG {h2['pdg']} (expected 9000006)",
                }
            if abs(h2["m"] - 150.0) > 1.0:
                return {
                    "valid": False,
                    "event_count": n_events,
                    "error": f"Event {ev['event_index']} H2 has mass {h2['m']} (expected ~150.0)",
                }

    return {
        "valid": True,
        "event_count": n_events,
        "error": None,
    }


def validate_banner_file(
    banner_path: Path,
    expected_g: float,
    expected_seed: int,
    expected_beam_energy: float = 6500.0,
    expected_lhaid: int = 230000,
) -> dict[str, Any]:
    """Validate banner text for correct param_card (GHphiphi) and run_card settings."""
    if not banner_path.exists():
        return {"valid": False, "error": f"Banner does not exist: {banner_path}"}

    text = banner_path.read_text(encoding="utf-8", errors="replace")

    # Verify seed
    m_seed = re.search(r"^\s*(\d+)\s*=\s*iseed\b", text, re.MULTILINE)
    if not m_seed or int(m_seed.group(1)) != expected_seed:
        actual_seed = int(m_seed.group(1)) if m_seed else None
        return {
            "valid": False,
            "error": f"Seed mismatch: expected {expected_seed}, found {actual_seed}",
        }

    # Verify beam energy
    m_ebeam1 = re.search(r"^\s*([\d\.]+)\s*=\s*ebeam1\b", text, re.MULTILINE)
    m_ebeam2 = re.search(r"^\s*([\d\.]+)\s*=\s*ebeam2\b", text, re.MULTILINE)
    if not m_ebeam1 or not m_ebeam2 or float(m_ebeam1.group(1)) != expected_beam_energy or float(m_ebeam2.group(1)) != expected_beam_energy:
        return {
            "valid": False,
            "error": f"Beam energy mismatch: expected {expected_beam_energy}",
        }

    # Verify LHAPDF ID
    m_lhaid = re.search(r"^\s*(\d+)\s*=\s*lhaid\b", text, re.MULTILINE)
    if not m_lhaid or int(m_lhaid.group(1)) != expected_lhaid:
        return {
            "valid": False,
            "error": f"LHAPDF ID mismatch: expected {expected_lhaid}",
        }

    # Verify GHphiphi in FRBlock 3
    target_ghphiphi = -abs(expected_g)
    m_gh = re.search(r"^\s*3\s+([\d\.eE\+-]+)\s*#\s*GHphiphi", text, re.MULTILINE)
    if m_gh:
        actual_gh = float(m_gh.group(1))
        if abs(actual_gh - target_ghphiphi) > 1e-4:
            return {
                "valid": False,
                "error": f"GHphiphi mismatch: expected {target_ghphiphi}, found {actual_gh}",
            }

    return {
        "valid": True,
        "error": None,
    }


def sha256_file(path: Path) -> str:
    """Compute sha256 hash of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()
