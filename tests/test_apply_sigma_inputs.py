import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "10_apply_sigma_inputs.py"

spec = importlib.util.spec_from_file_location("apply_sigma_inputs", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _priority() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "priority_rank": 1,
                "point_id": "p1",
                "source_csv": "scan.csv",
                "source_row": 10,
                "m_H_GeV": 500.0,
                "Gamma_H_GeV": 10.0,
                "Gamma_over_m": 0.02,
                "br_gaga": 0.05,
                "tanbeta": 2.0,
                "nearest_atlas_width_hypothesis": "2pct",
                "width_hypothesis_distance": 0.0,
                "atlas_mass_range_status": "INSIDE_ATLAS_SCALAR_RANGE_160_3000_GEV",
                "theory_status": "REAL_2HDMC_WIDTHS_AND_BR",
                "xsec_status": "MISSING_PRODUCTION_XSEC",
                "exclusion_status": "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED",
            },
            {
                "priority_rank": 2,
                "point_id": "p2",
                "source_csv": "scan.csv",
                "source_row": 11,
                "m_H_GeV": 700.0,
                "Gamma_H_GeV": 42.0,
                "Gamma_over_m": 0.06,
                "br_gaga": 0.01,
                "tanbeta": 2.0,
                "nearest_atlas_width_hypothesis": "6pct",
                "width_hypothesis_distance": 0.0,
                "atlas_mass_range_status": "INSIDE_ATLAS_SCALAR_RANGE_160_3000_GEV",
                "theory_status": "REAL_2HDMC_WIDTHS_AND_BR",
                "xsec_status": "MISSING_PRODUCTION_XSEC",
                "exclusion_status": "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED",
            },
        ]
    )


def _comparison() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "priority_rank": 1,
                "point_id": "p1",
                "source_csv": "scan.csv",
                "source_row": 10,
                "m_H_GeV": 500.0,
                "Gamma_H_GeV": 10.0,
                "Gamma_over_m": 0.02,
                "br_gaga": 0.05,
                "nearest_mass_GeV": 500.0,
                "nearest_width_hypothesis": "2pct",
                "nearest_Gamma_over_m": 0.02,
                "observed_limit_fb": 1.0,
                "expected_limit_fb": 2.0,
                "comparison_status": "NEEDS_SIGMA_X_BR",
                "exclusion_status": "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED",
                "notes": "ATLAS_LIMIT_CONTEXT_ONLY_NEEDS_SIGMA_X_BR",
            },
            {
                "priority_rank": 2,
                "point_id": "p2",
                "source_csv": "scan.csv",
                "source_row": 11,
                "m_H_GeV": 700.0,
                "Gamma_H_GeV": 42.0,
                "Gamma_over_m": 0.06,
                "br_gaga": 0.01,
                "nearest_mass_GeV": 700.0,
                "nearest_width_hypothesis": "6pct",
                "nearest_Gamma_over_m": 0.06,
                "observed_limit_fb": 3.0,
                "expected_limit_fb": 4.0,
                "comparison_status": "NEEDS_SIGMA_X_BR",
                "exclusion_status": "NOT_EXCLUSION_UNTIL_XSEC_SUPPLIED",
                "notes": "ATLAS_LIMIT_CONTEXT_ONLY_NEEDS_SIGMA_X_BR",
            },
        ]
    )


def test_template_contains_priority_points_and_blank_sigma_fields():
    template = mod.build_sigma_template(_priority(), max_rows=1)

    assert template["point_id"].tolist() == ["p1"]
    assert template.loc[0, "m_H_GeV"] == 500.0
    assert template.loc[0, "sigma_ggF_fb"] == ""
    assert template.loc[0, "sigma_total_fb"] == ""


def test_sigma_components_compute_total_and_context_ratios_without_exclusion():
    sigma = pd.DataFrame(
        [
            {
                "point_id": "p1",
                "sigma_ggF_fb": 30.0,
                "sigma_VBF_fb": 10.0,
                "sigma_source": "manual_test",
                "production_mode": "ggF+VBF",
            }
        ]
    )

    out = mod.build_sigma_applied(_priority(), _comparison(), sigma)
    row = out.loc[out["point_id"] == "p1"].iloc[0]

    assert row["sigma_total_fb"] == 40.0
    assert row["sigma_times_br_gaga_fb"] == 2.0
    assert row["ratio_to_observed_limit_context_only"] == 2.0
    assert row["ratio_to_expected_limit_context_only"] == 1.0
    assert row["ratio_observed_ge1_context_only"] == "TRUE_CONTEXT_ONLY"
    assert row["comparison_status"] == mod.COMPARISON_STATUS
    assert mod.NON_EXCLUSION_FLAG in row["quality_flags"]


def test_explicit_total_sigma_overrides_component_sum():
    sigma = pd.DataFrame(
        [
            {
                "point_id": "p1",
                "sigma_ggF_fb": 30.0,
                "sigma_VBF_fb": 10.0,
                "sigma_total_fb": 5.0,
            }
        ]
    )

    out = mod.build_sigma_applied(_priority(), _comparison(), sigma)
    row = out.loc[out["point_id"] == "p1"].iloc[0]

    assert row["sigma_total_fb"] == 5.0
    assert row["sigma_times_br_gaga_fb"] == 0.25
    assert row["ratio_observed_ge1_context_only"] == "FALSE_CONTEXT_ONLY"


def test_missing_sigma_keeps_waiting_status_and_no_ratio():
    out = mod.build_sigma_applied(_priority(), _comparison(), pd.DataFrame())
    row = out.loc[out["point_id"] == "p2"].iloc[0]

    assert row["sigma_status"] == mod.SIGMA_STATUS_MISSING
    assert row["comparison_status"] == "WAITING_FOR_SIGMA_OR_LIMIT_CONTEXT"
    assert pd.isna(row["ratio_to_observed_limit_context_only"])
    assert "PRODUCTION_XSEC_MISSING" in row["quality_flags"]


def test_duplicate_sigma_point_ids_are_rejected():
    sigma = pd.DataFrame([{"point_id": "p1", "sigma_total_fb": 1.0}, {"point_id": "p1", "sigma_total_fb": 2.0}])

    try:
        mod.build_sigma_applied(_priority(), _comparison(), sigma)
    except ValueError as exc:
        assert "duplicate point_id" in str(exc)
    else:
        raise AssertionError("duplicate sigma inputs should fail")
