# Physical-point MadGraph workflow

This is the default production workflow for the next 2HDM LLP scan.

## Goal

For every accepted physical `dihiggs.point.v2` row, obtain the production cross section from MadGraph rather than inferring it from a single coupling rescaling.

```text
dihiggs.point.v2
  -> point-specific UFO/parameter mapping
  -> MadGraph
  -> sigma_production_fb + sigma_production_unc_fb
  -> join by point_id
  -> Boundary / Trackless response
```

## Minimal execution rule

For each physical point:

1. preserve the stable `point_id`;
2. write the point-specific parameter card from the canonical model row;
3. run the frozen production process with the declared UFO, PDF, scales and collider energy;
4. record the LO cross section and MadGraph integration uncertainty;
5. join the result back onto the same row as `sigma_production_fb` and `sigma_production_unc_fb`.

No Pythia or recast run is required merely to obtain the production cross section.

## What must stay fixed across a comparable campaign

```text
UFO revision
MadGraph version
process syntax / coupling-order restrictions
sqrt(s)
PDF set
scale prescription
run-card settings except the intentional point-dependent values
```

Point-dependent parameters must come from the canonical row rather than a hand-edited benchmark copy.

## Validation before a larger scan

Use one known benchmark and one repeated seed/run to check:

- parameter-card values match the canonical point;
- the intended diagrams are present;
- units are correct;
- repeated integrations agree within their integration uncertainties;
- the exported row matches the frozen benchmark cross section within the expected integration precision.

Then run the physical points. A large architecture layer is not required.

## Coupling-scaling studies

Historical or dedicated scans of `g_hH2H2` remain useful for understanding the restricted production setup. A measured relation close to `sigma ~ g^2` in that controlled slice is a validation result, not the general production engine for a scan where the full 2HDM point changes.

## Downstream handoff

The downstream signal calculation receives, per point:

```text
point_id
m_H2_GeV
g_hH2H2_GeV
ctau_mm_H2
br_bb_H2
sigma_production_fb
sigma_production_unc_fb
```

and combines the production result with a separately versioned Trackless `Aeff(ctau)` response.

For the current H2 -> bb pair signal:

```text
sigma_4b      = sigma_production_fb * br_bb_H2^2
sigma_visible = sigma_4b * Trackless_Aeff
N_expected    = luminosity * sigma_visible
```

Do not hide production assumptions inside the acceptance calibration.
