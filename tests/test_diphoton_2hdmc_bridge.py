import importlib.util
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "09_link_2hdmc_to_diphoton.py"

spec = importlib.util.spec_from_file_location("diphoton_2hdmc_bridge", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _write_csv(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_inventory_records_required_and_missing_columns(tmp_path):
    complete = _write_csv(
        tmp_path / "complete.csv",
        [
            {
                "point_id": "p1",
                "m_phi": 500,
                "total_width": 5,
                "br_gaga": 0.01,
                "tanbeta": 2,
                "positivity_ok": 1,
                "unitarity_ok": 1,
                "perturbativity_ok": 1,
            }
        ],
    )
    missing = _write_csv(
        tmp_path / "missing.csv",
        [
            {
                "m_phi": 600,
                "total_width": 12,
                "positivity_ok": 1,
                "unitarity_ok": 0,
                "perturbativity_ok": 1,
            }
        ],
    )

    inventory = mod.build_scan_inventory([complete, missing]).sort_values("source_path").reset_index(drop=True)

    assert list(inventory.columns) == mod.INVENTORY_COLUMNS
    assert bool(inventory.loc[0, "accepted_as_2hdmc_scan"]) is True
    assert bool(inventory.loc[0, "has_required_columns"]) is True
    assert inventory.loc[0, "n_physical_rows"] == 1
    assert inventory.loc[0, "m_min"] == 500
    assert inventory.loc[0, "m_max"] == 500
    assert inventory.loc[0, "tanbeta_values"] == "2"
    assert bool(inventory.loc[1, "accepted_as_2hdmc_scan"]) is False
    assert inventory.loc[1, "rejection_reason"] == "MISSING_REQUIRED_COLUMNS"
    assert bool(inventory.loc[1, "has_required_columns"]) is False
    assert "br_gaga" in inventory.loc[1, "missing_columns"]


def test_cli_accepts_multiple_scan_roots(monkeypatch, tmp_path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    monkeypatch.setattr(sys, "argv", ["bridge", "--scan-root", str(root_a), "--scan-root", str(root_b)])

    args = mod.parse_args()

    assert args.scan_root == [root_a, root_b]


def test_discovery_accepts_fake_csv_with_required_columns(tmp_path):
    scan = _write_csv(
        tmp_path / "scan_tb_fake.csv",
        [
            {
                "m_phi": 500,
                "total_width": 5,
                "br_gaga": 0.01,
                "positivity_ok": 1,
                "unitarity_ok": 1,
                "perturbativity_ok": 1,
            }
        ],
    )

    candidates = mod.discover_scan_files([tmp_path])
    inventory = mod.build_scan_inventory(candidates)

    assert candidates == [scan]
    assert bool(inventory.loc[0, "accepted_as_2hdmc_scan"]) is True


def test_discovery_rejects_csv_missing_br_gaga_with_clear_reason(tmp_path):
    scan = _write_csv(
        tmp_path / "scan_tb_missing.csv",
        [
            {
                "m_phi": 500,
                "total_width": 5,
                "positivity_ok": 1,
                "unitarity_ok": 1,
                "perturbativity_ok": 1,
            }
        ],
    )

    inventory = mod.build_scan_inventory(mod.discover_scan_files([tmp_path]))

    assert inventory.loc[0, "source_path"] == str(scan)
    assert bool(inventory.loc[0, "accepted_as_2hdmc_scan"]) is False
    assert inventory.loc[0, "rejection_reason"] == "MISSING_REQUIRED_COLUMNS"
    assert inventory.loc[0, "missing_columns"] == "br_gaga"


def test_parquet_is_read_or_reported_when_engine_missing(tmp_path):
    parquet = tmp_path / "scan_fake.parquet"
    rows = pd.DataFrame(
        [
            {
                "m_phi": 500,
                "total_width": 5,
                "br_gaga": 0.01,
                "positivity_ok": 1,
                "unitarity_ok": 1,
                "perturbativity_ok": 1,
            }
        ]
    )
    try:
        rows.to_parquet(parquet)
    except Exception:
        parquet.write_bytes(b"not a parquet file")

    inventory = mod.build_scan_inventory(mod.discover_scan_files([tmp_path]))

    if bool(inventory.loc[0, "accepted_as_2hdmc_scan"]):
        assert inventory.loc[0, "file_type"] == "parquet"
        assert inventory.loc[0, "n_rows"] == 1
    else:
        assert inventory.loc[0, "rejection_reason"] == "PARQUET_ENGINE_MISSING"


def test_zero_accepted_files_writes_schema_outputs_and_discovery_report(tmp_path):
    outdir = tmp_path / "bridge"
    root = tmp_path / "scans"
    root.mkdir()
    _write_csv(root / "scan_tb_bad.csv", [{"m_phi": 500, "total_width": 5}])

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--outdir",
            str(outdir),
            "--scan-root",
            str(root),
            "--write-discovery-report",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert list(pd.read_csv(outdir / "theory_side_from_2hdmc.csv").columns) == mod.THEORY_COLUMNS
    assert list(pd.read_csv(outdir / "priority_points_for_sigma.csv").columns) == mod.PRIORITY_COLUMNS
    assert list(pd.read_csv(outdir / "diphoton_comparison_needs_xsec.csv").columns) == mod.COMPARISON_COLUMNS
    report = (outdir / "discovery_report.md").read_text(encoding="utf-8")
    assert "scan_tb_bad.csv" in report
    assert "MISSING_REQUIRED_COLUMNS" in report


def test_physical_filter_requires_all_three_flags():
    df = pd.DataFrame(
        [
            {"point_id": "keep", "positivity_ok": 1, "unitarity_ok": 1, "perturbativity_ok": 1},
            {"point_id": "drop_pos", "positivity_ok": 0, "unitarity_ok": 1, "perturbativity_ok": 1},
            {"point_id": "drop_uni", "positivity_ok": 1, "unitarity_ok": 0, "perturbativity_ok": 1},
            {"point_id": "drop_per", "positivity_ok": 1, "unitarity_ok": 1, "perturbativity_ok": 0},
        ]
    )

    physical = mod.filter_physical(df)

    assert physical["point_id"].tolist() == ["keep"]


def test_theory_side_rows_are_physical_and_non_exclusionary():
    df = pd.DataFrame(
        [
            {
                "point_id": "physical",
                "m_phi": 500,
                "total_width": 10,
                "br_gaga": 0.02,
                "positivity_ok": 1,
                "unitarity_ok": 1,
                "perturbativity_ok": 1,
            },
            {
                "point_id": "not_physical",
                "m_phi": 600,
                "total_width": 12,
                "br_gaga": 0.05,
                "positivity_ok": 1,
                "unitarity_ok": 0,
                "perturbativity_ok": 1,
            },
        ]
    )

    theory = mod.theory_side_from_scan_frame(df, Path("scan.csv"))

    assert theory["point_id"].tolist() == ["physical"]
    assert set(theory["theory_status"]) == {mod.THEORY_STATUS}
    assert set(theory["xsec_status"]) == {mod.XSEC_STATUS}
    assert set(theory["exclusion_status"]) == {mod.EXCLUSION_STATUS}
    assert theory.loc[0, "Gamma_over_m"] == 0.02


def test_priority_selection_is_capped_deterministic_and_favors_high_br_in_range():
    theory = pd.DataFrame(
        [
            {
                "source_csv": "scan.csv",
                "source_row": 0,
                "point_id": "low_br_in_range",
                "m_phi": 500,
                "m_H_GeV": 500,
                "total_width": 10,
                "Gamma_H_GeV": 10,
                "Gamma_over_m": 0.02,
                "br_gaga": 0.01,
                "tanbeta": pd.NA,
                "theory_status": mod.THEORY_STATUS,
                "xsec_status": mod.XSEC_STATUS,
                "exclusion_status": mod.EXCLUSION_STATUS,
            },
            {
                "source_csv": "scan.csv",
                "source_row": 1,
                "point_id": "high_br_in_range",
                "m_phi": 700,
                "m_H_GeV": 700,
                "total_width": 42,
                "Gamma_H_GeV": 42,
                "Gamma_over_m": 0.06,
                "br_gaga": 0.05,
                "tanbeta": pd.NA,
                "theory_status": mod.THEORY_STATUS,
                "xsec_status": mod.XSEC_STATUS,
                "exclusion_status": mod.EXCLUSION_STATUS,
            },
            {
                "source_csv": "scan.csv",
                "source_row": 2,
                "point_id": "higher_br_out_of_range",
                "m_phi": 3100,
                "m_H_GeV": 3100,
                "total_width": 62,
                "Gamma_H_GeV": 62,
                "Gamma_over_m": 0.02,
                "br_gaga": 0.9,
                "tanbeta": pd.NA,
                "theory_status": mod.THEORY_STATUS,
                "xsec_status": mod.XSEC_STATUS,
                "exclusion_status": mod.EXCLUSION_STATUS,
            },
        ]
    )

    first = mod.rank_priority_points(theory, max_points=2)
    second = mod.rank_priority_points(theory, max_points=2)

    assert first["point_id"].tolist() == ["high_br_in_range", "low_br_in_range"]
    assert first.equals(second)
    assert len(first) == 2
    assert first["priority_rank"].tolist() == [1, 2]


def test_default_search_roots_include_repo_local_drop_in_dir():
    assert Path("data/2hdmc_scans") in mod.DEFAULT_SEARCH_ROOTS
    assert not any("Asus" in str(root) or "dihiggs_lake" in str(root) for root in mod.DEFAULT_SEARCH_ROOTS)


def test_default_search_roots_dir_is_discovered(monkeypatch, tmp_path):
    drop_in = tmp_path / "data" / "2hdmc_scans"
    drop_in.mkdir(parents=True)
    scan = _write_csv(
        drop_in / "scan_tb_dropped.csv",
        [
            {
                "m_phi": 500,
                "total_width": 5,
                "br_gaga": 0.01,
                "positivity_ok": 1,
                "unitarity_ok": 1,
                "perturbativity_ok": 1,
            }
        ],
    )
    monkeypatch.setattr(mod, "DEFAULT_SEARCH_ROOTS", (drop_in, tmp_path / "outputs", tmp_path / "data"))

    candidates = mod.discover_scan_files(mod.default_search_roots())

    assert scan in candidates


def test_comparison_output_is_context_only_and_needs_sigma_x_br():
    priority = pd.DataFrame(
        [
            {
                "priority_rank": 1,
                "point_id": "p1",
                "source_csv": "scan.csv",
                "source_row": 0,
                "m_H_GeV": 505,
                "Gamma_H_GeV": 10,
                "Gamma_over_m": 0.02,
                "br_gaga": 0.02,
            }
        ]
    )
    experiment = pd.DataFrame(
        [
            {
                "mass_GeV": 500,
                "width_hypothesis": "2pct",
                "Gamma_over_m": 0.02,
                "observed_limit_fb": 1.5,
                "expected_limit_fb": 1.2,
                "expected_minus_1sigma_fb": 1.0,
                "expected_plus_1sigma_fb": 1.4,
                "expected_minus_2sigma_fb": 0.8,
                "expected_plus_2sigma_fb": 1.8,
                "fiducial_or_total": "fiducial",
                "spin_assumption": "spin-0",
                "source_table": "Limit1D_LW002_Scalar.yaml",
            },
            {
                "mass_GeV": 900,
                "width_hypothesis": "10pct",
                "Gamma_over_m": 0.10,
                "observed_limit_fb": 2.5,
                "expected_limit_fb": 2.2,
                "expected_minus_1sigma_fb": 2.0,
                "expected_plus_1sigma_fb": 2.4,
                "expected_minus_2sigma_fb": 1.8,
                "expected_plus_2sigma_fb": 2.8,
                "fiducial_or_total": "fiducial",
                "spin_assumption": "spin-0",
                "source_table": "Limit1D_LW01_Scalar.yaml",
            },
        ]
    )

    comparison = mod.build_comparison(priority, experiment)

    assert comparison.loc[0, "comparison_status"] == mod.COMPARISON_STATUS
    assert comparison.loc[0, "exclusion_status"] == mod.EXCLUSION_STATUS
    assert comparison.loc[0, "nearest_mass_GeV"] == 500
    assert comparison.loc[0, "nearest_width_hypothesis"] == "2pct"
    assert "ratio" not in " ".join(comparison.columns).lower()
