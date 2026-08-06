"""Tests for R12 MadGraph production helpers and driver."""

from __future__ import annotations

import json
import math
from pathlib import Path
import pytest

from llp_recast.r12_madgraph_production import (
    R12_G_TARGETS,
    R12_SEEDS,
    combine_inverse_variance,
    fmt_g_dir,
)


def test_r12_g_targets_and_seeds():
    assert len(R12_G_TARGETS) == 6
    assert len(R12_SEEDS) == 2
    assert R12_SEEDS == [101, 107]
    assert 40.0 in R12_G_TARGETS
    assert 63.59142520075966 in R12_G_TARGETS
    assert 100.0 in R12_G_TARGETS
    assert 150.0 in R12_G_TARGETS
    assert 205.09272542237372 in R12_G_TARGETS
    assert 300.0 in R12_G_TARGETS


def test_fmt_g_dir():
    assert fmt_g_dir(40.0) == "g40"
    assert fmt_g_dir(63.59142520075966) == "g63p591425"
    assert fmt_g_dir(100.0) == "g100"
    assert fmt_g_dir(150.0) == "g150"
    assert fmt_g_dir(205.09272542237372) == "g205p092725"
    assert fmt_g_dir(300.0) == "g300"


def test_combine_inverse_variance():
    s1, e1 = 0.00020, 0.00001
    s2, e2 = 0.00022, 0.00001
    s_comb, e_comb = combine_inverse_variance(s1, e1, s2, e2)

    assert pytest.approx(s_comb, rel=1e-5) == 0.00021
    expected_err = math.sqrt(1.0 / (1.0 / (0.00001**2) + 1.0 / (0.00001**2)))
    assert pytest.approx(e_comb, rel=1e-5) == expected_err
