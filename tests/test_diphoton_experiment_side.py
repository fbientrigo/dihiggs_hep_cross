import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "diphoton_meeting_package", Path(__file__).resolve().parents[1] / "scripts" / "08_diphoton_meeting_package.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_experiment_side_bands_and_range():
    df = mod.load_experiment_side()
    assert set(df["width_hypothesis"]) == {"NWA", "2pct", "6pct", "10pct"}
    nwa = df[df["width_hypothesis"] == "NWA"]
    assert nwa["mass_GeV"].min() == 160
    assert nwa["mass_GeV"].max() == 3000
    row = nwa[nwa["mass_GeV"] == 160].iloc[0]
    assert row["expected_minus_2sigma_fb"] < row["expected_minus_1sigma_fb"] < row["expected_limit_fb"]
    assert row["expected_limit_fb"] < row["expected_plus_1sigma_fb"] < row["expected_plus_2sigma_fb"]
