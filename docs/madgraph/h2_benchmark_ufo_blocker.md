# H2 benchmark UFO blocker

The frozen `H2scan_mH150_tb300000` candidate is ready for a downstream
`H2H2 -> 4b` handoff, but the active Pack A UFO cannot represent that physical
construction. The bridge therefore emits `BLOCKED_BY_UFO`; it does not run
MadGraph or create a cross section.

Run the static bridge with:

```bash
python scripts/13_h2_benchmark_handoff.py \
  --candidate /home/fabi/atlas_dihiggs/main_dihiggs/benchmarks/FIRST_H2_RECAST_CANDIDATE.json \
  --ufo /home/fabi/atlas_dihiggs/ufos/releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip \
  --output /tmp/h2_benchmark_handoff.json
```

The JSON preserves `m12_sq_construction_GeV2` and
`M2_construction_GeV2`. The roundtrip-reconstructed `m12_sq` is recorded only
under `roundtrip_diagnostic` with `accepted_as_construction: false`. Any
candidate whose `soft_scale_export_status` is not
`VALIDATED_BY_SET_PARAM_PHYS_REPLAY` is rejected before the UFO is inspected.

The static inspection records these exact blockers:

1. Pack A is not a full 2HDM UFO. The expected `mA=450 GeV`, `mHp=450 GeV`,
   `tan_beta=300000`, alignment, `lambda1/lambda6/lambda7`, Type-I selector,
   construction `m12_sq/M2`, and `h2->bb` inputs have no UFO parameter names.
2. The only mass parameter is `Mh2` (default `200 GeV`, expected `150 GeV`);
   the internal width is `Wh2=1.9732698e-16/ctauh2` with default
   `ctauh2=0.1`, not the expected `4.56118529862185e-14 GeV`.
3. Pack A accepts only `PI_FIXED` and uses `GC_90` for `H h2 h2`, so the
   replay-validated physical construction cannot determine the production
   coupling.
4. Pack A generates `h2` stable in LHE; its declared `bb` decay runtime remains
   pending, so the requested displaced `bb` chain is not validated.

The bridge reads ZIP members as text/JSON only. It never imports or executes
UFO Python.
