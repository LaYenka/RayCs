#include "rcs.hpp"
#include <cmath>
#include <fstream>
#include <iostream>
#include <algorithm>

RCSResult compute_rcs(const Config& cfg,
                      const std::vector<std::complex<double>>& field_vv,
                      const std::vector<std::complex<double>>& field_hh,
                      const std::vector<double>& theta_vals,
                      const std::vector<double>& phi_vals) {
    double lambda = 299792458.0 / cfg.frequency;
    double k = 2.0 * M_PI / lambda;
    size_t n = field_vv.size();

    RCSResult result;
    result.theta_vals = theta_vals;
    result.phi_vals = phi_vals;
    result.rcs_total_db.resize(n);
    result.rcs_vv_db.resize(n);
    result.rcs_hh_db.resize(n);

    for (size_t i = 0; i < n; ++i) {
        double sigma_vv = 4.0 * M_PI * std::norm(field_vv[i]) / (k * k);
        double sigma_hh = 4.0 * M_PI * std::norm(field_hh[i]) / (k * k);
        double sigma_total = sigma_vv + sigma_hh;

        result.rcs_vv_db[i] = 10.0 * std::log10(std::max(sigma_vv, 1e-30));
        result.rcs_hh_db[i] = 10.0 * std::log10(std::max(sigma_hh, 1e-30));
        result.rcs_total_db[i] = 10.0 * std::log10(std::max(sigma_total, 1e-30));
    }

    return result;
}

void write_rcs_csv(const std::string& filename, const RCSResult& result) {
    std::ofstream out(filename);
    if (!out.is_open()) {
        std::cerr << "Error: cannot open output file " << filename << "\n";
        return;
    }
    out << "theta_deg,phi_deg,RCS_total_dBsm,RCS_VV_dBsm,RCS_HH_dBsm\n";
    for (size_t i = 0; i < result.theta_vals.size(); ++i) {
        out << result.theta_vals[i] << ","
            << result.phi_vals[i] << ","
            << result.rcs_total_db[i] << ","
            << result.rcs_vv_db[i] << ","
            << result.rcs_hh_db[i] << "\n";
    }
    out.close();
}
