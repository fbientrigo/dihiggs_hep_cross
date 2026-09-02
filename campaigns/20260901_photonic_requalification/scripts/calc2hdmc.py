#!/usr/bin/env python3
"""Thin, reusable driver around the canonical 2HDMC binaries.

No 2HDMC physics is reimplemented here: this module only shells out to
  ~/atlas_dihiggs/dihiggs/2hdmc/CalcGen   (THDM::set_param_gen)
  ~/atlas_dihiggs/dihiggs/2hdmc/CalcLH    (Constraints + DecayTable)
and parses their stdout.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

DIHIGGS = Path.home() / "atlas_dihiggs/dihiggs"
CALCGEN = DIHIGGS / "2hdmc/CalcGen"
CALCLH = DIHIGGS / "2hdmc/CalcLH"
LAMBDA1_V2 = DIHIGGS / "dihiggs/app/Lambda1EvaluatorV2"

HBARC_GEV_MM = 1.973269804e-13  # GeV * mm  (matches Lambda1EvaluatorV2 kHbarCGeVmm)

_PHYS_KEYS = {
    "m_h": "mh", "m_H": "mH", "m_A": "mA", "m_H+": "mHp",
    "sin(b-a)": "sba", "lambda_6": "lambda6", "lambda_7": "lambda7",
    "m12^2": "m12sq", "tan(beta)": "tanb",
}


@dataclass
class GenPoint:
    """A 2HDM point in the generic (Lagrangian) basis -- the self-consistent
    definition: masses are *derived* by diagonalisation, never asserted."""
    lambda1: float
    lambda2: float
    lambda3: float
    lambda4: float
    lambda5: float
    lambda6: float
    lambda7: float
    m12sq: float
    tanb: float
    yukawa_type: int = 1

    def argv(self) -> list[str]:
        return [f"{v!r}" for v in (
            self.lambda1, self.lambda2, self.lambda3, self.lambda4,
            self.lambda5, self.lambda6, self.lambda7, self.m12sq, self.tanb,
        )] + [str(self.yukawa_type)]


@dataclass
class CalcResult:
    ok: bool
    phys: dict = field(default_factory=dict)
    constraints: dict = field(default_factory=dict)
    widths: dict = field(default_factory=dict)   # state -> {channel: GeV}
    brs: dict = field(default_factory=dict)      # state -> {channel: BR}
    total_width: dict = field(default_factory=dict)
    stdout: str = ""

    @property
    def mH(self) -> float:
        return self.phys["mH"]

    @property
    def gammaH(self) -> float:
        return self.total_width["H"]

    @property
    def ctau_mm(self) -> float:
        return HBARC_GEV_MM / self.gammaH

    def br(self, channel: str) -> float:
        return self.brs.get("H", {}).get(channel, 0.0)


def _parse_calclh(text: str) -> CalcResult:
    res = CalcResult(ok=True, stdout=text)

    sec = re.search(r"physical mass basis:\n(.*?)\n\n", text, re.S)
    if sec:
        for line in sec.group(1).splitlines():
            k, _, v = line.strip().partition(":")
            key = _PHYS_KEYS.get(k.strip())
            if key:
                res.phys[key] = float(v)

    for name, key in (("Tree-level unitarity", "unitarity_ok"),
                      ("Perturbativity", "perturbativity_ok"),
                      ("Stability", "stability_ok")):
        m = re.search(rf"{re.escape(name)}:\s*(\d)", text)
        if m:
            res.constraints[key] = int(m.group(1))

    for m in re.finditer(
        r"Decay table for (\S+)\s*\nTotal width:\s+(\S+) GeV\s+BR\n(.*?)\n-{5,}",
        text, re.S,
    ):
        state, tw, body = m.group(1), float(m.group(2)), m.group(3)
        res.total_width[state] = tw
        res.widths[state], res.brs[state] = {}, {}
        for line in body.splitlines():
            mm = re.match(r"\s*\S+\s+->\s+(.*?)\s{2,}(\S+)\s+(\S+)\s*$", line)
            if not mm:
                continue
            chan = "".join(mm.group(1).split())
            res.widths[state][chan] = float(mm.group(2))
            res.brs[state][chan] = float(mm.group(3))
    return res


# CalcLH prints e.g. "H  -> ga ga" / "H  -> Z  ga"; normalise to short names.
CHAN = {"gammagamma": "gaga", "Zgamma": "Zga", "bb": "bb", "gg": "gg", "hh": "hh"}


def evaluate(point: GenPoint, workdir: Path | None = None, tag: str = "pt") -> CalcResult:
    """Run CalcGen -> CalcLH on a generic-basis point and parse the result."""
    tmp = None
    if workdir is None:
        tmp = tempfile.TemporaryDirectory()
        workdir = Path(tmp.name)
    workdir.mkdir(parents=True, exist_ok=True)
    lha = workdir / f"{tag}.lha"
    out = workdir / f"{tag}_out.lha"

    gen = subprocess.run([str(CALCGEN), *point.argv(), str(lha)],
                         capture_output=True, text=True)
    if gen.returncode != 0 or not lha.exists():
        r = CalcResult(ok=False, stdout=gen.stdout + gen.stderr)
        if tmp:
            tmp.cleanup()
        return r

    lh = subprocess.run([str(CALCLH), str(lha), str(out)],
                        capture_output=True, text=True)
    res = _parse_calclh(lh.stdout + lh.stderr)
    res.ok = lh.returncode == 0 and "H" in res.total_width
    (workdir / f"{tag}_calclh.txt").write_text(lh.stdout + lh.stderr)
    if tmp:
        tmp.cleanup()
    return res
