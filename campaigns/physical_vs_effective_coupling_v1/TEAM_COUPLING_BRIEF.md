# The h-φ-φ trilinear coupling: what we know, in one page

Full technical detail, every derivation, and the adversarial review trail
are in `COUPLING_STUDY_REPORT.md` and `validation/`. This document is the
short version for a meeting, a PI conversation, or onboarding a
collaborator. Every claim below survived two independent adversarial
review rounds (`validation/SOL_REVIEW.md`, `validation/SOL_FINAL_REVIEW.md`).

## 1. The one equation to remember

At exact alignment (sin(β−α)=1) — which this benchmark uses — 2HDMC's
physical h-φ-φ trilinear reduces to:

```
g_hφφ = (2·M² − 2·m_φ² − m_h²) / v          where M² ≡ m12² / (sinβ·cosβ)
```

This is **exact**, for *any* tanβ, λ6, λ7, m_A, m_H± — not an
approximation, not a benchmark-specific fit. m_A and m_H± cancel
identically; λ6 and λ7 cancel identically. Only M² and the SM-like mass
m_h control the coupling.

## 2. Why our physical coupling looked fixed

Plugging in this benchmark's own inputs, M² lands within about 10⁻¹⁴
relative of m_φ² — so close that, to every digit we can print,
`g_hφφ ≈ −m_h²/v ≈ −63.46 GeV`, independent of which of the three benchmark
masses (200/250/300 GeV) we use.

**This is not because the coupling is intrinsically constant.** It is
because *this benchmark's own inputs* (λ1 order-unity, λ7 exactly 0,
tanβ=4×10⁷) leave almost no room for M² to be anything else — vacuum
stability and perturbativity together squeeze the allowed M² into a window
only ~10⁻¹⁴ relative wide around m_φ². **That forcing holds only within the
λ7=0 slice.** A λ7 as small as 10⁻⁸ — invisible in every other observable
at this benchmark — is enough to move M² by 20% and the coupling to
−165 GeV instead of −63 GeV.

## 3. What M² really controls

```
Δg_hφφ = 2·ΔM² / v          (at fixed m_φ, m_h)
```

M² is an excellent dial — g_hφφ moves linearly and without bound as M²
moves. **Mathematically the dial is wide open. Physically, this benchmark's
inputs barely let us turn it.** Figure 2 (`physical_vs_M2.png`) makes this
one point visually: one broad curve, one point marked at M²=m_φ², one
annotation stating the valid window is too narrow to draw on that axis.

## 4. Why EF_simple is different

`EF_simple = 8m_φ²/v` (the value hardcoded in the *frozen, unmodified*
production UFO) is reachable algebraically — it corresponds to
`M² = 5m_φ² + m_h²/2` — but at exact alignment with λ6=λ7=0, requiring both
λ1>0 and λ2>0 (vacuum stability) forces `m_φ < 62.5 GeV`, which is
impossible in this benchmark (m_φ is by construction the *heavier* state,
>125 GeV). **EF_simple is not just numerically far from the physical value
here — it is theoretically excluded at this alignment, for every mass in
this benchmark's regime, by vacuum stability, not by "the physics being
different."** A broader scan (λ6/λ7 free) found no exception in 4000
random points. Untested: away from exact alignment.

## 5. What EF_m2 actually means

`EF_m2 = 8(m_φ² − m₂²)/v` uses a *different* mass parameter, 2HDMC's
internal Higgs-basis mass Y₂ (not directly exposed by the library, and
**not** the same quantity as this project's own M²). At exact alignment,
for *any* tanβ/λ6/λ7/mA/mH±, `Y₂ = M² − m_h²/2` exactly — which makes

```
EF_m2 = −4 · g_hφφ          (exact, at alignment, any tanβ/λ6/λ7/mA/mH±)
```

The "4×" gap is nothing but the ratio of EF_m2's prefactor (8) to the
physical Feynman-rule prefactor (2) — no separate physics. EF_m2 tracks
the *real* physical coupling far more closely than EF_simple does (it is a
fixed multiple of it), but it is still a different quantity, not a stand-in
for the trilinear itself.

## 6. What is physical vs. what is an approximation

`physical_2HDM` (§1's equation, evaluated with 2HDMC) **is** exact 2HDM
physics — there is no approximation in it. `EF_simple` is a phenomenological
prescription hardcoded years ago in the production UFO, with no derivation
found anywhere in the repository for why it takes that form, and it is
20-46× the physical magnitude here, with the **opposite sign**. `EF_m2` is
closer (exact 4× relation to the physical coupling) but is still built from
a different mass parameter than the physical trilinear itself — keeping
`m₂²` (EF_m2's Y₂) and `M²` (this project's own coordinate) distinct is
exactly what this study exists to make possible.

## 7. What we validated numerically

The master equation was independently re-derived from 2HDMC source code
**twice**, by two reviewers with no shared context, and measured to machine
precision (≤2×10⁻¹⁵) at points spanning tanβ ∈ [0.5, 50], λ6 ∈ [−0.3, 2],
λ7 ∈ [−1, 0.5], mA/mHp ∈ [150, 900] — none of which are this benchmark's
own values. The UFO/2HDMC normalization was independently anchored via the
UFO's own hhh self-coupling. **One important, unrelated finding surfaced by
the review:** at this benchmark's tanβ=4×10⁷, 2HDMC's own reconstructed
masses are off by 1.5-4.6% (a pre-existing 2HDMC floating-point limitation)
— which means every decay-width/cτ number this campaign computed at this
tanβ is unreliable, even though the trilinear coupling itself is immune.
See `COUPLING_STUDY_REPORT.md` §12.

## 8. What MadGraph still needs

No MadGraph installation exists in this environment, so nothing below was
run — see `madgraph_smoke/README.md`. What is ready: a genuine external-
coupling UFO copy (`ufo/LLscalar_v3_UFO_GHphiphi_external/`) that exposes
`GHphiphi` as a real, scannable parameter, plus the exact commands and
target values (`madgraph_smoke/commands.txt`) for a future session with
MG5_aMC to run the import smoke test, the ± sign test, and the σ∝|g|²
check. That is a separate, later decision — this mission stops here.

---

## Main comparison table (m_A = m_H± = 300 GeV, tanβ = 4×10⁷, exact alignment)

| m_φ [GeV] | M² [GeV²] | M²/m_φ² | physical_2HDM [GeV] | EF_simple [GeV] | EF_m2 [GeV] | theory_valid | short_reason |
|---|---|---|---|---|---|---|---|
| 200 | 40000.0 | 1.000000 | −63.459 | 1299.6 | 253.8 | yes | M²≈m_φ² forced (λ7=0 slice, this benchmark); g≈−m_h²/v |
| 250 | 62500.0 | 1.000000 | −63.459 | 2030.7 | 253.8 | yes | same mechanism; g mass-independent within this benchmark |
| 300 | 90000.0 | 1.000000 | −63.459 | 2924.2 | 253.8 | yes | same mechanism; g mass-independent within this benchmark |

Full-precision values: `coupling_comparison/coupling_table.csv`. Educational
(non-benchmark) M² variation points: `m2_study/` (secondary, illustrative,
not this project's validated benchmark family).

---

## PI questions

**Q: Why is physical_2HDM ~63 GeV?**
A: Because at this benchmark M²≈m_φ² to ~10⁻¹⁴ relative, and the master
equation collapses to g_hφφ = −m_h²/v = −63.46 GeV whenever that holds.

**Q: Is physical_2HDM generally constant?**
A: No. It is exactly `(2M²−2m_φ²−m_h²)/v`, linear and unbounded in M². It
only looks constant here because this benchmark's own inputs pin M² so
tightly.

**Q: Can we change it?**
A: Yes, in principle, by moving M² (equivalently m12², equivalently λ1 or
λ7) to a different physical point.

**Q: Why can't we change it much in this benchmark?**
A: Because vacuum stability and perturbativity together allow only a
~10⁻¹⁴-relative window around M²=m_φ² once λ7 is fixed to 0, as this
benchmark does. Relaxing λ7 even slightly (~10⁻⁸) reopens the dial
substantially.

**Q: Can physical_2HDM reproduce EF_simple?**
A: Not in this benchmark's regime. At exact alignment with λ6=λ7=0,
reaching EF_simple's magnitude requires m_φ<62.5 GeV, which contradicts m_φ
being the heavier state here. It is excluded by vacuum stability, not
merely "far away" numerically.

**Q: What exactly is m₂² in EF_m2?**
A: 2HDMC's internal Higgs-basis mass parameter Y₂ (not the same as this
project's own M²). At alignment, Y₂ = M² − m_h²/2 exactly, for any tanβ.

**Q: Is EF_m2 a 2HDMC definition?**
A: No — 2HDMC never returns Y₂ directly (it is private/internal); this
project reconstructs it from the library's public outputs, and EF_m2 itself
is a project-level comparison quantity, not something 2HDMC computes.

**Q: Which coupling should a future MadGraph run use?**
A: Not decided by this mission — a production decision for the PIs. The
physically correct value is `physical_2HDM` from §1's equation; the
externalized UFO (`ufo/LLscalar_v3_UFO_GHphiphi_external/`) is ready to
take it as a real scan parameter once that decision is made.
