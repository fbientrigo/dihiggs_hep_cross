#!/usr/bin/env python3
"""R9 Iteration 2: bounded, one-dimensional model-derived reachability scan.

Drives the canonical 2HDMC evaluator
``fbientrigo/dihiggs:benchmarks/check_H2scan_mH150_tb300000.cpp`` (which calls
``THDM::set_param_phys`` directly with an externally supplied ``m12_2``) and
answers two questions with measurements rather than assumptions:

1. **Which single input coordinate controls ``g_hH2H2``?**  A sensitivity probe
   varies each candidate independently and records d|g|/dx.  Its output is
   ``coordinate_selection.json``.

2. **How far can that coordinate move before the benchmark stops being a valid
   2HDM point?**  A bounded scan of at most seven points (baseline included)
   records the theory predicates, the coupling, the width, ctau and every
   material branching ratio at each point -- never inherited from the baseline.

The evaluator is treated as read-only: nothing in ``dihiggs`` is modified and
all build products live outside the checkouts.

Usage::

    python3 scripts/r9_run_model_scan.py --evaluator /path/to/check_h2 \\
        --outdir results/r9_h2_sensitivity_threshold
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from llp_recast.r9_threshold import (  # noqa: E402
    acceptance_reuse_label,
    kappa_from_coupling,
    model_point_expected_events,
    relative_ctau_change,
    visible_sigma_fb,
)

# ---------------------------------------------------------------------------
# Frozen construction of benchmark H2scan_mH150_tb300000.
# Source: fbientrigo/dihiggs benchmarks/H2scan_mH150_tb300000_production_coupling.json
# ---------------------------------------------------------------------------
MH_GEV = 125.13
MH2_GEV = 150.0
MA_GEV = 450.0
MHP_GEV = 450.0
SBA = 1.0
LAMBDA6 = 1e-10
LAMBDA7 = 0.0
TAN_BETA = 300000.0
M12_SQ_BASELINE = 7.49999999996479594e-02

# Frozen R8 quantities the yield estimate reuses.
BASELINE_SIGMA_PB = 0.000230291167568
BASELINE_ABS_G_GEV = 63.5914252007596588
BASELINE_CTAU_MM = 4.32622152973311191
TRACKLESS_A_EFF = 0.01573386
LUMI_FB_INV = 139.0

# Perturbativity envelope used to bound the lambda1 re-parameterisation.
LAMBDA1_PERTURBATIVE_LIMIT = 4.0 * math.pi

SIN_BETA = TAN_BETA / math.sqrt(1.0 + TAN_BETA * TAN_BETA)
COS_BETA = 1.0 / math.sqrt(1.0 + TAN_BETA * TAN_BETA)
SIN_COS_BETA = SIN_BETA * COS_BETA


def m2_from_m12sq(m12_sq: float) -> float:
    """M^2 = m12^2 / (sin beta cos beta), the construction coordinate."""
    return m12_sq / SIN_COS_BETA


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Evaluator:
    """Thin, caching wrapper around the canonical 2HDMC check binary."""

    def __init__(self, binary: Path):
        self.binary = Path(binary)
        if not self.binary.exists():
            raise SystemExit(f"evaluator binary not found: {self.binary}")
        self._cache: dict[tuple, dict] = {}
        self.calls = 0

    def __call__(self, m12_sq: float, lambda6: float = LAMBDA6, tan_beta: float = TAN_BETA) -> dict:
        key = (repr(m12_sq), repr(lambda6), repr(tan_beta))
        if key in self._cache:
            return self._cache[key]
        argv = [
            str(self.binary),
            repr(MH_GEV), repr(MH2_GEV), repr(MA_GEV), repr(MHP_GEV),
            repr(SBA), repr(lambda6), repr(LAMBDA7), repr(m12_sq), repr(tan_beta),
        ]
        proc = subprocess.run(argv, capture_output=True, text=True)
        self.calls += 1
        if proc.returncode != 0:
            raise SystemExit(f"evaluator failed ({proc.returncode}): {proc.stderr.strip()}")
        tokens = proc.stdout.strip().split(",")
        record = dict(zip(tokens[0::2], tokens[1::2]))
        self._cache[key] = record
        return record


def g_hH2H2(record: dict) -> float:
    """g_hH2H2 in GeV from the 2HDMC complex coupling.

    2HDMC returns ``c = -i*g``; the production artifact fixes
    ``g_hH2H2 = -Im(c)``.  The sign is physical and flips as M^2 crosses the
    cancellation point; sigma depends on the magnitude only.
    """
    return -float(record["g_h1h2h2_imag_gev"])


def theory_flags(record: dict) -> dict:
    construction_ok = int(record.get("construction_ok", "0"))
    if not construction_ok:
        return {
            "construction_ok": 0, "numerical_ok": 0, "positivity_ok": 0,
            "unitarity_ok": 0, "perturbativity_ok": 0, "theory_ok_v1": 0,
        }
    positivity = int(record["positivity_ok"])
    unitarity = int(record["unitarity_ok"])
    perturbativity = int(record["perturbativity_ok"])
    # numerical_ok: every published quantity must be finite and the widths
    # strictly positive, otherwise the point cannot be interpreted.
    numeric_fields = (
        "lambda1_reconstructed", "total_width_gev", "ctau_mm", "br_bb",
        "g_h1h2h2_imag_gev",
    )
    numerical_ok = 1
    for field in numeric_fields:
        value = float(record[field])
        if not math.isfinite(value):
            numerical_ok = 0
    if float(record["total_width_gev"]) <= 0.0 or float(record["ctau_mm"]) <= 0.0:
        numerical_ok = 0
    return {
        "construction_ok": 1,
        "numerical_ok": numerical_ok,
        "positivity_ok": positivity,
        "unitarity_ok": unitarity,
        "perturbativity_ok": perturbativity,
        "theory_ok_v1": int(bool(numerical_ok and positivity and unitarity and perturbativity)),
    }


def is_theory_valid(evaluate: Evaluator, m12_sq: float) -> bool:
    return theory_flags(evaluate(m12_sq))["theory_ok_v1"] == 1


def bisect_validity_edge(evaluate: Evaluator, *, direction: int, max_rel: float = 1.0) -> float:
    """Largest |relative offset| from the baseline m12^2 that stays theory-valid.

    ``direction`` is +1 (increase m12^2) or -1 (decrease it).  Returns the
    relative offset of the last valid point found.
    """
    def valid(rel: float) -> bool:
        return is_theory_valid(evaluate, M12_SQ_BASELINE * (1.0 + direction * rel))

    if not valid(0.0):
        raise SystemExit("baseline point is not theory-valid; refusing to scan")
    lo, hi = 0.0, None
    probe = 1e-15
    while probe <= max_rel:
        if valid(probe):
            lo = probe
            probe *= 10.0
        else:
            hi = probe
            break
    if hi is None:
        return lo
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        if valid(mid):
            lo = mid
        else:
            hi = mid
    return lo


def validity_edge_cause(evaluate: Evaluator, *, direction: int, edge_rel: float) -> dict:
    """Report which predicate actually fails just past a validity edge.

    Measured rather than asserted: evaluate immediately outside the edge and
    name the flags that flipped, together with the lambda1 values on both sides.
    """
    inside = evaluate(M12_SQ_BASELINE * (1.0 + direction * edge_rel))
    outside = evaluate(M12_SQ_BASELINE * (1.0 + direction * edge_rel * 1.05))
    fi, fo = theory_flags(inside), theory_flags(outside)
    predicates = ("construction_ok", "numerical_ok", "positivity_ok",
                  "unitarity_ok", "perturbativity_ok")
    flipped = [p for p in predicates if fi[p] == 1 and fo[p] == 0]
    return {
        "direction": "increasing m12_sq" if direction > 0 else "decreasing m12_sq",
        "edge_relative_offset": edge_rel,
        "first_failing_predicates": flipped,
        "lambda1_inside_edge": float(inside["lambda1_reconstructed"]),
        "lambda1_outside_edge": float(outside["lambda1_reconstructed"]),
        "flags_inside": fi,
        "flags_outside": fo,
    }


def solve_m12sq_for_kappa(evaluate: Evaluator, target_kappa: float) -> float:
    """Find m12^2 on the increasing-M^2 branch giving |g|/|g0| = target_kappa.

    |g| grows without bound as M^2 increases, so the branch is monotonic in
    |g| once past the sign flip.  Bracket, then bisect on |g|.
    """
    def abs_kappa(m12_sq: float) -> float:
        return kappa_from_coupling(g_hH2H2(evaluate(m12_sq)), BASELINE_ABS_G_GEV)

    lo = M12_SQ_BASELINE
    hi = M12_SQ_BASELINE * 2.0
    for _ in range(80):
        if abs_kappa(hi) >= target_kappa:
            break
        hi *= 2.0
    else:
        raise SystemExit(f"could not bracket kappa={target_kappa}")
    # The sign flip sits between lo and hi; restrict to the monotone piece by
    # first walking lo up to where |g| already exceeds the baseline magnitude.
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if abs_kappa(mid) < target_kappa:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 1e-18 * max(abs(hi), 1.0):
            break
    return hi


def point_record(evaluate: Evaluator, m12_sq: float, point_id: str, role: str) -> dict:
    raw = evaluate(m12_sq)
    flags = theory_flags(raw)
    if not flags["construction_ok"]:
        return {
            "point_id": point_id, "role": role,
            "m12_sq_GeV2": f"{m12_sq:.17e}", "M2_GeV2": f"{m2_from_m12sq(m12_sq):.17e}",
            "m12_sq_over_baseline": f"{m12_sq / M12_SQ_BASELINE:.17e}",
            **flags,
        }
    g = g_hH2H2(raw)
    kappa = kappa_from_coupling(g, BASELINE_ABS_G_GEV)
    ctau = float(raw["ctau_mm"])
    br_bb = float(raw["br_bb"])
    # A point that fails the theory predicates is not a 2HDM prediction: its
    # quartics are far outside the perturbative regime, so the loop-induced
    # widths (and hence ctau and every BR) are numerical artefacts of an
    # invalid Lagrangian.  They are recorded for transparency but must never
    # be read as physics.
    yield_status = (
        "PHYSICAL" if flags["theory_ok_v1"] == 1
        else "THEORY_INVALID_DERIVED_OBSERVABLES_NOT_PHYSICAL"
    )
    br_bb_sq = br_bb * br_bb
    # sigma scales exactly with kappa^2 (structural result, Iteration 1).
    sigma_pb = BASELINE_SIGMA_PB * kappa * kappa
    vis_fb = visible_sigma_fb(sigma_pb, br_bb_sq, TRACKLESS_A_EFF)
    events = model_point_expected_events(
        sigma_pb=sigma_pb, br_bb_squared=br_bb_sq,
        a_eff=TRACKLESS_A_EFF, luminosity_fb_inverse=LUMI_FB_INV,
    )
    return {
        "point_id": point_id,
        "role": role,
        "m12_sq_GeV2": f"{m12_sq:.17e}",
        "M2_GeV2": f"{m2_from_m12sq(m12_sq):.17e}",
        "m12_sq_over_baseline": f"{m12_sq / M12_SQ_BASELINE:.17e}",
        **flags,
        "lambda1_reconstructed": raw["lambda1_reconstructed"],
        "g_hH2H2_GeV": f"{g:.17e}",
        "abs_g_hH2H2_GeV": f"{abs(g):.17e}",
        "kappa_g": f"{kappa:.17e}",
        "total_width_GeV": raw["total_width_gev"],
        "ctau_mm": f"{ctau:.17e}",
        "ctau_relative_change": f"{relative_ctau_change(ctau, BASELINE_CTAU_MM):.6e}",
        "BR_bb": f"{br_bb:.17e}",
        "BR_bb_squared": f"{br_bb_sq:.17e}",
        "BR_gg": raw["br_gg"],
        "BR_tautau": raw["br_tautau"],
        "BR_gammagamma": raw["br_gammagamma"],
        "BR_Zgamma": raw["br_Zgamma"],
        "sigma_H2H2_pb": f"{sigma_pb:.17e}",
        "visible_sigma_fb": f"{vis_fb:.17e}",
        "expected_trackless_events_139fb": f"{events:.17e}",
        "acceptance_label": acceptance_reuse_label(ctau, BASELINE_CTAU_MM),
        "yield_status": yield_status,
    }


def run_coordinate_probe(evaluate: Evaluator) -> dict:
    """Measure d|g|/dx for every candidate control coordinate."""
    baseline = evaluate(M12_SQ_BASELINE)
    g0 = g_hH2H2(baseline)

    # --- candidate 1: m12_sq (equivalently M^2) -----------------------------
    m12_samples = []
    for rel in (1e-12, 1e-9, 1e-6, 1e-3, 1e-1, 1.0):
        m12 = M12_SQ_BASELINE * (1.0 + rel)
        rec = evaluate(m12)
        m12_samples.append({
            "relative_offset": rel,
            "m12_sq_GeV2": m12,
            "M2_GeV2": m2_from_m12sq(m12),
            "lambda1_reconstructed": float(rec["lambda1_reconstructed"]),
            "g_hH2H2_GeV": g_hH2H2(rec),
            "kappa_g": kappa_from_coupling(g_hH2H2(rec), BASELINE_ABS_G_GEV),
            "theory_ok_v1": theory_flags(rec)["theory_ok_v1"],
        })
    big = m12_samples[-1]
    d_abs_g_d_m12 = (abs(big["g_hH2H2_GeV"]) - abs(g0)) / (big["m12_sq_GeV2"] - M12_SQ_BASELINE)

    # --- candidate 2: lambda6 ----------------------------------------------
    l6_samples = []
    for l6 in (1e-10, 1e-8, 1e-6, 1e-4, 1e-2, 1.0):
        rec = evaluate(M12_SQ_BASELINE, lambda6=l6)
        l6_samples.append({
            "lambda6": l6,
            "lambda1_reconstructed": float(rec["lambda1_reconstructed"]),
            "g_hH2H2_GeV": g_hH2H2(rec),
            "kappa_g": kappa_from_coupling(g_hH2H2(rec), BASELINE_ABS_G_GEV),
            "ctau_mm": float(rec["ctau_mm"]),
            "theory_ok_v1": theory_flags(rec)["theory_ok_v1"],
        })
    l6_kappa_span = max(s["kappa_g"] for s in l6_samples) - min(s["kappa_g"] for s in l6_samples)

    # --- candidate 3: lambda1_target ---------------------------------------
    # lambda1 is a re-parameterisation of m12_sq: 2HDMC inverts
    #   m12_2 = (mH^2 ca^2 + mh^2 sa^2 - v^2 cb^2 (l1 + 1.5 l6 tb - 0.5 l7 tb^3)) / tb
    # so d m12_sq / d lambda1 = -v^2 cb^2 / tb.  Map the entire perturbative
    # lambda1 window onto m12_sq and measure the induced |g| span directly.
    lam1_baseline = float(baseline["lambda1_reconstructed"])
    slope = None
    probe_rel = 1e-9
    rec_probe = evaluate(M12_SQ_BASELINE * (1.0 + probe_rel))
    d_lambda1 = float(rec_probe["lambda1_reconstructed"]) - lam1_baseline
    if d_lambda1 != 0.0:
        slope = (M12_SQ_BASELINE * probe_rel) / d_lambda1  # d m12_sq / d lambda1
    lam1_samples = []
    if slope is not None:
        for lam1_target in (-LAMBDA1_PERTURBATIVE_LIMIT, 0.0, lam1_baseline, LAMBDA1_PERTURBATIVE_LIMIT):
            m12 = M12_SQ_BASELINE + slope * (lam1_target - lam1_baseline)
            rec = evaluate(m12)
            lam1_samples.append({
                "lambda1_target": lam1_target,
                "lambda1_reconstructed": float(rec["lambda1_reconstructed"]),
                "m12_sq_GeV2": m12,
                "g_hH2H2_GeV": g_hH2H2(rec),
                "kappa_g": kappa_from_coupling(g_hH2H2(rec), BASELINE_ABS_G_GEV),
                "theory_ok_v1": theory_flags(rec)["theory_ok_v1"],
            })
    lam1_kappa_span = (
        max(s["kappa_g"] for s in lam1_samples) - min(s["kappa_g"] for s in lam1_samples)
        if lam1_samples else 0.0
    )

    return {
        "schema": "hep_cross.r9.coordinate_selection.v1",
        "question": "Which single 2HDM input coordinate most directly changes g_hH2H2?",
        "method": "numeric perturbation of each candidate through the canonical 2HDMC evaluator",
        "baseline": {
            "m12_sq_GeV2": M12_SQ_BASELINE,
            "M2_GeV2": m2_from_m12sq(M12_SQ_BASELINE),
            "lambda1_reconstructed": lam1_baseline,
            "g_hH2H2_GeV": g0,
        },
        "candidates": {
            "m12_sq": {
                "enters_g_hH2H2": True,
                "mechanism": (
                    "g_hH2H2 = [2 (mH2^2 - M^2) + mh^2] / v with M^2 = m12^2/(sb cb); "
                    "m12^2 is the only input that moves M^2 at fixed masses and tan beta"
                ),
                "d_abs_g_d_m12sq_GeV_per_GeV2": d_abs_g_d_m12,
                "samples": m12_samples,
            },
            "lambda6": {
                "enters_g_hH2H2": False,
                "kappa_g_span_over_10_decades": l6_kappa_span,
                "mechanism": (
                    "lambda6 shifts lambda1 through -1.5*lambda6*tan(beta) but does not enter "
                    "the h-H2-H2 trilinear at exact alignment; it does move ctau at large values"
                ),
                "samples": l6_samples,
            },
            "lambda1_target": {
                "enters_g_hH2H2": "only as a re-parameterisation of m12_sq",
                "d_m12sq_d_lambda1_GeV2": slope,
                "kappa_g_span_over_full_perturbative_window": lam1_kappa_span,
                "perturbative_window": [-LAMBDA1_PERTURBATIVE_LIMIT, LAMBDA1_PERTURBATIVE_LIMIT],
                "samples": lam1_samples,
            },
        },
        "selected_coordinate": "m12_sq (equivalently M2 = m12_sq / (sin beta cos beta))",
        "selection_reason": (
            "Measured, not assumed: lambda6 leaves kappa_g unchanged to the printed precision "
            "across ten decades, and the entire perturbative lambda1 window maps onto an m12_sq "
            "interval whose kappa_g span is negligible. m12_sq is the only coordinate with a "
            "non-vanishing d|g|/dx at fixed mH2, mA, mHp, sin(beta-alpha) and tan beta."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--evaluator-source", type=Path, default=None)
    parser.add_argument("--lib2hdmc", type=Path, default=None)
    args = parser.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    evaluate = Evaluator(args.evaluator)

    # ---- gate: the rebuilt evaluator must reproduce the frozen baseline ----
    base = evaluate(M12_SQ_BASELINE)
    gate = {
        "g_hH2H2_GeV": (g_hH2H2(base), BASELINE_ABS_G_GEV),
        "ctau_mm": (float(base["ctau_mm"]), BASELINE_CTAU_MM),
        "BR_bb": (float(base["br_bb"]), 0.756737485808578692),
        "total_width_GeV": (float(base["total_width_gev"]), 4.56118529862185007e-14),
    }
    gate_report = {}
    for name, (got, want) in gate.items():
        rel = abs(got - want) / abs(want)
        gate_report[name] = {"computed": got, "frozen": want, "relative_difference": rel}
        if rel > 1e-14:
            raise SystemExit(f"BASELINE GATE FAILED for {name}: {got!r} vs frozen {want!r}")

    probe = run_coordinate_probe(evaluate)
    probe["baseline_gate"] = gate_report
    (outdir / "coordinate_selection.json").write_text(
        json.dumps(probe, indent=2) + "\n", encoding="utf-8"
    )

    # ---- bounded scan: at most 7 points including the baseline -------------
    up_edge = bisect_validity_edge(evaluate, direction=+1)
    down_edge = bisect_validity_edge(evaluate, direction=-1)

    points = [
        (M12_SQ_BASELINE, "R9_P1_baseline", "frozen R8 benchmark"),
        (M12_SQ_BASELINE * (1.0 + up_edge), "R9_P2_valid_edge_up",
         "largest theory-valid m12_sq (M^2 increasing branch)"),
        (M12_SQ_BASELINE * (1.0 - down_edge), "R9_P3_valid_edge_down",
         "smallest theory-valid m12_sq (M^2 decreasing branch)"),
    ]
    kappa_targets = [
        (1.20, "R9_P4_kappa_1p20", "intermediate coupling target"),
        (1.50, "R9_P5_kappa_1p50", "intermediate coupling target"),
        (None, "R9_P6_kappa_N1", "kappa_g for the 1-event illustrative threshold"),
        (None, "R9_P7_kappa_N10", "kappa_g for the 10-event illustrative threshold"),
    ]
    # The N=1 and N=10 kappa values come from the frozen baseline yield.
    baseline_events = model_point_expected_events(
        sigma_pb=BASELINE_SIGMA_PB, br_bb_squared=float(base["br_bb"]) ** 2,
        a_eff=TRACKLESS_A_EFF, luminosity_fb_inverse=LUMI_FB_INV,
    )
    kappa_targets[2] = (math.sqrt(1.0 / baseline_events), kappa_targets[2][1], kappa_targets[2][2])
    kappa_targets[3] = (math.sqrt(10.0 / baseline_events), kappa_targets[3][1], kappa_targets[3][2])

    for kappa, pid, role in kappa_targets:
        points.append((solve_m12sq_for_kappa(evaluate, kappa), pid, f"{role} (kappa_g={kappa:.6f})"))

    if len(points) > 7:
        raise SystemExit(f"scan budget exceeded: {len(points)} points")

    rows = [point_record(evaluate, m12, pid, role) for m12, pid, role in points]
    fieldnames = list(rows[0].keys())
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    csv_path = outdir / "model_reachability_scan.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, lineterminator="\n", fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    valid = [r for r in rows if r.get("theory_ok_v1") == 1]
    meta = {
        "schema": "hep_cross.r9.model_scan_provenance.v1",
        "evaluator_binary": str(args.evaluator),
        "evaluator_binary_sha256": sha256_file(args.evaluator),
        "evaluator_source": str(args.evaluator_source) if args.evaluator_source else None,
        "evaluator_source_sha256": sha256_file(args.evaluator_source) if args.evaluator_source else None,
        "lib2hdmc_sha256": sha256_file(args.lib2hdmc) if args.lib2hdmc else None,
        "evaluator_calls": evaluate.calls,
        "varied_coordinate": "m12_sq (M2 = m12_sq / (sin beta cos beta))",
        "fixed_inputs": {
            "mh_GeV": MH_GEV, "mH2_GeV": MH2_GEV, "mA_GeV": MA_GEV, "mHp_GeV": MHP_GEV,
            "sin_beta_minus_alpha": SBA, "lambda6": LAMBDA6, "lambda7": LAMBDA7,
            "tan_beta": TAN_BETA, "yukawa_type": "Type I",
        },
        "scan_points": len(rows),
        "scan_budget": 7,
        "theory_valid_points": len(valid),
        "theory_valid_kappa_max": max((float(r["kappa_g"]) for r in valid), default=None),
        "theory_valid_kappa_min": min((float(r["kappa_g"]) for r in valid), default=None),
        "theory_valid_ctau_mm_range": [
            min((float(r["ctau_mm"]) for r in valid), default=None),
            max((float(r["ctau_mm"]) for r in valid), default=None),
        ],
        "theory_valid_br_bb_range": [
            min((float(r["BR_bb"]) for r in valid), default=None),
            max((float(r["BR_bb"]) for r in valid), default=None),
        ],
        "theory_validity_boundary_cause": {
            "method": "measured by evaluating just outside each edge and recording which flags flip",
            "increasing_m12_sq": validity_edge_cause(evaluate, direction=+1, edge_rel=up_edge),
            "decreasing_m12_sq": validity_edge_cause(evaluate, direction=-1, edge_rel=down_edge),
        },
        "theory_validity_edge_relative_offset_up": up_edge,
        "theory_validity_edge_relative_offset_down": down_edge,
        "baseline_gate": gate_report,
    }
    (outdir / "model_scan_provenance.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {csv_path} ({len(rows)} points, {len(valid)} theory-valid)")
    print(f"evaluator calls: {evaluate.calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
