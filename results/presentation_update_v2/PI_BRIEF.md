# PI Brief: is the fixed-mass g_hH2H2 direction testable against direct MadGraph?

## Question

The previous campaign found that direct MadGraph production tracks g² scaling
exactly along tan β (production-blind) but disagrees by 40–71% along mH
(±20 GeV), even though g_hH2H2 barely moved. That left an ambiguity: is g²
scaling actually being tested at fixed mass, or is g_hH2H2 simply frozen at
fixed mH by theory constraints, making the tan β "agreement" trivial rather
than informative? This mission tests whether **any** physically valid,
fixed-mH=150 GeV direction in the 2HDM parameter space can move g_hH2H2 enough
to mount a meaningful direct-MadGraph-vs-g² comparison.

## Domain tested

- **mH**: fixed at 150 GeV (Region I: mH < 2·mh ≈ 250.26 GeV, H2→hh closed).
- **tan β**: logarithmic, primary range 1×10⁴ – 1×10⁶ (11 points, denser near
  3×10⁵ = benchmark), plus diagnostic probes at 3×10⁶ and 9×10⁶ — explicitly
  **below** the declared 1×10⁷ numerical ceiling. That ceiling is an
  operational limit of 2HDMC's floating-point precision at extreme tan β, not
  a physical boundary of the 2HDM.
- **M2**: not scanned as an independent coordinate. At each tan β, M2 was set
  by Newton correction to the evaluator's own lambda1_reconstructed=1 (using
  the model's exact linear relation lambda1 ≈ [mh² + tanβ²(mH²−M2)]/v², solved
  to <1e-9 residual), then the theory-valid M2 **window** around that center
  was found by direct bisection on `theory_ok_v1` (positivity ∧ unitarity ∧
  perturbativity) — not assumed.
- **lambda6**: swept from the benchmark value (1×10⁻¹⁰) through decades in
  both signs up to |lambda6|=10 (a deliberately generous numerical ceiling),
  at fixed mH=150, tan β=3×10⁵, M2 = manifold center.

All points generated exclusively via `DihiggsPointV2Evaluator`
(2HDM physical params → 2HDMC → derived couplings/widths). No coupling,
width, ctau, or BR was set directly at any point.

## Main result

1. **M2/tan β axis**: the theory-valid M2 window shrinks from 2.5×10⁻³ GeV²
   (tan β=1×10⁴, loosest end of the primary range) to 2.8×10⁻⁶ GeV² (tan
   β=3×10⁵, the benchmark) — confirming and quantifying the M2≈mH²
   knife-edge. **Max |Δg/g| achievable anywhere in these windows: 2.5×10⁻⁷
   (best case) down to 2.7×10⁻¹⁰.**
2. **lambda6 axis**: theory-valid over a much wider *absolute* range,
   [−7.09×10⁻⁶, +2.22×10⁻⁶] (bisected boundary), but **g_hH2H2 varies by only
   ~1×10⁻¹⁴ relative** across the entire window — indistinguishable from
   2HDMC's own floating-point noise floor. lambda6 does not couple to
   g_hH2H2 at this alignment point.
3. Both tested directions fall **6 to 13 orders of magnitude** below the
   ~0.7% MadGraph Monte Carlo statistical floor that would be needed for any
   g-driven cross-section difference to be observable.

## Interpretation

In the exact-alignment (sin(β−α)=1), Type-I, lambda1≈1-constructed slice that
defines this benchmark, g_hH2H2 at fixed mH is controlled almost entirely by
mh (fixed at 125.13 GeV) and the lambda1≈1 condition itself — not
independently by M2, tan β, or lambda6. Within this slice, the fixed-mass
manifold **collapses to a single point in g_hH2H2-space**: every
theory-valid point at mH=150 GeV has essentially the same coupling. This
explains, rather than merely confirms, the previous campaign's exact tan β
agreement: it was never a nontrivial test of sigma∝g², because tan β cannot
move g at fixed mass. The mH-axis disagreement (40–71%) is therefore not in
tension with sigma∝g² as a coupling relation — it reflects mH changing the
production phase space/threshold, a channel g²-only scaling was never able to
capture in the first place.

## Caveat

This is a property of the **tested slice** — exact alignment, Type-I Yukawa,
the specific lambda1≈1 construction, mA=mHp=mH+300, lambda7=0 — not a
universal statement about the 2HDM. A different alignment point, a different
lambda1 target, or a genuinely 2-dimensional scan relaxing sin(β−α) could in
principle reopen this direction, but that lies outside this session's frozen
model contract and failure policy. This result also does **not** prove or
disprove sigma∝g² as a general approximation — it shows only that the
fixed-mH direction cannot be used to test it here.

## Decision

**No further work needed on this question.**

The ambiguity left by the previous campaign is resolved: g_hH2H2 cannot be
varied meaningfully at fixed mH=150 GeV in this benchmark's slice, by margins
of 6–13 orders of magnitude below what MadGraph could resolve. The
scientifically live question remains the mH-axis phase-space effect (already
quantified in the previous campaign, `presentation_update/README.md`), for
which the standing recommendation (install Pythia8, run the existing
Trackless wrapper on the mH=130/170 samples already on disk) is unchanged and
still blocked on infrastructure (`pythia_probe.md`, `BLOCKED_PYTHIA`).
