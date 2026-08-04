# First physical H2 production artifacts

This directory records the first model-derived `H2scan_mH150_tb300000` production smoke chain.

- MadGraph: two independent 1000-event LO runs at 13 TeV; H2 is stable in the LHE.
- Pythia 8.308: pre-hadronization smoke with forced `9000006 -> b bbar`.
- Full Pythia 8.308 sample: both canonical 1000-event LHE inputs, hadronization enabled, 2000 events total.
- Forced decays change sampling only; physical normalization remains `sigma_H2H2 * br_bb^2`.
- No detector recast or acceptance is claimed.
