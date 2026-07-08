import csv
import os

import pytest

from llp_recast import data_contract
from llp_recast.constants import HBAR_C_GEV_MM

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT_YAML = os.path.join(
    REPO_ROOT, "contracts", "model_point_to_llp_recast_v1.yaml"
)


def _good_row(total_width_GeV=1e-13):
    return {
        "model": "2HDM_typeII",
        "point_id": "p0",
        "m_scalar_GeV": "150.0",
        "total_width_GeV": repr(total_width_GeV),
        "ctau_mm": repr(HBAR_C_GEV_MM / total_width_GeV),
        "sigma_production_fb": "10.0",
        "BR_bb": "0.6",
        "BR_WW": "0.1",
        "BR_ZZ": "0.05",
        "BR_gg": "0.1",
        "BR_tautau": "0.05",
        "BR_hadronic_proxy": "0.8",
        "beta_gamma_source": "assumed_flat",
        "recast_channel_hint": "trackless_sr",
    }


def _write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_committed_yaml_matches_code():
    """contracts/model_point_to_llp_recast_v1.yaml must equal the code
    definition. If this fails, run `python -m llp_recast.data_contract --emit`."""
    yaml = pytest.importorskip("yaml")
    assert os.path.exists(CONTRACT_YAML), "run data_contract --emit and commit"
    with open(CONTRACT_YAML) as fh:
        committed = yaml.safe_load(fh)
    assert committed == data_contract.MODEL_POINT_CONTRACT


def test_accepts_good_model_points(tmp_path):
    path = tmp_path / "good.csv"
    _write_csv(path, [_good_row(), _good_row(total_width_GeV=5e-14)])
    report = data_contract.validate_csv(str(path))
    assert report.ok, report.describe()
    assert report.n_rows == 2


def test_rejects_missing_column(tmp_path):
    row = _good_row()
    del row["ctau_mm"]
    path = tmp_path / "missing.csv"
    _write_csv(path, [row])
    report = data_contract.validate_csv(str(path))
    assert not report.ok
    assert "ctau_mm" in report.missing_columns


def test_catches_inconsistent_ctau(tmp_path):
    """ctau_mm that does not equal hbar_c / total_width_GeV is exactly the
    'independently-guessed value' the contract forbids."""
    row = _good_row()
    row["ctau_mm"] = "999.0"  # inconsistent with total_width_GeV
    path = tmp_path / "badctau.csv"
    _write_csv(path, [row])
    report = data_contract.validate_csv(str(path))
    assert not report.ok
    assert any("ctau" in name for name, _c, _e in report.invariant_violations)


def test_catches_br_sum_over_one(tmp_path):
    row = _good_row()
    row["BR_bb"] = "0.9"
    row["BR_WW"] = "0.9"  # sum now well over 1
    path = tmp_path / "badbr.csv"
    _write_csv(path, [row])
    report = data_contract.validate_csv(str(path))
    assert not report.ok
    assert any("BR" in name or "sum" in name for name, _c, _e in report.invariant_violations)


def test_catches_illegal_beta_gamma_source(tmp_path):
    row = _good_row()
    row["beta_gamma_source"] = "made_up_value"
    path = tmp_path / "badenum.csv"
    _write_csv(path, [row])
    report = data_contract.validate_csv(str(path))
    assert not report.ok
    assert report.bad_enum_rows


def test_empty_and_missing_file(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    assert not data_contract.validate_csv(str(empty)).ok
    assert not data_contract.validate_csv(str(tmp_path / "nope.csv")).ok
