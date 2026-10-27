# Current data authority

This file governs which numerical results may be described as current. It is separate from the project-wide theory convention, whose owner is `dihiggs`; this repository keeps a controlled v3 cache at `conventions/physics_conventions.yaml` with provenance in `conventions/physics_conventions.lock.yaml`.

## Current results

**Authoritative MadGraph results: none.** `state/CURRENT_CAMPAIGN.yaml` must keep `madgraph.authoritative_results: null` until a campaign has completed and passed banner verification, coupling consistency, independent-seed agreement, manifest review, and explicit human acceptance. Setup or a successful run does not promote results.

The separately authorized, non-MadGraph high-mass validity artifact is `dihiggs/docs/campaigns/high_mass_h2_physical_point_scan_v2_mh12520/` from `dihiggs@ef241b6fae92aa0324ef736a613c19bf52bab03e`. Its authorization is limited to the 208 recalculated points' theoretical-validity and kinematic flags; it contains no production cross sections and authorizes neither new points nor new runs. It remains distinct from the MadGraph results registry above.

That exact directory is absent from the currently pinned `dihiggs@087ba246e9a9fa34b16249b52629a62703893b5c` checkout. Recover it from the recorded `ef241b6fae92aa0324ef736a613c19bf52bab03e` commit and verify its `checksums.sha256` before relying on the artifact. Pinned v3 tools are current tooling; their presence does not promote any output.

The current theory convention for new production is the v3 authority identified by the cache sidecar: `m_h = "125.20"` GeV under `mh_125p20_active_2026`. It is a project convention, not a claim that the value is the PDG central value. New handoffs must carry the v3 schema, source commit, source SHA-256, explicit campaign choices, and coupling prescription.

## Historical and replay data

Artifacts generated with 125.13, 125.09, or 125.0 retain their original values and hashes. They are historical/replay inputs and cannot be relabeled as v3 production. The checked-in R9 mass-jet control and seed/threshold fixtures remain frozen; this migration does not regenerate them. Archived campaigns remain historical regardless of their completeness or timestamp.

The root workspace's pinned `dihiggs` commit is the current convention source. Its separate result registry remains empty. Verify both this document and `state/CURRENT_CAMPAIGN.yaml` before making a numerical claim; never infer authority from a local file, branch, or timestamp.

## Requirements for future MadGraph promotion

Before a result can be promoted, all of the following must be recorded and checked:

1. Banner agrees with the declared process, energy, masses, widths, and UFO parameter card.
2. `GHphiphi` follows the declared prescription. For v3 `physical_2HDM`, the canonical signed mapping is `GHphiphi = -g_physical_hphiphi_GeV`; magnitude-only replay is marked historical.
3. For two independent seeds, `compatible()` requires `abs(sigma_a - sigma_b) <= 3 * hypot(unc_a, unc_b)` (3σ agreement).
4. A manifest records `mH2`, `GHphiphi`, prescription, process, collision energy, UFO identity, seed, banner/source artifact, and convention provenance; a human reviews and accepts it before `authoritative_results` changes.

The effective prescriptions `effective_mass_only` and `effective_m22_shifted` have unresolved UFO sign mappings in the authority. This repository does not treat them as implemented for sign-sensitive production.
