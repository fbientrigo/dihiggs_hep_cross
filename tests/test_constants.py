import os

import pytest

from llp_recast import constants, recast_math

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVENTIONS = os.path.join(REPO_ROOT, "conventions", "physics_conventions.yaml")


def test_conventions_file_present():
    assert os.path.exists(CONVENTIONS)


def test_constants_match_pinned_fallback():
    """The loaded constants must equal the pinned fallback literals, so the
    shared conventions file can never silently disagree with the code."""
    assert constants.HBAR_C_GEV_MM == constants._HBAR_C_GEV_MM_PINNED
    assert constants.C_MM_PER_NS == constants._C_MM_PER_NS_PINNED


def test_constants_match_conventions_yaml():
    yaml = pytest.importorskip("yaml")
    with open(CONVENTIONS) as fh:
        conv = yaml.safe_load(fh)
    assert constants.HBAR_C_GEV_MM == float(conv["hbar_c_gev_mm"])
    assert constants.C_MM_PER_NS == float(conv["c_mm_per_ns"])


def test_pinned_values():
    assert constants.HBAR_C_GEV_MM == 1.973269804e-13
    assert constants.C_MM_PER_NS == 299.792458


def test_recast_math_uses_shared_constant():
    """ctau_mm_from_width_gev must be consistent with the shared hbar_c."""
    width = 1e-13
    assert recast_math.ctau_mm_from_width_gev(width) == (
        constants.HBAR_C_GEV_MM / width
    )
