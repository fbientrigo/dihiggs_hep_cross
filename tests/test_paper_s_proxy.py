import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_COLUMNS = {
    "mS_GeV",
    "ctau_mm",
    "tau_ns",
    "beta_gamma_assumed",
    "sigma_fb_assumed",
    "BR_hadronic_proxy",
    "P_single_ID_4_300",
    "P_event_at_least_one_ID",
    "eff_event_proxy",
    "eff_vertex_proxy",
    "aeff_proxy",
    "Nsig_139fb",
    "nearest_public_limit_fb",
    "ratio_to_limit_proxy",
    "quality_flag",
    "missing_inputs",
}


def _run(cmd: list[str], cwd: Path) -> None:
    env = dict(os.environ, PYTHONPATH="src")
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_paper_proxy_output_has_required_columns_and_is_not_exclusion_grade(tmp_path):
    tidy_dir = tmp_path / "hepdata_tidy"
    proxy_dir = tmp_path / "paper_s_proxy"

    _run(
        [sys.executable, "scripts/02_hepdata_tidy_extract.py", "--outdir", str(tidy_dir)],
        cwd=REPO_ROOT,
    )
    _run(
        [
            sys.executable,
            "scripts/03_paper_s_benchmark_proxy.py",
            "--tidy-dir",
            str(tidy_dir),
            "--outdir",
            str(proxy_dir),
        ],
        cwd=REPO_ROOT,
    )

    csv_path = proxy_dir / "paper_s_benchmark_proxy.csv"
    md_path = proxy_dir / "paper_s_benchmark_proxy.md"
    assert csv_path.exists()
    assert md_path.exists()

    df = pd.read_csv(csv_path)
    assert REQUIRED_COLUMNS.issubset(df.columns)
    assert len(df) == 3 * 7  # 3 benchmark masses x 7 ctau grid points
    assert (df["quality_flag"].str.contains("PAPER_AWARE_PROXY_NOT_EXCLUSION")).all()
    assert (df["P_single_ID_4_300"].between(0.0, 1.0)).all()

    md_text = md_path.read_text(encoding="utf-8")
    assert "not a reproduction" in md_text.lower()
    assert "not an atlas exclusion" in md_text.lower()
