# Phase D — bounded Pythia/jet-level probe

**Status: `BLOCKED_PYTHIA`**

Per the mission's bound ("do not build Pythia from source, redesign environment,
change package architecture, spend hours on setup"), this was a probe of the
*existing* environment only, not an installation attempt.

## Checks performed (2026-08-10)

| check | result |
|---|---|
| `pythia8-config` on `$PATH` | not found |
| `~/.local/pythia8*`, `/usr/local/pythia8*`, `/opt/pythia8*` | none exist |
| MG5 HEPTools bundled Pythia (`~/.local/mg5amcnlo/3.5.3/HEPTools`) | none found |
| HepMC anywhere on host | none found |
| `python3 -c "import pythia8"` (project venv) | `ModuleNotFoundError` |
| Existing project Pythia driver | `dihiggs_hep_cross/artifacts/h2_first_physical/pythia_full/pythia_full_driver.cc` exists but its build gate (`tests/test_pythia_full_driver_gate.py`) requires `PYTHIA8_DIR` (default `~/.local/pythia8308`, confirmed absent) |

This reproduces the finding from the prior session (which additionally found
only a non-functional single-header Pythia stub inside an ephemeral pytest
tmp fixture — not a real install, and not reachable outside that fixture's
lifetime).

## Conclusion

No functional Pythia8/shower route is recoverable in this environment without
new infrastructure work (building Pythia8 from source), which is explicitly
out of scope for this mission. Phase D stops here.

**Consequence for Section 14 (recast gate):** jet-level / shower-level
observables (leading-jet pT, HT, HepMC-based Rxy/L3D) cannot be produced this
session. The recast-relevance question is answered using only the
parton-level LHE observables already available from the prior campaign
(H2 boost, pT(H2), ΔR(H2,H2) — see `presentation_update/tables/kinematic_summary.csv`),
which is the basis for the Phase C / PI_BRIEF conclusion below.
