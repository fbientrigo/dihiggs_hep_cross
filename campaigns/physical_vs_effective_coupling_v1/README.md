# physical_vs_effective_coupling_v1

Understand the physical 2HDM h-φ-φ trilinear (2HDMC's `get_coupling_hhh(1,2,2)`),
why the current photonic/mixed benchmark family lands at `M² ≈ m_φ²`, whether
that's required or accidental, how the coupling responds to controlled
variation, and whether the effective prescriptions `EF_simple = 8m_φ²/v` and
`EF_m2 = 8(m_φ²−m₂²)/v` correspond to any physical limit. See
`COUPLING_STUDY_REPORT.md` for the full synthesis, answering the 11
mission-required questions in order.

No MadGraph production was run. Stop condition reached: the physical
coupling, its M² dependence, and its relation (or lack of one) to both
effective prescriptions are now understood analytically and confirmed
numerically. The next coupling-comparison/production campaign is explicitly
**not** started by this mission.

## Layout

- `derivation/` — the analytic work (source trace, closed-form derivation,
  M² mechanism). Read in this order:
  `physical_trilinear_source_trace.md` → `physical_trilinear_derivation.md`
  → `assumptions_and_limits.md`.
- `2hdmc_build/` — private compiled copy of canonical 2HDMC (never modifies
  `~/atlas_dihiggs/dihiggs/2hdmc/`), plus `GeneralProbe.cpp/.o/binary`, the
  instrument behind every numeric claim below.
- `inputs/` — benchmark coordinates and Christopher's production reference
  (both reused from the reviewed photonic-requalification campaign, not
  re-derived).
- `validation/numerical_crosschecks.csv` — independent numeric verification
  of the two closed-form formulas derived in `derivation/`.
- `m2_study/` — Phase 2/3: the M² variation grid at the real benchmark
  (tanβ=4×10⁷) plus an illustrative moderate-tanβ (=10) grid, and single-
  parameter sensitivity probes (λ6, tanβ-at-fixed-M2, λ1).
- `coupling_comparison/` — Phase 6: physical vs. EF_simple vs. EF_m2 table
  and plot.
- `ufo/` — Phase 5: a real `GHphiphi`-externalized UFO copy (2-file diff),
  distinct from the pre-existing, non-functional
  `dihiggs_ufo/LLscalar_v3_UFO_external_GHphiphi/`.
- `logs/run_all_probes.py` — the driver that produced every CSV in
  `validation/`, `m2_study/`, `coupling_comparison/`.

Reproduction: see `COUPLING_STUDY_REPORT.md` §"Exact validation commands".
