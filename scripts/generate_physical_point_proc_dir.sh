#!/usr/bin/env bash
# Regenerate the MadGraph process directory used by run_physical_point_madgraph.py
# (process: g g > H > h2 h2) from the canonical UFO model, without requiring any
# pre-existing generated output to be copied from another machine.
#
# Resolution order (same convention as scripts/portable_paths.py):
#   DIHIGGS_ROOT                       workspace root containing main_dihiggs/ufos/hep_cross/...
#   MG5_HOME                           MadGraph5_aMC@NLO install directory
#   DIHIGGS_MG5_PROC_DIR                target process directory (defaults under hep_cross/results)
#   DIHIGGS_PHYSICAL_POINT_UFO_DIR     explicit override for the UFO model directory
#
# Usage: scripts/generate_physical_point_proc_dir.sh [--force]
#
# UFO source, in priority order:
#   1. $DIHIGGS_PHYSICAL_POINT_UFO_DIR, if set.
#   2. hep_cross/results/r14_direct_g_production/ufo/.../LLscalar_v3_UFO_runtime
#      -- the exact UFO revision validated for this milestone (frozen benchmark
#      closure sigma_production_fb ~= 0.230291 fb). It is a small
#      (~388K) CANONICAL_SMALL_ARTIFACT transferred via the migration
#      bundle (migration/ARTIFACT_MANIFEST.json), not reproducible from
#      the ufos repo alone -- see caveat below.
#   3. ufos/CURRENT_PACK_A (the ufos repo's frozen release zip), as a
#      last-resort fallback ONLY.
#
# KNOWN CAVEAT: as of this writing, ufos/CURRENT_PACK_A
# (pi_ufo_baseline_v1_frozen_hotfix1.zip) does NOT expose GHphiphi as an
# external FRBlock parameter (verified: its parameters.py has no GHphiphi
# entry, only ctauh2). The UFO actually used to validate this milestone
# does expose it (nature='external', lhablock='FRBlock', lhacode=[3]).
# Falling back to option 3 will generate a process directory that silently
# ignores the requested g_hH2H2 coupling and will NOT reproduce the frozen
# benchmark cross section. This is a discrepancy in the ufos repo's
# current release, not something this script can fix -- prefer option 2.

set -euo pipefail

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -n "${DIHIGGS_ROOT:-}" ]]; then
  WORKSPACE_ROOT="$DIHIGGS_ROOT"
else
  WORKSPACE_ROOT="$REPO_ROOT"
  for _ in 1 2 3 4 5 6; do
    hits=0
    for marker in main_dihiggs ufos hep_cross llp_recast boundary; do
      [[ -d "$WORKSPACE_ROOT/$marker" ]] && hits=$((hits + 1))
    done
    if [[ $hits -ge 2 ]]; then
      break
    fi
    parent="$(dirname "$WORKSPACE_ROOT")"
    [[ "$parent" == "$WORKSPACE_ROOT" ]] && break
    WORKSPACE_ROOT="$parent"
  done
fi

if [[ -n "${MG5_HOME:-}" ]]; then
  MG5_DIR="$MG5_HOME"
else
  MG5_DIR="$(find "$HOME/.local/mg5amcnlo" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -1)"
fi

if [[ -z "$MG5_DIR" || ! -x "$MG5_DIR/bin/mg5_aMC" ]]; then
  echo "ERROR: could not locate mg5_aMC. Set MG5_HOME to the MadGraph5_aMC@NLO install directory." >&2
  exit 1
fi

PROC_DIR="${DIHIGGS_MG5_PROC_DIR:-$WORKSPACE_ROOT/hep_cross/results/r14_direct_g_production/proc_output}"

if [[ -d "$PROC_DIR" && $FORCE -eq 0 ]]; then
  echo "[SKIP] Process directory already exists: $PROC_DIR (use --force to regenerate)"
  exit 0
fi

VALIDATED_UFO_DIR="$WORKSPACE_ROOT/hep_cross/results/r14_direct_g_production/ufo/pi_ufo_baseline_v1_release_candidate_hotfix1/model/LLscalar_v3_UFO_runtime"
UFO_MODEL_DIR=""
CLEANUP_DIR=""

if [[ -n "${DIHIGGS_PHYSICAL_POINT_UFO_DIR:-}" ]]; then
  UFO_MODEL_DIR="$DIHIGGS_PHYSICAL_POINT_UFO_DIR"
  echo "[GENERATE] Using explicit UFO override: $UFO_MODEL_DIR"
elif [[ -d "$VALIDATED_UFO_DIR" ]]; then
  UFO_MODEL_DIR="$VALIDATED_UFO_DIR"
  echo "[GENERATE] Using validated UFO (frozen benchmark-tested revision): $UFO_MODEL_DIR"
else
  CANONICAL_UFO_ZIP="$WORKSPACE_ROOT/ufos/CURRENT_PACK_A"
  if [[ ! -e "$CANONICAL_UFO_ZIP" ]]; then
    echo "ERROR: no UFO source found. Checked:" >&2
    echo "  - \$DIHIGGS_PHYSICAL_POINT_UFO_DIR (unset)" >&2
    echo "  - $VALIDATED_UFO_DIR (missing -- see migration/ARTIFACT_MANIFEST.json)" >&2
    echo "  - $CANONICAL_UFO_ZIP (missing)" >&2
    exit 1
  fi
  echo "[GENERATE] WARNING: validated UFO not found at $VALIDATED_UFO_DIR." >&2
  echo "[GENERATE] WARNING: falling back to ufos/CURRENT_PACK_A, which is KNOWN to be" >&2
  echo "[GENERATE] WARNING: missing the external GHphiphi FRBlock parameter. The" >&2
  echo "[GENERATE] WARNING: resulting process will NOT reproduce the frozen benchmark" >&2
  echo "[GENERATE] WARNING: closure (sigma_production_fb ~= 0.230291 fb). Extract the" >&2
  echo "[GENERATE] WARNING: validated UFO from the migration bundle instead." >&2
  CLEANUP_DIR="$(mktemp -d)"
  unzip -q "$CANONICAL_UFO_ZIP" -d "$CLEANUP_DIR"
  UFO_MODEL_DIR="$(find "$CLEANUP_DIR" -maxdepth 3 -type d -name "LLscalar_v3_UFO_runtime" | head -1)"
  if [[ -z "$UFO_MODEL_DIR" ]]; then
    echo "ERROR: LLscalar_v3_UFO_runtime model not found inside $CANONICAL_UFO_ZIP" >&2
    exit 1
  fi
fi
trap '[[ -n "$CLEANUP_DIR" ]] && rm -rf "$CLEANUP_DIR"' EXIT

if [[ -d "$PROC_DIR" && $FORCE -eq 1 ]]; then
  rm -rf "$PROC_DIR"
fi
mkdir -p "$(dirname "$PROC_DIR")"

PROC_CARD="$(mktemp)"
trap '[[ -n "$CLEANUP_DIR" ]] && rm -rf "$CLEANUP_DIR"; rm -f "$PROC_CARD"' EXIT
cat > "$PROC_CARD" <<EOF
import model $UFO_MODEL_DIR
generate g g > H > h2 h2
output $PROC_DIR -f
EOF

echo "[GENERATE] Running mg5_aMC to build process directory at $PROC_DIR"
"$MG5_DIR/bin/mg5_aMC" "$PROC_CARD"
echo "[GENERATE] Done. Process directory ready at $PROC_DIR"
