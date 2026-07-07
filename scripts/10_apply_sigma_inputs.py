#!/usr/bin/env python3
"""Apply externally supplied production cross sections to diphoton candidates.

This script is deliberately non-exclusionary.  It takes the existing
``priority_points_for_sigma.csv`` and ``diphoton_comparison_needs_xsec.csv``
outputs from ``scripts/09_link_2hdmc_to_diphoton.py``, joins an external
sigma-input table, and computes sigma*BR / ATLAS-limit ratios for triage.

The result is still not an exclusion.  A ratio >= 1 only means that the point
is worth a careful treatment of production, fiducial/total acceptance, width
hypotheses, and signal modeling.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

DEFAULT_BRIDGE_DIR = Path("outputs/diphoton_2hdmc_bridge")
DEFAULT_PRIORITY = DEFAULT_BRIDGE_DIR / "priority_points_for_sigma.csv"
DEFAULT_COMPARISON = DEFAULT_BRIDGE_DIR / "diphoton_comparison_needs_xsec.csv"
DEFAULT_SIGMA_INPUT = Path("data/manual/diphoton_sigma_inputs.csv")
DEFAULT_OUTDIR = Path("outputs/diphoton_sigma_applied")

SIGMA_STATUS_SUPPLIED = "SIGMA_SUPPLIED_RATIO_CONTEXT_ONLY"
SIGMA_STATUS_MISSING = "MISSING_PRODUCTION_XSEC"
LIMIT_STATUS_AVAILABLE = "LIMIT_CONTEXT_AVAILABLE"
LIMIT_STATUS_MISSING = "LIMIT_CONTEXT_MISSING"
COMPARISON_STATUS = "RATIO_COMPUTED_NOT_EXCLUSION"
NON_EXCLUSION_FLAG = "NOT_EXCLUSION_ACCEPTANCE_AND_SIGNAL_MODEL_REQUIRED"

SIGMA_COLUMNS = [
    "point_id",
    "sigma_ggF_fb",
    "sigma_VBF_fb",
    "sigma_total_fb",
    "sigma_source",
    "production_mode",
    "sigma_notes",
]

OUTPUT_COLUMNS = [
    "priority_rank",
    "point_id",
    "source_csv",
    "source_row",
    "m_H_GeV",
    "Gamma_H_GeV",
    "Gamma_over_m",
    "br_gaga",
    "sigma_ggF_fb",
    "sigma_VBF_fb",
    "sigma_total_fb",
    "sigma_source",
    "production_mode",
    "sigma_notes",
    "sigma_times_br_gaga_fb",
    "nearest_mass_GeV",
    "nearest_width_hypothesis",
    "nearest_Gamma_over_m",
    "observed_limit_fb",
    "expected_limit_fb",
    "ratio_to_observed_limit_context_only",
    "ratio_to_expected_limit_context_only",
    "ratio_observed_ge1_context_only",
    "ratio_expected_ge1_context_only",
    "sigma_status",
    "limit_status",
    "comparison_status",
    "quality_flags",
]


def _empty(columns: Iterable[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(pd.NA, index=df.index, dtype="Float64")
    return pd.to_numeric(df[column], errors="coerce")


def _finite_positive(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    values = numeric.to_numpy(dtype=float, na_value=np.nan)
    return pd.Series(np.isfinite(values) & (values > 0), index=series.index)


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def normalize_sigma_input(sigma: pd.DataFrame) -> pd.DataFrame:
    """Return one row per point_id with a non-negative total sigma when possible."""
    if sigma.empty:
        return _empty(SIGMA_COLUMNS)
    if "point_id" not in sigma.columns:
        raise ValueError("sigma input must contain a point_id column")

    work = sigma.copy()
    work["point_id"] = work["point_id"].astype(str)
    for col in ("sigma_ggF_fb", "sigma_VBF_fb", "sigma_total_fb"):
        if col not in work.columns:
            work[col] = pd.NA
        work[col] = pd.to_numeric(work[col], errors="coerce")
        if (work[col].dropna() < 0).any():
            raise ValueError(f"{col} must be non-negative")

    if work["point_id"].duplicated().any():
        dupes = sorted(set(work.loc[work["point_id"].duplicated(), "point_id"].astype(str)))
        raise ValueError(f"sigma input contains duplicate point_id values: {dupes[:5]}")

    computed_total = work[["sigma_ggF_fb", "sigma_VBF_fb"]].fillna(0).sum(axis=1)
    has_mode_component = work[["sigma_ggF_fb", "sigma_VBF_fb"]].notna().any(axis=1)
    work["sigma_total_fb"] = work["sigma_total_fb"].where(work["sigma_total_fb"].notna(), computed_total.where(has_mode_component, pd.NA))

    for col in ("sigma_source", "production_mode", "sigma_notes"):
        if col not in work.columns:
            work[col] = ""

    return work[SIGMA_COLUMNS].copy()


def build_sigma_template(priority: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
    """Build a fill-in template for external cross-section calculations."""
    if priority.empty:
        return _empty([
            "point_id",
            "priority_rank",
            "m_H_GeV",
            "Gamma_over_m",
            "br_gaga",
            "sigma_ggF_fb",
            "sigma_VBF_fb",
            "sigma_total_fb",
            "sigma_source",
            "production_mode",
            "sigma_notes",
        ])

    cols = [col for col in ("point_id", "priority_rank", "m_H_GeV", "Gamma_over_m", "br_gaga") if col in priority.columns]
    template = priority[cols].head(max_rows).copy()
    for col in ("sigma_ggF_fb", "sigma_VBF_fb", "sigma_total_fb", "sigma_source", "production_mode", "sigma_notes"):
        template[col] = ""
    return template


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    valid = _finite_positive(numerator) & _finite_positive(denominator)
    out = pd.Series(pd.NA, index=numerator.index, dtype="Float64")
    out.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return out


def _context_bool(series: pd.Series) -> pd.Series:
    # Coerce to a plain numpy float array (NaN for missing) before comparing.
    # Comparing a nullable Float64 series that contains pd.NA raises
    # "boolean value of NA is ambiguous" inside np.where; NaN comparisons are safe.
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    labels = np.where(values >= 1.0, "TRUE_CONTEXT_ONLY", "FALSE_CONTEXT_ONLY")
    labels = np.where(np.isnan(values), "UNKNOWN", labels)
    return pd.Series(labels, index=series.index)


def build_sigma_applied(priority: pd.DataFrame, comparison: pd.DataFrame, sigma_input: pd.DataFrame) -> pd.DataFrame:
    """Join priority points, nearest ATLAS context, and external sigma inputs."""
    if priority.empty:
        return _empty(OUTPUT_COLUMNS)
    if "point_id" not in priority.columns:
        raise ValueError("priority table must contain point_id")

    base = priority.copy()
    base["point_id"] = base["point_id"].astype(str)

    if comparison.empty:
        comp_cols = ["point_id", "nearest_mass_GeV", "nearest_width_hypothesis", "nearest_Gamma_over_m", "observed_limit_fb", "expected_limit_fb"]
        comp = _empty(comp_cols)
    else:
        comp = comparison.copy()
        comp["point_id"] = comp["point_id"].astype(str)
        keep = [
            col
            for col in (
                "point_id",
                "nearest_mass_GeV",
                "nearest_width_hypothesis",
                "nearest_Gamma_over_m",
                "observed_limit_fb",
                "expected_limit_fb",
            )
            if col in comp.columns
        ]
        comp = comp[keep].drop_duplicates(subset=["point_id"], keep="first")

    sigma = normalize_sigma_input(sigma_input)
    merged = base.merge(comp, on="point_id", how="left", suffixes=("", "_limit"))
    merged = merged.merge(sigma, on="point_id", how="left")

    for col in ("br_gaga", "sigma_total_fb", "observed_limit_fb", "expected_limit_fb"):
        merged[col] = _numeric(merged, col)

    merged["sigma_times_br_gaga_fb"] = merged["sigma_total_fb"] * merged["br_gaga"]
    has_sigma = _finite_positive(merged["sigma_total_fb"])
    has_observed = _finite_positive(merged["observed_limit_fb"])
    has_expected = _finite_positive(merged["expected_limit_fb"])

    merged["ratio_to_observed_limit_context_only"] = _ratio(merged["sigma_times_br_gaga_fb"], merged["observed_limit_fb"])
    merged["ratio_to_expected_limit_context_only"] = _ratio(merged["sigma_times_br_gaga_fb"], merged["expected_limit_fb"])
    merged["ratio_observed_ge1_context_only"] = _context_bool(merged["ratio_to_observed_limit_context_only"])
    merged["ratio_expected_ge1_context_only"] = _context_bool(merged["ratio_to_expected_limit_context_only"])
    merged["sigma_status"] = np.where(has_sigma, SIGMA_STATUS_SUPPLIED, SIGMA_STATUS_MISSING)
    merged["limit_status"] = np.where(has_observed | has_expected, LIMIT_STATUS_AVAILABLE, LIMIT_STATUS_MISSING)
    merged["comparison_status"] = np.where(has_sigma & (has_observed | has_expected), COMPARISON_STATUS, "WAITING_FOR_SIGMA_OR_LIMIT_CONTEXT")

    def flags(row: pd.Series) -> str:
        values = [NON_EXCLUSION_FLAG]
        if row["sigma_status"] == SIGMA_STATUS_SUPPLIED:
            values.append("PRODUCTION_XSEC_EXTERNAL_INPUT")
        else:
            values.append("PRODUCTION_XSEC_MISSING")
        if row["limit_status"] == LIMIT_STATUS_AVAILABLE:
            values.append("ATLAS_LIMIT_CONTEXT_AVAILABLE")
        else:
            values.append("ATLAS_LIMIT_CONTEXT_MISSING")
        values.append("FIDUCIAL_VS_TOTAL_CHECK_REQUIRED")
        values.append("WIDTH_MATCH_APPROXIMATE")
        return ";".join(values)

    merged["quality_flags"] = merged.apply(flags, axis=1)

    for col in OUTPUT_COLUMNS:
        if col not in merged.columns:
            merged[col] = pd.NA
    return merged[OUTPUT_COLUMNS].copy()


def write_readme(outdir: Path, priority: pd.DataFrame, sigma_input: pd.DataFrame, applied: pd.DataFrame) -> Path:
    path = outdir / "README.md"
    supplied = int((applied["sigma_status"] == SIGMA_STATUS_SUPPLIED).sum()) if "sigma_status" in applied else 0
    ratio_rows = int((applied["comparison_status"] == COMPARISON_STATUS).sum()) if "comparison_status" in applied else 0
    text = f"""# Diphoton sigma-input application

Generated by `scripts/10_apply_sigma_inputs.py`.

## Purpose

This package applies externally supplied production cross sections to the existing
2HDMC diphoton priority candidates and computes `sigma * BR(gamma gamma)` ratios
against the nearest ATLAS limit-context rows.

## Counts

- Priority candidates loaded: {len(priority)}
- Sigma-input rows loaded: {len(sigma_input)}
- Candidates with supplied sigma: {supplied}
- Rows with context-only ratios: {ratio_rows}

## Outputs

- `sigma_input_template.csv`: fill-in table for external cross-section inputs.
- `diphoton_sigma_applied.csv`: joined table with `sigma * BR` and limit ratios.

## Non-exclusion policy

Every row remains marked `{NON_EXCLUSION_FLAG}`.  A ratio above one is a triage
signal only, not an exclusion.  Before any exclusion statement, the production
rate source, fiducial-vs-total treatment, acceptance, and signal model must be
validated.
"""
    path.write_text(text, encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply external sigma inputs to diphoton priority candidates")
    parser.add_argument("--priority", type=Path, default=DEFAULT_PRIORITY)
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON)
    parser.add_argument("--sigma-input", type=Path, default=DEFAULT_SIGMA_INPUT)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--template-rows", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    priority = read_csv_or_empty(args.priority)
    comparison = read_csv_or_empty(args.comparison)
    sigma_input = read_csv_or_empty(args.sigma_input)

    template = build_sigma_template(priority, max_rows=args.template_rows)
    template.to_csv(args.outdir / "sigma_input_template.csv", index=False)

    applied = build_sigma_applied(priority, comparison, sigma_input)
    applied.to_csv(args.outdir / "diphoton_sigma_applied.csv", index=False)
    write_readme(args.outdir, priority, sigma_input, applied)

    print(f"[OK] wrote sigma application outputs under {args.outdir}")
    print(f"[OK] priority candidates: {len(priority)}")
    print(f"[OK] sigma rows supplied: {len(sigma_input)}")
    print(f"[OK] ratio rows: {int((applied['comparison_status'] == COMPARISON_STATUS).sum()) if not applied.empty else 0}")
    print("[OK] comparison status remains non-exclusionary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
