"""Shared MadGraph interface helpers for the diphoton sigma-input pipeline.

This module is the single source of truth for:

* the normalized MadGraph cross-section run-table schema
  (consumed by ``scripts/11_ingest_madgraph_xsec.py``), and
* the MadGraph run-preparation basis
  (produced by ``scripts/12_prepare_madgraph_runs.py``).

It deliberately contains **no physics fabrication**.  It only defines the table
columns, the input-deck templates' placeholder contract, and small pure helpers.
No UFO/model is shipped and no cross section is invented anywhere in this module:
the run-table skeleton it builds leaves every cross-section field blank, to be
filled in only after a real MadGraph run.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

# --- Normalized run-table schema -------------------------------------------

# Columns of the normalized MadGraph run table consumed by
# ``scripts/11_ingest_madgraph_xsec.py`` (see
# docs/contracts/madgraph_xsec_output_contract.md).
MADGRAPH_RUN_COLUMNS = [
    "point_id",
    "mg_run_name",
    "process",
    "sqrt_s_TeV",
    "xsec_pb",
    "xsec_fb",
    "xsec_unc_pb",
    "k_factor",
    "production_mode",
    "madgraph_version",
    "model_name",
    "param_card_path",
    "run_card_path",
    "banner_path",
    "lhe_path",
    "notes",
]

# Priority-context columns carried at the front of the fill-in template so that a
# human filling cross sections can see the point they belong to.
PRIORITY_CONTEXT_COLUMNS = ["point_id", "priority_rank", "m_H_GeV", "Gamma_over_m", "br_gaga"]

# The full fill-in template = priority context + run columns (minus the duplicate
# point_id already provided by the context block).
MADGRAPH_TEMPLATE_COLUMNS = PRIORITY_CONTEXT_COLUMNS + [c for c in MADGRAPH_RUN_COLUMNS if c != "point_id"]

# Cross-section fields that must stay blank in a prepared-but-not-run skeleton.
UNRUN_BLANK_COLUMNS = ["xsec_pb", "xsec_fb", "xsec_unc_pb", "madgraph_version", "banner_path", "lhe_path"]

# --- Defaults for the preparation basis ------------------------------------

# Production of the heavy scalar only; BR(gamma gamma) is applied downstream in
# scripts/10_apply_sigma_inputs.py, so the MadGraph process is production-only.
DEFAULT_PROCESS = "g g > h2"
DEFAULT_SQRT_S_TEV = 13.0
# The UFO/model does not exist yet.  This placeholder must be replaced with a real
# model name before running MadGraph; it is never treated as a valid model here.
MODEL_PLACEHOLDER = "TODO_SUPPLY_UFO_MODEL"
UNRUN_NOTE = "PREPARED_DECK_AWAITING_MADGRAPH_RUN;NO_XSEC_FABRICATED"

TEMPLATE_DIR = Path("data/madgraph/templates")


def infer_production_mode(process: str = "", existing: str = "") -> str:
    """Best-effort production-mode label from an explicit value or a process string."""
    if isinstance(existing, str) and existing.strip():
        return existing.strip()
    text = str(process).lower()
    if "vbf" in text or "j j" in text or "jj" in text:
        return "VBF"
    if "g g" in text or "gg" in text or "gluon" in text:
        return "ggF"
    return "unknown"


def sanitize_run_name(point_id: str) -> str:
    """Turn a point_id into a filesystem/MadGraph-safe run tag."""
    safe = re.sub(r"[^0-9A-Za-z]+", "_", str(point_id)).strip("_")
    return f"mg_{safe}" if safe else "mg_run"


def render_template(text: str, mapping: Mapping[str, object]) -> str:
    """Replace ``{{KEY}}`` placeholders in ``text`` with values from ``mapping``.

    Unknown placeholders are left untouched so that missing values are visible
    rather than silently blanked.
    """
    rendered = text
    for key, value in mapping.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def _empty(columns: Iterable[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))


def generated_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_run_skeleton(
    priority: pd.DataFrame,
    *,
    max_rows: int = 50,
    process: str = DEFAULT_PROCESS,
    sqrt_s_TeV: float = DEFAULT_SQRT_S_TEV,
    model_name: str = MODEL_PLACEHOLDER,
    deck_root: Path = Path("outputs/madgraph_runs"),
) -> pd.DataFrame:
    """Build a normalized run-table skeleton (one row per priority point).

    Cross-section fields are left blank on purpose: nothing is fabricated.  Each
    row records the process, the placeholder model, and the paths of the input
    deck that ``scripts/12_prepare_madgraph_runs.py`` renders for the point.
    """
    if priority.empty or "point_id" not in priority.columns:
        return _empty(MADGRAPH_TEMPLATE_COLUMNS)

    context = [c for c in PRIORITY_CONTEXT_COLUMNS if c in priority.columns]
    skeleton = priority[context].head(max_rows).copy()
    skeleton["point_id"] = skeleton["point_id"].astype(str)

    run_names = skeleton["point_id"].map(sanitize_run_name)
    mode = infer_production_mode(process=process)

    skeleton["mg_run_name"] = run_names
    skeleton["process"] = process
    skeleton["sqrt_s_TeV"] = sqrt_s_TeV
    skeleton["production_mode"] = mode
    skeleton["model_name"] = model_name
    skeleton["k_factor"] = ""
    skeleton["param_card_path"] = run_names.map(lambda r: str(deck_root / r / "param_card_fragment.dat"))
    skeleton["run_card_path"] = run_names.map(lambda r: str(deck_root / r / "run_card_fragment.dat"))
    skeleton["notes"] = UNRUN_NOTE
    for col in UNRUN_BLANK_COLUMNS:
        skeleton[col] = ""

    for col in MADGRAPH_TEMPLATE_COLUMNS:
        if col not in skeleton.columns:
            skeleton[col] = ""
    return skeleton[MADGRAPH_TEMPLATE_COLUMNS].reset_index(drop=True)


def deck_context(row: pd.Series, *, model_name: str = MODEL_PLACEHOLDER) -> dict[str, object]:
    """Assemble the placeholder mapping used to render one point's input deck."""
    run_name = sanitize_run_name(row["point_id"])
    sqrt_s = row.get("sqrt_s_TeV", DEFAULT_SQRT_S_TEV)
    try:
        ebeam = float(sqrt_s) * 1000.0 / 2.0
    except (TypeError, ValueError):
        ebeam = ""
    return {
        "POINT_ID": row["point_id"],
        "RUN_NAME": run_name,
        "MODEL": row.get("model_name", model_name) or model_name,
        "PROCESS": row.get("process", DEFAULT_PROCESS),
        "SQRT_S_TEV": sqrt_s,
        "EBEAM_GEV": ebeam,
        "MH_GEV": row.get("m_H_GeV", ""),
        "WIDTH_GEV": row.get("Gamma_H_GeV", ""),
        "BR_GAGA": row.get("br_gaga", ""),
        "GENERATED_AT": generated_at(),
    }
