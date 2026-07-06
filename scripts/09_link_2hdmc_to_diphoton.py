#!/usr/bin/env python3
"""Link real 2HDMC scan outputs to the diphoton pre-recast contract.

This bridge is deliberately non-exclusionary.  It exports physical 2HDMC
points with real widths/BRs, ranks a compact set of points that need
production cross sections, and joins those candidates to nearby ATLAS
HIGG-2018-27 scalar limit rows for context only.
"""
from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import math
import os
import re
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTPUT_DIR = Path("outputs/diphoton_2hdmc_bridge")
FIG_DIR_NAME = "figures"
EXPERIMENT_SIDE_CSV = Path("outputs/diphoton_recast_contract/experiment_side.csv")
MEETING_PACKAGE_SCRIPT = Path("scripts/08_diphoton_meeting_package.py")

DEFAULT_SEARCH_ROOTS = (
    Path("outputs"),
    Path("data"),
    Path("/mnt/c/Users/Asus/cern_db/dihiggs_lake"),
)

SCAN_PATTERNS = (
    "scan_tb_*.csv",
    "scan_tb_*.csv.gz",
    "*.parquet",
    "silver_all.parquet",
    "*scan*.csv",
    "*scan*.parquet",
)
PRUNE_DIR_NAMES = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
SCAN_BATCH_SIZE = 100_000

REQUIRED_COLUMNS = (
    "m_phi",
    "total_width",
    "br_gaga",
    "positivity_ok",
    "unitarity_ok",
    "perturbativity_ok",
)
PHYSICAL_FLAG_COLUMNS = ("positivity_ok", "unitarity_ok", "perturbativity_ok")
ATLAS_WIDTH_HYPOTHESES = (("NWA", 0.0), ("2pct", 0.02), ("6pct", 0.06), ("10pct", 0.10))
THEORY_INPUT_COLUMNS = tuple(dict.fromkeys((*REQUIRED_COLUMNS, "tanbeta", "point_id")))

THEORY_STATUS = "REAL_2HDMC_WIDTHS_AND_BR"
XSEC_STATUS = "MISSING_PRODUCTION_XSEC"
EXCLUSION_STATUS = "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED"
COMPARISON_STATUS = "NEEDS_SIGMA_X_BR"

INVENTORY_COLUMNS = [
    "source_path",
    "file_type",
    "exists",
    "readable",
    "accepted_as_2hdmc_scan",
    "rejection_reason",
    "n_rows",
    "n_physical_rows",
    "has_required_columns",
    "missing_columns",
    "m_min",
    "m_max",
    "tanbeta_values",
]

THEORY_COLUMNS = [
    "source_csv",
    "source_row",
    "point_id",
    "m_phi",
    "m_H_GeV",
    "total_width",
    "Gamma_H_GeV",
    "Gamma_over_m",
    "br_gaga",
    "tanbeta",
    "positivity_ok",
    "unitarity_ok",
    "perturbativity_ok",
    "sigma_ggF_fb",
    "sigma_VBF_fb",
    "sigma_total_fb",
    "sigma_times_br_gaga_fb",
    "theory_status",
    "xsec_status",
    "exclusion_status",
]

PRIORITY_COLUMNS = [
    "priority_rank",
    "source_csv",
    "source_row",
    "point_id",
    "m_phi",
    "m_H_GeV",
    "total_width",
    "Gamma_H_GeV",
    "Gamma_over_m",
    "br_gaga",
    "tanbeta",
    "nearest_atlas_width_hypothesis",
    "width_hypothesis_distance",
    "atlas_mass_range_status",
    "theory_status",
    "xsec_status",
    "exclusion_status",
]

COMPARISON_COLUMNS = [
    "priority_rank",
    "point_id",
    "source_csv",
    "source_row",
    "m_H_GeV",
    "Gamma_H_GeV",
    "Gamma_over_m",
    "br_gaga",
    "nearest_mass_GeV",
    "nearest_width_hypothesis",
    "nearest_Gamma_over_m",
    "observed_limit_fb",
    "expected_limit_fb",
    "expected_minus_1sigma_fb",
    "expected_plus_1sigma_fb",
    "expected_minus_2sigma_fb",
    "expected_plus_2sigma_fb",
    "fiducial_or_total",
    "spin_assumption",
    "source_table",
    "comparison_status",
    "exclusion_status",
    "notes",
]


def default_search_roots() -> list[Path]:
    """Return the configured search roots, including absent roots for reporting."""
    return list(DEFAULT_SEARCH_ROOTS)


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def file_type(path: Path) -> str:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes[-2:] == [".csv", ".gz"]:
        return "csv.gz"
    if suffixes and suffixes[-1] == ".csv":
        return "csv"
    if suffixes and suffixes[-1] == ".parquet":
        return "parquet"
    return "unknown"


def _is_parquet_engine_missing(exc: Exception) -> bool:
    text = str(exc).lower()
    return isinstance(exc, ImportError) or (
        "pyarrow" in text and "fastparquet" in text and ("missing" in text or "unable to find" in text)
    )


def read_scan_frame(path: Path, nrows: int | None = None) -> pd.DataFrame:
    kind = file_type(path)
    if kind in {"csv", "csv.gz"}:
        return pd.read_csv(path, nrows=nrows)
    if kind == "parquet":
        if nrows is not None:
            return pd.read_parquet(path).head(nrows)
        return pd.read_parquet(path)
    raise ValueError(f"unsupported input type: {kind}")


def parquet_columns_and_rows(path: Path) -> tuple[list[str], int | None]:
    if importlib.util.find_spec("pyarrow") is not None:
        import pyarrow.parquet as pq

        parquet_file = pq.ParquetFile(path)
        n_rows = parquet_file.metadata.num_rows if parquet_file.metadata is not None else None
        return list(parquet_file.schema.names), n_rows
    if importlib.util.find_spec("fastparquet") is not None:
        import fastparquet

        parquet_file = fastparquet.ParquetFile(path)
        n_rows = sum(row_group.num_rows for row_group in parquet_file.fmd.row_groups)
        return list(parquet_file.columns), n_rows
    raise ImportError("No parquet engine is available; install pyarrow or fastparquet")


def scan_columns_and_rows(path: Path) -> tuple[list[str], int | None]:
    kind = file_type(path)
    if kind in {"csv", "csv.gz"}:
        return list(pd.read_csv(path, nrows=0).columns), None
    if kind == "parquet":
        return parquet_columns_and_rows(path)
    raise ValueError(f"unsupported input type: {kind}")


def read_scan_columns(path: Path, columns: Iterable[str]) -> pd.DataFrame:
    wanted = set(columns)
    kind = file_type(path)
    if kind in {"csv", "csv.gz"}:
        return pd.read_csv(path, usecols=lambda column: column in wanted)
    if kind == "parquet":
        available, _ = parquet_columns_and_rows(path)
        selected = [column for column in columns if column in available]
        return pd.read_parquet(path, columns=selected)
    raise ValueError(f"unsupported input type: {kind}")


def iter_scan_column_frames(path: Path, columns: Iterable[str], batch_size: int = SCAN_BATCH_SIZE) -> Iterable[pd.DataFrame]:
    wanted = set(columns)
    kind = file_type(path)
    if kind in {"csv", "csv.gz"}:
        for chunk in pd.read_csv(path, usecols=lambda column: column in wanted, chunksize=batch_size):
            yield chunk
        return
    if kind == "parquet":
        available, _ = parquet_columns_and_rows(path)
        selected = [column for column in columns if column in available]
        if importlib.util.find_spec("pyarrow") is not None:
            import pyarrow.parquet as pq

            offset = 0
            parquet_file = pq.ParquetFile(path)
            for batch in parquet_file.iter_batches(batch_size=batch_size, columns=selected):
                df = batch.to_pandas()
                df.index = pd.RangeIndex(offset, offset + len(df))
                offset += len(df)
                yield df
            return
        yield pd.read_parquet(path, columns=selected)
        return
    raise ValueError(f"unsupported input type: {kind}")


def _read_header(path: Path) -> list[str] | None:
    try:
        columns, _ = scan_columns_and_rows(path)
        return columns
    except Exception:
        return None


def missing_required_columns(columns: Iterable[str]) -> list[str]:
    present = set(columns)
    return [col for col in REQUIRED_COLUMNS if col not in present]


def has_required_columns(columns: Iterable[str]) -> bool:
    return not missing_required_columns(columns)


def looks_like_2hdmc_scan(columns: Iterable[str], min_required_columns: int = 2) -> bool:
    """Return True for CSVs worth inventorying as possible 2HDMC scan outputs."""
    present = set(columns)
    return sum(col in present for col in REQUIRED_COLUMNS) >= min_required_columns


def discover_manifest_scan_paths(roots: Iterable[Path]) -> list[Path]:
    """Best-effort discovery of scan paths named inside manifest-like files."""
    scan_paths: set[Path] = set()
    pattern = re.compile(r"(?P<path>(?:/|\.{1,2}/|[A-Za-z]:[\\/])?[^\s'\",;]+\.(?:csv(?:\.gz)?|parquet))")
    for root in roots:
        if not root.exists():
            continue
        for manifest in root.rglob("*manifest*"):
            if not manifest.is_file() or manifest.suffix.lower() not in {".txt", ".csv", ".json", ".yaml", ".yml"}:
                continue
            try:
                text = manifest.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for match in pattern.finditer(text):
                raw = match.group("path")
                candidate = Path(raw)
                if not candidate.is_absolute():
                    candidate = manifest.parent / candidate
                if candidate.exists() and candidate.is_file():
                    scan_paths.add(candidate)
    return sorted(scan_paths)


def _path_matches_scan_pattern(path: Path) -> bool:
    name = path.name
    return any(fnmatch.fnmatch(name, pattern) for pattern in SCAN_PATTERNS)


def iter_candidate_paths(root: Path, output_dir: Path) -> Iterable[Path]:
    if root.is_file():
        if _path_matches_scan_pattern(root):
            yield root
        return

    resolved_output = output_dir.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in PRUNE_DIR_NAMES and not _is_under(current / name, resolved_output)
        ]
        for filename in filenames:
            path = current / filename
            if _path_matches_scan_pattern(path):
                yield path


def discover_scan_files(
    roots: Iterable[Path] | None = None,
    output_dir: Path = OUTPUT_DIR,
    max_files: int | None = None,
) -> list[Path]:
    """Discover candidate scan files by name only; validation happens later."""
    roots = list(default_search_roots() if roots is None else roots)
    candidates: set[Path] = set()

    for root in roots:
        if not root.exists():
            continue
        for path in iter_candidate_paths(root, output_dir):
            if not path.is_file():
                continue
            if _is_under(path, output_dir):
                continue
            candidates.add(path)
            if max_files is not None and len(candidates) >= max_files:
                return sorted(candidates, key=lambda p: str(p))

    for path in discover_manifest_scan_paths(roots):
        if _is_under(path, output_dir):
            continue
        candidates.add(path)
        if max_files is not None and len(candidates) >= max_files:
            break

    return sorted(candidates, key=lambda p: str(p))


def discover_scan_csvs(roots: Iterable[Path] | None = None, output_dir: Path = OUTPUT_DIR) -> list[Path]:
    """Backward-compatible alias for older tests/callers."""
    return [path for path in discover_scan_files(roots, output_dir=output_dir) if file_type(path) in {"csv", "csv.gz"}]


def physical_mask(df: pd.DataFrame) -> pd.Series:
    """Rows are physical only when all required 2HDMC flags equal 1."""
    if any(col not in df.columns for col in PHYSICAL_FLAG_COLUMNS):
        return pd.Series(False, index=df.index)
    mask = pd.Series(True, index=df.index)
    for col in PHYSICAL_FLAG_COLUMNS:
        mask &= pd.to_numeric(df[col], errors="coerce").eq(1)
    return mask


def filter_physical(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[physical_mask(df)].copy()


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(pd.NA, index=df.index, dtype="Float64")
    return pd.to_numeric(df[column], errors="coerce")


def _finite_mask(*series: pd.Series) -> pd.Series:
    if not series:
        return pd.Series(dtype=bool)
    mask = pd.Series(True, index=series[0].index)
    for values in series:
        numeric = pd.to_numeric(values, errors="coerce")
        mask &= pd.Series(np.isfinite(numeric.to_numpy(dtype=float, na_value=np.nan)), index=values.index)
    return mask


def _format_tanbeta_values(df: pd.DataFrame, max_values: int = 20) -> str:
    if "tanbeta" not in df.columns:
        return ""
    numeric = pd.to_numeric(df["tanbeta"], errors="coerce").dropna()
    if not numeric.empty:
        values = sorted(set(float(v) for v in numeric))
        formatted = [f"{value:g}" for value in values[:max_values]]
    else:
        values = sorted(set(str(v) for v in df["tanbeta"].dropna() if str(v) != ""))
        formatted = values[:max_values]
    if len(values) > max_values:
        formatted.append("...")
    return ";".join(formatted)


def _format_tanbeta_set(values: set[object], max_values: int = 20) -> str:
    numeric_values = []
    text_values = []
    for value in values:
        if pd.isna(value) or str(value) == "":
            continue
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.notna(numeric):
            numeric_values.append(float(numeric))
        else:
            text_values.append(str(value))
    if numeric_values:
        unique = sorted(set(numeric_values))
        formatted = [f"{value:g}" for value in unique[:max_values]]
        if len(unique) > max_values:
            formatted.append("...")
        return ";".join(formatted)
    unique_text = sorted(set(text_values))
    formatted = unique_text[:max_values]
    if len(unique_text) > max_values:
        formatted.append("...")
    return ";".join(formatted)


def _inventory_row(
    path: Path,
    *,
    readable: bool,
    accepted: bool,
    rejection_reason: str,
    n_rows: int = 0,
    n_physical_rows: int = 0,
    has_required: bool = False,
    missing: list[str] | None = None,
    m_min: object = pd.NA,
    m_max: object = pd.NA,
    tanbeta_values: str = "",
) -> dict[str, object]:
    return {
        "source_path": str(path),
        "file_type": file_type(path),
        "exists": path.exists(),
        "readable": readable,
        "accepted_as_2hdmc_scan": accepted,
        "rejection_reason": rejection_reason,
        "n_rows": int(n_rows),
        "n_physical_rows": int(n_physical_rows),
        "has_required_columns": has_required,
        "missing_columns": ";".join(missing or []),
        "m_min": m_min,
        "m_max": m_max,
        "tanbeta_values": tanbeta_values,
    }


def inventory_scan_file(path: Path) -> dict[str, object]:
    if not path.exists():
        return _inventory_row(path, readable=False, accepted=False, rejection_reason="FILE_MISSING")
    if file_type(path) not in {"csv", "csv.gz", "parquet"}:
        return _inventory_row(path, readable=False, accepted=False, rejection_reason="UNSUPPORTED_FILE_TYPE")
    try:
        columns, metadata_rows = scan_columns_and_rows(path)
    except Exception as exc:
        reason = "PARQUET_ENGINE_MISSING" if file_type(path) == "parquet" and _is_parquet_engine_missing(exc) else f"UNREADABLE_{file_type(path).upper()}:{type(exc).__name__}"
        return _inventory_row(path, readable=False, accepted=False, rejection_reason=reason)

    missing = missing_required_columns(columns)
    selected_columns = tuple(dict.fromkeys(("m_phi", "tanbeta", *PHYSICAL_FLAG_COLUMNS)))
    try:
        n_rows_seen = 0
        n_physical_rows = 0
        m_min = pd.NA
        m_max = pd.NA
        tanbeta_values: set[object] = set()
        for df in iter_scan_column_frames(path, selected_columns):
            n_rows_seen += len(df)
            m_phi = _numeric(df, "m_phi")
            finite_mass = _finite_mask(m_phi)
            if finite_mass.any():
                chunk_min = float(m_phi[finite_mass].min())
                chunk_max = float(m_phi[finite_mass].max())
                m_min = chunk_min if pd.isna(m_min) else min(float(m_min), chunk_min)
                m_max = chunk_max if pd.isna(m_max) else max(float(m_max), chunk_max)
            if len(missing) == 0:
                n_physical_rows += int(physical_mask(df).sum())
            if "tanbeta" in df.columns:
                tanbeta_values.update(df["tanbeta"].dropna().unique().tolist())
    except Exception as exc:
        reason = "PARQUET_ENGINE_MISSING" if file_type(path) == "parquet" and _is_parquet_engine_missing(exc) else f"UNREADABLE_{file_type(path).upper()}:{type(exc).__name__}"
        return _inventory_row(path, readable=False, accepted=False, rejection_reason=reason)

    accepted = len(missing) == 0
    n_rows = metadata_rows if metadata_rows is not None else n_rows_seen
    return _inventory_row(
        path,
        readable=True,
        accepted=accepted,
        rejection_reason="" if accepted else "MISSING_REQUIRED_COLUMNS",
        n_rows=n_rows,
        n_physical_rows=n_physical_rows if accepted else 0,
        has_required=accepted,
        missing=missing,
        m_min=m_min,
        m_max=m_max,
        tanbeta_values=_format_tanbeta_set(tanbeta_values),
    )


def inventory_scan_csv(path: Path) -> dict[str, object]:
    """Backward-compatible wrapper for older tests/callers."""
    return inventory_scan_file(path)


def build_scan_inventory(scan_paths: Iterable[Path]) -> pd.DataFrame:
    rows = [inventory_scan_file(path) for path in scan_paths]
    return pd.DataFrame.from_records(rows, columns=INVENTORY_COLUMNS)


def _point_id(row: pd.Series, source: Path) -> str:
    if "point_id" in row.index and pd.notna(row["point_id"]) and str(row["point_id"]) != "":
        return str(row["point_id"])
    return f"{source.stem}:row{int(row.name)}"


def theory_side_from_scan_frame(df: pd.DataFrame, source_csv: Path) -> pd.DataFrame:
    """Normalize one complete scan frame into the theory-side contract."""
    if not has_required_columns(df.columns):
        return _empty(THEORY_COLUMNS)

    physical = filter_physical(df)
    if physical.empty:
        return _empty(THEORY_COLUMNS)

    m_phi = _numeric(physical, "m_phi")
    total_width = _numeric(physical, "total_width")
    br_gaga = _numeric(physical, "br_gaga")
    finite = _finite_mask(m_phi, total_width, br_gaga)
    finite &= m_phi.gt(0)
    finite &= total_width.ge(0)
    finite &= br_gaga.ge(0)
    physical = physical.loc[finite].copy()
    if physical.empty:
        return _empty(THEORY_COLUMNS)

    m_phi = _numeric(physical, "m_phi").astype(float)
    total_width = _numeric(physical, "total_width").astype(float)
    br_gaga = _numeric(physical, "br_gaga").astype(float)
    gamma_over_m = total_width / m_phi

    rows = []
    for idx, row in physical.iterrows():
        rows.append(
            {
                "source_csv": str(source_csv),
                "source_row": int(idx),
                "point_id": _point_id(row, source_csv),
                "m_phi": float(m_phi.loc[idx]),
                "m_H_GeV": float(m_phi.loc[idx]),
                "total_width": float(total_width.loc[idx]),
                "Gamma_H_GeV": float(total_width.loc[idx]),
                "Gamma_over_m": float(gamma_over_m.loc[idx]),
                "br_gaga": float(br_gaga.loc[idx]),
                "tanbeta": row["tanbeta"] if "tanbeta" in row.index and pd.notna(row["tanbeta"]) else pd.NA,
                "positivity_ok": row["positivity_ok"],
                "unitarity_ok": row["unitarity_ok"],
                "perturbativity_ok": row["perturbativity_ok"],
                "sigma_ggF_fb": pd.NA,
                "sigma_VBF_fb": pd.NA,
                "sigma_total_fb": pd.NA,
                "sigma_times_br_gaga_fb": pd.NA,
                "theory_status": THEORY_STATUS,
                "xsec_status": XSEC_STATUS,
                "exclusion_status": EXCLUSION_STATUS,
            }
        )
    return pd.DataFrame.from_records(rows, columns=THEORY_COLUMNS)


def build_theory_side(scan_paths: Iterable[Path]) -> pd.DataFrame:
    frames = []
    for path in scan_paths:
        header = _read_header(path)
        if header is None or not has_required_columns(header):
            continue
        try:
            for chunk in iter_scan_column_frames(path, THEORY_INPUT_COLUMNS):
                frames.append(theory_side_from_scan_frame(chunk, path))
        except Exception:
            continue
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return _empty(THEORY_COLUMNS)
    return pd.concat(frames, ignore_index=True)[THEORY_COLUMNS]


def nearest_width_hypothesis(gamma_over_m: float) -> tuple[str, float, float]:
    label, value = min(ATLAS_WIDTH_HYPOTHESES, key=lambda item: (abs(gamma_over_m - item[1]), item[1]))
    return label, value, abs(gamma_over_m - value)


def rank_priority_points(theory: pd.DataFrame, max_points: int = 50) -> pd.DataFrame:
    if theory.empty:
        return _empty(PRIORITY_COLUMNS)

    work = theory.copy()
    for col in ("m_phi", "total_width", "br_gaga", "Gamma_over_m"):
        work[col] = pd.to_numeric(work[col], errors="coerce")
    finite = _finite_mask(work["m_phi"], work["total_width"], work["br_gaga"], work["Gamma_over_m"])
    work = work.loc[finite].copy()
    if work.empty:
        return _empty(PRIORITY_COLUMNS)

    width_matches = work["Gamma_over_m"].map(nearest_width_hypothesis)
    work["nearest_atlas_width_hypothesis"] = [item[0] for item in width_matches]
    work["width_hypothesis_distance"] = [item[2] for item in width_matches]
    work["_in_atlas_mass_range"] = work["m_phi"].between(160.0, 3000.0, inclusive="both")
    work["atlas_mass_range_status"] = work["_in_atlas_mass_range"].map(
        {True: "INSIDE_ATLAS_SCALAR_RANGE_160_3000_GEV", False: "OUTSIDE_ATLAS_SCALAR_RANGE_160_3000_GEV"}
    )
    work["point_id"] = work["point_id"].astype(str)

    work = work.sort_values(
        by=["_in_atlas_mass_range", "br_gaga", "width_hypothesis_distance", "m_phi", "point_id"],
        ascending=[False, False, True, True, True],
        kind="mergesort",
    ).head(max_points)
    work.insert(0, "priority_rank", range(1, len(work) + 1))
    return work[PRIORITY_COLUMNS].reset_index(drop=True)


def load_experiment_side(contract_csv: Path = EXPERIMENT_SIDE_CSV) -> pd.DataFrame:
    if contract_csv.exists():
        return pd.read_csv(contract_csv)

    spec = importlib.util.spec_from_file_location("diphoton_meeting_package", MEETING_PACKAGE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {MEETING_PACKAGE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_experiment_side()


def nearest_experiment_row(point: pd.Series, experiment: pd.DataFrame) -> pd.Series | None:
    if experiment.empty:
        return None
    exp = experiment.copy()
    exp["mass_GeV"] = pd.to_numeric(exp["mass_GeV"], errors="coerce")
    exp["Gamma_over_m"] = pd.to_numeric(exp["Gamma_over_m"], errors="coerce")
    exp = exp.dropna(subset=["mass_GeV", "Gamma_over_m"])
    if exp.empty:
        return None

    mass = float(point["m_H_GeV"])
    gamma = float(point["Gamma_over_m"])
    mass_span = max(float(exp["mass_GeV"].max() - exp["mass_GeV"].min()), 1.0)
    gamma_span = max(float(exp["Gamma_over_m"].max() - exp["Gamma_over_m"].min()), 0.01)
    exp["_mass_distance"] = (exp["mass_GeV"] - mass).abs()
    exp["_width_distance"] = (exp["Gamma_over_m"] - gamma).abs()
    exp["_nearest_score"] = exp["_mass_distance"] / mass_span + exp["_width_distance"] / gamma_span
    exp = exp.sort_values(
        by=["_nearest_score", "_mass_distance", "_width_distance", "mass_GeV", "Gamma_over_m"],
        kind="mergesort",
    )
    return exp.iloc[0]


def build_comparison(priority: pd.DataFrame, experiment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, point in priority.iterrows():
        exp_row = nearest_experiment_row(point, experiment)
        if exp_row is None:
            rows.append(
                {
                    "priority_rank": point.get("priority_rank", pd.NA),
                    "point_id": point.get("point_id", pd.NA),
                    "source_csv": point.get("source_csv", pd.NA),
                    "source_row": point.get("source_row", pd.NA),
                    "m_H_GeV": point.get("m_H_GeV", pd.NA),
                    "Gamma_H_GeV": point.get("Gamma_H_GeV", pd.NA),
                    "Gamma_over_m": point.get("Gamma_over_m", pd.NA),
                    "br_gaga": point.get("br_gaga", pd.NA),
                    "nearest_mass_GeV": pd.NA,
                    "nearest_width_hypothesis": pd.NA,
                    "nearest_Gamma_over_m": pd.NA,
                    "observed_limit_fb": pd.NA,
                    "expected_limit_fb": pd.NA,
                    "expected_minus_1sigma_fb": pd.NA,
                    "expected_plus_1sigma_fb": pd.NA,
                    "expected_minus_2sigma_fb": pd.NA,
                    "expected_plus_2sigma_fb": pd.NA,
                    "fiducial_or_total": pd.NA,
                    "spin_assumption": pd.NA,
                    "source_table": pd.NA,
                    "comparison_status": COMPARISON_STATUS,
                    "exclusion_status": EXCLUSION_STATUS,
                    "notes": "NO_EXPERIMENT_SIDE_ROWS_AVAILABLE",
                }
            )
            continue

        rows.append(
            {
                "priority_rank": point["priority_rank"],
                "point_id": point["point_id"],
                "source_csv": point["source_csv"],
                "source_row": point["source_row"],
                "m_H_GeV": point["m_H_GeV"],
                "Gamma_H_GeV": point["Gamma_H_GeV"],
                "Gamma_over_m": point["Gamma_over_m"],
                "br_gaga": point["br_gaga"],
                "nearest_mass_GeV": exp_row["mass_GeV"],
                "nearest_width_hypothesis": exp_row["width_hypothesis"],
                "nearest_Gamma_over_m": exp_row["Gamma_over_m"],
                "observed_limit_fb": exp_row.get("observed_limit_fb", pd.NA),
                "expected_limit_fb": exp_row.get("expected_limit_fb", pd.NA),
                "expected_minus_1sigma_fb": exp_row.get("expected_minus_1sigma_fb", pd.NA),
                "expected_plus_1sigma_fb": exp_row.get("expected_plus_1sigma_fb", pd.NA),
                "expected_minus_2sigma_fb": exp_row.get("expected_minus_2sigma_fb", pd.NA),
                "expected_plus_2sigma_fb": exp_row.get("expected_plus_2sigma_fb", pd.NA),
                "fiducial_or_total": exp_row.get("fiducial_or_total", pd.NA),
                "spin_assumption": exp_row.get("spin_assumption", pd.NA),
                "source_table": exp_row.get("source_table", pd.NA),
                "comparison_status": COMPARISON_STATUS,
                "exclusion_status": EXCLUSION_STATUS,
                "notes": "ATLAS_LIMIT_CONTEXT_ONLY_NEEDS_SIGMA_X_BR",
            }
        )
    return pd.DataFrame.from_records(rows, columns=COMPARISON_COLUMNS)


def _annotate_empty(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes, color="dimgray")


def make_br_figure(theory: pd.DataFrame, priority: pd.DataFrame, fig_dir: Path) -> Path:
    path = fig_dir / "br_gaga_vs_mass.png"
    fig, ax = plt.subplots(figsize=(8, 5.5))
    if theory.empty:
        _annotate_empty(ax, "NO REAL 2HDMC SCAN FILES FOUND")
    else:
        ax.scatter(theory["m_H_GeV"], theory["br_gaga"], s=18, alpha=0.45, label="physical 2HDMC points")
        if not priority.empty:
            ax.scatter(
                priority["m_H_GeV"],
                priority["br_gaga"],
                s=42,
                facecolors="none",
                edgecolors="tab:red",
                linewidths=1.2,
                label="priority sigma candidates",
            )
        positive = pd.to_numeric(theory["br_gaga"], errors="coerce").dropna()
        if (positive > 0).any():
            ax.set_yscale("log")
        ax.legend(fontsize=8)
    ax.set_xlabel("m_phi [GeV]")
    ax.set_ylabel("BR(phi -> gamma gamma)")
    ax.set_title("2HDMC diphoton branching ratios")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def make_width_figure(theory: pd.DataFrame, priority: pd.DataFrame, fig_dir: Path) -> Path:
    path = fig_dir / "width_over_mass_vs_mass.png"
    fig, ax = plt.subplots(figsize=(8, 5.5))
    if theory.empty:
        _annotate_empty(ax, "NO REAL 2HDMC SCAN FILES FOUND")
    else:
        ax.scatter(theory["m_H_GeV"], theory["Gamma_over_m"], s=18, alpha=0.45, label="physical 2HDMC points")
        if not priority.empty:
            ax.scatter(
                priority["m_H_GeV"],
                priority["Gamma_over_m"],
                s=42,
                facecolors="none",
                edgecolors="tab:red",
                linewidths=1.2,
                label="priority sigma candidates",
            )
    for label, value in ATLAS_WIDTH_HYPOTHESES:
        ax.axhline(value, color="black", linewidth=0.8, linestyle="--", alpha=0.45)
        ax.text(0.99, value, label, ha="right", va="bottom", transform=ax.get_yaxis_transform(), fontsize=8)
    ax.set_xlabel("m_phi [GeV]")
    ax.set_ylabel("Gamma / m")
    ax.set_title("2HDMC width fractions against ATLAS hypotheses")
    ax.grid(alpha=0.3)
    if not theory.empty or not priority.empty:
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def make_limit_context_figure(experiment: pd.DataFrame, priority: pd.DataFrame, fig_dir: Path) -> Path:
    path = fig_dir / "diphoton_limit_vs_candidate_points.png"
    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    colors = {"NWA": "black", "2pct": "tab:blue", "6pct": "tab:green", "10pct": "tab:red"}
    y_values = []
    if not experiment.empty:
        exp = experiment.copy()
        exp["mass_GeV"] = pd.to_numeric(exp["mass_GeV"], errors="coerce")
        for col in ("observed_limit_fb", "expected_limit_fb"):
            exp[col] = pd.to_numeric(exp[col], errors="coerce")
        for width_hyp, group in exp.groupby("width_hypothesis"):
            group = group.sort_values("mass_GeV")
            color = colors.get(width_hyp, "gray")
            ax.plot(group["mass_GeV"], group["observed_limit_fb"], color=color, linewidth=1.3, label=f"observed {width_hyp}")
            ax.plot(group["mass_GeV"], group["expected_limit_fb"], color=color, linestyle="--", linewidth=1.0, alpha=0.75)
            y_values.extend(group["observed_limit_fb"].dropna().tolist())
            y_values.extend(group["expected_limit_fb"].dropna().tolist())
    else:
        _annotate_empty(ax, "ATLAS experiment-side limits unavailable")

    positive_y = [float(value) for value in y_values if pd.notna(value) and float(value) > 0]
    rug_y = min(positive_y) * 0.75 if positive_y else 1.0
    if not priority.empty:
        ax.scatter(
            priority["m_H_GeV"],
            [rug_y] * len(priority),
            marker="|",
            s=180,
            color="tab:orange",
            linewidths=1.4,
            label="candidate mass, needs sigma * BR",
        )
        ax.text(
            0.02,
            0.04,
            "Candidate markers are locations only: NEEDS_SIGMA_X_BR",
            transform=ax.transAxes,
            fontsize=8.5,
            color="dimgray",
        )
    elif experiment.empty:
        pass
    else:
        ax.text(0.02, 0.04, "NO REAL 2HDMC SCAN FILES FOUND", transform=ax.transAxes, fontsize=8.5, color="dimgray")

    ax.set_yscale("log")
    ax.set_xlabel("m_X [GeV]")
    ax.set_ylabel("95% CL upper limit on sigma * BR(gamma gamma) [fb]")
    ax.set_title("ATLAS scalar diphoton limits with candidate mass locations")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def make_figures(theory: pd.DataFrame, priority: pd.DataFrame, experiment: pd.DataFrame, outdir: Path) -> list[Path]:
    fig_dir = outdir / FIG_DIR_NAME
    fig_dir.mkdir(parents=True, exist_ok=True)
    return [
        make_br_figure(theory, priority, fig_dir),
        make_width_figure(theory, priority, fig_dir),
        make_limit_context_figure(experiment, priority, fig_dir),
    ]


def write_readme(
    outdir: Path,
    roots: Iterable[Path],
    inventory: pd.DataFrame,
    theory: pd.DataFrame,
    priority: pd.DataFrame,
    comparison: pd.DataFrame,
    figures: Iterable[Path],
) -> Path:
    path = outdir / "README.md"
    roots_text = "\n".join(f"- `{root}`" for root in roots) or "- no search roots existed"
    figures_text = "\n".join(f"- `{figure}`" for figure in figures)
    if inventory.empty:
        scan_note = "No candidate 2HDMC scan files were found under the configured search roots."
    elif theory.empty:
        scan_note = "Candidate scan files were found, but none produced physical rows with finite m_phi, total_width, and br_gaga."
    else:
        scan_note = "Physical 2HDMC rows were exported to the theory-side contract."

    text = f"""# 2HDMC to Diphoton Pre-Recast Bridge

This directory is generated by `scripts/09_link_2hdmc_to_diphoton.py`.

{scan_note}

## Search Roots

{roots_text}

## Outputs

- `2hdmc_scan_inventory.csv`: accepted and rejected candidate scan inventory.
- `theory_side_from_2hdmc.csv`: physical 2HDMC widths and BRs only.
- `priority_points_for_sigma.csv`: compact list of points that need production cross sections.
- `diphoton_comparison_needs_xsec.csv`: nearest ATLAS limit context only.

## Counts

- Candidate scan files: {len(inventory)}
- Accepted 2HDMC scan files: {int(inventory["accepted_as_2hdmc_scan"].sum()) if "accepted_as_2hdmc_scan" in inventory else 0}
- Physical rows in inventory: {int(inventory["n_physical_rows"].sum()) if "n_physical_rows" in inventory else 0}
- Theory rows exported: {len(theory)}
- Priority points: {len(priority)}
- Comparison rows: {len(comparison)}

## Figures

{figures_text}

## Caveat

Every comparison row is marked `{COMPARISON_STATUS}` and `{EXCLUSION_STATUS}`.  The ATLAS limit values are context only until `sigma_ggF` and/or `sigma_VBF` are computed and combined as `sigma * BR(phi -> gamma gamma)` with the appropriate fiducial or acceptance treatment.
"""
    path.write_text(text, encoding="utf-8")
    return path


def _markdown_list(values: Iterable[str], empty: str = "- none") -> str:
    items = list(values)
    return "\n".join(f"- `{item}`" for item in items) if items else empty


def write_discovery_report(outdir: Path, roots: Iterable[Path], inventory: pd.DataFrame, max_files: int | None) -> Path:
    path = outdir / "discovery_report.md"
    outdir.mkdir(parents=True, exist_ok=True)

    roots = list(roots)
    searched = [str(root) for root in roots if root.exists()]
    missing = [str(root) for root in roots if not root.exists()]
    candidates = inventory["source_path"].astype(str).tolist() if "source_path" in inventory else []
    accepted = (
        inventory.loc[inventory["accepted_as_2hdmc_scan"].astype(bool), "source_path"].astype(str).tolist()
        if not inventory.empty and "accepted_as_2hdmc_scan" in inventory
        else []
    )

    rejected_lines = []
    if not inventory.empty:
        rejected = inventory.loc[~inventory["accepted_as_2hdmc_scan"].astype(bool)].copy()
        for _, row in rejected.iterrows():
            detail = row["rejection_reason"]
            if row.get("missing_columns", ""):
                detail = f"{detail} ({row['missing_columns']})"
            rejected_lines.append(f"- `{row['source_path']}`: {detail}")

    next_command = ""
    if not accepted:
        next_command = (
            'make diphoton-2hdmc-bridge DIPHOTON_2HDMC_ARGS="'
            '--scan-root /path/to/real/2hdmc/campaign --write-discovery-report"'
        )

    cap_text = str(max_files) if max_files is not None else "none"
    text = f"""# 2HDMC Scan Discovery Report

## Roots Searched

{_markdown_list(searched)}

## Roots Missing

{_markdown_list(missing)}

## Candidate Files Found

{_markdown_list(candidates)}

## Accepted 2HDMC Scan Files

{_markdown_list(accepted)}

## Rejected Files

{chr(10).join(rejected_lines) if rejected_lines else "- none"}

## Discovery Settings

- File cap: `{cap_text}`
- Required columns: `{", ".join(REQUIRED_COLUMNS)}`

## Next Command If Zero Accepted

{f'`{next_command}`' if next_command else "- not needed; accepted files were found"}
"""
    path.write_text(text, encoding="utf-8")
    return path


def write_outputs(
    outdir: Path,
    inventory: pd.DataFrame,
    theory: pd.DataFrame,
    priority: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(outdir / "2hdmc_scan_inventory.csv", index=False)
    theory.to_csv(outdir / "theory_side_from_2hdmc.csv", index=False)
    priority.to_csv(outdir / "priority_points_for_sigma.csv", index=False)
    comparison.to_csv(outdir / "diphoton_comparison_needs_xsec.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Link physical 2HDMC scan files to the diphoton pre-recast contract")
    parser.add_argument("--outdir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--max-priority", type=int, default=50)
    parser.add_argument("--scan-root", type=Path, action="append", help="Scan root to search first. May be repeated.")
    parser.add_argument("--search-root", dest="scan_root", type=Path, action="append", help=argparse.SUPPRESS)
    parser.add_argument("--include-default-roots", action="store_true", help="Also search the legacy default roots.")
    parser.add_argument("--max-files", type=int, default=None, help="Safety cap on candidate files to inventory.")
    parser.add_argument("--write-discovery-report", action="store_true", help="Write discovery_report.md.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.scan_root:
        roots = list(args.scan_root)
        if args.include_default_roots:
            roots.extend(default_search_roots())
    else:
        roots = default_search_roots()

    scan_files = discover_scan_files(roots, output_dir=args.outdir, max_files=args.max_files)
    inventory = build_scan_inventory(scan_files)
    accepted_scan_files = (
        [Path(path) for path in inventory.loc[inventory["accepted_as_2hdmc_scan"].astype(bool), "source_path"]]
        if not inventory.empty
        else []
    )
    theory = build_theory_side(accepted_scan_files)
    priority = rank_priority_points(theory, max_points=args.max_priority)
    experiment = load_experiment_side()
    comparison = build_comparison(priority, experiment)

    write_outputs(args.outdir, inventory, theory, priority, comparison)
    figures = make_figures(theory, priority, experiment, args.outdir)
    write_readme(args.outdir, roots, inventory, theory, priority, comparison, figures)
    write_discovery_report(args.outdir, roots, inventory, args.max_files)

    print(f"[OK] wrote bridge outputs under {args.outdir}")
    print(f"[OK] roots searched: {', '.join(str(root) for root in roots if root.exists()) or 'none'}")
    print(f"[OK] candidate scan files: {len(inventory)}")
    print(f"[OK] accepted 2HDMC scan files: {len(accepted_scan_files)}")
    print(f"[OK] physical rows in inventory: {int(inventory['n_physical_rows'].sum()) if 'n_physical_rows' in inventory else 0}")
    print(f"[OK] priority points needing sigma: {len(priority)}")
    print("[OK] comparison status: NEEDS_SIGMA_X_BR; NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
