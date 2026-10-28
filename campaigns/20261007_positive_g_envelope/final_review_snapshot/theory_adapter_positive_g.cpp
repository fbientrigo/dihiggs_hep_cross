#include "Constraints.h"
#include "THDM.h"
#include "YukawaType.hpp"

#include <cmath>
#include <complex>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>

// Verified Theory Adapter for Positive Signed g_hphiphi Envelope Campaign.
// Coordinates: (point_id, mphi, tanbeta, delta_g, lambda1_input, mA, mHp)
// Stable relations:
// delta = 0.5 * v * delta_g (direct, no subtraction)
// M2 = mphi^2 - delta
// lambda6 = t * delta_g / (3v) + 2 / (3t) * (mh^2 / v^2 - lambda1)
// g_phys = -Im(c_122) = v*(Z3+Z4+Z5)
// g_expected_stable = mh^2 / v + delta_g
// Z7_analytic = (mh^2/v^2 - lambda1)/3 * (1/t + 1/t^3) + delta/(3*v^2) * (-2t + 4/t)
int main() {
  std::cout << "point_id,mphi,tanbeta,delta_g,lambda1_input,mA,mHp,M2_input,m12sq_input,lambda6_input,"
               "lambda1,lambda2,lambda3,lambda4,lambda5,lambda6,lambda7,"
               "Z1,Z2,Z3,Z4,Z5,Z6,Z7,c_real,c_imag,v,"
               "sba_reconstructed,tanbeta_reconstructed,mh_reconstructed,mH_reconstructed,mA_reconstructed,mHp_reconstructed,"
               "m12_reconstructed,M2_reconstructed,yukawa_type_installed,"
               "err_mh,err_mH,err_mA,err_mHp,err_sba,err_tanb,err_lambda1,err_lambda6,err_lambda7,"
               "res_Z345,res_Z7,g_phys_signed,res_g_stable,res_g_mass_formula,res_g_reconstructed_M2,"
               "positivity,unitarity,perturbativity,stability_alias,scalar_pass,"
               "unitarity_eigenmax,quartic_vertex_max,"
               "res_mh_indep,res_mphi_indep,res_alignment_indep,res_mA_indep,res_mHp_indep,"
               "numerical_status,precision_warning,accepted,rejection\n";

  std::string line;
  while (std::getline(std::cin, line)) {
    if (line.empty() || line[0] == '#') continue;
    std::string point_id;
    double mphi = 0.0, tb = 0.0, delta_g = 0.0, l1in = 0.0, mA = 300.0, mHp = 300.0;
    char comma;
    std::istringstream in(line);

    if (line.find(',') != std::string::npos) {
      std::string first_token;
      std::getline(in, first_token, ',');
      char* endptr = nullptr;
      double test_val = std::strtod(first_token.c_str(), &endptr);
      if (endptr && *endptr == '\0') {
        point_id = "pt";
        mphi = test_val;
        if (!(in >> tb >> comma >> delta_g >> comma >> l1in)) {
          std::cerr << "bad_input_row: " << line << '\n';
          continue;
        }
        if (in >> comma >> mA) {
          in >> comma >> mHp;
        }
      } else {
        point_id = first_token;
        if (!(in >> mphi >> comma >> tb >> comma >> delta_g >> comma >> l1in)) {
          std::cerr << "bad_input_row: " << line << '\n';
          continue;
        }
        if (in >> comma >> mA) {
          in >> comma >> mHp;
        }
      }
    } else {
      continue;
    }

    const double mh = 125.13;
    SM sm;
    THDM model;
    model.set_SM(sm);
    const double v = sm.get_v();

    // Direct formulation per instructions
    const double delta = 0.5 * v * delta_g;
    const double M2_in = mphi * mphi - delta;
    const double lambda6_in = tb * delta_g / (3.0 * v) + 2.0 / (3.0 * tb) * (mh * mh / (v * v) - l1in);

    const double beta = std::atan(tb);
    const double m12sq_in = M2_in * std::sin(beta) * std::cos(beta);

    const bool built = model.set_param_phys(mh, mphi, mA, mHp, 1.0, lambda6_in, 0.0, m12sq_in, tb);
    if (built) dihiggs::install_yukawa_type(model, 1);
    const int yukawa_installed = built ? model.get_yukawas_type() : 0;

    double l[7] = {};
    double m12r = std::numeric_limits<double>::quiet_NaN(), tbr = m12r;
    double mhr = m12r, mHr = m12r, mAr = m12r, mHpr = m12r, sbar = m12r, l6r = m12r, l7r = m12r;
    double unitarity = std::numeric_limits<double>::quiet_NaN(), qmax = unitarity;
    double c_re = unitarity, c_im = unitarity;
    double Z[7] = {unitarity, unitarity, unitarity, unitarity, unitarity, unitarity, unitarity};
    double massHp = unitarity;

    bool pos = false, unit = false, pert = false, stable = false, scalar_pass = false;
    bool accepted = false;
    std::string numerical_status = built ? "ok" : "construction";
    bool precision_warning = false;

    double err_mh = unitarity, err_mH = unitarity, err_mA = unitarity, err_mHp = unitarity;
    double err_sba = unitarity, err_tanb = unitarity, err_lambda1 = unitarity, err_lambda6 = unitarity, err_lambda7 = unitarity;
    double res_Z345 = unitarity, res_Z7 = unitarity;
    double res_mh_indep = unitarity, res_mphi_indep = unitarity, res_alignment_indep = unitarity;
    double res_mA_indep = unitarity, res_mHp_indep = unitarity;
    double g_phys_signed = unitarity, res_g_stable = unitarity, res_g_mass_formula = unitarity, res_g_reconstructed_M2 = unitarity;
    double M2_rec = unitarity;
    std::string rejection = built ? "unknown" : "construction";

    if (built) {
      model.get_param_gen(l[0], l[1], l[2], l[3], l[4], l[5], l[6], m12r, tbr);
      model.get_param_phys(mhr, mHr, mAr, mHpr, sbar, l6r, l7r, m12r, tbr);
      std::complex<double> c;
      model.get_coupling_hhh(1, 2, 2, c);
      c_re = c.real(); c_im = c.imag();
      g_phys_signed = -c_im;

      model.get_param_higgs(Z[0], Z[1], Z[2], Z[3], Z[4], Z[5], Z[6], massHp);

      // Independent generic-basis reconstruction. get_param_phys() reports cached
      // requested masses, so it cannot validate its own construction.
      const double s = std::sin(beta), cb = std::cos(beta), v2 = v * v;
      const double m11 = mA*mA*s*s + v2*(l[0]*cb*cb + l[4]*s*s + 2*l[5]*s*cb);
      const double m22 = mA*mA*cb*cb + v2*(l[1]*s*s + l[4]*cb*cb);
      const double m12off = -mA*mA*s*cb + v2*( (l[2]+l[3])*s*cb + l[5]*cb*cb );
      const double mvv = cb*cb*m11 + 2*s*cb*m12off + s*s*m22;
      const double mpp = s*s*m11 - 2*s*cb*m12off + cb*cb*m22;
      const double mvp = -s*cb*m11 + (cb*cb-s*s)*m12off + s*cb*m22;
      const double mh_ind = std::sqrt(std::max(0.0, mvv));
      const double mphi_ind = std::sqrt(std::max(0.0, mpp));
      const double mA2_ind = M2_in - 0.5*v2*(2*l[4] + l[5]/tb);
      const double mHp2_ind = M2_in - 0.5*v2*(l[3]+l[4]+l[5]/tb);
      if (mA2_ind >= 0.0) res_mA_indep = std::sqrt(mA2_ind) - mA;
      if (mHp2_ind >= 0.0) res_mHp_indep = std::sqrt(mHp2_ind) - mHp;
      res_mh_indep = mh_ind - mh;
      res_mphi_indep = mphi_ind - mphi;
      res_alignment_indep = mvp;

      // Reconstructed M2 from m12r and tbr
      if (tbr > 0.0) {
        M2_rec = m12r * (tbr + 1.0 / tbr);
      }

      // Check all finite
      bool all_finite = std::isfinite(g_phys_signed) && std::isfinite(mHr) && std::isfinite(M2_rec) &&
                        std::isfinite(mhr) && std::isfinite(mAr) && std::isfinite(mHpr) && std::isfinite(sbar) &&
                        std::isfinite(tbr) && std::isfinite(m12r) && std::isfinite(c_re) && std::isfinite(c_im) &&
                        std::isfinite(res_mh_indep) &&
                        std::isfinite(res_mphi_indep) && std::isfinite(res_alignment_indep) &&
                        std::isfinite(res_mA_indep) && std::isfinite(res_mHp_indep);
      for (double x : l) all_finite = all_finite && std::isfinite(x);
      for (double x : Z) all_finite = all_finite && std::isfinite(x);
      if (!all_finite) {
        numerical_status = "non_finite";
      }

      err_mh = mhr - mh;
      err_mH = mHr - mphi;
      err_mA = mAr - mA;
      err_mHp = mHpr - mHp;
      err_sba = sbar - 1.0;
      err_tanb = tbr - tb;
      err_lambda1 = l[0] - l1in;
      err_lambda6 = l6r - lambda6_in;
      err_lambda7 = l7r - 0.0;

      // Z345 residual: Z3+Z4+Z5 should equal mh^2/v^2 + delta_g/v
      res_Z345 = (Z[2] + Z[3] + Z[4]) - (mh * mh / (v * v) + delta_g / v);

      // Z7 analytic formula
      const double Z7_analytic = (mh * mh / (v * v) - l1in) / 3.0 * (1.0 / tb + 1.0 / (tb * tb * tb)) +
                                 delta / (3.0 * v * v) * (-2.0 * tb + 4.0 / tb);
      res_Z7 = Z[6] - Z7_analytic;

      // Coupling residuals
      const double g_expected_stable = mh * mh / v + delta_g;
      const double g_expected_mass = (mh * mh + 2.0 * mphi * mphi - 2.0 * M2_in) / v;
      const double g_expected_rec = (mhr * mhr + 2.0 * mHr * mHr - 2.0 * M2_rec) / v;

      res_g_stable = g_phys_signed - g_expected_stable;
      res_g_mass_formula = g_phys_signed - g_expected_mass;
      res_g_reconstructed_M2 = g_phys_signed - g_expected_rec;
      const double residuals[] = {err_mh, err_mH, err_mA, err_mHp, err_sba, err_tanb,
        err_lambda1, err_lambda6, err_lambda7, res_Z345, res_Z7, res_g_stable,
        res_g_mass_formula, res_g_reconstructed_M2, res_mh_indep, res_mphi_indep,
        res_alignment_indep, res_mA_indep, res_mHp_indep};
      for (double x : residuals) all_finite = all_finite && std::isfinite(x);
      if (!all_finite) numerical_status = "non_finite";

      // Scale-aware tolerances for precision
      const double tol_l1_warn = 1e-7 * std::max(1.0, std::abs(l1in));
      const double tol_l1_fail = 1e-4 * std::max(1.0, std::abs(l1in));
      const double tol_m_warn = 1e-6 * mphi;
      const double tol_m_fail = 1e-6 * mphi;

      if (std::abs(err_lambda1) > tol_l1_warn || std::abs(err_mH) > tol_m_warn || std::abs(err_sba) > 1e-7) {
        precision_warning = true;
      }
      if (std::abs(err_lambda1) > tol_l1_fail || std::abs(err_mH) > tol_m_fail || std::abs(err_sba) > 1e-7 ||
          std::abs(res_mh_indep) > 1e-6*mh || std::abs(res_mphi_indep) > 1e-6*mphi ||
          std::abs(res_alignment_indep) > 1e-6*v2 || std::abs(res_mA_indep) > 1e-6*mA ||
          std::abs(res_mHp_indep) > 1e-6*mHp || std::abs(res_Z345) > 1e-8 || std::abs(res_Z7) > 1e-8 ||
          std::abs(res_g_stable) > 1e-6*std::max(1.0, std::abs(g_phys_signed)) ||
          std::abs(res_g_mass_formula) > 1e-6*std::max(1.0, std::abs(g_phys_signed))) {
        numerical_status = "unresolved_precision";
      }

      // Constraints
      Constraints controls(model);
      pos = controls.check_positivity();
      unitarity = std::abs(model.calc_unitarity());
      unit = controls.check_unitarity(16.0 * M_PI);
      std::complex<double> q;
      int i, j, k, ll;
      model.calc_perturbativity(q, i, j, k, ll);
      qmax = std::abs(q);
      pert = controls.check_perturbativity(4.0 * M_PI);
      stable = controls.check_stability();
      scalar_pass = pos && unit && pert;

      if (numerical_status != "ok") {
        accepted = false;
        rejection = numerical_status;
      } else if (!built) {
        accepted = false;
        rejection = "construction";
      } else if (yukawa_installed != 1) {
        accepted = false;
        rejection = "yukawa_type";
      } else if (!scalar_pass) {
        accepted = false;
        if (!pos) rejection = "positivity";
        else if (!unit) rejection = "unitarity";
        else rejection = "quartic_perturbativity";
      } else {
        accepted = true;
        rejection = "accepted";
      }
    }

    std::cout << point_id << ','
              << std::setprecision(17) << mphi << ',' << tb << ',' << delta_g << ',' << l1in << ','
              << mA << ',' << mHp << ',' << M2_in << ',' << m12sq_in << ',' << lambda6_in;
    for (double x : l) std::cout << ',' << x;
    for (double x : Z) std::cout << ',' << x;
    std::cout << ',' << c_re << ',' << c_im << ',' << v << ','
              << sbar << ',' << tbr << ',' << mhr << ',' << mHr << ',' << mAr << ',' << mHpr << ','
              << m12r << ',' << M2_rec << ',' << yukawa_installed << ','
              << err_mh << ',' << err_mH << ',' << err_mA << ',' << err_mHp << ',' << err_sba << ',' << err_tanb << ','
              << err_lambda1 << ',' << err_lambda6 << ',' << err_lambda7 << ','
              << res_Z345 << ',' << res_Z7 << ','
              << g_phys_signed << ',' << res_g_stable << ',' << res_g_mass_formula << ',' << res_g_reconstructed_M2 << ','
              << (pos ? 1 : 0) << ',' << (unit ? 1 : 0) << ',' << (pert ? 1 : 0) << ',' << (stable ? 1 : 0) << ','
              << (scalar_pass ? 1 : 0) << ','
              << unitarity << ',' << qmax << ','
              << res_mh_indep << ',' << res_mphi_indep << ',' << res_alignment_indep << ','
              << res_mA_indep << ',' << res_mHp_indep << ','
              << numerical_status << ',' << (precision_warning ? 1 : 0) << ','
              << (accepted ? 1 : 0) << ',' << rejection << '\n';
  }
  return 0;
}
