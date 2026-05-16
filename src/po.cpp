#include "po.hpp"
#include <cmath>
#include <complex>

static const double MU0 = 4.0 * M_PI * 1e-7;
static const double EPS0 = 8.854187817e-12;
static const double ETA0 = std::sqrt(MU0 / EPS0);
static const double C0 = 299792458.0;

POField compute_po_scattering(const BVH& bvh,
                               const Config& cfg,
                               const Vec3& inc_dir,
                               const Vec3& obs_dir) {
    double k = 2.0 * M_PI * cfg.frequency / C0;

    Vec3 E_inc{1.0, 0.0, 0.0};
    Vec3 H_inc = inc_dir.cross(E_inc) / ETA0;

    double E_theta_real = 0.0, E_theta_imag = 0.0;
    double E_phi_real = 0.0, E_phi_imag = 0.0;

    #pragma omp parallel for reduction(+:E_theta_real, E_theta_imag, E_phi_real, E_phi_imag)
    for (int i = 0; i < (int)bvh.triangles().size(); ++i) {
        const Triangle& tri = bvh.triangles()[i];

        double n_dot_inc = -tri.normal.dot(inc_dir);
        if (n_dot_inc <= 0.0) continue;

        Vec3 J_s = (tri.normal.cross(H_inc) * 2.0) * tri.area;

        double theta = std::acos(std::clamp(obs_dir.z, -1.0, 1.0));
        double phi = std::atan2(obs_dir.y, obs_dir.x);
        
        Vec3 e_theta{std::cos(theta)*std::cos(phi), std::cos(theta)*std::sin(phi), -std::sin(theta)};
        Vec3 e_phi{-std::sin(phi), std::cos(phi), 0.0};

        double phase = k * obs_dir.dot(tri.centroid);
        std::complex<double> exp_jp(std::cos(phase), std::sin(phase));

        std::complex<double> j_theta(
            J_s.x * e_theta.x + J_s.y * e_theta.y + J_s.z * e_theta.z, 0.0);
        std::complex<double> j_phi(
            J_s.x * e_phi.x + J_s.y * e_phi.y + J_s.z * e_phi.z, 0.0);

        std::complex<double> proj_theta = j_theta * exp_jp;
        std::complex<double> proj_phi = j_phi * exp_jp;

        E_theta_real += proj_theta.real();
        E_theta_imag += proj_theta.imag();
        E_phi_real += proj_phi.real();
        E_phi_imag += proj_phi.imag();
    }

    std::complex<double> E_theta(E_theta_real, E_theta_imag);
    std::complex<double> E_phi(E_phi_real, E_phi_imag);
    
    double prefactor = k * 10000.0 / (4.0 * M_PI);
    E_theta *= std::complex<double>(0, prefactor);
    E_phi *= std::complex<double>(0, prefactor);

    return {E_theta, E_phi};
}
