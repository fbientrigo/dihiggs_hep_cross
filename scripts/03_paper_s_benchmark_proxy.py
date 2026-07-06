#!/usr/bin/env python3
"""Paper-aware scalar-S benchmark proxy (arXiv:2606.01681 workflow).

This is NOT a reproduction of the ATLAS DV+jets analysis and NOT an
exclusion. It takes a scalar-S benchmark grid inspired by the paper's
pp -> gg -> h* -> S S topology, applies our own ID decay-probability geometry,
and anchors the efficiency/cross-section-limit scale using ATLAS HEPData
products that were published for a *different* benchmark (chargino/neutralino
pair production, not our scalar S). Every borrowed or placeholder number is
named explicitly in `quality_flag` and `missing_inputs`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from llp_recast.constants import ATLAS_DVJETS_LUMI_FB, ID_R_MAX_MM, ID_R_MIN_MM
from llp_recast.paper_model import (
    PAPER_BENCHMARK_CTAU_MM,
    PAPER_BENCHMARK_MASSES_GEV,
    br_hadronic_proxy,
)
from llp_recast.recast_math import (
    ctau_mm_to_tau_ns,
    decay_probability_between,
    event_probability_at_least_one,
    expected_yield,
)

# ponytail: flat placeholders, not fitted curves. Replace once MG5/Pythia truth
# kinematics and a real S width calculator exist.
BETA_GAMMA_ASSUMED_PROXY = 1.0
SIGMA_FB_ASSUMED_PLACEHOLDER = 1.0
EFF_EVENT_PROXY_PLACEHOLDER = 0.5

QUALITY_FLAGS = (
    "PAPER_AWARE_PROXY_NOT_EXCLUSION;"
    "USES_PLACEHOLDER_SIGMA;"
    "USES_PLACEHOLDER_BR;"
    "HEPDATA_TABLE_PARSED;"
    "NEEDS_MG5_PYTHIA_SIGNAL;"
    "NEEDS_VALIDATION_AGAINST_PAPER_CURVES"
)


def _qual(qualifiers: str, name: str) -> str:
    for part in qualifiers.split("; "):
        if part.startswith(f"{name}="):
            return part.split("=", 1)[1]
    return ""


def eff_vertex_proxy_from_cutflow(cutflow_csv: Path) -> float:
    """Average final-step 'Full Sim A x eps' across the EWK cutflow series.

    This is borrowed from an unrelated ATLAS SUSY EWK benchmark cutflow (not
    our scalar S) and used only as an order-of-magnitude anchor for what a
    full trigger->DV->track-selection chain achieves in this analysis.
    """
    df = pd.read_csv(cutflow_csv)
    finals = df.groupby("qualifiers", sort=False).tail(1)
    return float(finals["value"].mean())


def nearest_observed_limit_fb(excl_xsec_csv: Path, mass_gev: float, tau_ns: float) -> tuple[float, float, float]:
    """Nearest ATLAS observed EWK cross-section limit (illustrative anchor only).

    The published excl_xsec_ewk table is indexed by neutralino mass and proper
    lifetime tau, not by our scalar mass mS or ctau. Returns
    (limit_fb, matched_mass_gev, matched_tau_ns).
    """
    df = pd.read_csv(excl_xsec_csv)
    df = df[df["qualifiers"].apply(lambda q: _qual(q, "Limit") == "Observed")].copy()
    df["tau_ns_tag"] = df["qualifiers"].apply(lambda q: float(_qual(q, "Lifetime").rstrip("ns")))
    nearest_tau = min(df["tau_ns_tag"].unique(), key=lambda t: abs(t - tau_ns))
    df = df[df["tau_ns_tag"] == nearest_tau]
    df["mass_col"] = df["Neutralino Mass [GeV]"].astype(float)
    row = df.iloc[(df["mass_col"] - mass_gev).abs().argsort().iloc[0]]
    return float(row["value"]), float(row["mass_col"]), float(nearest_tau)


def main() -> int:
    ap = argparse.ArgumentParser(description="Paper-aware scalar-S benchmark proxy (not an exclusion)")
    ap.add_argument("--tidy-dir", default="outputs/hepdata_tidy")
    ap.add_argument("--outdir", default="outputs/paper_s_proxy")
    args = ap.parse_args()

    tidy_dir = Path(args.tidy_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    eff_vertex_proxy = eff_vertex_proxy_from_cutflow(tidy_dir / "cutflow_trackless_ewk.csv")

    rows = []
    for mS in PAPER_BENCHMARK_MASSES_GEV:
        br_had = br_hadronic_proxy(mS, mode="paper_placeholder")
        for ctau in PAPER_BENCHMARK_CTAU_MM:
            tau_ns = ctau_mm_to_tau_ns(ctau)
            lab_len = BETA_GAMMA_ASSUMED_PROXY * ctau
            p_single = decay_probability_between(ID_R_MIN_MM, ID_R_MAX_MM, lab_len)
            p_event = event_probability_at_least_one(p_single, n_llp=2)
            aeff_proxy = p_event * EFF_EVENT_PROXY_PLACEHOLDER * eff_vertex_proxy
            br_factor = br_had ** 2
            nsig = expected_yield(ATLAS_DVJETS_LUMI_FB, SIGMA_FB_ASSUMED_PLACEHOLDER, br_factor, aeff_proxy)

            limit_fb, matched_mass, matched_tau = nearest_observed_limit_fb(
                tidy_dir / "excl_xsec_ewk.csv", mS, tau_ns
            )
            ratio = SIGMA_FB_ASSUMED_PLACEHOLDER / limit_fb if limit_fb > 0 else float("nan")

            missing_inputs = (
                "beta_gamma:flat_placeholder=1.0(needs_MG5_Pythia);"
                "sigma_fb:flat_placeholder=1.0(needs_MG5_Pythia_or_paper_curve);"
                "BR_hadronic:paper_placeholder_mode(not_from_paper_tables);"
                "eff_event_proxy:flat_placeholder=0.5(needs_truth_DV_track_kinematics);"
                f"eff_vertex_proxy:borrowed_from_EWK_cutflow_final_step_mass_tau_avg(not_scalar_S_mapped);"
                f"nearest_public_limit_fb:EWKino_benchmark_m={matched_mass:g}GeV_tau={matched_tau:g}ns(not_scalar_S_specific)"
            )

            rows.append(
                {
                    "mS_GeV": mS,
                    "ctau_mm": ctau,
                    "tau_ns": tau_ns,
                    "beta_gamma_assumed": BETA_GAMMA_ASSUMED_PROXY,
                    "sigma_fb_assumed": SIGMA_FB_ASSUMED_PLACEHOLDER,
                    "BR_hadronic_proxy": br_had,
                    "P_single_ID_4_300": p_single,
                    "P_event_at_least_one_ID": p_event,
                    "eff_event_proxy": EFF_EVENT_PROXY_PLACEHOLDER,
                    "eff_vertex_proxy": eff_vertex_proxy,
                    "aeff_proxy": aeff_proxy,
                    "Nsig_139fb": nsig,
                    "nearest_public_limit_fb": limit_fb,
                    "ratio_to_limit_proxy": ratio,
                    "quality_flag": QUALITY_FLAGS,
                    "missing_inputs": missing_inputs,
                }
            )

    df_out = pd.DataFrame.from_records(rows)
    csv_path = outdir / "paper_s_benchmark_proxy.csv"
    df_out.to_csv(csv_path, index=False)

    md_path = outdir / "paper_s_benchmark_proxy.md"
    lines = [
        "# Paper-aware scalar-S benchmark proxy",
        "",
        "**This is not a reproduction of the ATLAS analysis. This is not an ATLAS exclusion.**",
        "This is a paper-aware proxy designed to identify the missing ingredients needed",
        "for a validated recast of arXiv:2606.01681 (`pp -> gg -> h* -> S S`).",
        "",
        "## What is real vs. placeholder",
        "",
        "- Decay geometry (`P_single_ID_4_300`, `P_event_at_least_one_ID`): real analytic geometry"
        " for an exponential lab decay length between the ID baseline radii (4-300 mm).",
        "- `eff_vertex_proxy`: HEPData-derived, but borrowed from the ATLAS SUSY EWK"
        " (chargino/neutralino) cutflow's final selection step, averaged over its 4 published"
        " mass/lifetime points. It is NOT mapped to our scalar S.",
        "- `nearest_public_limit_fb`: nearest published *observed* EWK cross-section limit by"
        " lifetime and mass. The published table indexes neutralino mass, not mS -- treat this"
        " as an order-of-magnitude anchor only.",
        f"- `beta_gamma_assumed` = {BETA_GAMMA_ASSUMED_PROXY}, `sigma_fb_assumed` ="
        f" {SIGMA_FB_ASSUMED_PLACEHOLDER} fb, `eff_event_proxy` = {EFF_EVENT_PROXY_PLACEHOLDER}:"
        " flat documented placeholders, not derived from MC or the paper.",
        "- `BR_hadronic_proxy`: `paper_placeholder` mode (mS<140 GeV -> 0.8, mS>=140 GeV -> 0.5),"
        " not read from the paper's own branching-fraction tables.",
        "",
        "## Columns",
        "",
        "See `paper_s_benchmark_proxy.csv`. Every row also carries `quality_flag` and"
        " `missing_inputs` documenting exactly what is placeholder vs. HEPData-derived.",
        "",
        "## What would make this validation-grade",
        "",
        "1. FeynRules/UFO -> MadGraph5_aMC@NLO -> Pythia signal MC for `pp -> gg -> h* -> S S`,",
        "   giving a real `sigma_fb_assumed`, `beta_gamma` distribution, and truth DV kinematics.",
        "2. A scalar-S branching-fraction table (from the paper, HDECAY, or a dedicated width",
        "   calculator) to replace `BR_hadronic_proxy`.",
        "3. Truth-level DV mass / track multiplicity per benchmark point so that",
        "   `vertex_efficiency_grid.csv` and `event_efficiency_trackless.csv` can be looked up",
        "   directly instead of using flat placeholders.",
        "4. Comparison against the paper's own benchmark curves (Fig. references) once available,",
        "   not just the EWK cross-section limit used here as a scale anchor.",
        "",
        f"Rows: {len(df_out)}. Masses: {PAPER_BENCHMARK_MASSES_GEV} GeV."
        f" ctau grid: {PAPER_BENCHMARK_CTAU_MM} mm.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {md_path}")
    print("[NOTE] This is a paper-aware proxy. It is not an ATLAS exclusion and not a reproduction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
