#!/usr/bin/env python3
"""Convert normalized MadGraph cross-section runs into diphoton sigma inputs.

This is a preparation scaffold: it does not require the MadGraph model to exist
yet, and it does not parse fragile MG5 logs.  Instead, it defines the stable table that
future MadGraph runs must export.  The generated output can be consumed by
``scripts/10_apply_sigma_inputs.py``.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from llp_recast.madgraph import (
    MADGRAPH_RUN_COLUMNS as NORMALIZED_INPUT_COLUMNS,
    MADGRAPH_TEMPLATE_COLUMNS as TEMPLATE_COLUMNS,
    infer_production_mode as _infer_production_mode,
)
from llp_recast.tables import (
    empty_frame as _empty,
    finite_positive as _finite_positive,
    numeric_column as _numeric,
    read_csv_or_empty,
)

DEFAULT_MADGRAPH_TABLE = Path("data/manual/madgraph_xsec_runs.csv")
DEFAULT_PRIORITY = Path("outputs/diphoton_2hdmc_bridge/priority_points_for_sigma.csv")
DEFAULT_SIGMA_OUTPUT = Path("data/manual/diphoton_sigma_inputs.csv")
DEFAULT_REPORT_DIR = Path("outputs/madgraph_sigma_ingest")

SIGMA_COLUMNS = [
    "point_id",
    "sigma_ggF_fb",
    "sigma_VBF_fb",
    "sigma_total_fb",
    "sigma_source",
    "production_mode",
    "sigma_notes",
]

# TEMPLATE_COLUMNS / NORMALIZED_INPUT_COLUMNS are imported from llp_recast.madgraph
# (the single source of truth for the MadGraph run-table schema) and re-exported
# here under their historical names.


def known_point_ids(priority: pd.DataFrame) -> set[str]:
    if priority.empty or "point_id" not in priority.columns:
        return set()
    return set(priority["point_id"].dropna().astype(str))


def infer_production_mode(row: pd.Series) -> str:
    return _infer_production_mode(
        process=str(row.get("process", "")),
        existing=str(row.get("production_mode", "")),
    )


def build_madgraph_template(priority: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
    if priority.empty:
        return _empty(TEMPLATE_COLUMNS)
    cols = [col for col in ("point_id", "priority_rank", "m_H_GeV", "Gamma_over_m", "br_gaga") if col in priority.columns]
    template = priority[cols].head(max_rows).copy()
    for col in TEMPLATE_COLUMNS:
        if col not in template.columns:
            template[col] = ""
    return template[TEMPLATE_COLUMNS]


def validate_madgraph_input(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return _empty(NORMALIZED_INPUT_COLUMNS)
    if "point_id" not in table.columns:
        raise ValueError("MadGraph table must contain point_id")
    if "xsec_pb" not in table.columns and "xsec_fb" not in table.columns:
        raise ValueError("MadGraph table must contain xsec_pb or xsec_fb")

    work = table.copy()
    work["point_id"] = work["point_id"].astype(str)
    if work["point_id"].duplicated().any():
        dupes = sorted(set(work.loc[work["point_id"].duplicated(), "point_id"].astype(str)))
        raise ValueError(f"MadGraph table contains duplicate point_id values: {dupes[:5]}")

    for col in NORMALIZED_INPUT_COLUMNS:
        if col not in work.columns:
            work[col] = "" if col not in {"xsec_pb", "xsec_fb", "xsec_unc_pb", "k_factor"} else pd.NA

    for col in ("xsec_pb", "xsec_fb", "xsec_unc_pb", "k_factor"):
        work[col] = pd.to_numeric(work[col], errors="coerce")
        if col != "k_factor" and (work[col].dropna() < 0).any():
            raise ValueError(f"{col} must be non-negative")
        if col == "k_factor" and (work[col].dropna() <= 0).any():
            raise ValueError("k_factor must be positive when supplied")

    has_fb = _finite_positive(work["xsec_fb"])
    has_pb = _finite_positive(work["xsec_pb"])
    if (~(has_fb | has_pb)).any():
        bad = work.loc[~(has_fb | has_pb), "point_id"].astype(str).tolist()
        raise ValueError(f"Rows without positive xsec_pb or xsec_fb: {bad[:5]}")

    return work[NORMALIZED_INPUT_COLUMNS].copy()


def madgraph_to_sigma_input(
    table: pd.DataFrame,
    *,
    priority: pd.DataFrame | None = None,
    strict_point_ids: bool = False,
    apply_k_factor: bool = False,
) -> pd.DataFrame:
    work = validate_madgraph_input(table)
    if work.empty:
        return _empty(SIGMA_COLUMNS)

    allowed = known_point_ids(priority if priority is not None else pd.DataFrame())
    if strict_point_ids and allowed:
        unknown = sorted(set(work["point_id"].astype(str)) - allowed)
        if unknown:
            raise ValueError(f"MadGraph table has point_id values not present in priority table: {unknown[:5]}")

    xsec_fb = _numeric(work, "xsec_fb")
    from_pb = _numeric(work, "xsec_pb") * 1000.0
    sigma_total = xsec_fb.where(_finite_positive(xsec_fb), from_pb)

    if apply_k_factor:
        k = _numeric(work, "k_factor")
        has_k = _finite_positive(k)
        sigma_total = sigma_total.where(~has_k, sigma_total * k)

    rows = []
    for idx, row in work.iterrows():
        mode = infer_production_mode(row)
        total = float(sigma_total.loc[idx])
        sigma_ggf = total if mode == "ggF" else pd.NA
        sigma_vbf = total if mode == "VBF" else pd.NA
        source_parts = ["MadGraph_normalized_table"]
        if str(row.get("madgraph_version", "")).strip():
            source_parts.append(str(row["madgraph_version"]).strip())
        if str(row.get("mg_run_name", "")).strip():
            source_parts.append(str(row["mg_run_name"]).strip())

        note_parts = []
        for col in ("process", "model_name", "param_card_path", "run_card_path", "banner_path", "lhe_path", "notes"):
            value = str(row.get(col, "")).strip()
            if value:
                note_parts.append(f"{col}={value}")
        if apply_k_factor and pd.notna(row.get("k_factor", pd.NA)):
            note_parts.append(f"k_factor_applied={row['k_factor']}")
        elif pd.notna(row.get("k_factor", pd.NA)):
            note_parts.append(f"k_factor_recorded_not_applied={row['k_factor']}")

        rows.append(
            {
                "point_id": str(row["point_id"]),
                "sigma_ggF_fb": sigma_ggf,
                "sigma_VBF_fb": sigma_vbf,
                "sigma_total_fb": total,
                "sigma_source": ";".join(source_parts),
                "production_mode": mode,
                "sigma_notes": ";".join(note_parts),
            }
        )
    return pd.DataFrame.from_records(rows, columns=SIGMA_COLUMNS)


def write_report(
    report_dir: Path,
    *,
    priority: pd.DataFrame,
    madgraph: pd.DataFrame,
    sigma: pd.DataFrame,
    sigma_output: Path,
    strict_point_ids: bool,
    apply_k_factor: bool,
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "README.md"
    text = f"""# MadGraph sigma ingest

Generated by `scripts/11_ingest_madgraph_xsec.py`.

## Purpose

This step prepares the interface expected from future MadGraph runs.  It does
not require the MadGraph UFO/model to exist yet.  It consumes a normalized table
of MadGraph cross-section results and emits the sigma-input contract consumed by
`make sigma-apply`.

## Counts

- Priority rows loaded: {len(priority)}
- MadGraph rows loaded: {len(madgraph)}
- Sigma rows written: {len(sigma)}

## Output

- Sigma input: `{sigma_output}`
- Template: `{report_dir / 'madgraph_xsec_template.csv'}`

## Settings

- Strict point-id validation: `{strict_point_ids}`
- Apply k-factor: `{apply_k_factor}`

## Non-exclusion policy

This step only supplies production cross sections.  Exclusion statements remain
forbidden until acceptance/fiducial treatment, signal model, and width matching
are validated downstream.
"""
    path.write_text(text, encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert normalized MadGraph xsec runs into diphoton sigma inputs")
    parser.add_argument("--madgraph-table", type=Path, default=DEFAULT_MADGRAPH_TABLE)
    parser.add_argument("--priority", type=Path, default=DEFAULT_PRIORITY)
    parser.add_argument("--sigma-output", type=Path, default=DEFAULT_SIGMA_OUTPUT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--template-rows", type=int, default=50)
    parser.add_argument("--strict-point-ids", action="store_true")
    parser.add_argument("--apply-k-factor", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    priority = read_csv_or_empty(args.priority)
    madgraph = read_csv_or_empty(args.madgraph_table)

    args.report_dir.mkdir(parents=True, exist_ok=True)
    template = build_madgraph_template(priority, max_rows=args.template_rows)
    template.to_csv(args.report_dir / "madgraph_xsec_template.csv", index=False)

    sigma = madgraph_to_sigma_input(
        madgraph,
        priority=priority,
        strict_point_ids=args.strict_point_ids,
        apply_k_factor=args.apply_k_factor,
    )
    args.sigma_output.parent.mkdir(parents=True, exist_ok=True)
    sigma.to_csv(args.sigma_output, index=False)
    write_report(
        args.report_dir,
        priority=priority,
        madgraph=madgraph,
        sigma=sigma,
        sigma_output=args.sigma_output,
        strict_point_ids=args.strict_point_ids,
        apply_k_factor=args.apply_k_factor,
    )

    print(f"[OK] wrote MadGraph template under {args.report_dir / 'madgraph_xsec_template.csv'}")
    print(f"[OK] wrote sigma input under {args.sigma_output}")
    print(f"[OK] MadGraph rows ingested: {len(madgraph)}")
    print(f"[OK] sigma rows written: {len(sigma)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
