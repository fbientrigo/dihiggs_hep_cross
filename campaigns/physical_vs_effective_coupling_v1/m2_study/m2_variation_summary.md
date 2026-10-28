# M2 variation grid — factual summary (no interpretation)

**FIXED (previously flagged per `validation/SOL_FINAL_REVIEW.md` Additional issue #3, now resolved -- see `validation/MASS_RECONSTRUCTION_FIX.md`):** every row in `m2_variation.csv` is at tan(beta)=4e7. 2HDMC's own `get_hmass()` used to round-trip through `get_m12_2()` (catastrophic cancellation, THDM.cpp:2786) and return a mass 1.5-4.6% off the requested mphi/mA/mHp, which fed directly into `total_width_h2_GeV`/`ctau_h2_mm` via `DecayTable`. `THDM::set_param_phys()`/`set_param_phys_lam1()` now cache the exact physical-basis inputs they are given (masses, m12_2, and -- a second, independent conditioning bug found while fixing the first -- lambda1) instead of re-deriving them through the lossy round-trip, so `get_hmass()` now returns the requested mass exactly at any tan(beta). The `hmass_h2_reconstructed_GeV`/`hmass_hA_reconstructed_GeV`/`hmass_hHp_reconstructed_GeV` columns confirm this directly (now equal to `mphi_in`/`mA_in`/`mHp_in` to machine precision). `total_width_h2_GeV` and `ctau_h2_mm` in this file and `sensitivity_probes.csv` were regenerated with the fix. In `m2_variation.csv` the shift is roughly 5-10% relative to the pre-fix values (e.g. mphi=200 GeV row 1: total_width_h2_GeV 1.198e7->1.287e7 GeV, ctau_h2_mm 1.648e-20->1.533e-20 mm), consistent with the previously measured mass error. In `sensitivity_probes.csv` (the r=M2/mphi^2=1 anchor point) the shift is smaller, ~1.7% (pre-fix 1.3118e-15 GeV -> post-fix 1.3339e-15 GeV on total_width_h2_GeV). **Correction to this paragraph, made during a later bias/behavior audit (`validation/SOL_BIAS_AUDIT.md`):** an earlier version of this text claimed the sensitivity_probes.csv pre-fix value was 2.349e-13 GeV (a ~176x swing). That number was never a real pre-fix value -- it was itself an artifact of the build-staleness bug described next, and asserting it as 'the pre-fix value' repeated, in this exact paragraph, the same error class the paragraph was written to explain. The number above (1.3118e-15 GeV, ~1.7%) is the genuine, independently-reproduced pre-fix value. **Build-hygiene bug, found by an independent review (`validation/SOL_FINAL_REVIEW_2.md`), and FIXED (not just documented) in the Makefile itself:** 2HDMC's Makefile used to make each object file depend only on its own matching header, not on any header it transitively `#include`s. `DecayTable`/`Constraints` each hold a `THDM model;` member BY VALUE, so any incremental `make` (without `make clean` first) after `THDM.h` changed size used to silently link a fresh `THDM.o` against stale `DecayTable.o`/`Constraints.o`/`SM.o`/`Util.o` -- a real ODR violation producing deterministic but wrong width/BR/ctau/theory-flag numbers, with NO compiler warning. This bug (not the mass-reconstruction physics fix) was responsible for several wildly wrong 'before/after' comparisons produced earlier in this same session and since corrected (see `validation/MASS_RECONSTRUCTION_FIX.md`), including the 176x claim corrected two paragraphs above. The Makefile (`2hdmc_build/Makefile` here and in every other 2hdmc build directory in this workspace) now uses `-MMD -MP` plus an `-include` of the generated `.d` files, so a plain `make` after any header change rebuilds everything that actually depends on it -- verified directly: touching only `THDM.h` and running `make` (no `make clean`) now recompiles `THDM.o`, `DecayTable.o`, and `Constraints.o` automatically. `make clean` before the first build on a fresh checkout is still needed (no `.d` files exist yet then), but this bug can no longer recur silently on an ordinary incremental build. The values in this file and `sensitivity_probes.csv` were regenerated after this Makefile fix and independently cross-checked. The trilinear coupling itself (`g_hphiphi_imag_GeV`) was never affected -- `get_coupling_hhh` never calls `get_m12_2()` -- and changed only in its last significant digit across this regeneration. (The separate `m2_variation_moderate_tanbeta_illustrative.csv` and `m2_variation_finegrid_tanbeta10_illustrative.csv` files, at tan(beta)=10, were never affected -- mass round-trip was already machine-precision there.)


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
