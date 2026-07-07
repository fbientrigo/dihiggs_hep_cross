"""Small shared pandas/CSV helpers used across the sigma-input scripts.

These are the tiny, byte-identical helpers that scripts 10/11/12 and
``llp_recast.madgraph`` previously each defined for themselves.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    """Read a CSV, or return an empty frame if the file does not exist."""
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def empty_frame(columns: Iterable[str]) -> pd.DataFrame:
    """An empty frame with a fixed, ordered set of columns (schema-stable)."""
    return pd.DataFrame(columns=list(columns))


def numeric_column(df: pd.DataFrame, column: str) -> pd.Series:
    """Coerce a column to numeric, tolerating an absent column."""
    if column not in df.columns:
        return pd.Series(pd.NA, index=df.index, dtype="Float64")
    return pd.to_numeric(df[column], errors="coerce")


def finite_positive(series: pd.Series) -> pd.Series:
    """Boolean mask of entries that are finite and strictly positive."""
    numeric = pd.to_numeric(series, errors="coerce")
    values = numeric.to_numpy(dtype=float, na_value=np.nan)
    return pd.Series(np.isfinite(values) & (values > 0), index=series.index)
