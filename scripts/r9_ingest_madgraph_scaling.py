#!/usr/bin/env python3
"""Ingest real MadGraph results into the R9 coupling-scaling table and fit p.

The R9 session could not run MadGraph (every distribution host is denied by the
egress policy), so ``madgraph_coupling_scaling.csv`` ships with empty measured
columns.  An operator with MadGraph access runs
``results/r9_h2_sensitivity_threshold/madgraph_deck/run_commands.sh`` and then
feeds the resulting cross sections here.

Input CSV must have columns ``kappa_g``, ``sigma_pb``, ``integration_error_pb``
and optionally ``log``.  This script fills the measured columns, computes the
residuals against kappa^2, fits the exponent p by weighted least squares in
log-log space, and rewrites ``madgraph_scaling_fit.json`` with the empirical
result beside the structural one.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"

#: Declared numerical tolerance added in quadrature to the MC integration error
#: when deciding whether a residual from kappa^2 is acceptable.
NUMERICAL_TOLERANCE = 1e-3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fit_exponent(points: list[dict]) -> dict:
    """Weighted least-squares fit of ln(sigma/sigma0) = p * ln(kappa).

    The kappa = 1 point defines sigma0 and carries no information about p, so it
    is used as the normalisation and excluded from the fit rows.
    """
    base = next((p for p in points if abs(p["kappa_g"] - 1.0) < 1e-12), None)
    if base is None:
        raise SystemExit("the scaling table must contain a kappa_g = 1.0 point")
    sigma0 = base["sigma_pb"]
    err0 = base["integration_error_pb"]
    rel0 = err0 / sigma0

    xs, ys, ws = [], [], []
    for p in points:
        if p is base:
            continue
        ratio = p["sigma_pb"] / sigma0
        rel = math.hypot(p["integration_error_pb"] / p["sigma_pb"], rel0)
        xs.append(math.log(p["kappa_g"]))
        ys.append(math.log(ratio))
        ws.append(1.0 / (rel * rel))

    if len(xs) < 2:
        raise SystemExit("need at least two non-unit kappa points to fit p")

    sxx = sum(w * x * x for w, x in zip(ws, xs))
    sxy = sum(w * x * y for w, x, y in zip(ws, xs, ys))
    p_hat = sxy / sxx
    p_err = math.sqrt(1.0 / sxx)
    return {"p": p_hat, "p_uncertainty": p_err, "sigma_baseline_pb": sigma0, "n_fit_points": len(xs)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path,
                        help="CSV with kappa_g, sigma_pb, integration_error_pb[, log]")
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    args = parser.parse_args()

    with open(args.results, newline="") as fh:
        measured = [
            {
                "kappa_g": float(r["kappa_g"]),
                "sigma_pb": float(r["sigma_pb"]),
                "integration_error_pb": float(r["integration_error_pb"]),
                "log": r.get("log", ""),
            }
            for r in csv.DictReader(fh)
        ]
    by_kappa = {round(m["kappa_g"], 9): m for m in measured}

    scaling_csv = args.outdir / "madgraph_coupling_scaling.csv"
    with open(scaling_csv, newline="") as fh:
        rows = list(csv.DictReader(fh))
        fieldnames = list(rows[0].keys())

    fit = fit_exponent(measured)
    sigma0 = fit["sigma_baseline_pb"]

    residual_report = []
    for row in rows:
        kappa = round(float(row["kappa_g"]), 9)
        m = by_kappa.get(kappa)
        if m is None:
            continue
        ratio = m["sigma_pb"] / sigma0
        expected = kappa * kappa
        residual = ratio / expected - 1.0
        rel_unc = math.hypot(
            m["integration_error_pb"] / m["sigma_pb"],
            by_kappa[1.0]["integration_error_pb"] / sigma0,
        )
        allowed = math.hypot(rel_unc, NUMERICAL_TOLERANCE)
        row["sigma_pb"] = f"{m['sigma_pb']:.17e}"
        row["integration_error_pb"] = f"{m['integration_error_pb']:.17e}"
        row["sigma_over_sigma_baseline"] = f"{ratio:.17e}"
        row["relative_residual"] = f"{residual:.6e}"
        row["log"] = m["log"]
        row["sha256"] = sha256_file(Path(m["log"])) if m["log"] and Path(m["log"]).exists() else ""
        row["status"] = "MEASURED"
        residual_report.append({
            "kappa_g": kappa, "relative_residual": residual,
            "allowed": allowed, "compatible": abs(residual) <= allowed,
        })

    with open(scaling_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, lineterminator="\n", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    fit_path = args.outdir / "madgraph_scaling_fit.json"
    payload = json.loads(fit_path.read_text())
    compatible_with_two = abs(fit["p"] - 2.0) <= 3.0 * fit["p_uncertainty"]
    all_residuals_ok = all(r["compatible"] for r in residual_report)
    payload["empirical_fit"] = {
        "fitted_exponent_p": fit["p"],
        "exponent_uncertainty": fit["p_uncertainty"],
        "n_fit_points": fit["n_fit_points"],
        "method": "weighted least squares on ln(sigma/sigma0) vs ln(kappa_g)",
        "declared_numerical_tolerance": NUMERICAL_TOLERANCE,
        "residuals_vs_kappa_squared": residual_report,
        "p_compatible_with_2_at_3sigma": compatible_with_two,
        "all_residuals_compatible": all_residuals_ok,
        "quadratic_scaling": "PASS" if (compatible_with_two and all_residuals_ok) else "FAIL",
        "source_results_csv": str(args.results),
        "source_results_sha256": sha256_file(args.results),
    }
    payload["empirical_fit_status"] = "MEASURED"
    if not (compatible_with_two and all_residuals_ok):
        payload["empirical_fit"]["action_required"] = (
            "Quadratic scaling failed empirically. Do NOT apply an analytic square-root "
            "extrapolation: rebuild the thresholds from the measured interpolation and "
            "explain the cause (check for a GHphiphi-dependent width or an extra diagram)."
        )
    fit_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"p = {fit['p']:.6f} +/- {fit['p_uncertainty']:.6f}  "
          f"({'PASS' if compatible_with_two and all_residuals_ok else 'FAIL'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
