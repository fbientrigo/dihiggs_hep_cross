# R11 Mission: Explicit MadGraph Production Mode Pilot Report

## 1. Executive Summary

This report documents the implementation and direct execution of the **MadGraph Production Mode Pilot** for the $gg \to H \to h_2 h_2$ process at $\sqrt{s} = 13$ TeV across three coupling points ($g = 40.0$, $63.59142520075966$, $150.0$ GeV).

The physical pilot verdict is **VALIDATED**. All three requested coupling points were physically generated with MadGraph 3.5.3, producing 1000 unweighted events per coupling point with $h_2$ (PDG 9000006) kept stable in LHE.

The direct MadGraph cross-section measurements confirm purely quadratic cross-section scaling:
$$\sigma_{\text{mg}}(g) = \sigma_0 \left(\frac{g}{g_0}\right)^2$$
with relative cross-section residuals $< 0.4\%$ across all coupling points. Parton-level shape comparison across all 8 kinematic observables confirms that normalized production kinematics are strictly unchanged by coupling scaling.

## 2. MadGraph Execution Summary

* **MadGraph Version**: 3.5.3
* **Process**: `g g > H > h2 h2`
* **Center-of-Mass Energy**: 13 TeV
* **PDF Set**: `nn23lo1` (LHAPDF ID 230000; built-in MG PDF support)
* **Scale Settings**: `fixed_ren_scale = False`, `fixed_fac_scale = False`, `scalefact = 1.0`
* **UFO Model SHA-256**: `9c685714f8840190cb08c34e4b804481564599619c1a3fa9a212256624951d33`

| Point ID | $g_{\text{target}}$ [GeV] | $GHphiphi$ [GeV] | Seed | $\sigma_{\text{mg}}$ [pb] | Error [pb] | $\sigma_{\text{pred}}$ [pb] | Relative Residual | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `mg_pilot_g40` | 40.0000 | -40.0000 | 1101 | 9.129000e-05 | 2.2250e-07 | 9.111715e-05 | +1.8970e-03 | `MADGRAPH_DIRECT_RUN` |
| `mg_pilot_g63p591425` | 63.5914 | -63.5914 | 1102 | 2.299000e-04 | 7.9820e-07 | 2.302912e-04 | -1.6986e-03 | `MADGRAPH_DIRECT_RUN` |
| `mg_pilot_g150` | 150.0000 | -150.0000 | 1103 | 1.281000e-03 | 3.9660e-06 | 1.281335e-03 | -2.6143e-04 | `MADGRAPH_DIRECT_RUN` |

## 3. Parton-Level Kinematic Shape Comparison

Eight parton-level kinematic observables were reconstructed directly from the final-state $h_2$ pair in the LHE files:
1. $m_{H2H2}$: Invariant mass of $h_2 h_2$ pair
2. $p_{T, H2H2}$: Transverse momentum of $h_2 h_2$ pair
3. $p_{T, H2, \text{leading}}$: Leading $h_2$ transverse momentum
4. $p_{T, H2, \text{subleading}}$: Subleading $h_2$ transverse momentum
5. $y_{H2, \text{leading}}$: Leading $h_2$ rapidity
6. $y_{H2, \text{subleading}}$: Subleading $h_2$ rapidity
7. $\Delta\phi(H2, H2)$: Azimuthal opening angle
8. $\Delta R(H2, H2)$: Angular separation $\sqrt{(\Delta y)^2 + (\Delta\phi)^2}$

For each observable and point pair, normalized 20-bin histograms were compared.

### Summary of Pairwise Shape Differences (Max Absolute Bin Difference)

| Observable | $g=40$ vs $g=63.59$ | $g=63.59$ vs $g=150$ | $g=40$ vs $g=150$ |
| :--- | :--- | :--- | :--- |
| `m_H2H2` | 0.0199 | 0.0250 | 0.0227 |
| `pT_H2H2` | 0.0000 | 0.0000 | 0.0000 |
| `pT_H2_leading` | 0.0322 | 0.0155 | 0.0419 |
| `pT_H2_subleading` | 0.0310 | 0.0242 | 0.0234 |
| `y_H2_leading` | 0.0160 | 0.0120 | 0.0199 |
| `y_H2_subleading` | 0.0295 | 0.0263 | 0.0270 |
| `delta_phi_H2H2` | 0.0000 | 0.0000 | 0.0000 |
| `delta_R_H2H2` | 0.0310 | 0.0070 | 0.0290 |

All maximum absolute bin differences are within statistical Monte Carlo fluctuations ($N = 1000$ events per point).

## 4. Verification & Validation Gates

* [x] Three requested g points executed (g = 40.0, 63.59142520075966, 150.0 GeV)
* [x] Three authoritative param cards preserved with modified `FRBlock 3`
* [x] Three distinct seeds recorded (1101, 1102, 1103)
* [x] Three LHE files preserved with 1000 events each
* [x] Two stable $H_2$ particles (PDG 9000006) per event verified
* [x] MadGraph $\sigma$ and integration error extracted
* [x] $g_{\text{effective}}$ value independently verified ($GHphiphi = -g$)
* [x] Quadratic residual calculated (max relative residual = 1.8970e-03)
* [x] Normalized LHE shapes compared across all 8 observables
* [x] Cards, banners, logs, and LHE files hashed in `artifact_manifest.json`
* [x] Factorized-mode regression passes
* [x] No silent fallback exists between `madgraph` and `factorized` modes

## 5. Limitations & Downstream Scope

* Pythia showering, hadronization, trackless recast, and $A \times \epsilon$ calculation were explicitly excluded from this pilot mission.
* Statistical comparison is bounded by finite Monte Carlo sample size (1000 events per point).
