"""Data-preparation for the paper-aware figures (arXiv:2606.01681 recast scaffold).

No matplotlib import here on purpose: these functions must stay importable and
unit-testable even before the plotting dependency is installed. Rendering lives
in scripts/04_make_paper_aware_figures.py.
"""
from __future__ import annotations

import pandas as pd

from .constants import ID_R_MAX_MM, ID_R_MIN_MM
from .hepdata_yaml import parse_bin_label
from .recast_math import decay_probability_between_radii

# Radial category is only encoded in the filename for these 3 event-efficiency tables.
EVENT_EFFICIENCY_RADIAL_CATEGORIES = {
    "event_efficiency_trackless_r_1150_mm.yaml": "R < 1150 mm",
    "event_efficiency_trackless_r_1150_3870_mm.yaml": "1150 < R < 3870 mm",
    "event_efficiency_trackless_r_3870_mm.yaml": "R > 3870 mm",
}


def prepare_fig1_sweetspot(
    ctau_mm_values: list[float],
    beta_gamma_values: list[float],
    r_min_mm: float = ID_R_MIN_MM,
    r_max_mm: float = ID_R_MAX_MM,
) -> pd.DataFrame:
    """P(decay inside [r_min_mm, r_max_mm)) vs ctau_mm, one curve per beta_gamma."""
    rows = []
    for beta_gamma in beta_gamma_values:
        for ctau_mm in ctau_mm_values:
            lab_len = beta_gamma * ctau_mm
            p = decay_probability_between_radii(lab_len, r_min_mm, r_max_mm)
            rows.append({"ctau_mm": ctau_mm, "beta_gamma": beta_gamma, "P_decay_in_ID": p})
    return pd.DataFrame.from_records(rows)


def prepare_fig2_event_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """Tag each row with its radial category and a numeric Sumpt bin midpoint."""
    unknown = sorted(set(df["source_yaml"]) - set(EVENT_EFFICIENCY_RADIAL_CATEGORIES))
    if unknown:
        raise ValueError(f"unrecognized event-efficiency source_yaml value(s): {unknown}")
    out = df.copy()
    out["radial_category"] = out["source_yaml"].map(EVENT_EFFICIENCY_RADIAL_CATEGORIES)
    out["sumpt_lo_gev"] = out["Sumpt [GeV]"].apply(lambda s: parse_bin_label(s)[0])
    return out.sort_values(["radial_category", "sumpt_lo_gev"]).reset_index(drop=True)


def prepare_fig3_vertex_heatmap(
    df: pd.DataFrame,
    radius_bin_labels: tuple[str, ...] = ("22_25_mm", "84_111_mm", "180_300_mm"),
) -> dict[str, pd.DataFrame]:
    """One m_DV x n_tracks efficiency matrix per requested radial bin."""
    available = set(df["radius_bin_label"])
    missing = [r for r in radius_bin_labels if r not in available]
    if missing:
        raise ValueError(f"requested radius_bin_label(s) not found in data: {missing}")

    grids: dict[str, pd.DataFrame] = {}
    for label in radius_bin_labels:
        sub = df[df["radius_bin_label"] == label].copy()
        sub["m_DV_lo"] = sub["m_DV [GeV]"].apply(lambda s: parse_bin_label(s)[0])
        sub["n_tracks_lo"] = sub["n_tracks"].apply(lambda s: parse_bin_label(s)[0])
        grid = sub.pivot_table(index="m_DV_lo", columns="n_tracks_lo", values="value", aggfunc="mean")
        grids[label] = grid.sort_index().sort_index(axis=1)
    return grids


def prepare_fig4_cutflow(df: pd.DataFrame) -> pd.DataFrame:
    """Add step_index (per qualifier group, in original YAML order) and a short legend label."""
    out = df.copy()
    out["step_index"] = out.groupby("qualifiers", sort=False).cumcount()
    counts = out.groupby("qualifiers", sort=False).size()
    bad = counts[counts != 10]
    if len(bad):
        raise ValueError(f"expected 10 cutflow steps per qualifier group, got: {bad.to_dict()}")

    def _qual(qualifiers: str, name: str) -> str:
        for part in qualifiers.split("; "):
            if part.startswith(f"{name}="):
                return part.split("=", 1)[1]
        return ""

    mass_key = r"$m(\tilde{\chi}^0_1)$"
    tau_key = r"$\tau$"

    def _legend_label(q: str) -> str:
        mass = _qual(q, mass_key)
        tau = _qual(q, tau_key)
        return f"m={mass}, tau={tau}"

    out["legend_label"] = out["qualifiers"].apply(_legend_label)
    return out


def prepare_fig5_inventory(df: pd.DataFrame) -> pd.Series:
    """Table count by category, including 'other'."""
    return df["group"].value_counts()


def prepare_fig6_proxy_map(df: pd.DataFrame, value_col: str = "Nsig_139fb") -> pd.DataFrame:
    """Pivot the scalar-S proxy grid to mS_GeV x ctau_mm -> value_col."""
    if value_col not in df.columns:
        raise ValueError(f"value_col {value_col!r} not found in proxy dataframe")
    grid = df.pivot_table(index="mS_GeV", columns="ctau_mm", values=value_col)
    if grid.isna().any().any():
        raise ValueError("scalar-S proxy grid is not dense (contains NaN) -- benchmark grid changed?")
    return grid.sort_index().sort_index(axis=1)


def values_above_one(df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
    """Rows where value_col exceeds 1 -- used to audit HEPData 'Efficiency' columns.

    A bounded probability/efficiency can never exceed 1; a HEPData column merely
    named 'Efficiency' can (see docs/recast/efficiency_semantics.md). This never
    clips or drops rows -- it only flags them for the caller to label explicitly.
    """
    return df[df[value_col] > 1.0]
