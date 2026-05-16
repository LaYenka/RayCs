#pragma once
#include "mesh.hpp"
#include "bvh.hpp"
#include "vec3.hpp"
#include "config.hpp"
#include <complex>

struct POField {
    std::complex<double> E_theta;
    std::complex<double> E_phi;
};

POField compute_po_scattering(const BVH& bvh,
                               const Config& cfg,
                               const Vec3& inc_dir,
                               const Vec3& obs_dir);
