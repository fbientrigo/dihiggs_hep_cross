# Reproduce this campaign

All commands are run from this directory. Total runtime is a few seconds after
the one-time build.

## 0. Build the canonical calculators (once)

Nothing under `~/atlas_dihiggs/dihiggs` is modified; all three binaries land on
gitignored paths.

```bash
cd ~/atlas_dihiggs/dihiggs/2hdmc   && make lib -j"$(nproc)" && make CalcGen CalcLH
cd ~/atlas_dihiggs/dihiggs/dihiggs && make directories && make app/Lambda1EvaluatorV2
```

Requires GSL (2.8 used here) and a C++17 compiler (g++ 14.2 used here).

## 1. Extract the targets deterministically

```bash
python3 scripts/extract_targets.py          # -> work/targets.csv
```
Asserts internally that ħc/Γ reproduces each recorded cτ and that the four quoted
BRs match `photonic_all_decay_channels_CalcLH.csv`.

## 2. Exact replay of Christopher's points (bit-exact check)

```bash
~/atlas_dihiggs/dihiggs/2hdmc/CalcGen \
  1.000000000000000000e+00 2.577337926164229298e-01 1.907230065364474703e+00 \
  -8.247481363784422426e-01 -8.247481363784425756e-01 1.177689207010650991e-04 \
  0.000000000000000000e+00 9.999999999933048556e-04 4.000000000000000745e+07 1 \
  /tmp/m200.lha
~/atlas_dihiggs/dihiggs/2hdmc/CalcLH /tmp/m200.lha /tmp/m200_out.lha
```
`CalcLH` must print `Total width: 2.715e-16`, `H -> ga ga ... 6.645e-01`,
`H -> Z ga ... 3.216e-01`, `m_H: 205.42774`, and unitarity/perturbativity/stability
all `1`. Note `CalcGen`'s own stdout reports `m_H: 198.21749` — the discrepancy is
the defect this campaign corrects.

## 3. Reproduce the tan(beta) conditioning diagnosis

```bash
python3 scripts/diagnose_tanb_conditioning.py   # -> logs/tanb_conditioning_diagnosis.txt
```

## 4. Rebuild every deliverable

```bash
python3 scripts/build_deliverables.py   # validated/, event_yields/, inputs/production_reference/
python3 scripts/make_plots.py           # plots/
```

`build_deliverables.py` invokes `Lambda1EvaluatorV2` itself; the raw evaluator
input/output and its stderr warnings are kept under
`work/calculator_runs/selected/`.

## 5. Supporting evidence already on disk

| path | what it shows |
|---|---|
| `work/calculator_runs/replay_gen/` | bit-exact replay of all three original points |
| `work/calculator_runs/truncation_diag/` | in-memory vs post-LesHouches spectrum |
| `work/calculator_runs/lam1_grid/` | λ1 ∈ [0.25, 4] × m_h ∈ {125.0, 125.20} inertness scan |
| `work/calculator_runs/pointv2/` | the rejected (mH, M²) route, incl. λ1 = −7066 |
| `work/calculator_runs/replay_lam1/` | λ1-route replay at the design coordinates |
| `work/calculator_runs/roundtrip/` | reconstructed λ's fed back through `set_param_gen` |
