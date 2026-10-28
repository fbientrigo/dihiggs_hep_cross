#!/usr/bin/env python3
"""coupling_vs_mass.{png,pdf} -- Phase 6 required plot.
Physical 2HDM coupling (ground truth, M2=mphi^2 anchor) vs the two
effective prescriptions, across the 3 benchmark masses. Log y-axis: single
axis (no dual-axis), needed because EF_simple spans ~20-45x the physical
curve's scale -- collapsing that onto linear y would flatten the physical/
EF_m2 curves to invisibility.
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

CAMP = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(CAMP / "coupling_comparison" / "coupling_table.csv")))
masses = [float(r["mphi_GeV"]) for r in rows]
physical = [abs(float(r["physical_2HDM_GeV"])) for r in rows]
ef_simple = [float(r["EF_simple_GeV"]) for r in rows]
ef_m2 = [float(r["EF_m2_GeV"]) for r in rows]

# Validated categorical palette (dataviz skill reference instance, already
# used and CVD-validated in campaigns/20260901_photonic_requalification/scripts/make_plots.py).
C_PHYS = "#2a78d6"
C_EFSIMPLE = "#eb6834"
C_EFM2 = "#1baf7a"

fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=150)
ax.set_yscale("log")

ax.plot(masses, physical, "-o", color=C_PHYS, linewidth=2, markersize=7, zorder=3,
        label=r"physical 2HDM (2HDMC, M$^2$=m$_\phi^2$ anchor)")
ax.plot(masses, ef_simple, "-s", color=C_EFSIMPLE, linewidth=2, markersize=7, zorder=3,
        label=r"EF$_{\rm simple}$ = 8m$_\phi^2$/v")
ax.plot(masses, ef_m2, "-^", color=C_EFM2, linewidth=2, markersize=7, zorder=3,
        label=r"EF$_{m2}$ = 8(m$_\phi^2$-M$_{22}^2$)/v  (Higgs-basis M$_{22}^2$, not the M$^2$ anchor above)")

for x, y in zip(masses, physical):
    ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 9),
                ha="center", fontsize=8.5, color=C_PHYS)
for x, y in zip(masses, ef_simple):
    ax.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=8.5, color=C_EFSIMPLE)
for x, y in zip(masses, ef_m2):
    ax.annotate(f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 8),
                ha="center", fontsize=8.5, color=C_EFM2)

ax.set_xlabel(r"m$_\phi$ [GeV]", fontsize=11)
ax.set_ylabel(r"|g$_{h\phi\phi}$| [GeV]  (log scale)", fontsize=11)
ax.set_title("Physical vs. effective h-φ-φ coupling\n"
             "(exact alignment, mA=mH$^\\pm$=300 GeV, λ$_6$ frozen, tanβ=4×10$^7$ benchmark)",
             fontsize=10.5)
ax.set_xticks(masses)
ax.set_ylim(40, 12000)
ax.grid(True, which="both", axis="y", linewidth=0.4, color="#cccccc", alpha=0.6)
ax.grid(True, which="major", axis="x", linewidth=0.4, color="#cccccc", alpha=0.6)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.72), frameon=False, fontsize=9)
ax.annotate("physical_2HDM is nearly flat here because this benchmark's\n"
            "M$^2$ tracks m$_\\phi^2$ (forced only within its λ$_7$=0 slice --\n"
            "not a general property of the physical coupling, see §4).\n"
            "EF$_{simple}$ grows as 8m$_\\phi^2$/v by definition.",
            xy=(0.98, 0.97), xycoords="axes fraction", fontsize=7.8, color="#666666",
            va="top", ha="right")

fig.tight_layout()
fig.savefig(CAMP / "coupling_comparison" / "coupling_vs_mass.png")
fig.savefig(CAMP / "coupling_comparison" / "coupling_vs_mass.pdf")
print("wrote coupling_vs_mass.{png,pdf}")
