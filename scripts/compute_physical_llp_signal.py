#!/usr/bin/env python3
"""Combine physical MadGraph production cross section with canonical Trackless Aeff.

Implements the canonical signal combination:
    sigma_production_fb, ctau_response_mm, BR_bb
             |
             v
        Trackless Aeff(ctau)  [log-linear interpolation]
             |
             v
        sigma_4b_fb = sigma_production_fb * BR_bb^2
        sigma_visible_fb = sigma_4b_fb * Aeff
        N_expected = luminosity_fb_inv * sigma_visible_fb
             |
             v
        N_expected / S_95  (L = 139 fb^-1, S_95 = 3.0 events)
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from portable_paths import find_workspace_root  # noqa: E402

DIHIGGS_ROOT = find_workspace_root(REPO_ROOT)
CANONICAL_EFFICIENCY_CSV = Path(os.environ.get(
    "DIHIGGS_TRACKLESS_EFFICIENCY_CSV",
    str(DIHIGGS_ROOT / "hep_cross" / "results" / "r10_effective_ctau_g_br_scan" / "efficiency_vs_ctau.csv"),
))
DEFAULT_LUMINOSITY_FB_INV = 139.0
DEFAULT_S95 = 3.0


def load_canonical_trackless_curve(csv_path: Path = CANONICAL_EFFICIENCY_CSV) -> List[Tuple[float, float]]:
    """Load (ctau_mm, Trackless_Aeff) sorted by ctau."""
    points: List[Tuple[float, float]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ctau = float(row["ctau_mm"])
                aeff = float(row["Trackless_Aeff"])
                points.append((ctau, aeff))
            except (ValueError, KeyError):
                continue
    points.sort(key=lambda p: p[0])
    return points


def interpolate_aeff(ctau_mm: float, curve: List[Tuple[float, float]]) -> float:
    """Log-linear interpolation of Trackless Aeff vs ctau."""
    if not math.isfinite(ctau_mm) or ctau_mm <= 0:
        return 0.0
    if ctau_mm <= curve[0][0]:
        return curve[0][1]
    if ctau_mm >= curve[-1][0]:
        return curve[-1][1]

    log_ctau = math.log10(ctau_mm)
    for i in range(len(curve) - 1):
        c1, a1 = curve[i]
        c2, a2 = curve[i + 1]
        if c1 <= ctau_mm <= c2:
            log_c1 = math.log10(c1)
            log_c2 = math.log10(c2)
            frac = (log_ctau - log_c1) / (log_c2 - log_c1)
            return a1 + frac * (a2 - a1)
    return 0.0


def process_physical_llp_signals(
    input_csv: Path,
    output_csv: Path,
    *,
    luminosity_fb_inv: float = DEFAULT_LUMINOSITY_FB_INV,
    s95_events: float = DEFAULT_S95,
    curve_csv: Path = CANONICAL_EFFICIENCY_CSV,
) -> int:
    """Combine input MadGraph production CSV with Trackless acceptance."""
    curve = load_canonical_trackless_curve(curve_csv)

    rows_in = []
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_in = list(reader)

    required = {"sigma_production_fb", "sigma_source", "sigma_provenance", "ctau_response_mm", "BR_bb"}
    missing = sorted(required - set(rows_in[0])) if rows_in else sorted(required)
    if missing:
        raise ValueError("canonical model-point input missing required fields: " + ", ".join(missing))

    rows_out = []
    for r in rows_in:
        out = dict(r)
        try:
            sigma_prod = float(r["sigma_production_fb"])
            ctau = float(r["ctau_response_mm"])
            br_bb = float(r["BR_bb"])
        except (TypeError, ValueError):
            sigma_prod, ctau, br_bb = float("nan"), float("nan"), float("nan")

        if math.isfinite(sigma_prod) and math.isfinite(ctau) and math.isfinite(br_bb) and sigma_prod > 0:
            aeff = interpolate_aeff(ctau, curve)
            sigma_4b = sigma_prod * (br_bb ** 2)
            sigma_vis = sigma_4b * aeff
            n_expected = luminosity_fb_inv * sigma_vis
            ratio_s95 = n_expected / s95_events
            status = "EXCLUDED_BY_ATLAS_TRACKLESS_95CL" if n_expected >= s95_events else "ALLOWED_BY_ATLAS_TRACKLESS_95CL"
        else:
            aeff = float("nan")
            sigma_4b = float("nan")
            sigma_vis = float("nan")
            n_expected = float("nan")
            ratio_s95 = float("nan")
            status = "UNCLASSIFIED_INVALID_INPUT"

        out["Trackless_Aeff"] = aeff
        out["sigma_4b_fb"] = sigma_4b
        out["sigma_visible_fb"] = sigma_vis
        out["N_expected"] = n_expected
        out["N_over_S95"] = ratio_s95
        out["atlas_trackless_status"] = status
        rows_out.append(out)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows_out[0].keys()) if rows_out else []
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ro in rows_out:
            writer.writerow(ro)

    print(f"[SIGNAL] Combined {len(rows_out)} rows -> {output_csv}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine MadGraph production cross section with Trackless Aeff")
    parser.add_argument("--input", type=Path, required=True, help="Input MadGraph CSV")
    parser.add_argument("--output", type=Path, required=True, help="Output signal CSV")
    parser.add_argument("--luminosity", type=float, default=DEFAULT_LUMINOSITY_FB_INV, help="Luminosity in fb^-1")
    parser.add_argument("--s95", type=float, default=DEFAULT_S95, help="95% CL upper limit in events")
    args = parser.parse_args()

    return process_physical_llp_signals(
        args.input,
        args.output,
        luminosity_fb_inv=args.luminosity,
        s95_events=args.s95,
    )


if __name__ == "__main__":
    raise SystemExit(main())
