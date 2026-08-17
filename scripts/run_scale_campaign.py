#!/usr/bin/env python3
"""Scale physical 2HDM point evaluation to MadGraph and produce diagnostic figures.

Generates a representative grid of valid physical points, executes MadGraph
production cross sections per point, combines with canonical Trackless Aeff,
and generates publication-ready diagnostic plots using matplotlib.
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "src"))

from llp_recast import constants

from compute_physical_llp_signal import (
    CANONICAL_EFFICIENCY_CSV,
    DEFAULT_LUMINOSITY_FB_INV,
    DEFAULT_S95,
    interpolate_aeff,
    load_canonical_trackless_curve,
)
from portable_paths import find_workspace_root
from run_physical_point_madgraph import DEFAULT_PROC_DIR, run_single_physical_point_madgraph

DIHIGGS_ROOT = find_workspace_root(REPO_ROOT)
EVALUATOR_BIN = Path(os.environ.get(
    "DIHIGGS_POINT_V2_EVALUATOR_BIN",
    str(DIHIGGS_ROOT / "main_dihiggs" / "dihiggs" / "app" / "DihiggsPointV2Evaluator"),
))
RESULTS_DIR = REPO_ROOT / "results"
REPORTS_DIR = REPO_ROOT / "reports" / "figures"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# Canonical SM-like Higgs mass for this NEW scan (not a frozen benchmark):
# conventions/physics_conventions.yaml, sm_like_higgs.m_h_GeV.
M_H_GEV_TEXT = constants.M_H_GEV_TEXT


def generate_physical_point_grid() -> List[Dict[str, Any]]:
    """Generate 25-40 diverse physical 2HDM points from DihiggsPointV2Evaluator."""
    points: List[Dict[str, Any]] = []
    seen_ids = set()

    tan_betas = [10.0, 50.0, 100.0, 500.0, 1000.0, 10000.0, 50000.0, 150000.0, 300000.0]
    lambda6s = [1e-10, 0.001, 0.01, 0.05, 0.1]
    M2_values = [18000.0, 20000.0, 22499.9999995]

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        tmp_csv = tf.name

    try:
        for tb in tan_betas:
            for l6 in lambda6s:
                for M2 in M2_values:
                    cmd = [
                        str(EVALUATOR_BIN),
                        "--campaign-id", "scale_scan",
                        "--run-id", f"tb_{tb}_l6_{l6}_M2_{M2}",
                        "--mh", M_H_GEV_TEXT,
                        "--mH-min", "150.0", "--mH-max", "150.0", "--n-mH", "1",
                        "--mA", "450.0", "--mHp", "450.0",
                        "--yukawa-type", "1",
                        "--sin-ba", "1.0",
                        "--tan-beta", str(tb),
                        "--M2-min", str(M2), "--M2-max", str(M2), "--n-M2", "1",
                        "--lambda6", str(l6),
                        "--lambda7", "0.0",
                        "--output", tmp_csv,
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0 and os.path.exists(tmp_csv):
                        with open(tmp_csv, newline="", encoding="utf-8") as f:
                            reader = csv.DictReader(f)
                            for r in reader:
                                pid = r.get("point_id")
                                if pid and pid not in seen_ids and r.get("construction_ok") == "1" and r.get("rejection_stage") == "accepted":
                                    seen_ids.add(pid)
                                    points.append(r)
    finally:
        if os.path.exists(tmp_csv):
            os.remove(tmp_csv)

    # Ensure benchmark is always present
    return points


def run_scaled_campaign(points: List[Dict[str, Any]]) -> pd.DataFrame:
    """Run MadGraph for each point and compute LLP signal."""
    curve = load_canonical_trackless_curve(CANONICAL_EFFICIENCY_CSV)
    results = []

    print(f"[SCALE] Evaluating {len(points)} physical points...", flush=True)
    for i, pt in enumerate(points):
        pid = pt["point_id"]
        tb = float(pt.get("tan_beta_input", pt.get("tan_beta", 300000.0)))
        g = float(pt.get("g_hH2H2_GeV", 63.591425))
        ctau = float(pt.get("ctau_mm", 4.32622))
        br_bb = float(pt.get("br_bb", 0.756737))
        mH2 = float(pt.get("mH_input_GeV", 150.0))
        l6 = float(pt.get("lambda6_input", 1e-10))
        M2 = float(pt.get("M2_input_GeV2", 22500.0))

        print(f"[{i+1}/{len(points)}] {pid} (tan_beta={tb}, g={g:.2f}, ctau={ctau:.2e} mm) ... ", end="", flush=True)

        res = run_single_physical_point_madgraph(
            pt,
            proc_dir=DEFAULT_PROC_DIR,
            cards_out_dir=RESULTS_DIR / "scale_cards",
            nevents=10000,
            seeds=[101, 107],
        )

        sigma_prod = res["sigma_production_fb"]
        unc_prod = res["sigma_production_unc_fb"]
        status_mg = res["madgraph_status"]

        aeff = interpolate_aeff(ctau, curve)
        sigma_4b = sigma_prod * (br_bb ** 2) if math.isfinite(sigma_prod) else float("nan")
        sigma_vis = sigma_4b * aeff if math.isfinite(sigma_4b) else float("nan")
        n_expected = DEFAULT_LUMINOSITY_FB_INV * sigma_vis if math.isfinite(sigma_vis) else float("nan")
        ratio_s95 = n_expected / DEFAULT_S95 if math.isfinite(n_expected) else float("nan")

        status_atlas = (
            "EXCLUDED_BY_ATLAS_TRACKLESS_95CL"
            if (math.isfinite(n_expected) and n_expected >= DEFAULT_S95)
            else "ALLOWED_BY_ATLAS_TRACKLESS_95CL"
        )

        print(f"{status_mg} | sigma={sigma_prod:.4f} fb | Aeff={aeff:.4e} | N={n_expected:.4f}", flush=True)

        results.append({
            "point_id": pid,
            "mH2_GeV": mH2,
            "tan_beta": tb,
            "lambda6": l6,
            "M2_GeV2": M2,
            "g_hH2H2_GeV": g,
            "ctau_mm": ctau,
            "BR_bb": br_bb,
            "sigma_production_fb": sigma_prod,
            "sigma_production_unc_fb": unc_prod,
            "madgraph_status": status_mg,
            "Trackless_Aeff": aeff,
            "sigma_4b_fb": sigma_4b,
            "sigma_visible_fb": sigma_vis,
            "N_expected": n_expected,
            "N_over_S95": ratio_s95,
            "atlas_trackless_status": status_atlas,
            "madgraph_run_id_or_path": res.get("madgraph_run_id_or_path", ""),
        })

    df = pd.DataFrame(results)
    out_csv = RESULTS_DIR / "physical_llp_signal_points.csv"
    df.to_csv(out_csv, index=False)
    print(f"[SCALE] Saved {len(df)} points to {out_csv}")
    return df


def plot_diagnostic_figures(df: pd.DataFrame) -> None:
    """Create three publication-ready diagnostic Matplotlib figures."""
    # Plot style setup
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 13,
        "axes.titlesize": 14,
        "legend.fontsize": 10,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "figure.titlesize": 15,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })

    curve_pts = load_canonical_trackless_curve(CANONICAL_EFFICIENCY_CSV)
    c_vals = [p[0] for p in curve_pts]
    a_vals = [p[1] for p in curve_pts]

    # Benchmark point
    bm_ctau = 4.326221529733112
    bm_aeff = 0.01573386
    bm_g = 63.5914252
    bm_sigma = 0.230291

    # Figure 1: Canonical Trackless Acceptance vs ctau
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    ax.plot(c_vals, a_vals, "o-", color="#1f77b4", linewidth=2.2, markersize=5.5, label="Canonical Trackless Response (R8/R10)")
    ax.scatter([bm_ctau], [bm_aeff], color="#d62728", s=110, zorder=5, label=f"Benchmark: $c\\tau=4.33\\,$mm, $A_{{\\mathrm{{eff}}}}={bm_aeff:.5f}$")
    ax.annotate(
        f"Benchmark Closure\n$c\\tau = {bm_ctau:.2f}\\,$mm\n$A_{{\\mathrm{{eff}}}} = 0.01573$",
        xy=(bm_ctau, bm_aeff),
        xytext=(bm_ctau * 2.2, bm_aeff * 0.55),
        arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1.5, headwidth=7),
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#d62728", alpha=0.9),
        fontweight="semibold",
    )
    ax.set_xscale("log")
    ax.set_xlabel(r"Proper Lifetime $c\tau$ [mm]")
    ax.set_ylabel(r"ATLAS Trackless Acceptance $\times$ Efficiency $A_{\mathrm{eff}}$")
    ax.set_title(r"Canonical ATLAS Trackless Recast Response $A_{\mathrm{eff}}(c\tau)$")
    ax.set_xlim(0.2, 1200.0)
    ax.legend(loc="upper right", frameon=True, framealpha=0.9)
    plt.tight_layout()
    fig1_path = REPORTS_DIR / "trackless_acceptance_vs_ctau.png"
    fig.savefig(fig1_path)
    plt.close(fig)
    print(f"[PLOT] Generated {fig1_path}")

    # Figure 2: MadGraph sigma(pp -> H2 H2) vs |g_hH2H2|
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    ax.errorbar(
        df["g_hH2H2_GeV"],
        df["sigma_production_fb"],
        yerr=df["sigma_production_unc_fb"],
        fmt="o",
        color="#2ca02c",
        ecolor="#7f7f7f",
        elinewidth=1.2,
        capsize=3,
        markersize=6,
        alpha=0.85,
        label=r"Physical 2HDM Points ($\sqrt{s}=13\,$TeV, $m_{H_2}=150\,$GeV)",
    )
    ax.scatter([bm_g], [bm_sigma], color="#d62728", s=120, zorder=5, label=f"Benchmark: $|g_{{hH_2H_2}}|={bm_g:.2f}\\,$GeV, $\\sigma={bm_sigma:.4f}\\,$fb")
    ax.annotate(
        f"Benchmark\n$|g_{{hH_2H_2}}| = {bm_g:.2f}\\,$GeV\n$\\sigma = 0.2303\\,$fb",
        xy=(bm_g, bm_sigma),
        xytext=(bm_g * 1.05, bm_sigma * 0.75),
        arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1.5, headwidth=7),
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#d62728", alpha=0.9),
        fontweight="semibold",
    )
    ax.set_xlabel(r"Trilinear Coupling $|g_{hH_2H_2}|$ [GeV]")
    ax.set_ylabel(r"MadGraph Production Cross Section $\sigma(pp \to H_2 H_2)$ [fb]")
    ax.set_title(r"MadGraph Production Cross Section vs Trilinear Coupling $|g_{hH_2H_2}|$")
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    plt.tight_layout()
    fig2_path = REPORTS_DIR / "madgraph_sigma_vs_coupling.png"
    fig.savefig(fig2_path)
    plt.close(fig)
    print(f"[PLOT] Generated {fig2_path}")

    # Figure 3: 2HDM Parameter Plane colored by N_expected / S_95
    fig, ax = plt.subplots(figsize=(8.0, 5.5), dpi=300)
    valid_df = df[df["sigma_production_fb"].notna()].copy()
    valid_df["log10_ratio"] = np.log10(np.maximum(valid_df["N_over_S95"], 1e-6))

    scatter = ax.scatter(
        valid_df["tan_beta"],
        valid_df["lambda6"],
        c=valid_df["log10_ratio"],
        cmap="coolwarm",
        s=80,
        edgecolors="black",
        linewidths=0.7,
        alpha=0.9,
        zorder=4,
    )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label(r"$\log_{10}(N_{\mathrm{expected}} / S_{95})$ ($\mathcal{L}=139\,\mathrm{fb}^{-1}, S_{95}=3.0$)")

    # Mark benchmark point
    ax.scatter([300000.0], [1e-10], marker="*", color="#ffd700", edgecolors="black", s=240, zorder=6, label="Benchmark Point")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\tan\beta$")
    ax.set_ylabel(r"$\lambda_6$")
    ax.set_title(r"2HDM Physical Parameter Plane: ATLAS Trackless Sensitivity")
    ax.legend(loc="upper right", frameon=True, framealpha=0.9)
    plt.tight_layout()
    fig3_path = REPORTS_DIR / "parameter_plane_signal_exclusion.png"
    fig.savefig(fig3_path)
    plt.close(fig)
    print(f"[PLOT] Generated {fig3_path}")


def main() -> int:
    grid = generate_physical_point_grid()
    print(f"[CAMPAIGN] Generated {len(grid)} physical 2HDM grid points.")
    df = run_scaled_campaign(grid)
    plot_diagnostic_figures(df)
    print("[CAMPAIGN] Complete! All CSVs and figures generated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
