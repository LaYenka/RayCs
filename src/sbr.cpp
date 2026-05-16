#include "sbr.hpp"
#include <cmath>
#include <complex>
#include <algorithm>

static const double C0 = 299792458.0;

SBRResult compute_sbr_scattering(const Mesh& mesh, const BVH& bvh,
                                  const Config& cfg, int rank, int world_size) {
    double lambda = C0 / cfg.frequency;
    double k = 2.0 * M_PI / lambda;
    double spacing = lambda / cfg.ray_density;

    AABB bounds = mesh.bounds;
    Vec3 center = bounds.center();
    double extent_x = (bounds.max_pt.x - bounds.min_pt.x) * 0.5 + spacing;
    double extent_y = (bounds.max_pt.y - bounds.min_pt.y) * 0.5 + spacing;
    double extent_z = (bounds.max_pt.z - bounds.min_pt.z) * 0.5 + spacing;
    double max_extent = std::max({extent_x, extent_y, extent_z});

    int n_rays_x = std::max((int)std::ceil(2.0 * max_extent / spacing), 1);
    int n_rays_y = std::max((int)std::ceil(2.0 * max_extent / spacing), 1);
    int total_rays = n_rays_x * n_rays_y;

    int n_obs = cfg.theta_steps * cfg.phi_steps;
    int obs_per_rank = (n_obs + world_size - 1) / world_size;
    int obs_start = rank * obs_per_rank;
    int obs_end = std::min(obs_start + obs_per_rank, n_obs);
    int local_obs = std::max(obs_end - obs_start, 0);

    std::vector<double> theta_vals(local_obs), phi_vals(local_obs);
    for (int oi = 0; oi < local_obs; ++oi) {
        int global_oi = obs_start + oi;
        int ti = global_oi / cfg.phi_steps;
        int pi = global_oi % cfg.phi_steps;
        theta_vals[oi] = cfg.theta_min + ti * (cfg.theta_max - cfg.theta_min) / std::max(cfg.theta_steps - 1, 1);
        phi_vals[oi] = cfg.phi_min + pi * (cfg.phi_max - cfg.phi_min) / std::max(cfg.phi_steps - 1, 1);
    }

    std::vector<std::complex<double>> field_vv(local_obs, 0.0);
    std::vector<std::complex<double>> field_hh(local_obs, 0.0);

    double prefactor = k * 100.0;

    #pragma omp parallel for schedule(dynamic, 1)
    for (int oi = 0; oi < local_obs; ++oi) {
        double th = theta_vals[oi] * M_PI / 180.0;
        double ph = phi_vals[oi] * M_PI / 180.0;
        Vec3 obs_dir{std::sin(th)*std::cos(ph), std::sin(th)*std::sin(ph), std::cos(th)};

        Vec3 inc_dir = -obs_dir;
        Vec3 up = std::abs(inc_dir.dot(Vec3{0,0,1})) > 0.99 ? Vec3{1,0,0} : Vec3{0,0,1};
        Vec3 ux = inc_dir.cross(up).normalized();
        Vec3 uy = inc_dir.cross(ux).normalized();
        Vec3 launch_center = center - inc_dir * (max_extent + 2.0 * spacing);

        double E_theta_real = 0.0, E_theta_imag = 0.0;
        double E_phi_real = 0.0, E_phi_imag = 0.0;

        for (int ri = 0; ri < total_rays; ++ri) {
            int ix = ri % n_rays_x;
            int iy = ri / n_rays_x;
            double sx = (ix + 0.5) * spacing - max_extent;
            double sy = (iy + 0.5) * spacing - max_extent;

            Vec3 ray_origin = launch_center + ux * sx + uy * sy;
            HitRecord hit = bvh.closest_hit(ray_origin, inc_dir);
            if (!hit.hit) continue;

            const Triangle& tri = bvh.triangles()[hit.tri_index];
            double cos_inc = std::abs(tri.normal.dot(-inc_dir));
            if (cos_inc <= 0.0) continue;

            Vec3 hit_pos = ray_origin + inc_dir * hit.t;
            
            double phase = k * hit_pos.dot(obs_dir);
            double cos_theta = std::acos(std::clamp(obs_dir.z, -1.0, 1.0));
            double phi = std::atan2(obs_dir.y, obs_dir.x);
            Vec3 e_theta{std::cos(cos_theta)*std::cos(phi), std::cos(cos_theta)*std::sin(phi), -std::sin(cos_theta)};
            Vec3 e_phi{-std::sin(phi), std::cos(phi), 0.0};

            Vec3 J = tri.normal.cross(-inc_dir) * 2.0 * cos_inc * tri.area;
            double J_theta = J.dot(e_theta);
            double J_phi = J.dot(e_phi);

            E_theta_real += J_theta * std::cos(phase);
            E_theta_imag += J_theta * std::sin(phase);
            E_phi_real += J_phi * std::cos(phase);
            E_phi_imag += J_phi * std::sin(phase);
        }

        double scale = prefactor * 0.01;
        field_vv[oi] = std::complex<double>(E_theta_real * scale, E_theta_imag * scale);
        field_hh[oi] = std::complex<double>(E_phi_real * scale * 0.5, E_phi_imag * scale * 0.5);
    }

    SBRResult result;
    result.theta_vals = theta_vals;
    result.phi_vals = phi_vals;
    result.field_vv = field_vv;
    result.field_hh = field_hh;

    return result;
}