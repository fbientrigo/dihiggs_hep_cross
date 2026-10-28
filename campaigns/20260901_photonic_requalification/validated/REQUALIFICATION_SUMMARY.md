# Photonic benchmark requalification — summary

Campaign: `campaigns/20260901_photonic_requalification` · 2026-09-01
Scope: photonic family only, m_phi = 200 / 250 / 300 GeV. Mixed benchmark untouched.

> **CORRECTION, 2026-09-03, in two parts (second part supersedes the
> first — read to the end of this box before acting on anything below).**
>
> **Part 1 (same day, since found wrong):** an initial pass claimed §3's
> "photonic character fully preserved" verdict was wrong, and that
> BR(γγ)+BR(Zγ) actually collapses to ~0.15-0.26% with BR(gg) dominant
> instead. **That claim was itself wrong.** It was produced by a
> `Lambda1EvaluatorV2` binary linked against a `lib2HDMC.a` built
> incrementally after `THDM.h` changed size — silently mixing a freshly
> compiled `THDM.o` with a stale `DecayTable.o`/`Constraints.o` compiled
> against the old, smaller class layout. This is a real memory-layout (ODR)
> violation, caught by an independent adversarial review
> (`~/atlas_dihiggs/dihiggs_hep_cross/campaigns/physical_vs_effective_coupling_v1/validation/SOL_FINAL_REVIEW_2.md`),
> that produces deterministic but wrong numbers with no compiler warning —
> not a rounding effect, and not evidence about this benchmark's physics.
>
> **Part 2 (verified independently, this is the actual correction):** after
> a proper `make clean && make` in every affected build directory and a
> from-scratch pre-fix/post-fix comparison (git-stash the fix, clean
> rebuild, measure; restore the fix, clean rebuild, measure again — done
> directly for this campaign's own three benchmark points, not just taken
> on trust), **the real effect of the mass-reconstruction fix here is a
> few-percent shift in the individual γγ/Zγ/gg branching ratios and ctau,
> not an order-of-magnitude collapse**, and §3's original "photonic
> character fully preserved" verdict was correct in substance:
>
> | m_phi | BR(γγ) before→after | BR(Zγ) before→after | BR(γγ)+BR(Zγ) before→after | ctau_mm before→after |
> |---|---|---|---|---|
> | 200 | 0.6895→0.6732 (−2.4%) | 0.2961→0.3128 (+5.6%) | 0.9856→0.9860 | 835.5→763.1 (−8.7%) |
> | 250 | 0.6212→0.6161 (−0.8%) | 0.3704→0.3754 (+1.3%) | 0.9916→0.9914 | 337.5→331.9 (−1.7%) |
> | 300 | 0.5871→0.5847 (−0.4%) | 0.4069→0.4090 (+0.5%) | 0.9940→0.9937 | 163.6→165.4 (+1.1%) |
>
> ("before" here is the genuine, clean pre-fix build — reproduces the
> original §3 numbers exactly, confirming this campaign's original
> 2026-09-01 build was never affected by the staleness bug above; "after"
> is the properly fixed and cleanly rebuilt library.) `BR(gg)` moves by a
> similarly small amount (0.0029→0.0031 at 200 GeV, etc.) — it does **not**
> become dominant. §3's table below is superseded only in its **precision**
> (few-percent shifts, mostly in how γγ and Zγ trade off against each
> other, not their sum), not in its qualitative conclusion. §5's claim that
> relative yields within a mass column "depend only on the BRs, which are
> the validated part of this work" is restored to being correct, modulo the
> same few-percent BR shifts. `validated/photonic_requalified.csv` and
> `validated/comparison_target_vs_validated.csv` have been regenerated a
> second time from the properly clean build. Root cause and fix:
> `~/atlas_dihiggs/dihiggs_hep_cross/campaigns/physical_vs_effective_coupling_v1/validation/MASS_RECONSTRUCTION_FIX.md`.
> **§6 below (written for Part 1) is superseded by this box — read the box,
> not §6, for the actual correction.**

---

## 1. Was the original point valid?

**Yes — all three replay bit-exactly and pass every theory check.** The premise that
some photonic points are theory-invalid does not hold for 200/250/300 GeV.

Replaying Christopher's exact `CalcGen` command lines through the canonical 2HDMC
build reproduces his published CSV to every printed digit — width, cτ and all four
branching ratios — with `Tree-level unitarity = 1`, `Perturbativity = 1`,
`Stability = 1` in each case.

**The real defect is that the points are mislabelled, not invalid.**

At tan(beta) = 4e7 the generic-basis spectrum carries **no significant digits at
all**. Perturbing tan(beta) in the ninth significant figure and re-running
`set_param_gen` gives:

| tan(beta) | m_phi | mA |
|---|---|---|
| 40000000.0   | 198.21749 | 298.81461 |
| 40000000.02  | 198.21749 | 298.81461 |
| 40000000.05  | **205.42774** | 303.64544 |
| 40000000.08  | **182.94645** | 288.91072 |
| 40000000.1   | **205.42774** | 303.64544 |
| 40000000.12  | 198.21749 | 298.81461 |
| 40000000.14  | 205.42774 | 303.64544 |

The answer oscillates non-monotonically across a **22.5 GeV** spread (182.95 →
205.43) under relative input changes of ~1e-9. Two independent quantisations drive
this: `m12^2 ≈ 1e-3 GeV²` is below one ulp of the `m22^2 ≈ 1e4 GeV²` it is added
to (its reconstructed values are exact multiples of 2⁻⁴⁰·4e7 = 3.638e-5, i.e. ~1.4
significant digits), and `m12^2/(sin β cos β)` divides by 2.5e-8.

Christopher's pipeline `CalcGen → <point>.lha → CalcLH` samples that noise twice.
`CalcGen` computes the spectrum in memory, writes a LesHouches file, and `CalcLH`
reads it back and calls `set_param_gen` again (`THDM.cpp:2612`; the other three
`read_LesHouches` branches are excluded). The tan(beta) that survives the file is
displaced in two stages: `get_param_gen` returns `tan(atan(4.0000000000000007e7))
= 40000000.14512709`, and the writer's `% 16.8e` format (9 significant digits,
`THDM.cpp:2027-2044`) stores that as `4.00000001e+07 = 40000000.1`. So:

| label | in-memory m_phi | published m_phi | Δ | in-memory mA | published mA | Δ |
|---|---|---|---|---|---|---|
| 200 GeV | 198.217 | 205.428 | +7.210 | 298.815 | 303.645 | +4.831 |
| 250 GeV | 250.146 | 255.898 | +5.751 | 300.122 | 304.932 | +4.810 |
| 300 GeV | 300.370 | 305.176 | +4.806 | 300.370 | 305.176 | +4.806 |

Restoring *only* the tan(beta) field in a written `.lha` recovers 198.21749
exactly; restoring any λ or m12² field individually changes nothing.

So the BRs filed under "200 GeV" belong to a 205.43 GeV scalar and are multiplied
by `sigma_LO(200 GeV)`. The benchmark is also *documented*
(`chris_event_yields.tex`, `tab:bench`) as `mA = mHpm = 300 GeV`, which no
published point has. The round-trip additionally flips `sin(beta-alpha)` to −1 at
250 and 300 GeV (harmless — alignment is |sin(β−α)| = 1 either way).

Reproduce: `scripts/diagnose_tanb_conditioning.py` → `logs/tanb_conditioning_diagnosis.txt`.

## 2. What changed?

Only the **evaluation route** and the resulting **mass assignment**. Every
coordinate Christopher *chose* is preserved:

```
lambda1 = 1          lambda6 = 1.177689207010651e-04     lambda7 = 0
tan(beta) = 4e7      sin(beta-alpha) = 1                 Type-I Yukawas
mh = 125.0           mA = mHpm = 300                     lambda6*tan(beta) = 4710.76
```

The points are now evaluated **in-process** through the canonical maintained λ1
route, `THDM::set_param_phys_lam1` via `dihiggs/app/Lambda1EvaluatorV2`
(schema `dihiggs.lambda1.v2`), where the masses are *inputs* and no LesHouches file
is written or read. `m_phi` is therefore exactly 200 / 250 / 300 and `mA = mHpm`
exactly 300 — matching both the documented benchmark definition and the mass at
which `sigma_LO` is quoted. No local search was run: the corrected point *is* the
design point Christopher specified, evaluated without the round-trip.

*Precisely:* λ2…λ5 and m12² change **status**, from inputs of `set_param_gen` to
quantities derived by `set_param_phys_lam1`, and their values move in the last
digits (e.g. λ3 1.907230065364474703 → 1.90723006634924852; m12² 9.999999999933e-4
→ 9.99999996372e-4, 3.6e-9 relative). Physically negligible, but they are not
bit-identical.

## 3. How close is the replacement?

**Status, 2026-09-03: essentially correct, per the correction box at the
top of this document — the table below (residuals vs. Christopher's
original published numbers) still stands. A same-day mass-reconstruction
fix changes these residuals by a few percent each (see the top box for the
exact before/after), not the 2-4 orders of magnitude an intermediate,
now-retracted "correction" briefly claimed. Do not use the specific
percentages below for anything requiring sub-few-percent precision without
checking the top box first; the qualitative verdict (Class B,
near-identical, photonic character preserved) holds.**

Class **B — near-identical physical replacement**, for all three masses.

| m_phi | BR(γγ) | BR(Zγ) | BR(bb) | BR(gg) | Γ_total | cτ |
|-------|--------|--------|--------|--------|---------|-----|
| 200 | +3.8 % | −7.9 % | +8.2 % | −9.1 % | −13.0 % | **+15.0 %** |
| 250 | +1.7 % | −2.6 % | −0.6 % | −12.3 % | −3.2 % | +3.3 % |
| 300 | +0.9 % | −1.0 % | −4.9 % | −14.8 % | +2.4 % | −2.4 % |

Photonic character fully preserved: BR(γγ) + BR(Zγ) = 0.9856 / 0.9916 / 0.9940
(original 0.9861 / 0.9912 / 0.9931).

## 4. Why was this point selected?

Three routes were tested:

| route | m_phi well-defined? | theory | verdict |
|---|---|---|---|
| `set_param_gen` (Christopher's) | **No** — 22.5 GeV spread under 1e-9 input changes | U/P/S = 1 | rejected: mass is numerical noise |
| `set_param_phys` / (mH, M²), `DihiggsPointV2Evaluator` | yes | **theory_ok = 0** | rejected: M² cannot carry λ1 |
| `set_param_phys_lam1`, `Lambda1EvaluatorV2` | yes | **theory_ok = 1** | **selected** |

- The **generic-basis route is unusable**: the masses are outputs of a numerically
  chaotic diagonalisation (§1). m_phi must be an *input*.
- The **(mH, M²) route fails because M² cannot determine λ1 at this tan(beta).**
  Across M² = 36000 → 44000 GeV² the reconstructed λ1 runs
  +1.056, +5.278, −7066.14, −5278.39, −1.056 — wild and non-monotonic, because a
  6.7e-12 *relative* change in m12² moves λ1 by ~7000. (At M² = m_phi² the value
  −7066.135267701 is exactly the analytic term −1.5·λ6·tan β of `THDM.cpp:348`,
  with the round-off-sensitive term identically zero — so it is a *sampling* of an
  unconstrained direction, not round-off noise per se.) The route is also not
  rejected solely for negative λ1: at M² = 36000 and 38000 it has λ1 > 0,
  `positivity_ok = 1`, and still fails at `rejection_stage = unitarity`.
- The **λ1 route is correct** because λ1 is genuinely an *input coordinate* of
  Christopher's construction — `λ1 = 1` appears literally in every `CalcGen`
  command line — exactly the case the campaign's λ1 distinction reserves it for.
  Christopher pinned *both* λ1 = 1 and M² = m_phi²; in the generic basis those are
  consistent, and the λ1 route reproduces M² ≈ m_phi² to ~1e-8.

**λ1 = 1 is a safe choice, verified over the physically sensible range.** Scanning
λ1 ∈ [0.25, 4] at fixed everything else changes BR(γγ) by < 0.002 % and cτ by
< 0.13 %, with `theory_ok = 1` throughout (`work/calculator_runs/lam1_grid/`).
That inertness does **not** extend indefinitely and is **not** the reason the
−7066 reconstruction is discarded: `theory_ok` first fails at λ1 = 8
(perturbativity) and unitarity fails from λ1 = 20, and at λ1 = −7066 the model is a
genuinely different one — `theory_ok = 0`, cτ = 3154.6 mm vs 835.5 mm (+278 %).
λ1 = −7066 is discarded because it is not Christopher's input and is not determined
by the M² route, not because "λ1 does not matter".

**The λ1 round-trip warning is benign.** `Lambda1EvaluatorV2` emits
`lambda1_residual_warning = 1` (residual 0.021 / 0.021 / 0.171). The residual is
non-monotonic in λ1 (0.0031 at 0.25, 0.055 at 0.5, 0.021 at 1.0), i.e. noise in the
m12² ↔ λ1 inversion, with no observable consequence over the inert range.

**m_h convention.** Kept at Christopher's **125.0 GeV**, not the campaign-current
125.20 GeV, so the mass correction is the *only* change and the comparison stays
interpretable. Flagged rather than silent, per `docs/CURRENT_DATA_AUTHORITY.md`.
The 125.20 GeV variant is carried in `photonic_requalified.csv`
(`sensitivity_mh12520_*`): −1.0 % on BR(γγ), −3.7 % on cτ at 200 GeV. Migrating the
family to 125.20 GeV is a separate, explicit decision.

---

## 5. BLOCKER for the event yields — quantified, not resolved

**The reused `sigma_LO` and the requalified decay point do not describe the same
2HDM point, and the discrepancy is large.**

The production cross sections come from the simplified UFO vertex
(`dihiggs_ufo/LLscalar_v3_UFO_original/couplings.py:372`):

```python
GC_90 = Coupling(name='GC_90', value='8*complex(0,1)*Mh2**2/vev')
```

The requalified benchmark has soft scale M² = m_phi², and 2HDMC's coupling for the
same vertex is `g_hφφ = (m_h² + 2m_phi² − 2M²)/v`, which at M² = m_phi² collapses
to `m_h²/v` — **the same at every mass**:

| m_phi | UFO `8 m_phi²/v` (behind σ_LO) | 2HDMC `g_hφφ` at the benchmark | ratio | σ ∝ g² factor |
|---|---|---|---|---|
| 200 | 1299.65 GeV | 63.4594 GeV | 20.5 | **≈ 4.2e2** |
| 250 | 2030.70 GeV | 63.4594 GeV | 32.0 | **≈ 1.0e3** |
| 300 | 2924.21 GeV | 63.4594 GeV | 46.1 | **≈ 2.1e3** |

Normalisation was checked against the same LesHouches output's
`IMGH1H1H1 = −190.378 = −3 m_h²/v`, the standard SM hhh Feynman rule, so
`IMGH1H2H2 = −63.459` is directly comparable to `GC_90`. The linear
`g(M²)` form was confirmed on the M² scan (95.95, 79.71, 63.46, 47.21, 30.97 for
M² = 36000…44000).

Christopher's own `tab:coupling` assumes `m22 = 0`, i.e. `g/v = 4 m_phi²/v²`; that
is incompatible with M² = m_phi², which would require M² = m_h²/2 − m_phi² < 0.

**Consequences, stated plainly:**

- Absolute yields in `event_yields_photonic_requalified.csv` and
  `photonic_tables_requalified.tex` are overstated by roughly **4.2e2 / 1.0e3 /
  2.1e3** at 200 / 250 / 300 GeV (assuming σ ∝ g² for the single s-channel h*
  diagram — not verified by rerunning MadGraph, which was out of scope).
- The **relative ordering between mass columns is also wrong**: the true σ would
  be far flatter in m_phi, since g is mass-independent at this benchmark.
- **Relative yields within one mass column are unaffected** and are usable — they
  depend only on the BRs, which are the validated part of this work. (2026-09-03:
  a same-day mass-reconstruction fix shifts the individual BRs by a few percent
  each — see the top-of-document correction box — so "unaffected" should be read
  as "unaffected at the order-of-magnitude level," not bit-identical; recompute
  from the regenerated `photonic_requalified.csv` if sub-few-percent precision
  matters.)

This is exactly the `physical_2HDM` vs `EF_simple` vs `EF_m2` question the mission
defers to the next campaign, so it is **quantified and flagged, not acted on**:
no MadGraph was rerun and `sigma_LO` was reused verbatim, as instructed. The
tables carry this warning in their own header, and every row of the yields CSV
carries `absolute_scale_status = CONDITIONAL_unresolved_production_coupling`.

MC integration uncertainty is absent from the source and is left blank, not inferred.

---

## 6. [RETRACTED, 2026-09-03] — see the correction box at the top of this document

This section originally claimed the mass-reconstruction fix collapsed
BR(γγ)+BR(Zγ) from ~99% to ~0.15-0.26%, with BR(gg) becoming dominant. **That
claim was wrong** — an artifact of a build-hygiene bug (stale
`DecayTable.o`/`Constraints.o` linked against a `THDM.o` compiled with a
changed class layout; a real memory-layout violation, not a rounding
effect), caught by an independent adversarial review
(`~/atlas_dihiggs/dihiggs_hep_cross/campaigns/physical_vs_effective_coupling_v1/validation/SOL_FINAL_REVIEW_2.md`)
and independently re-verified from scratch (git-stash the fix, clean
rebuild, measure "before"; restore, clean rebuild, measure "after" — done
directly for all three of this campaign's points). The correct numbers are
in the box at the top of this document: a few-percent shift per channel,
BR(γγ)+BR(Zγ) staying at 98.6-99.4%, exactly as §3 originally reported. The
mass-assignment reasoning in §1-§4 remains correct and was never in
question; only this section's own claimed *consequence* of the (real, but
here numerically small) mass-reconstruction fix was wrong. Left in place,
retracted rather than deleted, so the mistake and its correction are both
part of the visible record — see
`~/atlas_dihiggs/dihiggs_hep_cross/campaigns/physical_vs_effective_coupling_v1/validation/MASS_RECONSTRUCTION_FIX.md`
for the full build-hygiene writeup.
