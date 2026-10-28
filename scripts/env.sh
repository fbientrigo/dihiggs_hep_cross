#!/usr/bin/env bash
# Source it: . dihiggs_hep_cross/scripts/env.sh
# Environment helper for DiHiggs production workspace (clean container,
# built 2026-08-31 -- see docs/CURRENT_DATA_AUTHORITY.md in dihiggs_hep_cross).
# Renamed from atlas_dihiggs_clean to atlas_dihiggs on 2026-09-24; this file
# derives its own location instead of hardcoding the workspace root, so
# renaming the workspace again does not require editing it.

DIHIGGS_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-${(%):-%x}}")/../.." && pwd -P)"  # scripts/ -> module -> workspace root
export DIHIGGS_ROOT
export MG5_HOME="/home/fabian/.local/mg5amcnlo/3.5.3"
export DIHIGGS_PHYSICAL_POINT_UFO_DIR="$DIHIGGS_ROOT/dihiggs_hep_cross/results/r14_direct_g_production/ufo/model/LLscalar_v3_UFO_runtime"
export PATH="$MG5_HOME/bin:$PATH"

# DIHIGGS_PHYSICAL_POINT_UFO_DIR does not exist yet in a fresh checkout --
# results/r14_direct_g_production/ is deliberately gitignored (generated
# MadGraph process output, not tracked source). Generate it with
# dihiggs_hep_cross/scripts/generate_physical_point_proc_dir.sh before the
# first run.

if [[ -f "$DIHIGGS_ROOT/.venv/bin/activate" ]]; then
    source "$DIHIGGS_ROOT/.venv/bin/activate"
fi
