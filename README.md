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
