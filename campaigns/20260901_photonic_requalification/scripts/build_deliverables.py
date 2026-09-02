#!/usr/bin/env python3
"""Build the validated point set, the target comparison, and the corrected
photonic event-yield tables.

Selected route: THDM::set_param_phys_lam1 via the canonical
`dihiggs/app/Lambda1EvaluatorV2` binary (schema dihiggs.lambda1.v2).
See validated/REQUALIFICATION_SUMMARY.md for why.
"""
from __future__ import annotations

import csv
import math
import subprocess
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1]
EVAL = Path.home() / "atlas_dihiggs/dihiggs/dihiggs/app/Lambda1EvaluatorV2"

# ---- selected benchmark coordinates (Christopher's photonic family) ----------
MH_LIGHT = 125.0            # Christopher's convention; 125.20 reported as sensitivity
MA = MHP = 300.0
SBA = 1.0
TANB = 40000000.00000001
LAMBDA1 = 1.0               # input coordinate (NOT reconstructed)
LAMBDA6 = 0.0001177689207010651
LAMBDA7 = 0.0
MASSES = (200.0, 250.0, 300.0)

# ---- production normalisation (Christopher's LaTeX, immutable) ---------------
SIGMA_FB = {200.0: 23.51, 250.0: 13.35, 300.0: 7.530}
LUMI_IFB = 300.0

# ---- Z branching fractions, as used in Christopher's expanded table ----------
# Solved from his own published numbers by scripts/verify_chris_conventions.py:
# BR(Z->jj)=0.6991, BR(Z->ee)=0.03363, BR(Z->mumu)=0.03366  (PDG)
Z_BR = {"jj": 0.6991, "ee": 0.03363, "mumu": 0.03366}


def run_evaluator(mh: float, outdir: Path, tag: str) -> dict[float, dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    inp, out = outdir / f"in_{tag}.csv", outdir / f"out_{tag}.csv"
    with inp.open("w") as fh:
        fh.write("point_id,mh_gev,mH_gev,mA_gev,mHp_gev,sin_beta_minus_alpha,"
                 "tan_beta,lambda1_target,lambda6_input,lambda7_input\n")
        for m in MASSES:
            fh.write(f"photonic_{m:.0f},{mh!r},{m!r},{MA!r},{MHP!r},{SBA!r},"
                     f"{TANB!r},{LAMBDA1!r},{LAMBDA6!r},{LAMBDA7!r}\n")
    proc = subprocess.run([str(EVAL), str(inp), str(out)],
                          capture_output=True, text=True)
    (outdir / f"warnings_{tag}.txt").write_text(proc.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"Lambda1EvaluatorV2 failed: {proc.stderr}")
    rows = {}
    for r in csv.DictReader(out.open()):
        rows[float(r["mH_input_gev"])] = r
    return rows


def fmt_chris(v: float) -> str:
    """Reproduce Christopher's number-formatting rule.

    Checked by scripts/verify_chris_conventions.py: 27 of the 30 tab:A_fotonico
    entries reproduce exactly and 3 differ in the last digit only, because he
    rounded the BRs to 4 significant figures before multiplying."""
    if v >= 1000:
        return f"{v:.2e}".replace("e+0", "e+")
    if v >= 100:
        return f"{v:.0f}"
    if v >= 10:
        return f"{v:.2f}"
    if v >= 1:
        return f"{v:.3f}"
    return f"{v:.4f}"


def main() -> int:
    work = CAMPAIGN / "work/calculator_runs/selected"
    sel = run_evaluator(MH_LIGHT, work, "mh125p00")
    alt = run_evaluator(125.20, work, "mh125p20")

    targets = {float(t["m_phi_GeV"]): t
               for t in csv.DictReader((CAMPAIGN / "work/targets.csv").open())}

    validated = CAMPAIGN / "validated"
    validated.mkdir(exist_ok=True)

    # ------------------------------------------------------------------ 1 ----
    obs = [("br_gammagamma", "BR_gamma_gamma", "br_gammagamma"),
           ("br_Zgamma", "BR_Z_gamma", "br_Zgamma"),
           ("br_bb", "BR_bb", "br_bb"),
           ("br_gg", "BR_gg", "br_gg")]

    req_rows, cmp_rows = [], []
    for m in MASSES:
        s, t, a = sel[m], targets[m], alt[m]
        req_rows.append({
            "m_phi_GeV": f"{m:.0f}",
            "original_tan_beta": t["tan_beta"],
            "selected_tan_beta": repr(TANB),
            "original_lambda1": t["lambda1"],
            "selected_lambda1": repr(LAMBDA1),
            "original_lambda6": t["lambda6"],
            "selected_lambda6": repr(LAMBDA6),
            "lambda7": repr(LAMBDA7),
            "mA_GeV": repr(MA),
            "mHp_GeV": repr(MHP),
            "mh_GeV": repr(MH_LIGHT),
            "sin_beta_minus_alpha": repr(SBA),
            "construction_ok": s["construction_ok"],
            "positivity_ok": s["positivity_ok"],
            "unitarity_ok": s["unitarity_ok"],
            "perturbativity_ok": s["perturbativity_ok"],
            "stability_ok": s["stability_ok"],
            "theory_ok": s["theory_ok"],
            "width_ok": s["width_ok"],
            "original_m_phi_realized_GeV": t["mH_calclh_GeV"],
            "selected_m_phi_GeV": f"{m:.0f}",
            "original_mA_realized_GeV": t["mA_calclh_GeV"],
            "original_mHp_realized_GeV": t["mHp_calclh_GeV"],
            "original_total_width": t["total_width_GeV"],
            "selected_total_width": s["total_width_gev"],
            "original_ctau_mm": t["ctau_mm"],
            "selected_ctau_mm": s["ctau_mm"],
            "original_br_gammagamma": t["BR_gamma_gamma"],
            "selected_br_gammagamma": s["br_gammagamma"],
            "original_br_Zgamma": t["BR_Z_gamma"],
            "selected_br_Zgamma": s["br_Zgamma"],
            "original_br_bb": t["BR_bb"],
            "selected_br_bb": s["br_bb"],
            "original_br_gg": t["BR_gg"],
            "selected_br_gg": s["br_gg"],
            "selection_class": "B_near_identical_physical_replacement",
            "selection_caveat": (
                "ctau moves +15.0% vs original (727->835 mm); for an LLP "
                "acceptance study this is the physically consequential change"
                if m == 200.0 else "ctau within 3.3% of original"),
            "absolute_yield_caveat":
                "event yields built from this point inherit an UNRESOLVED "
                "production-coupling mismatch; relative yields within one mass "
                "column are unaffected. See REQUALIFICATION_SUMMARY.md section 5.",
            "calculator_route": "THDM::set_param_phys_lam1 (Lambda1EvaluatorV2, dihiggs.lambda1.v2)",
            "lambda1_reconstructed": s["lambda1_reconstructed"],
            "lambda1_abs_residual": s["lambda1_abs_residual"],
            "lambda1_residual_warning": s["lambda1_residual_warning"],
            "lambda2_reconstructed": s["lambda2_reconstructed"],
            "lambda3_reconstructed": s["lambda3_reconstructed"],
            "lambda4_reconstructed": s["lambda4_reconstructed"],
            "lambda5_reconstructed": s["lambda5_reconstructed"],
            "m12_sq_reconstructed_gev2": s["m12_sq_reconstructed_gev2"],
            "tan_beta_reconstructed": s["tan_beta_reconstructed"],
            "width_unaccounted_gev": s["width_unaccounted_gev"],
            "sensitivity_mh12520_ctau_mm": a["ctau_mm"],
            "sensitivity_mh12520_br_gammagamma": a["br_gammagamma"],
            "notes": ("original point is theory-valid but its realised spectrum is "
                      "mislabelled: CalcGen->LesHouches->CalcLH shifts m_phi by "
                      "+4.8..+7.2 GeV (tan(beta)=4e7 conditioning, see "
                      "logs/tanb_conditioning_diagnosis.txt). Replacement fixes "
                      "m_phi and mA=mHp to their nominal values via the "
                      "physical-basis lambda1 route; no other coordinate moved."),
        })

        # ------------------------------------------------------------- 2 ----
        for sel_key, tgt_key, _ in obs:
            tv, sv = float(t[tgt_key]), float(s[sel_key])
            cmp_rows.append({
                "m_phi_GeV": f"{m:.0f}", "observable": tgt_key,
                "target": repr(tv), "validated": repr(sv),
                "delta": repr(sv - tv),
                "relative_delta": repr((sv - tv) / tv),
                "log10_ratio": repr(math.log10(sv / tv)),
            })
        for label, tgt_key, sel_key in (("total_width_GeV", "total_width_GeV", "total_width_gev"),
                                        ("ctau_mm", "ctau_mm", "ctau_mm")):
            tv, sv = float(t[tgt_key]), float(s[sel_key])
            cmp_rows.append({
                "m_phi_GeV": f"{m:.0f}", "observable": label,
                "target": repr(tv), "validated": repr(sv),
                "delta": repr(sv - tv),
                "relative_delta": repr((sv - tv) / tv),
                "log10_ratio": repr(math.log10(sv / tv)),
            })
        for label, tgt_key, sv in (("m_phi_GeV", "mH_calclh_GeV", m),
                                   ("mA_GeV", "mA_calclh_GeV", MA)):
            tv = float(t[tgt_key])
            cmp_rows.append({
                "m_phi_GeV": f"{m:.0f}", "observable": label,
                "target": repr(tv), "validated": repr(float(sv)),
                "delta": repr(sv - tv), "relative_delta": repr((sv - tv) / tv),
                "log10_ratio": repr(math.log10(sv / tv)),
            })

    _write(validated / "photonic_requalified.csv", req_rows)
    _write(validated / "comparison_target_vs_validated.csv", cmp_rows)

    # ------------------------------------------------------------------ 3 ----
    prov = [{"m_phi_GeV": f"{m:.0f}", "sigma_LO_fb": repr(SIGMA_FB[m]),
             "sqrt_s_TeV": "13", "luminosity_fb-1": repr(LUMI_IFB),
             "N_phiphi": repr(round(LUMI_IFB * SIGMA_FB[m], 6)),
             "source": "inputs/chris_original/chris_event_yields.tex, Table tab:xsec",
             "production_prescription":
                 "Christopher's original simplified UFO; gg -> h2 h2, LO. "
                 "UFO vertex GC_90 = 8i*Mh2^2/vev (verified in "
                 "dihiggs_ufo/LLscalar_v3_UFO_original/couplings.py:372). "
                 "NOTE: 'EF_simple' is workspace jargon and does NOT appear in "
                 "the source LaTeX.",
             "integration_uncertainty_fb": "",
             "sigma_provenance": "transcribed verbatim from tab:xsec",
             "N_phiphi_provenance":
                 "DERIVED here as L*sigma (7053.0/4005.0/2259.0); Christopher's "
                 "tab:xsec prints the rounded 7.05e+3/4.01e+3/2.26e+3",
             "production_coupling_caveat":
                 "UNRESOLVED: this sigma uses g_hphiphi = 8*m_phi^2/v = "
                 "1299.6/2030.7/2924.2 GeV, but the requalified decay point has "
                 "M^2 = m_phi^2, giving 2HDMC g_hphiphi = m_h^2/v = 63.46 GeV at "
                 "all three masses. See REQUALIFICATION_SUMMARY.md section 5.",
             "provenance_note":
                 "NOT raw MadGraph output: no banner, seed, or run directory is "
                 "available in this workspace. MC integration uncertainty is not "
                 "quoted in the source and is deliberately left blank, not inferred."}
            for m in MASSES]
    _write(CAMPAIGN / "inputs/production_reference/christopher_xsec_from_latex.csv", prov)

    # ------------------------------------------------------------------ 4 ----
    direct = ("bb", "gg", "Zga", "gaga")
    disp = {"bb": r"$b\bar b$", "gg": r"$gg$", "Zga": r"$Z\gamma$",
            "gaga": r"$\gamma\gamma$", "jjga": r"$jj\gamma$",
            "eega": r"$e^+e^-\gamma$", "mumuga": r"$\mu^+\mu^-\gamma$"}

    def brs(m):
        s = sel[m]
        return {"bb": float(s["br_bb"]), "gg": float(s["br_gg"]),
                "Zga": float(s["br_Zgamma"]), "gaga": float(s["br_gammagamma"])}

    def expanded(m):
        b = brs(m)
        return {"bb": b["bb"], "gg": b["gg"], "gaga": b["gaga"],
                "jjga": b["Zga"] * Z_BR["jj"], "eega": b["Zga"] * Z_BR["ee"],
                "mumuga": b["Zga"] * Z_BR["mumu"]}

    def yields(bmap, order, m):
        n = LUMI_IFB * SIGMA_FB[m]
        out = {}
        for i, a in enumerate(order):
            for bch in order[i:]:
                out[(a, bch)] = n * (bmap[a] ** 2 if a == bch
                                     else 2 * bmap[a] * bmap[bch])
        return out

    yield_rows = []
    tabA, tabB = {}, {}
    for m in MASSES:
        tabA[m] = yields(brs(m), direct, m)
        tabB[m] = yields(expanded(m), ("bb", "gg", "jjga", "eega", "mumuga", "gaga"), m)
    for table, data in (("A_direct", tabA), ("B_expanded", tabB)):
        for pair in data[MASSES[0]]:
            row = {"table": table, "channel_a": pair[0], "channel_b": pair[1],
                   "absolute_scale_status": "CONDITIONAL_unresolved_production_coupling"}
            for m in MASSES:
                row[f"N_events_{m:.0f}GeV"] = repr(data[m][pair])
            yield_rows.append(row)
    _write(CAMPAIGN / "event_yields/event_yields_photonic_requalified.csv", yield_rows)

    # ------------------------------------------------------------------ 5 ----
    def latex_table(data, order, label, caption, size=r"\small"):
        L = [r"\begin{table}[H]", r"\centering", size,
             f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             r"\begin{adjustbox}{max width=\textwidth}",
             r"\begin{tabular}{lrrr}", r"\toprule",
             r"Canal & 200 GeV & 250 GeV & 300 GeV \\", r"\midrule"]
        for i, a in enumerate(order):
            for bch in order[i:]:
                cells = " & ".join(fmt_chris(data[m][(a, bch)]) for m in MASSES)
                L.append(f"({disp[a]})({disp[bch]}) & {cells} \\\\")
        L += [r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}",
              r"\end{table}"]
        return "\n".join(L)

    tex = [
        "% Regenerated photonic event-yield tables (requalified benchmark points).",
        "% Produced by campaigns/20260901_photonic_requalification/scripts/build_deliverables.py",
        "% Point route: THDM::set_param_phys_lam1 via dihiggs/app/Lambda1EvaluatorV2.",
        "% sigma_LO from chris_event_yields.tex Table tab:xsec (unchanged); L = 300 fb^-1.",
        "% Mixed-benchmark tables are NOT regenerated and are unchanged.",
        "%",
        "% ==================== READ BEFORE USING THESE NUMBERS ====================",
        "% The ABSOLUTE scale of every entry is CONDITIONAL and unresolved.",
        "% sigma_LO was produced with the simplified-UFO vertex GC_90 = 8*m_phi^2/v",
        "%   = 1299.6 / 2030.7 / 2924.2 GeV for m_phi = 200 / 250 / 300 GeV,",
        "% whereas the requalified decay point (soft scale M^2 = m_phi^2) has",
        "%   2HDMC g_hphiphi = m_h^2/v = 63.46 GeV, the SAME at all three masses.",
        "% If sigma ~ g^2 for the single s-channel h* diagram, these tables",
        "% overstate absolute yields by roughly 4.2e2 / 1.0e3 / 2.1e3, and the",
        "% relative ordering BETWEEN mass columns is wrong as well.",
        "% RELATIVE yields WITHIN one mass column are unaffected and are usable.",
        "% Resolving this is the next campaign (physical_2HDM vs EF_simple vs EF_m2);",
        "% it was explicitly out of scope here, so sigma_LO was reused unchanged.",
        "% =========================================================================",
        "",
        latex_table(tabA, direct, "tab:A_fotonico_requal",
                    "Tabla A directa, caso fot\\'onico \\textbf{requalificado}: eventos "
                    "esperados truth-level para $L=300~\\mathrm{fb}^{-1}$."),
        "",
        latex_table(tabB, ("bb", "gg", "jjga", "eega", "mumuga", "gaga"),
                    "tab:B_fotonico_requal",
                    "Tabla B expandida, caso fot\\'onico \\textbf{requalificado}: eventos "
                    "esperados truth-level con $Z\\to jj,e^+e^-,\\mu^+\\mu^-$.",
                    size=r"\scriptsize"),
        "",
    ]
    (CAMPAIGN / "event_yields/photonic_tables_requalified.tex").write_text("\n".join(tex))

    print("selected points (mh = 125.0, lambda1 = 1, mA = mHp = 300, tanb = 4e7):")
    for m in MASSES:
        s = sel[m]
        print(f"  m_phi={m:.0f}  theory_ok={s['theory_ok']} width_ok={s['width_ok']}  "
              f"ctau={float(s['ctau_mm']):.3f} mm  BRgaga={float(s['br_gammagamma']):.6f}  "
              f"BRZga={float(s['br_Zgamma']):.6f}")
    print("\nwrote validated/, event_yields/, inputs/production_reference/")
    return 0


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path.relative_to(CAMPAIGN)} ({len(rows)} rows)")


if __name__ == "__main__":
    raise SystemExit(main())
