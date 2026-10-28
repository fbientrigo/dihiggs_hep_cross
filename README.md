# MadGraph production and data authority

This repository owns the tracked MadGraph production drivers, output
contracts, ingestion tooling, and current-campaign data-authority registry.
It does not own the global workspace setup or the theory conventions.

In a workspace checkout, begin with the [global onboarding guide](../docs/ONBOARDING.md)
and [workspace map](../docs/WORKSPACE_MAP.md). Before using a numerical
result, read [`docs/CURRENT_DATA_AUTHORITY.md`](docs/CURRENT_DATA_AUTHORITY.md)
and [`state/CURRENT_CAMPAIGN.yaml`](state/CURRENT_CAMPAIGN.yaml).

For production, follow this repository's [instructions](AGENTS.md) and use
the tracked `scripts/run_physical_point_madgraph.py` driver. Verify the
produced banner with `scripts/madgraph_banner_verification.py` before trusting
its cross section. Do not treat a successful run as promotion to current
authority; follow the explicit review and registry update procedure in the
authority document.

## Restoring data

Bulk data under `campaigns/`, `results/` and `artifacts/` (csv, json, dat, txt, log, lha, png, pdf, ...) is not in git; it lives in the lake and, at the pre-N3 commit, in this repo's history. Code, `.md`, `.cmnd` cards and `campaigns/physical_vs_effective_coupling_v1/2hdmc_build` stay tracked. Restore a tree with `python lake/lake.py restore <cid> <dir>` from the workspace root:

| Tree | Lake commit |
|---|---|
| `campaigns/20260901_photonic_requalification` | `20261013T000618Z-f72af7` |
| `campaigns/20261007_positive_g_envelope` | `20261013T000851Z-418de4` (+ `20261028T023944Z-7966a0`) |
| `campaigns/physical_vs_effective_coupling_v1` | `20261013T001001Z-a347d8` |
| `results` | `20261013T001159Z-7e0782` |
| `artifacts` | `20261013T001159Z-9752fb` |

e.g. `python lake/lake.py restore 20261013T001159Z-7e0782 dihiggs_hep_cross/results`. Tests that read these files (`tests/test_r9_artifacts.py`, `tests/test_r10_effective_scan.py`, ...) need the restore first.
