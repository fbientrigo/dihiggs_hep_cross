#!/usr/bin/env bash
set -euo pipefail
MG5=/home/fabi/.local/mg5amcnlo/3.5.3/bin/mg5_aMC
PROC_DIR="../proc_output"
cp param_card.dat "$PROC_DIR/Cards/param_card.dat"
cp run_card.dat "$PROC_DIR/Cards/run_card.dat"
(cd "$PROC_DIR" && ./bin/generate_events -f run_g150)
