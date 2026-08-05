# R10 Scientific Report — Effective Phenomenological Scan in $(c\tau, g_{hH_2H_2}, \mathrm{BR}_{b\bar{b}})$

## Executive Summary

This study constructs a model-independent effective exploration of the scalar pair-production signal $pp \to H_2 H_2 \to (b\bar{b})(b\bar{b})$ at $\sqrt{s} = 13\text{ TeV}$ with an integrated luminosity of $139\text{ fb}^{-1}$, evaluated against the primary ATLAS DV+jets Trackless signal region.

In this exploration, three physical parameters are varied as independent numerical inputs:
1. **$c\tau_{\mathrm{mm}}$**: Proper decay length of $H_2$.
2. **$g_{hH_2H_2}$** [GeV]: Trilinear production coupling for $h \to H_2 H_2$.
3. **$\mathrm{BR}(H_2 \to b\bar{b})$**: Branching fraction of $H_2$ to $b\bar{b}$.

Every point evaluated in this scan is explicitly labeled as an **effective phenomenological point**. These variables are treated as numerically independent and are **not yet mapped to a theory-valid 2HDM point**. No 2HDM theoretical validity condition (such as vacuum stability, unitarity, or perturbativity) is imposed on this effective scan grid.

---

## Core Factorization and Simulation Contract

The physical yield in the ATLAS DV+jets Trackless region is factorized as:

$$\sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = \sigma_{\text{production}}(g) \times 1000\,\frac{\text{fb}}{\text{pb}} \times \mathrm{BR}(H_2 \to b\bar{b})^2 \times (A \times \epsilon)_{\text{Trackless}}(c\tau)$$

$$N_{\text{expected}}(c\tau, g, \mathrm{BR}_{b\bar{b}}) = 139\text{ fb}^{-1} \times \sigma_{\text{visible}}(c\tau, g, \mathrm{BR}_{b\bar{b}})$$

To prevent double counting, event samples were generated under a **conditional forced-bb efficiency** contract:
* Pythia/recast samples were generated forcing $H_2 \to b\bar{b}$ with $100\%$ branching fraction.
* The total decay width of $H_2$ is set purely by lifetime: $\Gamma_{\text{total}} = 1.973269804 \times 10^{-13}\text{ GeV mm} / c\tau_{\text{mm}}$.
* The physical branching fraction factor $\mathrm{BR}(H_2 \to b\bar{b})^2$ is applied algebraically during normalization.

---

## Validation of the Baseline Anchor

The frozen R8/R9 benchmark anchor point was verified with exact agreement before constructing the grid:
* $m_{H_2} = 150.0\text{ GeV}$
* $c\tau_0 = 4.326221529733112\text{ mm}$
* $g_0 = 63.59142520075966\text{ GeV}$ ($GH_{\phi\phi,0} = -63.59142520075966\text{ GeV}$)
* $\mathrm{BR}_{b\bar{b},0} = 0.7567374858085787$
* $\sigma_0 = 0.000230291167568\text{ pb}$
* $(A \times \epsilon)_{\text{Trackless},0} = 0.01573386$
* $\sigma_{\text{visible},0} = 0.0020749281306360694\text{ fb}$
* $N_{\text{expected},0} = 0.28841501015841364\text{ events}$

---

## Answers to Key Scientific Questions

### 1. How does Trackless efficiency vary with $c\tau$?
The selection efficiency $(A \times \epsilon)_{\text{Trackless}}$ exhibits a strongly non-monotonic dependence on $c\tau$:
* At $c\tau = 0.3\text{ mm}$, the efficiency is zero (0 selected events out of 2000), yielding status `LOW_MC_STATISTICS`.
* As $c\tau$ increases to $1.0\text{ mm}$, efficiency rises to $0.003952$ (10 selected events).
* At the baseline anchor $c\tau_0 = 4.326\text{ mm}$, efficiency is $0.015734$ (40 selected events).
* Peak selection efficiency occurs in the window $c\tau \in [10, 30]\text{ mm}$, reaching **$0.018625$** (47–48 selected events).
* Beyond $30\text{ mm}$, efficiency decreases as LLPs decay beyond the inner detector tracking volume, falling to $0.006872$ at $c\tau = 300\text{ mm}$.

### 2. How does the production cross section vary with $g$?
The production cross section $\sigma_{\text{production}}(g)$ scales quadratically with the trilinear coupling:

$$\sigma(g) = \sigma_0 \times \left(\frac{g}{g_0}\right)^2$$

For the tested couplings $g \in [40.0, 300.0]\text{ GeV}$:
* $g = 40.0\text{ GeV} \implies \sigma = 0.0000910\text{ pb}$ ($0.395 \times \sigma_0$)
* $g = 63.59\text{ GeV} \implies \sigma = 0.0002303\text{ pb}$ ($1.000 \times \sigma_0$)
* $g = 100.0\text{ GeV} \implies \sigma = 0.0005691\text{ pb}$ ($2.471 \times \sigma_0$)
* $g = 150.0\text{ GeV} \implies \sigma = 0.01280\text{ pb}$ ($5.560 \times \sigma_0$)
* $g = 205.09\text{ GeV} \implies \sigma = 0.0023954\text{ pb}$ ($10.402 \times \sigma_0$)
* $g = 300.0\text{ GeV} \implies \sigma = 0.0051280\text{ pb}$ ($22.268 \times \sigma_0$)

### 3. How strongly does $\mathrm{BR}_{b\bar{b}}^2$ suppress or enhance the final yield?
Because both produced scalars decay into $b\bar{b}$, the signal yield scales quadratically with $\mathrm{BR}(H_2 \to b\bar{b})$:
* $\mathrm{BR} = 1.00 \implies \text{factor} = 1.0000$ (enhancement of $1.75\times$ over baseline)
* $\mathrm{BR} = 0.7567 \implies \text{factor} = 0.5727$ (baseline anchor)
* $\mathrm{BR} = 0.50 \implies \text{factor} = 0.2500$ ($2.29\times$ suppression relative to baseline)
* $\mathrm{BR} = 0.25 \implies \text{factor} = 0.0625$ ($9.16\times$ suppression relative to baseline)
* $\mathrm{BR} = 0.10 \implies \text{factor} = 0.0100$ ($57.27\times$ suppression relative to baseline)

### 4. Which effective combinations reach one expected event ($N_{\text{expected}} \ge 1$)?
Out of the 240 grid points, **42 effective combinations** reach or exceed $N_{\text{expected}} \ge 1.0$.
Representative conditions:
* $g \ge 150\text{ GeV}$ with $c\tau \in [3, 100]\text{ mm}$ and $\mathrm{BR} \ge 0.50$.
* $g \ge 205\text{ GeV}$ with $c\tau \in [1, 300]\text{ mm}$ for $\mathrm{BR} \ge 0.50$.
* $g = 300\text{ GeV}$ for all $c\tau \in [1, 300]\text{ mm}$ down to $\mathrm{BR} = 0.25$.

### 5. Which effective combinations reach observed $S_{95} = 3.0$ events?
Out of 240 grid points, **21 effective combinations** reach or exceed the official ATLAS model-independent Trackless threshold of $S_{95} = 3.0$ events ($\sigma_{\text{visible}} \ge 0.022\text{ fb}$):
* At baseline lifetime $c\tau_0 = 4.33\text{ mm}$ and $\mathrm{BR}_0 = 0.757$, $g = 205.09\text{ GeV}$ yields exactly **$N_{\text{expected}} = 3.00$ events**.
* At $g = 300\text{ GeV}$ and peak lifetime $c\tau \in [10, 30]\text{ mm}$ with $\mathrm{BR} = 1.00$, the yield reaches **$N_{\text{expected}} = 25.8$ events** ($8.6 \times S_{95}$).

### 6. Where is the validated R8/R9 anchor in the effective space?
The baseline anchor point sits at $(c\tau = 4.326\text{ mm}, g = 63.59\text{ GeV}, \mathrm{BR} = 0.7567)$ with:
* $N_{\text{expected}} = 0.2884\text{ events}$
* $N / S_{95} = 0.0961$ ($9.6\%$ of the exclusion threshold)
* `above_observed_S95 = False`

The anchor point is safely below experimental exclusion, situated in the unexcluded regime of the parameter space.

### 7. Which results are measured with MadGraph/recast and which are algebraic?
* **Measured with Full Pythia + ATLAS DV+jets Recast**:
  The 8 efficiency values $(A \times \epsilon)_{\text{Trackless}}(c\tau)$ were computed via Pythia showering and detector recast across 16 run logs (2000 events per $c\tau$ point).
* **Algebraic Cartesian Grid**:
  The 240-point grid for $\sigma_{\text{production}}(g)$, $\sigma_{4b}$, $\sigma_{\text{visible}}$, and $N_{\text{expected}}$ was constructed algebraically exploiting the core factorization.
* **MadGraph Production Status**:
  MadGraph cross-section measurements could not be executed due to the local absence of LHAPDF set 230000. Measured columns in `production_vs_g.csv` are preserved blank with status `MADGRAPH_NOT_EXECUTED_LHAPDF_UNAVAILABLE;STRUCTURAL_PREDICTION_ONLY`.

---

## Artifact Inventory

All generated artifacts are committed under `results/r10_effective_ctau_g_br_scan/`:
* `production_vs_g.csv` (6 production coupling points)
* `efficiency_vs_ctau.csv` (8 lifetime efficiency points)
* `effective_grid.csv` (240 Cartesian grid points)
* `result_summary.json` (Structured JSON summary)
* `efficiency_vs_ctau.png` (Static plot 1)
* `nexpected_3d_ctau_g_br.png` (Static plot 2)
* `nexpected_ctau_vs_g_br_baseline.png` (2D Cut 1)
* `nexpected_g_vs_br_ctau_baseline.png` (2D Cut 2)
* `nexpected_ctau_vs_br_g_atlas.png` (2D Cut 3)
* `nexpected_3d_interactive.html` (Plotly interactive 3D model)
* `artifact_manifest.json` (Cryptographic SHA-256 manifest)
