#!/usr/bin/env python3
"""Interpretation figures: paper needs vs. HEPData provides vs. current proxy vs. 2HDM needs.

Five figures, each built to clarify interpretation rather than decorate:
A. decay-geometry transferable layer (no ATLAS efficiency applied)
B. trackless event efficiency, audited -- annotates the published >1 point
C. vertex efficiency requirements (needs m_DV/n_tracks from signal MC)
D. paper-vs-our-case pipeline bridge (text/table figure from llp_recast.interpretation)
E. scalar-S proxy map with missing-input overlay panel

None of these is an ATLAS reproduction or an exclusion. See
docs/recast/efficiency_semantics.md and docs/recast/paper_vs_our_2hdm_bridge.md.
"""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from llp_recast.interpretation import BRIDGE_LAYERS, STATUS_READY, STATUS_HEPDATA_BENCHMARK_ONLY
from llp_recast.plots import (
    prepare_fig1_sweetspot,
    prepare_fig2_event_efficiency,
    prepare_fig3_vertex_heatmap,
    prepare_fig6_proxy_map,
    values_above_one,
)

STATUS_COLORS = {
    STATUS_READY: "#2e7d32",
    "PROXY_ONLY": "#f9a825",
    STATUS_HEPDATA_BENCHMARK_ONLY: "#ef6c00",
    "NEEDS_SIGNAL_MC": "#c62828",
    "NEEDS_2HDM_MAPPING": "#6a1b9a",
    "NOT_DIRECTLY_TRANSFERABLE": "#424242",
}

FIGURES = {
    "figA_decay_geometry_transferable": {
        "title": "Figure A: Decay-geometry transferable layer",
        "message": "Transferable if ctau and beta_gamma are known. No ATLAS efficiency applied.",
        "flags": "GEOMETRIC_PROBABILITY; NEEDS_2HDM_MAPPING(ctau only)",
    },
    "figB_trackless_event_efficiency_audited": {
        "title": "Figure B: Trackless event efficiency, audited",
        "message": "Published ATLAS EWK-benchmark efficiency, not scalar-S's; radius- and"
        " Sumpt-dependent, and not bounded by 1 (see annotated point).",
        "flags": "HEPDATA_BENCHMARK_PARAMETRIZATION; NOT_UNIVERSAL_EFFICIENCY; EWK_BENCHMARK_NOT_SCALAR_S",
    },
    "figC_vertex_efficiency_requirements": {
        "title": "Figure C: Vertex efficiency requirements",
        "message": "Requires m_DV and n_tracks from signal MC. Not determined by lifetime alone.",
        "flags": "HEPDATA_BENCHMARK_PARAMETRIZATION; NEEDS_SIGNAL_MC",
    },
    "figD_paper_vs_our_case_pipeline": {
        "title": "Figure D: Paper S -> HEPData -> current proxy -> 2HDM missing inputs",
        "message": "Color = transfer status per layer. See docs/recast/paper_vs_our_2hdm_bridge.md.",
        "flags": "SEE_BRIDGE_TABLE",
    },
    "figE_scalarS_proxy_with_missing_inputs": {
        "title": "Figure E: Scalar-S proxy map with missing-input overlay",
        "message": "PAPER-AWARE PROXY -- NOT EXCLUSION GRADE. Every input on the right is a placeholder"
        " or borrowed number, not a measurement or MC output.",
        "flags": "PAPER_AWARE_PROXY; NOT_EXCLUSION_GRADE; NEEDS_SIGNAL_MC",
    },
}


def _flag_text(fig, flags: str) -> None:
    fig.text(0.5, 0.01, flags, fontsize=7, ha="center", color="dimgray")


def make_figA(outdir: Path) -> None:
    key = "figA_decay_geometry_transferable"
    ctau_values = [10 ** (x / 10) for x in range(0, 41)]  # 1 to 10000 mm, log-spaced
    beta_gamma_values = [0.5, 1, 2, 5]
    df = prepare_fig1_sweetspot(ctau_values, beta_gamma_values)

    fig, ax = plt.subplots(figsize=(7, 5))
    for bg, group in df.groupby("beta_gamma"):
        ax.plot(group["ctau_mm"], group["P_decay_in_ID"], label=f"beta*gamma={bg}")
    ax.set_xscale("log")
    ax.set_xlabel("ctau [mm]")
    ax.set_ylabel("P(4 mm < R < 300 mm)")
    ax.set_title(FIGURES[key]["title"])
    ax.legend()
    ax.grid(alpha=0.3)
    fig.text(0.5, 0.94, FIGURES[key]["message"], fontsize=9, ha="center", wrap=True, color="#2e7d32")
    _flag_text(fig, FIGURES[key]["flags"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.90))
    fig.savefig(outdir / f"{key}.png", dpi=150)
    plt.close(fig)


def make_figB(outdir: Path, tidy_dir: Path) -> None:
    key = "figB_trackless_event_efficiency_audited"
    raw = pd.read_csv(tidy_dir / "event_efficiency_trackless.csv")
    df = prepare_fig2_event_efficiency(raw)
    over_one = values_above_one(df)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for cat, group in df.groupby("radial_category"):
        ax.plot(group["sumpt_lo_gev"], group["value"], marker="o", label=cat)
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1, alpha=0.6)
    ax.text(0.02, 1.03, "efficiency = 1", fontsize=7, ha="left", color="black")
    for _, row in over_one.iterrows():
        ax.annotate(
            f"{row['value']:.4f} (published, not a plot bug)",
            xy=(row["sumpt_lo_gev"], row["value"]),
            xytext=(row["sumpt_lo_gev"] + 0.55, row["value"] + 0.05),
            fontsize=7,
            color="firebrick",
            arrowprops=dict(arrowstyle="->", color="firebrick", lw=0.8),
        )
    ax.set_xlabel("Sumpt [GeV] (summed track pT in event, bin lower edge)")
    ax.set_ylabel("Trackless SR event efficiency (HEPData 'Efficiency' column)")
    ax.set_title(FIGURES[key]["title"])
    ax.legend(loc="center right")
    ax.grid(alpha=0.3)
    fig.text(0.5, 0.965, "HEPData benchmark parameterization, not universal probability.",
              fontsize=9, ha="center", color="firebrick", weight="bold")
    fig.text(0.5, 0.925, FIGURES[key]["message"], fontsize=7.5, ha="center", wrap=True)
    _flag_text(fig, FIGURES[key]["flags"])
    fig.tight_layout(rect=(0, 0.03, 1, 0.87))
    fig.savefig(outdir / f"{key}.png", dpi=150)
    plt.close(fig)


def make_figC(outdir: Path, tidy_dir: Path) -> None:
    key = "figC_vertex_efficiency_requirements"
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
    fig.suptitle(FIGURES[key]["title"], y=1.06, fontsize=13)
    fig.colorbar(im, ax=axes, label="vertex efficiency (bounded [0,1] in this data)", shrink=0.8)
    fig.text(0.5, 1.0, FIGURES[key]["message"], fontsize=9, ha="center", wrap=True, color="#c62828")
    fig.text(0.5, -0.08, FIGURES[key]["flags"], fontsize=7, ha="center", color="dimgray")
    fig.savefig(outdir / f"{key}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_figD(outdir: Path) -> None:
    key = "figD_paper_vs_our_case_pipeline"
    fields = ["paper_scalar_S", "atlas_hepdata", "current_proxy", "our_2hdm_need"]
    wrap_width = 30
    line_h = 1.0

    wrapped_rows = []
    for row in BRIDGE_LAYERS:
        cells = [textwrap.wrap(row[f], wrap_width) or [""] for f in fields]
        n_lines = max(len(c) for c in cells)
        wrapped_rows.append((row, cells, n_lines))

    row_heights = [n_lines * line_h + 1.2 for _, _, n_lines in wrapped_rows]
    total_h = sum(row_heights)

    fig, ax = plt.subplots(figsize=(15, max(0.35 * total_h, 6)))
    ax.set_xlim(0, 5.2)
    ax.set_ylim(0, total_h + 2)
    ax.axis("off")

    col_x = [1.3, 2.55, 3.55, 4.55]
    col_widths = [1.15, 1.0, 1.0, 0.65]
    headers = ["Paper scalar S", "ATLAS HEPData provides", "Current proxy", "Our 2HDM requirement"]
    y_cursor = total_h + 1.3
    for x, h in zip(col_x, headers):
        ax.text(x, y_cursor, h, fontsize=9, weight="bold", va="bottom")
    ax.text(0.0, y_cursor, "Layer / status", fontsize=9, weight="bold", va="bottom")

    for row, cells, n_lines in wrapped_rows:
        rh = n_lines * line_h + 1.2
        y_top = y_cursor - 0.5
        y_center = y_top - rh / 2 + 0.5
        color = STATUS_COLORS.get(row["status"], "#000000")

        ax.add_patch(plt.Rectangle((0.0, y_top - rh), 0.08, rh, color=color))
        ax.text(0.15, y_center, row["layer"], fontsize=8, weight="bold", va="center")
        ax.text(0.15, y_center - 0.55, row["status"], fontsize=6, color=color, va="center")

        for x, lines in zip(col_x, cells):
            ax.text(x, y_center + (len(lines) - 1) * line_h / 2, "\n".join(lines),
                     fontsize=6.5, va="center", linespacing=1.4)

        y_cursor -= rh
        ax.axhline(y_cursor, xmin=0.0, xmax=1.0, color="lightgray", linewidth=0.5)

    ax.set_title(FIGURES[key]["title"], fontsize=13, pad=20)
    fig.text(0.5, 0.005, FIGURES[key]["message"], fontsize=9, ha="center", color="dimgray")
    fig.tight_layout(rect=(0.02, 0.02, 1, 0.96))
    fig.savefig(outdir / f"{key}.png", dpi=150)
    plt.close(fig)


def make_figE(outdir: Path, proxy_dir: Path) -> None:
    key = "figE_scalarS_proxy_with_missing_inputs"
    raw = pd.read_csv(proxy_dir / "paper_s_benchmark_proxy.csv")
    grid = prepare_fig6_proxy_map(raw, value_col="Nsig_139fb")
    row0 = raw.iloc[0]

    fig = plt.figure(figsize=(11, 5.5))
    ax = fig.add_axes((0.08, 0.15, 0.55, 0.68))
    ax_side = fig.add_axes((0.68, 0.15, 0.28, 0.68))
    ax_side.axis("off")

    im = ax.imshow(grid.values, aspect="auto", origin="lower", cmap="magma")
    ax.set_xticks(range(len(grid.columns)))
    ax.set_xticklabels([f"{v:g}" for v in grid.columns], rotation=45)
    ax.set_yticks(range(len(grid.index)))
    ax.set_yticklabels([f"{v:g}" for v in grid.index])
    ax.set_xlabel("ctau [mm]")
    ax.set_ylabel("mS [GeV]")
    fig.colorbar(im, ax=ax, label="Nsig proxy @ 139 fb^-1", shrink=0.85)
    ax.set_title("Scalar-S proxy map", fontsize=11)

    side_lines = [
        "MISSING / PLACEHOLDER INPUTS",
        "",
        f"sigma assumed: {row0['sigma_fb_assumed']:g} fb (flat placeholder)",
        f"BR_hadronic assumed: step function, no citation",
        f"beta_gamma assumed: {row0['beta_gamma_assumed']:g} (flat placeholder)",
        f"eff_event borrowed: {row0['eff_event_proxy']:g} (flat placeholder)",
        f"eff_vertex borrowed: {row0['eff_vertex_proxy']:.3f}",
        "  (EWK cutflow final step, averaged,",
        "   not scalar-S mapped)",
        "limit anchor: nearest EWK-benchmark",
        "  observed limit (not scalar-S specific)",
        "",
        "NOT EXCLUSION GRADE",
    ]
    ax_side.text(
        0.0, 1.0, "\n".join(side_lines), fontsize=8.5, va="top", ha="left",
        family="monospace", transform=ax_side.transAxes,
        color="firebrick",
    )

    fig.suptitle(FIGURES[key]["title"], y=0.99, fontsize=12)
    fig.text(0.5, 0.90, FIGURES[key]["message"], fontsize=7.5, ha="center", wrap=True)
    _flag_text(fig, FIGURES[key]["flags"])
    fig.savefig(outdir / f"{key}.png", dpi=150)
    plt.close(fig)


def write_readme(outdir: Path) -> None:
    lines = [
        "# Interpretation figures v2 (paper vs. HEPData vs. current proxy vs. 2HDM)",
        "",
        "**None of these figures is an ATLAS reproduction or an exclusion.**",
        "See `docs/recast/efficiency_semantics.md` and",
        "`docs/recast/paper_vs_our_2hdm_bridge.md` for full caveats.",
        "",
        "| Figure | Message | Quality flags |",
        "|---|---|---|",
    ]
    for key, meta in FIGURES.items():
        lines.append(f"| {meta['title']} (`{key}.png`) | {meta['message']} | {meta['flags']} |")
    lines += [
        "",
        "## Event-efficiency >1 note (Figure B)",
        "",
        "The `R < 1150 mm` trackless curve peaks at **1.1851** (Sumpt in [0.6, 0.8) GeV)."
        " This value is identical in the raw HEPData YAML, the tidy CSV, and this plot --"
        " confirmed by direct trace, not assumed. It is not a plotting bug or a normalization"
        " error in this pipeline. See `docs/recast/efficiency_audit_event_efficiency_gt1.md`"
        " for the full trace and `docs/recast/efficiency_semantics.md` for why HEPData's"
        " 'Efficiency' column here is a reinterpretation-recipe weight, not a bounded"
        " pass/total probability.",
        "",
    ]
    (outdir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate interpretation figures (not exclusion grade)")
    ap.add_argument("--tidy-dir", default="outputs/hepdata_tidy")
    ap.add_argument("--proxy-dir", default="outputs/paper_s_proxy")
    ap.add_argument("--outdir", default="outputs/figures_v2")
    args = ap.parse_args()

    tidy_dir = Path(args.tidy_dir)
    proxy_dir = Path(args.proxy_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    make_figA(outdir)
    make_figB(outdir, tidy_dir)
    make_figC(outdir, tidy_dir)
    make_figD(outdir)
    make_figE(outdir, proxy_dir)
    write_readme(outdir)

    print(f"[OK] wrote 5 figures to {outdir}")
    print(f"[OK] wrote {outdir / 'README.md'}")
    print("[NOTE] These are interpretation figures. Not an ATLAS reproduction. Not an exclusion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
