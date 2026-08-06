"""R11 Mission: MadGraph Production Mode Pilot helpers.

Contains pure functions for:
- Bin edge configurations for LHE parton-level shape observables
- Parsing LHE files (1000 events, 2 stable H2 PDG 9000006 per event)
- Computing kinematic observables (m_H2H2, pT_H2H2, pT_H2_leading, pT_H2_subleading,
  y_H2_leading, y_H2_subleading, delta_phi_H2H2, delta_R_H2H2)
- Computing normalized histograms and statistical shape diagnostics (max bin diff, chi2, KS, underflow/overflow)
- Three-run cross-section ratio R(g) and pull statistics
- Extracting cross section & error from MadGraph banner / output
- Extracting full applied run_card from MadGraph banner text
"""

from __future__ import annotations

import gzip
import math
import re
from pathlib import Path
from typing import Any, Sequence

# Canonical physical constants & baseline anchor
G0_GEV = 63.59142520075966
SIGMA0_PB = 0.000230291167568
PILOT_G_TARGETS = [40.0, 63.59142520075966, 150.0]
PILOT_SEEDS = {
    40.0: 1101,
    63.59142520075966: 1102,
    150.0: 1103,
}

# Frozen binning configuration for shape observables
OBSERVABLE_BINS: dict[str, list[float]] = {
    "m_H2H2": [250.0 + i * 25.0 for i in range(21)],  # 250 to 750 GeV (20 bins)
    "pT_H2H2": [i * 10.0 for i in range(21)],        # 0 to 200 GeV (20 bins)
    "pT_H2_leading": [i * 15.0 for i in range(21)],  # 0 to 300 GeV (20 bins)
    "pT_H2_subleading": [i * 10.0 for i in range(21)], # 0 to 200 GeV (20 bins)
    "y_H2_leading": [-3.0 + i * 0.3 for i in range(21)], # -3.0 to 3.0 (20 bins)
    "y_H2_subleading": [-3.0 + i * 0.3 for i in range(21)], # -3.0 to 3.0 (20 bins)
    "delta_phi_H2H2": [i * (math.pi / 20.0) for i in range(21)], # 0 to pi (20 bins)
    "delta_R_H2H2": [i * 0.25 for i in range(21)],  # 0 to 5.0 (20 bins)
}

# Observables expected to be kinematically degenerate at Born level (LO 2->2)
LO_2TO2_DEGENERATE_OBSERVABLES = {"pT_H2H2", "delta_phi_H2H2"}


def fmt_point_dir(g: float) -> str:
    """Format point directory name: 40.0 -> g40, 63.59142520075966 -> g63p591425, 150.0 -> g150."""
    if abs(g - 63.59142520075966) < 1e-5:
        return "g63p591425"
    s = f"{g:.6g}".replace(".", "p")
    return f"g{s}"


def calculate_g2_prediction(g: float, g0: float = G0_GEV, sigma0: float = SIGMA0_PB) -> float:
    """Analytical quadratic prediction: sigma(g) = sigma0 * (g / g0)^2."""
    return sigma0 * (g / g0) ** 2


def calculate_relative_residual(sigma_mg: float, sigma_pred: float) -> float:
    """Relative residual: (sigma_mg / sigma_pred) - 1.0."""
    if sigma_pred == 0.0:
        return 0.0
    return (sigma_mg / sigma_pred) - 1.0


def calculate_cross_section_ratio_and_pull(
    sigma_g: float,
    err_g: float,
    sigma_ref: float,
    err_ref: float,
    g: float,
    g0: float = G0_GEV,
) -> dict[str, float]:
    """Calculate direct ratio R(g), propagated error delta_R, and pull (R - 1) / delta_R.

    R(g) = [sigma_mg(g) / sigma_ref] / [(g / g0)^2]
    delta_R = R(g) * sqrt((err_g / sigma_g)^2 + (err_ref / sigma_ref)^2)
    pull = (R(g) - 1.0) / delta_R
    """
    scale_sq = (g / g0) ** 2
    if sigma_ref <= 0 or scale_sq <= 0:
        return {"R": 0.0, "delta_R": 0.0, "pull": 0.0}

    r_val = (sigma_g / sigma_ref) / scale_sq
    rel_err_g = (err_g / sigma_g) if sigma_g > 0 else 0.0
    rel_err_ref = (err_ref / sigma_ref) if sigma_ref > 0 else 0.0
    delta_r = r_val * math.sqrt(rel_err_g**2 + rel_err_ref**2)
    pull = (r_val - 1.0) / delta_r if delta_r > 0 else 0.0

    return {
        "R": r_val,
        "delta_R": delta_r,
        "pull": pull,
    }


def ks_critical_value_95(n1: int, n2: int) -> float:
    """Two-sample Kolmogorov-Smirnov critical value at alpha=0.05 level."""
    if n1 <= 0 or n2 <= 0:
        return 1.0
    return 1.36 * math.sqrt((n1 + n2) / (n1 * n2))


def parse_lhe_events(lhe_path: Path) -> list[dict[str, Any]]:
    """Parse LHE file (plain text or gzipped) and extract event records."""
    if str(lhe_path).endswith(".gz"):
        fh = gzip.open(lhe_path, "rt", encoding="utf-8", errors="replace")
    else:
        fh = open(lhe_path, "r", encoding="utf-8", errors="replace")

    events: list[dict[str, Any]] = []
    in_event = False
    lines_buffer: list[str] = []

    try:
        for line in fh:
            stripped = line.strip()
            if stripped == "<event>":
                in_event = True
                lines_buffer = []
                continue
            elif stripped == "</event>":
                in_event = False
                if lines_buffer:
                    ev = _parse_single_lhe_event(len(events) + 1, lines_buffer)
                    events.append(ev)
                continue

            if in_event:
                lines_buffer.append(line)
    finally:
        fh.close()

    return events


def _parse_single_lhe_event(idx: int, lines: list[str]) -> dict[str, Any]:
    h2_particles = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 10 and not ("." in parts[0] and len(parts) == 6):
            try:
                pdg = int(parts[0])
                status = int(parts[1])
                px = float(parts[6])
                py = float(parts[7])
                pz = float(parts[8])
                e = float(parts[9])
                m = float(parts[10])
                if pdg == 9000006 and status == 1:
                    h2_particles.append({
                        "pdg": pdg,
                        "status": status,
                        "px": px,
                        "py": py,
                        "pz": pz,
                        "E": e,
                        "m": m,
                    })
            except (ValueError, IndexError):
                continue

    return {
        "event_index": idx,
        "h2_particles": h2_particles,
    }


def compute_event_observables(h2_list: list[dict[str, float]]) -> dict[str, float]:
    """Compute 8 kinematic observables from the two final-state H2 particles."""
    if len(h2_list) < 2:
        raise ValueError(f"Expected at least 2 H2 particles, found {len(h2_list)}")

    p1 = h2_list[0]
    p2 = h2_list[1]

    pt1 = math.hypot(p1["px"], p1["py"])
    pt2 = math.hypot(p2["px"], p2["py"])

    if pt1 >= pt2:
        lead, sublead = p1, p2
        pt_lead, pt_sublead = pt1, pt2
    else:
        lead, sublead = p2, p1
        pt_lead, pt_sublead = pt2, pt1

    def rapidity(p: dict[str, float]) -> float:
        e, pz = p["E"], p["pz"]
        if e <= abs(pz):
            return 0.0
        return 0.5 * math.log((e + pz) / (e - pz))

    y_lead = rapidity(lead)
    y_sublead = rapidity(sublead)

    px_pair = p1["px"] + p2["px"]
    py_pair = p1["py"] + p2["py"]
    pz_pair = p1["pz"] + p2["pz"]
    e_pair = p1["E"] + p2["E"]

    m2_pair = e_pair**2 - (px_pair**2 + py_pair**2 + pz_pair**2)
    m_h2h2 = math.sqrt(max(0.0, m2_pair))
    pt_h2h2 = math.hypot(px_pair, py_pair)

    phi1 = math.atan2(p1["py"], p1["px"])
    phi2 = math.atan2(p2["py"], p2["px"])
    dphi = abs(phi1 - phi2)
    while dphi > math.pi:
        dphi = abs(dphi - 2.0 * math.pi)

    dy = y_lead - y_sublead
    dr = math.sqrt(dy**2 + dphi**2)

    return {
        "m_H2H2": m_h2h2,
        "pT_H2H2": pt_h2h2,
        "pT_H2_leading": pt_lead,
        "pT_H2_subleading": pt_sublead,
        "y_H2_leading": y_lead,
        "y_H2_subleading": y_sublead,
        "delta_phi_H2H2": dphi,
        "delta_R_H2H2": dr,
    }


def compute_histogram(values: Sequence[float], bin_edges: Sequence[float]) -> dict[str, Any]:
    """Compute raw and normalized histogram counts across bin_edges."""
    n_bins = len(bin_edges) - 1
    counts = [0] * n_bins
    underflow = 0
    overflow = 0

    for v in values:
        if v < bin_edges[0]:
            underflow += 1
        elif v >= bin_edges[-1]:
            overflow += 1
        else:
            for i in range(n_bins):
                if bin_edges[i] <= v < bin_edges[i + 1]:
                    counts[i] += 1
                    break

    total = len(values)
    in_range = sum(counts)
    norm_counts = [c / in_range if in_range > 0 else 0.0 for c in counts]
    underflow_frac = underflow / total if total > 0 else 0.0
    overflow_frac = overflow / total if total > 0 else 0.0

    return {
        "counts": counts,
        "normalized_counts": norm_counts,
        "underflow": underflow,
        "overflow": overflow,
        "underflow_fraction": underflow_frac,
        "overflow_fraction": overflow_frac,
        "total_events": total,
        "in_range_events": in_range,
    }


def compare_histograms(
    h1: dict[str, Any],
    h2: dict[str, Any],
) -> dict[str, float]:
    """Compute statistical shape diagnostics between two histograms using actual in-range sample sizes."""
    norm1 = h1["normalized_counts"]
    norm2 = h2["normalized_counts"]
    n1 = h1["in_range_events"]
    n2 = h2["in_range_events"]

    if len(norm1) != len(norm2):
        raise ValueError("Histogram bin counts must match length")

    diffs = [abs(p1 - p2) for p1, p2 in zip(norm1, norm2)]
    max_abs_diff = max(diffs) if diffs else 0.0

    # KS statistic on cumulative distributions
    cdf1 = 0.0
    cdf2 = 0.0
    ks_stat = 0.0
    for p1, p2 in zip(norm1, norm2):
        cdf1 += p1
        cdf2 += p2
        ks_stat = max(ks_stat, abs(cdf1 - cdf2))

    ks_crit = ks_critical_value_95(n1, n2)

    # Chi2 diagnostic using estimated sample counts
    chi2 = 0.0
    for p1, p2 in zip(norm1, norm2):
        c1 = n1 * p1
        c2 = n2 * p2
        denom = c1 + c2
        if denom > 0:
            chi2 += ((c1 - c2) ** 2) / denom

    return {
        "max_abs_diff": max_abs_diff,
        "ks_stat": ks_stat,
        "ks_critical_95": ks_crit,
        "chi2_stat": chi2,
        "n1_in_range": float(n1),
        "n2_in_range": float(n2),
    }


def extract_madgraph_xsec(banner_or_log_path: Path) -> tuple[float, float]:
    """Extract cross section (pb) and integration error (pb) from MadGraph banner or output."""
    text = banner_or_log_path.read_text(encoding="utf-8", errors="replace")

    m = re.search(r"Cross-section\s*:\s*([\d\.eE\+-]+)\s*\+-\s*([\d\.eE\+-]+)", text, re.I)
    if m:
        return float(m.group(1)), float(m.group(2))

    log_path = banner_or_log_path.parent / "madgraph_run.txt"
    if log_path.exists() and log_path != banner_or_log_path:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        m_log = re.search(r"Cross-section\s*:\s*([\d\.eE\+-]+)\s*\+-\s*([\d\.eE\+-]+)", log_text, re.I)
        if m_log:
            return float(m_log.group(1)), float(m_log.group(2))

    m_weight = re.search(r"#\s*Integrated weight \(pb\)\s*:\s*([\d\.eE\+-]+)", text)
    if m_weight:
        xsec = float(m_weight.group(1))
        return xsec, 0.0

    raise ValueError(f"Could not extract MadGraph cross section from {banner_or_log_path}")


def extract_run_card_applied_from_banner(banner_path: Path) -> str:
    """Extract full applied run_card section from banner.txt."""
    text = banner_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"<(?:MGRunCard|run_card)>\n(.*?)\n</(?:MGRunCard|run_card)>", text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not extract run card block from banner {banner_path}")
    return match.group(1).strip() + "\n"

