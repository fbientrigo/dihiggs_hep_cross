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
# Production UFO: the dihiggs_ufo release validated by the 0.230291 fb closure (DATA_FLOW N5).
export DIHIGGS_PHYSICAL_POINT_UFO_DIR="$DIHIGGS_ROOT/dihiggs_ufo/releases/r14_runtime/LLscalar_v3_UFO_runtime"
export PATH="$MG5_HOME/bin:$PATH"

# The MadGraph process dir (results/r14_direct_g_production/proc_output) is
# generated, not tracked: build it with
# dihiggs_hep_cross/scripts/generate_physical_point_proc_dir.sh before the
# first run.

if [[ -f "$DIHIGGS_ROOT/.venv/bin/activate" ]]; then
    source "$DIHIGGS_ROOT/.venv/bin/activate"
fi
