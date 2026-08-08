# Regenerating the MadGraph process directory (portability)

Companion to [`PHYSICAL_POINT_MADGRAPH_WORKFLOW.md`](PHYSICAL_POINT_MADGRAPH_WORKFLOW.md),
which fixes the physics contract. This note covers the mechanical steps for
turning the canonical UFO into a runnable process directory on a machine
that does not already have one -- e.g. a fresh Debian 13 install.

## Chain

```text
canonical UFO (ufos repo, CURRENT_PACK_A)
    -> mg5_aMC process generation (proc_card: import model / generate / output)
    -> reusable generated process directory (proc_output/)
    -> point-specific param_card.dat (written per point by the runner)
    -> ./bin/generate_events
```

## The process directory is not required to pre-exist

`run_physical_point_madgraph.py` takes `--proc-dir` (default resolved via
`DIHIGGS_MG5_PROC_DIR` / `DIHIGGS_ROOT`, see `scripts/portable_paths.py`).
It does not generate the process itself -- it expects a compiled MadGraph
process directory to already be there, because process generation is a
one-time, order-of-a-minute step that should not be repeated per point or
per campaign run.

On a machine that has never generated it, run:

```bash
scripts/generate_physical_point_proc_dir.sh
```

This resolves the same `DIHIGGS_ROOT`/`MG5_HOME` conventions as the Python
runner, writes a temporary `proc_card.dat` for `generate g g > H > h2 h2`,
and invokes `$MG5_HOME/bin/mg5_aMC` to build the process at the resolved
target path (same relative location as the source machine:
`hep_cross/results/r14_direct_g_production/proc_output`, unless
`DIHIGGS_MG5_PROC_DIR` overrides it). It is a no-op if the target already
exists; pass `--force` to rebuild.

### UFO source -- read this before trusting a regenerated benchmark

The script prefers, in order: `$DIHIGGS_PHYSICAL_POINT_UFO_DIR` (explicit
override) > the validated UFO frozen at
`hep_cross/results/r14_direct_g_production/ufo/pi_ufo_baseline_v1_release_candidate_hotfix1/model/LLscalar_v3_UFO_runtime`
(a small, untracked `CANONICAL_SMALL_ARTIFACT` -- see
`migration/ARTIFACT_MANIFEST.json` -- transferred via the migration
bundle, not reproducible from the `ufos` repo alone) > `ufos/CURRENT_PACK_A`
as a last resort.

**Verified during clean-room migration testing**: `ufos/CURRENT_PACK_A`
(`pi_ufo_baseline_v1_frozen_hotfix1.zip`) does *not* expose `GHphiphi` as
an external `FRBlock` parameter -- its `parameters.py` only defines
`ctauh2`. The UFO actually used to validate this milestone does
(`nature='external'`, `lhablock='FRBlock'`, `lhacode=[3]`,
`value=-63.5914252...`). A process directory built from `CURRENT_PACK_A`
silently ignores the requested `g_hH2H2_GeV` coupling (the regex in
`generate_param_card_text()` finds no `# GHphiphi` line to substitute) and
produces a wrong cross section -- confirmed by clean-room testing to be
off by roughly two orders of magnitude at the benchmark point. This is a
discrepancy in the `ufos` repo's current frozen release, not something
this script can fix; make sure the validated UFO artifact is present
(extract it from the migration bundle) before running `--benchmark` on a
new machine.

This is the "reconstruct the process directory rather than requiring the
old R14 folder" path: the directory name is kept for continuity with
existing run provenance (`results/*.csv` -> `provenance.proc_dir`), but
nothing about a fresh Debian install depends on that specific directory
having been copied from another machine -- it is rebuilt from source.

## What stays fixed

Regeneration does not change any physics: same UFO revision, same
`generate g g > H > h2 h2` process syntax, same MadGraph version pin
(`bootstrap/external_tools.lock.yaml`). Only the filesystem paths involved
in building it are now portable.

## Verification

`bootstrap/verify_workspace.sh --benchmark` regenerates the process
directory if missing (via this script) and then runs the frozen benchmark
point (`m_H2=150 GeV`, `g_hH2H2=63.59 GeV`), checking
`sigma_production_fb` against the expected 0.230291 fb within normal
MadGraph integration tolerance.
