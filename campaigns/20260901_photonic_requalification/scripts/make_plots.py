#!/usr/bin/env python3
"""The two minimal validation plots: BRs and ctau, original vs requalified.

Original points are drawn at their *realised* m_phi (205.4 / 255.9 / 305.2 GeV),
not at the label they were filed under -- that mislabelling is the defect this
campaign corrects, so the horizontal offset is part of the message.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CAMPAIGN = Path(__file__).resolve().parents[1]
PLOTS = CAMPAIGN / "plots"

# categorical slots 1-4 of the validated reference palette (light mode)
SERIES = [
    ("BR_gamma_gamma", "br_gammagamma", r"$\gamma\gamma$", "#2a78d6"),
    ("BR_Z_gamma", "br_Zgamma", r"$Z\gamma$", "#eb6834"),
    ("BR_bb", "br_bb", r"$b\bar{b}$", "#1baf7a"),
    ("BR_gg", "br_gg", r"$gg$", "#eda100"),
]
INK, MUTED = "#1a1a19", "#6b6a63"


def style(ax):
    ax.set_facecolor("#fcfcfb")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#d5d4cc")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, which="major", color="#e8e7e1", lw=0.7, zorder=0)
    ax.set_axisbelow(True)


def main() -> int:
    PLOTS.mkdir(exist_ok=True)
    tgt = list(csv.DictReader((CAMPAIGN / "work/targets.csv").open()))
    val = list(csv.DictReader((CAMPAIGN / "validated/photonic_requalified.csv").open()))

    m_orig = [float(r["mH_calclh_GeV"]) for r in tgt]
    m_new = [float(r["selected_m_phi_GeV"]) for r in val]

    # ---------------------------------------------------------------- plot 1
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=200)
    style(ax)
    for tkey, vkey, lab, col in SERIES:
        yo = [float(r[tkey]) for r in tgt]
        yn = [float(r[f"selected_{vkey}"]) for r in val]
        ax.plot(m_orig, yo, ls="--", lw=2, color=col, marker="o", ms=8,
                mfc="#fcfcfb", mew=2, zorder=3)
        ax.plot(m_new, yn, ls="-", lw=2, color=col, marker="o", ms=8,
                mec="#fcfcfb", mew=1.5, zorder=4)
        # stagger the two near-degenerate small BRs so their labels don't tangle
        dy = {"BR_bb": 9, "BR_gg": -11}.get(tkey, 0)
        ax.annotate(lab, (m_orig[-1], yo[-1]), xytext=(12, dy),
                    textcoords="offset points", color=col, fontsize=11,
                    va="center", fontweight="bold")
    ax.set_yscale("log")
    ax.set_xlabel(r"$m_\phi$  [GeV]", color=INK, fontsize=11)
    ax.set_ylabel(r"BR$(\phi \to XX)$", color=INK, fontsize=11)
    ax.set_xlim(192, 337)
    ax.set_title("Photonic benchmark branching ratios: original vs requalified",
                 color=INK, fontsize=12, fontweight="bold", loc="left", pad=14)
    h = [plt.Line2D([], [], color=MUTED, ls="--", lw=2, marker="o", ms=8,
                    mfc="#fcfcfb", mew=2),
         plt.Line2D([], [], color=MUTED, ls="-", lw=2, marker="o", ms=8,
                    mec="#fcfcfb", mew=1.5)]
    ax.legend(h, ["original (at realised $m_\\phi$)", "requalified (at nominal $m_\\phi$)"],
              frameon=False, fontsize=9, labelcolor=MUTED,
              loc="center left", bbox_to_anchor=(0.02, 0.42), handlelength=3.4)
    fig.tight_layout()
    fig.savefig(PLOTS / "photonic_BR_original_vs_requalified.png",
                facecolor="#fcfcfb")
    plt.close(fig)

    # ---------------------------------------------------------------- plot 2
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=200)
    style(ax)
    co = [float(r["ctau_mm"]) for r in tgt]
    cn = [float(r["selected_ctau_mm"]) for r in val]
    ax.plot(m_orig, co, ls="--", lw=2, color="#2a78d6", marker="o", ms=9,
            mfc="#fcfcfb", mew=2, label="original (at realised $m_\\phi$)", zorder=3)
    ax.plot(m_new, cn, ls="-", lw=2, color="#2a78d6", marker="o", ms=9,
            mec="#fcfcfb", mew=1.5, label="requalified (at nominal $m_\\phi$)", zorder=4)
    for x, y in zip(m_new, cn):
        ax.annotate(f"{y:.0f} mm", (x, y), xytext=(-11, 9), textcoords="offset points",
                    ha="right", fontsize=9, color=INK, fontweight="bold")
    for x, y in zip(m_orig, co):
        ax.annotate(f"{y:.0f} mm", (x, y), xytext=(9, -14), textcoords="offset points",
                    ha="left", fontsize=9, color=MUTED)
    ax.set_yscale("log")
    ax.set_xlabel(r"$m_\phi$  [GeV]", color=INK, fontsize=11)
    ax.set_ylabel(r"$c\tau$  [mm]", color=INK, fontsize=11)
    ax.set_xlim(192, 322)
    ax.set_ylim(130, 1050)
    ax.set_title(r"Photonic benchmark $c\tau$: original vs requalified",
                 color=INK, fontsize=12, fontweight="bold", loc="left", pad=14)
    ax.legend(frameon=False, fontsize=9, labelcolor=MUTED, handlelength=3.4,
              loc="upper right")
    fig.tight_layout()
    fig.savefig(PLOTS / "photonic_ctau_original_vs_requalified.png",
                facecolor="#fcfcfb")
    plt.close(fig)

    print("wrote plots/photonic_BR_original_vs_requalified.png")
    print("wrote plots/photonic_ctau_original_vs_requalified.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
