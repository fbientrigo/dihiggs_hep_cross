# AGENTS.md — dihiggs_hep_cross

This repo owns MadGraph production and is the workspace's data-authority
registry. It carries the two files every agent must consult before citing a
number: `docs/CURRENT_DATA_AUTHORITY.md` and `state/CURRENT_CAMPAIGN.yaml`.

## Data authority (read this before citing any number)

Before using any numerical DiHiggs result:

1. Read `docs/CURRENT_DATA_AUTHORITY.md`.
2. Read `state/CURRENT_CAMPAIGN.yaml`.
3. Use only artifacts those two files explicitly mark current/authoritative.
4. Never use archived, superseded, legacy, search, exploratory, or
   presentation-only results for a current physics claim unless the user
   explicitly asks for historical comparison.

A MadGraph cross section is incomplete metadata unless it includes: mH2,
GHphiphi, coupling prescription, process, sqrt(s), UFO identity, seed, and a
banner/source artifact.

## Before running a MadGraph point

Use `scripts/run_physical_point_madgraph.py` (the tracked driver) and verify
the resulting banner with `scripts/madgraph_banner_verification.py`'s
`banner_checks()` / `checks_pass()` before trusting its sigma. Do not copy a
sigma from a results.html or a summary CSV without this check passing.

## Contracts

See `docs/contracts/` for the normalized interfaces this repo exposes to
downstream repos (`madgraph_xsec_output_contract.md`,
`model_point_to_llp_recast_contract.md`, etc.) before changing an output
format those contracts describe.
