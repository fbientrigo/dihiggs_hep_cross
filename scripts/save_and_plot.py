#!/usr/bin/env python3
"""Process evaluated physical points, save dataset, and generate diagnostic figures."""

import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
REPORTS_DIR = REPO_ROOT / "reports" / "figures"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

from compute_physical_llp_signal import (
    CANONICAL_EFFICIENCY_CSV,
    DEFAULT_LUMINOSITY_FB_INV,
    DEFAULT_S95,
    interpolate_aeff,
    load_canonical_trackless_curve,
)
from run_scale_campaign import generate_physical_point_grid, run_scaled_campaign

def main():
    grid = generate_physical_point_grid()
    print(f"Loaded {len(grid)} physical points.")
    
    curve = load_canonical_trackless_curve(CANONICAL_EFFICIENCY_CSV)
    
    # Run scaled campaign directly and get dataframe
    df = run_scaled_campaign(grid)
    
    out_csv = RESULTS_DIR / "physical_llp_signal_points.csv"
    df.to_csv(out_csv, index=False)
    print(f"Saved {len(df)} rows to {out_csv}")
    
    # Generate Figures
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
    print(f"[PLOT] Saved {fig1_path}")

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
    print(f"[PLOT] Saved {fig2_path}")

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
    print(f"[PLOT] Saved {fig3_path}")

if __name__ == "__main__":
    main()
