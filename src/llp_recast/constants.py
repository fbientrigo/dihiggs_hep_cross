"""Physics and analysis constants loaded from the controlled v3 cache."""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
CONVENTIONS_PATH = _REPO_ROOT / "conventions/physics_conventions.yaml"
CONVENTIONS_LOCK_PATH = _REPO_ROOT / "conventions/physics_conventions.lock.yaml"
_AUTHORITY_COMMIT = "087ba246e9a9fa34b16249b52629a62703893b5c"
_AUTHORITY_SHA256 = "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6"


def _load_conventions():
    try:
        content = CONVENTIONS_PATH.read_bytes()
        sidecar = yaml.safe_load(CONVENTIONS_LOCK_PATH.read_text(encoding="utf-8"))
        conventions = yaml.safe_load(content)
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError("cannot load the v3 physics convention cache and provenance") from exc

    digest = hashlib.sha256(content).hexdigest()
    expected = {
        "source_repository": "fbientrigo/dihiggs",
        "source_commit": _AUTHORITY_COMMIT,
        "source_path": "conventions/physics_conventions.yaml",
        "source_sha256": _AUTHORITY_SHA256,
        "schema_version": "physics_conventions_v3",
    }
    if digest != _AUTHORITY_SHA256 or not isinstance(sidecar, dict):
        raise RuntimeError("physics convention cache checksum or sidecar is invalid")
    for field, value in expected.items():
        if sidecar.get(field) != value:
            raise RuntimeError(f"physics convention provenance {field} does not match authority")
    if not isinstance(conventions, dict) or conventions.get("schema_version") != "physics_conventions_v3":
        raise RuntimeError("physics convention cache is not physics_conventions_v3")
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
