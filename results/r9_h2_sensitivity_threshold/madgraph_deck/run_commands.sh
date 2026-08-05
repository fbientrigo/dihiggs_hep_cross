#!/usr/bin/env bash
# R9 coupling-scaling runs. Requires MG5_aMC (canonical production used 3.5.3)
# and the Pack B UFO unpacked next to this script.
#
# These runs could NOT be executed in the session that produced this deck:
# every MadGraph distribution host is denied by the environment's egress
# policy. See madgraph_scaling_fit.json -> blocked_sources.
set -euo pipefail
MG5=${MG5:-mg5_aMC}
"$MG5" proc_card.dat
for k in 0p5 1p0 2p0 4p0; do
  cp "param_card_kappa_${k}.dat" r9_h2_scaling/Cards/param_card.dat
  cat run_card_fragment.dat >> r9_h2_scaling/Cards/run_card.dat
  (cd r9_h2_scaling && ./bin/generate_events -f "kappa_${k}")
done
# Then: python3 ../../../scripts/r9_ingest_madgraph_scaling.py --help
