# SOL_FINAL_RESPONSE — disposition of `validation/SOL_FINAL_REVIEW.md`

Per the mission's review acceptance rule: every WRONG / UNSUPPORTED /
NUMERICALLY_UNSTABLE item gets new evidence or a correction below; every
CONDITIONAL item's condition is propagated into the campaign's actual
scientific statements (not just noted here). Tally from the review:
**CONFIRMED 22 · CONDITIONAL 5 · WRONG 0 · UNSUPPORTED 0 ·
NUMERICALLY_UNSTABLE 2**, plus 6 additional issues. Unlike the first review
round, this one found zero outright WRONG/UNSUPPORTED labeled items — but
several CONFIRMED items ("CONFIRMED, but the stated domain is WRONG") and
the 6 additional issues carried real corrections that needed the same
treatment. All are addressed below; nothing is left as "will fix later."

## Master identity (★) — all A-items CONFIRMED, no action needed beyond one scope sentence

A1-A7 were independently re-derived and re-measured by Sol using a
different probe with no shared arithmetic (`SolProbe.cpp`), and all
confirmed the identity to machine precision away from the tanβ=4×10⁷
benchmark. **Action taken:** the one thing the review said was true but
"not carried next to the identity" — that (★) at the actual benchmark
tanβ=4×10⁷ holds only to 7.4×10⁻⁹, not machine precision — is now stated
directly under (★) in `COUPLING_STUDY_REPORT.md`'s "master result" section,
not just in §5.

## B9/B10 — CONDITIONAL, propagated

**B9 condition (M²≈m_φ² forced only within λ7≡0):** Sol constructed a
theory-valid counterexample at the benchmark tanβ with λ7=−1.03×10⁻⁸ and
M²=0.80·m_φ². **Fixed:** `COUPLING_STUDY_REPORT.md` §4 and
`derivation/assumptions_and_limits.md` §4 both now carry this
counterexample explicitly, and the headline claim was rewritten from
"Required — forced by perturbativity, route-independently, not optional"
to state the λ7=0 condition as part of the headline, not a trailing clause.

**B10 condition (window is asymmetric, stability-bound not
perturbativity-bound on the upper side):** the true window is
`ΔM² ∈ (−4.8×10⁻¹⁰, +3.9×10⁻¹¹) GeV²`, not `±4.8×10⁻¹⁰`. **Fixed:** both
files above, plus `COUPLING_STUDY_REPORT.md` §6a, now quote the asymmetric
window and the correct binding constraint `0 < λ1 ≲ 4π` rather than
`|λ1| ≲ 4π`.

## C15 — CONDITIONAL, propagated

**Condition:** the mechanism excluding EF_simple is vacuum stability
(λ1>0 and λ2>0 cannot hold simultaneously for m_φ > 62.5 GeV at exact
alignment, λ6=λ7=0), not perturbativity — a *stronger and cleaner* result
than originally claimed, reached by the *wrong* named mechanism. With
λ6/λ7 free, only a 4000-point empirical scan (0/4000 valid) supports the
claim, not a proof, and it is entirely untested away from exact alignment.
**Fixed:** `COUPLING_STUDY_REPORT.md` §8 rewritten with Sol's analytic
proof (reproduced from `set_param_phys`'s own λ1/λ2 formulas) and the scan
result, replacing "excluded by perturbativity, full stop."

## D18/D19 — CONDITIONAL / domain correction, propagated

**Condition/correction:** `M22²=M²−m_h²/2` is exact at exact alignment for
*any* tanβ/λ6/λ7/mA/mHp (not a "large-tanβ identity" as both
`COUPLING_STUDY_REPORT.md` §9 and `derivation/physical_trilinear_derivation.md`
§0 previously called it) and is numerically *cleanest* at small tanβ,
degrading as tanβ grows — the reverse of what "large-tanβ identity" implies.
**Fixed:** both files rewritten with the corrected domain statement and the
tanβ-scaling table Sol measured (7×10⁻¹²GeV² at tanβ=0.5 → 8×10⁻³GeV² at
tanβ=10⁵), plus the precise domain statement from D19 (sin(β−α)=1 exactly;
untested for cos(β−α)≠0).

## E21/E23 — NUMERICALLY_UNSTABLE, both addressed

**E21 (tanβ=4×10⁷ conditioning, three separate failure modes, only two
previously named):** the third — `set_param_phys`'s own λ1 reconstruction
carrying ≈±0.2 absolute floating-point granularity — is now documented, and
its consequence (E21 item 3 / Additional issue #3, see below) is the
review's single most important finding.

**E23 (`get_m12_2()` ~4.5% round-trip error, campaign's figure confirmed):**
no new action needed on the figure itself — already flagged pre-review. The
under-stated consequence is fixed via Additional issue #3.

## Additional issue #1 — `GeneralProbe.cpp` sign bug, masked by a tolerant test — FIXED

`GeneralProbe.cpp:234` computed `+v·[bracket]` where the formula (and
`get_coupling_hhh`) require `−v·[bracket]`; `logs/run_all_probes.py` scored
the test as PASS against `min(|g−g_gen|, |g+g_gen|)`, silently accepting
either sign. **Fixed:** the sign in `GeneralProbe.cpp` is negated to match
the formula as printed in `COUPLING_STUDY_REPORT.md` §1, and the harness
now does a strict sign-inclusive comparison (`logs/run_all_probes.py`,
`STEP1a`). Rebuilt and re-ran the full probe suite: **still 25/25 PASS,
worst relative deviation unchanged at 4.05×10⁻¹⁵** — the printed formula
was correct all along; only its probe implementation's sign was wrong.
`COUPLING_STUDY_REPORT.md` §1 documents this.

## Additional issue #2 — §4's λ1-inversion formula was not the actual inverse — FIXED

Missing `+m_h²/v²` term; `1/(v²cos²β)` should be `tan²β/v²`. **Fixed** in
both `COUPLING_STUDY_REPORT.md` §4 and `derivation/assumptions_and_limits.md`
§4 — corrected formula now printed, with the old (wrong) form shown
struck-through for the record. Numerical conclusions in both files were
unaffected (shift is `~m_h²/tan²β ≈ 1×10⁻¹¹ GeV²`, inside the already-quoted
window) — only the printed formula itself was wrong.

## Additional issue #3 — mass/width/ctau contamination at tanβ=4×10⁷ — FIXED, this campaign's single most important correction

`get_hmass()` routes through `get_m12_2()`, so at the benchmark 2HDMC
reconstructs m_φ = 190.73/244.26/295.49 GeV for requested 200/250/300, and
mA=mHp=295.23 for requested 300. Every `total_width_h2_GeV`/`ctau_h2_mm`
value in `m2_study/m2_variation.csv` and `m2_study/sensitivity_probes.csv`
(the two files at this tanβ) is computed at the wrong mass. The trilinear
coupling is unaffected (`get_coupling_hhh` never calls `get_m12_2()`).
**Fixed:**
- `GeneralProbe.cpp` now echoes 2HDMC's own reconstructed
  `hmass_h2_reconstructed_GeV`/`hmass_hA_reconstructed_GeV`/
  `hmass_hHp_reconstructed_GeV` in every row (rebuilt, full suite re-run).
- `m2_study/m2_variation_summary.md` now states the caveat explicitly
  (baked into `logs/run_all_probes.py`'s generation code, so it survives
  regeneration, not hand-edited into the output file).
- `COUPLING_STUDY_REPORT.md` gets a new §12 dedicated to this finding, and
  it is now the #1 item in "Unresolved scientific questions" (was previously
  a downplayed clause under a different item).
- Not fixed (correctly out of scope): the underlying `get_m12_2()`
  cancellation bug itself — pre-existing 2HDMC behavior.

## Additional issue #4 — UFO default value carried a floating-point artefact — FIXED

`GHphiphi`'s default (−63.459361555950252, the tanβ=4×10⁷ mφ=250 value)
had its last ~8 digits as the `cos(atan(tanβ))` artefact this campaign's own
report calls "not real physics." **Fixed:**
`ufo/LLscalar_v3_UFO_GHphiphi_external/parameters.py`'s default changed to
the exact, artefact-free `M²=m_φ²` value, `−m_h²/v = −63.459361087483`.
Re-verified the UFO still imports cleanly after the edit (`py_compile` +
direct import, both succeed). `ufo/validation.md` and
`COUPLING_STUDY_REPORT.md` §11 updated to match.

## Additional issue #5 — stability vs. perturbativity mislabeled at the upper M² edge — FIXED

Recurs in both B10 (tanβ=4×10⁷) and the tanβ=10 illustrative fine grid
(off-by-one grid step: fails at r=1.004, not r≈1.005, and by
stability/positivity, not perturbativity). **Fixed:**
`COUPLING_STUDY_REPORT.md` §6b corrected on both counts.

## Additional issue #6 — "canonical, unmodified 2HDMC" needs one qualifying sentence — FIXED

`2hdmc_build/`'s 2HDMC is byte-identical to this workspace's own canonical
copy, but that copy itself carries local additions
(`set_param_phys_lam1` and its validation machinery) relative to upstream
2HDMC 1.8.0. **Fixed:** added as item 7 in `COUPLING_STUDY_REPORT.md`'s
"Unresolved scientific questions," clarifying the claim is relative to this
workspace's canonical copy, not upstream.

## One more item surfaced by F28 that wasn't a numbered mandate item

F28 additionally noted the frozen UFO's `GC_90 = 8i·Mh2²/vev` is itself an
undocumented hand-edit of the archived 2021 model's original
`2i·vev` (still present, commented out). Added as item 8 in "Unresolved
scientific questions" — worth tracing before treating EF_simple as more
than a historical placeholder, but out of this mission's scope to trace
further (would mean reopening `dihiggs_ufo` provenance, explicitly
restricted).

## What did NOT need changing

D16, D20, F25, F26, F27 — all CONFIRMED with no correction attached. A1-A7,
B11, B12, C13, C14, E22, E24 — all CONFIRMED, several *strengthening* the
campaign's claims (e.g., A6 shown exact rather than merely small; C13/C14
independently re-derived). No text was weakened where the review found the
existing claim already correct.
