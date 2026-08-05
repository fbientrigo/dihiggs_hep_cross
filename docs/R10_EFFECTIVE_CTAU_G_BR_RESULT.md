# R10 Scientific Report — Effective Phenomenological Scan in $(c\tau, g_{hH_2H_2}, \mathrm{BR}_{b\bar{b}})$

## Executive Summary

This study constructs a model-independent effective exploration of the scalar pair-production signal $pp \to H_2 H_2 \to (b\bar{b})(b\bar{b})$ at $\sqrt{s} = 13\text{ TeV}$ with an integrated luminosity of $139\text{ fb}^{-1}$, evaluated against the primary ATLAS DV+jets Trackless signal region across an extended 12-point lifetime grid ($c\tau \in [0.3, 1000.0]\text{ mm}$, covering the centimetre-to-metre regime: $1\text{ cm}$, $10\text{ cm}$, $20\text{ cm}$, $50\text{ cm}$, $70\text{ cm}$, $1\text{ m}$).

In this exploration, three physical parameters are varied as independent numerical inputs:
1. **$c\tau_{\mathrm{mm}}$**: Proper decay length of $H_2$ ($12$ values up to $1000\text{ mm} = 1\text{ m}$).
2. **$g_{hH_2H_2}$** [GeV]: Trilinear production coupling for $h \to H_2 H_2$ ($6$ values from $40$ to $300\text{ GeV}$).
3. **$\mathrm{BR}(H_2 \to b\bar{b})$**: Branching fraction of $H_2$ to $b\bar{b}$ ($5$ values from $0.1$ to $1.0$).

Every point evaluated in this 360-point grid is explicitly labeled as an **effective phenomenological point**. These variables are treated as numerically independent and are **not yet mapped to a theory-valid 2HDM point**. No 2HDM theoretical validity condition (such as vacuum stability, unitarity, or perturbativity) is imposed on this effective scan grid.

All conclusions based on $g_{hH_2H_2}$ use the structurally exact quadratic cross-section prediction $\sigma(g) = \sigma_0 \cdot (g/g_0)^2$ anchored to the validated baseline. They are not measured MadGraph outputs because MadGraph could not be executed locally due to missing LHAPDF set 230000 (`MADGRAPH_NOT_EXECUTED_LHAPDF_UNAVAILABLE; STRUCTURAL_PREDICTION_ONLY`).

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

### Primary Question: How far into the centimetre-to-metre lifetime regime does ATLAS Trackless selection retain sensitivity?
The ATLAS Trackless selection retains significant single-event sensitivity ($N_{\text{expected}} \ge 1.0$) up to **$c\tau = 1000\text{ mm}$ ($1\text{ m}$)**:
* At $c\tau = 200\text{ mm}$ ($20\text{ cm}$), $(A \times \epsilon) = 0.009507$, reaching **$N_{\text{expected}} = 6.778\text{ events}$** at $g = 300\text{ GeV}$ ($\mathrm{BR} = 1.0$) and **$3.882\text{ events}$** at baseline BR ($0.7567$), exceeding the observed $S_{95} = 3.0$ threshold.
* At $c\tau = 500\text{ mm}$ ($50\text{ cm}$), $(A \times \epsilon) = 0.003869$, reaching $N_{\text{expected}} = 2.758\text{ events}$ ($\mathrm{BR} = 1.0$) and $1.579\text{ events}$ at baseline BR.
* At $c\tau = 700\text{ mm}$ ($70\text{ cm}$), $(A \times \epsilon) = 0.003478$, reaching $N_{\text{expected}} = 2.479\text{ events}$ ($\mathrm{BR} = 1.0$) and $1.420\text{ events}$ at baseline BR.
* At $c\tau = 1000\text{ mm}$ ($1\text{ m}$), $(A \times \epsilon) = 0.002464$, retaining single-event sensitivity with **$N_{\text{expected}} = 1.756\text{ events}$** at $g = 300\text{ GeV}$ ($\mathrm{BR} = 1.0$) and $1.006\text{ events}$ at baseline BR.

Thus, $S_{95}$ exclusion reach extends to $c\tau \approx 200\text{ mm}$ ($20\text{ cm}$), while $N \ge 1$ sensitivity extends fully to **$1000\text{ mm}$ ($1\text{ m}$)**.

### 1. How does Trackless efficiency vary with $c\tau$?
Across the 12 $c\tau$ points:
* $c\tau = 0.3\text{ mm}$: 0 selected events out of 2000; efficiency is unresolved and recorded as a 95% CL upper limit ($< 0.001498$) rather than claiming zero physically.
* $c\tau = 1.0\text{ mm}$: $(A \times \epsilon) = 0.003952$ (10 selected events, `VALIDATED`).
* $c\tau = 4.33\text{ mm}$ (baseline anchor): $(A \times \epsilon) = 0.015734$ (40 selected events, `VALIDATED`).
* $c\tau \in [10.0, 30.0]\text{ mm}$: Statistically compatible efficiency plateau with $(A \times \epsilon) \approx 0.0186$ (47–48 selected events, `VALIDATED`).
* $c\tau = 100\text{ mm}$ ($10\text{ cm}$): $(A \times \epsilon) = 0.014253$ (47 selected events, `VALIDATED`).
* $c\tau = 200\text{ mm}$ ($20\text{ cm}$): $(A \times \epsilon) = 0.009507$ (40 selected events, `VALIDATED`).
* $c\tau = 500\text{ mm}$ ($50\text{ cm}$): $(A \times \epsilon) = 0.003869$ (24 selected events, `VALIDATED`).
* $c\tau = 700\text{ mm}$ ($70\text{ cm}$): $(A \times \epsilon) = 0.003478$ (17 selected events, `VALIDATED`).
* $c\tau = 1000\text{ mm}$ ($1\text{ m}$): $(A \times \epsilon) = 0.002464$ (15 selected events, `VALIDATED`).
* The gradual decrease at large $c\tau$ is consistent with more decays occurring outside the fiducial displaced-vertex volume.

### 2. How does the production cross section vary with $g$?
The production cross section $\sigma_{\text{production}}(g)$ uses the structurally exact quadratic prediction anchored to the validated baseline $\sigma(g) = \sigma_0 \cdot (g/g_0)^2$:
* $g = 40.0\text{ GeV} \implies \sigma = 0.000091001428\text{ pb}$
* $g = 63.59\text{ GeV} \implies \sigma = 0.000230291168\text{ pb}$ (baseline anchor)
* $g = 100.0\text{ GeV} \implies \sigma = 0.000569103756\text{ pb}$
* $g = 150.0\text{ GeV} \implies \sigma = 0.001281334981\text{ pb}$ (structural prediction)
* $g = 205.09\text{ GeV} \implies \sigma = 0.002395414519\text{ pb}$
* $g = 300.0\text{ GeV} \implies \sigma = 0.005125339926\text{ pb}$

### 3. How strongly does $\mathrm{BR}_{b\bar{b}}^2$ suppress or enhance the final yield?
Because both produced scalars decay into $b\bar{b}$, the signal yield scales quadratically with $\mathrm{BR}(H_2 \to b\bar{b})$:
* $\mathrm{BR} = 1.00 \implies \text{factor} = 1.0000$ ($1.75\times$ enhancement over baseline $\text{BR}_0^2$)
* $\mathrm{BR} = 0.7567 \implies \text{factor} = 0.5727$ (baseline anchor)
* $\mathrm{BR} = 0.50 \implies \text{factor} = 0.2500$ ($2.29\times$ suppression relative to baseline)
* $\mathrm{BR} = 0.25 \implies \text{factor} = 0.0625$ ($9.16\times$ suppression relative to baseline)
* $\mathrm{BR} = 0.10 \implies \text{factor} = 0.0100$ ($57.27\times$ suppression relative to baseline)

### 4. Which effective combinations reach one expected event ($N_{\text{expected}} \ge 1$)?
Out of 360 grid points, **68 effective combinations** reach or exceed $N_{\text{expected}} \ge 1.0$.

### 5. Which effective combinations reach observed $S_{95} = 3.0$ events?
Out of 360 grid points, **26 effective combinations** reach or exceed the official ATLAS model-independent Trackless threshold of $S_{95} = 3.0$ events ($\sigma_{\text{visible}} \ge 0.022\text{ fb}$):
* Maximum yield in the grid occurs at $(c\tau = 10\text{ mm}, g = 300\text{ GeV}, \mathrm{BR} = 1.0)$, reaching **$N_{\text{expected}} = 13.269202801224393\text{ events}$**.
* At baseline BR ($\mathrm{BR}_0 = 0.7567$), the maximum yield at $(c\tau = 10\text{ mm}, g = 300\text{ GeV})$ is **$N_{\text{expected}} = 7.598630512445835\text{ events}$**.

---

## Artifact Inventory

All generated artifacts are committed under `results/r10_effective_ctau_g_br_scan/`:
* `production_vs_g.csv` (6 production coupling points)
* `efficiency_vs_ctau.csv` (12 lifetime efficiency points)
* `effective_grid.csv` (360 Cartesian grid points)
* `result_summary.json` (Programmatically generated JSON summary)
* `efficiency_vs_ctau.png` (Static plot 1)
* `nexpected_3d_ctau_g_br.png` (Static plot 2)
* `nexpected_ctau_vs_g_br_baseline.png` (2D Cut 1)
* `nexpected_g_vs_br_ctau_baseline.png` (2D Cut 2)
* `nexpected_ctau_vs_br_g_atlas.png` (2D Cut 3)
* `nexpected_3d_interactive.html` (Plotly interactive 3D model)
* `artifact_manifest.json` (Cryptographic SHA-256 manifest)
