#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from llp_recast.constants import ATLAS_DVJETS_LUMI_FB, ID_R_MIN_MM, ID_R_MAX_MM
from llp_recast.recast_math import (
    ToyScalarPoint,
    ctau_mm_from_width_gev,
    decay_probability_between_radii,
    event_probability_at_least_one,
    expected_yield,
)


def parse_csv_floats(text: str) -> list[float]:
    return [float(x.strip()) for x in text.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Toy S->hadronic LLP recast proxy for ATLAS DV+jets")
    ap.add_argument("--masses", default="100,170,250", help="Comma-separated scalar masses in GeV")
    ap.add_argument("--ctau-mm", default="10,30,100,300,1000", help="Comma-separated proper c*tau values in mm")
    ap.add_argument("--beta-gamma", type=float, default=1.0)
    ap.add_argument("--xsec-fb", type=float, default=1.0, help="Toy production cross section in fb")
    ap.add_argument("--br-had", type=float, default=0.8, help="Toy hadronic BR per LLP")
    ap.add_argument("--eps-reco-proxy", type=float, default=0.10, help="Explicit placeholder for DV/event reconstruction efficiency")
    ap.add_argument("--out", default="outputs/toy_s_recast/toy_s_recast_summary.csv")
    args = ap.parse_args()

    masses = parse_csv_floats(args.masses)
    ctaus = parse_csv_floats(args.ctau_mm)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for m in masses:
        for ctau in ctaus:
            p = ToyScalarPoint(
                mass_gev=m,
                ctau_mm=ctau,
                beta_gamma=args.beta_gamma,
                xsec_fb=args.xsec_fb,
                br_had=args.br_had,
                eps_reco_proxy=args.eps_reco_proxy,
            )
            p_single_id = decay_probability_between_radii(p.lab_decay_length_mm, ID_R_MIN_MM, ID_R_MAX_MM)
            p_event_id = event_probability_at_least_one(p_single_id, n_llp=2)
            br_factor = p.br_had ** 2
            aeff_proxy = p_event_id * p.eps_reco_proxy
            nsig = expected_yield(ATLAS_DVJETS_LUMI_FB, p.xsec_fb, br_factor, aeff_proxy)
            rows.append({
                "mass_gev": m,
                "ctau_mm": ctau,
                "total_width_gev_from_ctau": p.total_width_gev,
                "beta_gamma": p.beta_gamma,
                "lab_decay_length_mm": p.lab_decay_length_mm,
                "xsec_fb_toy": p.xsec_fb,
                "br_had_per_llp": p.br_had,
                "br_factor_pair_had": br_factor,
                "p_single_decay_ID_4_300mm": p_single_id,
                "p_event_at_least_one_ID": p_event_id,
                "eps_reco_proxy_explicit_placeholder": p.eps_reco_proxy,
                "aeff_proxy": aeff_proxy,
                "nsig_139fb_proxy": nsig,
                "quality_flag": "GEOMETRY_PLUS_PLACEHOLDER_EFF_NOT_EXCLUSION",
            })

    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] wrote {out}")
    print("[NOTE] This is a proxy only. It is not an ATLAS exclusion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
