#include "config.hpp"
#include "cgns_mesh.hpp"
#include "bvh.hpp"
#include "po.hpp"
#include "sbr.hpp"
#include "rcs.hpp"
#include <iostream>
#include <string>
#include <cstring>
#include <chrono>
#include <algorithm>
#include <vector>
#include <complex>

#if defined(USE_MPI) && USE_MPI
#include <mpi.h>
#endif

static void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " [options]\n"
              << "  --mesh <file>          CGNS mesh file (required)\n"
              << "  --freq <Hz>            Frequency (default: 10e9)\n"
              << "  --method <po|sbr|both> Scattering method (default: sbr)\n"
              << "  --bounces <N>          Max ray bounces (default: 3)\n"
              << "  --ray-density <N>      Rays per wavelength (default: 10)\n"
              << "  --theta-min <deg>      (default: 0)\n"
              << "  --theta-max <deg>      (default: 180)\n"
              << "  --theta-steps <N>      (default: 180)\n"
              << "  --phi-min <deg>        (default: 0)\n"
              << "  --phi-max <deg>        (default: 360)\n"
              << "  --phi-steps <N>        (default: 360)\n"
              << "  --bistatic             Enable bistatic mode (default: monostatic)\n"
              << "  --inc-theta <deg>      Incident direction theta (bistatic, default: 0)\n"
              << "  --inc-phi <deg>        Incident direction phi (bistatic, default: 0)\n"
              << "  --output <file>        Output CSV (default: rcs.csv)\n";
}

static Config parse_args(int argc, char** argv) {
    Config cfg;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        auto next = [&]() -> const char* {
            if (i + 1 < argc) return argv[++i];
            throw std::runtime_error("Missing value for " + arg);
        };
        if (arg == "--mesh") cfg.mesh_file = next();
        else if (arg == "--freq") cfg.frequency = std::stod(next());
        else if (arg == "--method") {
            std::string m = next();
            if (m == "po") cfg.method = Method::PO;
            else if (m == "sbr") cfg.method = Method::SBR;
            else if (m == "both") cfg.method = Method::BOTH;
        }
        else if (arg == "--bounces") cfg.max_bounces = std::stoi(next());
        else if (arg == "--ray-density") cfg.ray_density = std::stod(next());
        else if (arg == "--theta-min") cfg.theta_min = std::stod(next());
        else if (arg == "--theta-max") cfg.theta_max = std::stod(next());
        else if (arg == "--theta-steps") cfg.theta_steps = std::stoi(next());
        else if (arg == "--phi-min") cfg.phi_min = std::stod(next());
        else if (arg == "--phi-max") cfg.phi_max = std::stod(next());
        else if (arg == "--phi-steps") cfg.phi_steps = std::stoi(next());
        else if (arg == "--bistatic") cfg.bistatic = true;
        else if (arg == "--inc-theta") cfg.inc_theta = std::stod(next());
        else if (arg == "--inc-phi") cfg.inc_phi = std::stod(next());
        else if (arg == "--output") cfg.output_file = next();
        else if (arg == "--help") { print_usage(argv[0]); std::exit(0); }
    }
    if (cfg.mesh_file.empty()) {
        std::cerr << "Error: --mesh is required\n";
        print_usage(argv[0]);
        std::exit(1);
    }
    return cfg;
}

int main(int argc, char** argv) {
#if defined(USE_MPI) && USE_MPI
    MPI_Init(&argc, &argv);
#endif

    int rank = 0, world_size = 1;
#if defined(USE_MPI) && USE_MPI
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
#endif

    auto t0 = std::chrono::steady_clock::now();

    Config cfg = parse_args(argc, argv);

    Mesh mesh;
    if (rank == 0) {
        std::cout << "Loading mesh: " << cfg.mesh_file << "\n";
    }

    if (cfg.mesh_file.find(".obj") != std::string::npos) {
        mesh = load_obj_mesh(cfg.mesh_file);
    } else {
        mesh = load_cgns_mesh(cfg.mesh_file);
    }
    
    if (rank == 0) {
        std::cout << "  Triangles: " << mesh.triangles.size() << "\n";
        std::cout << "Building BVH...\n";
    }

    BVH bvh;
    bvh.build(mesh.triangles);
    
    if (rank == 0) {
        std::cout << "  BVH nodes: " << bvh.nodes().size() << "\n";
    }

    int n_obs = cfg.theta_steps * cfg.phi_steps;
    std::vector<double> theta_vals(n_obs), phi_vals(n_obs);
    for (int i = 0; i < n_obs; ++i) {
        int ti = i / cfg.phi_steps;
        int pi = i % cfg.phi_steps;
        theta_vals[i] = cfg.theta_min + ti * (cfg.theta_max - cfg.theta_min) / std::max(cfg.theta_steps - 1, 1);
        phi_vals[i] = cfg.phi_min + pi * (cfg.phi_max - cfg.phi_min) / std::max(cfg.phi_steps - 1, 1);
    }

    std::vector<std::complex<double>> global_vv(n_obs, 0), global_hh(n_obs, 0);

    if (cfg.method == Method::PO || cfg.method == Method::BOTH) {
        if (rank == 0) std::cout << "Computing PO scattering...\n";
        
        Vec3 inc_dir;
        if (cfg.bistatic) {
            double th = cfg.inc_theta * M_PI / 180.0;
            double ph = cfg.inc_phi * M_PI / 180.0;
            inc_dir = {std::sin(th)*std::cos(ph), std::sin(th)*std::sin(ph), std::cos(th)};
        } else {
            inc_dir = {0.0, 0.0, -1.0};
        }

        for (int oi = 0; oi < n_obs; ++oi) {
            double th = theta_vals[oi] * M_PI / 180.0;
            double ph = phi_vals[oi] * M_PI / 180.0;
            Vec3 obs_dir{std::sin(th)*std::cos(ph), std::sin(th)*std::sin(ph), std::cos(th)};

            if (!cfg.bistatic) {
                inc_dir = -obs_dir;
            }

            POField field = compute_po_scattering(bvh, cfg, inc_dir, obs_dir);
            global_vv[oi] = field.E_theta;
            global_hh[oi] = field.E_phi;
        }
    }

    if (cfg.method == Method::SBR || cfg.method == Method::BOTH) {
        if (rank == 0) std::cout << "Computing SBR scattering...\n";
        
        SBRResult sbr = compute_sbr_scattering(mesh, bvh, cfg, rank, world_size);

        for (size_t i = 0; i < sbr.field_vv.size(); ++i) {
            int global_oi = (int)sbr.theta_vals[i] / cfg.phi_steps;
            global_vv[global_oi] += sbr.field_vv[i];
            global_hh[global_oi] += sbr.field_hh[i];
        }
    }

    if (rank == 0) {
        auto t1 = std::chrono::steady_clock::now();
        double elapsed = std::chrono::duration<double>(t1 - t0).count();
        std::cout << "Computation complete in " << elapsed << "s\n";
        std::cout << "Computing RCS...\n";

        RCSResult rcs = compute_rcs(cfg, global_vv, global_hh, theta_vals, phi_vals);
        write_rcs_csv(cfg.output_file, rcs);
        std::cout << "Output written to " << cfg.output_file << "\n";
    }

#if defined(USE_MPI) && USE_MPI
    MPI_Finalize();
#endif
    return 0;
}
