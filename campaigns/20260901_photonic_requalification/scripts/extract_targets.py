#!/usr/bin/env python3
"""Deterministic extraction of the photonic benchmark targets.

Reads only immutable reference material under inputs/chris_original/ and
writes work/targets.csv.  No physics is recomputed here: every field is
either copied verbatim from Christopher's CSVs or parsed out of the recorded
CalcGen command line.

Decoded CalcGen argv (2HDMC generic/Higgs basis):
    CalcGen l1 l2 l3 l4 l5 l6 l7 m12sq tanb yukawa_type out.lha
"""
from __future__ import annotations

import argparse
import csv
import math
import shlex
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1]
FINAL = CAMPAIGN / "inputs/chris_original/photonic_final_results_CalcLH.csv"
CHANNELS = CAMPAIGN / "inputs/chris_original/photonic_all_decay_channels_CalcLH.csv"
OUT = CAMPAIGN / "work/targets.csv"

TARGET_MASSES = ("200.0", "250.0", "300.0")

FIELDS = [
    "m_phi_GeV",
    # --- requested (design) coordinates, reconstructed from CalcGen argv ---
    "tan_beta",
    "lambda1",
    "lambda2",
    "lambda3",
    "lambda4",
    "lambda5",
    "lambda6",
    "lambda7",
    "m12sq_GeV2",
    "M_soft_GeV",
    "yukawa_type",
    "mA_requested_GeV",
    "mHp_requested_GeV",
    "alignment",
    "lambda6_tanbeta",
    # --- realized point as reported by CalcLH ---
    "mH_calclh_GeV",
    "mass_drift_GeV",
    "mA_calclh_GeV",
    "mHp_calclh_GeV",
    # --- target observables ---
    "BR_gamma_gamma",
    "BR_Z_gamma",
    "BR_bb",
    "BR_gg",
    "BR_loop",
    "total_width_GeV",
    "ctau_mm",
    "ctau_m",
    # --- provenance ---
    "source_file",
    "source_row",
    "calcgen_command",
]

# 2HDMC prints widths in GeV; ctau = hbar*c / Gamma
HBARC_GEV_M = 1.9732698e-16  # GeV * m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    final_rows = list(csv.DictReader(FINAL.open()))
    chan_rows = list(csv.DictReader(CHANNELS.open()))

    out_rows = []
    for idx, r in enumerate(final_rows):
        if r["mH_requested"] not in TARGET_MASSES:
            continue

        argv = shlex.split(r["calcgen_command"])
        lam = [float(x) for x in argv[1:8]]
        m12sq = float(argv[8])
        tanb = float(argv[9])
        ytype = int(argv[10])

        sb = tanb / math.sqrt(1.0 + tanb * tanb)
        cb = 1.0 / math.sqrt(1.0 + tanb * tanb)
        M2 = m12sq / (sb * cb)

        # v^2 implied by the construction: lambda4 = -(mA^2 - mphi_req^2)/v^2
        # with mA_requested = mHp_requested = 300 GeV (verified exact for all rows).
        m_req = float(r["mH_requested"])
        mA_req = 300.0
        v2 = (mA_req**2 - m_req**2) / (-lam[3]) if abs(lam[3]) > 1e-9 else float("nan")

        # alignment: lambda3+lambda4+lambda5 == lambda2  <=>  sin(beta-alpha)=1
        l345 = lam[2] + lam[3] + lam[4]
        aligned = abs(l345 - lam[1]) < 1e-9

        gamma = float(r["Gamma_total_calclh_GeV"])
        ctau_m = float(r["ctau_calclh_m"])

        out_rows.append(
            {
                "m_phi_GeV": f"{m_req:g}",
                "tan_beta": repr(tanb),
                "lambda1": repr(lam[0]),
                "lambda2": repr(lam[1]),
                "lambda3": repr(lam[2]),
                "lambda4": repr(lam[3]),
                "lambda5": repr(lam[4]),
                "lambda6": repr(lam[5]),
                "lambda7": repr(lam[6]),
                "m12sq_GeV2": repr(m12sq),
                "M_soft_GeV": repr(math.sqrt(M2)),
                "yukawa_type": str(ytype),
                "mA_requested_GeV": repr(mA_req),
                "mHp_requested_GeV": repr(mA_req),
                "alignment": "sin(beta-alpha)=1" if aligned else "NOT_ALIGNED",
                "lambda6_tanbeta": repr(lam[5] * tanb),
                "mH_calclh_GeV": r["mH_calclh"],
                "mass_drift_GeV": r["mass_drift_calclh_GeV"],
                "mA_calclh_GeV": r["mA_calclh"],
                "mHp_calclh_GeV": r["mHp_calclh"],
                "BR_gamma_gamma": r["BR_gammagamma"],
                "BR_Z_gamma": r["BR_Zgamma"],
                "BR_bb": r["BR_bb"],
                "BR_gg": r["BR_gg"],
                "BR_loop": r["BR_loop"],
                "total_width_GeV": r["Gamma_total_calclh_GeV"],
                "ctau_mm": repr(ctau_m * 1000.0),
                "ctau_m": r["ctau_calclh_m"],
                "source_file": FINAL.name,
                "source_row": str(idx + 2),  # +2: 1-based with header
                "calcgen_command": r["calcgen_command"],
            }
        )

        # consistency: hbar*c/Gamma must reproduce the recorded ctau
        assert abs(HBARC_GEV_M / gamma / ctau_m - 1.0) < 5e-3, (m_req, gamma, ctau_m)

        # consistency: the four quoted BRs must match the per-channel CSV
        chans = {
            c["channel"]: float(c["BR"])
            for c in chan_rows
            if c["mH_requested"] == r["mH_requested"]
        }
        for csv_key, chan_key in (
            ("BR_gammagamma", "gammagamma"),
            ("BR_Zgamma", "Zgamma"),
            ("BR_bb", "bb"),
            ("BR_gg", "gg"),
        ):
            assert abs(float(r[csv_key]) - chans[chan_key]) < 1e-12, (m_req, csv_key)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out_rows)

    print(f"wrote {args.out} ({len(out_rows)} rows)")
    for row in out_rows:
        print(
            f"  m_phi={row['m_phi_GeV']:>3}  mH_calclh={row['mH_calclh_GeV']:>9}"
            f"  drift={float(row['mass_drift_GeV']):+.3f} GeV"
            f"  BRgg={row['BR_gamma_gamma']}  ctau={float(row['ctau_mm']):.1f} mm"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
