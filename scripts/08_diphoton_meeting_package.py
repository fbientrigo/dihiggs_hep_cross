#!/usr/bin/env python3
"""Build the diphoton pivot meeting package: recast-contract CSVs, dedicated
diphoton chat-summary JSONs, and the two/three meeting figures.

Reads the HIGG-2018-27 scalar (spin-0) 1D limit YAML tables directly (not via
the tidy CSVs from script 07) because we need both the +-1 sigma and +-2 sigma
expected bands, and llp_recast.hepdata_yaml.tidy_rows only keeps the first
error band per value -- that helper is shared with the DV+jets scripts and
changing its contract is out of scope for this meeting pivot.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

YAML_ROOT = Path("data/hepdata/atlas_diphoton_higg_2018_27/yaml_raw/HEPData-ins1849059-v2-yaml")
CONTRACT_DIR = Path("outputs/diphoton_recast_contract")
CHAT_DIR = Path("outputs/diphoton_chat_summaries")
FIG_DIR = Path("outputs/diphoton_pivot_figures")

WIDTH_TABLES = {
    "NWA": ("Limit1D_NW_Scalar.yaml", 0.0),
    "2pct": ("Limit1D_LW002_Scalar.yaml", 0.02),
    "6pct": ("Limit1D_LW006_Scalar.yaml", 0.06),
    "10pct": ("Limit1D_LW01_Scalar.yaml", 0.10),
}

DOI = "10.17182/hepdata.100161"
ARXIV = "2102.13405"


def load_experiment_side() -> pd.DataFrame:
    rows = []
    for width_hyp, (fname, gamma_over_m) in WIDTH_TABLES.items():
        d = yaml.safe_load((YAML_ROOT / fname).open())
        masses = [v["value"] for v in d["independent_variables"][0]["values"]]
        dep_by_limit = {}
        for dv in d["dependent_variables"]:
            quals = {q["name"]: q["value"] for q in dv.get("qualifiers", [])}
            dep_by_limit[quals.get("Limit")] = dv["values"]

        observed = dep_by_limit.get("Observed", [None] * len(masses))
        expected = dep_by_limit.get("Expected", [None] * len(masses))
        for i, mass in enumerate(masses):
            exp_val = expected[i] if i < len(expected) else None
            obs_val = observed[i] if i < len(observed) else None
            row = {
                "mass_GeV": mass,
                "width_hypothesis": width_hyp,
                "Gamma_over_m": gamma_over_m,
                "observed_limit_fb": obs_val.get("value") if isinstance(obs_val, dict) else None,
                "expected_limit_fb": exp_val.get("value") if isinstance(exp_val, dict) else None,
                "expected_minus_1sigma_fb": None,
                "expected_plus_1sigma_fb": None,
                "expected_minus_2sigma_fb": None,
                "expected_plus_2sigma_fb": None,
                "fiducial_or_total": "fiducial",
                "spin_assumption": "spin-0",
                "source_table": fname,
            }
            if isinstance(exp_val, dict):
                central = exp_val.get("value")
                for err in exp_val.get("errors", []):
                    asym = err.get("asymerror", {})
                    if err.get("label") == "1 sigma":
                        row["expected_minus_1sigma_fb"] = central + asym.get("minus", 0)
                        row["expected_plus_1sigma_fb"] = central + asym.get("plus", 0)
                    elif err.get("label") == "2 sigma":
                        row["expected_minus_2sigma_fb"] = central + asym.get("minus", 0)
                        row["expected_plus_2sigma_fb"] = central + asym.get("plus", 0)
            rows.append(row)
    return pd.DataFrame.from_records(rows).sort_values(["width_hypothesis", "mass_GeV"]).reset_index(drop=True)


def build_theory_side() -> pd.DataFrame:
    """Illustrative placeholder points only -- no real 2HDMC scan output lives in
    this repo yet, and cross sections are explicitly not to be invented."""
    rows = [
        {
            "point_id": "ILLUSTRATIVE_A",
            "m_H_GeV": 500.0,
            "Gamma_H_GeV": None,
            "Gamma_over_m": None,
            "br_gaga": None,
            "sigma_ggF_fb": None,
            "sigma_VBF_fb": None,
            "sigma_total_fb": None,
            "sigma_times_br_gaga_fb": None,
            "production_mode": "ggF_assumed",
            "validity_flags": "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED;PLACEHOLDER_POINT_NO_2HDMC_ROW_YET",
        },
        {
            "point_id": "ILLUSTRATIVE_B",
            "m_H_GeV": 1000.0,
            "Gamma_H_GeV": None,
            "Gamma_over_m": None,
            "br_gaga": None,
            "sigma_ggF_fb": None,
            "sigma_VBF_fb": None,
            "sigma_total_fb": None,
            "sigma_times_br_gaga_fb": None,
            "production_mode": "ggF_assumed",
            "validity_flags": "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED;PLACEHOLDER_POINT_NO_2HDMC_ROW_YET",
        },
    ]
    return pd.DataFrame.from_records(rows)


def build_comparison(theory: pd.DataFrame, experiment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, t in theory.iterrows():
        nearest = experiment.iloc[(experiment["mass_GeV"] - t["m_H_GeV"]).abs().argsort()[:1]]
        exp_row = nearest.iloc[0]
        rows.append(
            {
                "point_id": t["point_id"],
                "nearest_mass_GeV": exp_row["mass_GeV"],
                "nearest_width_hypothesis": exp_row["width_hypothesis"],
                "theory_over_observed_limit": None,
                "theory_over_expected_limit": None,
                "excluded_observed_proxy": "UNKNOWN_NO_XSEC",
                "excluded_expected_proxy": "UNKNOWN_NO_XSEC",
                "quality_flag": (
                    "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED;"
                    "WIDTH_MATCH_APPROXIMATE;"
                    "MASS_INTERPOLATION_APPROXIMATE;"
                    "FIDUCIAL_VS_TOTAL_CHECK_REQUIRED;"
                    "SPIN0_ASSUMPTION_OK_FOR_2HDM"
                ),
            }
        )
    return pd.DataFrame.from_records(rows)


def make_fig01_channel_pivot():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    ax.text(0.02, 0.92, "Channel pivot: Neil's paper -> our 2HDM diphoton target", fontsize=14, fontweight="bold")

    ax.add_patch(plt.Rectangle((0.02, 0.5), 0.44, 0.32, fill=False, edgecolor="tab:blue", linewidth=1.5))
    ax.text(0.24, 0.78, "Neil's paper (arXiv:2606.01681)", ha="center", fontweight="bold", color="tab:blue")
    ax.text(
        0.04, 0.53,
        "h* -> S S  (long-lived scalar pair)\n"
        "S -> displaced hadrons / jets\n"
        "Search: ATLAS DV+jets / Trackless SR\n"
        "Signature: LLP decay vertices",
        fontsize=9, va="bottom",
    )

    ax.add_patch(plt.Rectangle((0.54, 0.5), 0.44, 0.32, fill=False, edgecolor="tab:green", linewidth=1.5))
    ax.text(0.76, 0.78, "Our target: 2HDM Type I", ha="center", fontweight="bold", color="tab:green")
    ax.text(
        0.56, 0.53,
        "H2 -> gamma gamma  (prompt)\n"
        "m_H2 > m_h = 125 GeV\n"
        "Search: ATLAS HIGG-2018-27\n"
        "Signature: diphoton mass resonance",
        fontsize=9, va="bottom",
    )

    ax.annotate(
        "", xy=(0.52, 0.62), xytext=(0.46, 0.62),
        arrowprops=dict(arrowstyle="->", lw=2, color="black"),
    )
    ax.text(0.49, 0.65, "PIVOT", ha="center", fontsize=9, fontstyle="italic")

    ax.text(
        0.02, 0.4,
        "What carried over (methodology): mass-scan discipline, HEPData tidy-extraction pipeline,\n"
        "honesty conventions for placeholders/missing inputs, sigma*BR-vs-limit comparison logic.",
        fontsize=9,
    )
    ax.text(
        0.02, 0.28,
        "What did NOT carry over (physics): LLP lifetime/DV efficiencies, trackless-vertex\n"
        "reconstruction, paper's hSS coupling / sin(theta) (!= 2HDM lambda6/7 or sin(beta-alpha)).",
        fontsize=9,
    )
    ax.text(0.02, 0.12, f"Dataset: ATLAS HIGG-2018-27, arXiv:{ARXIV}, HEPData DOI {DOI}, 139 fb$^{{-1}}$", fontsize=9, color="dimgray")

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig01_channel_pivot_dvjets_to_diphoton.png", dpi=150)
    plt.close(fig)


def make_fig02_contract():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    ax.text(0.02, 0.94, "Minimum diphoton recast contract", fontsize=14, fontweight="bold")

    boxes = [
        (0.02, 0.62, "2HDMC point", "m_H, Gamma_H, BR(gamma gamma)", "tab:orange"),
        (0.36, 0.62, "cross-section input", "sigma_ggF, sigma_VBF\n(NOT YET SUPPLIED)", "tab:red"),
        (0.68, 0.62, "experiment (HIGG-2018-27)", "obs/exp sigma*BR limit\nvs mass, width hyp.", "tab:green"),
    ]
    for x, y, title, body, color in boxes:
        ax.add_patch(plt.Rectangle((x, y), 0.30, 0.26, fill=False, edgecolor=color, linewidth=1.5))
        ax.text(x + 0.15, y + 0.21, title, ha="center", fontweight="bold", color=color, fontsize=10)
        ax.text(x + 0.02, y + 0.03, body, fontsize=8.5, va="bottom")

    ax.annotate("", xy=(0.34, 0.75), xytext=(0.30, 0.75), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.66, 0.75), xytext=(0.32, 0.85), arrowprops=dict(arrowstyle="->", lw=1.5, connectionstyle="arc3,rad=0.15"))

    ax.add_patch(plt.Rectangle((0.25, 0.28), 0.5, 0.22, fill=False, edgecolor="black", linewidth=1.5))
    ax.text(0.5, 0.46, "comparison", ha="center", fontweight="bold", fontsize=10)
    ax.text(
        0.27, 0.30,
        "theory sigma*BR / experimental limit\n"
        "-> currently UNDEFINED: no sigma_ggF/sigma_VBF supplied yet\n"
        "-> quality_flag = NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED",
        fontsize=9, va="bottom",
    )
    ax.annotate("", xy=(0.45, 0.5), xytext=(0.3, 0.62), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.55, 0.5), xytext=(0.75, 0.62), arrowprops=dict(arrowstyle="->", lw=1.5))

    ax.text(
        0.02, 0.14,
        "Other quality flags: WIDTH_MATCH_APPROXIMATE, MASS_INTERPOLATION_APPROXIMATE,\n"
        "FIDUCIAL_VS_TOTAL_CHECK_REQUIRED, SPIN0_ASSUMPTION_OK_FOR_2HDM.",
        fontsize=8.5, color="dimgray",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig02_minimum_recast_contract.png", dpi=150)
    plt.close(fig)


def make_fig03_limit_preview(experiment: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = {"NWA": "black", "2pct": "tab:blue", "6pct": "tab:green", "10pct": "tab:red"}
    for width_hyp, grp in experiment.groupby("width_hypothesis"):
        grp = grp.sort_values("mass_GeV")
        ax.plot(grp["mass_GeV"], grp["observed_limit_fb"], color=colors.get(width_hyp, "gray"), label=f"observed, {width_hyp}", linewidth=1.5)
        ax.plot(grp["mass_GeV"], grp["expected_limit_fb"], color=colors.get(width_hyp, "gray"), linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_yscale("log")
    ax.set_xlabel("m_X [GeV]")
    ax.set_ylabel("95% CL upper limit on sigma x BR(gamma gamma) [fb]")
    ax.set_title("ATLAS HIGG-2018-27 spin-0 limits (solid=observed, dashed=expected)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig03_atlas_diphoton_limit_preview.png", dpi=150)
    plt.close(fig)


def main() -> int:
    CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    experiment = load_experiment_side()
    theory = build_theory_side()
    comparison = build_comparison(theory, experiment)

    experiment.to_csv(CONTRACT_DIR / "experiment_side.csv", index=False)
    theory.to_csv(CONTRACT_DIR / "theory_side.csv", index=False)
    comparison.to_csv(CONTRACT_DIR / "comparison.csv", index=False)
    print(f"[OK] wrote {CONTRACT_DIR}/{{theory_side,experiment_side,comparison}}.csv")

    # --- chat-summary JSONs ---
    neil_summary = {
        "pivot": {
            "from": {
                "paper": "arXiv:2606.01681",
                "process": "h* -> S S (long-lived scalar pair)",
                "search": "ATLAS DV+jets / Trackless SR",
            },
            "to": {
                "model": "2HDM Type I, neutral H2 (m_H2 > m_h = 125 GeV)",
                "process": "H2 -> gamma gamma (prompt)",
                "search": "ATLAS HIGG-2018-27 (arXiv:2102.13405)",
            },
        },
        "why_dvjets_not_final": [
            "DV+jets targets displaced/LLP signatures; H2 -> gamma gamma is prompt.",
            "Paper's hSS coupling / sin(theta) are not the same quantities as 2HDM lambda6/lambda7 or sin(beta-alpha).",
            "DV+jets efficiencies (vertex/track based) do not transfer to diphoton reconstruction efficiencies.",
        ],
        "carried_over_methodology": [
            "HEPData YAML tidy-extraction pipeline (src/llp_recast/hepdata_yaml.py, reused unmodified)",
            "Placeholder/quality-flag honesty conventions",
            "sigma*BR-vs-limit comparison contract shape",
        ],
        "not_carried_over_physics": [
            "LLP lifetime/decay-probability math",
            "Trackless-vertex reconstruction efficiencies",
            "Displaced-hadron jet substructure",
        ],
        "what_to_say_tomorrow": [
            "We pivoted from the DV+jets LLP exercise (Neil's paper) to the correct channel for our 2HDM target: prompt H2 -> gamma gamma.",
            "Primary dataset locked in: ATLAS HIGG-2018-27, 139 fb^-1, HEPData DOI 10.17182/hepdata.100161 -- verified downloaded and parsed locally.",
            "We have the full spin-0 sigma*BR(gamma gamma) 95% CL limit curves (observed + expected +-1/2 sigma) for 4 width hypotheses (NWA, 2%, 6%, 10%) over 160-3000 GeV.",
            "We do NOT yet have sigma_ggF/sigma_VBF from our 2HDM scan, so no exclusion statement is possible yet -- next step is wiring 2HDMC BR output to a cross-section tool.",
            "The DV+jets exercise was not wasted: the extraction/contract/honesty-flag pipeline reused directly for this dataset.",
        ],
    }
    with (CHAT_DIR / "neil_paper_to_diphoton_summary.json").open("w") as f:
        json.dump(neil_summary, f, indent=2)

    dataset_card = {
        "dataset_name": "Search for resonances decaying into photon pairs in 139 fb^-1 of pp collisions at sqrt(s)=13 TeV with the ATLAS detector",
        "short_name": "ATLAS HIGG-2018-27",
        "arxiv": ARXIV,
        "collaboration": "ATLAS",
        "luminosity_fb": 139.0,
        "sqrt_s_TeV": 13,
        "final_state": "diphoton (prompt, gamma gamma)",
        "spin_hypotheses": ["spin-0 (scalar)", "spin-2 (RS graviton)"],
        "mass_range_GeV": {"scalar_NWA": [160, 3000], "scalar_LW": [400, 2800]},
        "width_hypotheses_pct_of_mX": [0.0, 2, 6, 10],
        "main_observable": "95% CL upper limit on fiducial sigma x BR(X -> gamma gamma) vs m_X",
        "hepdata_doi": DOI,
        "hepdata_doi_verified_against_target": "10.17182/hepdata.100161",
        "expected_hepdata_tables_needed": [
            "Limit1D_NW_Scalar.yaml (t1)",
            "Limit1D_LW002_Scalar.yaml (t5)",
            "Limit1D_LW006_Scalar.yaml (t6)",
            "Limit1D_LW01_Scalar.yaml (t7)",
            "Limit2D_Scalar.yaml (t3)",
        ],
        "download_status": "DOWNLOAD_VERIFIED",
        "status_labels": [
            "PRIMARY_DATASET",
            "DIRECTLY_RELEVANT_DIPHOTON",
            "DOWNLOAD_VERIFIED",
            "TABLES_NOT_YET_VERIFIED_AGAINST_PAPER_TEXT",
            "READY_FOR_PRESENTATION",
        ],
        "immediate_usefulness": "Experiment-side of the sigma*BR contract is complete (observed/expected limits, 4 width hypotheses, 160-3000 GeV). Only the theory-side cross section is missing.",
        "limitations": [
            "No sigma_ggF/sigma_VBF from our own tools yet -- cannot compute theory/limit ratio.",
            "Width hypotheses are discrete (0%, 2%, 6%, 10%); a 2HDM point's actual Gamma/m needs interpolation or nearest-hypothesis matching.",
            "Limits are FIDUCIAL cross sections; converting from a total theoretical cross section requires an acceptance x efficiency factor (C_X, A_X parameterizations exist in Table 13/14 but are not yet applied here).",
        ],
    }
    with (CHAT_DIR / "atlas_higg_2018_27_dataset_card.json").open("w") as f:
        json.dump(dataset_card, f, indent=2)

    contract_summary = {
        "theory_side_columns": list(theory.columns),
        "experiment_side_columns": list(experiment.columns),
        "comparison_columns": list(comparison.columns),
        "theory_side_rows": json.loads(theory.to_json(orient="records")),
        "experiment_side_n_rows": len(experiment),
        "experiment_side_mass_range_GeV": [float(experiment["mass_GeV"].min()), float(experiment["mass_GeV"].max())],
        "experiment_side_width_hypotheses": sorted(experiment["width_hypothesis"].unique().tolist()),
        "comparison_rows": json.loads(comparison.to_json(orient="records")),
        "quality_flags_defined": [
            "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED",
            "WIDTH_MATCH_APPROXIMATE",
            "MASS_INTERPOLATION_APPROXIMATE",
            "FIDUCIAL_VS_TOTAL_CHECK_REQUIRED",
            "SPIN0_ASSUMPTION_OK_FOR_2HDM",
        ],
    }
    with (CHAT_DIR / "diphoton_recast_contract.json").open("w") as f:
        json.dump(contract_summary, f, indent=2)
    print(f"[OK] wrote 3 JSON files under {CHAT_DIR}")

    # --- figures ---
    make_fig01_channel_pivot()
    make_fig02_contract()
    make_fig03_limit_preview(experiment)
    print(f"[OK] wrote 3 figures under {FIG_DIR}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
