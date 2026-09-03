# Analytic derivation of g_hφφ^physical

**§0 added after independent adversarial review (`validation/SOL_REVIEW.md`,
`validation/SOL_REVIEW_RESPONSE.md`) — read it first; it is the master
identity that §§1-6 below build up to more slowly and that subsumes several
of their conclusions. A second, independent review round
(`validation/SOL_FINAL_REVIEW.md`, `validation/SOL_FINAL_RESPONSE.md`) then
re-derived (★) from scratch and confirmed it, but found the domain claim
made below for `M22²=M²−m_h²/2` was backwards — see the correction right
below the identity it appears in.**

## 0. The master exact identity (alignment, any tanβ/λ6/λ7/mA/mHp)

```
g_hφφ ≡ Im[get_coupling_hhh(1,2,2)] = (2·M² − 2·m_φ² − m_h²) / v          (★)
        with M² ≡ m12²/(sinβ·cosβ)
```

**GENERAL IDENTITY at exact alignment sin(β−α)=1 — holds for any tanβ, any
λ6, any λ7, any m_A, any m_H±.** Derivation: at alignment, `set_param_phys`'s
own formulas (`THDM.cpp:352-356`) give
`λ3+λ4+λ5 = (m_h²−m_φ²+M²)/v² − 1.5λ6/tanβ − 1.5λ7·tanβ`, with **m_A and
m_H± cancelling identically**; the λ6/λ7 pieces cancel exactly against the
corresponding terms in the Higgs-basis rotation (`get_param_higgs`'s
`Λ_i = ¼s²_{2β}(…) + λ_i − s_{2β}c_{2β}(λ6−λ7)`, `THDM.cpp:1125-1131`) plus
the `3λ1cosβ²` piece, leaving `g = −v·(Z3+Z4+Z5)` independent of λ1, λ6, λ7
individually.

**Verified three separate times, independently:**
1. By hand, term-by-term against `set_param_phys`/`get_param_higgs` (above).
2. Numerically at an asymmetric, non-benchmark point (mA=340≠mHp=320,
   λ6=0.05, λ7=0.02, tanβ=7, m_φ=260, r=0.8) — rel. dev. **3.3×10⁻¹⁶**.
3. Via the committed `validation/numerical_crosschecks.csv`
   `test_name=star_identity_independent_via_coupling` (5 diverse points,
   ties (★)'s M² to `g_hphiphi_imag_GeV` — an actual `get_coupling_hhh()`
   query, not a re-implementation) — 4/5 PASS at rel. dev. < 10⁻⁹; the one
   point that misses that threshold is the tanβ=4×10⁷ benchmark point
   itself, and the miss (7.35×10⁻⁹) is itself the diagnostic for §5's
   floating-point artefact below, not a failure of (★).

(★) immediately gives, by substitution:
- **At M²=m_φ² exactly: g_hφφ = −m_h²/v**, with *no* m_φ, m_A, m_H±, λ6, λ7,
  or tanβ dependence at all (§5).
- **EF_m2 (M22²-based) = −4·g_hφφ identically**, since `M22² = M² − m_h²/2`
  — an **exact identity at exact alignment, for ANY tanβ, any λ6, any λ7,
  any mA/mHp** (closing the prior 2026-08-31 audit's open question 2, not
  the benchmark-specific coincidence it was left as). **Corrected**
  (`validation/SOL_FINAL_REVIEW.md` D17): an earlier version of this line
  called it "a large-tanβ identity" — backwards. It is proved directly from
  2HDMC's own minimization conditions (`THDM.cpp:1134`, `THDM.cpp:2786`,
  independent of the (★) derivation above) with no tanβ expansion anywhere,
  and *numerically* it is cleanest at **small** tanβ and degrades as tanβ
  grows (residual ~7×10⁻¹²GeV² at tanβ=0.5 vs. ~8×10⁻³GeV² at tanβ=10⁵),
  through the same `get_m12_2()` conditioning issue as §5's floating-point
  artefact — the opposite of what "large-tanβ identity" would suggest.
  Domain, precisely: sin(β−α)=1 exactly; not claimed or tested for
  cos(β−α)≠0.
  and `EF_m2 ≡ 8(m_φ²−M22²)/v = 8(m_φ²−M²+m_h²/2)/v = −4·(2M²−2m_φ²−m_h²)/v = −4·g_hφφ`.
  The "~4.00×" gap this document originally left unexplained (§5, superseded
  below) is exactly the ratio of the EF prescription's prefactor (8) to the
  physical Feynman-rule prefactor (2) — **no separate physics in it.**
  Measured in `coupling_comparison/coupling_table.csv`:
  `EF_m2_over_physical_2HDM` = −4.000000000000006 / −4.0000000000000036 /
  −3.9999999999999933 at the three masses.
- **EF_simple = 8m_φ²/v is reached at M² = 5m_φ² + m_h²/2** — always,
  independent of m_A/m_H± (they cancel in (★)); whether that M² is
  theory-valid is a separate, tanβ-and-mass-dependent question (answered
  numerically to be "no" at this benchmark family in `m2_study/`).

§§1-6 below (the original derivation, largely superseded by (★) but kept
for the source-level trace it documents) still hold as written except where
noted — see the inline supersession notes.

---

Every result below is labeled: **GENERAL IDENTITY** (true for any 2HDM
point, no campaign assumption), **CONVENTION** (a sign/normalization choice,
not physics), **CAMPAIGN ASSUMPTION** (true because this project chooses it,
e.g. sin(β−α)=1, λ7=0, mA=mHp), or **NUMERICAL LIMIT** (true only in a
regime, e.g. large tanβ) / **BENCHMARK-SPECIFIC RELATION** (an empirical
coincidence of one benchmark family, not derived from the others). Source
citations are to `physical_trilinear_source_trace.md`.

---

## 1. General closed form (before any campaign assumption)

Write `s = sin(β−α)`, `c = cos(β−α)` (2HDMC's `sba`, `cba`). For neutral
CP-even states 1("h"), 2("H"), the qki matrix (source trace §2) restricted
to k∈{1,2} is real:

```
qki(1,1)=s   qki(1,2)=-c
qki(2,1)=c   qki(2,2)=s
```

`get_coupling_hhh(1,2,2)` sums 6 permutations of the multiset {1,2,2} — 3
distinct value-patterns, each occurring twice (source trace §1's sum, with
h=(1,2,2)). Substituting the qki values above into the 5-term sum for each
of the 3 patterns (h0,h1,h2) = (1,2,2), (2,1,2), (2,2,1), and adding with
multiplicity 2, all terms are real (no conjugation needed since qki(1,i),
qki(2,i) are real), giving:

```
c_hhh(1,2,2) = -i·v·[ 3sc² Z1  +  (s³−2sc²)(Z3+Z4+Z5)  +  3c(2s²−c²) Z6  −  3cs² Z7 ]
```

**DERIVED, this mission** — hand algebra, by-hand-summed all 3 permutation
patterns explicitly (shown in full in the mission transcript; reproduced
compactly here). Checked for internal consistency: `s²+c²=1` was used
nowhere in collecting terms (a good sign — the s,c powers were tracked
independently), and setting `s=1,c=0` collapses every non-`(Z3+Z4+Z5)` term
to zero, reducing to §2 below exactly, matching two independent
already-verified numbers (the audit's compiled `AuditProbe` and my separate
by-hand alignment-only derivation). **[UPDATE: now independently confirmed]**
— `test_name=general_nonaligned_coupling_formula` in
`validation/numerical_crosschecks.csv`, 25/25 PASS across 3 masses × 12
tanβ/sba combinations × degenerate-and-asymmetric mA/mHp/λ6/λ7 configurations
(fixed after `SOL_REVIEW.md` item 4 found the original run tested only 6
degenerate points due to a premature-break bug in `logs/run_all_probes.py`;
worst rel. dev. across the corrected, diverse set: 4.05×10⁻¹⁵), plus Sol's
own independent 9-point check at λ6,λ7≠0/mA≠mHp (5.1×10⁻¹⁵).

## 2. Alignment limit (CAMPAIGN ASSUMPTION: sin(β−α)=1 exactly)

Setting s=1, c=0 in §1:

```
g_hφφ ≡ |c_hhh(1,2,2)| = v·(Z3+Z4+Z5)          [CAMPAIGN ASSUMPTION applied to a GENERAL IDENTITY]
```

**NUMERICALLY CONFIRMED** by the 2026-08-31 audit's `AuditProbe` to 13
significant figures against 2HDMC's actual `get_coupling_hhh(1,2,2)` output,
independently of this derivation.

## 3. mA = mHp (CAMPAIGN ASSUMPTION) ⇒ Z4 = Z5 (GENERAL IDENTITY given that assumption)

From `get_param_higgs` (source trace §3):

```
Z4 − Z5 = lambda[4] − lambda[5]          [subtracting the two formulas — every other term cancels identically]
```

This holds for **any** β, any λ6,λ7 — it is not restricted to large tanβ or
alignment. **GENERAL IDENTITY.**

Separately, from `set_param_phys`'s own mHp formula (`THDM.cpp:1088`,
generic-basis physical-point construction): `m_Hp² = m_A² + ½v²(λ5−λ4)`.
**GENERAL IDENTITY.** So the campaign's invariant `mA = mHp` forces
`λ4 = λ5` (generic basis) **exactly**, at any tanβ, without invoking
alignment at all — which via the boxed identity above forces `Z4 = Z5`
(Higgs basis) too. This refines the earlier campaign's informal note
("mA=mHpm expressed structurally as λ4==λ5") into a proven, unconditional
statement, and extends it to the Higgs basis.

**Consequence for §2:** with Z4=Z5,

```
g_hφφ = v·(Z3 + 2·Z5)                          [CAMPAIGN ASSUMPTIONS: sba=1 AND mA=mHp]
```

## 4. Z3 in terms of masses (GENERAL IDENTITY, source trace §3)

```
Z3 = 2·(m_Hp² − M22²) / v²
```
directly from `m_Hp² = M22² + ½v²Z3` (`THDM.cpp:1137`). Substituting:

```
g_hφφ = 2·(m_Hp² − M22²)/v + 2·v·Z5
```

## 5. [SUPERSEDED BY §0] What remains open, and why the audit's independent formula is not yet re-derived here

**Resolved — see §0.** The gap identified below (why `g=v(Z3+2Z5)` and
`g=2(M22²−m_φ²)/v` must numerically agree) is now closed: both are
special cases of (★), and `M22²=M²−m_h²/2` is an *exact identity at exact
alignment for any tanβ* (§0, corrected there per `SOL_FINAL_REVIEW.md` D17
— not the "large-tanβ identity" an earlier version of this sentence called
it), not a coincidence of this benchmark. Section kept verbatim below for
the record of what was and wasn't known before the adversarial review.

The 2026-08-31 audit numerically established (14-16 sig figs, 3 masses,
`03_M2_IDENTITY_TEST.csv`) a **second**, independently-verified expression:

```
g_hφφ = 2·(M22² − m_φ²)/v          [BENCHMARK-SPECIFIC RELATION, tested only at
                                     this project's extreme-tanβ, exact-alignment,
                                     mA=mHp benchmark points]
```

Both §2/§4's formula and this one are separately confirmed to match 2HDMC's
actual `get_coupling_hhh(1,2,2)` output at the same benchmark points. They
must therefore be numerically equal there — which requires, at those points,

```
Z3 + 2Z5  =  -2(M22² − m_φ²)/v²
```

I have **not** derived this second relation from first principles (it would
require an independent Higgs-basis expression for `m_φ²` — the "H" mass —
which I attempted from generic 2HDM literature memory (hep-ph/0504050-style
`m_H² = M22² + Z5·v²` at Z6=0) but could **not** verify against any line 2HDMC
itself computes; 2HDMC obtains masses via the *generic-basis* mass matrix
(`M112,M122,M222`, `THDM.cpp:1089-1093`), not a Higgs-basis one with an
explicit `Z6=0` alignment shortcut, so that literature relation is not
directly checkable against this codebase without a further derivation this
mission does not need for its numeric conclusions.

**Disposition:** treat `g_hφφ = 2(M22²−m_φ²)/v` as **BENCHMARK-SPECIFIC
RELATION, numerically verified, algebraic origin not re-derived by this
mission** — consistent with, not contradicting, §2-§4's fully-general
result. Both are valid, verified descriptions of the same number at these
points; only §2-§4 is asserted as holding beyond this benchmark family (it
follows from GENERAL IDENTITY + explicit CAMPAIGN ASSUMPTIONS only).

## 6. [SUPERSEDED BY §0] Which parameters actually control g_hφφ (campaign regime)

**Resolved by (★), which is exact, not an approximate ranking:** only `M²`
and `m_h` appear at all; `m_φ` enters only through `M²`'s own construction
(when M² is built from masses+λ1 route); `λ6`, `λ7`, `m_A`, `m_H±` do **not
appear in (★) at all** — their absence from `g_hφφ` at this benchmark is an
**exact cancellation**, confirmed algebraically (SOL_REVIEW.md item 6: λ6's
appearance in λ345, in `3λ1cos²β`, and in the Higgs-basis rotation cancels
exactly at O(1/tanβ), not merely "too small to resolve" as an earlier
version of this section claimed from the numerical sensitivity probes
alone). `tanβ` does not appear in (★) either **once M² is held fixed** —
the earlier version of this section, and `COUPLING_STUDY_REPORT.md` §7,
read a genuine-looking ~10⁻⁸–10⁻⁹ tanβ-trend in `m2_study/sensitivity_probes.csv`;
that trend is a floating-point artefact of 2HDMC computing `cosβ` as
`cos(atan(tanβ))` (−3.6×10⁻⁹ relative error at tanβ=4×10⁷ vs the
algebraically exact `1/√(1+tanβ²)`), not real tanβ-dependence — confirmed by
the same three masses at tanβ=10 reproducing `−m_h²/v` to 10⁻¹⁵, vs. 10⁻⁸ at
tanβ=4×10⁷. λ1 has one genuine, small, exactly-predictable effect **only
through M²'s own λ1-dependence** (§0's M² identity): `∂g/∂λ1 = −2v/tan²β`,
which at tanβ=4×10⁷ predicts Δg=1.20×10⁻¹² over λ1∈[0.1,4] — matching the
measured Δg=1.14×10⁻¹² in `m2_study/sensitivity_probes.csv` to one digit.
This is resolvable, not "at or below the noise floor" as an earlier version
of the report claimed.

Original (partly superseded) discussion kept below for the source-level
detail:

```
g_hφφ = v·Z3 + 2v·Z5
```

`Z3` and `Z5` are both Higgs-basis quantities built from **all seven**
generic λ's and β via `get_param_higgs`'s formulas (source trace §3) — so
in full generality every λ_i and tanβ contributes; (★) shows that at this
campaign's specific alignment+mA=mHp assumptions, that generality collapses
to dependence on M² and m_h alone. §4's identity shows `M22²` (hence `M2`, this project's
convention, via `M22² ≈ f(M2, other campaign quantities)` — itself only
established as a benchmark-specific near-coincidence, not a general identity,
per the 2026-08-31 audit's open question 2) is one lever on `Z3`; λ6 enters
`Z3,Z5` both directly and through the `s2b·c2b·(λ6−λ7)` term, which is
**not** tanβ-suppressed the way §5 of the source trace's λ1 term is (that
term carries `s2b·c2b`, not `1/tan³β`) — so **λ6 is a priori a much more
operative parameter than λ1 at this project's tanβ**, consistent with the
mission's stated Phase-3 priority (λ6 above tanβ above λ1). This qualitative
ranking is tested quantitatively in `coupling_comparison/coupling_table.csv`.
