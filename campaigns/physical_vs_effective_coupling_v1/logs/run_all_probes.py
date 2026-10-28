#!/usr/bin/env python3
"""Driver for physical_vs_effective_coupling_v1 numeric deliverables.
Calls the compiled GeneralProbe binary (dihiggs/2hdmc/GeneralProbe; build: make -C dihiggs/2hdmc GeneralProbe) only.
Writes: validation/numerical_crosschecks.csv, m2_study/m2_variation.csv,
m2_study/sensitivity_probes.csv, coupling_comparison/coupling_table.csv.
"""
import csv
import math
import subprocess
from pathlib import Path

CAMP = Path(__file__).resolve().parents[1]
PROBE = CAMP.parents[2] / "dihiggs" / "2hdmc" / "GeneralProbe"  # 2hdmc_build/ retired (DATA_FLOW N2; lake 20261013T001001Z-a347d8)

HEADER = subprocess.run([str(PROBE), "--header"], capture_output=True, text=True, check=True).stdout.strip().split(",")


def run(mode, args):
    argv = [str(PROBE), mode] + [f"{a:.17g}" for a in args] + []
    out = subprocess.run(argv, capture_output=True, text=True)
    line = [l for l in out.stdout.strip().split("\n") if l.startswith("phys,") or l.startswith("lam1,")]
    if not line:
        raise RuntimeError(f"no CSV row from {argv}: stdout={out.stdout!r} stderr={out.stderr!r}")
    vals = line[-1].split(",")
    row = dict(zip(HEADER, vals))
    return row


def run_phys(mh, mphi, mA, mHp, sba, lambda6, lambda7, m12_2, tanb, yukawa=1):
    return run("phys", [mh, mphi, mA, mHp, sba, lambda6, lambda7, m12_2, tanb, yukawa])


def run_lam1(mh, mphi, mA, mHp, sba, lambda1, lambda6, lambda7, tanb, yukawa=1):
    return run("lam1", [mh, mphi, mA, mHp, sba, lambda1, lambda6, lambda7, tanb, yukawa])


def as_float(row, key):
    try:
        return float(row[key])
    except Exception:
        return math.nan


def theory_ok(row):
    return all(row[k] == "1" for k in ("construction_ok", "unitarity_ok", "perturbativity_ok", "positivity_ok"))


V_DEFAULT = 246.21965079  # overwritten from actual probe output below

# ---------------------------------------------------------------------------
# STEP 1a: general (non-aligned) coupling formula, 6 points, moderate tanbeta
# ---------------------------------------------------------------------------
crosscheck_rows = []

candidates = []
for tanb in (1.0, 3.0, 10.0, 50.0):
    for sba in (0.9, 0.7, 0.5):
        candidates.append((tanb, sba))

testA_points = []
mh = 125.0
# Diverse: degenerate mA=mHp=350 AND asymmetric mA!=mHp, zero AND nonzero
# lambda6/lambda7, across all 3 masses and the full tanb/sba grid -- fixed
# after SOL_REVIEW.md item 4 found the original version tested only
# mphi=150, lambda6=lambda7=0, mA=mHp=350 (an early-break bug, see below).
for mphi in (150.0, 250.0, 400.0):
    for tanb, sba in candidates:
        beta = math.atan(tanb)
        sb, cb = math.sin(beta), math.cos(beta)
        for (mA, mHp, l6, l7) in ((350.0, 350.0, 0.0, 0.0), (340.0, 320.0, 0.05, -0.03)):
            m12_2 = 0.5 * mphi * mphi * sb * cb
            testA_points.append((mh, mphi, mA, mHp, sba, l6, l7, m12_2, tanb))

nA_pass = 0
nA_total = 0
nA_theoryok = 0
# No early break (SOL_REVIEW.md item 4: the original loop broke after the
# first 6 theory-valid points, which happened to all come from the first
# (mphi=150, degenerate mA=mHp, lambda6=lambda7=0) block -- so the claimed
# "diverse" validation set was never actually diverse). Now runs every point.
for (mh, mphi, mA, mHp, sba, l6, l7, m12_2, tanb) in testA_points:
    row = run_phys(mh, mphi, mA, mHp, sba, l6, l7, m12_2, tanb)
    if not theory_ok(row):
        continue  # skip invalid points per instructions
    nA_theoryok += 1
    g_imag = as_float(row, "g_hphiphi_imag_GeV")
    g_gen = as_float(row, "g_general_formula_GeV")
    # Strict sign check (SOL_FINAL_REVIEW.md Additional issue #1): GeneralProbe.cpp's
    # sign was fixed to equal Im[get_coupling_hhh] directly, so no +/- tolerance
    # is needed or wanted here -- a sign flip must FAIL, not silently pass as "-g".
    diff = abs(g_imag - g_gen)
    rel = diff / abs(g_imag) if g_imag else math.nan
    verdict = "PASS" if rel < 1e-6 else "FAIL"
    nA_total += 1
    if verdict == "PASS":
        nA_pass += 1
    crosscheck_rows.append(dict(
        test_name="general_nonaligned_coupling_formula",
        point_description=f"mphi={mphi},tanb={tanb},sba={sba}",
        mh=mh, mphi=mphi, mA=mA, mHp=mHp, sba=sba, lambda6=l6, lambda7=l7,
        m12_2_or_lambda1=m12_2, tan_beta=tanb, mode="phys",
        quantity_tested="g_hphiphi_imag_GeV vs g_general_formula_GeV",
        formula_value=g_gen, ground_truth_value=g_imag,
        abs_diff=diff, rel_diff=rel,
        verdict=verdict,
        note="strict_sign_match",
    ))

# ---------------------------------------------------------------------------
# STEP 1b: M2 exact-identity formula (alignment, lam1 route)
# ---------------------------------------------------------------------------
# NOTE (added after SOL_REVIEW.md item 6): the M2_actual vs
# M2_computed_from_lam1_formula comparison below is CIRCULAR -- both are
# computed inside GeneralProbe from the same CLI arguments via the same
# trigonometric rearrangement, neither queries the THDM object. It verifies
# the algebra of the rearrangement, not agreement with 2HDMC. Retained
# because the algebra itself is a real, useful check, but re-labeled
# "internal_consistency" below rather than "independent". The GENUINELY
# independent check is test_name=star_identity_independent_via_coupling
# further down, which ties the same M2 formula to g_hphiphi_imag_GeV -- an
# actual get_coupling_hhh() query, a different code path entirely.
nB_pass = 0
nB_total = 0
mh = 125.0
lambda6_anchor = 1.177689207010651e-4
for mphi in (200.0, 250.0, 300.0):
    mA = mHp = 300.0
    for tanb in (1e3, 1e5, 4e7):
        row = run_lam1(mh, mphi, mA, mHp, 1.0, 1.0, lambda6_anchor, 0.0, tanb)
        m2_actual = as_float(row, "M2_actual_GeV2")
        m2_formula = as_float(row, "M2_computed_from_lam1_formula_GeV2")
        abs_diff = abs(m2_actual - m2_formula)
        rel_diff = abs_diff / abs(m2_actual) if m2_actual else math.nan
        verdict = "PASS" if rel_diff < 1e-6 else "FAIL"
        nB_total += 1
        nB_pass += verdict == "PASS"
        crosscheck_rows.append(dict(
            test_name="M2_internal_consistency_lam1_route",
            point_description=f"mphi={mphi},tanb={tanb},lambda1=1.0",
            mh=mh, mphi=mphi, mA=mA, mHp=mHp, sba=1.0, lambda6=lambda6_anchor, lambda7=0.0,
            m12_2_or_lambda1=1.0, tan_beta=tanb, mode="lam1",
            quantity_tested="M2_actual_GeV2 vs M2_computed_from_lam1_formula_GeV2",
            formula_value=m2_formula, ground_truth_value=m2_actual,
            abs_diff=abs_diff, rel_diff=rel_diff, verdict=verdict, note="",
        ))

for lam1 in (0.1, 1.0, 4.0):
    row = run_lam1(125.0, 250.0, 300.0, 300.0, 1.0, lam1, lambda6_anchor, 0.0, 4.0e7)
    m2_actual = as_float(row, "M2_actual_GeV2")
    m2_formula = as_float(row, "M2_computed_from_lam1_formula_GeV2")
    abs_diff = abs(m2_actual - m2_formula)
    rel_diff = abs_diff / abs(m2_actual) if m2_actual else math.nan
    verdict = "PASS" if rel_diff < 1e-6 else "FAIL"
    nB_total += 1
    nB_pass += verdict == "PASS"
    crosscheck_rows.append(dict(
        test_name="M2_internal_consistency_lambda1_independence",
        point_description=f"mphi=250,tanb=4e7,lambda1={lam1}",
        mh=125.0, mphi=250.0, mA=300.0, mHp=300.0, sba=1.0, lambda6=lambda6_anchor, lambda7=0.0,
        m12_2_or_lambda1=lam1, tan_beta=4.0e7, mode="lam1",
        quantity_tested="M2_actual_GeV2 vs M2_computed_from_lam1_formula_GeV2",
        formula_value=m2_formula, ground_truth_value=m2_actual,
        abs_diff=abs_diff, rel_diff=rel_diff, verdict=verdict, note="lambda1 sweep",
    ))

# lambda7 != 0 divergence probe (report only, no verdict threshold)
row = run_lam1(125.0, 250.0, 300.0, 300.0, 1.0, 1.0, lambda6_anchor, 0.05, 4.0e7)
m2_actual = as_float(row, "M2_actual_GeV2")
m2_formula = as_float(row, "M2_computed_from_lam1_formula_GeV2")
crosscheck_rows.append(dict(
    test_name="M2_lambda7_nonzero_divergence_probe",
    point_description="mphi=250,tanb=4e7,lambda1=1.0,lambda7=0.05",
    mh=125.0, mphi=250.0, mA=300.0, mHp=300.0, sba=1.0, lambda6=lambda6_anchor, lambda7=0.05,
    m12_2_or_lambda1=1.0, tan_beta=4.0e7, mode="lam1",
    quantity_tested="M2_actual_GeV2 vs M2_computed_from_lam1_formula_GeV2",
    formula_value=m2_formula, ground_truth_value=m2_actual,
    abs_diff=abs(m2_actual - m2_formula),
    rel_diff=abs(m2_actual - m2_formula) / abs(m2_actual) if m2_actual else math.nan,
    verdict="REPORT_ONLY", note=f"expected large deviation ~0.5*v^2*lambda7*tanb={0.5*246.22**2*0.05*4e7:.4g}",
))

# ---------------------------------------------------------------------------
# STEP 1c: (*) identity g_hphiphi = (2*M2 - 2*mphi^2 - mh^2)/v, GENUINELY
# independent test -- ties the closed-form M2 (from lambda1/lambda6/lambda7/
# tanbeta alone, no coupling involved) to g_hphiphi_imag_GeV, an ACTUAL
# get_coupling_hhh() query -- a different code path from the M2 arithmetic
# entirely. Added after SOL_REVIEW.md item 0/6/15 identified this identity
# and flagged Step 1b as circular.
nC_pass = 0
nC_total = 0
diverse_points = [
    (125.0, 260.0, 340.0, 320.0, 0.05, 0.02, 3.0, 0.8),
    (125.0, 260.0, 340.0, 320.0, 0.05, 0.02, 3.0, 1.2),
    (125.0, 400.0, 400.0, 400.0, 0.0, 0.0, 10.0, 1.0),
    (125.0, 220.0, 500.0, 480.0, -0.03, 0.01, 25.0, 0.6),
    (125.0, 250.0, 300.0, 300.0, 1.177689207010651e-4, 0.0, 4.0e7, 1.0),
]
for (mh_, mphi_, mA_, mHp_, l6_, l7_, tanb_, r_) in diverse_points:
    M2_ = r_ * mphi_ * mphi_
    beta_ = math.atan(tanb_)
    sb_, cb_ = math.sin(beta_), math.cos(beta_)
    m12_2_ = M2_ * sb_ * cb_
    row = run_phys(mh_, mphi_, mA_, mHp_, 1.0, l6_, l7_, m12_2_, tanb_)
    g_true = as_float(row, "g_hphiphi_imag_GeV")
    M2_actual_ = as_float(row, "M2_actual_GeV2")
    star = (2.0 * M2_actual_ - 2.0 * mphi_ * mphi_ - mh_ * mh_) / as_float(row, "v_GeV")
    rel = abs(g_true - star) / abs(g_true) if g_true else math.nan
    verdict = "PASS" if rel < 1e-9 else "FAIL"
    nC_total += 1
    nC_pass += verdict == "PASS"
    crosscheck_rows.append(dict(
        test_name="star_identity_independent_via_coupling",
        point_description=f"mphi={mphi_},mA={mA_},mHp={mHp_},l6={l6_},l7={l7_},tanb={tanb_},r={r_}",
        mh=mh_, mphi=mphi_, mA=mA_, mHp=mHp_, sba=1.0, lambda6=l6_, lambda7=l7_,
        m12_2_or_lambda1=m12_2_, tan_beta=tanb_, mode="phys",
        quantity_tested="g_hphiphi_imag_GeV (actual get_coupling_hhh query) vs (2*M2-2*mphi^2-mh^2)/v",
        formula_value=star, ground_truth_value=g_true,
        abs_diff=abs(g_true - star), rel_diff=rel, verdict=verdict,
        note="genuinely independent (SOL_REVIEW.md item 0's (*) identity)",
    ))

val_dir = CAMP / "validation"
val_dir.mkdir(exist_ok=True)
with open(val_dir / "numerical_crosschecks.csv", "w", newline="") as f:
    fieldnames = list(crosscheck_rows[0].keys())
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(crosscheck_rows)

print(f"STEP1a general-formula: {nA_pass}/{nA_total} PASS (theory-valid points found: {nA_theoryok})")
print(f"STEP1b M2-internal-consistency: {nB_pass}/{nB_total} PASS")
print(f"STEP1c (*) identity independent test: {nC_pass}/{nC_total} PASS")
worstA = max((r["rel_diff"] for r in crosscheck_rows if r["test_name"] == "general_nonaligned_coupling_formula" and not math.isnan(r["rel_diff"])), default=math.nan)
worstB = max((r["rel_diff"] for r in crosscheck_rows if r["test_name"].startswith("M2_internal_consistency") and not math.isnan(r["rel_diff"])), default=math.nan)
worstC = max((r["rel_diff"] for r in crosscheck_rows if r["test_name"] == "star_identity_independent_via_coupling" and not math.isnan(r["rel_diff"])), default=math.nan)
print(f"STEP1c worst rel_diff: {worstC:.3g}")
print(f"STEP1a worst rel_diff: {worstA:.3g}")
print(f"STEP1b worst rel_diff: {worstB:.3g}")

# ---------------------------------------------------------------------------
# STEP 2: M2 variation grid
# ---------------------------------------------------------------------------
m2_dir = CAMP / "m2_study"
m2_dir.mkdir(exist_ok=True)
anchor_lambda6 = 1.177689207010651e-4
anchor_tanb = 40000000.00000001
grid_rows = []
grid_summary = {}
for mphi in (200.0, 250.0, 300.0):
    beta = math.atan(anchor_tanb)
    sb, cb = math.sin(beta), math.cos(beta)
    valid_rs = []
    for r in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        M2 = r * mphi * mphi
        m12_2 = M2 * sb * cb
        row = run_phys(125.0, mphi, 300.0, 300.0, 1.0, anchor_lambda6, 0.0, m12_2, anchor_tanb)
        row["mphi_target"] = mphi
        row["r_M2_over_mphi2"] = r
        row["M2_target"] = M2
        row["m12_2_used"] = m12_2
        grid_rows.append(row)
        if theory_ok(row):
            valid_rs.append((r, as_float(row, "g_hphiphi_imag_GeV")))

    # Added after SOL_REVIEW.md item 9(b): the coarse Delta-r=0.25 grid above
    # never lands close enough to the theory-valid M2 to demonstrate that the
    # phys-route (masses+m12^2 direct) CAN produce theory-valid points at
    # this tanbeta -- it can, once M2 is set via the campaign's own exact
    # identity (assumptions_and_limits.md Section 2) rather than the naive
    # M2=r*mphi^2. This row makes that demonstration a committed artefact
    # instead of only a reviewer's ad-hoc check.
    v_ = float(row["v_GeV"])
    M2_exact = mphi * mphi + (125.0 * 125.0 - v_ * v_ * 1.0) / anchor_tanb**2 - 1.5 * v_ * v_ * anchor_lambda6 / anchor_tanb
    m12_2_exact = M2_exact * sb * cb
    row_exact = run_phys(125.0, mphi, 300.0, 300.0, 1.0, anchor_lambda6, 0.0, m12_2_exact, anchor_tanb)
    row_exact["mphi_target"] = mphi
    row_exact["r_M2_over_mphi2"] = "exact_via_star_identity_lambda1eq1"
    row_exact["M2_target"] = M2_exact
    row_exact["m12_2_used"] = m12_2_exact
    grid_rows.append(row_exact)
    if theory_ok(row_exact):
        valid_rs.append(("exact_via_star_identity_lambda1eq1", as_float(row_exact, "g_hphiphi_imag_GeV")))
    grid_summary[mphi] = valid_rs

fieldnames = list(grid_rows[0].keys())
with open(m2_dir / "m2_variation.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(grid_rows)

with open(m2_dir / "m2_variation_summary.md", "w") as f:
    f.write("# M2 variation grid — factual summary (no interpretation)\n\n")
    f.write(
        "**FIXED (previously flagged per `validation/SOL_FINAL_REVIEW.md` Additional "
        "issue #3, now resolved -- see `validation/MASS_RECONSTRUCTION_FIX.md`):** "
        "every row in `m2_variation.csv` is at tan(beta)=4e7. 2HDMC's own "
        "`get_hmass()` used to round-trip through `get_m12_2()` (catastrophic "
        "cancellation, THDM.cpp:2786) and return a mass 1.5-4.6% off the requested "
        "mphi/mA/mHp, which fed directly into `total_width_h2_GeV`/`ctau_h2_mm` via "
        "`DecayTable`. `THDM::set_param_phys()`/`set_param_phys_lam1()` now cache "
        "the exact physical-basis inputs they are given (masses, m12_2, and -- a "
        "second, independent conditioning bug found while fixing the first -- "
        "lambda1) instead of re-deriving them through the lossy round-trip, so "
        "`get_hmass()` now returns the requested mass exactly at any tan(beta). "
        "The `hmass_h2_reconstructed_GeV`/`hmass_hA_reconstructed_GeV`/"
        "`hmass_hHp_reconstructed_GeV` columns confirm this directly (now equal to "
        "`mphi_in`/`mA_in`/`mHp_in` to machine precision). `total_width_h2_GeV` and "
        "`ctau_h2_mm` in this file and `sensitivity_probes.csv` were regenerated "
        "with the fix. In `m2_variation.csv` the shift is roughly 5-10% relative "
        "to the pre-fix values (e.g. mphi=200 GeV row 1: total_width_h2_GeV "
        "1.198e7->1.287e7 GeV, ctau_h2_mm 1.648e-20->1.533e-20 mm), consistent "
        "with the previously measured mass error. In `sensitivity_probes.csv` "
        "(the r=M2/mphi^2=1 anchor point) the shift is smaller, ~1.7% "
        "(pre-fix 1.3118e-15 GeV -> post-fix 1.3339e-15 GeV on "
        "total_width_h2_GeV). "
        "**Correction to this paragraph, made during a later bias/behavior "
        "audit (`validation/SOL_BIAS_AUDIT.md`):** an earlier version of this "
        "text claimed the sensitivity_probes.csv pre-fix value was 2.349e-13 "
        "GeV (a ~176x swing). That number was never a real pre-fix value -- "
        "it was itself an artifact of the build-staleness bug described next, "
        "and asserting it as 'the pre-fix value' repeated, in this exact "
        "paragraph, the same error class the paragraph was written to explain. "
        "The number above (1.3118e-15 GeV, ~1.7%) is the genuine, "
        "independently-reproduced pre-fix value. "
        "**Build-hygiene bug, found by an independent review "
        "(`validation/SOL_FINAL_REVIEW_2.md`), and FIXED (not just documented) "
        "in the Makefile itself:** 2HDMC's Makefile used to make each object "
        "file depend only on its own matching header, not on any header it "
        "transitively `#include`s. `DecayTable`/`Constraints` each hold a "
        "`THDM model;` member BY VALUE, so any incremental `make` (without "
        "`make clean` first) after `THDM.h` changed size used to silently "
        "link a fresh `THDM.o` against stale `DecayTable.o`/`Constraints.o`/"
        "`SM.o`/`Util.o` -- a real ODR violation producing deterministic but "
        "wrong width/BR/ctau/theory-flag numbers, with NO compiler warning. "
        "This bug (not the mass-reconstruction physics fix) was responsible "
        "for several wildly wrong 'before/after' comparisons produced earlier "
        "in this same session and since corrected (see "
        "`validation/MASS_RECONSTRUCTION_FIX.md`), including the 176x claim "
        "corrected two paragraphs above. The Makefile (`2hdmc_build/Makefile` "
        "here and in every other 2hdmc build directory in this workspace) now "
        "uses `-MMD -MP` plus an `-include` of the generated `.d` files, so a "
        "plain `make` after any header change rebuilds everything that "
        "actually depends on it -- verified directly: touching only `THDM.h` "
        "and running `make` (no `make clean`) now recompiles `THDM.o`, "
        "`DecayTable.o`, and `Constraints.o` automatically. `make clean` "
        "before the first build on a fresh checkout is still needed (no `.d` "
        "files exist yet then), but this bug can no longer recur silently "
        "on an ordinary incremental build. The values in this file and "
        "`sensitivity_probes.csv` were regenerated after this Makefile fix "
        "and independently cross-checked. "
        "The trilinear coupling itself (`g_hphiphi_imag_GeV`) "
        "was never affected -- `get_coupling_hhh` never calls `get_m12_2()` -- and "
        "changed only in its last significant digit across this regeneration. "
        "(The separate `m2_variation_moderate_tanbeta_illustrative.csv` and "
        "`m2_variation_finegrid_tanbeta10_illustrative.csv` files, at tan(beta)=10, "
        "were never affected -- mass round-trip was already machine-precision "
        "there.)\n\n"
    )
    for mphi, valid in grid_summary.items():
        f.write(f"\n## mphi = {mphi} GeV\n\n")
        f.write("theory-valid r = M2/mphi^2 values (construction_ok AND unitarity_ok AND perturbativity_ok AND positivity_ok, all ==1):\n\n")
        if valid:
            f.write("| r | g_hphiphi_imag_GeV |\n|---|---|\n")
            for r, g in valid:
                f.write(f"| {r} | {g:.6f} |\n")
        else:
            f.write("(none of the 7 scanned r values were theory-valid)\n")
print(f"STEP2 grid written: {len(grid_rows)} rows; valid r-counts: {{m: len(v) for m,v in grid_summary.items()}}".replace("{m: len(v) for m,v in grid_summary.items()}", str({m: len(v) for m, v in grid_summary.items()})))

# ---------------------------------------------------------------------------
# STEP 2b: illustrative moderate-tanbeta=10 grid (coarse, r=0..1.5 step 0.25)
# and a fine follow-up scan near r=1 at mphi=250 -- both now committed
# artefacts (previously run ad hoc and only reported in prose; the fine scan
# in particular had "no committed artefact", SOL_REVIEW.md item 11).
# NOT this project's benchmark family -- illustrative only, see
# COUPLING_STUDY_REPORT.md.
# ---------------------------------------------------------------------------
illus_tanb = 10.0
illus_rows = []
beta_i = math.atan(illus_tanb)
sb_i, cb_i = math.sin(beta_i), math.cos(beta_i)
for mphi in (200.0, 250.0, 300.0):
    for r in (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        M2 = r * mphi * mphi
        m12_2 = M2 * sb_i * cb_i
        row = run_phys(125.0, mphi, 300.0, 300.0, 1.0, anchor_lambda6, 0.0, m12_2, illus_tanb)
        row["mphi_target"] = mphi
        row["r_M2_over_mphi2"] = r
        row["M2_target"] = M2
        row["m12_2_used"] = m12_2
        row["tan_beta_illustrative"] = illus_tanb
        illus_rows.append(row)
with open(m2_dir / "m2_variation_moderate_tanbeta_illustrative.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(illus_rows[0].keys()))
    w.writeheader()
    w.writerows(illus_rows)
print(f"STEP2b illustrative grid written: {len(illus_rows)} rows")

fine_rows = []
mphi_fine = 250.0
for i in range(21):
    r = 0.80 + 0.02 * i
    M2 = r * mphi_fine * mphi_fine
    m12_2 = M2 * sb_i * cb_i
    row = run_phys(125.0, mphi_fine, 300.0, 300.0, 1.0, anchor_lambda6, 0.0, m12_2, illus_tanb)
    row["mphi_target"] = mphi_fine
    row["r_M2_over_mphi2"] = r
    row["M2_target"] = M2
    row["m12_2_used"] = m12_2
    row["tan_beta_illustrative"] = illus_tanb
    fine_rows.append(row)
# Extra fine points around the upper boundary (SOL_REVIEW.md item 11: r=1.005
# already fails, not r=1.02 as originally, uncommitted, reported) -- add a
# tighter sub-scan there specifically.
for r in (1.00, 1.002, 1.005, 1.01, 1.02):
    M2 = r * mphi_fine * mphi_fine
    m12_2 = M2 * sb_i * cb_i
    row = run_phys(125.0, mphi_fine, 300.0, 300.0, 1.0, anchor_lambda6, 0.0, m12_2, illus_tanb)
    row["mphi_target"] = mphi_fine
    row["r_M2_over_mphi2"] = r
    row["M2_target"] = M2
    row["m12_2_used"] = m12_2
    row["tan_beta_illustrative"] = illus_tanb
    fine_rows.append(row)
with open(m2_dir / "m2_variation_finegrid_tanbeta10_illustrative.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(fine_rows[0].keys()))
    w.writeheader()
    w.writerows(fine_rows)
valid_fine = sorted(set(float(r["r_M2_over_mphi2"]) for r in fine_rows if theory_ok(r)))
print(f"STEP2b fine grid written: {len(fine_rows)} rows; theory-valid r values at mphi=250,tanb=10: {valid_fine}")

# ---------------------------------------------------------------------------
# STEP 3: sensitivity probes (anchor = mphi=250, exact-via-star-identity row,
# theory-valid -- switched from the theory-invalid r=1.0 row per SOL_REVIEW.md
# "Additional issue #1")
# ---------------------------------------------------------------------------
anchor_row = next(r for r in grid_rows if r["mphi_target"] == 250.0 and r["r_M2_over_mphi2"] == "exact_via_star_identity_lambda1eq1")
assert theory_ok(anchor_row), f"sensitivity-probe anchor is not theory-valid: {anchor_row}"
anchor_m12_2 = float(anchor_row["m12_2_used"])

sens_rows = []
for l6 in (0.0, 1.177689207010651e-4, 1e-3, 1e-2, 0.1):
    row = run_phys(125.0, 250.0, 300.0, 300.0, 1.0, l6, 0.0, anchor_m12_2, anchor_tanb)
    row["sweep_type"] = "lambda6"
    row["swept_value"] = l6
    sens_rows.append(row)

for tanb in (1e5, 1e6, 1e7, 4e7):
    beta = math.atan(tanb)
    sb, cb = math.sin(beta), math.cos(beta)
    m12_2 = 62500.0 * sb * cb  # keep M2 fixed at mphi^2=62500
    row = run_phys(125.0, 250.0, 300.0, 300.0, 1.0, anchor_lambda6, 0.0, m12_2, tanb)
    row["sweep_type"] = "tan_beta_fixed_M2"
    row["swept_value"] = tanb
    sens_rows.append(row)

for lam1 in (0.1, 0.5, 1.0, 2.0, 4.0):
    row = run_lam1(125.0, 250.0, 300.0, 300.0, 1.0, lam1, anchor_lambda6, 0.0, anchor_tanb)
    row["sweep_type"] = "lambda1"
    row["swept_value"] = lam1
    sens_rows.append(row)

fieldnames = list(sens_rows[0].keys())
# union of keys across all rows (phys vs lam1 rows may have same header, but be safe)
allkeys = []
for r in sens_rows:
    for k in r.keys():
        if k not in allkeys:
            allkeys.append(k)
with open(m2_dir / "sensitivity_probes.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=allkeys)
    w.writeheader()
    w.writerows(sens_rows)
print(f"STEP3 sensitivity probes written: {len(sens_rows)} rows")

# ---------------------------------------------------------------------------
# STEP 4: coupling comparison table
# ---------------------------------------------------------------------------
# Anchor point: the lam1-route (lambda1=1 as literal input), NOT the
# phys-route r=1.0 grid row. Fixed after SOL_REVIEW.md "Additional issue #1":
# the phys-route r=1.0 row (m12_2 = mphi^2*sin(beta)*cos(beta), no lambda6
# correction) fails all four theory checks at this tanbeta (see
# m2_variation.csv) even though the coupling value itself only differs in
# the 9th significant digit -- the flagship comparison table should not be
# built from a point the campaign itself calls theory-invalid.
cc_dir = CAMP / "coupling_comparison"
cc_dir.mkdir(exist_ok=True)
cc_rows = []
for mphi in (200.0, 250.0, 300.0):
    row = run_lam1(125.0, mphi, 300.0, 300.0, 1.0, 1.0, anchor_lambda6, 0.0, anchor_tanb)
    assert theory_ok(row), f"lam1-route anchor at mphi={mphi} is not theory-valid: {row}"
    v = float(row["v_GeV"])
    g_phys_signed = float(row["g_hphiphi_imag_GeV"])
    M22 = float(row["M22_2_Y2_candidate_GeV2"])
    M2act = float(row["M2_actual_GeV2"])
    ef_simple = 8.0 * mphi * mphi / v
    ef_m2 = 8.0 * (mphi * mphi - M22) / v
    ef_m2_using_M2 = 8.0 * (mphi * mphi - M2act) / v
    star_check = (2.0 * M2act - 2.0 * mphi * mphi - 125.0 * 125.0) / v  # (*) identity, SOL_REVIEW.md item 0
    cc_rows.append(dict(
        mphi_GeV=mphi, v_GeV=v,
        physical_2HDM_GeV=g_phys_signed,
        physical_2HDM_from_star_identity_GeV=star_check,
        M2_actual_GeV2=M2act,
        EF_simple_GeV=ef_simple,
        M22_2_candidate_GeV2=M22,
        EF_m2_GeV=ef_m2,
        m2_definition_used="M22_2_Higgs_basis_candidate_per_prior_audit",
        EF_m2_using_M2_GeV=ef_m2_using_M2,
        EF_m2_over_physical_2HDM=ef_m2 / g_phys_signed,
        construction_route="lam1 (lambda1=1 literal input), theory-valid (unitarity=perturbativity=stability=positivity=1)",
    ))
with open(cc_dir / "coupling_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(cc_rows[0].keys()))
    w.writeheader()
    w.writerows(cc_rows)
print("STEP4 coupling_table.csv:")
for r in cc_rows:
    print(r)
