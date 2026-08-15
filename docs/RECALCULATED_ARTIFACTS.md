# Recalculated-artifact register

The old tracked pilot/signal CSVs are not silently relabeled. They were
produced with the obsolete bare `ctau_mm` handoff and lack the required
sigma provenance and complete canonical BR/mass fields.

| Old artifact | Old SHA256 | Status | Canonical replacement |
|---|---|---|---|
| `results/archive/obsolete_schema/physical_point_madgraph_pilot.csv` | `2d9d837b9e1a9c9e0c12e2e6b34a42422879f2ce2847ded546a724e3ff098578` | Not regenerated in this migration | `run_physical_point_madgraph.py` now emits named lifetime fields and direct-MadGraph provenance |
| `results/archive/obsolete_schema/physical_llp_signal_pilot.csv` | `79983aeac2ba6f722d674f2987cd1416b6657f6100fd57089c9bd8ec7f524ac5` | Not regenerated in this migration | `compute_physical_llp_signal.py` now requires `ctau_response_mm`, `sigma_source`, and `sigma_provenance` |
| `results/archive/obsolete_schema/physical_llp_signal_points.csv` | `af0a93de7ce06c04df8bce462f783182a042255f28bb3c272bde9ffaac69e2c` | Not regenerated in this migration | Same canonical signal producer |

The former `results/pilot_points_input.json` is archived beside these outputs;
the active pilot now requires `results/canonical_model_points.json`.
Regeneration requires a working compiled MadGraph process directory. The
available local process fails before event production at link time with
`undefined reference to setpara_`; preserving those rows as if they had been
recomputed would be scientifically misleading. The old files therefore
remain identifiable historical artifacts until a point-specific MadGraph run
can produce complete canonical rows.

The Pack B benchmark was recomputed through the canonical builder's generic
path. Its deterministic overlay hash is recorded by
`pack_b/tests/test_model_derived.py` in the UFO repository.
