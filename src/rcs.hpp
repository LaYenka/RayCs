#pragma once
#include "config.hpp"
#include <string>
#include <vector>
#include <complex>

struct RCSResult {
    std::vector<double> theta_vals;
    std::vector<double> phi_vals;
    std::vector<double> rcs_total_db;
    std::vector<double> rcs_vv_db;
    std::vector<double> rcs_hh_db;
};

RCSResult compute_rcs(const Config& cfg,
                      const std::vector<std::complex<double>>& field_vv,
                      const std::vector<std::complex<double>>& field_hh,
                      const std::vector<double>& theta_vals,
                      const std::vector<double>& phi_vals);

void write_rcs_csv(const std::string& filename, const RCSResult& result);
