#!/usr/bin/env python3
"""physical_vs_M2.{png,pdf} -- Figure 2 (ORCA MISSION Phase 4): "How does the
physical coupling depend on M^2?" One representative mass, m_phi=250 GeV.
Plots the exact analytic identity (star) g = (2*M2 - 2*mphi^2 - mh^2)/v over
a broad M2/mphi^2 range, to show the physical coupling has real functional
freedom -- then annotates that this benchmark's own theory-valid window
(tan(beta)=4e7, lambda7=0) is ~8e-15 relative around M2=mphi^2, far too
narrow to render as a visible band at this scale. Single axis, one curve,
one message.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

CAMP = Path(__file__).resolve().parents[1]

mh = 125.0
mphi = 250.0
v = 246.22056907348588

C_PHYS = "#2a78d6"
C_MARK = "#c0392b"

r = np.linspace(-0.2, 2.1, 400)
M2 = r * mphi * mphi
g = (2.0 * M2 - 2.0 * mphi * mphi - mh * mh) / v

fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=150)

ax.plot(r, g, "-", color=C_PHYS, linewidth=2.5, zorder=3,
        label=r"g$_{h\phi\phi}$ = (2M$^2$ - 2m$_\phi^2$ - m$_h^2$)/v   (exact, any tanβ/λ6/λ7/mA/mH$^\pm$)")

ax.axvline(1.0, color=C_MARK, linestyle="--", linewidth=1.4, zorder=2)
g_at_1 = (2.0 * mphi * mphi - 2.0 * mphi * mphi - mh * mh) / v
ax.plot([1.0], [g_at_1], "o", color=C_MARK, markersize=8, zorder=4)
ax.annotate(f"M$^2$=m$_\\phi^2$\ng = -m$_h^2$/v = {g_at_1:.2f} GeV",
            xy=(1.0, g_at_1), xytext=(1.28, g_at_1 - 130),
            fontsize=9, color=C_MARK, ha="left",
            arrowprops=dict(arrowstyle="-", color=C_MARK, linewidth=0.9))

ax.annotate(
    "At this benchmark (tanβ=4×10$^7$, λ$_7$=0), the theory-valid\n"
    "M$^2$ window around this point is only ~8×10$^{-15}$ relative wide --\n"
    "far too narrow to draw at any readable scale on this axis.\n"
    "The physical coupling has real functional freedom in M$^2$;\n"
    "this benchmark's own inputs simply don't let it use most of it.",
    xy=(0.03, 0.04), xycoords="axes fraction", fontsize=8.3, color="#444444",
    va="bottom", ha="left",
    bbox=dict(boxstyle="round,pad=0.4", fc="#f5f5f0", ec="#cccccc", linewidth=0.7))

ax.set_xlabel(r"M$^2$ / m$_\phi^2$", fontsize=11)
ax.set_ylabel(r"g$_{h\phi\phi}$ [GeV]", fontsize=11)
ax.set_title("The physical coupling vs. M$^2$ at fixed mass (m$_\\phi$=250 GeV)\n"
             "the dial exists -- this benchmark barely lets us turn it",
             fontsize=10.5)
ax.grid(True, linewidth=0.4, color="#cccccc", alpha=0.6)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.legend(loc="upper left", frameon=False, fontsize=8.7)

fig.tight_layout()
fig.savefig(CAMP / "coupling_comparison" / "physical_vs_M2.png")
fig.savefig(CAMP / "coupling_comparison" / "physical_vs_M2.pdf")
print("wrote physical_vs_M2.{png,pdf}")
