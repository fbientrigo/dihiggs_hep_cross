# Dataset card: ATLAS HIGG-2018-27

```text
Dataset name       : Search for resonances decaying into photon pairs in
                      139 fb^-1 of pp collisions at sqrt(s)=13 TeV with the
                      ATLAS detector
Paper/arXiv         : arXiv:2102.13405
Collaboration       : ATLAS
Luminosity          : 139 fb^-1 (full Run 2)
sqrt(s)             : 13 TeV
Final state         : prompt diphoton (gamma gamma)
Spin hypotheses     : spin-0 (scalar), spin-2 (RS graviton, k/Mpl 0.01/0.05/0.1)
Mass range found    : NWA scalar: 160-3000 GeV (143 pts)
                       2%/6%/10% width scalar: 400-2800 GeV (121 pts each)
Width hypotheses    : NWA (~0%), 2%, 6%, 10% of m_X (spin-0);
                       also a 2D grid (Limit2D_Scalar, continuous width axis)
Main observable     : 95% CL upper limit on fiducial sigma x BR(X -> gamma gamma)
                       vs m_X, observed + expected (+-1, +-2 sigma bands)
```

## Status labels

```text
PRIMARY_DATASET
DIRECTLY_RELEVANT_DIPHOTON
DOWNLOAD_VERIFIED
TABLES_NOT_YET_VERIFIED_AGAINST_PAPER_TEXT   (numbers pulled from YAML,
                                               not cross-checked against
                                               printed paper figures)
READY_FOR_PRESENTATION
```

`DOWNLOAD_VERIFIED` applies because the local bundle exists at
`data/hepdata/atlas_diphoton_higg_2018_27/yaml_raw/HEPData-ins1849059-v2-yaml/`
(extracted from the user-supplied
`data/HEPData-ins1849059-v2-yaml.tar.gz`) and every table's `table_doi`
field resolves to `10.17182/hepdata.100161.v2/tN`, matching the target DOI
`10.17182/hepdata.100161` from the task brief.

## Expected HEPData tables needed (all present locally)

| Table | File | Role |
|---|---|---|
| t1 | `Limit1D_NW_Scalar.yaml` | scalar, narrow-width limit vs mass |
| t5 | `Limit1D_LW002_Scalar.yaml` | scalar, Gamma/m=2% limit vs mass |
| t6 | `Limit1D_LW006_Scalar.yaml` | scalar, Gamma/m=6% limit vs mass |
| t7 | `Limit1D_LW01_Scalar.yaml` | scalar, Gamma/m=10% limit vs mass |
| t3 | `Limit2D_Scalar.yaml` | scalar, 2D grid (mass x Gamma/m), 2541 pts |
| t13 | `Selection_Eff_Spin0.yaml` | C_X * A_X (acceptance x efficiency) vs mass |
| t15 | `DSCB_Parameters_Spin0.yaml` | mass-resolution model parameters |
| t10/t11 | `diphoton_invMassSpectrum_*.yaml` | observed diphoton mass spectrum |
| t12 | `diphoton_selection_cutflow.yaml` | event-selection cutflow |

Full machine-readable inventory:
`outputs/diphoton_higg_2018_27_inventory/table_inventory.{csv,md}`.

## Immediate usefulness

The 4 spin-0 1D limit tables + the 2D grid give us the complete
experiment side of the sigma*BR comparison contract today, with no
further downloading needed. `Selection_Eff_Spin0.yaml` is the bridge if
we ever need to go from a *total* theoretical cross section to the
*fiducial* one the limits are actually quoted against.

## Limitations

- Width hypotheses are 4 discrete points (0/2/6/10%); a 2HDM point's
  `Gamma_H/m_H` will usually fall between them — nearest-hypothesis
  matching or the `Limit2D_Scalar` grid is needed for anything more
  precise (`WIDTH_MATCH_APPROXIMATE` flag).
- Limits are on the **fiducial** cross section, not the total one; using
  them against a total theoretical `sigma_ggF`/`sigma_VBF` requires
  applying `C_X * A_X` from `Selection_Eff_Spin0.yaml`
  (`FIDUCIAL_VS_TOTAL_CHECK_REQUIRED` flag) — not yet done here.
- Spin-0 limits assume a generic scalar resonance, not specifically a
  2HDM `H2`; production-mode-dependent angular/acceptance effects are not
  captured (`SPIN0_ASSUMPTION_OK_FOR_2HDM` flag, meaning "assumption
  holds but not independently checked").
