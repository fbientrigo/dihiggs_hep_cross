# Contract — `model_point_to_llp_recast`

Status: implemented, canonical, and sole active model-point handoff.

Code: `src/llp_recast/data_contract.py`. Machine-readable mirror (written by
that module's `emit()`, never hand-edited):
`contracts/model_point_to_llp_recast.yaml`. Tests:
`tests/test_data_contract.py`.

The former v1 contract is archived for interpreting old evidence only. It is
not imported, emitted, or accepted as a runtime input.

## Why

`docs/DOWNSTREAM_INTERFACE_GAP_REPORT.md` (produced by a read-only inspection
of this repo from the `dihiggs` side) found v1 cannot represent a high-mass
2HDM H2 point from the `dihiggs` high-mass point factory
(`docs/HIGH_MASS_H2_CONTRACT.md`, `docs/contracts/high_mass_point_schema.yaml`,
`docs/contracts/cascade_contract.yaml` in that repo) without losing
information: no heavy-state masses, no `model_variant`, a single `ctau_mm`
that conflates physical and detector-response lifetime, a 5-of-10-channel BR
list, no cascade-state flags, no production-process identity, and no
provenance distinguishing a canonical MadGraph cross section from a scaling
estimate.

## Minimum required-column list

```
schema_version, point_id, model_variant,
m_h_GeV, m_H2_GeV, m_A_GeV, m_Hp_GeV, Delta_heavy_GeV,
g_hH2H2_GeV,
total_width_GeV, ctau_physical_mm, ctau_response_mm, lifetime_mode,
BR_bb, BR_cc, BR_tt, BR_tautau, BR_WW, BR_ZZ, BR_gg, BR_gammagamma, BR_Zgamma, BR_hh,
production_process, production_owner, decay_owner, response_decay_channel,
H2_to_AZ_open, H2_to_HpW_open, H2_to_AA_open, H2_to_HpHm_open,
theory_status, experimental_status,
sigma_production_fb, sigma_source, sigma_provenance,
producer_commit, config_hash, input_hash
```

39 columns. This is a straight cross-check pass of the mission's field list
against the gap report's findings; every field above is independently
confirmed as a genuine gap by the report (see the report's table for the
field-by-field justification).

## Design decisions

### 1. `sigma_production_fb` provenance (`sigma_source`, `sigma_provenance`)

The canonical evaluator (`DihiggsPointV2Evaluator`) never emits a MadGraph
cross section (`HIGH_MASS_H2_CONTRACT.md` section 8); `sigma_production_fb`
is always a downstream enrichment. v1 had no way to say *how* trustworthy
that number is. The canonical contract adds:

- `sigma_source`: checked enum, `{DIRECT_MADGRAPH_POINT,
  G_SQUARED_SCALING_ESTIMATE, OTHER_ESTIMATE}`. Only
  `DIRECT_MADGRAPH_POINT` is treated as canonical/physically trustworthy by
  `is_canonical_sigma_source()`.
- `sigma_provenance`: free-text/dict field for human-readable production
  context (run id, config, etc.). **Not** consulted for the
  canonical/non-canonical decision — only `sigma_source` gates that. This
  keeps the "is this number trustworthy" question structural (one enum
  check) rather than something a caller has to infer by parsing free text.
- Rows with a non-canonical `sigma_source` are **accepted**, not rejected —
  carrying a scaling estimate is legitimate — but
  `ValidationReport.non_canonical_sigma_rows` records them and `describe()`
  prints an explicit `[info]` line, so a caller cannot silently treat a
  scaling estimate as canonical just because the column is populated.

### 2. Physical vs. response lifetime (`ctau_physical_mm`, `ctau_response_mm`, `lifetime_mode`)

Two distinct required columns, never aliases of each other.

- `ctau_physical_mm` must equal `hbar_c_GeV_mm / total_width_GeV` for
  **every** row, regardless of variant (`rel_tol=1e-6`; v1 used `1e-4` as a
  loose legacy tolerance, the upstream `high_mass_point_schema.yaml` uses
  `1e-9`; `1e-6` is a deliberate middle point — tight enough to catch a
  wrong/independently-guessed lifetime, loose enough to tolerate CSV
  string round-tripping of a value that started as a full-precision float).
- `lifetime_mode=PHYSICAL_PREDICTION` requires
  `ctau_response_mm == ctau_physical_mm` within `rel_tol=1e-9`.
- `lifetime_mode=DETECTOR_RESPONSE_EXPERIMENT` explicitly permits a
  Variant-A response scan to differ from the physical prediction. It is not
  valid for Variant B, which always uses the physical lifetime.
- Both lifetime columns remain required and positive; a missing response
  value is an error, never a silent copy of the physical value.

### 3. `model_variant`

Checked enum: `FACTORIZED_G_ONLY`, `PHYSICAL_DECAYS_NO_HEAVY_CASCADES`. Any
other value is a hard rejection (missing/invalid variant is exactly the kind
of "silently ambiguous" record v1 could produce and v2 must not).

### 4. Cascade-open flags

`H2_to_AZ_open, H2_to_HpW_open, H2_to_AA_open, H2_to_HpHm_open` are required
columns on every row (per `cascade_contract.yaml`, computed as a diagnostic
regardless of variant). The validator only enforces them false
(`false`/`False`/`0`, case-insensitive on the leading token) for
`PHYSICAL_DECAYS_NO_HEAVY_CASCADES` rows; `FACTORIZED_G_ONLY` rows may carry
any value in these columns without failing validation, since that variant
does not claim a complete physical H2 decay model.

### 5. BR invariants — full 10-channel list

`BR_bb, BR_cc, BR_tt, BR_tautau, BR_WW, BR_ZZ, BR_gg, BR_gammagamma,
BR_Zgamma, BR_hh` are all required columns and all participate in the
`sum <= 1` invariant (`abs_tol=1e-6`). v1's sum invariant only covered
`BR_bb, BR_WW, BR_ZZ, BR_gg, BR_tautau` — `BR_cc`, `BR_tt`,
`BR_gammagamma`, `BR_Zgamma`, `BR_hh` were entirely absent, confirmed as a
gap by the report (`BR_tt` in particular is the exact channel Gate A closed
upstream; `BR_hh` opens well inside the high-mass factory's target range).

### 6. Mass hierarchy

`m_h_GeV < m_H2_GeV < m_A_GeV` (strict, no tolerance — these are meant to be
well-separated scan coordinates), `m_A_GeV == m_Hp_GeV`
(`abs_tol=1e-6 GeV`), `Delta_heavy_GeV == m_A_GeV - m_H2_GeV`
(`abs_tol=1e-6 GeV`). Tolerances are absolute (not relative) because these
are typically clean scan-grid coordinates, not the output of a numerically
sensitive calculation; documented here per the mission spec's "exact, or
document your tolerance" instruction.

### 7. Production process identity

`production_process` is a checked enum with exactly one currently-accepted
value: `"pp -> H2 H2"` (`HIGH_MASS_H2_CONTRACT.md` sections 1 and 4: heavy
A/Hp production and cascade feed-down are explicitly out of scope until a
later contract revision). A future `v3` contract would extend this enum,
not this one.

### 8. Decay/production ownership provenance

`production_owner` (`CANONICAL_EVALUATOR` | `DOWNSTREAM_MADGRAPH`) and
`decay_owner` (`CANONICAL_EVALUATOR` | `PYTHIA_FORCED_RESPONSE_STUDY`)
record which pipeline stage is responsible for the production-level and
decay-level numbers in a row — this is what closes the gap report's "Decay
ownership" finding (v1 had no way to distinguish a physical `BR_bb` from a
sample forced 100% to `bb` for a response study). `response_decay_channel`
names the forced channel (or `"NONE"` when nothing was forced). The
validator enforces: `decay_owner == PYTHIA_FORCED_RESPONSE_STUDY` is only
valid on `FACTORIZED_G_ONLY` rows (Variant B never forces a decay,
`HIGH_MASS_H2_CONTRACT.md` section 4) and always requires a real, non-empty
`response_decay_channel`.

These two fields' exact enum values and the cross-field invariant between
them are **not** literally specified by the mission's field list or the gap
report (both only say the field names must exist) — they are this task's
own design to make "decay ownership" a checkable, not just storable,
property. Flagged as a judgment call for the orchestrating session.

### 9. `theory_status` / `experimental_status`

Checked enums (`{PASS, FAIL, UNCHECKED}` and `{PASS, FAIL, UNCHECKED,
NOT_APPLICABLE}` respectively), collapsing the upstream schema's several
boolean theory-validity flags (`construction_ok`, `theory_ok`, etc.) and the
as-yet-unpopulated `experimental_ok` into a single tri/quad-state summary
column per axis, consistent with the upstream contract's "rejected points
are retained, not dropped" philosophy (`NOT_APPLICABLE` covers a row that
has not yet been enriched by a `dihiggs_boundary` handoff, mirroring
upstream's `experimental_ok = nan`). This collapsing (versus carrying the
full upstream flag set verbatim) is this task's own design choice, not
dictated by the mission's field list.

## Historical artifacts

The archived v1 contract and mapping under `docs/archive/` are retained only
to interpret frozen historical outputs. New producers and consumers must use
the canonical named fields above; no compatibility adapter is provided.
