"""Focused regression test for the PR #10 P2 finding: the full-sample Pythia
driver must reject incomplete LHE processing instead of reporting success for
a positive partial sample.

Builds artifacts/h2_first_physical/pythia_full/pythia_full_driver.cc against
a local Pythia 8.3 install and runs it against a deliberately truncated LHE
fixture. Skipped entirely when a compiler or Pythia8 install is unavailable,
since this repo does not otherwise depend on either for its Python test
suite.
"""

import json
import os
import shutil
import subprocess

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_SRC = os.path.join(
    REPO_ROOT, "artifacts", "h2_first_physical", "pythia_full", "pythia_full_driver.cc"
)
DECAY_SLHA = os.path.join(
    REPO_ROOT, "artifacts", "h2_first_physical", "pythia_full", "decay.slha"
)
POINT_JSON = os.path.join(
    REPO_ROOT, "artifacts", "h2_first_physical", "pythia_full", "point.json"
)
CANONICAL_LHE_GZ = os.path.join(
    REPO_ROOT,
    "artifacts",
    "h2_first_physical",
    "madgraph",
    "run_01",
    "unweighted_events.lhe.gz",
)

PYTHIA8_DIR = os.environ.get("PYTHIA8_DIR", os.path.expanduser("~/.local/pythia8308"))
GXX = shutil.which("g++")

pytestmark = pytest.mark.skipif(
    GXX is None or not os.path.isdir(os.path.join(PYTHIA8_DIR, "include", "Pythia8")),
    reason="requires g++ and a Pythia8 install (set PYTHIA8_DIR to override the default path)",
)


@pytest.fixture(scope="module")
def driver_binary(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("pythia_full_driver_build")
    binary = out_dir / "pythia_full_driver"
    subprocess.run(
        [
            GXX,
            "-std=c++17",
            "-O2",
            "-I", os.path.join(PYTHIA8_DIR, "include"),
            DRIVER_SRC,
            "-o", str(binary),
            "-L", os.path.join(PYTHIA8_DIR, "lib"),
            "-lpythia8",
            "-ldl",
            "-Wl,-rpath," + os.path.join(PYTHIA8_DIR, "lib"),
        ],
        check=True,
    )
    return binary


@pytest.fixture(scope="module")
def truncated_lhe(tmp_path_factory):
    """First 500 complete <event> blocks of the canonical run_01 LHE, closed
    with a valid </LesHouchesEvents> tag -- i.e. a well-formed file that
    genuinely contains fewer events than the canonical sample, not corrupted
    XML."""
    out_dir = tmp_path_factory.mktemp("truncated_lhe")
    full_path = out_dir / "full.lhe"
    subprocess.run(["gunzip", "-k", "-c", CANONICAL_LHE_GZ], stdout=open(full_path, "wb"), check=True)

    text = full_path.read_text()
    marker = "</event>"
    idx = -1
    for _ in range(500):
        idx = text.index(marker, idx + 1)
    cutoff = idx + len(marker)

    truncated_path = out_dir / "truncated_500.lhe"
    truncated_path.write_text(text[:cutoff] + "\n</LesHouchesEvents>\n")
    return truncated_path


def _run_driver(driver_binary, lhe_path, tmp_path, expected_events, seed=99001):
    metrics = tmp_path / "metrics.csv"
    summary = tmp_path / "summary.json"
    result = subprocess.run(
        [
            str(driver_binary),
            str(lhe_path),
            DECAY_SLHA,
            POINT_JSON,
            str(metrics),
            str(summary),
            str(seed),
            str(expected_events),
        ],
        capture_output=True,
        text=True,
    )
    return result, summary


def test_truncated_lhe_is_rejected_when_full_count_expected(driver_binary, truncated_lhe, tmp_path):
    """The exact bug from PR #10: a truncated LHE with a positive partial
    sample (all 500 available events have 4 b quarks each) must not be
    reported as success when 1000 events were expected."""
    result, summary = _run_driver(driver_binary, truncated_lhe, tmp_path, expected_events=1000)
    assert result.returncode == 4, result.stderr
    assert "truncated" in result.stderr.lower()
    assert not summary.exists() or json.loads(summary.read_text()).get("events", 0) < 1000


def test_truncated_lhe_is_accepted_when_matching_count_expected(driver_binary, truncated_lhe, tmp_path):
    """Positive control for the test above: the same file succeeds when the
    expected count actually matches what the file contains, proving the
    rejection above is driven by the count mismatch and not a hardcoded
    failure."""
    result, summary = _run_driver(driver_binary, truncated_lhe, tmp_path, expected_events=500)
    assert result.returncode == 0, result.stderr
    payload = json.loads(summary.read_text())
    assert payload["events"] == 500
    assert payload["llp_records"] == 1000
    assert payload["llp_decayed"] == 1000
    assert payload["b_quarks_from_h2"] == 2000
    assert payload["status"] == "PASS"


def test_canonical_lhe_matches_expected_count(driver_binary, tmp_path):
    """The canonical run_01 LHE (1000 events) must pass with expected=1000
    and produce the exact counts recorded in production_manifest.json."""
    full_lhe = tmp_path / "run_01.lhe"
    subprocess.run(["gunzip", "-k", "-c", CANONICAL_LHE_GZ], stdout=open(full_lhe, "wb"), check=True)
    result, summary = _run_driver(driver_binary, full_lhe, tmp_path, expected_events=1000)
    assert result.returncode == 0, result.stderr
    payload = json.loads(summary.read_text())
    assert payload["events"] == 1000
    assert payload["llp_records"] == 2000
    assert payload["llp_decayed"] == 2000
    assert payload["b_quarks_from_h2"] == 4000
    assert payload["tau0_configured_mm"] == pytest.approx(4.326221529733112, rel=1e-12)
