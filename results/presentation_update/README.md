# Presentation update: g² scaling and kinematic stability near the validated H2 benchmark

## 1. Question

Around the validated 2HDM benchmark (mH2 = 150 GeV, ctau = 4.326 mm, |g_hH2H2| = 63.591 GeV,
BR(H2→bb) = 0.7567), two approximations were tested:

- **Production**: does `sigma(point) = sigma_ref * (g_hH2H2(point) / g_hH2H2(ref))^2`
  correctly predict the direct MadGraph cross section for nearby physical 2HDM points?
- **Kinematics**: do nearby physical points change event kinematics enough that the
  current `A×epsilon = A×epsilon(ctau)` approximation used by the Trackless recast might
  need revisiting?

The production process is `g g > H(125.13, SM-like) > h2 h2` — an **off-shell** SM Higgs
propagator (h2h2 invariant mass ≥ 300 GeV, far above the 125 GeV pole), which is why the
cross section is tiny (~0.23 fb) and, as shown below, sensitive to the h2h2 production
threshold in a way that a pure coupling-squared rescaling cannot capture.

## 2. Points

Five points were evaluated: the benchmark plus 4 alternates, each differing from the
benchmark along **one** physical axis (M2, tan β, or mH), using the same canonical
evaluator (`DihiggsPointV2Evaluator`, schema `dihiggs.point.v2`) that reproduces the
benchmark to 5–6 significant figures.

**M2 could not be used as an independent axis.** At this benchmark's tan β = 3×10⁵, the
theory-validity constraint (positivity/unitarity/perturbativity) pins M2 to mH² to within
~10⁻⁶ GeV² (an amplification of tan²β/v² ≈ 1.5×10⁶) — the benchmark sits essentially
exactly on this critical surface. A finer consequence, checked explicitly: **g_hH2H2 is
invariant to better than 0.001% across every theory-valid point found in this
neighborhood** (mH swept 127–300 GeV, tan β swept 1×10⁵–1×10⁶, and M2 swept across the
full accessible window at fixed mH) — in this exact-alignment (sin(β−α)=1), λ6=λ7≈0
slice, g_hH2H2 is controlled almost entirely by mh and the λ1=1 tuning that defines
the benchmark, not by mH/tan β/M2 individually. This is itself a genuine finding, not a
search failure — see points.csv for the full 2HDMC diagnostics.

The 4 alternates actually used (all theory-valid: construction_ok = theory_ok_v1 =
width_ok = 1):

| point_id | role | changed vs. benchmark | mH | tan β | ctau (mm) | BR(bb) |
|---|---|---|---|---|---|---|
| H2scan_mH150_tb300000 | benchmark | — | 150 | 3.0e5 | 4.326 | 0.7567 |
| H2scan_mH130_tb300000 | mH_down | mH only (M2 retuned to stay theory-valid) | 130 | 3.0e5 | 5.053 | 0.7858 |
| H2scan_mH170_tb300000 | mH_up | mH only (M2 retuned to stay theory-valid) | 170 | 3.0e5 | 3.739 | 0.7250 |
| H2scan_mH150_tb240000 | tb_down | tan β only (M2, mH untouched) | 150 | 2.4e5 | 2.769 | 0.7567 |
| H2scan_mH150_tb360000 | tb_up | tan β only (M2, mH untouched) | 150 | 3.6e5 | 6.230 | 0.7567 |

Full parameters, 2HDMC diagnostics, and derived quantities: `points.csv`.

## 3. Production result

**Direct MadGraph does NOT agree with g² scaling within current precision along the mH
axis; it agrees exactly along the tan β axis.**

| point | sigma_MG (fb) | sigma_g² pred. (fb) | ratio MG/g² |
|---|---|---|---|
| benchmark | 0.2265 ± 0.0016 | 0.2265 | 1.000 |
| mH=130 | 0.3874 ± 0.0027 | 0.2265 | **1.710** |
| mH=170 | 0.1347 ± 0.0010 | 0.2265 | **0.595** |
| tan β=2.4e5 | 0.2265 ± 0.0016 | 0.2265 | 1.000 |
| tan β=3.6e5 | 0.2265 ± 0.0016 | 0.2265 | 1.000 |

The tan β result is exact (not just consistent within uncertainty): tan β only affects
h2's decay width/ctau, not the production matrix element, and since g_hH2H2 is unchanged,
the two production runs are literally reproducing the same physics as the benchmark.
This is a clean internal-consistency check, not new physics.

The mH result is the substantive finding: **even though g_hH2H2 is unchanged to <0.001%**,
direct production differs from the benchmark by +71% (mH=130) and −40% (mH=170). This
is driven by the h2h2-pair production threshold/propagator virtuality shifting with mH,
an effect the g²-only approximation has no way to capture. See
`sigma_direct_vs_g2.png`/`.pdf`.

**Status: the g²-scaling approximation is suggestive/adequate only along directions that
leave the production kinematics unchanged (e.g. tan β here); it fails by 40–70% along a
±20 GeV mH shift at fixed coupling, and should not be assumed valid without checking the
production-side kinematics explicitly.**

## 4. Kinematics

Parton-level H2 kinematics were read directly from the MadGraph LHE output (10,000
events/point, seed 101) for the benchmark plus 3 alternates (mH=130, mH=170, tan
β=3.6e5), chosen per the largest g²-scaling deviation (mH=130), the opposite mH
direction (mH=170), and a point close to g² scaling but physically different (tan
β=3.6e5).

**Pythia8 is not installed on this host** (checked; only a non-functional stub exists in
an ephemeral pytest fixture). This blocks two things the mission asked for: the existing
validated displaced-vertex machinery (`pythia_full_driver.cc`, which produces
L3D_mm/Rxy_mm and underlies the Trackless A_eff(ctau) curve) and any shower+jet-level
observable (leading-jet pT, HT). Those plots are not included; this is an infrastructure
gap, not a physics result, and installing a shower MC was judged out of scope for this
controlled experiment. `h2_pt`, `h2_boost`, and `deltaR(H2,H2)` — all obtainable directly
from LHE without showering — are included.

- **pT(H2)**: median shifts −5.4% (mH=130) / +1.4% (mH=170) vs. benchmark; visible but
  modest shape change (`h2_pt.png`/`.pdf`).
- **H2 boost (βγ)**: median shifts **+8.2% (mH=130) / −9.1% (mH=170)** — the most
  sensitive observable found; visibly different peak position (`h2_boost.png`/`.pdf`).
- **ΔR(H2,H2)**: median shift <0.1% in all cases — the pair stays back-to-back
  (ΔR ≈ π) regardless of point; no meaningful shape change (`deltaR.png`/`.pdf`).
- tan β=3.6e5 kinematics are **bit-for-bit identical** to the benchmark (expected: tan β
  does not enter the production matrix element).

Full medians/deciles: `tables/kinematic_summary.csv`.

**Status: exploratory.** An 8–9% shift in the characteristic H2 boost along the mH axis
is a real, non-normalization shape change — the lab-frame decay length distribution at
fixed ctau depends on boost, so this is not automatically captured by an ctau-only
A×epsilon curve. It is not, by itself, proof that A×epsilon(ctau) is insufficient;
that requires propagating this boost shift through the actual recast, which needs
Pythia8 and was not run here.

## 5. Recast implication

**Is there credible evidence that nearby physical points change analysis-relevant event
shapes rather than only normalization? Suggestive, not conclusive.**

- The mH axis changes both normalization (σ, by up to 71%) *and* shape (H2 boost, by up
  to 9%) simultaneously — exactly the combination that a ctau-only A×epsilon curve is
  not designed to capture.
- The tan β axis changes neither shape nor the g²-scaling-relevant normalization (only
  ctau/BR, which the existing A×epsilon(ctau) curve already parametrizes directly).

Per the mission's stop-gate: this does **not** justify launching a new recast campaign.
**Recommended next step, if compute allows:** install Pythia8 (currently absent) and run
the existing `pythia_full_driver.cc` + Trackless recast wrapper (already validated, no
new development needed) for exactly two points — **mH=130** (largest σ deviation and
largest boost shift, same direction) and **mH=170** (opposite-sign check) — to see
whether the measured A_eff(ctau) at their respective ctau values differs from the
existing interpolated curve beyond MC statistics. Both already have MadGraph events on
disk; no new production would be needed.

## Reused vs. new code

- Reused unmodified: `DihiggsPointV2Evaluator` (2HDMC evaluator), `THDM::get_coupling_hhh`
  convention for g_hH2H2, `run_physical_point_madgraph.py` (one-line timeout parameter
  change only, disclosed in `manifest.json`), the existing UFO/proc_dir.
  `pythia_full_driver.cc` was **not** modified or run (Pythia8 unavailable).
- New (minimal, this session only): LHE parton-level kinematics extraction (no existing
  code computed pT(H2)/boost(H2)/ΔR(H2,H2) anywhere in the workspace); the ΔR(H2,H2)
  definition here is new to this project (no prior ΔR(bb)/ΔR(H2,H2) convention existed)
  — standard ΔR = sqrt(Δη² + Δφ²) between the two LHE-level h2 four-vectors.
