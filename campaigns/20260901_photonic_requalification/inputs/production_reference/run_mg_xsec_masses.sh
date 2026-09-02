#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# MadGraph LO xsec para pp(gg) -> h2 h2 a 13 TeV
#
# Requisitos dentro de esta carpeta:
#   - LLscalar_v3_UFO/  o  LLscalar_v3_UFO.zip
#   - MG5_aMC instalado, indicado con MG5_BIN o en PATH
#
# Ejemplo:
#   MG5_BIN=~/MG5_aMC_v3_5_3/bin/mg5_aMC ./run_mg_xsec_masses.sh
# ============================================================

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MG5_BIN="${MG5_BIN:-}"
if [[ -z "$MG5_BIN" ]]; then
    if command -v mg5_aMC >/dev/null 2>&1; then
        MG5_BIN="$(command -v mg5_aMC)"
    elif command -v mg5 >/dev/null 2>&1; then
        MG5_BIN="$(command -v mg5)"
    elif [[ -x "$ROOT/MG5_aMC_v3_5_3/bin/mg5_aMC" ]]; then
        MG5_BIN="$ROOT/MG5_aMC_v3_5_3/bin/mg5_aMC"
    elif [[ -x "$HOME/MG5_aMC_v3_5_3/bin/mg5_aMC" ]]; then
        MG5_BIN="$HOME/MG5_aMC_v3_5_3/bin/mg5_aMC"
    else
        echo "ERROR: no encontré mg5_aMC." >&2
        echo "Ejecuta, por ejemplo:" >&2
        echo "  MG5_BIN=~/MG5_aMC_v3_5_3/bin/mg5_aMC ./run_mg_xsec_masses.sh" >&2
        exit 1
    fi
fi

if [[ ! -x "$MG5_BIN" ]]; then
    echo "ERROR: MG5_BIN no es ejecutable: $MG5_BIN" >&2
    exit 1
fi

# Detectar raíz de MG5.
MG5_ROOT="$(cd "$(dirname "$MG5_BIN")/.." && pwd)"

UFO_NAME="${UFO_NAME:-LLscalar_v3_UFO}"
UFO_DIR="${UFO_DIR:-$ROOT/$UFO_NAME}"
UFO_ZIP="${UFO_ZIP:-$ROOT/${UFO_NAME}.zip}"

if [[ ! -d "$UFO_DIR" ]]; then
    if [[ -f "$UFO_ZIP" ]]; then
        echo "[UFO] Descomprimiendo $UFO_ZIP"
        unzip -q "$UFO_ZIP" -d "$ROOT"
    else
        echo "ERROR: no encontré $UFO_DIR ni $UFO_ZIP" >&2
        echo "Copia LLscalar_v3_UFO/ o LLscalar_v3_UFO.zip en esta carpeta." >&2
        exit 1
    fi
fi

if [[ ! -f "$UFO_DIR/particles.py" || ! -f "$UFO_DIR/parameters.py" ]]; then
    echo "ERROR: $UFO_DIR no parece ser un UFO válido." >&2
    exit 1
fi

# Para máxima compatibilidad, copiamos el UFO dentro de models/.
MODEL_NAME="${MODEL_NAME:-LLscalar_v3_UFO_local}"
MODEL_DEST="$MG5_ROOT/models/$MODEL_NAME"

echo "MG5_BIN   = $MG5_BIN"
echo "MG5_ROOT  = $MG5_ROOT"
echo "UFO_DIR   = $UFO_DIR"
echo "MODEL     = $MODEL_NAME"
echo

rm -rf "$MODEL_DEST"
cp -R "$UFO_DIR" "$MODEL_DEST"

MASSES="${MASSES:-200 250 300}"
SQRTS_GEV="${SQRTS_GEV:-13000}"
EBEAM="$(python3 - <<PY
print(float("$SQRTS_GEV")/2.0)
PY
)"
NEVENTS="${NEVENTS:-10000}"
ISEED_BASE="${ISEED_BASE:-12345}"

PROC_DIR="${PROC_DIR:-$ROOT/MG_h2h2_LO}"
MG_CMDS_DIR="${MG_CMDS_DIR:-$ROOT/mg5_cards}"
mkdir -p "$MG_CMDS_DIR"

# ------------------------------------------------------------
# Generar proceso
# ------------------------------------------------------------
GEN_CARD="$MG_CMDS_DIR/00_generate_h2h2.dat"
cat > "$GEN_CARD" <<EOF
set automatic_html_opening False
import model $MODEL_NAME
generate g g > h2 h2
output $PROC_DIR -f
EOF

echo "[MG5] Generando proceso g g > h2 h2"
"$MG5_BIN" "$GEN_CARD"

# ------------------------------------------------------------
# Función para editar param_card.dat por masa
# ------------------------------------------------------------
patch_param_card() {
    local mphi="$1"
    local card="$PROC_DIR/Cards/param_card.dat"

    python3 - "$card" "$mphi" "${CTAU_FOR_WIDTH:-1.0}" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
mphi = float(sys.argv[2])
ctau = float(sys.argv[3])
width = 1.9732698e-16 / ctau if ctau > 0 else 0.0

lines = path.read_text().splitlines()
out = []
block = None

for line in lines:
    stripped = line.strip()
    low = stripped.lower()

    if low.startswith("block "):
        parts = stripped.split()
        block = parts[1].upper() if len(parts) > 1 else None
        out.append(line)
        continue

    if stripped.upper().startswith("DECAY"):
        parts = stripped.split()
        if len(parts) >= 2 and parts[1] == "9000006":
            out.append(f"DECAY 9000006 {width:.8e} # Wh2 from ctauh2")
            continue
        out.append(line)
        continue

    if block == "MASS":
        # MASS 9000006 = Mh2
        if re.match(r"^\s*9000006\s+", line):
            out.append(f"  9000006 {mphi:.8e} # Mh2")
            continue

    if block == "FRBLOCK":
        # FRBlock 2 = ctauh2
        if re.match(r"^\s*2\s+", line):
            out.append(f"  2 {ctau:.8e} # ctauh2")
            continue

    out.append(line)

path.write_text("\n".join(out) + "\n")
PY
}

# ------------------------------------------------------------
# Lanzar cada masa
# ------------------------------------------------------------
for mphi in $MASSES; do
    run_name="mphi_${mphi}"
    seed=$((ISEED_BASE + ${mphi%.*}))

    echo
    echo "============================================================"
    echo "[MG5] m_phi = $mphi GeV"
    echo "============================================================"

    patch_param_card "$mphi"

    RUN_CARD="$MG_CMDS_DIR/run_${run_name}.dat"
    cat > "$RUN_CARD" <<EOF
set automatic_html_opening False
launch $PROC_DIR -n $run_name -f
set ebeam1 $EBEAM
set ebeam2 $EBEAM
set lpp1 1
set lpp2 1
set nevents $NEVENTS
set iseed $seed
EOF

    "$MG5_BIN" "$RUN_CARD"
done

# ------------------------------------------------------------
# Colectar xsec
# ------------------------------------------------------------
python3 "$ROOT/collect_mg_xsec.py" \
    --proc-dir "$PROC_DIR" \
    --masses $MASSES \
    --out "$ROOT/xsec_mg_h2h2.csv"

echo
echo "============================================================"
echo "Xsecs guardadas en:"
echo "  $ROOT/xsec_mg_h2h2.csv"
echo "============================================================"
