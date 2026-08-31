# Current Data Authority

This is the single file a human or an LLM agent should read before treating
any DiHiggs (2HDM Type-I) number as current. It exists because, as of
2026-08-31, this workspace was reset from a dirty, multi-campaign state where
several plausible-looking result sets coexisted with no single answer to
"which one is real right now." Read this alongside
[`state/CURRENT_CAMPAIGN.yaml`](../state/CURRENT_CAMPAIGN.yaml) (the
machine-readable form of the same contract) before citing a cross section,
benchmark point, or recast result as authoritative.

## 1. What is CURRENT

**CURRENT MadGraph results: NONE.** As of this reset, no MadGraph production
campaign has completed and been validated under the fresh physical_2HDM vs
PI_simplified coupling-comparison plan. `state/CURRENT_CAMPAIGN.yaml`'s
`madgraph.authoritative_results` is `null` and must stay `null` until a real
campaign finishes and is validated — do not set it just because a plausible
number exists somewhere in this workspace or its archive.

**CURRENT non-MadGraph artifacts** (usable for current physics claims):

- The active 2HDM point evaluators in `dihiggs` (`DihiggsPointV2Evaluator`,
  `Lambda1EvaluatorV2`) and `dihiggs_boundary`'s handoff layer, at their
  respective `main` branch HEADs.
- The active mass convention: **m_h = 125.20 GeV**, established by
  `dihiggs_hep_cross` commit `53fb57e` ("Unify active mh convention to
  125.20 GeV"), `dihiggs_ufo` commit `7dd02c1`, and
  `dihiggs/conventions/physics_conventions.yaml`. Any benchmark point or
  result computed under a different m_h (125.13 GeV appears throughout the
  pre-reset history) is a **historical convention**, not an error, but must
  never be silently mixed with 125.20 GeV results in one table or plot.
- The 208-point recalculation at
  `dihiggs/docs/campaigns/high_mass_h2_physical_point_scan_v2_mh12520/`
  (commit `ef241b6`): point-*validity* data under the 125.20 GeV convention.
  This is theory acceptance/kinematics, **not a cross section** — it does not
  make any repo an authoritative source for current MadGraph numbers.
- `dihiggs_hep_cross/scripts/run_physical_point_madgraph.py`, the tracked
  per-point MadGraph production driver, and
  `scripts/madgraph_banner_verification.py`, the banner-authoritative
  verification module (see §6). Both are current *tooling*, not results.

## 2. What is HISTORICAL

Everything under `/home/fabian/atlas_dihiggs_archive/20260831_pre_madgraph_reset/`
is historical: `mission_runs/` (8 dated campaigns, Aug 12–28), `runs/` (8 more),
`search_runs/`, `_handoff_out/`, `presentations/`, `figures/`,
`meeting_signal_table/`, `operator/`, the embedded MadGraph_aMC v3.5.3 install,
and full git mirrors of all 6 repos (including branches never merged to main).
See `ARCHIVE_MANIFEST.tsv` and `DO_NOT_USE_FOR_CURRENT_PHYSICS.md` at the
archive root. Also historical: the archived campaign
`dihiggs_hep_cross-h2-llp-production/campaigns/h2_llp_production_300_330_345/`
(6/6 complete MadGraph runs for mH2=300/330/345 GeV) — a genuinely complete,
checksummed, well-documented result, dated pre-reset, and explicitly **not**
promoted to current per §5.

## 3. Supersession chain

```
2026-08-12  high_mass_e2e pilot                        (historical)
2026-08-21  boundary_benchmark_discovery               (historical)
2026-08-22  senior_review_meeting                       (historical)
2026-08-23  senior_review_validation                    (historical)
2026-08-25  h2_event_yields_v1                          (historical)
2026-08-26  h2_table_v2_requalification                 (historical)
2026-08-26  christopher_requalification                 (historical)
2026-08-27  benchmark_closure, coordinate_explainer,
            photon_rich_family_package                  (historical)
2026-08-28  x_path_dependence_scan                       (historical)
2026-08-31  THIS RESET -- workspace made unambiguous,
            no campaign promoted to current
------------------------------------------------------------------
[pending]   fresh physical_2HDM vs PI_simplified
            coupling-comparison campaign                (will become
                                                          CURRENT once
                                                          complete AND
                                                          validated)
```

None of the pre-reset campaigns supersede each other in a strict technical
sense (most cover different mass points or different questions); what they
share is that **none is current**. Do not infer "most recent timestamp wins."

## 4. Directories agents may use for current numerical claims

- `dihiggs/`, `dihiggs_boundary/`, `dihiggs_hep_cross/`, `dihiggs_llp_recast/`,
  `dihiggs_ufo/` at their tracked `main`-branch HEADs, for **methodology,
  evaluators, contracts, and tooling** — not for pre-existing numerical
  results found in `results/`, `artifacts/`, or `docs/pilots/*/` subtrees
  unless this file or `state/CURRENT_CAMPAIGN.yaml` names that specific
  artifact as current (as §1 does for the v2 point-validity recalculation).
- `dihiggs_ufo/` model directories, as the authoritative UFO for MadGraph
  generation. Never overwrite the original PI UFO; new prescriptions are
  added, not substituted in place.

## 5. Directories forbidden as current evidence

- Anything under `/home/fabian/atlas_dihiggs_archive/`.
- Anything under the retired old container
  `/home/fabian/atlas_dihiggs/` (superseded by this clean container;
  retained only inside the archive's git mirrors and the archived loose
  trees, never as a live path).
- Any `mission_runs/`, `runs/`, or `search_runs/` directory anywhere,
  including ones that may reappear inside a repo's untracked working tree —
  treat any such directory found in an active checkout as scratch output to
  be archived, not read as data.
- Campaign or worktree material still living in a git worktree without
  having gone through this authority contract (e.g. a fresh worktree someone
  creates for exploratory work) — worktree output is not current just
  because it is newer than the archive.

## 6. How a MadGraph result becomes authoritative

In this order, all four required:

1. **The banner is authoritative over any copied summary value.** Run
   `scripts/madgraph_banner_verification.py`'s `banner_checks()` /
   `checks_pass()` against the point that was supposedly generated. A sigma
   copied into a CSV without its banner passing this check is not usable.
2. **GHphiphi consistency.** The banner's `GHphiphi` value must equal
   `-abs(g_hH2H2_GeV)` for the point's declared coupling prescription (see
   §7) — this is exactly what `banner_checks()` verifies; a mismatch means
   the run used the wrong coupling, not just the wrong number.
3. **Seed agreement.** At least two independent seeds must agree within
   3-sigma (`madgraph_banner_verification.compatible()`); silent
   disagreement between seeds must block promotion, not average away.
4. **Manifest + validation.** The result is recorded in a campaign manifest
   naming `mH2`, `GHphiphi`, the coupling prescription, process, `sqrt(s)`,
   UFO identity, seed, and the banner/source artifact path (the same 8 fields
   `AGENTS.md` requires) — and a human (not an agent alone) has reviewed and
   accepted it — before `state/CURRENT_CAMPAIGN.yaml` is updated to point at
   it as `authoritative_results`.

## 7. physical_2HDM vs PI_simplified

Two distinct coupling prescriptions for the `g g > H > h2 h2` production
vertex, both declared in `state/CURRENT_CAMPAIGN.yaml`:

- **`physical_2HDM`**: `GHphiphi` derived from the validated 2HDM benchmark
  point via the real evaluator chain (`DihiggsPointV2Evaluator` /
  `Lambda1EvaluatorV2` → `dihiggs_boundary` handoff →
  `run_physical_point_madgraph.py`'s `generate_param_card_text`, which writes
  `GHphiphi = -abs(g_hH2H2_GeV)`). This is the prescription every archived
  and current-tooling MadGraph run in this workspace has used so far.
- **`PI_simplified`**: a simplified production prescription,
  `GHphiphi = -8 * mH2^2 / v`. **As of this reset, this formula has no
  implementation anywhere in this workspace** (checked: not present in any
  of the 6 repos' source). It is a deliverable of the upcoming campaign, not
  an existing asset — do not assume it already exists or silently substitute
  the `physical_2HDM` value when asked for a `PI_simplified` result.

Every cross section produced going forward must record which of the two
prescriptions it used; a number without that label is incomplete metadata
regardless of how it was obtained.
