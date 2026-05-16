#pragma once
#include "mesh.hpp"
#include "bvh.hpp"
#include "config.hpp"
#include "vec3.hpp"
#include <vector>
#include <complex>

struct SBRResult {
    std::vector<double> theta_vals;
    std::vector<double> phi_vals;
    std::vector<std::complex<double>> field_vv;
    std::vector<std::complex<double>> field_hh;
};

SBRResult compute_sbr_scattering(const Mesh& mesh, const BVH& bvh,
                                  const Config& cfg, int rank, int world_size);
