# Photonic benchmark requalification — summary

Campaign: `campaigns/20260901_photonic_requalification` · 2026-09-01
Scope: photonic family only, m_phi = 200 / 250 / 300 GeV. Mixed benchmark untouched.

> **The three replacement points are sound and independently reproduced.**
> **The event-yield tables are NOT usable as absolute numbers** — they inherit an
> unresolved production-coupling mismatch of O(10²–10³). See section 5.

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

Class **B — near-identical physical replacement**, for all three masses.
Full residuals in `comparison_target_vs_validated.csv`.

| m_phi | BR(γγ) | BR(Zγ) | BR(bb) | BR(gg) | Γ_total | cτ |
|-------|--------|--------|--------|--------|---------|-----|
| 200 | +3.8 % | −7.9 % | +8.2 % | −9.1 % | −13.0 % | **+15.0 %** |
| 250 | +1.7 % | −2.6 % | −0.6 % | −12.3 % | −3.2 % | +3.3 % |
| 300 | +0.9 % | −1.0 % | −4.9 % | −14.8 % | +2.4 % | −2.4 % |

Photonic character fully preserved: BR(γγ) + BR(Zγ) = 0.9856 / 0.9916 / 0.9940
(original 0.9861 / 0.9912 / 0.9931).

- **cτ at 200 GeV moves +15 % (727 → 835 mm).** For an LLP analysis this is the
  physically consequential change, since decay-volume acceptance depends on cτ
  directly. Flagged in the CSV's `selection_caveat` column, not just here.
- **BR(gg) is low by 9–15 % throughout.** BR(gg) ≈ 0.003, so it moves the gg-gg
  yield (≈0.02–0.06 events) and nothing else.

These are **not** search residuals — they are the size of the error the round-trip
was introducing. Matching the published numbers more closely would mean
reproducing the artefact, so no attempt was made.

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
  depend only on the BRs, which are the validated part of this work.

This is exactly the `physical_2HDM` vs `EF_simple` vs `EF_m2` question the mission
defers to the next campaign, so it is **quantified and flagged, not acted on**:
no MadGraph was rerun and `sigma_LO` was reused verbatim, as instructed. The
tables carry this warning in their own header, and every row of the yields CSV
carries `absolute_scale_status = CONDITIONAL_unresolved_production_coupling`.

MC integration uncertainty is absent from the source and is left blank, not inferred.
