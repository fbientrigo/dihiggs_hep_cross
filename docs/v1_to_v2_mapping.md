# `model_point_to_llp_recast_v1` -> `v2` column mapping

`v1` (`contracts/model_point_to_llp_recast_v1.yaml`,
`src/llp_recast/data_contract.py`) is **untouched** by the introduction of
`v2` (`contracts/model_point_to_llp_recast_v2.yaml`,
`src/llp_recast/data_contract_v2.py`). This document is a reference for an
existing `v1` consumer that wants to understand what changed, not a
migration script — there is no automatic `v1`-row-to-`v2`-row converter,
because several `v2` fields (`model_variant`, `g_hH2H2_GeV`, cascade flags,
`sigma_source`, ownership fields) carry information `v1` rows never
recorded and cannot be safely inferred after the fact.

## Columns carried forward unchanged (same name, same meaning)

| v1 | v2 |
|---|---|
| `point_id` | `point_id` |
| `total_width_GeV` | `total_width_GeV` |
| `sigma_production_fb` | `sigma_production_fb` (now gated by the new `sigma_source` field — see below) |
| `BR_bb` | `BR_bb` |
| `BR_WW` | `BR_WW` |
| `BR_ZZ` | `BR_ZZ` |
| `BR_gg` | `BR_gg` |
| `BR_tautau` | `BR_tautau` |

## Columns renamed or split

| v1 | v2 | Why |
|---|---|---|
| `m_scalar_GeV` (alias `mS_GeV`) | `m_H2_GeV` | v1 had one undifferentiated "the scalar's mass"; v2 names it specifically as the H2 mass, alongside the new `m_A_GeV`/`m_Hp_GeV`/`m_h_GeV`/`Delta_heavy_GeV` fields v1 had no room for at all. |
| `ctau_mm` (alias `ctau_mm_H2`) | `ctau_physical_mm` **and** `ctau_response_mm` | v1's single `ctau_mm` conflated the width-derived physical lifetime with a detector-response study's independently-scanned lifetime. v2 requires both, as two distinct columns, never aliases of each other (`docs/contracts/model_point_to_llp_recast_v2.md` design decision 2). **A v1 `ctau_mm` value should be treated as `ctau_physical_mm` when migrating a genuinely physical-lifetime sample, or as `ctau_response_mm` when migrating a forced-decay detector-response sample — never both automatically**, since a v1 row gives no way to tell which case it was. |

## New in v2 (no v1 equivalent at all)

`schema_version`, `model_variant`, `m_h_GeV`, `m_A_GeV`, `m_Hp_GeV`,
`Delta_heavy_GeV`, `g_hH2H2_GeV`, `BR_cc`, `BR_tt`, `BR_gammagamma`,
`BR_Zgamma`, `BR_hh`, `production_process`, `production_owner`,
`decay_owner`, `response_decay_channel`, `H2_to_AZ_open`, `H2_to_HpW_open`,
`H2_to_AA_open`, `H2_to_HpHm_open`, `theory_status`, `experimental_status`,
`sigma_source`, `sigma_provenance`, `producer_commit`, `config_hash`,
`input_hash`.

All of these are confirmed genuine gaps in
`docs/DOWNSTREAM_INTERFACE_GAP_REPORT.md`; see
`docs/contracts/model_point_to_llp_recast_v2.md` for the full field-by-field
design rationale.

## v1 columns with no v2 required-column equivalent

| v1 column | Status in v2 |
|---|---|
| `model` | Not a required v2 column. v2 identifies a point's provenance via `schema_version` + `producer_commit` + `model_variant` instead of a free-text model tag. A producer that still wants a `model`-style free-text label may add it as an extra column — `validate_csv()` only checks that `REQUIRED_COLUMNS` are *present*, it does not reject unrecognized extra columns, so this is safe to carry forward informally. |
| `BR_hadronic_proxy` | Not a required v2 column. v1's `BR_hadronic_proxy` was a legacy-recast-tooling convenience derived from the real BRs; v2's full 10-channel BR list makes deriving an equivalent proxy on the consumer side straightforward (sum whichever hadronic channels a given recast SR cares about), so v2 does not standardize one built-in proxy value. Add it as an extra passthrough column if a specific legacy consumer still needs it literally. |
| `beta_gamma_source` | Not a required v2 column. The mission's `v2` field list (and the gap report, which called this field "orthogonal ... no gap identified") did not ask for it. Same passthrough-column note applies if a consumer needs it. |
| `recast_channel_hint` | Not a required v2 column, same reasoning as `beta_gamma_source`. |
| `sigma_production_unc_fb` (documented in `docs/contracts/model_point_to_llp_recast_contract.md`'s prose but not actually in v1's machine-readable `required_columns`) | Not a required v2 column either. Neither contract's enforced schema currently requires it; add as an extra passthrough column if a consumer needs the MadGraph integration uncertainty specifically (recommended for any row with `sigma_source == DIRECT_MADGRAPH_POINT`, but not validator-enforced in this contract version). |

**Known limitation, flagged for the orchestrating session:** the four rows
above are all fields the gap report explicitly said "should carry forward
unchanged unless `dihiggs_llp_recast` requests otherwise." This
implementation took the mission's literal minimum required-column list
(38 columns) rather than also carrying these four forward as required
columns. Because `validate_csv()` does not reject extra columns, a producer
can still emit them and any legacy consumer that reads them directly (not
through `REQUIRED_COLUMNS`) is unaffected — but they are not validated or
guaranteed present by the v2 contract itself. If a real `dihiggs_llp_recast`
consumer needs one of these as a *guaranteed* v2 column, that is a small,
additive change to `REQUIRED_COLUMNS` in `data_contract_v2.py`, not a
redesign.

## Invariant changes

| Invariant | v1 | v2 |
|---|---|---|
| ctau consistency | `ctau_mm == hbar_c/total_width_GeV`, `rel_tol=1e-4` | `ctau_physical_mm == hbar_c/total_width_GeV`, `rel_tol=1e-6`, for every row regardless of variant; `ctau_response_mm` is separately required to equal `ctau_physical_mm` exactly (`rel_tol=1e-9`) but **only** for `PHYSICAL_DECAYS_NO_HEAVY_CASCADES` rows |
| BR sum | `sum(BR_bb, BR_WW, BR_ZZ, BR_gg, BR_tautau) <= 1`, `abs_tol=1e-6` (5 of 10 channels) | `sum(BR_bb, BR_cc, BR_tt, BR_tautau, BR_WW, BR_ZZ, BR_gg, BR_gammagamma, BR_Zgamma, BR_hh) <= 1`, `abs_tol=1e-6` (all 10 channels) |
| `beta_gamma_source` enum | checked (`assumed_flat`, `mg5_pythia_truth`, `analytic_kinematics`) | not checked (column not required in v2 at all, see above) |
| Mass hierarchy | none (v1 has no heavy-state fields to check) | `m_h_GeV < m_H2_GeV < m_A_GeV == m_Hp_GeV`, `Delta_heavy_GeV == m_A_GeV - m_H2_GeV` |
| Cascade flags | none | all four forbidden flags must be false for `PHYSICAL_DECAYS_NO_HEAVY_CASCADES` rows |
| `model_variant`, `sigma_source`, `production_process`, `production_owner`, `decay_owner`, `theory_status`, `experimental_status` enums | none (fields don't exist in v1) | all checked enums |
