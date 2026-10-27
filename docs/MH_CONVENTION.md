# SM-like Higgs mass convention

The project-wide theory authority is owned by `dihiggs` at the source commit recorded in `conventions/physics_conventions.lock.yaml`. Its controlled cache is `conventions/physics_conventions.yaml`; validate the cache and sidecar with the workspace checker. The active new-production value is the exact decimal string `125.20` GeV under `mh_125p20_active_2026`. This is an adopted project convention, not an external-measurement attribution.

New points must carry `physics_conventions_schema`, `physics_conventions_commit`, and `physics_conventions_sha256`, plus their mass and prescription metadata. The MadGraph driver rejects incomplete or mismatched v3 provenance. It uses the signed `g_physical_hphiphi_GeV` mapping from v3 for `physical_2HDM`; magnitude-only coupling is accepted only with an explicit historical convention ID and `historical_replay: true`.

The 125.13, 125.09, and 125.0 fixtures, campaigns, and frozen scripts retain their original bytes and convention IDs for replay. They are not new-production defaults. In particular, locked R9 inputs and historical MadGraph banners must not be regenerated or relabeled during this migration.
