# M2 variation grid — factual summary (no interpretation)

**Caveat added per `validation/SOL_FINAL_REVIEW.md` Additional issue #3:** every row in `m2_variation.csv` is at tan(beta)=4e7. At this tan(beta), 2HDMC's own `get_hmass()` (which the DecayTable width/ctau calculation is built on) round-trips through `get_m12_2()` and returns a mass 1.5-4.6% off the requested mphi/mA/mHp (catastrophic cancellation, THDM.cpp:2786). The new `hmass_h2_reconstructed_GeV`/`hmass_hA_reconstructed_GeV`/`hmass_hHp_reconstructed_GeV` columns in `m2_variation.csv` and `sensitivity_probes.csv` show 2HDMC's own reconstructed value directly. **`total_width_h2_GeV` and `ctau_h2_mm` in those two files should be treated as computed at the reconstructed mass, not the requested `mphi_in`, and are not reliable width/ctau numbers at this tan(beta).** The trilinear coupling itself (`g_hphiphi_imag_GeV`) is unaffected -- `get_coupling_hhh` never calls `get_m12_2()`. (The separate `m2_variation_moderate_tanbeta_illustrative.csv` and `m2_variation_finegrid_tanbeta10_illustrative.csv` files, at tan(beta)=10, are not affected -- mass round-trip is machine-precision there.)


## mphi = 200.0 GeV

theory-valid r = M2/mphi^2 values (construction_ok AND unitarity_ok AND perturbativity_ok AND positivity_ok, all ==1):

| r | g_hphiphi_imag_GeV |
|---|---|
| exact_via_star_identity_lambda1eq1 | -63.459361 |

## mphi = 250.0 GeV

theory-valid r = M2/mphi^2 values (construction_ok AND unitarity_ok AND perturbativity_ok AND positivity_ok, all ==1):

| r | g_hphiphi_imag_GeV |
|---|---|
| exact_via_star_identity_lambda1eq1 | -63.459362 |

## mphi = 300.0 GeV

theory-valid r = M2/mphi^2 values (construction_ok AND unitarity_ok AND perturbativity_ok AND positivity_ok, all ==1):

| r | g_hphiphi_imag_GeV |
|---|---|
| exact_via_star_identity_lambda1eq1 | -63.459362 |
