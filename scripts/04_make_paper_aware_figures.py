#!/usr/bin/env python3
"""Paper-aware figures for the arXiv:2606.01681 recast scaffold.

These figures show the displaced-decay geometry, the public ATLAS DV+jets
selection structure, and the current scalar-S proxy -- they are NOT an ATLAS
reproduction and NOT an exclusion. See docs/recast/paper_aware_figures_interpretation.md
for the full caveats behind each figure.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from llp_recast.plots import (
    prepare_fig1_sweetspot,
    prepare_fig2_event_efficiency,
    prepare_fig3_vertex_heatmap,
    prepare_fig4_cutflow,
    prepare_fig5_inventory,
    prepare_fig6_proxy_map,
)

FIG_FLAGS = {
    "fig1_id_decay_probability": "PAPER_AWARE_PROXY",
    "fig2_event_efficiency_vs_sumpt": "HEPDATA_DERIVED_SHAPE; EWK_BENCHMARK_NOT_SCALAR_S; NEEDS_REAL_SIGNAL_MC",
    "fig3_vertex_efficiency_heatmap": "HEPDATA_DERIVED_SHAPE; EWK_BENCHMARK_NOT_SCALAR_S; NEEDS_REAL_SIGNAL_MC",
    "fig4_trackless_cutflow": "HEPDATA_DERIVED_SHAPE; EWK_BENCHMARK_NOT_SCALAR_S; NEEDS_REAL_SIGNAL_MC",
    "fig5_hepdata_inventory": "HEPDATA_DERIVED_SHAPE",
    "fig6_scalar_s_proxy_map": "PAPER_AWARE_PROXY; NOT_EXCLUSION_GRADE; NEEDS_REAL_SIGNAL_MC; HEPDATA_DERIVED_SHAPE",
}

FIG_MESSAGES = {
    "fig1_id_decay_probability": "The DV search only 'sees' a narrow ctau window between prompt-like decays"
    " (R<4mm) and decays that escape the inner detector (R>300mm).",
    "fig2_event_efficiency_vs_sumpt": "Public event-level efficiency is nontrivial and radius-dependent"
    " -- this is the ATLAS EWK benchmark's efficiency, not scalar-S's.",
    "fig3_vertex_efficiency_heatmap": "Passing the geometric radius cut is not enough: DV mass and track"
    " multiplicity gate efficiency further, and the gate shape changes with radius.",
    "fig4_trackless_cutflow": "Shows where signal is progressively lost through the selection chain;"
    " the 0.1ns vs 1.0ns divergence at DV-geometry/material-veto/n_tracks steps is the interesting signal.",
    "fig5_hepdata_inventory": "The public HEPData bundle contains real recast ingredients"
    " (efficiencies, cutflows, acceptance, limits), not just headline exclusion plots.",
    "fig6_scalar_s_proxy_map": "PAPER-AWARE PROXY -- NOT EXCLUSION GRADE. Shows where in (mass, lifetime)"
    " space the current placeholder-heavy pipeline predicts the most signal.",
}


def _flag_text(fig, flags: str) -> None:
    fig.text(0.5, 0.01, flags, fontsize=7, ha="center", color="dimgray")


def _plain_text(s: str) -> str:
    """Strip the HEPData cutflow's raw LaTeX ($..$, \\text{}, \\ge) into plain, mathtext-safe text."""
    s = re.sub(r"\\geq|\\ge\b", ">=", s)
    s = re.sub(r"\\(text|textrm|vec)\{([^}]*)\}", r"\2", s)
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = s.replace("$", "").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


def make_fig1(outdir: Path) -> None:
    ctau_values = [10 ** (x / 10) for x in range(0, 41)]  # 1 to 10000 mm, log-spaced
    beta_gamma_values = [0.5, 1, 2, 5]
    df = prepare_fig1_sweetspot(ctau_values, beta_gamma_values)

    fig, ax = plt.subplots(figsize=(7, 5))
    for bg, group in df.groupby("beta_gamma"):
        ax.plot(group["ctau_mm"], group["P_decay_in_ID"], label=f"beta*gamma={bg}")
    ax.set_xscale("log")
    ax.set_xlabel("ctau [mm]")
    ax.set_ylabel("P(4 mm < R < 300 mm)")
    ax.set_title("Figure 1: ID decay-probability sweet spot")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.text(0.5, 0.94, FIG_MESSAGES["fig1_id_decay_probability"], fontsize=8, ha="center", wrap=True)
    _flag_text(fig, FIG_FLAGS["fig1_id_decay_probability"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.90))
    fig.savefig(outdir / "fig1_id_decay_probability.png", dpi=150)
    plt.close(fig)


def make_fig2(outdir: Path, tidy_dir: Path) -> None:
    raw = pd.read_csv(tidy_dir / "event_efficiency_trackless.csv")
    df = prepare_fig2_event_efficiency(raw)

    fig, ax = plt.subplots(figsize=(7, 5))
    for cat, group in df.groupby("radial_category"):
        ax.plot(group["sumpt_lo_gev"], group["value"], marker="o", label=cat)
    ax.set_xlabel("Sumpt [GeV] (bin lower edge)")
    ax.set_ylabel("Trackless SR event efficiency")
    ax.set_title("Figure 2: Trackless event efficiency vs Sumpt (ATLAS EWK benchmark)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.text(0.5, 0.94, FIG_MESSAGES["fig2_event_efficiency_vs_sumpt"], fontsize=8, ha="center", wrap=True)
    _flag_text(fig, FIG_FLAGS["fig2_event_efficiency_vs_sumpt"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.88))
    fig.savefig(outdir / "fig2_event_efficiency_vs_sumpt.png", dpi=150)
    plt.close(fig)


def make_fig3(outdir: Path, tidy_dir: Path) -> None:
    raw = pd.read_csv(tidy_dir / "vertex_efficiency_grid.csv")
    labels = ("22_25_mm", "84_111_mm", "180_300_mm")
    grids = prepare_fig3_vertex_heatmap(raw, radius_bin_labels=labels)

    fig, axes = plt.subplots(1, len(labels), figsize=(15, 5), sharey=True)
    im = None
    for ax, label in zip(axes, labels):
        grid = grids[label]
        im = ax.imshow(grid.values, aspect="auto", origin="lower", vmin=0.0, vmax=1.0, cmap="viridis")
        ax.set_title(f"R in {label.replace('_', '-').replace('-mm', ' mm')}")
        ax.set_xticks(range(len(grid.columns)))
        ax.set_xticklabels([f"{int(v)}" for v in grid.columns], rotation=45)
        ax.set_xlabel("n_tracks (bin lower edge)")
    axes[0].set_yticks(range(len(grids[labels[0]].index)))
    axes[0].set_yticklabels([f"{v:g}" for v in grids[labels[0]].index])
    axes[0].set_ylabel("m_DV [GeV] (bin lower edge)")
    fig.suptitle("Figure 3: Vertex efficiency heatmaps (ATLAS EWK benchmark)", y=1.04, fontsize=13)
    fig.colorbar(im, ax=axes, label="vertex efficiency", shrink=0.8)
    fig.text(0.5, 0.98, FIG_MESSAGES["fig3_vertex_efficiency_heatmap"], fontsize=8, ha="center", wrap=True)
    fig.text(0.5, -0.08, FIG_FLAGS["fig3_vertex_efficiency_heatmap"], fontsize=7, ha="center", color="dimgray")
    fig.savefig(outdir / "fig3_vertex_efficiency_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_fig4(outdir: Path, tidy_dir: Path) -> None:
    raw = pd.read_csv(tidy_dir / "cutflow_trackless_ewk.csv")
    df = prepare_fig4_cutflow(raw)

    fig, ax = plt.subplots(figsize=(9, 5))
    for label, group in df.groupby("legend_label", sort=False):
        group = group.sort_values("step_index")
        ax.plot(group["step_index"], group["value"], marker="o", label=label)
    step_labels = [
        _plain_text(s)
        for s in df.sort_values("step_index").drop_duplicates("step_index")["Selections"].tolist()
    ]
    ax.set_xticks(range(len(step_labels)))
    ax.set_xticklabels(step_labels, rotation=60, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("Full Sim A x epsilon")
    ax.set_title("Figure 4: Trackless cutflow (ATLAS EWK benchmark, 4 mass/lifetime points)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout(rect=(0, 0.05, 1, 0.85))
    fig.text(0.5, 0.94, FIG_MESSAGES["fig4_trackless_cutflow"], fontsize=8, ha="center", wrap=True)
    _flag_text(fig, FIG_FLAGS["fig4_trackless_cutflow"])
    fig.savefig(outdir / "fig4_trackless_cutflow.png", dpi=150)
    plt.close(fig)


def make_fig5(outdir: Path, inventory_dir: Path) -> None:
    raw = pd.read_csv(inventory_dir / "atlas_dvjets_table_inventory.csv")
    counts = prepare_fig5_inventory(raw)

    fig, ax = plt.subplots(figsize=(7, 5))
    counts.sort_values(ascending=True).plot.barh(ax=ax)
    ax.set_xlabel("table count")
    ax.set_title("Figure 5: HEPData table inventory by category")
    fig.text(0.5, 0.94, FIG_MESSAGES["fig5_hepdata_inventory"], fontsize=8, ha="center", wrap=True)
    _flag_text(fig, FIG_FLAGS["fig5_hepdata_inventory"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.88))
    fig.savefig(outdir / "fig5_hepdata_inventory.png", dpi=150)
    plt.close(fig)


def make_fig6(outdir: Path, proxy_dir: Path) -> None:
    raw = pd.read_csv(proxy_dir / "paper_s_benchmark_proxy.csv")
    grid = prepare_fig6_proxy_map(raw, value_col="Nsig_139fb")

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(grid.values, aspect="auto", origin="lower", cmap="magma")
    ax.set_xticks(range(len(grid.columns)))
    ax.set_xticklabels([f"{v:g}" for v in grid.columns], rotation=45)
    ax.set_yticks(range(len(grid.index)))
    ax.set_yticklabels([f"{v:g}" for v in grid.index])
    ax.set_xlabel("ctau [mm]")
    ax.set_ylabel("mS [GeV]")
    fig.colorbar(im, ax=ax, label="Nsig proxy @ 139 fb^-1")
    ax.set_title("Figure 6: Scalar-S proxy map", fontsize=10)
    fig.tight_layout(rect=(0, 0.03, 1, 0.80))
    fig.suptitle("PAPER-AWARE PROXY -- NOT EXCLUSION GRADE", y=0.97, fontsize=12, color="firebrick")
    fig.text(0.5, 0.90, FIG_MESSAGES["fig6_scalar_s_proxy_map"], fontsize=7, ha="center", wrap=True)
    _flag_text(fig, FIG_FLAGS["fig6_scalar_s_proxy_map"])
    fig.savefig(outdir / "fig6_scalar_s_proxy_map.png", dpi=150)
    plt.close(fig)


def write_readme(outdir: Path) -> None:
    lines = [
        "# Paper-aware figures (arXiv:2606.01681 recast scaffold)",
        "",
        "**None of these figures is an ATLAS reproduction or an exclusion.**",
        "See `docs/recast/paper_aware_figures_interpretation.md` for full caveats.",
        "",
        "| Figure | Message | Quality flags |",
        "|---|---|---|",
    ]
    titles = {
        "fig1_id_decay_probability": "1. ID decay probability sweet spot",
        "fig2_event_efficiency_vs_sumpt": "2. Trackless event efficiency vs Sumpt",
        "fig3_vertex_efficiency_heatmap": "3. Vertex efficiency heatmaps",
        "fig4_trackless_cutflow": "4. Trackless cutflow",
        "fig5_hepdata_inventory": "5. HEPData inventory summary",
        "fig6_scalar_s_proxy_map": "6. Scalar-S proxy map",
    }
    for key, title in titles.items():
        lines.append(f"| {title} (`{key}.png`) | {FIG_MESSAGES[key]} | {FIG_FLAGS[key]} |")
    lines.append("")
    (outdir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate paper-aware figures (not exclusion grade)")
    ap.add_argument("--tidy-dir", default="outputs/hepdata_tidy")
    ap.add_argument("--inventory-dir", default="outputs/hepdata_inventory")
    ap.add_argument("--proxy-dir", default="outputs/paper_s_proxy")
    ap.add_argument("--outdir", default="outputs/figures")
    args = ap.parse_args()

    tidy_dir = Path(args.tidy_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    make_fig1(outdir)
    make_fig2(outdir, tidy_dir)
    make_fig3(outdir, tidy_dir)
    make_fig4(outdir, tidy_dir)
    make_fig5(outdir, Path(args.inventory_dir))
    make_fig6(outdir, Path(args.proxy_dir))
    write_readme(outdir)

    print(f"[OK] wrote 6 figures to {outdir}")
    print(f"[OK] wrote {outdir / 'README.md'}")
    print("[NOTE] These are paper-aware figures. Not an ATLAS reproduction. Not an exclusion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
