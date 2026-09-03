# M² analysis: why Christopher's benchmarks land at M² ≈ m_φ²

**Corrected after adversarial review — `validation/SOL_REVIEW.md` item 6 —
see §4 below, whose conclusion this file originally got backwards. Corrected
a second time after `validation/SOL_FINAL_REVIEW.md` items B8-B10 and
Additional issue #2: the "forced" claim needed the λ7=0 condition promoted
from a trailing clause to the headline (a theory-valid λ7≈10⁻⁸
counterexample with M²=0.80·m_φ² was constructed), the §4 λ1-inversion
formula was not actually the algebraic inverse of §2's identity, and the
quoted `±4.8×10⁻¹⁰ GeV²` window is asymmetric (vacuum stability binds ~12×
tighter than perturbativity on the upper side).**

`M2 = m12²/(sinβ·cosβ)` is this project's own convention
(`physical_trilinear_source_trace.md` §4), not a 2HDMC-native quantity.
`m12²` is a **direct, independent input** in both 2HDMC's generic-basis CLI
(`CalcGen`, taking λ1..7, m12², tanβ) and `THDM::set_param_phys`
(masses+m12²+tanβ) — mechanically, nothing in either route's *interface*
forces `m12² = m_φ²·sinβcosβ`. But at this project's tanβ, perturbativity
forces it anyway, for **any** route (§4). This section derives, exactly,
why Christopher's own inputs land there.

## 1. Christopher's actual recorded inputs (OBSERVED FROM FILES)

From `campaigns/20260901_photonic_requalification/work/targets.csv`
(extracted, with self-checking asserts, from the original
`chris_original/photonic_final_results_CalcLH.csv` provenance strings):

| m_φ target | tanβ | λ1 | λ6 | λ7 | m12² (GeV²) | M = √(M2) (GeV) |
|---|---|---|---|---|---|---|
| 200 | 40000000.00000001 | 1.0 | 1.177689207010651e-4 | 0.0 | 9.999999999933049e-04 | 199.99999999933058 |
| 250 | 40000000.00000001 | 1.0 | 1.177689207010651e-4 | 0.0 | 1.562499999999304e-03 | 249.99999999946445 |
| 300 | 40000000.00000001 | 1.0 | 1.177689207010651e-4 | 0.0 | 2.249999999999304e-03 | 299.9999999995538 |

M (= √M2) matches the m_φ target to a **relative ~1–5×10⁻¹⁰** at all three
masses — this is the raw fact the mission asks to explain. λ1=1.0 and λ6 are
identical across all three masses; only `m12²` (equivalently the mass
targets) differ. This is the signature of a **physical-input construction**
(masses + λ1 fixed as inputs, m12² solved for) — i.e. Christopher's external
pipeline (`flujo_listo_mixed_photonic_ctau08_ctau_fix`, per the recorded
`calcgen_command` path — not code in this repo, not inspected further per
the mission's UFO/reopening restrictions) is doing the same *algebraic*
inversion 2HDMC's own `set_param_phys_lam1` implements, whether or not it
literally calls that function.

## 2. Exact identity: M2 as a function of (mH, mh, λ1, λ6, λ7, tanβ) at alignment

Starting from `set_param_phys_lam1`'s own m12² formula
(`THDM.cpp:414-416`, quoted in the source trace), specialized to exact
alignment (sba=1 ⟹ β−α=90° ⟹ ca=sinβ, sa=−cosβ, so ca²=sin²β, sa²=cos²β):

```
m12² = [ mH²·sin²β + mh²·cos²β − v²cos²β·(λ1 + 1.5λ6·tanβ − 0.5λ7·tan³β) ] / tanβ
```

Divide by `sinβ·cosβ` to form `M2`, and substitute `sinβ = tanβ·cosβ`
throughout (pure trig identity, no approximation):

```
M2 = mH²  +  (mh² − v²λ1)/tan²β  −  1.5·v²·λ6/tanβ  +  0.5·v²·λ7·tanβ
```

**DERIVED, this mission — exact algebraic identity, no large-tanβ
approximation used yet.** `GENERAL IDENTITY given: (a) the λ1-input
construction route [set_param_phys_lam1, or any pipeline solving the same
inversion], (b) exact alignment sba=1.` Holds at **any** tanβ, not just
large tanβ.

## 3. The large-tanβ / λ7=0 limit

As tanβ→∞ with mh, λ1, λ6, λ7 held at O(1)/finite values:

- `(mh²−v²λ1)/tan²β → 0` as `1/tan²β`
- `1.5v²λ6/tanβ → 0` as `1/tanβ`
- `0.5v²λ7·tanβ` → **diverges linearly** in tanβ unless λ7=0

So, **given the campaign's λ7=0 assumption**, all three correction terms
vanish and:

```
M2 → mH²  =  m_φ²          [NUMERICAL LIMIT: tanβ → ∞, at fixed λ1/λ6/λ7=0/alignment]
```

This is the complete, exact mechanism. Note explicitly what does **not**
matter: **the numerical value of λ1 itself never survives to leading order**
— it appears only in the `1/tan²β`-suppressed term, consistent with
`physical_trilinear_source_trace.md` §5's independent finding that
`d(m12²)/dλ1 ~ 1/tan³β → 0`. Christopher's specific choice `λ1=1` is
therefore **not** why M2≈m_φ²; any λ1 order-unity value would have given
the same result at this tanβ. What **is** load-bearing is that λ1 (rather
than m12² or M2) was the coordinate chosen as the *input* — i.e. this is a
**λ1-construction artifact in the sense that using the λ1 route at large
tanβ automatically collapses M2 onto m_φ² regardless of λ1's value**, not
in the sense that λ1's numeric value matters.

## 4. Answering the mission's Q2 directly

> Why does M² ≈ m_φ² occur? Explicit construction choice / accidental
> consequence / alignment relation / large-tanβ limit / λ1 artifact / combination?

**Combination — but M²≈m_φ² is FORCED ONLY WITHIN THE λ7=0 SLICE, not for
2HDM parameter space at this tanβ in general. Corrected here after
`SOL_REVIEW.md` item 6 showed an earlier version of this section had this
backwards, and `validation/SOL_FINAL_REVIEW.md` item B9 then showed the
"forced" language, even after that fix, still overstated the λ7=0 condition
by burying it in a trailing clause instead of the headline.**

**Explicit counterexample (`SOL_FINAL_REVIEW.md` B9), constructed at this
benchmark's own tanβ=4×10⁷, mφ=250, λ1=1 as a literal input, with λ6=0 and
λ7=−1.0309278350515464×10⁻⁸ (a value indistinguishable from zero in every
other observable at this benchmark's precision):**

```
M² = 50000.0889 GeV²  =  0.80000142 · m_φ²        (20% away from m_φ²)
g_hφφ = −164.99361721019517 GeV                    (not −63.46 GeV)
unitarity_ok = perturbativity_ok = stability_ok = positivity_ok = 1  (ALL FOUR PASS)
```

So "M²≈m_φ² is forced by perturbativity" is a true statement about the
λ7=0 slice of this benchmark, not about tanβ=4×10⁷ 2HDM points in general.
The rest of this section (§2/§3, and the λ7=0 forcing mechanism itself) is
unchanged by this correction — only the strength of the headline claim is.

The λ1-route mechanism (§2/§3) explains **why Christopher's own pipeline**
(which used masses+λ1 as inputs) landed at M2≈m_φ²: it is the large-tanβ
NUMERICAL LIMIT of an exact GENERAL IDENTITY, given the λ1-input route and
exact alignment. That much survives unchanged.

But the claim that a **masses+m12²-route** point "would not automatically
land at M2≈m_φ²... since there m12² is the free input, not a derived
quantity" is **wrong**. Route-independently, at alignment (given λ7=0 — see
the counterexample above for what happens once that is relaxed), inverting
§2's identity for λ1 in terms of M² (valid regardless of which coordinate is
treated as "input" — it is a statement about the physical point, not about
which THDM setter function was called):

```
λ1 = (m_φ² − M²)·tan²β/v² + m_h²/v² − 1.5·λ6·tanβ + 0.5·λ7·tan³β
```

**Corrected** after `SOL_FINAL_REVIEW.md` B8/Additional-issue-#2: an earlier
version of this line read `λ1 = (m_φ²−M²)/(v²cos²β) − 1.5λ6tanβ +
0.5λ7tan³β`, which is not the algebraic inverse of §2's identity — it was
missing the `+m_h²/v²` term (≈0.258, ~2% of the `4π` perturbativity budget)
and used `1/(v²cos²β)` where `tan²β/v²` is required (the two differ by a
factor `1+cot²β`, negligible at this benchmark's tanβ=4×10⁷ but wrong by 4%
at tanβ=5). The numerical conclusions below are unaffected — the shift from
this fix is `~m_h²/tan²β ≈ 1×10⁻¹¹ GeV²`, inside the quoted window — but the
formula as printed was not, in fact, the inverse it claimed to be.

At tanβ=4×10⁷, `v²/tan²β ≈ 3.79×10⁻¹¹ GeV²`. The binding constraint is
**vacuum stability, `0 < λ1`, not `|λ1| ≲ 4π` perturbativity** — stability
binds on the upper side about 12× tighter than perturbativity does on the
lower side (`SOL_FINAL_REVIEW.md` B10). The window is therefore
**asymmetric**: `ΔM² ∈ (−4.8×10⁻¹⁰, +3.9×10⁻¹¹) GeV²` around
`m_φ² − 1.5v²λ6/tanβ`, total width ≈5.2×10⁻¹⁰ GeV² ≈ 8×10⁻¹⁵ relative — not
the `±4.8×10⁻¹⁰` symmetric window this section originally quoted. I
verified the asymmetry directly: pushing M² off m_φ² by relative
10⁻¹⁵/10⁻¹³/10⁻¹⁰ (via the masses+m12² route) moves the model's own
reconstructed `λ1_out` to roughly −7068 / −7231 / −1.7×10⁵ (all
theory-invalid on the lower/perturbativity side); on the upper/stability
side the window closes at `ΔM² ≈ +3.9×10⁻¹¹ GeV²`, not `+4.8×10⁻¹⁰`. **At
this benchmark's tanβ, within the λ7=0 slice, M²=m_φ² is forced — by vacuum
stability on one side and perturbativity on the other, route-independently —
but is not forced once λ7 is allowed to be even ~10⁻⁸ (see the
counterexample above).**

This does not remove the earlier answer's other two clauses: it is **not**
an explicit input choice in the sense of anyone typing `m12²=m_φ²·sinβcosβ`
directly (the λ1-route construction reaches it as a formula output, and a
masses+m12²-route construction reaches it as the only surviving
perturbativity-allowed choice — different mechanisms, same forced
destination), and it **is** still contingent on λ7=0 (a nonzero λ7 shifts
the forced destination itself, via the `0.5λ7·tan³β` term, rather than
removing the forcing). What changes is that "M²≈m_φ² is optional; a
masses+m12² route could easily avoid it" — the original conclusion here —
is false at this tanβ.

## 5. Falsifiability / what would break this

This derivation makes concrete, checkable predictions that
`m2_study/m2_variation.csv` and `validation/numerical_crosschecks.csv`
should test:

1. At fixed mH, mh, λ6, alignment, λ7=0: M2 computed via the λ1 route
   should follow §2's formula for **any** λ1 tested (not just λ1=1), with
   deviations from mH² shrinking as tanβ increases (∝ 1/tanβ, dominated by
   the λ6 term at these campaign values, since `1.5v²λ6/tanβ` ≈
   `1.5·60624·1.1777e-4/4e7` ≈ **2.678×10⁻⁷** GeV² at tanβ=4×10⁷ —
   **corrected after `SOL_REVIEW.md` item 6 caught a factor-1000 slip here**
   (an earlier version of this line wrote 2.68×10⁻⁴, a units/division error);
   this matches Christopher's own 200 GeV row exactly:
   `m_φ² − M2 = 40000 − 39999.99999999933… = 2.68×10⁻⁷ GeV²`) while the λ1
   term is ~15 orders of magnitude smaller still.
2. Turning on λ7≠0 at this tanβ should make M2 diverge from m_φ² linearly
   in tanβ·λ7 — a sharp, falsifiable prediction, not tested numerically by
   this mission unless a probe run shows otherwise (out of the mission's
   λ7=0 campaign assumption, but worth a single confirmatory point if cheap).
3. A **masses+m12²-route** point (`set_param_phys`, not `_lam1`) at the same
   masses/tanβ/alignment but with m12² chosen away from
   `mH²·sinβ·cosβ` should show `g_hφφ` deviating from the ≈constant
   `−m_h²/v = −63.4594` GeV value (this project's own benchmark's mh=125.0
   GeV value — not the `−63.66` GeV figure that belongs to a *different*
   benchmark family, mh=125.2 GeV, in the 2026-08-31 prior audit) — this is
   exactly Phase 2's M² variation grid, confirmed: only within the
   perturbativity-allowed window (§4) does `g_hφφ` sit near −63.4594; away
   from it, `g_hφφ` moves smoothly and roughly linearly in M² (per (★),
   `physical_trilinear_derivation.md` §0), reaching hundreds of GeV within
   the coarse `m2_study/m2_variation.csv` grid — see that file and
   `COUPLING_STUDY_REPORT.md` §6.
