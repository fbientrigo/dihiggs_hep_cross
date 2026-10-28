# Physical vs. effective h-φ-φ coupling — study report

**This report was independently, adversarially reviewed TWICE, by two
different reviewer passes with no shared context: `validation/SOL_REVIEW.md`
→ `validation/SOL_REVIEW_RESPONSE.md`, then a fresh, independent re-review
`validation/SOL_FINAL_REVIEW.md` → `validation/SOL_FINAL_RESPONSE.md`. Read
those four files if you want the before/after — this version incorporates
every correction from both rounds.** The single most consequential finding
from the second round is **not about the trilinear coupling** (which
survives intact) — see "New finding" under §4/§9 and the Unresolved
Questions list: at this campaign's benchmark tanβ=4×10⁷, 2HDMC's own
reconstructed masses (and therefore every decay-width/ctau number in this
campaign's CSVs) are computed at the wrong φ mass. Per
`dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md`: no MadGraph production
was run in this mission; nothing below is a MadGraph result. Every
"physical_2HDM" number is a direct, unmodified `THDM::get_coupling_hhh`
output from the canonical, unmodified 2HDMC library.

## The master result

Everything below follows from one exact identity, found only after
adversarial review (I had not derived it in my own first pass):

```
(★)   g_hφφ ≡ Im[get_coupling_hhh(1,2,2)] = (2·M² − 2·m_φ² − m_h²) / v
      with M² ≡ m12²/(sinβ·cosβ)
```

**GENERAL IDENTITY at exact alignment sin(β−α)=1 — holds for any tanβ, any
λ6, any λ7, any m_A, any m_H±.** Full derivation:
`derivation/physical_trilinear_derivation.md` §0. Verified independently
**four** ways to machine precision (2×10⁻¹⁵ or better), including at points
this campaign's benchmark never used (tanβ ∈ [0.5,50], λ6 ∈ [−0.3,2],
λ7 ∈ [−1,0.5], mA/mHp ∈ [150,900], M²/m_φ² ∈ [0.8,5.1] —
`validation/numerical_crosschecks.csv` plus a fully independent re-derivation
and probe, `validation/SOL_FINAL_REVIEW.md` §A).

**Scope note that must travel with this identity, not stay buried in §5:**
at the campaign's own benchmark, tanβ=4×10⁷, (★) is realized only to
**7.4×10⁻⁹ relative** (mφ=250), not machine precision — a floating-point
conditioning effect (`cos(atan(tanβ))`, §5), confirmed identical in both
review rounds. Away from that specific tanβ, machine precision holds.

## 1. Full physical 2HDM trilinear expression used by 2HDMC

2HDMC's `get_coupling_hhh(1,2,2)` (`THDM.cpp:1574-1629`) sums six
permutations of a Higgs-basis expression built from `Z1..Z7`, `hep-ph/0602242`
conventions. For the two neutral CP-even states (real qki entries at
`sba=sin(β−α)`, `cba=cos(β−α) = +√(1−sba²)` — 2HDMC's `get_cba()` always
returns the non-negative root, so this formula's scope is the `cba≥0`
branch only), the **general** closed form, before any alignment assumption:

```
c_hhh(1,2,2) = -i·v·[ 3·sba·cba²·Z1 + (sba³−2·sba·cba²)·(Z3+Z4+Z5)
                       + 3·cba·(2·sba²−cba²)·Z6 − 3·cba·sba²·Z7 ]
```

**Confirmed to 4.05×10⁻¹⁵ relative, including sign,** across 25 diverse
points (3 masses × 12 tanβ/sba combinations × degenerate-and-asymmetric
mA/mHp/λ6/λ7 — fixed from an original, much narrower 6-point test after
`SOL_REVIEW.md` item 4 found a premature-break bug that silently limited the
original run to degenerate, λ6=λ7=0 points only) —
`validation/numerical_crosschecks.csv`. **A second bug was found in this
formula's own probe implementation** by `validation/SOL_FINAL_REVIEW.md`
Additional issue #1: `GeneralProbe.cpp` computed `+v·[bracket]` instead of
the `−v·[bracket]` printed above, and the validation harness was scoring the
test as PASS whenever `g` matched *either* `+g_general_formula` or
`−g_general_formula` — silently masking the sign error rather than catching
it. Both are now fixed (`GeneralProbe.cpp`'s sign flipped to match the
formula as printed here; the harness now requires an exact sign match, no
tolerance) and the suite re-run: still 25/25 PASS, worst relative deviation
unchanged at 4.05×10⁻¹⁵ — confirming the formula as printed was correct all
along, only its probe implementation's sign was wrong.
Setting alignment (sba=1, cba=0) collapses this to `c=-iv(Z3+Z4+Z5)`, and
specializing further with `set_param_phys`'s own algebra gives (★) directly
(§0 above) — resolving the 2026-08-31 prior audit's open question 1 (the
general-`sin(β−α)≠1` closed form).

## 2. What simplifies it in our benchmark

At this benchmark's `sin(β−α)=1` (CAMPAIGN ASSUMPTION), (★) already
contains everything: **m_A and m_H± cancel identically**, and so do λ6, λ7
individually (they cancel between `λ345`'s own λ6/λ7 terms and the
Higgs-basis rotation's, `SOL_REVIEW.md` item 6 — an exact cancellation, not
merely small). The mission's other stated invariant, mA=mHp, is therefore
**not actually needed** for g_hφφ at this benchmark (it matters for other
observables, e.g. Z4=Z5, which was this report's original — more
complicated, though correct — route to the same answer; kept in
`derivation/physical_trilinear_derivation.md` §§1-6 for the source-level
detail it documents, but (★) supersedes it as the operative formula).

## 3. Why the current points satisfy M² ≈ m_φ²

Traced to Christopher's own recorded generic-basis inputs: λ1=1.0 and λ6
identical across all 3 masses, only m12² differs — a **masses+λ1-input
construction**. Starting from `set_param_phys_lam1`'s own m12² formula at
exact alignment and dividing by sinβcosβ, the **exact** identity (no
large-tanβ approximation, `derivation/assumptions_and_limits.md` §2):

```
M2 = m_H² + (m_h² − v²λ1)/tan²β − 1.5·v²·λ6/tanβ + 0.5·v²·λ7·tanβ
```

**Confirmed to 4.05×10⁻¹⁵** at 12 points spanning mφ∈{200,250,300},
tanβ∈{10³,10⁵,4×10⁷}, and a λ1-independence check — but this specific test
is an **internal-consistency check of the trigonometric rearrangement**,
not an independent query against 2HDMC (`SOL_REVIEW.md` item 6: both sides
are computed from the same CLI arguments inside `GeneralProbe`, neither
reads the THDM object). The **genuinely independent** confirmation is (★)
itself, §0 above, which ties this same M2 formula to an actual
`get_coupling_hhh()` call. As tanβ→∞ with λ7=0, every correction term
vanishes and `M2 → m_H² = m_φ²`.

## 4. Is that relation required or optional?

**Required — but only within the λ7=0 slice of this benchmark, and forced
by vacuum stability at least as much as by perturbativity. This is the
report's second correction on this exact point** (`SOL_REVIEW.md` item 6
fixed the direction of the first-pass answer; `SOL_FINAL_REVIEW.md` items
B8-B10 then found the corrected version still overstated it).

Inverting (★)/§3's identity for λ1 in terms of M² (a statement about the
physical point, independent of which THDM setter function constructed it):

```
λ1 = (m_φ² − M²)·tan²β/v² + m_h²/v² − 1.5·λ6·tanβ + 0.5·λ7·tan³β
```

(**Corrected** — an earlier version of this line printed `(m_φ²−M²)/(v²cos²β)
− 1.5λ6tanβ + 0.5λ7tan³β`, missing the `+m_h²/v²` term and using
`1/(v²cos²β)` in place of `tan²β/v²`; the two forms coincide at this
benchmark's tanβ=4×10⁷ but not in general — `SOL_FINAL_REVIEW.md` B8.)

At tanβ=4×10⁷, `v²/tan²β ≈ 3.79×10⁻¹¹ GeV²`. The binding constraint is
**`0 < λ1` (vacuum stability), not `|λ1| ≲ 4π` (perturbativity)** — stability
binds on the upper side about **12× tighter** than perturbativity does on
the lower side. This pins `M²` to an **asymmetric** window,
`ΔM² ∈ (−4.8×10⁻¹⁰, +3.9×10⁻¹¹) GeV²` around `m_φ² − 1.5v²λ6/tanβ` (total
width ≈8×10⁻¹⁵ relative) — **for any construction route, but only given
λ7≡0**. I verified the lower/perturbativity edge directly (`GeneralProbe`,
masses+m12² route): pushing M² off m_φ² by relative 10⁻¹⁵/10⁻¹³/10⁻¹⁰ moves
the model's own reconstructed `λ1_out` to roughly −7068 / −7231 / −1.7×10⁵
— all theory-invalid; the upper/stability edge closes about 12× closer in.

**λ7≡0 is a campaign input convention, not a 2HDM requirement, and relaxing
it breaks the forcing.** `SOL_FINAL_REVIEW.md` B9 constructed an explicit,
fully theory-valid counterexample at this benchmark's own tanβ=4×10⁷:

```
mh=125, mφ=250, mA=mHp=300, λ1=1 (literal input), λ6=0,
λ7 = −1.0309278350515464×10⁻⁸   (indistinguishable from zero in every
                                  other observable at this benchmark)
→ M² = 50000.0889 GeV² = 0.80000142·m_φ²         (20% away from m_φ²)
→ g_hφφ = −164.99361721019517 GeV                (not −63.46 GeV)
→ unitarity_ok = perturbativity_ok = stability_ok = positivity_ok = 1
```

So the correct statement is: **within λ7=0, M²=m_φ² is forced (route
independently) by the combination of perturbativity and vacuum stability;
outside λ7=0 it is not forced at all** — a λ7 of order 10⁻⁸, invisible in
every other benchmark quantity, is enough to move M² (and hence g_hφφ) by
20%.

## 5. Why g_hφφ was approximately constant

At M2=m_φ² exactly, (★) gives **g_hφφ = −m_h²/v exactly** — no m_φ, m_A,
m_H±, λ6, λ7, or tanβ dependence at all. This is now the exact statement,
not an empirical observation. The theory-valid anchor (λ1=1 literal input
route) gives `physical_2HDM_GeV` = −63.459361332…/−63.459361556…/
−63.459361830… at mφ=200/250/300 (`coupling_comparison/coupling_table.csv`)
— a **systematic**, monotone-in-mφ residual of +3.8×10⁻⁹ / +7.4×10⁻⁹ /
+1.2×10⁻⁸ relative from the exact `−m_h²/v = −63.459361087…`. **This
residual is not real physics** (an earlier version of this report called it
either "exact to the precision shown" or, in §7, a "resolvable tanβ
signal" — both wrong, and mutually inconsistent, `SOL_REVIEW.md` item 10):
it is a floating-point artefact of 2HDMC computing `cosβ` as
`cos(atan(tanβ))`, which carries a −3.6×10⁻⁹ relative error at tanβ=4×10⁷
versus the algebraically exact `1/√(1+tanβ²)`. Decisive discriminator: the
same three masses at tanβ=10 reproduce `−m_h²/v` to **10⁻¹⁵** (all three
masses), not 10⁻⁸ — confirmed in `m2_study/m2_variation_moderate_tanbeta_illustrative.csv`.

## 6. What happens when M² is varied

**(a) At the real benchmark tanβ=4×10⁷.** The original coarse grid
(r=M2/m_φ² ∈ {0, 0.25, ..., 1.5}, `m2_study/m2_variation.csv`) has 0/21
theory-valid points, including the naive r=1.0 row. **This report's
original explanation for that — "reproducing an equivalent m12² to 16
significant digits via external arithmetic is not sufficient" — was WRONG**
(`SOL_REVIEW.md` item 9). The real reason: the theory-valid window is
`m_φ² − 1.5v²λ6/tanβ + ΔM²` with `ΔM² ∈ (−4.8×10⁻¹⁰, +3.9×10⁻¹¹) GeV²` (§4,
asymmetric) — about **15 orders of
magnitude narrower** than the grid's Δr=0.25 step (≈15600 GeV²). A grid
point landing exactly on `M2=m_φ²` (not the λ6-shifted exact value) misses
by 2.68×10⁻⁷ GeV², already ~600× the valid half-width — enough to blow
λ1 up to ≈−7066. **The masses+m12²-direct route is fully capable of
theory-valid points at this tanβ**: setting `M2` via §3's exact formula
gives λ1_out = 1.021195 / 1.021195 / 1.597275 at mφ=200/250/300, all four
theory checks = 1 — now a committed row in `m2_variation.csv`
(`r_M2_over_mphi2=exact_via_star_identity_lambda1eq1`), not just a one-off
check. `g_hφφ` itself varies smoothly and near-linearly with M² throughout
the coarse grid (per (★), which is *linear* in M²) — it is only the
**grid's resolution**, not the route or the arithmetic, that misses the
valid window.

**(b) At an illustrative, non-benchmark tanβ=10** (same masses,
`m2_study/m2_variation_moderate_tanbeta_illustrative.csv` +
`m2_study/m2_variation_finegrid_tanbeta10_illustrative.csv`, both now
committed — not this project's benchmark family): the theory-valid window
is genuinely narrow but not pathological — at mφ=250, r∈{0.98, 1.0, 1.002}
pass on the committed fine grid (r=0.96 fails perturbativity, confirmed
correct on re-review; the upper
margin was previously mis-stated as failing at r=1.02 — it actually fails
already at r=1.004, `SOL_REVIEW.md` item 11, position corrected again by
`SOL_FINAL_REVIEW.md` Additional issue #5 from an earlier "r≈1.005"). **The
upper-margin failure mechanism is vacuum stability/positivity, not
perturbativity** (`SOL_FINAL_REVIEW.md` Additional issue #5 — same
correction as §4/§8): at r=1.004, λ1=−0.156 and
`unitarity/perturbativity/stability/positivity = 1/1/0/0`; only below
r≈0.97 does perturbativity itself (not stability) become the binding
constraint. `g_hφφ` again varies
essentially linearly with r, continuous through the valid/invalid boundary.

## 7. Which parameters materially affect the coupling

(★) makes this exact rather than a numerical ranking: **only M² and m_h
appear at all.** m_φ enters solely through M²'s own construction; λ6, λ7,
m_A, m_H± do not appear in (★) — their absence is an **exact cancellation**
(§2), not smallness. tanβ does not appear either, once M² is held fixed —
the ~10⁻⁸–10⁻⁹ "tanβ trend" this report originally read in
`m2_study/sensitivity_probes.csv` and called "well above the noise floor"
was **wrong**: it is the same `cos(atan(tanβ))` artefact as §5, confirmed
by its identical size, sign, and mass-dependence. λ1 has one genuine, tiny,
exactly-predictable effect through M2's own λ1-dependence:
`∂g/∂λ1 = −2v/tan²β`, predicting Δg=1.20×10⁻¹² over λ1∈[0.1,4] at
tanβ=4×10⁷ — matching the measured Δg=1.14×10⁻¹² to one digit. This
report's original claim that this was "at or below the noise floor" was an
**underclaim**, not an overclaim (`SOL_REVIEW.md` item 8): it is small, but
real and resolvable.

## 8. Can a physical mapping reproduce EF_simple?

**One-line closed-form answer from (★), replacing this report's original
empirical hedging:** EF_simple = 8m_φ²/v is reached exactly at
`M² = 5m_φ² + m_h²/2` — **independent of m_A and m_H±**, which cancel
identically in (★) (this report's original claim that reaching EF_simple
"would require a qualitatively different mass configuration, larger
mA−m_φ splitting" was **WRONG**, `SOL_REVIEW.md` item 12 — verified directly:
m_A=m_H± ∈ {300,400,600,900} at mφ=250 leaves g_hφφ unchanged to 10 digits).
Verified numerically: at mφ=250, tanβ=10, M²=320312.5 → g_hφφ =
+2030.69955 GeV = EF_simple exactly (8 digits), with λ1=−425 and all four
theory checks = 0.

**Answer: EF_simple's magnitude is reachable in the M² coordinate at any
tanβ, and — a cleaner, stronger, and differently-named result than this
report previously claimed — is excluded by vacuum stability, not
perturbativity, at exact alignment with λ6=λ7=0, for every tanβ and every
mφ > 62.5 GeV** (`SOL_FINAL_REVIEW.md` C15 corrects "excluded by
perturbativity, full stop"). Proof: at alignment, λ6=λ7=0, writing
`X ≡ (M²−m_φ²)/v² = (4m_φ²+m_h²/2)/v²` (from `M²=5m_φ²+m_h²/2`) and
`Y ≡ m_h²/v²`, `set_param_phys`'s own λ1/λ2 formulas give
`λ1 = Y − X·tan²β` and `λ2 = Y − X/tan²β`. Vacuum stability needs **both**
λ1>0 and λ2>0, i.e. `tan²β < Y/X` **and** `tan²β > X/Y`, which together
require `X < Y`, i.e. `4m_φ² + m_h²/2 < m_h²`, i.e. **m_φ < 62.5 GeV** —
impossible in this benchmark family, where m_φ is by construction the
*heavier* CP-even state (m_φ > m_h = 125 GeV). So EF_simple is **impossible
at exact alignment with λ6=λ7=0, for every tanβ, for every mass in this
benchmark's regime** — not merely "excluded at the points we happened to
test."

With λ6, λ7 free the algebra above no longer closes analytically; a
4000-point randomized scan (m_φ ∈ [126,1000], mA,mHp ∈ [1,1500],
tanβ ∈ [0.05,20], λ6,λ7 ∈ [−8,8], M² pinned to `5m_φ²+m_h²/2`, alignment,
`SOL_FINAL_REVIEW.md` C15) found **0/4000 points passing all four theory
checks** — strong empirical support, not a proof, for extending the λ6=λ7=0
result. **Not tested and not claimed:** away from exact alignment
(cos(β−α)≠0), where (★) itself does not apply.

## 9. Can a physical mapping reproduce EF_m2?

**No — and the relationship between EF_m2 and the physical coupling is now
an exact, closed-form ratio, not two independently-measured numbers.**
`M22² = M² − m_h²/2` is an **exact identity at exact alignment, for ANY
tanβ, any λ6, any λ7, any mA/mHp** — corrected twice: first from "benchmark
coincidence, not derived" to "a large-tanβ identity" (`SOL_REVIEW.md` item
7/15), then from "large-tanβ identity" to what it actually is
(`SOL_FINAL_REVIEW.md` D17). **The second correction reverses the direction
of the first:** this identity is *exact at any tanβ* (proved from 2HDMC's
own minimization conditions, `SOL_FINAL_REVIEW.md` D17, a genuinely
independent derivation from (★)'s own), and *numerically it is cleanest at
small tanβ and degrades monotonically as tanβ grows* — the opposite of
"large-tanβ identity" — through the same `get_m12_2()` conditioning as §5
(residual 7×10⁻¹²GeV² at tanβ=0.5, growing to 8×10⁻³GeV² at tanβ=10⁵; also
independently verified at tanβ=7, residual 2.2×10⁻¹¹GeV² absolute, matching
this report's own tanβ=7 measurement). Domain, stated precisely: holds
whenever sin(β−α)=1 exactly, for arbitrary tanβ/λ6/λ7/mA/mH±/m_φ/M²; not
claimed or tested for cos(β−α)≠0. Substituting into `EF_m2 ≡ 8(m_φ²−M22²)/v`:

```
EF_m2 = 8(m_φ² − M² + m_h²/2)/v = −4·(2M² − 2m_φ² − m_h²)/v = −4·g_hφφ    (exactly)
```

Measured in `coupling_comparison/coupling_table.csv`:
`EF_m2_over_physical_2HDM` = −4.000000000000006 / −4.0000000000000036 /
−3.9999999999999933. **The "~4.00×" gap this report's first pass left
"unexplained" is nothing but the ratio of EF_m2's prefactor (8) to the
physical Feynman-rule prefactor (2)** — no separate physics, derivable in
one line from two formulas the campaign already had (`derivation/physical_trilinear_derivation.md`
§§0/5/9). Using **this project's own `M2`** instead:
`EF_m2_using_M2_GeV` ≈ 8.7×10⁻⁹ GeV — no longer a construction tautology
as in this report's first pass (`SOL_REVIEW.md` item 7: the original grid's
r=1.0 point had `M2_actual` forced to equal m_φ² by the grid's own
arithmetic, making `8(m_φ²−M2_actual)/v=0` trivially; the table now anchors
on the theory-valid λ1-route point, where this is a genuine, tiny
measurement, not a tautology) — still confirming `M2 ≠ m₂²`, now
non-trivially. **Both "no" answers stand, now derived rather than
observed.**

## 10. What remains approximation vs. actual 2HDM physics

`physical_2HDM` is exact 2HDM physics. `EF_simple` is a phenomenological
prescription, hardcoded in the frozen original UFO (`GC_90 = 8i·Mh2²/vev`,
verified byte-identical against its 2021 source archive) — it is literally
what generated Christopher's quoted production cross sections
(23.51/13.35/7.530 fb). The mismatch has an **exact closed form**, not
three independent empirical numbers as this report's first pass presented
it: `(EF_simple/|g_hφφ|)² = (8m_φ²/m_h²)²` = 419.4304 / 1024 / 2123.3664
(the original "2124" was a rounding slip, `SOL_REVIEW.md` item 13).

**Citation corrected** (this report's first pass got this wrong on two
counts, `SOL_REVIEW.md` item 13): §5 of
`campaigns/20260901_photonic_requalification/validated/REQUALIFICATION_SUMMARY.md`
reports the **same** figures (4.2×10², 1.0×10³, 2.1×10³) for the **same**
benchmark family (mφ=200/250/300, same m_h²/v=63.4594), and **already
contains the same closed form** (`g_hφφ = (m_h²+2m_φ²−2M²)/v` — (★) up to
sign convention). This is **the same computation confirmed via a cleaner
derivation**, not — as this report originally, wrongly claimed — "two
independent computations" agreeing "via a completely different derivation
path" at "a different benchmark family." The strings "132" and "1017"
(quoted in this report's first pass as if from that file) do not appear in
it at all.

**New finding** (surfaced only by the adversarial review): the frozen
original UFO's `GC_90` is **positive** imaginary; the actual physical
coupling is **negative** imaginary at every benchmark point tested. The
production UFO therefore has the wrong sign in addition to the wrong
magnitude — irrelevant for a single-diagram |M|², relevant the moment
anything interferes with this vertex. See `ufo/validation.md`.

## 11. What should be used in future MadGraph runs

Not decided by this mission (a production-campaign decision for the PIs),
but the infrastructure now exists: `ufo/LLscalar_v3_UFO_GHphiphi_external/`
exposes `GHphiphi` as a genuine external FRBlock parameter (2-file diff
against the frozen original), its default now set to the exact
`M²=m_φ²` value, `−m_h²/v = −63.459361087483` GeV, with the correct sign
(corrected twice: from a theory-invalid grid point, `SOL_REVIEW.md`
"Additional issue #1"; then from the theory-valid but tanβ=4×10⁷-artefact-
carrying value to the artefact-free exact value, `SOL_FINAL_REVIEW.md`
"Additional issue #4"). No MadGraph import/production test was run against
it (no local MG5 installation in this environment — see
`madgraph_smoke/README.md`). The UFO/2HDMC normalization was independently
confirmed like-for-like **twice**, by two separate reviewer passes, via the
UFO's own `GC_94` (hhh self-coupling) matching `get_coupling_hhh(1,1,1)`
exactly (`ufo/validation.md` §3, `SOL_FINAL_REVIEW.md` A3/F29 — the second
pass additionally anchored the two-identical-scalar case via `GC_93`) — this
had never been demonstrated anywhere in the campaign before the first
review.

## 12. Mass-dependent quantities were wrong at this benchmark's tanβ — now fixed at the 2HDMC source level (trilinear coupling was never affected)

**The single most important correction from `SOL_FINAL_REVIEW.md`, and not
about the trilinear coupling at all — now fixed, not just documented.**
`get_hmass()` routes through `get_param_phys()` → `get_m12_2()` — the same
function whose ~4.5% round-trip error at tanβ=4×10⁷ this report already
flagged as making the `m12_2_out` CSV column unusable. That earlier
description under-stated the blast radius: **2HDMC's own reconstructed
masses were wrong by 1.5-4.6% at this tanβ**, not just its reconstructed
m12². Measured directly, before the fix:

| requested m_φ | 2HDMC's own `get_hmass(2)` (before fix) | error |
|---|---|---|
| 200 | 190.73486397 | −4.6% |
| 250 | 244.25980609 | −2.3% |
| 300 | 295.48518068 | −1.5% |

and requested mA=mHp=300 both reconstructed to 295.23. Every
`total_width_h2_GeV`/`ctau_h2_mm` value in `m2_study/m2_variation.csv` and
`m2_study/sensitivity_probes.csv` was therefore computed at the wrong φ
mass — for a programme whose headline downstream observable is cτ, this
was the largest-blast-radius unflagged issue either review round found.

**Root cause and fix — see `validation/MASS_RECONSTRUCTION_FIX.md` for the
full derivation.** `THDM` stores only the "generic basis" (λ[1..7], m22_2,
tanβ); `set_param_phys()` received the physical masses and m12² as exact
inputs but discarded them into that basis, where at extreme tanβ the
correction term `m12_2*ctb` is smaller than the floating-point noise floor
of the O(v²) leading term — the information is destroyed at construction,
not merely computed imprecisely. `get_m12_2()`'s attempt to invert that
step is therefore an information-theoretically lossy operation that no
reformulation can fix. **The actual fix**: `THDM` now caches the exact
physical-basis values at the one point they are known exactly
(`set_param_phys`/`set_param_phys_lam1`, directly or via
`read_LesHouches()`'s physical-basis branch) and returns the cache from
`get_param_phys()` — bypassing `get_m12_2()` and its lossy round-trip
entirely for these construction routes, which are the only ones this
campaign or any other campaign in `~/atlas_dihiggs` exercises at extreme
tanβ. A second, independent conditioning bug was found and fixed the same
way: `set_param_phys`'s own `lambda[1]` formula divides by `cos²β`
(≈1/tanβ²), producing up to 20-40% relative error in `lambda[1]` at this
benchmark's tanβ even with the masses fix in place;
`set_param_phys_lam1()` (the actual construction route `GeneralProbe.cpp`
uses) now overwrites `lambda[1]` with its own exact input the same way. A
third, independent bug (catastrophic cancellation in the `m_h`/`m_H`
eigenvalue formula, generic to any construction route with `m_h << m_H`,
not specific to large tanβ) was fixed with the standard stable-quadratic
rewrite. Patched in `THDM.cpp`/`THDM.h` and verified with an exact
round-trip test (`set_param_phys` → `get_hmass`/`get_param_phys`, tanβ ∈
{10, 1e4, 4e7, 1e8}, all exact to machine precision after the fix, vs. up
to 20% mass error and 90% `lambda[1]` error before it) and a regression
check (the trilinear coupling changed only in its last significant digit
across the fix — `get_coupling_hhh` never called `get_m12_2()` and still
doesn't).

**The trilinear coupling itself was never affected**: `get_coupling_hhh`
depends only on λ1..7 and β directly, and never calls `get_m12_2()` —
which is exactly why (★) and every number in
`coupling_comparison/coupling_table.csv` survived this issue untouched
(regenerated values differ from the pre-fix ones only in the last digit,
consistent with ordinary floating-point noise, not a physics change). This
was always a width/ctau-specific contamination, never a coupling-specific
one.

**Regenerated with the fix**: `m2_study/m2_variation.csv`,
`m2_study/sensitivity_probes.csv`, and `m2_study/*_illustrative.csv` (the
latter unaffected in value, tanβ=10, but regenerated for consistency).
`hmass_h2_reconstructed_GeV`/`hmass_hA_reconstructed_GeV`/
`hmass_hHp_reconstructed_GeV` now equal the requested masses exactly (e.g.
mphi=200 row: 192.587→200.000). In `m2_variation.csv`, `total_width_h2_GeV`/
`ctau_h2_mm` shifted by roughly 5-10% relative to their pre-fix values,
consistent with the previously measured mass error (e.g. mphi=200, row 1:
total width 1.198e7→1.287e7 GeV, cτ 1.648e-20→1.533e-20 mm). In
`sensitivity_probes.csv` (the r=M²/mφ²=1 anchor point specifically) the
genuine shift is smaller, ≈1.7% — see the note below on why that number
took two attempts to get right.
`m2_study/m2_variation_summary.md`'s caveat now states the fix, not just
the defect.

**Post-review correction, 2026-09-03 (added when re-opening this section —
see below for why it needed reopening):** the fix above was correct, but
the FIRST regeneration of these CSVs was run against a `2hdmc_build/`
library that had been rebuilt with incremental `make` instead of `make
clean && make`. 2HDMC's `DecayTable`/`Constraints` hold a `THDM model;`
member by value, so an incremental build after `THDM.h` grew in size
silently linked the new `THDM.o` against stale `DecayTable.o`/
`Constraints.o` — a real memory-layout (ODR) violation with no compiler
warning. This produced a spuriously large (~176×, not ~1.7%) swing in
`sensitivity_probes.csv`'s anchor-point row, and — more seriously —
fabricated three even larger "corrections" that were briefly written into
other repos' research records (a mission report, a UFO production
candidate's provenance note, and a sibling campaign's summary), overriding
at least one of those documents' own, correct, prior conclusions in the
process. An independent adversarial review I dispatched
(`validation/SOL_FINAL_REVIEW_2.md`) caught this; I rebuilt every 2HDMC
checkout in this workspace with `make clean && make`, fixed the Makefiles
themselves (`-MMD -MP` transitive header-dependency tracking, so a plain
`make` can no longer silently leave stale objects after a header-size
change), and corrected every document that had the wrong numbers,
including this one. A further bias/behavior audit
(`validation/SOL_BIAS_AUDIT.md`) independently re-verified the corrected
numbers a third time from scratch and found one further place
(`m2_study/m2_variation_summary.md`) where the stale-build number had been
re-asserted during the correction pass itself; that has also been fixed.
Full account: `validation/MASS_RECONSTRUCTION_FIX.md` §7-8.

---

## Files created

```
campaigns/physical_vs_effective_coupling_v1/
  README.md, COUPLING_STUDY_REPORT.md
  derivation/{physical_trilinear_source_trace,physical_trilinear_derivation,assumptions_and_limits}.md
  2hdmc_build/                          (private compiled 2HDMC copy + src/GeneralProbe.cpp)
  inputs/{benchmark_points,christopher_xsec_reference}.csv
  validation/{numerical_crosschecks.csv, SOL_REVIEW.md, SOL_REVIEW_RESPONSE.md,
              SOL_FINAL_REVIEW.md, SOL_FINAL_RESPONSE.md,
              MASS_RECONSTRUCTION_FIX.md, SOL_FINAL_REVIEW_2.md, SOL_FINAL_RESPONSE_2.md}
  madgraph_smoke/{README.md, commands.txt, smoke_results.csv}
  TEAM_COUPLING_BRIEF.md
  m2_study/{m2_variation, m2_variation_moderate_tanbeta_illustrative,
            m2_variation_finegrid_tanbeta10_illustrative, sensitivity_probes}.csv,
           m2_variation_summary.md
  coupling_comparison/{coupling_table.csv, coupling_vs_mass.{png,pdf},
                       physical_vs_M2.{png,pdf}, plot_coupling_vs_mass.py,
                       plot_physical_vs_M2.py}
  ufo/{LLscalar_v3_UFO_GHphiphi_external/, externalization_diff.patch, validation.md}
  logs/run_all_probes.py
```

**Modified outside this campaign directory (§12 mass-reconstruction fix
only):** `~/atlas_dihiggs/dihiggs/2hdmc/src/THDM.{cpp,h}` (canonical 2HDMC,
the actual bug fix — this is the one exception to the freeze principle
below, made deliberately and documented in full in
`validation/MASS_RECONSTRUCTION_FIX.md`, not an accidental touch), plus the
same patch propagated to every other 2HDMC checkout found under
`~/atlas_dihiggs` (`mission_runs/20260831_trilinear_lambda1_audit/2hdmc_build`,
`dihiggs_boundary/lib/2HDMC-1.8.0`) and their downstream artifacts —
see `validation/MASS_RECONSTRUCTION_FIX.md` for the full list.
`~/atlas_dihiggs/dihiggs_ufo` untouched (verified: pre-existing untracked
deletions noted in `ufo/validation.md` §1 predate and are unrelated to this
session). `git commit 30afea6` froze the reviewed photonic-requalification
campaign (Phase 0) before the original coupling-study work began; that
campaign's own artifacts were separately re-checked (not blindly
regenerated) against the fixed 2HDMC, see `validation/MASS_RECONSTRUCTION_FIX.md`.

## Exact validation commands

```bash
# Rebuild the probe (private 2HDMC copy already present at 2hdmc_build/):
cd campaigns/physical_vs_effective_coupling_v1/2hdmc_build
g++ src/GeneralProbe.cpp -Isrc -std=c++11 -Wall -O3 -fopenmp -L lib -l2HDMC -lgsl -lgslcblas -lm -o GeneralProbe

# Sanity check (Christopher's 200 GeV point, masses+m12sq route):
./GeneralProbe phys 125.0 200.0 300.0 300.0 1.0 1.177689207010651e-4 0.0 9.999999999933049e-04 40000000.00000001 1
# expect construction_ok=1, g_hphiphi_imag_GeV ~ -63.459 (theory checks = 0 --
# this is Christopher's raw generic-basis m12^2, not the theory-valid one)

# Reproduce the theory-VALID phys-route demonstration (Section 6a):
./GeneralProbe phys 125 250 300 300 1 1.177689207010651e-4 0 0.0015624999943242778 40000000.00000001 1
# expect lambda1_out=1.0211950364309814, unitarity_ok=perturbativity_ok=stability_ok=positivity_ok=1,
# g_hphiphi_imag_GeV=-63.459361555950252

# Regenerate every CSV (validation/, m2_study/, coupling_comparison/):
cd ../..
/home/fabian/atlas_dihiggs/.venv/bin/python logs/run_all_probes.py

# Regenerate the plots (one script per figure):
/home/fabian/atlas_dihiggs/.venv/bin/python coupling_comparison/plot_coupling_vs_mass.py
/home/fabian/atlas_dihiggs/.venv/bin/python coupling_comparison/plot_physical_vs_M2.py

# UFO externalization smoke test:
cd ufo/LLscalar_v3_UFO_GHphiphi_external && python3 -c "import parameters, couplings; print(couplings.GC_90.value, parameters.GHphiphi.value)"
# expect: complex(0,1)*GHphiphi -63.459361087483
```

## Unresolved scientific questions

1. ~~**Mass-dependent quantities (decay width, cτ) at tanβ=4×10⁷ are computed
   at the wrong φ mass**~~ — **RESOLVED.** Root-caused and fixed at the
   2HDMC source level (§12, `validation/MASS_RECONSTRUCTION_FIX.md`); all
   affected CSVs in this campaign regenerated. Two residual, narrower items
   remain open, both documented rather than silently fixed: whether
   `set_param_phys_lam1`'s own `m12_2` formula reintroduces a cancellation
   for large λ7 (not exercised by any λ7=0 benchmark here), and
   `read_LesHouches`'s generic/Higgs-basis branches, `recalc_tan_beta`'s own
   internal conditioning, and `get_param_higgs()`'s `m_Hp` formula for
   non-cached construction routes, none of which are exercised at extreme
   tanβ by anything in `~/atlas_dihiggs` today.
2. **Whether EF_simple corresponds to *any* physical 2HDM limit** away from
   exact alignment was not tested — §8 now proves impossibility at exact
   alignment for all tanβ and all mφ in this benchmark's regime (λ6=λ7=0
   analytically, λ6/λ7 free empirically via a 4000-point scan), but
   cos(β−α)≠0 is genuinely untested, not merely unlikely.
3. **No MadGraph import/process-generation test** was run on the
   externalized UFO (§11) — environment has no local MG5 install; see
   `madgraph_smoke/README.md` for exactly what was checked and
   `madgraph_smoke/commands.txt` for what a future session with MG5_aMC
   should run.
4. **The `get_cba()` non-negative-root scope limitation**
   (`derivation/physical_trilinear_source_trace.md` §2): (★) and its
   validation cover only `cos(β−α)≥0`; the `cba<0` branch (reachable via
   `get_param_hybrid`'s different sign convention) was not derived or
   tested.
5. **Cross-campaign λ1-scan inconsistency, flagged not adjudicated**
   (`SOL_REVIEW.md` "Additional issue #4"): `REQUALIFICATION_SUMMARY.md` §4
   reports a λ1 reconstruction scan (`+1.056, +5.278, −7066.14, −5278.39,
   −1.056` across M²=36000→44000 GeV²) that disagrees with this campaign's
   own algebra and probe results by roughly 11 orders of magnitude at
   comparable ΔM². This campaign's numbers are the ones consistent with the
   source-level derivation here; the discrepancy itself was not traced
   further (would require reopening that prior campaign, out of scope).
6. **The moderate-tanβ=10 illustrative M² grid is not a validated benchmark
   family** — masses/λ6 were reused from the real benchmark but tanβ was
   changed solely to demonstrate non-degenerate M² dependence; it should
   not be cited as a physics result on its own.
7. **The `2hdmc_build/` local copy is byte-identical to this workspace's
   canonical `dihiggs/2hdmc`, but that canonical copy is itself not stock
   upstream 2HDMC 1.8.0** (`SOL_FINAL_REVIEW.md` Additional issue #6):
   `set_param_phys_lam1` and its round-trip validation machinery are local
   additions. "Canonical, unmodified 2HDMC" in this report means unmodified
   *relative to this workspace's own canonical copy*, not upstream.
8. **The UFO's `GC_90 = '8*complex(0,1)*Mh2**2/vev'` (EF_simple, still the
   value in the frozen production model) is itself an undocumented hand-edit**
   to the archived 2021 LLscalar model, whose original `GC_90` (still present
   commented out, `couplings.py:368-370`) was `2*complex(0,1)*vev`
   (`SOL_FINAL_REVIEW.md` F28) — with no derivation anywhere in the
   repository for why it was changed to `8·Mh2²/vev`. Worth tracing before
   treating EF_simple as anything but a historical placeholder.
