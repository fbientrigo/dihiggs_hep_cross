"""Physics and analysis constants for the minimal LLP recast scaffold.

The shared physics conventions (hbar*c, c) are loaded from the ecosystem-wide
``conventions/physics_conventions.yaml`` so this repo cannot drift from
dihiggs / dihiggs_boundary. The pinned literals below are the fallback used
when PyYAML or the file is unavailable; ``tests/test_constants.py`` asserts the
loaded values equal these literals so the two can never silently disagree.
"""

import os

# Pinned fallback values (must equal conventions/physics_conventions.yaml).
_HBAR_C_GEV_MM_PINNED = 1.973269804e-13  # c*tau[mm] = hbar*c / Gamma[GeV]
_C_MM_PER_NS_PINNED = 299.792458  # c*tau[mm] = C_MM_PER_NS * tau[ns]

# repo root: src/llp_recast/constants.py -> up three levels.
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
CONVENTIONS_PATH = os.path.join(
    _REPO_ROOT, "conventions", "physics_conventions.yaml"
)


def _load_conventions():
    try:
        import yaml
    except ImportError:
        return {}
    try:
        with open(CONVENTIONS_PATH) as fh:
            return yaml.safe_load(fh) or {}
    except OSError:
        return {}


_CONV = _load_conventions()

HBAR_C_GEV_MM = float(_CONV.get("hbar_c_gev_mm", _HBAR_C_GEV_MM_PINNED))
C_MM_PER_NS = float(_CONV.get("c_mm_per_ns", _C_MM_PER_NS_PINNED))

ATLAS_DVJETS_LUMI_FB = 139.0
ATLAS_DVJETS_SQRTS_TEV = 13.0
ID_R_MIN_MM = 4.0
ID_R_MAX_MM = 300.0
ID_Z_MAX_MM = 300.0
