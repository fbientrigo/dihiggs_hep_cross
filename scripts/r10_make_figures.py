#!/usr/bin/env python3
"""R10 Phase 5: Generate presentation-ready static and interactive plots.

Produces:
1. efficiency_vs_ctau.png
2. nexpected_3d_ctau_g_br.png
3. nexpected_ctau_vs_g_br_baseline.png
4. nexpected_g_vs_br_ctau_baseline.png
5. nexpected_ctau_vs_br_g_atlas.png
6. nexpected_3d_interactive.html
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata

import plotly.graph_objects as go

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"

# Baseline anchor values
CTAU_0 = 4.326221529733112
G_0 = 63.59142520075966
BR_0 = 0.7567374858085787
G_ATLAS = 205.09272542237372

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 1.2


def plot_efficiency_vs_ctau() -> None:
    eff_csv = OUT_DIR / "efficiency_vs_ctau.csv"
    with open(eff_csv, newline="", encoding="utf-8") as fh:
        data = list(csv.DictReader(fh))

    ctaus = [float(r["ctau_mm"]) for r in data]
    aeffs = [float(r["Trackless_Aeff"]) for r in data]
    uncs = [float(r["Trackless_Aeff_stat_uncertainty"]) for r in data]

    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    # Plot line and error bars
    ax.errorbar(
        ctaus,
        aeffs,
        yerr=uncs,
        fmt="o-",
        color="#1f77b4",
        ecolor="#1f77b4",
        elinewidth=1.5,
        capsize=4,
        capthick=1.5,
        linewidth=2,
        markersize=7,
        label=r"ATLAS DV+jets Trackless ($A \times \epsilon$)",
    )

    # Baseline anchor line
    ax.axvline(
        x=CTAU_0,
        color="#d62728",
        linestyle="--",
        linewidth=1.5,
        label=f"Baseline Anchor ($c\\tau_0 = {CTAU_0:.2f}$ mm)",
    )

    ax.set_xscale("log")
    ax.set_xlabel(r"Proper Decay Length $c\tau$ [mm]", fontsize=13, labelpad=8)
    ax.set_ylabel(r"Selection Efficiency ($A \times \epsilon$)", fontsize=13, labelpad=8)
    ax.set_title("ATLAS DV+jets Trackless Selection Efficiency vs. Lifetime", fontsize=14, pad=12, fontweight="bold")

    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend(fontsize=11, loc="upper right", framealpha=0.95)
    ax.set_ylim(bottom=-0.001, top=0.024)

    plt.tight_layout()
    out_path = OUT_DIR / "efficiency_vs_ctau.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Wrote {out_path}")


def plot_3d_scatter() -> None:
    grid_csv = OUT_DIR / "effective_grid.csv"
    with open(grid_csv, newline="", encoding="utf-8") as fh:
        data = list(csv.DictReader(fh))

    ctaus = np.array([float(r["ctau_mm"]) for r in data])
    log_ctau = np.log10(ctaus)
    gs = np.array([float(r["g_hH2H2_GeV"]) for r in data])
    brs = np.array([float(r["BR_H2_to_bb"]) for r in data])
    n_exps = np.array([float(r["N_expected_139fb"]) for r in data])
    log_n = np.log10(np.maximum(n_exps, 1e-4))

    fig = plt.figure(figsize=(10, 8), dpi=300)
    ax = fig.add_subplot(111, projection="3d")

    # Categories
    cat1 = n_exps < 1.0
    cat2 = (n_exps >= 1.0) & (n_exps < 3.0)
    cat3 = n_exps >= 3.0

    s1 = ax.scatter(
        log_ctau[cat1],
        gs[cat1],
        brs[cat1],
        c=log_n[cat1],
        cmap="viridis",
        vmin=-3,
        vmax=2,
        marker="o",
        s=30,
        alpha=0.6,
        label=r"$N_{\mathrm{expected}} < 1$",
    )
    s2 = ax.scatter(
        log_ctau[cat2],
        gs[cat2],
        brs[cat2],
        c=log_n[cat2],
        cmap="viridis",
        vmin=-3,
        vmax=2,
        marker="s",
        s=50,
        alpha=0.85,
        edgecolors="blue",
        linewidths=0.8,
        label=r"$1 \leq N_{\mathrm{expected}} < 3$",
    )
    s3 = ax.scatter(
        log_ctau[cat3],
        gs[cat3],
        brs[cat3],
        c=log_n[cat3],
        cmap="viridis",
        vmin=-3,
        vmax=2,
        marker="^",
        s=80,
        alpha=1.0,
        edgecolors="crimson",
        linewidths=1.2,
        label=r"$N_{\mathrm{expected}} \geq 3$ ($S_{95}$)",
    )

    ax.set_xlabel(r"$\log_{10}(c\tau / \mathrm{mm})$", fontsize=11, labelpad=8)
    ax.set_ylabel(r"$g_{hH_2H_2}$ [GeV]", fontsize=11, labelpad=8)
    ax.set_zlabel(r"$\mathrm{BR}(H_2 \to b\bar{b})$", fontsize=11, labelpad=8)
    ax.set_title(
        r"Expected Yield $N_{\mathrm{expected}}$ across $(c\tau, g_{hH_2H_2}, \mathrm{BR}_{b\bar{b}})$",
        fontsize=13,
        pad=14,
        fontweight="bold",
    )

    cbar = fig.colorbar(s3, ax=ax, pad=0.1, shrink=0.7)
    cbar.set_label(r"$\log_{10}(N_{\mathrm{expected}})$", fontsize=11)

    ax.legend(loc="upper left", fontsize=10, framealpha=0.9)
    ax.view_init(elev=25, azim=135)

    plt.tight_layout()
    out_path = OUT_DIR / "nexpected_3d_ctau_g_br.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Wrote {out_path}")


def plot_2d_slice(
    fix_var: str,
    fix_val: float,
    x_var: str,
    y_var: str,
    out_filename: str,
    title: str,
    x_label: str,
    y_label: str,
    x_log: bool = False,
    anchor_pt: tuple[float, float] | None = None,
) -> None:
    grid_csv = OUT_DIR / "effective_grid.csv"
    with open(grid_csv, newline="", encoding="utf-8") as fh:
        data = list(csv.DictReader(fh))

    # Filter rows matching fix_var
    filtered = [r for r in data if abs(float(r[fix_var]) - fix_val) < 1e-4]

    xs = np.array([float(r[x_var]) for r in filtered])
    ys = np.array([float(r[y_var]) for r in filtered])
    ns = np.array([float(r["N_expected_139fb"]) for r in filtered])

    # Interpolate on fine 2D grid for smooth contouring
    x_unique = np.sort(np.unique(xs))
    y_unique = np.sort(np.unique(ys))

    if x_log:
        xi = np.logspace(np.log10(x_unique.min()), np.log10(x_unique.max()), 100)
    else:
        xi = np.linspace(x_unique.min(), x_unique.max(), 100)
    yi = np.linspace(y_unique.min(), y_unique.max(), 100)

    Xi, Yi = np.meshgrid(xi, yi)

    # Convert x to log scale if needed for griddata
    points_x = np.log10(xs) if x_log else xs
    eval_x = np.log10(Xi) if x_log else Xi

    Zi = griddata((points_x, ys), ns, (eval_x, Yi), method="cubic")

    fig, ax = plt.subplots(figsize=(8.5, 6.5), dpi=300)

    # Color fill (log scale for N_expected)
    log_Zi = np.log10(np.maximum(Zi, 1e-4))
    levels_fill = np.linspace(-3, 2, 51)
    cf = ax.contourf(Xi, Yi, log_Zi, levels=levels_fill, cmap="YlGnBu_r", extend="both")

    cbar = fig.colorbar(cf, ax=ax, label=r"$\log_{10}(N_{\mathrm{expected}})$")

    # Prominent contours for N = 1 and N = 3
    c1 = ax.contour(Xi, Yi, Zi, levels=[1.0], colors=["#ff7f0e"], linewidths=[2.0], linestyles=["--"])
    c3 = ax.contour(Xi, Yi, Zi, levels=[3.0], colors=["#d62728"], linewidths=[2.5], linestyles=["-"])

    # Label contours
    ax.clabel(c1, fmt={1.0: "N = 1"}, inline=True, fontsize=10)
    ax.clabel(c3, fmt={3.0: "N = 3 (S95)"}, inline=True, fontsize=11)

    if anchor_pt:
        ax.plot(
            anchor_pt[0],
            anchor_pt[1],
            "*",
            color="gold",
            markeredgecolor="black",
            markersize=14,
            label="Baseline Anchor Point",
        )
        ax.legend(loc="upper left", fontsize=11, framealpha=0.9)

    if x_log:
        ax.set_xscale("log")

    ax.set_xlabel(x_label, fontsize=12, labelpad=8)
    ax.set_ylabel(y_label, fontsize=12, labelpad=8)
    ax.set_title(title, fontsize=13, pad=12, fontweight="bold")

    plt.tight_layout()
    out_path = OUT_DIR / out_filename
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Wrote {out_path}")


def plot_interactive_3d() -> None:
    grid_csv = OUT_DIR / "effective_grid.csv"
    with open(grid_csv, newline="", encoding="utf-8") as fh:
        data = list(csv.DictReader(fh))

    ctaus = [float(r["ctau_mm"]) for r in data]
    gs = [float(r["g_hH2H2_GeV"]) for r in data]
    brs = [float(r["BR_H2_to_bb"]) for r in data]
    n_exps = [float(r["N_expected_139fb"]) for r in data]
    pids = [r["point_id"] for r in data]

    hover_text = [
        f"Point: {pid}<br>ctau: {c:.3f} mm<br>g: {g:.1f} GeV<br>BR(bb): {br:.2f}<br>N_expected: {n:.3f}"
        for pid, c, g, br, n in zip(pids, ctaus, gs, brs, n_exps)
    ]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=np.log10(ctaus),
                y=gs,
                z=brs,
                mode="markers",
                marker=dict(
                    size=6,
                    color=np.log10(np.maximum(n_exps, 1e-4)),
                    colorscale="Viridis",
                    colorbar=dict(title="log10(N_expected)"),
                    opacity=0.8,
                ),
                text=hover_text,
                hoverinfo="text",
            )
        ]
    )

    fig.update_layout(
        title="Interactive 3D Scan: Expected Yields N_expected(ctau, g, BR_bb)",
        scene=dict(
            xaxis_title="log10(ctau / mm)",
            yaxis_title="g_hH2H2 [GeV]",
            zaxis_title="BR(H2 -> bb)",
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    out_path = OUT_DIR / "nexpected_3d_interactive.html"
    fig.write_html(str(out_path))
    print(f"[OK] Wrote {out_path}")


def main() -> int:
    plot_efficiency_vs_ctau()
    plot_3d_scatter()

    # 2D Cut 1: ctau vs g (BR = 0.7567374858)
    plot_2d_slice(
        fix_var="BR_H2_to_bb",
        fix_val=BR_0,
        x_var="ctau_mm",
        y_var="g_hH2H2_GeV",
        out_filename="nexpected_ctau_vs_g_br_baseline.png",
        title=f"Expected Yield in $c\\tau$ vs. $g_{{hH_2H_2}}$ Plane (BR$_{{b\\bar{{b}}}} = {BR_0:.3f}$)",
        x_label=r"Proper Decay Length $c\tau$ [mm]",
        y_label=r"Production Coupling $g_{hH_2H_2}$ [GeV]",
        x_log=True,
        anchor_pt=(CTAU_0, G_0),
    )

    # 2D Cut 2: g vs BR (ctau = 4.3262215297 mm)
    plot_2d_slice(
        fix_var="ctau_mm",
        fix_val=CTAU_0,
        x_var="g_hH2H2_GeV",
        y_var="BR_H2_to_bb",
        out_filename="nexpected_g_vs_br_ctau_baseline.png",
        title=f"Expected Yield in $g_{{hH_2H_2}}$ vs. BR$_{{b\\bar{{b}}}}$ Plane ($c\\tau_0 = {CTAU_0:.2f}$ mm)",
        x_label=r"Production Coupling $g_{hH_2H_2}$ [GeV]",
        y_label=r"Branching Fraction $\mathrm{BR}(H_2 \to b\bar{b})$",
        x_log=False,
        anchor_pt=(G_0, BR_0),
    )

    # 2D Cut 3: ctau vs BR (g = 205.0927254224 GeV)
    plot_2d_slice(
        fix_var="g_hH2H2_GeV",
        fix_val=G_ATLAS,
        x_var="ctau_mm",
        y_var="BR_H2_to_bb",
        out_filename="nexpected_ctau_vs_br_g_atlas.png",
        title=f"Expected Yield in $c\\tau$ vs. BR$_{{b\\bar{{b}}}}$ Plane ($g_{{hH_2H_2}} = {G_ATLAS:.1f}$ GeV)",
        x_label=r"Proper Decay Length $c\tau$ [mm]",
        y_label=r"Branching Fraction $\mathrm{BR}(H_2 \to b\bar{b})$",
        x_log=True,
        anchor_pt=(CTAU_0, BR_0),
    )

    plot_interactive_3d()
    print("[PASS] All R10 figures generated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
