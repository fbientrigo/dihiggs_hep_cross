# SOL_FINAL_REVIEW — independent adversarial re-review of `physical_vs_effective_coupling_v1`

**Reviewer:** Sol (independent pass, 2026-09-03). This is a *fresh* review. I did not
take `validation/SOL_REVIEW.md` / `SOL_REVIEW_RESPONSE.md` as settled; I re-derived
every algebraic claim from `THDM.cpp` myself and re-measured every numerical claim with
my **own** probe (`SolProbe.cpp`, written this session, public-API only), not with
`GeneralProbe`.

**No file in the campaign, in `dihiggs/2hdmc`, or in `dihiggs_ufo/` was modified by this
review.** My probe source and binary live in the session scratchpad.

## Method / tooling

I wrote and compiled an independent probe against the *same* library the campaign uses
(`2hdmc_build/lib/lib2HDMC.a`; `2hdmc_build/src/THDM.cpp` is `md5 668fdf09…`, byte-identical
to canonical `dihiggs/2hdmc/src/THDM.cpp`). It differs from `GeneralProbe` in one important
way: **it reads the Higgs-basis Λ₁…Λ₇ from the library's own public
`THDM::get_param_higgs()`** rather than re-implementing the rotation, and it reconstructs
2HDMC's private `M22_2` (= Higgs-basis Y₂) from the library's own returned `m_Hp`:

```
Y2  =  mHp_from_get_param_higgs^2  -  0.5 * v^2 * Lambda3
```

which follows from `THDM.cpp:1137` (`m_Hp=sqrt(M22_2+0.5*v2*Lambda3)`). That gives a
route to Y₂ that shares no arithmetic with `GeneralProbe`'s re-derivation.

Build:
```
g++ SolProbe.cpp -Isrc -std=c++11 -O2 -L lib -l2HDMC -lgsl -lgslcblas -lm -o SolProbe
```

---

# A. Master physical coupling

## A1. Does `get_coupling_hhh(1,2,2)` reduce to `(2M² − 2m_φ² − m_h²)/v` at alignment? — **CONFIRMED**

Derived from source, not curve-fitted.

**Step 1 — the permutation sum.** `THDM.cpp:1610-1622`. At `sba=1`, `get_qki`
(`THDM.cpp:1201-1219`) gives `q(1,·)=(1,0)`, `q(2,·)=(0,1)`. Of the 5 terms in the sum,
for the multiset {1,2,2} (6 permutations = 3 patterns × 2):

| term | needs | survives? |
|---|---|---|
| `q(h0,1)q(h1,1)Re q(h2,1) Z1` | all three = state 1 | no |
| `q(h0,2)q(h1,2)Re q(h2,1)(Z3+Z4)` | pattern (2,2,1), ×2 | **yes → 2(Z3+Z4)** |
| `Re[q̄(h0,1)q(h1,2)q(h2,2) Z5]` | pattern (1,2,2), ×2 | **yes → 2 Z5** |
| `Re[(2q+q̄)(h0,1) q̄(h1,1) q(h2,2) Z6]` | two state-1 legs | no (only one 1 available) |
| `Re[q̄(h0,2)q(h1,2)q(h2,2) Z7]` | all three = state 2 | no |

With the `-I*v/2.` prefactor: **`c(1,2,2) = −i·v·(Z3+Z4+Z5)` exactly at `sba=1`.**
`Z6`/`Z7` drop out here structurally, not numerically.

**Step 2 — Higgs-basis mass relations.** `get_param_higgs` (`THDM.cpp:1105-1138`)
computes `M22_2 = m11_2*sb² + m22_2*cb² + m12_2*sin2β` — this is the standard Higgs-basis
`Y₂`. With `m_{H±}² = Y₂ + ½v²Λ₃` (the library's own line 1137) and the standard
hep-ph/0504050 relations, the (2,2) entry of the CP-even mass matrix in the Higgs basis is
`Y₂ + ½(Z3+Z4+Z5)v²`, which at `Λ₆=0` *is* `m_φ²`. Hence
`Z3+Z4+Z5 = 2(m_φ² − Y₂)/v²`.

**Step 3 — `Y₂ = M² − m_h²/2` (proved in D17 below, exactly, at alignment).** Substituting:

```
c(1,2,2) = −i·2(m_φ² − M² + m_h²/2)/v   ⟹   Im[c] = (2M² − 2m_φ² − m_h²)/v      (★)
```

**Independent measurement** (my probe, well-conditioned points; `star_pred` computed from
`m12²/(sinβcosβ)` of the *input*, `g` from an actual `get_coupling_hhh(1,2,2)` call):

| point | g (measured) | (★) | rel. dev. |
|---|---|---|---|
| mφ=250, tanβ=10, M²=62500, λ6=λ7=0 | −63.4593610874836 | −63.459361087483451 | 2.2e-15 |
| mφ=260, tanβ=7, mA=340≠mHp=320, M²=54080 | −173.27959301103874 | −173.27959301103886 | 6.6e-16 |
| mφ=260, tanβ=3, λ6=0.05, λ7=0.02 | −173.27959301103871 | −173.2795930110388 | 4.9e-16 |
| mφ=260, tanβ=0.5, M²=54080 | −173.27959301103871 | −173.27959301103886 | 8.2e-16 |

**Caveat that the report's headline does not carry:** at the *actual benchmark*
(tanβ=4×10⁷) (★) holds only to **7.4×10⁻⁹**, not machine precision
(−63.459361555950252 measured vs −63.459361089658486 predicted at mφ=250). §5 of the
report correctly identifies this as floating point; but §0/§"master result" says "verified
… to machine precision", which is true only away from the benchmark. See E21/E22.

## A2. Sign convention and "index 1 = SM-like" — **CONFIRMED**

- `get_cba()` (`THDM.cpp:2828-2831`) returns `+sqrt(1-sba²)` — **always the non-negative
  root**, discarding the sign of cos(β−α). At exact alignment `cba=0`, so (★) is unaffected;
  the campaign's own "unresolved question 3" correctly scopes everything to the `cba≥0`
  branch. Confirmed at source level.
- At `sba=1`, `q(1,1)=1` ⟹ index 1 *is* the Higgs-basis H₁ direction, i.e. the SM-like
  state. Verified independently: `get_coupling_hhh(1,1,1) = −190.37808326245033 i` at every
  aligned point I ran = exactly `−3i·m_h²/v` (the SM value) — the signature of the SM-like
  state.
- Sign of (★): measured `Im[c] < 0` at all three benchmarks, and (★) predicts
  `−m_h²/v < 0`. Consistent.
- **Note (convention, not error):** `g_hφφ ≡ Im[c]` is *not* the conventional Lagrangian
  coupling. With `L ⊃ −(κ/2)hφ²` the vertex is `−iκ`, so `κ = −Im[c] = +63.46 GeV`. The
  campaign uses `Im[c]` consistently and hands that same convention to the UFO
  (`GC_90 = i·GHphiphi`), so the handoff is self-consistent. Anyone quoting "the trilinear
  coupling is negative" outside this campaign must carry the convention with it.

## A3. Normalization directly comparable to `GC_90`? — **CONFIRMED**

Redone by me, not read off `ufo/validation.md`.

- UFO `GC_94 = '-6*complex(0,1)*lam*vev'`, `lam = MH**2/(2.*vev**2)` ⟹ `GC_94 = −3i·MH²/vev`.
- UFO `vev = (2*MW*sw)/ee`; evaluating the UFO's own EW inputs
  (`aEWM1=127.9, Gf=1.16637e-5, MZ=91.1876`) gives **vev = 246.2205690734859**, vs 2HDMC's
  `sm.get_v() = 246.22056907348588` — **relative difference 1.15×10⁻¹⁶**. Same scheme.
- Numerically: `GC_94 = −190.37808326245033 i`. My probe's
  `get_coupling_hhh(1,1,1) = −190.37808326245033 i`. **Digit-for-digit identical.**

So `GC_90` and `get_coupling_hhh(1,2,2)` are unit-for-unit comparable. CONFIRMED.

## A4. Hidden identical-particle (2!) factor or convention mismatch? — **CONFIRMED (none)**

A3 anchors the *three*-identical-scalar case. The *two*-identical case is anchored
separately: UFO `GC_93 = '-2*complex(0,1)*lam*vev' = −i·MH²/vev`, used on
`V_8 = [G0, G0, H]`. The SM Lagrangian term `−(m_h²/2v) h G0²` gives the Feynman rule
`i·(−m_h²/2v)·2! = −i m_h²/v` — matching `GC_93` exactly. So in *both* UFO and 2HDMC the
stored number is the **full Feynman rule with all combinatorial factors already in it**.
No hidden factor 2 in either direction.

## A5. Do m_A and m_H± cancel? — **CONFIRMED (exact, analytic)**

Summing `set_param_phys`'s own lines (`THDM.cpp:352-356`):

```
λ3+λ4+λ5 = [ (m_H²−m_h²)·ca·sa + m12² ] / (v² sβ cβ) − 1.5λ6/tβ − 1.5λ7·tβ
```
Every `m_A²` and `m_Hp²` term cancels *identically* in the sum (the `+2m_Hp²sc` in λ3,
`−2m_Hp²sc + m_A²sc` in λ4, `−m_A²sc` in λ5). At alignment `ca·sa = −sβcβ`, giving
`λ345 = (m_h² − m_φ² + M²)/v² − 1.5λ6/tanβ − 1.5λ7 tanβ` — the report's §0 expression,
confirmed term-by-term.

Independent numeric check at fixed M²=54080, mφ=260, tanβ=3:

| mA, mHp | g |
|---|---|
| 300, 300 | −173.27959301103874 |
| 340, 320 | −173.27959301103871 |
| 500, 200 | −173.27959301103863 |
| 900, 150 | −173.2795930110392 |
| 150, 900 | −173.27959301103891 |

Spread 6×10⁻¹³ absolute (2×10⁻¹⁵ relative) over a 750 GeV mA swing. Exact cancellation.

## A6. Do λ6 and λ7 drop out at fixed M²? — **CONFIRMED (exact, not just at λ6=λ7=0)**

I proved this analytically (see D17: the λ6/λ7 pieces cancel identically at alignment via
`c3β+cβ−2cβc2β ≡ 0` and `sβ+2sβc2β−s3β ≡ 0`), and measured it at fixed
M²=54080, mφ=260, tanβ=3, mA=340, mHp=320:

| λ6 | λ7 | g |
|---|---|---|
| 0 | 0 | −173.27959301103871 |
| 0.05 | 0.02 | −173.27959301103871 |
| −0.30 | 0.40 | −173.27959301103874 |
| 1.00 | −1.00 | −173.27959301103866 |
| 2.00 | 0.50 | −173.27959301103877 |

Invariant to 6×10⁻¹⁶ relative across λ6,λ7 ∈ [−1, 2]. This is far outside the benchmark's
λ6 ≈ 1.18e-4, so it is a genuine test, not an extrapolation.

## A7. Is (★) independent of tanβ at fixed M²? — **CONFIRMED**

Fixed M²=54080, mφ=260, mA=340, mHp=320, λ6=λ7=0, alignment:

| tanβ | g | rel. dev. from (★) |
|---|---|---|
| 0.5 | −173.27959301103871 | −8.2e-16 |
| 1 | −173.27959301103883 | +1.6e-16 |
| 3 | −173.27959301103871 | −4.9e-16 |
| 10 | −173.27959301103905 | +1.5e-15 |
| 50 | −173.27959301103951 | +4.1e-15 |
| 10³ | −173.27959301105173 | +7.4e-14 |
| 10⁵ | −173.27959301233136 | +7.5e-12 |

No alignment-limit expansion is involved — the derivation in A1 is exact algebra at
`sba=1`. The visible drift above tanβ≈10³ is *conditioning*, not tanβ-dependence (see E21).

---

# B. Why M² ≈ m_φ²

## B8. The λ1/M² identity — **CONFIRMED (exactly; I re-derived it)**

From `set_param_phys` (`THDM.cpp:352`):
`λ1 = (m_H²ca² + m_h²sa² − m12²·tβ)/(v²cβ²) − 1.5λ6 tβ + 0.5λ7 tβ³`.
At alignment `ca=sβ`, `sa=−cβ`, and `m12² = M²·sβcβ` so `m12²tβ = M²sβ²`:

```
λ1 = [ sβ²(m_φ² − M²) + m_h² cβ² ] / (v²cβ²) − 1.5λ6 tβ + 0.5λ7 tβ³
   = (m_φ² − M²)·tan²β/v²  +  m_h²/v²  − 1.5λ6 tanβ + 0.5λ7 tan³β
```
Solving for M²:
```
M² = m_φ² + (m_h² − v²λ1)/tan²β − 1.5·v²λ6/tanβ + 0.5·v²λ7·tanβ          ✔ = report §3
```
Numerically verified: benchmark (mφ=250, λ1=1, λ6=1.177689207010651e-4, tanβ=4e7)
⟹ formula gives **62499.99999973223**; the m12² that `set_param_phys_lam1` actually
constructs gives `M² = 62499.99999973223`. Exact.

> **BUT — report §4 / `assumptions_and_limits.md` §4 line 110 states the *inverse* wrongly:**
> ```
> λ1 = (m_φ² − M²)/(v²cos²β) − 1.5·λ6·tanβ + 0.5·λ7·tan³β        ← WRONG
> ```
> Two errors: (i) the `+ m_h²/v²` term (= 0.2577, i.e. 2% of the 4π perturbativity budget)
> is **missing**; (ii) `1/(v²cos²β)` should be `tan²β/v²` (they differ by a factor
> `1+cot²β`, harmless at tanβ=4e7, wrong by 4% at tanβ=5). Smallest correction: restore the
> line above from B8. The numerical conclusions of §4 survive (the shift is
> `m_h²/tan²β ≈ 1×10⁻¹¹ GeV²`, inside the quoted window), but the formula as printed is not
> the inverse of §3's, which is the whole point of printing it.

## B9. Is M²≈m_φ² *genuinely forced*, or an artifact of a narrow slice? — **CONDITIONAL**

**Condition: it is forced *only* if λ7 ≡ 0 exactly.** I constructed an explicit
counterexample that the campaign did not:

```
SolProbe lam1  mh=125  mφ=250  mA=300  mHp=300  sba=1  λ1=1  λ6=0  λ7=-1.0309278350515464e-08  tanβ=4e7
→ construction_ok=1
→ M² = 50000.0889  =  0.80000142 · m_φ²        (20% away from m_φ²)
→ g_hφφ = −164.99361721019517  (not −63.46)
→ generic λ = (1, 0.2577, 1.5773, −0.4536, −0.4536, 0, −1.03e-8)
→ Higgs basis Λ = (0.2577, 1.0, 1.5773, −0.4536, −0.4536, ~5e-17, −8.2e-9)
→ unitarity=1  perturbativity=1  stability=1  positivity=1     ← ALL FOUR PASS
```
A second point at λ7 = −5.15e-9 gives M² = 56255.67 (= 0.90 m_φ²), also all-four-valid.

λ7 = 10⁻⁸ is not an exotic choice — it is numerically indistinguishable from zero in every
other observable, and nothing in the model *requires* λ7=0; it is a campaign input
convention. So "M²=m_φ² is forced by perturbativity" is **a statement about the λ7=0
slice**, not about 2HDM parameter space at tanβ=4×10⁷.

The report *does* carry the hedge ("it *is* still contingent on λ7=0"), which is why this
is CONDITIONAL rather than WRONG — but the §4 headline ("**Required — forced by
perturbativity, route-independently, not optional**") and the (★) framing ("holds for any
λ7") are read together as a much stronger claim than the evidence supports. Smallest
correction: move the λ7 caveat from the last sentence of §4 into the §4 headline, and cite
a concrete counterexample point (the one above is free).

Within λ7=0, the forcing is real: λ6 cannot move the destination materially
(`ΔM² = −1.5v²λ6/tanβ = −2.27×10⁻³·λ6` — you would need λ6 ≈ −2.8×10⁵ to move M² by 1%),
and λ1 is the only lever, with the 1/(v²cos²β)-scale amplification.

## B10. Is ~10⁻¹⁴ relative the right window width? — **CONDITIONAL**

Order of magnitude CONFIRMED; **the stated `±4.8×10⁻¹⁰ GeV²` symmetry is wrong.** I scanned
M² around the exact forced value `M²* = 62499.99999973223` (mφ=250, tanβ=4e7, λ6 =
1.1777e-4, λ7=0), masses+m12² (`set_param_phys`) route:

| ΔM² (GeV²) | λ1_out | u / p / s / po |
|---|---|---|
| −1e-9 | +27.33 | 0 0 1 1 |
| −4.8e-10 | +13.69 | 1 **0** 1 1 |
| −1e-10 | +3.71 | 1 1 1 1 |
| −1e-11 | +1.213 | 1 1 1 1 |
| 0 | +1.021 | 1 1 1 1 |
| +1e-11 | +0.829 | 1 1 1 1 |
| +1e-10 | −1.667 | 1 1 **0 0** |
| +4.8e-10 | −11.65 | 1 0 0 0 |

The **upper** edge is set by **vacuum stability (λ1 > 0)**, not perturbativity, and sits at
`ΔM² = +λ1(0)·v²/tan²β ≈ +3.9×10⁻¹¹ GeV²` — about **12× tighter** than the quoted
±4.8×10⁻¹⁰. The lower edge is set by perturbativity at `−4.8×10⁻¹⁰`. So the true window is
asymmetric, `ΔM² ∈ (−4.8×10⁻¹⁰, +3.9×10⁻¹¹)` GeV², total width ≈ 5.2×10⁻¹⁰ GeV²
≈ 8×10⁻¹⁵ relative. Smallest correction: replace "`|λ1| ≲ 4π`" with "`0 < λ1 ≲ 4π`" and
quote the one-sided window.

## B11. Route-independence — **CONFIRMED**

Directly tested with `set_param_phys` (masses+m12² direct, **not** `_lam1`), at
tanβ=4×10⁷, mφ=250, m12² = M²*·sinβcosβ:

```
construction_ok=1, λ1_out = 1.0211950364309814,
unitarity=1 perturbativity=1 stability=1 positivity=1
```
So the m12²-direct route reaches a fully theory-valid point at this tanβ. The forcing is a
property of the physical point, not of which setter was called. CONFIRMED — this also
independently reproduces the report's §6a `exact_via_star_identity_lambda1eq1` row.

## B12. Genuine restriction vs floating-point noise in 2HDMC's own checks — **CONFIRMED (genuine), with a quantified fuzz**

The invalid verdicts are real, not noise:
- At `ΔM² = ±2.677×10⁻⁷` (the naive `M²=m_φ²` grid point) `λ1_out = ∓7065` — five orders
  of magnitude beyond any plausible noise. `check_perturbativity` operates on the λ's, so
  the verdict is well-determined.
- The floating-point *quantum* of λ1 at this tanβ is measurable: stepping M² by 1e-12 GeV²
  changes λ1_out not at all; stepping by 1e-11 changes it by 0.19. So λ1 carries ≈ ±0.2
  absolute fp granularity — **1.6% of the 4π budget**, i.e. the *edges* of the valid window
  are fuzzy at the ~±8×10⁻¹² GeV² level (≈2% of the window width). Everything more than a
  few window-widths away is unambiguous.

Verdict: the "0/21 theory-valid" result in `m2_variation.csv` is physics, not noise.

---

# C. EF_simple

## C13. Does `g = 8m_φ²/v` imply `M² = 5m_φ² + m_h²/2`? — **CONFIRMED**

`(2M² − 2m_φ² − m_h²)/v = 8m_φ²/v ⟹ 2M² = 10m_φ² + m_h² ⟹ M² = 5m_φ² + m_h²/2`. At
mφ=250: M² = 320312.5. Measured directly (my probe, tanβ=10):
`c(1,2,2) = +2030.6995547994707 i`, vs `8·250²/v = 2030.6995547994704`. Agreement to the
last digit.

## C14. Is that mapping actually shown theory-invalid? — **CONFIRMED (in the tested region)**

Same run: `λ1 = −425.003`, `unitarity=0 perturbativity=0 stability=0 positivity=0`. All
four fail, not merely one. Demonstrated, not asserted.

## C15. Is a claim stronger than the tested region being made? — **CONDITIONAL**

Report §8 says: *"EF_simple's magnitude is reachable in the M² coordinate at any tanβ, and
is **excluded by perturbativity, full stop**"*. Two problems and one under-claim:

1. **The stated mechanism is wrong.** The unavoidable obstruction is **vacuum stability**,
   not perturbativity. Proof (alignment, λ6=λ7=0, from B8 and the analogous λ2 line
   `THDM.cpp:353`), writing `X ≡ (M²−m_φ²)/v² = (4m_φ² + m_h²/2)/v²` and `Y ≡ m_h²/v²`:
   ```
   λ1 = Y − X·tan²β ,      λ2 = Y − X/tan²β
   ```
   Stability requires λ1>0 **and** λ2>0 ⟹ `tan²β < Y/X` **and** `tan²β > X/Y` ⟹ `X < Y`
   ⟹ `4m_φ² + m_h²/2 < m_h²` ⟹ **m_φ < 62.5 GeV**. Since 2HDMC's index-2 state is by
   construction the heavier one (m_φ > m_h = 125), EF_simple is **impossible at exact
   alignment with λ6=λ7=0, for every tanβ and every mass** — a *stronger and cleaner*
   result than the report proves, obtained by the *wrong* named mechanism in the report.
2. **The "full stop" over-reaches on scope.** With λ6, λ7 free the algebra above no longer
   closes analytically. I ran a **4000-point randomized scan** (m_φ ∈ [126,1000],
   mA, mHp ∈ [1,1500], tanβ ∈ [0.05,20], λ6, λ7 ∈ [−8,8], M² pinned to 5m_φ²+m_h²/2,
   alignment): **0 points passed all four checks**; the best partial was 2/4. That is strong
   but not a proof, and the whole scan is at exact alignment — the `sin(β−α)≠1` region is
   untested and (★) does not apply there.

Smallest correction: replace "excluded by perturbativity, full stop" with "excluded by
vacuum stability (λ1>0 and λ2>0 cannot hold simultaneously for m_φ > 62.5 GeV) at exact
alignment with λ6=λ7=0, for any tanβ; empirically excluded (0/4000 random points) with λ6,
λ7 free; untested away from alignment."

---

# D. EF_m2

## D16. What is `m₂²`/`M22_2`, and is it public? — **CONFIRMED (not public; reconstruction is legitimate)**

- `THDM::m22_2` is `private` (`THDM.h:899`).
- `M22_2` inside `get_param_higgs` (`THDM.cpp:1135`) is a **function-local**, never returned.
- So the campaign must reconstruct it. `GeneralProbe.cpp:255-258` does so by replaying
  `THDM.cpp:1133-1135` on public outputs. That is honest and correctly documented in the
  probe's own comments.
- **I reconstructed it a different way** — `Y2 = mHp_from_get_param_higgs² − ½v²Λ3`, from
  `THDM.cpp:1137` — sharing no arithmetic with the campaign's route, and got the same value
  at every well-conditioned point (see D17 table). The identification `M22_2 ≡ Y₂` (the
  Higgs-basis mass parameter) is correct.

## D17. Under what assumptions is `M22² = M² − m_h²/2`? — **CONFIRMED, but the report's stated domain is WRONG**

**Report §9 and `derivation/…§0` call this "a large-tanβ identity at alignment". It is not.
It is EXACT at exact alignment, for ANY tanβ, ANY λ6, ANY λ7, ANY mA/mHp.**

*Proof.* Using the two minimization conditions 2HDMC itself encodes
(`THDM.cpp:1134` for m11², `THDM.cpp:2786` inverted for m22²),
```
Y2 = m11²sβ² + m22²cβ² + m12²sin2β
   = m12²·[ (sβ⁴+cβ⁴)/(sβcβ) + 2sβcβ ] − ½v²·X = M² − ½v²·X
```
(the bracket collapses to `1/(sβcβ)` since `sβ⁴+cβ⁴+2sβ²cβ² = 1`), with
```
X = (λ1+λ2)sβ²cβ² + λ345(sβ⁴+cβ⁴) + λ6(3sβ³cβ + cβ⁵/sβ) + λ7(sβ⁵/cβ + 3sβcβ³).
```
The claim is `X = Λ1` (the Higgs-basis Z1, `THDM.cpp:1125`), since `m_h² = Λ1 v²` at
alignment. Forming `D ≡ X − Λ1` and simplifying:
```
D = −c2β[λ1cβ² − λ2sβ² − λ345c2β] − λ6·cβ·c2β(1−2c2β)/sβ + λ7·sβ·c2β(1+2c2β)/cβ
```
Alignment ⟺ `Λ6 = 0` (`THDM.cpp:1130`), which gives
`λ1cβ² − λ2sβ² − λ345c2β = 2(cβc3βλ6 + sβs3βλ7)/sin2β`. Substituting:
```
D = −(c2β λ6/sβ)[c3β + cβ − 2cβc2β] + (c2β λ7/cβ)[sβ + 2sβc2β − s3β]
```
and **both brackets vanish identically** (`c3β+cβ ≡ 2c2βcβ`, `s3β−sβ ≡ 2c2βsβ`).
Therefore `D = 0` ⟹ **`Y2 = M² − m_h²/2` exactly at alignment, with no tanβ or λ6/λ7
assumption.** ∎

Measured (`Y2` from the library's own `get_param_higgs` m_Hp; `M² − m_h²/2` from the input
m12²):

| point | Y2 − (M² − m_h²/2) [GeV²] |
|---|---|
| mφ=260, tanβ=0.5, λ6=λ7=0 | +7.3e-12 |
| mφ=260, tanβ=1 | −2.2e-11 |
| mφ=260, tanβ=3, λ6=0.05, λ7=0.02 | +7.3e-12 |
| mφ=260, tanβ=3, λ6=−0.30, λ7=+0.40 | 0.0 |
| mφ=260, tanβ=3, λ6=+2.0, λ7=+0.5 | −2.2e-11 |
| mφ=250, tanβ=10 | −1.2e-10 |
| mφ=260, tanβ=10³ | −5.4e-07 |
| mφ=260, tanβ=10⁵ | −8.0e-03 |

Note the direction: the identity is *cleanest at small tanβ and degrades monotonically as
tanβ grows* — the exact opposite of "large-tanβ identity". Smallest correction: change
"a large-tanβ identity at alignment" to "an exact identity at exact alignment (any tanβ,
λ6, λ7, mA, mH±); numerically it degrades above tanβ≈10³ through `get_m12_2()` conditioning."

## D18. Under what assumptions is `EF_m2 = −4·g_hφφ`? — **CONDITIONAL**

Exact, given: (i) **exact alignment** (Λ6=0), and (ii) `M²` and `M22²` taken as the same
self-consistent point's values. Then, by D17 and (★),
`EF_m2 ≡ 8(m_φ²−M22²)/v = 8(m_φ²−M²+m_h²/2)/v = −4·(2M²−2m_φ²−m_h²)/v = −4·g`.
No tanβ, λ6, λ7, mA or mHp assumption is needed — so it is *more* general than §9 states.

Independently measured at a point the campaign never used
(mφ=260, tanβ=3, λ6=0.05, λ7=0.02, mA=340, mHp=320, M²=54080):
`Y2 = 46267.500000000007`, `EF_m2 = 8(67600−46267.5)/246.22057 = 693.11837`,
`−4g = −4·(−173.27959301) = 693.11837`. Exact.

It is **not** general away from alignment (there `c(1,2,2)` picks up Z1, Z6, Z7 pieces and
Λ6≠0 breaks the D=0 cancellation).

## D19. Actual domain, stated precisely — **CONFIRMED (with the corrected domain)**

> `EF_m2 = −4·g_hφφ` holds **exactly whenever sin(β−α) = 1 exactly** (equivalently Λ6 = 0),
> for arbitrary tanβ, λ6, λ7, m_A, m_H±, m_φ, and arbitrary M² — provided `M22²` is the
> Higgs-basis Y₂ of the *same* point and `M² ≡ m12²/(sinβcosβ)` of the *same* point.
> It is **not** claimed and **not** tested for cos(β−α) ≠ 0.

The report's stated domain ("large-tanβ identity") is both too narrow (it holds at tanβ=0.5)
and misleading (numerical quality is *worst* at large tanβ). Hence WRONG-as-stated, correct
as an identity — I grade D17/D19 on the identity itself (CONFIRMED) and flag the domain
statement as the required correction.

## D20. Is project `M²` conflated with EF_m2's `m₂²`? — **CONFIRMED (no conflation)**

`logs/run_all_probes.py:429-445` reads `M22_2_Y2_candidate_GeV2` for `EF_m2_GeV` and
`M2_actual_GeV2` separately for `EF_m2_using_M2_GeV`; the two are distinct columns with
distinct names throughout `coupling_table.csv`, and the CSV carries an explicit
`m2_definition_used` column. `derivation/` and `COUPLING_STUDY_REPORT.md` §9 keep them
lexically distinct (`M2` vs `M22²`). No instance of substitution found. (Cosmetically, `M2`
and `M22²` differing by one character in a document that also uses `m₂²` is a readability
hazard, but no actual conflation is present.)

---

# E. Numerics

## E21. Is tanβ = 4×10⁷ inside double-precision safety margins? — **NUMERICALLY_UNSTABLE**

It is not, and the campaign under-states how far outside it is. Three separate failures,
only two of which the campaign names:

1. **`cos(atan(tanβ))`**, −3.6×10⁻⁹ relative (E22) — named by the campaign.
2. **`get_m12_2()`**, −4.54% (E23) — named by the campaign.
3. **`set_param_phys`'s own λ1 reconstruction** — *not named anywhere*. Line 352 forms
   `(m_H²ca² + m_h²sa² − m12²tβ)` — a difference of two numbers of size ~6×10⁴ whose true
   value is ~4×10⁻¹¹ — then divides by `v²cβ² = 3.79×10⁻¹¹`. Catastrophic cancellation:
   ULP(62500) = 7.3×10⁻¹² ⟹ **λ1 carries ≈ ±0.2 absolute floating-point granularity**.
   Observed directly: `set_param_phys_lam1` with λ1_in = 1.0 emits
   `WARNING: … lambda_1 round-trip abs error = 0.021195` and stores λ1 = 1.0211950364,
   and across the three benchmark masses the *same* λ1=1 input yields stored
   λ1 = 1.0211950 / 1.0211950 / **1.5972750**. λ1 is not reproducible to better than ~0.6
   at this tanβ.

**And the consequence the campaign has not flagged (see Additional issue #3): at
tanβ=4×10⁷, 2HDMC's own reconstructed physical masses are wrong by 1.5–4.6%.** My probe,
benchmark λ1-route points:

| requested m_φ | `get_hmass(2)` returns | error | requested mA=mHp=300 → returns |
|---|---|---|---|
| 200 | 190.73486397 | −4.6% | 285.4 (from Λ) |
| 250 | 244.25980609 | −2.3% | 295.23355648 |
| 300 | 295.48518068 | −1.5% | ~298 |

`get_hmass` → `get_param_phys` → `get_m12_2()` (`THDM.cpp:2809-2816`), so it inherits the
4.5% error. The *coupling* is safe (`get_coupling_hhh` depends only on `lambda[1..7]` and β,
never on `get_m12_2()`), but everything mass-dependent downstream is not.

## E22. Is `cosβ = cos(atan(tanβ))` and does it carry −3.6×10⁻⁹? — **CONFIRMED**

Source: `THDM.cpp:337` `beta=atan(tan_beta);` then `:339 sin(beta)`, `:341 cos(beta)`. The
algebraically exact form `cb = 1./sqrt(1.+tan_beta*tan_beta)` exists in the file but is
**commented out** at `THDM.cpp:390-391` with a note preferring the `atan/cos` route.

Measured at tanβ = 40000000.00000001:
```
cos(atan(tb))     = 2.4999999909295562e-08
1/sqrt(1+tb²)     = 2.4999999999999986e-08
relative error    = -3.6281769558021319e-09      ← matches the report's −3.6e-9 exactly
```
Mechanism: `atan(x)→π/2−1/x`; rounding `atan` to a double near π/2 costs ~2.2×10⁻¹⁶
absolute, and `cos` has unit slope there, so `δcβ/cβ ≈ 2.2×10⁻¹⁶·tanβ` — **linear in tanβ**.
That predicts the campaign's own `sensitivity_probes.csv` tanβ sweep exactly: the g residual
there is 1.17e-9 / 1.17e-8 / 1.17e-7 / 4.66e-7 at tanβ = 10⁵/10⁶/10⁷/4×10⁷ — perfectly
linear. And at the benchmark the g residual is 7.39×10⁻⁹ relative = **2.04 × the cβ error**.
The report's diagnosis is right, and its decisive discriminator (tanβ=10 reproduces −m_h²/v
to 10⁻¹⁵) I reproduced independently: −63.4593610874836 vs −63.459361087483451.

## E23. `get_m12_2()` round-trip at tanβ=4×10⁷ — **NUMERICALLY_UNSTABLE (campaign's ~4.5% CONFIRMED)**

Measured directly (mφ=250, λ1-route):
```
m12² implied by the λ1 input : 0.0015624999943242778
get_param_gen()/get_m12_2()  : 0.0014915713163192873
relative error               : −4.539 %
```
Root cause, from `THDM.cpp:2786`: `m12² = (m22_2 + ½v²(…))·tanβ` — the bracket must come out
to ≈3.7×10⁻¹¹ from a sum of terms each O(10⁴). That is a 15-digit cancellation; double
precision has ~16. A −4.5% error is exactly the expected magnitude
(10⁴·2.2×10⁻¹⁶ / 3.7×10⁻¹¹ ≈ 6%). This is a genuine 2HDMC limitation, not a campaign error,
and the campaign flags it — but only as "the `m12_2_out` columns are unusable", which
under-states the blast radius (E21 item 3, Additional issue #3).

## E24. Independent recomputation of four required points — **CONFIRMED**

All from my own `SolProbe`, not from any campaign CSV.

**(a) Benchmark, tanβ = 4×10⁷, λ1-route (λ1=1, λ6=1.177689207010651e-4, λ7=0, mA=mHp=300):**

| m_φ | `Im[get_coupling_hhh(1,2,2)]` | (★) prediction | rel. dev. | theory |
|---|---|---|---|---|
| 200 | **−63.459361332129987** | −63.459361089658486 | 3.8e-9 | 1/1/1/1 |
| 250 | **−63.459361555950252** | −63.459361089658486 | 7.3e-9 | 1/1/1/1 |
| 300 | **−63.459361829508119** | −63.459361089658373 | 1.2e-8 | 1/1/1/1 |

These reproduce `coupling_comparison/coupling_table.csv`'s `physical_2HDM_GeV` column
digit-for-digit. **They do NOT match (★) to machine precision** — the 10⁻⁸–10⁻⁹ residual is
the E22 artefact.

**(b) Moderate tanβ = 10** (mφ=250, M²=62500, λ6=λ7=0, mA=mHp=300):
`g = −63.4593610874836` vs (★) `−63.459361087483451` — **rel. dev. 2.2×10⁻¹⁵**. Machine
precision. All four theory checks = 1.

**(c) Asymmetric mA ≠ mHp** (mφ=260, mA=340, mHp=320, tanβ=7, M²=54080):
`g = −173.27959301103874` vs (★) `−173.27959301103886` — **6.6×10⁻¹⁶**.

**(d) λ6, λ7 explicitly non-benchmark** (mφ=260, mA=340, mHp=320, tanβ=3, M²=54080,
λ6=+2.0, λ7=+0.5 — four orders of magnitude above the benchmark's λ6):
`g = −173.27959301103877` vs (★) `−173.2795930110388` — **1.6×10⁻¹⁶**.

Conclusion: **(★) is exact to machine precision everywhere the arithmetic is conditioned,
and fails only at tanβ ≳ 10³ for floating-point reasons.**

---

# F. UFO

## F25. Is the frozen original untouched? — **CONFIRMED**

I unzipped `dihiggs_ufo/LLscalar_v3_UFO.zip` (mtime 2021-08-19) in memory and byte-compared
**all 14 `.py` files** against `dihiggs_ufo/LLscalar_v3_UFO_original/`:
`couplings.py, write_param_card.py, coupling_orders.py, CT_couplings.py, form_factors.py,
__init__.py, propagators.py, function_library.py, lorentz.py, particles.py,
object_library.py, parameters.py, decays.py, vertices.py` — **0 differences**. Only
non-source artefacts (`*.pyc`, `model.pkl`, `*~`) exist outside the archive, as
`ufo/validation.md` §1 states.

## F26. Does the externalized copy differ only where intended? — **CONFIRMED**

`diff -rq` original vs `ufo/LLscalar_v3_UFO_GHphiphi_external/`: exactly two source files
differ — `couplings.py` and `parameters.py`. `vertices.py` is byte-identical (V_7 still
references `C.GC_90` by name). The only other deltas are generated caches (`__pycache__`
`cpython-313` entries created by the campaign's import smoke test) and the deliberately
removed `*.pyc`/`model.pkl`/`*~`. Full diff reviewed line-by-line: the `GC_90` value line,
one commented-out copy of the old value, and one new `Parameter` block. Nothing else.

**Extra check the campaign did not do:** `lhacode` collision. The only pre-existing
`FRBlock` parameter is `ctauh2` with `lhacode = [2]` (`parameters.py:126-132`); `GHphiphi`
takes `[3]`. **No collision.**

## F27. Is the coupling expression exactly `i·GHphiphi`? — **CONFIRMED**

Read directly:
```python
GC_90 = Coupling(name = 'GC_90',
                 value = 'complex(0,1)*GHphiphi',
                 order = {'QED':-1})
```
and `GHphiphi = Parameter(… nature='external', type='real',
value = -63.459361555950252, lhablock='FRBlock', lhacode=[3])`.

## F28. Sign relation between the frozen `EF_simple` and the physical coupling — **CONFIRMED (opposite)**

Frozen: `GC_90 = '8*complex(0,1)*Mh2**2/vev'` ⟹ at Mh2=250, `+2030.6995547994704 i` —
**positive** imaginary. Physical: `Im[c] = −63.4593615…` at every benchmark point I ran —
**negative** imaginary. Opposite sign, confirmed independently of the campaign's claim.

**Provenance note the campaign records but does not weigh:** the pristine 2021 LLscalar
model's `GC_90` was `'2*complex(0,1)*vev'`, still present commented out at
`couplings.py:368-370`. So `8i·Mh2²/vev` is itself an undocumented hand-edit to the archived
model, with no derivation anywhere in the repository. That is worth stating explicitly next
to "it is literally what generated Christopher's quoted cross sections".

## F29. Independent UFO/2HDMC normalization cross-check via `GC_94` — **CONFIRMED**

Redone by me from scratch (see A3): UFO `GC_94 = −3i·MH²/vev = −190.37808326245033 i`
(computing `vev` from the UFO's own aEWM1/Gf/MZ), vs my probe's
`get_coupling_hhh(1,1,1) = −190.37808326245033 i`. Identical to the last printed digit, and
`vev`/`v` agree to 1.15×10⁻¹⁶. I additionally anchored the *two*-identical-scalar case via
`GC_93` (A4), which `ufo/validation.md` §3 does not do.

---

# Additional issues found (not covered by items 1–29)

### #1 — `GeneralProbe.cpp:234` has the general-formula sign flipped, and the validation harness hides it

`COUPLING_STUDY_REPORT.md` §1's general (non-aligned) closed form is **correct** — I verified
it independently at a non-aligned point (mφ=150, mA=340, mHp=320, sba=0.9, λ6=0.05,
λ7=−0.03, tanβ=1, m12²=5625), evaluating the bracket from the library's own
`get_param_higgs` outputs:
```
−v·[bracket] = −122.89141362634948      ← matches get_coupling_hhh = −122.89141362634945
+v·[bracket] = +122.89141362634948      ← what GeneralProbe.cpp:234 computes
```
But `GeneralProbe.cpp:234-237` defines `g_general_formula = +v*(…)`, i.e. the negative of
`Im[c]`, and `logs/run_all_probes.py:88-91` scores the test as PASS on
`min(|g−g_gen|, |g+g_gen|)`. The CSV `note` column records `matches(-g_general_formula)`, so
it is disclosed — but §1's "**Confirmed to 4.05×10⁻¹⁵ relative** across 25 diverse points"
reads as a validation of the printed formula *including its sign*, which the harness cannot
provide. Smallest fix: negate line 234 and drop the ±-tolerant comparison, or state in §1
that only the magnitude is machine-checked.

### #2 — §4's λ1 inversion is not the inverse of §3's identity

See B8. Missing `+ m_h²/v²`; `1/(v²cos²β)` should be `tan²β/v²`.

### #3 — At tanβ=4×10⁷, 2HDMC's own masses (and therefore every width/ctau in this campaign's CSVs) are wrong by 1.5–4.6%

The campaign flags `get_m12_2()`'s 4.5% error as affecting "the `m12_2_out` columns". It does
much more than that. `get_hmass()` (`THDM.cpp:2809-2816`) routes through `get_param_phys()`
→ `get_m12_2()`, so at the benchmark `get_hmass(2)` returns **190.73 / 244.26 / 295.49** for
requested m_φ = **200 / 250 / 300**, and `get_hmass(3) = get_hmass(4) = 295.23` for requested
mA = mHp = 300. `GeneralProbe.cpp:302-307` then builds `DecayTable table(model)` and reports
`total_width_h2_GeV` and `ctau_h2_mm` — **computed at the wrong φ mass**. For an LLP study
whose headline observable *is* cτ, this is the most operationally dangerous unflagged
consequence of the tanβ=4×10⁷ conditioning. The trilinear coupling itself is unaffected
(`get_coupling_hhh` never calls `get_m12_2()`), which is why the campaign's central result
survives — but the width/ctau columns in every CSV at this tanβ should be marked unusable,
not just `m12_2_out`.

### #4 — The committed `GHphiphi` default is the floating-point artefact, not the physics

`parameters.py` ships `GHphiphi = -63.459361555950252`, the tanβ=4×10⁷ mφ=250 value. By the
report's own §5 the last ~8 digits of that number are the `cos(atan(tanβ))` artefact; the
physically correct value at M²=m_φ² is `−m_h²/v = −63.459361087483`. The difference is
irrelevant for any cross section, but shipping the number the report itself calls "not real
physics" as the flagship default is internally inconsistent. Suggest `−63.4593610875` (or
better, a note that the default is a placeholder — which the comment already says).

### #5 — The upper edge of the theory-valid M² window is stability, not perturbativity — everywhere

This recurs. At tanβ=4×10⁷ (B10) and at the tanβ=10 illustrative fine grid, which I
reproduced independently (mφ=250, λ6=1.1777e-4, λ7=0):

| r = M²/m_φ² | g | λ1 | u/p/s/po |
|---|---|---|---|
| 0.96 | −83.766357 | +4.380 | 1/**0**/1/1 |
| 0.97 | −78.689608 | +3.349 | 1/1/1/1 |
| 1.000 | −63.459361 | +0.256 | 1/1/1/1 |
| 1.002 | −62.444011 | +0.050 | 1/1/1/1 |
| 1.004 | −61.428662 | −0.156 | 1/1/**0/0** |
| 1.005 | −60.920987 | −0.260 | 1/1/0/0 |

Report §6b's "r=0.96 fails perturbativity" ✔; "fails already at r≈1.005" is off by one grid
step (it fails at **1.004**) and, more importantly, fails by **stability/positivity**, not
perturbativity. Same correction as B10: the constraint is `0 < λ1 ≲ 4π`.

### #6 — Sanity note on `2hdmc_build/` provenance

`2hdmc_build/src/*` is byte-identical (`md5 668fdf09…` on `THDM.cpp`) to
`dihiggs/2hdmc/src/*`, so the campaign's "canonical, unmodified 2HDMC" claim is verified.
But note that this 2HDMC is *itself* not stock upstream 1.8.0 — `set_param_phys_lam1`,
`clear_param_phys_lam1_validation`, the lam1 round-trip validation block, and the commented
trig-rewrite experiment at `THDM.cpp:388-401` are local additions. The campaign's language
("the canonical, unmodified 2HDMC library") is accurate *relative to this workspace's
canonical copy*, but a reader could take it to mean upstream. Worth one clarifying sentence.

---

# Overall verdict

### Is the master identity (★) trustworthy as stated? — **YES, with one scope sentence added.**

I re-derived it from `THDM.cpp` independently (A1, D17) and confirmed it numerically to
2×10⁻¹⁵ relative or better at points spanning tanβ ∈ [0.5, 50], λ6 ∈ [−0.3, 2],
λ7 ∈ [−1, 0.5], mA ∈ [150, 900], mHp ∈ [150, 900], m_φ ∈ [250, 260], M²/m_φ² ∈ [0.8, 5.1].
It is a genuine exact identity at exact alignment, and — a point the report *under*-claims —
it does not need `mA = mHp`, `λ6 = λ7 = 0`, or any large-tanβ expansion. The single sentence
missing is: **"at the campaign's own benchmark tanβ = 4×10⁷, (★) is realized only to
7×10⁻⁹ because of floating-point conditioning, not to machine precision."** The report says
this in §5 but not next to the identity.

### Is "M² ≈ m_φ² is forced by perturbativity" trustworthy as stated? — **NO, as stated. Two corrections needed.**

1. **It is forced only at λ7 ≡ 0.** I built a theory-valid counterexample at the benchmark
   tanβ with λ7 = −1.03×10⁻⁸ where M² = 0.80·m_φ² and all four 2HDMC checks pass. The
   report's hedge is in the final clause of §4; it belongs in the headline.
2. **The forcing agent is `0 < λ1 ≲ 4π`, not `|λ1| ≲ 4π`.** Vacuum stability binds on the
   upper side, ~12× tighter than perturbativity, making the window asymmetric:
   `ΔM² ∈ (−4.8×10⁻¹⁰, +3.9×10⁻¹¹) GeV²`, not `±4.8×10⁻¹⁰`.

Within λ7=0 the forcing itself is real, route-independent (I verified the masses+m12² route
lands theory-valid at the exact forced M²), and not a floating-point artefact.

### Single most important correction the team needs to make

**Flag every mass-derived quantity computed at tanβ = 4×10⁷ as unusable, not just
`m12_2_out`.** `get_hmass()` routes through `get_m12_2()`, so at the benchmark 2HDMC
believes m_φ = 190.73 / 244.26 / 295.49 GeV for the requested 200 / 250 / 300, and
m_A = m_H± = 295.23 for the requested 300. Every `total_width_h2_GeV` and `ctau_h2_mm`
column this campaign (and, by the same mechanism, any other campaign using this probe
family at this tanβ) produced is computed at the wrong φ mass. The trilinear coupling — the
actual subject of this report — is immune, because `get_coupling_hhh` never touches
`get_m12_2()`. But for an LLP programme whose headline observable is cτ, this is the finding
with the largest downstream blast radius, and it is currently unrecorded.

---

## Verdict tally

| Item | Verdict |
|---|---|
| A1 | CONFIRMED |
| A2 | CONFIRMED |
| A3 | CONFIRMED |
| A4 | CONFIRMED |
| A5 | CONFIRMED |
| A6 | CONFIRMED |
| A7 | CONFIRMED |
| B8 | CONFIRMED (§3 identity) — but §4's printed inverse is WRONG, see Additional #2 |
| B9 | CONDITIONAL (λ7 ≡ 0 only) |
| B10 | CONDITIONAL (order of magnitude right; window asymmetric, upper edge 12× tighter) |
| B11 | CONFIRMED |
| B12 | CONFIRMED (genuine; edges fuzzy at ±0.2 in λ1 ≈ ±8×10⁻¹² GeV²) |
| C13 | CONFIRMED |
| C14 | CONFIRMED |
| C15 | CONDITIONAL (mechanism is stability not perturbativity; "full stop" untested off alignment) |
| D16 | CONFIRMED |
| D17 | CONFIRMED (identity) — stated domain WRONG ("large-tanβ") |
| D18 | CONDITIONAL (exact alignment; any tanβ/λ6/λ7/mA/mHp) |
| D19 | CONFIRMED (with corrected domain above) |
| D20 | CONFIRMED |
| E21 | NUMERICALLY_UNSTABLE |
| E22 | CONFIRMED |
| E23 | NUMERICALLY_UNSTABLE (campaign's 4.5% figure CONFIRMED) |
| E24 | CONFIRMED |
| F25 | CONFIRMED |
| F26 | CONFIRMED |
| F27 | CONFIRMED |
| F28 | CONFIRMED |
| F29 | CONFIRMED |

**Counts:** CONFIRMED 22 · CONDITIONAL 5 · WRONG 0 · UNSUPPORTED 0 · NUMERICALLY_UNSTABLE 2.
Plus 6 additional issues, of which #3 (mass/ctau contamination) is the most consequential
and #2 (§4's λ1 formula) and #5 (stability vs perturbativity) are outright errors in the
report text.
