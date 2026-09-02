#!/usr/bin/env python3
"""Why Christopher's photonic points are mislabelled: tan(beta)=4e7 conditioning.

Christopher's pipeline is CalcGen -> <file>.lha -> CalcLH.  CalcGen calls
THDM::set_param_gen with the exact double-precision generic-basis lambdas and
then writes a LesHouches file; CalcLH reads that file back and calls
set_param_gen again (read_LesHouches, generic branch) before building the
DecayTable.

At tan(beta) = 4e7 the CP-even/CP-odd spectrum is chaotically sensitive to
tan(beta) at the 1e-9 *relative* level, and the LesHouches file stores
tan(beta) with only 9 significant digits.  The round-trip therefore moves the
physical masses by several GeV, and the published BRs / ctau belong to the
shifted point rather than to the requested one.

This script demonstrates that, deterministically, with no fitting.
"""
from __future__ import annotations

import csv
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1]
CALCGEN = Path.home() / "atlas_dihiggs/dihiggs/2hdmc/CalcGen"
CALCLH = Path.home() / "atlas_dihiggs/dihiggs/2hdmc/CalcLH"


def _phys(text: str) -> dict:
    block = re.search(r"physical mass basis:\n(.*?)\n\n", text, re.S).group(1)
    out = {}
    for line in block.splitlines():
        key, _, val = line.strip().partition(":")
        out[key.strip()] = float(val)
    return out


def in_memory(argv10, workdir) -> dict:
    """Masses as set_param_gen computes them, before any file round-trip."""
    lha = Path(workdir) / "x.lha"
    r = subprocess.run([str(CALCGEN), *argv10, str(lha)], capture_output=True, text=True)
    return _phys(r.stdout)


def after_roundtrip(argv10, workdir) -> dict:
    """Masses CalcLH recovers after CalcGen's LesHouches file is read back."""
    lha = Path(workdir) / "y.lha"
    subprocess.run([str(CALCGEN), *argv10, str(lha)], capture_output=True, text=True)
    r = subprocess.run([str(CALCLH), str(lha), str(lha) + ".out"],
                       capture_output=True, text=True)
    return _phys(r.stdout)


def main() -> int:
    targets = list(csv.DictReader((CAMPAIGN / "work/targets.csv").open()))
    tmp = tempfile.mkdtemp()

    print("=" * 78)
    print("A. In-memory spectrum vs spectrum after the LesHouches round-trip")
    print("=" * 78)
    print(f"{'label':>6} {'in-mem mphi':>12} {'rt mphi':>10} {'d_mphi':>8} "
          f"{'in-mem mA':>10} {'rt mA':>9} {'d_mA':>8}")
    for t in targets:
        argv = shlex.split(t["calcgen_command"])[1:11]
        a, b = in_memory(argv, tmp), after_roundtrip(argv, tmp)
        print(f"{t['m_phi_GeV']:>6} {a['m_H']:12.5f} {b['m_H']:10.5f} "
              f"{b['m_H'] - a['m_H']:+8.3f} {a['m_A']:10.5f} {b['m_A']:9.5f} "
              f"{b['m_A'] - a['m_A']:+8.3f}")

    print()
    print("=" * 78)
    print("B. Root cause: tan(beta) is written to the .lha with 9 significant")
    print("   digits.  Perturbing tan(beta) alone, in memory, reproduces the shift.")
    print("=" * 78)
    argv = shlex.split(targets[0]["calcgen_command"])[1:11]
    rt = after_roundtrip(argv, tmp)
    print(f"m_phi label 200; CalcLH after round-trip reports m_phi = {rt['m_H']:.5f}")
    print(f"{'tan(beta) passed to set_param_gen':>36} {'m_phi':>12} {'mA':>12}")
    for tb in ("40000000.0", "40000000.1", "40000000.14513", "40000000.2",
               "40000001.0", "40000000.05"):
        a = list(argv)
        a[8] = tb
        p = in_memory(a, tmp)
        print(f"{tb:>36} {p['m_H']:12.5f} {p['m_A']:12.5f}")
    print()
    print("A 0.1 absolute (2.5e-9 relative) change in tan(beta) moves m_phi by")
    print("~7 GeV, and the response is not monotonic.  At tan(beta)=4e7 the")
    print("generic-basis spectrum is not a numerically stable function of its")
    print("inputs, so m_phi must be an INPUT (physical-basis route), never an")
    print("output of set_param_gen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
