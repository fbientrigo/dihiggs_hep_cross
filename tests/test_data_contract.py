import csv
import os

import pytest

from llp_recast import data_contract as dc2
from llp_recast.constants import HBAR_C_GEV_MM

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT_YAML = os.path.join(
    REPO_ROOT, "contracts", "model_point_to_llp_recast.yaml"
)

# Shared synthetic high-mass-point coordinates (respect the mA=mHp>mH2>mh
# hierarchy and the H2_to_*_open kinematic formulas from cascade_contract.yaml
# in the dihiggs repo). All four cascade flags are false at this point.
M_H = 125.13
M_H2 = 300.0
DELTA_HEAVY = 500.0
M_A = M_H2 + DELTA_HEAVY  # 800.0
M_HP = M_A
TOTAL_WIDTH = 2.5
CTAU_PHYSICAL = HBAR_C_GEV_MM / TOTAL_WIDTH


def _base_row(**overrides):
    row = {
        "schema_version": dc2.SCHEMA_VERSION,
        "point_id": "hmp_0001",
        "model_variant": dc2.VARIANT_A,
        "m_h_GeV": repr(M_H),
        "m_H2_GeV": repr(M_H2),
        "m_A_GeV": repr(M_A),
        "m_Hp_GeV": repr(M_HP),
        "Delta_heavy_GeV": repr(DELTA_HEAVY),
        "g_hH2H2_GeV": "45.7",
        "total_width_GeV": repr(TOTAL_WIDTH),
        "ctau_physical_mm": repr(CTAU_PHYSICAL),
        "ctau_response_mm": repr(CTAU_PHYSICAL),
        "lifetime_mode": dc2.PHYSICAL_LIFETIME_MODE,
        "BR_bb": "0.3",
        "BR_cc": "0.05",
        "BR_tt": "0.0",
        "BR_tautau": "0.05",
        "BR_WW": "0.2",
        "BR_ZZ": "0.1",
        "BR_gg": "0.05",
        "BR_gammagamma": "0.01",
        "BR_Zgamma": "0.01",
        "BR_hh": "0.2",
        "production_process": "pp -> H2 H2",
        "production_owner": "DOWNSTREAM_MADGRAPH",
        "decay_owner": "CANONICAL_EVALUATOR",
        "response_decay_channel": "NONE",
        "H2_to_AZ_open": "False",
        "H2_to_HpW_open": "False",
        "H2_to_AA_open": "False",
        "H2_to_HpHm_open": "False",
        "theory_status": "PASS",
        "experimental_status": "NOT_APPLICABLE",
        "sigma_production_fb": "12.5",
        "sigma_source": dc2.CANONICAL_SIGMA_SOURCE,
        "sigma_provenance": "madgraph run xyz, seed 42",
        "producer_commit": "abc1234",
        "config_hash": "sha256:deadbeef",
        "input_hash": "sha256:cafef00d",
    }
    row.update(overrides)
    return row


def _good_row_variant_a(**overrides):
    row = _base_row(
        model_variant=dc2.VARIANT_A,
        lifetime_mode=dc2.RESPONSE_LIFETIME_MODE,
    )
    # Variant A: response lifetime independently scanned, may legitimately
    # differ from the physical (width-derived) lifetime.
    row["ctau_response_mm"] = "50.0"
    row.update(overrides)
    return row


def _good_row_variant_b(**overrides):
    row = _base_row(
        model_variant=dc2.VARIANT_B,
        lifetime_mode=dc2.PHYSICAL_LIFETIME_MODE,
    )
    # Variant B: response lifetime must equal the physical lifetime exactly.
    row["ctau_response_mm"] = repr(CTAU_PHYSICAL)
    row.update(overrides)
    return row


def _write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# --- contract/YAML mirror ----------------------------------------------------


def test_committed_yaml_matches_code():
    """contracts/model_point_to_llp_recast.yaml must equal the code
    definition. If this fails, run
    `python -m llp_recast.data_contract --emit`."""
    yaml = pytest.importorskip("yaml")
    assert os.path.exists(CONTRACT_YAML), "run data_contract --emit and commit"
    with open(CONTRACT_YAML) as fh:
        committed = yaml.safe_load(fh)
    assert committed == dc2.MODEL_POINT_CONTRACT


def test_legacy_runtime_paths_are_removed():
    assert os.path.exists(os.path.join(REPO_ROOT, "contracts", "model_point_to_llp_recast.yaml"))
    assert os.path.exists(os.path.join(REPO_ROOT, "src", "llp_recast", "data_contract.py"))


# --- basic acceptance ---------------------------------------------------------


def test_accepts_good_variant_a_row(tmp_path):
    path = tmp_path / "good_a.csv"
    _write_csv(path, [_good_row_variant_a()])
    report = dc2.validate_csv(str(path))
    assert report.ok, report.describe()
    assert report.n_rows == 1


def test_accepts_good_variant_b_row(tmp_path):
    path = tmp_path / "good_b.csv"
    _write_csv(path, [_good_row_variant_b()])
    report = dc2.validate_csv(str(path))
    assert report.ok, report.describe()
    assert report.n_rows == 1


def test_rejects_missing_column(tmp_path):
    row = _good_row_variant_a()
    del row["ctau_physical_mm"]
    path = tmp_path / "missing.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert "ctau_physical_mm" in report.missing_columns


def test_requires_sigma_provenance_value(tmp_path):
    row = _good_row_variant_a(sigma_provenance="")
    path = tmp_path / "missing_sigma_provenance.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("required semantic fields" in name for name, _c, _e in report.invariant_violations)


def test_requires_explicit_lifetime_mode_for_a_mismatch(tmp_path):
    row = _good_row_variant_a(lifetime_mode=dc2.PHYSICAL_LIFETIME_MODE)
    path = tmp_path / "implicit_response.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("lifetime" in name for name, _c, _e in report.invariant_violations)


def test_rejects_negative_branching_fraction(tmp_path):
    row = _good_row_variant_a(BR_tt="-0.1")
    path = tmp_path / "negative_br.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("branching fractions" in name for name, _c, _e in report.invariant_violations)


# --- model_variant enum -------------------------------------------------------


def test_rejects_bad_model_variant(tmp_path):
    row = _good_row_variant_a()
    row["model_variant"] = "SOME_MADE_UP_VARIANT"
    path = tmp_path / "badvariant.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("model_variant" in name for name, _c, _e in report.invariant_violations)


# --- cascade flags -------------------------------------------------------------


def test_rejects_variant_b_with_forbidden_cascade_flag_true(tmp_path):
    row = _good_row_variant_b()
    row["H2_to_AZ_open"] = "True"
    path = tmp_path / "badcascade.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("cascade" in name for name, _c, _e in report.invariant_violations)


def test_accepts_variant_a_with_cascade_flag_true():
    """Variant A carries the cascade flags as a diagnostic only; a true flag
    is not itself a contract violation for FACTORIZED_G_ONLY."""
    row = _good_row_variant_a()
    row["H2_to_AZ_open"] = "True"
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "a_cascade_true.csv")
        _write_csv(path, [row])
        report = dc2.validate_csv(path)
    assert report.ok, report.describe()


# --- ctau_physical_mm / total_width_GeV consistency ---------------------------


def test_rejects_variant_a_bad_ctau_physical(tmp_path):
    row = _good_row_variant_a()
    row["ctau_physical_mm"] = "999.0"  # inconsistent with total_width_GeV
    path = tmp_path / "bad_ctau_a.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("ctau_physical_mm" in name for name, _c, _e in report.invariant_violations)


def test_rejects_variant_b_bad_ctau_physical(tmp_path):
    row = _good_row_variant_b()
    row["ctau_physical_mm"] = "999.0"
    row["ctau_response_mm"] = "999.0"  # keep equal-to-physical so only the
    # physical-vs-width invariant is under test here.
    path = tmp_path / "bad_ctau_b.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("ctau_physical_mm" in name for name, _c, _e in report.invariant_violations)


# --- ctau_response_mm vs ctau_physical_mm --------------------------------------


def test_rejects_variant_b_response_ctau_mismatch(tmp_path):
    row = _good_row_variant_b()
    row["ctau_response_mm"] = repr(CTAU_PHYSICAL * 2.0)  # mismatched
    path = tmp_path / "b_mismatch.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("lifetime" in name for name, _c, _e in report.invariant_violations)


def test_accepts_variant_a_response_ctau_mismatch(tmp_path):
    """The same physical/response mismatch that is fatal for Variant B is
    legitimate for Variant A (an independently scanned response lifetime)."""
    row = _good_row_variant_a()
    row["ctau_response_mm"] = repr(CTAU_PHYSICAL * 2.0)
    path = tmp_path / "a_mismatch_ok.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert report.ok, report.describe()


# --- BR sum ---------------------------------------------------------------------


def test_catches_br_sum_over_one(tmp_path):
    row = _good_row_variant_a()
    row["BR_bb"] = "0.9"
    row["BR_WW"] = "0.9"  # sum now well over 1
    path = tmp_path / "badbr.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any(
        "BR" in name or "sum" in name for name, _c, _e in report.invariant_violations
    )


def test_br_sum_covers_all_ten_channels(tmp_path):
    """The gap report's core finding: v1 only summed 5 of 10 channels
    (missing BR_cc, BR_tt, BR_gammagamma, BR_Zgamma, BR_hh). Confirm v2's sum
    invariant is violated by an overflow concentrated entirely in one of
    those previously-missing channels."""
    row = _good_row_variant_a()
    row["BR_hh"] = "0.99"  # alone already pushes the 10-channel sum > 1
    path = tmp_path / "badbr_hh.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok


# --- hierarchy -------------------------------------------------------------------


def test_rejects_bad_hierarchy(tmp_path):
    row = _good_row_variant_a()
    row["m_H2_GeV"] = "900.0"  # now m_H2 > m_A, hierarchy broken
    path = tmp_path / "badhierarchy.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("hierarchy" in name for name, _c, _e in report.invariant_violations)


def test_rejects_mA_not_equal_mHp(tmp_path):
    row = _good_row_variant_a()
    row["m_Hp_GeV"] = "750.0"  # != m_A_GeV
    path = tmp_path / "bad_mhp.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("hierarchy" in name for name, _c, _e in report.invariant_violations)


# --- production process ----------------------------------------------------------


def test_rejects_bad_production_process(tmp_path):
    row = _good_row_variant_a()
    row["production_process"] = "pp -> H2 H2 A"
    path = tmp_path / "badprocess.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("production_process" in name for name, _c, _e in report.invariant_violations)


# --- sigma_source: accepted but not mislabeled as canonical ----------------------


def test_non_canonical_sigma_source_accepted_but_flagged(tmp_path):
    row = _good_row_variant_a()
    row["sigma_source"] = "G_SQUARED_SCALING_ESTIMATE"
    path = tmp_path / "noncanonical.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    # Row is accepted...
    assert report.ok, report.describe()
    # ...but structurally flagged as non-canonical, not silently accepted as
    # a trustworthy physical cross section.
    assert report.non_canonical_sigma_rows == [1]
    assert not dc2.is_canonical_sigma_source(row["sigma_source"])
    assert "non-canonical" in report.describe()


def test_canonical_sigma_source_not_flagged(tmp_path):
    row = _good_row_variant_a()
    assert row["sigma_source"] == dc2.CANONICAL_SIGMA_SOURCE
    path = tmp_path / "canonical.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert report.ok, report.describe()
    assert report.non_canonical_sigma_rows == []
    assert dc2.is_canonical_sigma_source(row["sigma_source"])


def test_rejects_bad_sigma_source(tmp_path):
    row = _good_row_variant_a()
    row["sigma_source"] = "MADE_UP_SOURCE"
    path = tmp_path / "badsigma.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("sigma_source" in name for name, _c, _e in report.invariant_violations)


# --- decay ownership ---------------------------------------------------------------


def test_forced_decay_owner_valid_on_variant_a_with_channel(tmp_path):
    row = _good_row_variant_a(
        decay_owner=dc2.DECAY_OWNER_RESPONSE_FORCED,
        response_decay_channel="bb",
    )
    path = tmp_path / "forced_ok.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert report.ok, report.describe()


def test_forced_decay_owner_rejected_without_channel(tmp_path):
    row = _good_row_variant_a(
        decay_owner=dc2.DECAY_OWNER_RESPONSE_FORCED,
        response_decay_channel="NONE",
    )
    path = tmp_path / "forced_no_channel.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("decay_owner" in name for name, _c, _e in report.invariant_violations)


def test_forced_decay_owner_rejected_on_variant_b(tmp_path):
    row = _good_row_variant_b(
        decay_owner=dc2.DECAY_OWNER_RESPONSE_FORCED,
        response_decay_channel="bb",
    )
    path = tmp_path / "forced_on_b.csv"
    _write_csv(path, [row])
    report = dc2.validate_csv(str(path))
    assert not report.ok
    assert any("decay_owner" in name for name, _c, _e in report.invariant_violations)


# --- empty/missing files ------------------------------------------------------------


def test_empty_and_missing_file(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    assert not dc2.validate_csv(str(empty)).ok
    assert not dc2.validate_csv(str(tmp_path / "nope.csv")).ok
