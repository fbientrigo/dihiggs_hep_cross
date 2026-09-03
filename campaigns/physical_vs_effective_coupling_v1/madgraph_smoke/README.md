# Phase 6 — MadGraph smoke test: NOT PERFORMED (no local installation)

**Status: blocked at the environment level, not attempted further. No results
below are invented.**

## What was checked

```
$ which mg5_aMC          -> not found
$ find / -maxdepth 6 -iname "mg5_aMC" -type f   -> no matches
$ ls ~/MG5*, ~/madgraph*, ~/atlas_dihiggs/MG5*  -> no matches
$ pip3 list | grep -i madgraph                  -> no matches
```

There is a directory `2hdmc_build/MGME/2HDMC/` inside this campaign, but it
contains only the 2HDMC-to-MadGraph model-linking scaffold (the UFO model
directory tree), **not** an MG5_aMC executable or engine. It is not a
MadGraph installation.

This confirms the same finding already recorded in `ufo/validation.md` §4
from the earlier campaign pass: no `mg5_aMC` binary exists anywhere in this
environment.

## What this means for the mission's Phase 6 requirements

The mission instructs: *"If MadGraph is not available locally, document that
and STOP Phase 6 without inventing results."* That is what this file does.

None of the following were performed, and none of their outputs should be
assumed, estimated, or fabricated:

- `import model` / `generate g g > h2 h2` / `output` (UFO import smoke test)
- inspection of a generated `param_card.dat` to confirm `GHphiphi` resolves
  as an external FRBlock parameter
- the ± sign cross-section test (`+|g|` vs `-|g|`)
- the `sigma / |g|²` constancy check

`commands.txt` in this directory records the exact commands a future session
**with a real MG5_aMC install** should run to complete this phase — written
now, before any such session exists, so that phase can be executed
mechanically without re-deriving the setup.

## What is NOT blocked

The coupling values needed for that future smoke test are already fully
determined by this campaign (see `coupling_comparison/coupling_table.csv`
and `COUPLING_STUDY_REPORT.md`): the physical 2HDM coupling, `EF_simple`,
and `EF_m2` at m_φ = 200/250/300 GeV. Nothing about Phase 6 is waiting on
further physics work — only on an MG5_aMC installation being available.

## Recommendation

Do not install MadGraph as part of this mission (out of scope — this
mission's explicit stop condition is "STOP before a MadGraph production
campaign"). A future session with MG5_aMC available should run exactly the
commands in `commands.txt` and populate `smoke_results.csv`, then stop —
per the mission's own MADGRAPH STOP CONDITION, that smoke test is not
license to launch a full production campaign automatically.
