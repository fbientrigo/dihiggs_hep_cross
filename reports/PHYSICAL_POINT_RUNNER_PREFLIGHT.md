# Forensic Physics Review: Recovered Files vs Canonical Upstream

**Date**: August 8, 2026  
**Repositories**:
- Canonical upstream `main_dihiggs`: commit `9f8019690c44bb68d46a3b60f5ac2ac349d445f2` (branch `main`)
- Recovered orphaned backup: `/home/fabi/atlas_dihiggs/main_dihiggs_orphaned_backup_2026-08-07`

---

## 1. Executive Summary

| Recovered File | Category | Verdict |
| :--- | :--- | :--- |
| `dihiggs/src/DihiggsPointV2Evaluator.cpp` | **ALREADY_SUPERSEDED** | Canonical upstream already includes the complete `THDM::get_coupling_hhh(1, 2, 2, ...)` evaluation and exports `g_hH2H2_GeV = std::abs(coupling_h1_h2_h2.imag())`. The backup is an older state prior to PR #76. |
| `docs/contracts/canonical_evaluators_v2.md` | **ALREADY_SUPERSEDED** | Canonical upstream already contains the full contract section "Canonical `h-H2-H2` observable", documenting `g_hH2H2_GeV`, the `2HDMC: c = -i*g` vs `UFO: GHphiphi = Im(c) = -g_hH2H2_GeV` sign convention, and the frozen benchmark anchor values. |
| `benchmarks/check_H2scan_mH150_tb300000.cpp` | **ALREADY_SUPERSEDED** | Canonical upstream already checks `g_h1h2h2_real_gev` and `g_h1h2h2_imag_gev` and tests the frozen benchmark anchor. |

---

## 2. Detailed File Inspection & Diffs

### File A: `dihiggs/src/DihiggsPointV2Evaluator.cpp`

- **Diff**:
  ```diff
  --- /home/fabi/atlas_dihiggs/main_dihiggs/dihiggs/src/DihiggsPointV2Evaluator.cpp
  +++ /home/fabi/atlas_dihiggs/main_dihiggs_orphaned_backup_2026-08-07/dihiggs/src/DihiggsPointV2Evaluator.cpp
  @@ -23,7 +22,7 @@
  -constexpr const char* kApi = "THDM::set_param_phys+THDM::get_param_gen+THDM::get_coupling_hhh+2HDMC::DecayTable";
  +constexpr const char* kApi = "THDM::set_param_phys+THDM::get_param_gen+2HDMC::DecayTable";
  @@ -189,10 +187,6 @@
  -    std::complex<double> coupling_h1_h2_h2;
  -    model.get_coupling_hhh(1, 2, 2, coupling_h1_h2_h2);
  -    r.g_hH2H2_GeV = std::abs(coupling_h1_h2_h2.imag());
  ```
- **Physics vs Implementation**: The backup omitted the native trilinear coupling observable calculation `get_coupling_hhh(1,2,2)`. Upstream commit `9f80196` added it properly.
- **Serialized dihiggs.point.v2 observable**: Upstream exports `g_hH2H2_GeV` in CSV column 20. Backup had this column missing.
- **Physics quantities affected**: No change to masses, widths, BRs, lifetimes ($c\tau$), $M^2$, $m_{12}^2$, or $\lambda_i$. Upstream additionally computes and emits $g_{hH_2H_2}$.
- **Classification**: **ALREADY_SUPERSEDED** by upstream `9f80196`.

### File B: `docs/contracts/canonical_evaluators_v2.md`

- **Diff**: Upstream contains the full subsection explaining `THDM::get_coupling_hhh(1,2,2,c)` with `g_hH2H2_GeV = abs(Im(c))` and the anchor benchmark:
  - $m_H = 150\text{ GeV}$
  - $g_{hH_2H_2} = 63.5914252007596588\text{ GeV}$
  - $c\tau = 4.32622152973311191\text{ mm}$
  - $\text{BR}(H_2 \to b\bar{b}) = 0.756737485808578692$
- **Classification**: **ALREADY_SUPERSEDED** by upstream `9f80196`.

### File C: `benchmarks/check_H2scan_mH150_tb300000.cpp`

- **Diff**: Upstream checks real and imaginary parts of the coupling and ensures parity with 2HDMC's native methods.
- **Classification**: **ALREADY_SUPERSEDED** by upstream `9f80196`.

---

## 3. Decision

No manual recovery from `/home/fabi/atlas_dihiggs/main_dihiggs_orphaned_backup_2026-08-07` is necessary because canonical `main_dihiggs` at commit `9f80196` already embodies all required physical updates. The backup directory will be left untouched as reference.

All tests in `main_dihiggs` (`tests/test_dihiggs_point_v2.py` and `benchmarks/test_h2_production_coupling.py`) pass cleanly.
