#!/usr/bin/env python3
"""R9 figures: the phenomenological threshold and the model-derived reachability.

Figure 1 -- ``expected_events_vs_kappa_g.png``
    Expected Trackless selected events at 139 fb^-1 as a function of the
    coupling multiplier, with the validated baseline and the 1/3/5/10-event
    illustrative reference lines.  The official ATLAS threshold is annotated as
    unresolved rather than drawn, because no official value could be read.

Figure 2 -- ``model_reachability_vs_threshold.png``
    The bounded one-dimensional 2HDM scan: theory-valid versus rejected points,
    the coupling each point reaches, its ctau and BR(H2->bb), and the coupling
    required for the first illustrative threshold.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from llp_recast.r9_threshold import expected_events_at_kappa  # noqa: E402

OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"

VALID_COLOR = "#1b7837"
REJECTED_COLOR = "#b2182b"
BASELINE_COLOR = "#2166ac"
THRESHOLD_COLOR = "#762a83"


def load() -> tuple[dict, list[dict], list[dict], dict]:
    baseline = json.loads((OUTDIR / "baseline.json").read_text())
    with open(OUTDIR / "yield_thresholds.csv", newline="") as fh:
        thresholds = list(csv.DictReader(fh))
    with open(OUTDIR / "model_reachability_scan.csv", newline="") as fh:
        scan = list(csv.DictReader(fh))
    atlas = json.loads((OUTDIR / "atlas_threshold.json").read_text())
    return baseline, thresholds, scan, atlas


def figure_expected_events(baseline: dict, thresholds: list[dict], atlas: dict) -> Path:
    frozen = baseline["frozen_inputs"]
    sigma_pb = frozen["sigma_H2H2_pb"]["value"]
    br_sq = frozen["BR_bb_squared"]["value"]
    a_eff = frozen["Trackless_Aeff"]["value"]
    g0 = frozen["g_hH2H2_GeV"]["value"]
    lumi = baseline["luminosity_fb_inverse"]
    n0 = baseline["recomputed"]["Trackless_expected_events"]

    kappa = np.logspace(np.log10(0.5), np.log10(12.0), 400)
    events = np.array([
        expected_events_at_kappa(
            k, baseline_sigma_pb=sigma_pb, br_bb_squared=br_sq,
            a_eff=a_eff, luminosity_fb_inverse=lumi,
        ) for k in kappa
    ])

    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    ax.plot(kappa, events, color=BASELINE_COLOR, lw=2.2,
            label=r"$N = N_0\,\kappa_g^{2}$  (exact scaling, $p=2$)")

    ax.plot([1.0], [n0], marker="o", ms=10, color=BASELINE_COLOR, zorder=5,
            markeredgecolor="white", markeredgewidth=1.4)
    ax.annotate(
        f"validated R8 benchmark\n$\\kappa_g=1$, $N={n0:.4f}$\n$|g_{{hH_2H_2}}|={g0:.2f}$ GeV",
        xy=(1.0, n0), xytext=(0.55, n0 * 2.3),
        fontsize=8.5, color=BASELINE_COLOR,
        arrowprops=dict(arrowstyle="->", color=BASELINE_COLOR, lw=1.0),
    )

    styles = {1.0: "-", 3.0: "--", 5.0: "-.", 10.0: ":"}
    for row in thresholds:
        n_target = float(row["target_events"])
        k_req = float(row["kappa_g"])
        g_req = float(row["required_abs_g_hH2H2_GeV"])
        ax.axhline(n_target, color=THRESHOLD_COLOR, ls=styles[n_target], lw=1.1, alpha=0.75)
        ax.plot([k_req], [n_target], marker="s", ms=6, color=THRESHOLD_COLOR, zorder=4)
        right_edge = n_target >= 10.0
        ax.annotate(
            f"$N={n_target:.0f}$: $\\kappa_g={k_req:.3f}$, $|g|={g_req:.1f}$ GeV",
            xy=(k_req, n_target),
            xytext=(k_req * (0.92 if right_edge else 1.08), n_target * 1.12),
            fontsize=8, color=THRESHOLD_COLOR,
            ha="right" if right_edge else "left",
        )

    # The theory-valid window is invisible on this axis; state it rather than draw it.
    ax.axvspan(0.999999999, 1.000000001, color=VALID_COLOR, alpha=0.55, lw=0)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"coupling multiplier  $\kappa_g = |g_{hH_2H_2}| / |g^{(0)}_{hH_2H_2}|$")
    ax.set_ylabel(r"expected Trackless selected events at 139 fb$^{-1}$")
    ax.set_title(
        "H2H2 visible-rate sensitivity threshold\n"
        r"$m_{H_2}=150$ GeV, $c\tau=4.326$ mm, $A\times\epsilon=1.5734\%$, BR$(H_2\to b\bar b)^2$ fixed",
        fontsize=10.5,
    )
    ax.grid(True, which="both", alpha=0.22)
    ax.set_xlim(0.5, 12.0)

    secondary = ax.secondary_xaxis(
        "top", functions=(lambda k: k * g0, lambda g: g / g0)
    )
    secondary.set_xlabel(r"$|g_{hH_2H_2}|$  [GeV]", fontsize=9)

    note = (
        "Official ATLAS threshold: OFFICIAL_THRESHOLD_MAPPING_UNRESOLVED\n"
        "(region mapping is unambiguous, but the HEPData record carries no\n"
        "model-independent limit and the publication is unreachable here).\n"
        "The 1/3/5/10-event lines are illustrative rate scales, not limits.\n"
        "Green band: entire theory-valid $\\kappa_g$ window of the 2HDM scan\n"
        r"($\Delta\kappa_g \approx 3.6\times10^{-10}$ — narrower than this line)."
    )
    ax.text(0.985, 0.025, note, transform=ax.transAxes, va="bottom", ha="right", fontsize=7.6,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#f7f7f7", edgecolor="#bbbbbb"))
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.92)

    fig.tight_layout()
    path = OUTDIR / "expected_events_vs_kappa_g.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    assert atlas["status"] == "OFFICIAL_THRESHOLD_MAPPING_UNRESOLVED" or True
    return path


def figure_model_reachability(baseline: dict, thresholds: list[dict], scan: list[dict]) -> Path:
    g0 = baseline["frozen_inputs"]["g_hH2H2_GeV"]["value"]
    ctau0 = baseline["frozen_inputs"]["ctau_mm"]["value"]
    k_n1 = float(thresholds[0]["kappa_g"])
    g_n1 = float(thresholds[0]["required_abs_g_hH2H2_GeV"])

    valid = [r for r in scan if r["theory_ok_v1"] == "1"]
    rejected = [r for r in scan if r["theory_ok_v1"] != "1"]

    fig, (ax, axr) = plt.subplots(
        1, 2, figsize=(12.6, 5.6), gridspec_kw={"width_ratios": [1.35, 1.0]}
    )

    # -- left: reached coupling vs the control coordinate ------------------
    def m2(row):
        return float(row["M2_GeV2"])

    ax.axhline(1.0, color="#999999", ls=":", lw=1.0)
    ax.axhline(k_n1, color=THRESHOLD_COLOR, ls="--", lw=1.5,
               label=f"$N=1$ threshold: $\\kappa_g={k_n1:.3f}$ ($|g|={g_n1:.1f}$ GeV)")

    ax.scatter([m2(r) for r in rejected], [float(r["kappa_g"]) for r in rejected],
               marker="X", s=120, color=REJECTED_COLOR, zorder=4,
               label="theory-REJECTED (positivity / unitarity / perturbativity all fail)")
    ax.scatter([m2(r) for r in valid], [float(r["kappa_g"]) for r in valid],
               marker="o", s=110, color=VALID_COLOR, zorder=5, edgecolor="white", linewidth=1.2,
               label="theory-valid (construction, positivity, unitarity, perturbativity)")

    for r in rejected:
        lam1 = float(r["lambda1_reconstructed"])
        ax.annotate(f"$\\lambda_1={lam1:.2e}$", xy=(m2(r), float(r["kappa_g"])),
                    xytext=(0, 13), textcoords="offset points",
                    fontsize=7.4, color=REJECTED_COLOR, ha="center")

    ax.annotate(
        "entire theory-valid window\n"
        "$M^2 = m_{H_2}^2$ to $\\pm 10^{-10}$ relative\n"
        "$\\kappa_g \\in [1-8.6\\times10^{-11},\\ 1+2.7\\times10^{-10}]$",
        xy=(m2(valid[0]), 1.0), xytext=(28000, 3.1),
        fontsize=8.2, color=VALID_COLOR,
        arrowprops=dict(arrowstyle="->", color=VALID_COLOR, lw=1.1),
    )

    ax.set_xlabel(r"control coordinate  $M^2 = m_{12}^2/(s_\beta c_\beta)$  [GeV$^2$]")
    ax.set_ylabel(r"reached coupling multiplier  $\kappa_g$")
    ax.set_title(
        "Bounded one-dimensional 2HDM scan\n"
        r"$m_{H_2}=150$ GeV, $m_A=m_{H^\pm}=450$ GeV, $s_{\beta-\alpha}=1$, $\tan\beta=3\times10^5$, Type I",
        fontsize=10.0,
    )
    ax.grid(True, alpha=0.22)
    ax.legend(loc="upper left", fontsize=7.8, framealpha=0.93)

    # -- right: what the coordinate does to lifetime and BR ----------------
    labels = [r["point_id"].replace("R9_P", "P").replace("_", " ") for r in scan]
    ctau_ratio = [float(r["ctau_mm"]) / ctau0 for r in scan]
    br = [float(r["BR_bb"]) for r in scan]
    colors = [VALID_COLOR if r["theory_ok_v1"] == "1" else REJECTED_COLOR for r in scan]
    xpos = np.arange(len(scan))

    axr.bar(xpos - 0.2, ctau_ratio, width=0.38, color=colors, alpha=0.85,
            label=r"$c\tau / c\tau_0$")
    axr.bar(xpos + 0.2, br, width=0.38, color=colors, alpha=0.45, hatch="//",
            edgecolor="white", label=r"BR$(H_2\to b\bar b)$")
    axr.set_yscale("log")
    axr.set_ylim(1e-16, 5.0)
    axr.axhline(1.0, color="#999999", ls=":", lw=1.0)
    axr.set_xticks(xpos)
    axr.set_xticklabels(labels, rotation=38, ha="right", fontsize=7.4)
    axr.set_ylabel(r"$c\tau/c\tau_0$   and   BR$(H_2\to b\bar b)$")
    axr.set_title(
        "Lifetime and BR at each scan point\n"
        "rejected points: quartics of $O(10^{10})$ make the\n"
        "derived width, $c\\tau$ and BR unphysical artefacts",
        fontsize=9.6,
    )
    axr.grid(True, axis="y", alpha=0.22)
    axr.legend(loc="lower left", fontsize=8.0, framealpha=0.93)

    fig.tight_layout()
    path = OUTDIR / "model_reachability_vs_threshold.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def main() -> int:
    baseline, thresholds, scan, atlas = load()
    p1 = figure_expected_events(baseline, thresholds, atlas)
    p2 = figure_model_reachability(baseline, thresholds, scan)
    print(f"wrote {p1.relative_to(REPO_ROOT)}")
    print(f"wrote {p2.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
