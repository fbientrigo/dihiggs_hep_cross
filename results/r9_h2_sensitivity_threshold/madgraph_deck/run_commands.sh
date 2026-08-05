#!/usr/bin/env bash
# R9 coupling-scaling runs. Requires the canonical MG5_aMC 3.5.3 environment
# and the Pack B UFO unpacked next to this script.
set -euo pipefail

MG5=${MG5:-mg5_aMC}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"

"$MG5" proc_card.dat

RUN_DIR="$HERE/r9_h2_scaling"
RUN_CARD="$RUN_DIR/Cards/run_card.dat"
BASE_CARD="$RUN_DIR/Cards/run_card.r9_base.dat"

# Replace every target setting exactly once. Do not append the fragment inside
# the run loop: that would duplicate keys in later runs.
python3 - "$RUN_CARD" "$HERE/run_card_fragment.dat" "$BASE_CARD" <<'PY'
from pathlib import Path
import re
import sys

run_card = Path(sys.argv[1])
fragment = Path(sys.argv[2])
output = Path(sys.argv[3])

fragment_lines = [
    line.rstrip("\n")
    for line in fragment.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]


def key_of(line: str):
    if "=" not in line:
        return None
    rhs = line.split("=", 1)[1].split("#", 1)[0].strip()
    return rhs.split()[0] if rhs else None


settings = {}
for line in fragment_lines:
    key = key_of(line)
    if not key:
        raise SystemExit(f"cannot parse fragment line: {line}")
    if key in settings:
        raise SystemExit(f"duplicate key in fragment: {key}")
    settings[key] = line

kept = []
for line in run_card.read_text(encoding="utf-8").splitlines():
    if key_of(line) not in settings:
        kept.append(line)

kept += ["", "# R9 canonical overrides (each key appears exactly once)"]
kept += [settings[key] for key in settings]
text = "\n".join(kept) + "\n"

for key in settings:
    pattern = re.compile(rf"^[^#\n]*=\s*{re.escape(key)}(?:\s|$)", re.M)
    if len(pattern.findall(text)) != 1:
        raise SystemExit(f"run-card key {key} does not occur exactly once")

output.write_text(text, encoding="utf-8")
PY

for k in 0p5 1p0 2p0 4p0; do
  cp "$BASE_CARD" "$RUN_CARD"
  cp "$HERE/param_card_kappa_${k}.dat" "$RUN_DIR/Cards/param_card.dat"
  (
    cd "$RUN_DIR"
    ./bin/generate_events -f "kappa_${k}"
  )
done

cat <<'EOF'
MadGraph runs complete.
Create a CSV with columns:
  kappa_g,sigma_pb,integration_error_pb,log
Then run:
  python3 ../../../scripts/r9_ingest_madgraph_scaling.py \
    --results measured_scaling.csv \
    --outdir ..
EOF
