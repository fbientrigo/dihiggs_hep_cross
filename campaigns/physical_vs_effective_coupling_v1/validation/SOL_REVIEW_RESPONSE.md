# Response to SOL_REVIEW.md

Every WRONG / UNSUPPORTED / NUMERICALLY_UNSTABLE item, addressed with new
evidence or by removing/correcting the claim. I independently re-verified
Sol's counter-claims myself (not just trusted them) before acting — see the
GeneralProbe invocations in this session; the three load-bearing new checks
are now committed: `numerical_crosschecks.csv` `test_name=star_identity_independent_via_coupling`
(formula ★, 4/5 PASS — the one FAIL is itself informative, see item 10
below), `m2_variation.csv`'s `exact_via_star_identity_lambda1eq1` rows (now
theory-valid at all 3 masses, where the coarse grid was 0/21), and
`m2_variation_finegrid_tanbeta10_illustrative.csv` (committed; previously
only reported in prose).

**The master fix, applied throughout:** formula
`(★) g_hφφ = (2M² − 2m_φ² − m_h²)/v` (exact, alignment, any tanβ/λ6/λ7/mA/mHp)
is now the primary derived result — verified independently at my own
asymmetric test point (rel. dev. 3.3×10⁻¹⁶, mA≠mHp, λ6,λ7≠0, tanβ=7) and via
the new committed `star_identity` test set. See
`derivation/physical_trilinear_derivation.md` §0.

## Item-by-item

**Item 1 (WRONG wording defect):** "index 1 = SM-like" corrected to "index 1
= lighter CP-even eigenstate (coincides with SM-like only at exact
alignment)" in `physical_trilinear_source_trace.md`.

**Item 2 (sign bookkeeping WRONG in two places):** `coupling_table.csv`'s
`physical_2HDM_GeV` is now the **signed** value (`run_all_probes.py` no
longer calls `abs()`); report §5 rewritten to quote −63.4594, not +63.4594.
`ufo/validation.md` §2's false "signed quantity" claim and its citation of a
nonexistent `numerical_crosschecks.csv` column are both fixed. The
`get_cba()`-always-non-negative scope limitation is now stated explicitly in
`physical_trilinear_derivation.md` §1.

**Item 4 (validation set misdescribed, WRONG):** `run_all_probes.py`'s Step
1a premature-break bug fixed (it broke after 6 theory-valid points, all from
the first, least-diverse block); now runs all 25 diverse points (3 masses ×
12 tanβ/sba combos × 2 mA/mHp/λ6/λ7 configurations, degenerate and
asymmetric) with no early exit. 25/25 PASS, worst rel. dev. 4.05×10⁻¹⁵. The
report's description now matches the CSV.

**Item 6 ("optional" conclusion WRONG; validation CIRCULAR):**
`assumptions_and_limits.md` §4 rewritten: M²=m_φ² is **forced** by
perturbativity at this tanβ, route-independently, to relative ~10⁻¹⁴–10⁻¹⁵
(re-derived and independently spot-checked via `GeneralProbe`: pushing M²
off m_φ² by relative 10⁻¹⁵/10⁻¹³/10⁻¹⁰ moves λ1_out to the hundreds/thousands,
confirmed on my own re-run, not just Sol's). §5's arithmetic error (claimed
2.68×10⁻⁴ GeV², actual 2.678×10⁻⁷ GeV², a factor-1000 slip) corrected. Step
1b's circularity is now disclosed in-script and in the CSV note column; the
genuinely independent replacement is the new `star_identity_independent_via_coupling`
test set.

**Item 7 (§9 "definitively"/"quantitative" overclaim on a tautology):**
`EF_m2_using_M2_GeV` is no longer a construction tautology — the coupling
table now anchors on the theory-valid λ1-route point, where `M2_actual` is
not forced to equal m_φ² by the grid's own arithmetic; it comes out to
8.7×10⁻⁹ GeV² away from zero, a genuine (tiny) measurement. The
`M22²=M²−m_h²/2` large-tanβ identity (closing the prior audit's open
question 2) is now stated in `physical_trilinear_derivation.md` §0, sourced
from Sol's derivation and independently spot-checked by me at tanβ=7 (diff
2.2×10⁻¹¹ GeV² absolute, matching Sol's tanβ=7-scale numbers).

**Item 9 (mechanism WRONG; CSVs NUMERICALLY_UNSTABLE):** `GeneralProbe.cpp`'s
input-echo columns changed from `%.10g` to `%.17g` (full round-trip
precision) and rebuilt — CSVs are now self-reproducing from their own
printed inputs. §6a's mechanism claim ("only the λ1 route can be
theory-valid... external arithmetic is insufficient") is **removed and
replaced**: I independently reproduced Sol's decisive test myself (not
just read it) — the phys route (masses+m12² direct) **does** give
fully theory-valid points at tanβ=4×10⁷ at all three masses (λ1_out =
1.021195, 1.021195, 1.597275; all four theory flags = 1) when M² is set via
the campaign's own exact identity rather than a naive `r*m_φ²`. This is now
a committed grid row (`m2_variation.csv`, `r_M2_over_mphi2=exact_via_star_identity_lambda1eq1`),
not just a one-off check. The correct statement: 0/21 coarse-grid points
pass because Δr=0.25 (≈15600 GeV² steps) is enormously coarser than the
theory-valid window (~10⁻⁹–10⁻¹⁰ GeV² wide at this tanβ) — a **grid-resolution**
artefact, not a route or arithmetic-precision limitation.

**Item 10 (exactness claim UNSUPPORTED; §7's "resolvable" trend WRONG):**
Report §5 rewritten to state the exact, m_φ-independent physics via (★) —
g=−m_h²/v exactly at M²=m_φ² — and to separately, explicitly flag that the
~10⁻⁸ mass-dependent spread visible in the raw CSV numbers at tanβ=4×10⁷ is
a floating-point artefact (2HDMC's `cos(atan(tanβ))` vs the algebraically
exact `1/√(1+tanβ²)`, a −3.6×10⁻⁹ relative error at this tanβ — I did not
re-derive this root cause myself beyond confirming the tanβ=10 vs tanβ=4×10⁷
contrast Sol used as the discriminator; re-ran that contrast independently
and it reproduces). §7's "well above the noise floor" tanβ-trend claim is
**removed** — it was the same artefact, not a real tanβ-dependence of the
physics.

**Item 12 (§8 "larger mA splitting" WRONG):** Removed. (★) makes g_hφφ
exactly independent of m_A and m_H± at alignment — verified directly: I
re-ran `GeneralProbe` at m_A=m_H± ∈ {300, 500, 800} (mφ=250, tanβ=10) and
confirmed g_hφφ unchanged beyond the 10th digit. §8 rewritten around the
one-line closed-form answer (★) gives directly: EF_simple is reached at
M²=5m_φ²+m_h²/2, always excluded by perturbativity, independent of any mass
configuration.

**Item 13 (citation WRONG — "132×-1017×" not in the cited file; "different
benchmark family" WRONG):** Both claims removed. §10 rewritten: the
(EF_simple/physical)² figures are shown as the **exact closed form**
`(8m_φ²/m_h²)²` (419.43, 1024, 2123.37 — Sol's rounding correction applied,
"2124" fixed), and the comparison to `REQUALIFICATION_SUMMARY.md` §5 is
now correctly described as **the same benchmark family, the same numbers,
already containing the same closed form there** — a confirmation of an
existing result via a cleaner derivation, not independent corroboration
from a different family.

**Additional issue #1 (flagship table built from a theory-invalid point):**
Fixed. `coupling_table.csv` is now built from the λ1-route (λ1=1 literal
input) point at each mass, with an assertion in `run_all_probes.py` that it
is theory-valid before being written (`assert theory_ok(row)`), and a
`construction_route` column documenting this. `ufo/validation.md`'s
hardcoded `GHphiphi` default updated to the theory-valid value
(−63.459361555950252, from `coupling_table.csv`) instead of the old
theory-invalid phys-route value.

## Not changed / disposition of remaining items

- **Item 3, 5, 8, 14, 15:** CONFIRMED by Sol with no defect requiring a
  fix, or (item 15) already resolved and folded into §0/§9's rewrite.
- **Item 2's cba≥0 branch, item 11's "well-posed as a coordinate scan":**
  CONDITIONAL/CONFIRMED findings incorporated as explicit caveats rather
  than requiring a structural fix.
- **UFO sign mismatch (frozen original UFO has positive-imaginary GC_90
  vs. the physical coupling's negative-imaginary sign):** newly surfaced by
  Sol, not previously stated anywhere in the campaign. Added to
  `COUPLING_STUDY_REPORT.md` §11 and `ufo/validation.md` as a new,
  previously-undisclosed finding — relevant the moment any interference
  calculation is done, irrelevant for a single-diagram |M|².
- **`get_m12_2()`'s own 4.5% round-trip bug (Additional issue #2):**
  documented as a new caveat in `derivation/physical_trilinear_source_trace.md`
  rather than fixed (it is a pre-existing 2HDMC/CalcLH behavior, out of
  scope to alter — `m12_2_out` columns in all CSVs are now explicitly
  marked unusable).
- **Cross-campaign λ1 inconsistency (Additional issue #4):** flagged, not
  adjudicated, per Sol's own framing — noted in the report's unresolved
  list as a question for whoever revisits the earlier campaign's λ1 scan,
  not something this mission's scope permits resolving (would mean
  reopening `christopher_requalification_20260826`, explicitly out of
  scope).
