#!/usr/bin/env python3
"""Generate R9 threshold figures, including the official ATLAS Trackless limit."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"


def main() -> int:
    baseline = json.loads((OUTDIR / "baseline.json").read_text())
    atlas = json.loads((OUTDIR / "atlas_threshold.json").read_text())
    with open(OUTDIR / "model_reachability_scan.csv", newline="") as fh:
        scan = list(csv.DictReader(fh))

    n0 = baseline["recomputed"]["Trackless_expected_events"]
    g0 = baseline["frozen_inputs"]["g_hH2H2_GeV"]["value"]
    k_official = atlas["required_kappa_g"]
    s95 = atlas["numerical_threshold"]["observed_S95"]

    k = np.logspace(np.log10(0.5), np.log10(7.0), 500)
    events = n0 * k**2

    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.plot(k, events, lw=2.2, label=r"$N=N_0\kappa_g^2$")
    ax.scatter([1.0], [n0], s=70, zorder=4, label=f"R8 baseline: {n0:.3f} events")
    ax.axhline(s95, ls="--", lw=1.8, label=f"ATLAS observed $S^{{95}}={s95:.1f}$")
    ax.scatter([k_official], [s95], marker="s", s=70, zorder=5)
    ax.annotate(
        f"official Trackless threshold\n"
        f"$\\kappa_g={k_official:.3f}$, $|g|={k_official*g0:.1f}$ GeV",
        xy=(k_official, s95), xytext=(2.0, 8.0),
        arrowprops={"arrowstyle": "->"}, fontsize=9,
    )
    ax.axvspan(0.9999999999, 1.0000000003, alpha=0.25,
               label=r"theory-valid $M^2$ window (visually unresolved)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.5, 7.0)
    ax.set_ylim(0.05, 20.0)
    ax.set_xlabel(r"$\kappa_g=|g_{hH_2H_2}|/|g_0|$")
    ax.set_ylabel(r"expected Trackless events at 139 fb$^{-1}$")
    ax.set_title("R9: official Trackless sensitivity threshold")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTDIR / "expected_events_vs_kappa_g.png", dpi=170)
    fig.savefig(OUTDIR / "expected_events_vs_kappa_g_official.svg")
    plt.close(fig)

    valid = [r for r in scan if r["theory_ok_v1"] == "1"]
    invalid = [r for r in scan if r["theory_ok_v1"] != "1"]
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.scatter(
        [float(r["M2_GeV2"]) for r in valid],
        [float(r["kappa_g"]) for r in valid],
        label="theory-valid",
    )
    ax.scatter(
        [float(r["M2_GeV2"]) for r in invalid],
        [float(r["kappa_g"]) for r in invalid],
        marker="x", label="theory-rejected",
    )
    ax.axhline(k_official, ls="--", label=f"ATLAS threshold $\\kappa_g={k_official:.3f}$")
    ax.set_xlabel(r"$M^2$ [GeV$^2$]")
    ax.set_ylabel(r"$\kappa_g$")
    ax.set_title("Reachability in the tested fixed 2HDM slice")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUTDIR / "model_reachability_vs_threshold.png", dpi=170)
    plt.close(fig)

    print("R9 figures written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
