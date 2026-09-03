# SOL_REVIEW — adversarial review of `physical_vs_effective_coupling_v1`

Reviewer: independent agent, 2026-09-02. No prior context on this campaign.
Everything below was re-derived by hand from `~/atlas_dihiggs/dihiggs/2hdmc/src/THDM.cpp`
and re-measured with fresh `2hdmc_build/GeneralProbe` invocations (≈40 new runs).
**No file in the campaign was modified.** Labels: CONFIRMED / CONDITIONAL /
UNSUPPORTED / WRONG / NUMERICALLY_UNSTABLE.

---

## 0. The one result that should have been the report's centrepiece

Before the item-by-item list, the finding that reframes several of them.
Re-deriving `get_coupling_hhh` and `set_param_phys` by hand and then testing
numerically, I find:

```
g_hφφ ≡ Im[get_coupling_hhh(1,2,2)] = ( 2·M² − 2·m_φ² − m_h² ) / v          (★)
        with M² ≡ m12²/(sinβ cosβ)
```

**(★) is an EXACT GENERAL IDENTITY at exact alignment sin(β−α)=1.** It holds for
*any* tanβ, *any* λ6, *any* λ7, *any* m_A, *any* m_H±. Verified to machine
precision at (tanβ, λ6, λ7, m_A, m_H±, m_φ, r) =
(3, 0.05, 0.02, 340, 410, 270, 0.8), (3, 0, 0, 340, 410, 270, 0.8),
(10, 0.05, 0, 400, 400, 270, 1.2), (10, 0, 0.02, 400, 400, 270, 1.2),
at tanβ ∈ {1,2,5,10} × r ∈ {0.5,1.0}, and against **all 21 rows** of
`m2_study/m2_variation.csv` (max rel. dev. 1.2×10⁻⁸, itself a conditioning
artefact — see item 10) and all 21 rows of the tanβ=10 illustrative grid (exact
to 1e-13).

Derivation sketch (alignment ⇒ α=β−π/2 ⇒ ca=sβ, sa=−cβ), from `set_param_phys`
(THDM.cpp:352-356): λ3+λ4+λ5 = (m_h² − m_φ² + M²)/v² − 1.5λ6/tβ − 1.5λ7·tβ, in
which **m_A and m_H± cancel identically**; the residual λ6/λ7 pieces are cancelled
exactly by the corresponding pieces of the Higgs-basis rotation (Λ_i = ¼s²_{2β}(…)
+ λ_i − s_{2β}c_{2β}(λ6−λ7)) plus the 3λ1cβ² piece; g = −v·(Z3+Z4+Z5).

(★) immediately settles §5, §6, §8, §9, §10 and the report's two "unresolved"
questions 1 and 2, all of which the report leaves as empirical observations or
open algebra. Note also that REQUALIFICATION_SUMMARY.md §5 already states (★)
verbatim (as `g_hφφ = (m_h² + 2m_φ² − 2M²)/v`) — see item 13.

---

## 1. Identity and field ordering (index 1 = "h", index 2 = "H" = m_φ)

**CONFIRMED, with one wording defect.** `set_param_phys` (THDM.cpp:322-326)
refuses m_h > m_H, and `get_param_phys` (THDM.cpp:1094-1095) assigns m_h/m_H as
the smaller/larger eigenvalue of the CP-even mass matrix. With m_h=125 < m_φ ∈
{200,250,300}, 2HDMC index 1 is the 125 GeV state and index 2 is m_φ. Applied
consistently in `GeneralProbe.cpp` and every CSV.

Defect: `physical_trilinear_source_trace.md` §1 writes "index 1 = 'h' = SM-like".
2HDMC's index 1 is the **lighter** state, not the SM-like one; the two coincide
only at alignment. This matters because the general-formula validation points
(`numerical_crosschecks.csv`) run at sba ∈ {0.5,0.7,0.9}, where index 1 is *not*
SM-like. Harmless for the algebra, wrong as a general statement.

## 2. Coupling normalization and signs

**Source quotes CONFIRMED; product sign bookkeeping WRONG in two places.**

Verified verbatim against source: `Z6=-l6, Z7=-l7` with Z1..Z5 unflipped
(THDM.cpp:1580); `get_param_higgs`'s Λ6/Λ7 used unflipped elsewhere
(`get_param_hybrid`, THDM.cpp:1163-1165 sets `Z7 = Lambda7`) — the report's
CONVENTION claim is correct. `get_cba()` (THDM.cpp:2828-2831) returns
`+sqrt(1-sba²)`, i.e. 2HDMC **cannot represent cos(β−α) < 0**; `get_param_hybrid`
by contrast returns `sign(sinba)·sqrt(...)`. The report's "general" formula and
its validation therefore cover only the cba ≥ 0 branch. Not stated in the
derivation docs (only in a `GeneralProbe.cpp` comment). CONDITIONAL.

Sign defects:
- `logs/run_all_probes.py:263` computes `g_phys = abs(float(row["g_hphiphi_imag_GeV"]))`.
  So `coupling_table.csv:physical_2HDM_GeV` = **+63.459…**, a magnitude. Report §5
  then says this value "equals −m_h²/v = −63.4594 **exactly**". The actual signed
  coupling is Im(c) = −63.459; the tabulated column is +63.459. The sentence as
  written is false about its own table.
- `ufo/validation.md` §2 asserts the `physical_2HDM_GeV` column "report[s] the same
  signed quantity" as `GHphiphi = Im(c)`. It does not (see above). It also cites
  "`validation/numerical_crosschecks.csv`, `physical_2HDM_GeV` column" — that
  column does not exist in that file.

## 3. Factor-of-two / identical-particle conventions in the permutation sum

**CONFIRMED, and independently anchored.** The `-I*v/2.` prefactor is exactly
compensated by the multiset {1,2,2} producing each of the 3 distinct
(h0,h1,h2) patterns twice under `gsl_permutation`. I checked this two ways:

1. By hand: 6 permutations = 2×[P(1,2,2)+P(2,1,2)+P(2,2,1)]; the ×2 cancels the /2.
2. Against a known external anchor: the same code at (1,1,1) gives
   c = −3i·v·Z1 = −3i·m_h²/v at alignment (Z1 = m_h²/v² = 0.257734 in every CSV
   row; −3·246.2206·0.257734 = −190.378). That is exactly the SM hhh Feynman rule,
   and exactly the UFO's own `GC_94 = -6i·lam·vev = -3i·MH²/vev`. The
   identical-particle combinatorics and the overall normalization are therefore
   correct and directly comparable to a UFO coupling.

## 4. Independent re-derivation of the general closed form

**CONFIRMED (my algebra reproduces the report's formula term-by-term), but the
report misdescribes its own validation set.**

For real qki (k∈{1,2}) the Z6 term's `(2q+conj q)` → `3q`. Summing the three
patterns:

| | Z1 | Z3+Z4 | Z5 | Z6 | Z7 |
|---|---|---|---|---|---|
|(1,2,2)| sc² | −sc² | s³ | 3s²c | −cs² |
|(2,1,2)| sc² | −sc² | −sc² | 3s²c | −s²c |
|(2,2,1)| sc² | s³ | −sc² | −3c³ | −s²c |
|Σ| 3sc² | s³−2sc² | s³−2sc² | 3c(2s²−c²) | −3cs² |

×2×(−iv/2) reproduces exactly
`c = −i·v·[3sc²Z1 + (s³−2sc²)(Z3+Z4+Z5) + 3c(2s²−c²)Z6 − 3cs²Z7]`. ✔

**Independent numeric extension (new, this review).** The report's own validation
(`numerical_crosschecks.csv`, 6 rows) never exercises the Z6/Z7 or generic-λ6/λ7
structure: all 6 rows have m_φ=150, λ6=λ7=0, m_A=m_H±=350. I re-ran the formula at
9 fresh points with **λ6=0.03, λ7=−0.05, m_A=340 ≠ m_H±=320, m_φ=260**,
sba ∈ {0.4,0.75,0.95}, tanβ ∈ {2,7,25}: max |rel. dev.| = **5.1×10⁻¹⁵**. The
formula is correct well beyond what the campaign tested.

**But report §1 misstates its own evidence.** It claims confirmation "at 6
non-aligned, **non-degenerate** points (moderate tanβ ∈ {1,3,10,50}, sba ∈
{0.5,0.7,0.9})". The CSV contains tanβ ∈ {1,3} only, m_φ=150 only, λ6=λ7=0, and
m_A=m_H±=350 — i.e. *degenerate*. `run_all_probes.py:78-81` breaks after the first
6 theory-valid points; the {10,50} and m_φ ∈ {250,400} candidates were never
reached. WRONG as written (the underlying claim survives on my evidence, not the
report's).

## 5. Alignment and m_A=m_H± ⇒ Z4=Z5

**CONFIRMED as an identity; the "two independent routes" claim is UNSUPPORTED.**

Λ4−Λ5 = λ4−λ5 identically (every other term in THDM.cpp:1128-1129 is
character-for-character the same) — GENERAL IDENTITY, no β/alignment assumption. ✔
And from `set_param_phys` itself, λ5−λ4 = 2(m_H±²−m_A²)/v² exactly, so m_A=m_H± ⇒
λ4=λ5 ⇒ Z4=Z5 at any tanβ. ✔ Confirmed in data: `lambda4_out == lambda5_out` and
`HiggsBasis_Z4 == HiggsBasis_Z5` to all 17 digits in every m_A=m_H± row.

Two defects: (a) report §2 promises "**two** independent routes that must agree (a
genuine cross-check, not asserted)" and then lists only a route "(a)" — there is no
(b). It is one route with two steps. (b) The cited `THDM.cpp:1088` is inside
`get_param_phys` (the λ→mass forward map), not "`set_param_phys`'s own mHp formula"
as claimed. Both are true identities, but the framing overstates the cross-check.

Note that per (★), Z4=Z5 is not actually needed: m_A and m_H± drop out of g_hφφ
entirely at alignment.

## 6. Is M² = m_φ² input, consequence, or accident?

**Algebra CONFIRMED. Validation CIRCULAR. §4's answer ("optional") WRONG.**

I re-derived §2 of `assumptions_and_limits.md` independently from
`set_param_phys_lam1` (THDM.cpp:414-416): with α=β−π/2, dividing by sβcβ and using
sβ = tβ·cβ, the denominator is tβ²cβ² and

```
M² = m_H² + (m_h² − v²λ1)/tan²β − 1.5·v²·λ6/tanβ + 0.5·v²·λ7·tanβ
```
exactly. ✔ Matches the report term for term.

**The "independent confirmation to 2.33×10⁻¹⁶ (12/12 points)" is circular.** In
`GeneralProbe.cpp`, `M2_actual` = `m12_2_exact_used/(sb*cb)` where in `lam1` mode
`m12_2_exact_used` is the probe's **own re-implementation** of the same formula
(lines 168-174), and `M2_from_lam1_formula` is the rearranged version (lines
228-234). Both are computed in the same program from the same CLI arguments and
**neither ever queries the THDM object**. The test verifies a trig rearrangement,
not agreement with 2HDMC. Calling it "independently confirmed" is an overclaim.
(The underlying algebra is nonetheless right — I checked it by hand.)

**§4's conclusion is wrong.** §4 says M²≈m_φ² is "Optional — a NUMERICAL LIMIT of
one specific, but not the only, construction route", and that a masses+m12² point
"does not automatically land at M2≈m_φ²". Route-independently, at alignment,

```
λ1 = (m_φ² − M²)/(v²cos²β) − 1.5·λ6·tanβ + 0.5·λ7·tan³β
```
and at tanβ=4×10⁷, v²cos²β = **3.79×10⁻¹¹ GeV²**. Requiring |λ1| ≲ 4π therefore pins
M² to within **±4.8×10⁻¹⁰ GeV², i.e. 7.6×10⁻¹⁵ relative**, of
m_φ² − 1.5v²λ6/tanβ. I verified this by probe: pushing M² off m_φ² by relative
1e-15 / 1e-13 / 1e-10 / 1e-8 moves λ1_out to −7068 / −7231 / −1.7e5 / −1.7e7.
**M²=m_φ² is not optional at this tanβ — it is forced by perturbativity for any
construction route whatsoever.** The report has the right identity and draws the
wrong conclusion from it.

**Arithmetic error.** `assumptions_and_limits.md` §5.1 states the λ6 correction is
"1.5·60624·1.1777e-4/4e7 ≈ **2.68×10⁻⁴** GeV²" and that this matches "the
≈2.7×10⁻⁴ discrepancy hand-computed against Christopher's own 200 GeV row".
Correct value: **2.678×10⁻⁷ GeV²** — a factor of 1000. Christopher's row has
m_φ²−M² = 40000 − 39999.99999999933·… = 2.68×10⁻⁷ GeV², so the *formula* is right
and the *stated arithmetic and its claimed agreement* are both wrong.

## 7. Is M² confused with m₂² anywhere?

**Columns CONFIRMED not conflated; §9's prose OVERCLAIMS.**
`EF_m2_using_M2_GeV` uses `M2_actual` and `EF_m2_GeV` uses `M22_2_Y2_candidate`;
`m2_definition_used` labels the latter. No numerical conflation.

But `EF_m2_using_M2 ≈ 0` is a **tautology of the grid construction**, not a
measurement: `run_all_probes.py` sets `m12_2 = M2*sb*cb` with M2 = 1.0·m_φ², and
the probe computes `M2_actual = m12_2/(sb*cb)`; `8(m_φ²−M2_actual)/v` is then
0 to one ulp by round-trip. Calling this "a clean, **quantitative** confirmation …
**definitively**" dresses up 8·(x−x)/v = 0. The substantive statement — that M² and
the Higgs-basis m₂² differ — is true and, better, quantifiable: from (★) and
g = 2(M22²−m_φ²)/v, **M22² = M² − m_h²/2 + O(cos²β)**; at tanβ=4×10⁷ the residual
is 5.7×10⁻⁵ GeV², at tanβ=10 it is 619 GeV², at tanβ=1 it is 31250 GeV² (I measured
all three). This also **closes the report's own "unresolved question 2"**: the
audit's `M22² = M2 − m_h²/2` is a large-tanβ identity at alignment, not a
benchmark coincidence, and is *independent* of M²=m_φ².

## 8. λ1-input vs reconstructed λ1

**CONFIRMED, no conflation found.** `GeneralProbe` keeps `lambda1_input_echo`,
`lambda1_recomputed`, `lambda1_roundtrip_abs_error` and `lambda1_out` distinct, and
the `M2_from_lam1_formula` column documents its mode-dependent choice
(`lambda1_in` for lam1, `lambda1_out` for phys). The round-trip error is surfaced
(0.0212 at λ1=1, warning flag = 1) rather than hidden.

Minor: report §7 ranks "λ1 (at fixed … masses respectively)". In the lam1 sweep,
M² moves with λ1 (by (m_h²−v²λ1)/tan²β), so what is measured is ∂g/∂M²·∂M²/∂λ1.
That is in fact predictable in closed form: ∂g/∂λ1 = −2v/tan²β = −3.08×10⁻¹³ per
unit λ1; over λ1: 0.1→4 that predicts Δg = 1.20×10⁻¹²; the CSV shows
63.459361555949954 → 63.459361555951098, Δ = **1.14×10⁻¹²**. So the effect is not
"at or below the noise floor" (report §7.3) — it is resolvable and matches theory
to one digit. Underclaim, not error.

## 9. Numerical stability at tanβ=4×10⁷

**"0 of 21 pass" CONFIRMED in the CSV. The stated MECHANISM is WRONG.
Separately: NUMERICALLY_UNSTABLE — the CSVs cannot be reproduced from their own
printed inputs.**

(a) *0/21 including r=1*: confirmed by reading columns 41-44 of every row. ✔

(b) *The mechanism is misdiagnosed.* Report §6a: "feeding m12² = m_φ²·sinβ·cosβ
computed externally in double-precision Python still reconstructs λ1_out ≈ −7066 …
reproducing an 'equivalent' m12² to 16 significant digits via external arithmetic
is **not sufficient** at this conditioning." That is not what is happening. At
M² = m_φ² *exactly*, λ1 = 0/(v²cβ²) − 1.5λ6·tanβ = **−7066.135… identically** —
exact algebra, reachable with infinite precision. The λ1-route point is not "the
same m12² to 16 digits"; it is a *different* M² (m_φ² − 1.5v²λ6/tanβ, offset
2.678×10⁻⁷ GeV², 4.3×10⁻¹² relative), which is precisely what cancels the −7066.

Decisive test (mine): I fed the **phys** route the M² prescribed by the campaign's
own §3 identity at λ1=1 —

```
./GeneralProbe phys 125 <mφ> 300 300 1 1.177689207010651e-4 0 <M2*sb*cb> 4e7 1
  with M2 = mφ² + (mh² − v²·1)/tanβ² − 1.5v²λ6/tanβ
```
→ m_φ=200: λ1_out = **1.021195**, unitarity=perturbativity=stability=positivity=**1**
→ m_φ=250: λ1_out = **1.021195**, all four = **1**
→ m_φ=300: λ1_out = **1.597275**, all four = **1**

So the masses+m12² route **does** produce fully theory-valid points at tanβ=4×10⁷
at all three masses. The report's claim that "the only genuinely theory-valid point
at this tanβ is the λ1-route point" is **WRONG**; 0/21 is a grid-design artefact
(Δr = 0.25 ⇒ 15625 GeV² steps against a valid window ~5×10⁻¹⁰ GeV² wide), not a
statement about routes or about external arithmetic.

(c) *The CSVs are not self-reproducing.* `run_all_probes.py` passes arguments with
`%.17g` but `GeneralProbe` echoes the input columns with `%.10g`. Feeding
`m2_variation.csv`'s own printed inputs (`m12_2_in=0.001562499994`,
`lambda6_in=0.0001177689207`) back into the binary gives **λ1_out = +342334**
instead of the recorded **−7065.94** (sign flip, factor 48) and flips
`stability_ok`/`positivity_ok` from 0 to 1. The report's own documented "Sanity
check" command line gives λ1_out = **−3 830 184**, again not −7066. The coupling
column reproduces to ~2×10⁻⁹, so no *conclusion* moves — but no theory-validity
flag in these CSVs can be audited from the file itself.

## 10. Is g ≈ −63.4594 ≈ −m_h²/v genuine physics or conditioning?

**Physics CONFIRMED (and derivable, (★)); the claim of exactness at the printed
precision is UNSUPPORTED; §7's "resolvable tanβ trend" is WRONG.**

(★) at M² = m_φ² gives g = −m_h²/v exactly, with no m_φ, m_A, m_H±, λ6, λ7 or tanβ
dependence at all. I verified m_A/m_H± independence directly: m_A = m_H± ∈
{300,400,600,900} at m_φ=250 leaves g unchanged to 10 digits.

But "63.4594 GeV **to 6 significant figures** … **no residual m_φ dependence at all
at the precision shown**" is not what the table says. m_h²/v = 63.45936108748345,
and the three tabulated values deviate by **+3.82e-9 / +7.35e-9 / +1.17e-8**
relative — monotone in m_φ, i.e. a *systematic* residual, not a random last digit.

Decisive discriminator (mine): the same three masses at r=1 with tanβ=10
(`m2_variation_moderate_tanbeta_illustrative.csv`) give
−63.459361087483501 / …558 / …707, i.e. −m_h²/v to **1×10⁻¹⁵ at all three masses**.
So the 10⁻⁸ spread at tanβ=4×10⁷ is pure floating-point conditioning. Root cause,
which the report never identifies: 2HDMC computes cosβ as `cos(atan(tanβ))`; at
tanβ=4×10⁷ that carries a **−3.63×10⁻⁹ relative error** versus `1/sqrt(1+tanβ²)`
(2.4999999909295562e-8 vs 2.4999999999999992e-8). (`set_param_phys_lam1` has the
stable form commented out at THDM.cpp:389-399.) This single error explains the
mass spread *and* item 7's tanβ trend.

Consequence: report §7.2's "g_hφφ shifts by ~7×10⁻⁹ relative across
tanβ∈[10⁵,4×10⁷], monotonic, **well above the double-precision noise floor**" is
**WRONG** — it is the same cosβ artefact, the same size and the same sign, and it
is internally inconsistent with §5 treating an 8×10⁻⁹ mass spread as exactly zero.
NUMERICALLY_UNSTABLE.

## 11. Is the M² variation a fair comparison of physical models?

**Well-posed as a coordinate scan; the report's interpretation of the tanβ=4×10⁷
grid is UNSUPPORTED. The tanβ=10 grid CONFIRMED and correctly caveated.**

Holding masses, λ6, λ7, tanβ and sba while varying m12² does not silently change
anything — it changes λ1..λ5 as the deterministic outputs of `set_param_phys`, and
that is the intended meaning of the scan. However, at tanβ=4×10⁷ it drives
λ1 = (m_φ²−M²)/(v²cos²β) − 1.5λ6·tanβ to **±10¹⁴–10¹⁵** at every r ≠ 1 (CSV
`lambda1_out` column; I reproduced it). That is genuine algebra, not roundoff. So
the report's framing — "`g_hφφ` itself still varies smoothly … it is the
theory-validity *check* … that is catastrophically ill-conditioned, not the
coupling" — is backwards. The coupling is smooth because (★) makes it linear in
M²; the underlying quartic really does diverge; the constraint checker is right,
not ill-conditioned. Only 1 of 21 grid points is even a candidate physical model.

§6b (tanβ=10) is the informative panel and is correctly labelled illustrative. Its
"finer follow-up scan, logged in this report only" has **no committed artefact** —
I reproduced it independently: theory-valid r ∈ {0.98, 0.99, 1.00} at m_φ=250;
r=0.96 fails perturbativity, r=**1.005** already fails stability and positivity. So
"roughly r∈[0.98,1.00], asymmetric" is right; "r=1.02 already fails" understates
by a factor of 4 in the upper margin.

## 12. Is any EF mapping fitted-but-physically-invalid?

**§8's answer is right; §8's reasoning contains a WRONG claim. §9 is
quantitatively right but its "unexplained" gap is not unexplained (item 15).**

From (★), EF_simple = 8m_φ²/v is reached exactly at M² = 5m_φ² + m_h²/2. Verified:
at m_φ=250, tanβ=10, M²=320312.5 → g = **+2030.69955** GeV vs EF_simple =
2030.69955 GeV (8 digits), with λ1 = −425 and unitarity/perturbativity/stability/
positivity all 0. So EF_simple's magnitude is reachable in the M² coordinate at any
tanβ and is excluded by perturbativity, full stop — a one-line closed-form answer
in place of §8's empirical hedging.

**WRONG:** §8 states "Reaching EF_simple's magnitude would require a qualitatively
different mass configuration (**larger mA−m_φ splitting**, or a genuinely different
quartic regime)". g_hφφ is **exactly independent of m_A and m_H±** at alignment
(derivation above; measured: m_A=m_H± ∈ {300,400,600,900} → g identical to 10
digits). Mass splitting is irrelevant; only M²/m_φ² is.

§9's numbers are correct. Both "no" answers stand.

## 13. σ ∝ g² and the (EF_simple/physical)² table

**Arithmetic CONFIRMED (with a rounding slip); the framing and the citation are
WRONG.**

(EF_simple/|g|)² = (8m_φ²/m_h²)² **exactly**: 20.48² = 419.4304, 32² = **1024**,
46.08² = 2123.3664. The report's "2124" is a mis-rounding of 2123.37 (and "to 3
significant figures" would be 2120). The closed form is exact and worth stating —
these are not three empirical numbers.

The mismatch also factorizes cleanly: EF_simple/|g| = 4 × (m_φ²/(m_h²/2)) — a
factor **4** from the prescription's prefactor 8 where the physical Feynman rule
carries 2, times a factor 2m_φ²/m_h² from setting m₂²=0 instead of
m₂² = M22² = m_φ² − m_h²/2.

**Citation is wrong on both counts.** Report §10 claims this "independently
reproduces, via a completely different derivation path (… vs the prior audit's
UFO-coupling comparison at a *different* benchmark family), the same
**132×-1017×**-type normalization mismatch already flagged … in
REQUALIFICATION_SUMMARY.md §5". In fact:
- §5 of that file is the **same** family — photonic m_φ = 200/250/300, same
  m_h²/v = 63.4594 — and reports **4.2e2 / 1.0e3 / 2.1e3**, i.e. the *identical*
  numbers, not an independent family.
- The string "132" and "1017" appear **nowhere** in REQUALIFICATION_SUMMARY.md.
  The cited figures do not exist.
- §5 of that file already contains the closed form
  `g_hφφ = (m_h² + 2m_φ² − 2M²)/v` and its linear-in-M² verification. So this is
  the same computation redone, not "two independent computations agree".

## 14. UFO coupling normalization vs 2HDMC's returned trilinear

**Patch CONFIRMED correct (by my check, not the report's); validation.md contains
two false statements.**

Normalization is genuinely like-for-like, which nobody in the campaign
demonstrated: UFO `V_10 = [H,H,H]` carries `GC_94 = -6i·lam·vev = -3i·MH²/vev`,
and 2HDMC's `get_coupling_hhh(1,1,1)` = −3i·v·Z1 = −3i·m_h²/v at alignment. The
UFO's `vev = 2·MW·sw/ee` evaluates to **246.2205690734859** against 2HDMC's
246.22056907348588 — identical to 15 digits. So `GC_90` and
`get_coupling_hhh(1,2,2)` are directly comparable, and

`GC_90 = complex(0,1)*GHphiphi` with `GHphiphi = Im(c) = −63.459…` reproduces
c = −63.459i exactly (Re(c) = 0). The 2-file diff does exactly this and touches
nothing else. ✔

Worth stating and never stated: the frozen UFO's `8i·Mh2²/vev` is **positive
imaginary**, while the physical coupling is negative imaginary. The production UFO
therefore has the wrong **sign** as well as a 20–46× wrong magnitude. Irrelevant
for a single-diagram |M|², relevant the moment anything interferes.

Defects (already listed in item 2): validation.md §2's claim that
`physical_2HDM_GeV` is signed is false (it is `abs()`), and its citation of a
`physical_2HDM_GeV` column in `numerical_crosschecks.csv` points at a column that
does not exist. Also, the hard-coded default (−63.45936155377521) is copied from
the theory-**invalid** phys-route r=1 grid point rather than the theory-valid
λ1-route value (−63.459361555950252).

## 15. The "unexplained ~4.00× gap" between EF_m2 (M22²-based) and physical

**SOLVED. It is exactly 4, it is a pure normalization artefact, and there is no
physics in it.**

```
EF_m2  ≡ 8·(m_φ² − M22²)/v
g_hφφ  =  2·(M22² − m_φ²)/v      ← equivalent to (★) via M22² = M² − m_h²/2
⇒ EF_m2 = −4 · g_hφφ             identically
```
The 4 is nothing but the ratio of the effective prescription's prefactor (8) to the
physical Feynman-rule prefactor (2). Measured ratios in `coupling_table.csv`:
**4.0000000000000036, 4.000000000000004, 4.000000000000002** — exact to the last
representable digit, as an algebraic identity must be.

Both ingredients were already inside the campaign: `physical_trilinear_derivation.md`
§5 prints `g = 2(M22²−m_φ²)/v` and §9 prints `EF_m2 = 8(m_φ²−m₂²)/v` on facing
pages. Dividing them closes "Unresolved scientific question 1" in one line. It also
shows the relation is **not** benchmark-specific: 2(M22²−m_φ²)/v reproduces
`g_hphiphi_imag_GeV` at **every** r in `m2_variation.csv` (e.g. r=0.5, m_φ=250:
2(23437.5−62500)/246.2206 = −317.2968 = the CSV value), so the derivation doc's
"BENCHMARK-SPECIFIC RELATION, tested only at this project's … benchmark points"
label is an underclaim.

---

## Additional issues found

1. **`coupling_table.csv` provenance is misstated.** Report §5 says "At the
   requalified benchmark anchor (M2=m_φ²), `physical_2HDM_GeV` is 63.4594…". Those
   three rows are lifted (`run_all_probes.py:252-254`) from the **phys-route r=1
   grid points**, which the report itself declares theory-invalid
   (unitarity=perturbativity=stability=positivity=0). The theory-valid λ1-route
   value differs in the 9th digit (63.459361555950252 vs 63.45936155377521), so no
   conclusion changes — but §5, §8, §9, §10 and the UFO default all trace to points
   the report elsewhere disowns.

2. **`get_m12_2()` does not return the input m12².** THDM.cpp:2774-2792
   *re-derives* it from `m22_2` and the λ's. At tanβ=4×10⁷ the round trip is off by
   **4.5%** (0.0015624999943 in, 0.0014915713163 out — see any `m12_2_out` column).
   `GeneralProbe` correctly avoids it and comments on it; the report body never
   warns readers that `m12_2_out` in the shipped CSVs is unusable.

3. **The dominant numerical error source is unidentified.** `cos(atan(tanβ))` at
   tanβ=4×10⁷ is wrong by −3.6×10⁻⁹ relative (item 10). Everything the report reads
   as a 10⁻⁸–10⁻⁹ "signal" is this. 2HDMC's own author left the stable
   `1/sqrt(1+tb²)` form commented out at THDM.cpp:389-399.

4. **Cross-campaign inconsistency (flagged, not adjudicated).**
   REQUALIFICATION_SUMMARY.md §4 states that across M² = 36000 → 44000 GeV² the
   reconstructed λ1 runs "+1.056, +5.278, −7066.14, −5278.39, −1.056". The algebra
   λ1 = (m_φ²−M²)/(v²cos²β) − 1.5λ6·tanβ with v²cos²β = 3.79×10⁻¹¹ GeV² gives
   |λ1| ~ 10¹⁴ at |ΔM²| ~ 4000 GeV², which is what *this* campaign's
   `m2_variation.csv` and my own probes both show. The two campaigns' λ1 scans are
   mutually inconsistent by ~11 orders of magnitude; this campaign's is the one
   consistent with the source algebra.

5. **Line-number citations are accurate** (spot-checked: 1574, 1201-1220,
   1105-1138, 1088, 1135, 1137, 359, 414-416). Two are off by a couple of lines
   (`set_param_phys` starts at 317 not 319; `set_param_phys_lam1` at 368 not 398);
   both quoted code blocks are verbatim-correct.

6. **Ranking claim in §7 is inverted in explanation.** λ6's near-total absence from
   g_hφφ is not "too small to resolve above floating-point noise" — it is an
   **exact cancellation** at O(1/tanβ) between λ6's appearance in λ345 (−1.5λ6/tβ),
   in 3λ1cos²β (−4.5λ6/tβ) and in the Higgs-basis rotation (+6λ6/tβ). Consistent
   with (★), in which λ6 does not appear at all. The empirical conclusion is right;
   the stated reason is not.

---

## Overall verdict

The report's scientific spine holds. I independently re-derived the permutation-sum
closed form (it is exactly right, and I validated it at 9 points the campaign never
tested, including λ6,λ7≠0 and m_A≠m_H±), the Z4=Z5 identity, the M² λ1-route
identity, the collapse of g_hφφ onto −m_h²/v at M²=m_φ², and the O(10²–10³)
EF_simple/physical mismatch — every headline number reproduces. What does not hold
is a layer of interpretation on top: §4's "M²=m_φ² is optional" is wrong
(perturbativity pins M² to m_φ² within 8×10⁻¹⁵ relative at this tanβ, route
independently); §6a's "only the λ1 route can be theory-valid at this tanβ, external
arithmetic is insufficient" is wrong (I produced theory-valid phys-route points at
all three masses in one command); §7.2's tanβ "signal" and §5's "no residual m_φ
dependence at the precision shown" are two readings of the same `cos(atan(tanβ))`
artefact; §8's appeal to mass splitting is wrong (g_hφφ is exactly independent of
m_A, m_H±); §10's attribution to a "different benchmark family" and its
"132×-1017×" figures are not in the cited document; and the flagship "unexplained
4.00×" is 8/2, derivable in one line from two formulas the campaign itself prints.
Layered on that, the CSVs cannot be re-run from their own printed inputs (10 vs 17
significant digits), and the headline coupling table is built from points the report
elsewhere calls theory-invalid. My recommendation: the campaign's *derivations and
numbers* can stand with the caveats above recorded; §4, §6a, §7.2, §8 and §10
should be rewritten around the exact identity g_hφφ = (2M² − 2m_φ² − m_h²)/v, which
subsumes all of them and closes both of the report's "unresolved" questions.
