import os

import pytest

from llp_recast import constants, recast_math

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVENTIONS = os.path.join(REPO_ROOT, "conventions", "physics_conventions.yaml")


def test_conventions_file_present():
    assert os.path.exists(CONVENTIONS)


def test_constants_are_loaded_from_the_v3_cache():
    assert constants.HBAR_C_GEV_MM == 1.973269804e-13
    assert constants.C_MM_PER_NS == 299.792458
    assert constants.M_H_GEV_TEXT == "125.20"


def test_constants_match_conventions_yaml():
    yaml = pytest.importorskip("yaml")
    with open(CONVENTIONS) as fh:
        conv = yaml.safe_load(fh)
    assert constants.HBAR_C_GEV_MM == float(conv["constants"]["hbar_c_gev_mm"])
    assert constants.C_MM_PER_NS == float(conv["constants"]["c_mm_per_ns"])


def test_pinned_values():
    assert constants.HBAR_C_GEV_MM == 1.973269804e-13
    assert constants.C_MM_PER_NS == 299.792458


def test_recast_math_uses_shared_constant():
    """ctau_mm_from_width_gev must be consistent with the shared hbar_c."""
    width = 1e-13
    assert recast_math.ctau_mm_from_width_gev(width) == (
        constants.HBAR_C_GEV_MM / width
    )


def test_canonical_mh_matches_conventions_file():
    """The SM-like Higgs mass has exactly one owner; constants must serve the
    file's value, not its pinned fallback."""
    yaml = pytest.importorskip("yaml")
    with open(CONVENTIONS) as fh:
        conv = yaml.safe_load(fh)
    assert conv["mass_conventions"]["active"]["value_GeV"] == constants.M_H_GEV_TEXT
    # Decimal string, not float: f"{125.20:.17e}" is 1.25200000000000003e+02,
    # which is not the byte form SLHA/UFO cards need.
    assert isinstance(conv["mass_conventions"]["active"]["value_GeV"], str)


def test_convention_loader_fails_closed_on_tampered_sidecar(tmp_path, monkeypatch):
    import yaml

    cache = tmp_path / "physics_conventions.yaml"
    sidecar = tmp_path / "physics_conventions.lock.yaml"
    cache.write_bytes(open(CONVENTIONS, "rb").read())
    lock = yaml.safe_load(open(constants.CONVENTIONS_LOCK_PATH))
    lock["source_commit"] = "0" * 40
    sidecar.write_text(yaml.safe_dump(lock))
    monkeypatch.setattr(constants, "CONVENTIONS_PATH", cache)
    monkeypatch.setattr(constants, "CONVENTIONS_LOCK_PATH", sidecar)
    with pytest.raises(RuntimeError, match="source_commit"):
        constants._load_conventions()
