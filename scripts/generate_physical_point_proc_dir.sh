#!/usr/bin/env bash
# Regenerate the MadGraph process directory used by run_physical_point_madgraph.py
# (process: g g > H > h2 h2) from the canonical UFO model, without requiring any
# pre-existing generated output to be copied from another machine.
#
# Resolution order (same convention as scripts/portable_paths.py):
#   DIHIGGS_ROOT             workspace root containing main_dihiggs/ufos/hep_cross/...
#   MG5_HOME                 MadGraph5_aMC@NLO install directory
#   DIHIGGS_MG5_PROC_DIR     target process directory (defaults under hep_cross/results)
#
# Usage: scripts/generate_physical_point_proc_dir.sh [--force]

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

CANONICAL_UFO_ZIP="$WORKSPACE_ROOT/ufos/CURRENT_PACK_A"
if [[ ! -e "$CANONICAL_UFO_ZIP" ]]; then
  echo "ERROR: canonical UFO not found at $CANONICAL_UFO_ZIP (expected ufos repo checkout)." >&2
  exit 1
fi

UFO_EXTRACT_DIR="$(mktemp -d)"
trap 'rm -rf "$UFO_EXTRACT_DIR"' EXIT
unzip -q "$CANONICAL_UFO_ZIP" -d "$UFO_EXTRACT_DIR"
UFO_MODEL_DIR="$(find "$UFO_EXTRACT_DIR" -maxdepth 3 -type d -name "LLscalar_v3_UFO_runtime" | head -1)"
if [[ -z "$UFO_MODEL_DIR" ]]; then
  echo "ERROR: LLscalar_v3_UFO_runtime model not found inside $CANONICAL_UFO_ZIP" >&2
  exit 1
fi

if [[ -d "$PROC_DIR" && $FORCE -eq 1 ]]; then
  rm -rf "$PROC_DIR"
fi
mkdir -p "$(dirname "$PROC_DIR")"

PROC_CARD="$(mktemp)"
trap 'rm -rf "$UFO_EXTRACT_DIR" "$PROC_CARD"' EXIT
cat > "$PROC_CARD" <<EOF
import model $UFO_MODEL_DIR
generate g g > H > h2 h2
output $PROC_DIR -f
EOF

echo "[GENERATE] Running mg5_aMC to build process directory at $PROC_DIR"
"$MG5_DIR/bin/mg5_aMC" "$PROC_CARD"
echo "[GENERATE] Done. Process directory ready at $PROC_DIR"
