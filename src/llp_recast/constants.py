"""Physics and analysis constants loaded from the dihiggs v3 convention."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
# One owner: dihiggs. Sibling checkout (the workspace layout) or $DIHIGGS_ROOT.
CONVENTIONS_PATH = (
    Path(os.environ.get("DIHIGGS_ROOT") or _REPO_ROOT.parent / "dihiggs") / "conventions/physics_conventions.yaml"
)
_AUTHORITY_SHA256 = "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6"


def _load_conventions():
    try:
        content = CONVENTIONS_PATH.read_bytes()
    except OSError as exc:
        raise RuntimeError(
            f"physics convention YAML not found at {CONVENTIONS_PATH}; "
            "check out dihiggs next to this repo or set DIHIGGS_ROOT"
        ) from exc
    if hashlib.sha256(content).hexdigest() != _AUTHORITY_SHA256:
        raise RuntimeError(f"physics convention checksum mismatch at {CONVENTIONS_PATH}")
    conventions = yaml.safe_load(content)
    if not isinstance(conventions, dict) or conventions.get("schema_version") != "physics_conventions_v3":
        raise RuntimeError("physics convention is not physics_conventions_v3")
    return conventions


_CONV = _load_conventions()
HBAR_C_GEV_MM = float(_CONV["constants"]["hbar_c_gev_mm"])
C_MM_PER_NS = float(_CONV["constants"]["c_mm_per_ns"])
M_H_GEV_TEXT = _CONV["mass_conventions"]["active"]["value_GeV"]
if not isinstance(M_H_GEV_TEXT, str):
    raise RuntimeError("active m_h convention must remain a decimal string")
M_H_GEV = float(M_H_GEV_TEXT)

ATLAS_DVJETS_LUMI_FB = 139.0
ATLAS_DVJETS_SQRTS_TEV = 13.0
ID_R_MIN_MM = 4.0
ID_R_MAX_MM = 300.0
ID_Z_MAX_MM = 300.0
