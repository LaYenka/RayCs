#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/operators.h>

#include "config.hpp"
#include "cgns_mesh.hpp"
#include "bvh.hpp"
#include "po.hpp"
#include "sbr.hpp"
#include "rcs.hpp"
#include "vec3.hpp"
#include "mat3.hpp"
#include "mesh.hpp"
#include "ray.hpp"

#include <iostream>
#include <string>
#include <vector>
#include <complex>
#include <cmath>
#include <chrono>
#include <algorithm>

#if defined(USE_MPI) && USE_MPI
#include <mpi.h>
#endif

namespace py = pybind11;
using namespace py::literals;

static const double C0 = 299792458.0;

// ─── Progress helper ──────────────────────────────────────────────────
static void print_progress(int current, int total, const std::string& label) {
    if (total <= 0) return;
    int pct = (current * 100) / total;
    int bars = (current * 20) / total;
    std::string bar = std::string(bars, '|') + std::string(20 - bars, '.');
    std::fprintf(stderr, "\r%s: %3d%% [%s] (%d/%d angles)",
                 label.c_str(), pct, bar.c_str(), current, total);
    if (current == total) std::fprintf(stderr, "\n");
    std::fflush(stderr);
}

// ─── Angle grid helper ───────────────────────────────────────────────
static void make_angle_grid(const Config& cfg,
                            std::vector<double>& theta_vals,
                            std::vector<double>& phi_vals) {
    int n_obs = cfg.theta_steps * cfg.phi_steps;
    theta_vals.resize(n_obs);
    phi_vals.resize(n_obs);
    for (int i = 0; i < n_obs; ++i) {
        int ti = i / cfg.phi_steps;
        int pi = i % cfg.phi_steps;
        theta_vals[i] = cfg.theta_min + ti * (cfg.theta_max - cfg.theta_min)
                            / std::max(cfg.theta_steps - 1, 1);
        phi_vals[i] = cfg.phi_min + pi * (cfg.phi_max - cfg.phi_min)
                          / std::max(cfg.phi_steps - 1, 1);
    }
}

// ─── MPI complex type ────────────────────────────────────────────────
#if defined(USE_MPI) && USE_MPI
static MPI_Datatype mpi_complex_double() {
    static MPI_Datatype type = MPI_DATATYPE_NULL;
    if (type == MPI_DATATYPE_NULL) {
        MPI_Type_contiguous(2, MPI_DOUBLE, &type);
        MPI_Type_commit(&type);
    }
    return type;
}
#endif

// ─── MPI gather helper for complex vectors ────────────────────────────
#if defined(USE_MPI) && USE_MPI
static std::vector<std::complex<double>> mpi_gather_complex(
    const std::vector<std::complex<double>>& local, int rank, int world_size) {
    int local_n = (int)local.size();
    std::vector<int> counts(world_size), displs(world_size);
    MPI_Gather(&local_n, 1, MPI_INT, counts.data(), 1, MPI_INT, 0, MPI_COMM_WORLD);

    std::vector<std::complex<double>> gathered;
    if (rank == 0) {
        int total = 0;
        for (int i = 0; i < world_size; ++i) {
            displs[i] = total;
            total += counts[i];
        }
        gathered.resize(total);
    }
    MPI_Gatherv(local.data(), local_n, mpi_complex_double(),
                gathered.data(), counts.data(), displs.data(),
                mpi_complex_double(), 0, MPI_COMM_WORLD);
    return gathered;
}
#endif

// ─── PO sweep (full angle grid, MPI-distributed) ─────────────────────
static RCSResult compute_po_sweep(const BVH& bvh, const Config& cfg) {
    int rank = 0, world_size = 1;
#if defined(USE_MPI) && USE_MPI
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
#endif

    std::vector<double> theta_vals, phi_vals;
    make_angle_grid(cfg, theta_vals, phi_vals);
    int n_obs = (int)theta_vals.size();

    // Distribute across ranks
    int obs_per_rank = (n_obs + world_size - 1) / world_size;
    int local_start = rank * obs_per_rank;
    int local_end = std::min(local_start + obs_per_rank, n_obs);
    int local_obs = std::max(local_end - local_start, 0);

    // Incident direction
    Vec3 inc_dir{0, 0, -1};
    if (cfg.bistatic) {
        double th = cfg.inc_theta * M_PI / 180.0;
        double ph = cfg.inc_phi * M_PI / 180.0;
        inc_dir = {std::sin(th) * std::cos(ph),
                   std::sin(th) * std::sin(ph),
                   std::cos(th)};
    }

    std::vector<std::complex<double>> local_vv(local_obs);
    std::vector<std::complex<double>> local_hh(local_obs);

    int progress_next = 0;
    for (int oi = 0; oi < local_obs; ++oi) {
        int global_oi = local_start + oi;
        double th = theta_vals[global_oi] * M_PI / 180.0;
        double ph = phi_vals[global_oi] * M_PI / 180.0;
        Vec3 obs_dir{std::sin(th) * std::cos(ph),
                     std::sin(th) * std::sin(ph),
                     std::cos(th)};

        Vec3 inc = cfg.bistatic ? inc_dir : -obs_dir;
        POField field = compute_po_scattering(bvh, cfg, inc, obs_dir);
        local_vv[oi] = field.E_theta;
        local_hh[oi] = field.E_phi;

        if (cfg.verbose && rank == 0 && local_obs >= 20) {
            int pct = (oi + 1) * 100 / local_obs;
            if (pct >= progress_next) {
                print_progress(oi + 1, local_obs, "PO sweep");
                progress_next = pct + 5;
            }
        }
    }

    // Gather to rank 0
    std::vector<std::complex<double>> global_vv, global_hh;
#if defined(USE_MPI) && USE_MPI
    global_vv = mpi_gather_complex(local_vv, rank, world_size);
    global_hh = mpi_gather_complex(local_hh, rank, world_size);
#else
    global_vv = std::move(local_vv);
    global_hh = std::move(local_hh);
#endif

    if (cfg.verbose && rank == 0)
        std::fprintf(stderr, "\n");

    if (rank == 0) {
        return compute_rcs(cfg, global_vv, global_hh, theta_vals, phi_vals);
    }
    return RCSResult{};
}

// ─── SBR sweep ───────────────────────────────────────────────────────
static RCSResult compute_sbr_sweep(const Mesh& mesh, const BVH& bvh, const Config& cfg) {
    int rank = 0, world_size = 1;
#if defined(USE_MPI) && USE_MPI
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
#endif

    if (cfg.verbose && rank == 0)
        std::fprintf(stderr, "Computing SBR scattering...\n");

    SBRResult sbr = compute_sbr_scattering(mesh, bvh, cfg, rank, world_size);

    // Place local results into full-size arrays by computing global indices
    int n_obs = cfg.theta_steps * cfg.phi_steps;
    std::vector<double> theta_vals(n_obs), phi_vals(n_obs);
    make_angle_grid(cfg, theta_vals, phi_vals);

    std::vector<std::complex<double>> global_vv, global_hh;
#if defined(USE_MPI) && USE_MPI
    global_vv = mpi_gather_complex(sbr.field_vv, rank, world_size);
    global_hh = mpi_gather_complex(sbr.field_hh, rank, world_size);
#else
    global_vv = sbr.field_vv;
    global_hh = sbr.field_hh;
#endif

    if (rank == 0) {
        return compute_rcs(cfg, global_vv, global_hh, theta_vals, phi_vals);
    }
    return RCSResult{};
}

// ─── BOTH sweep ──────────────────────────────────────────────────────
static RCSResult compute_both_sweep(const Mesh& mesh, const BVH& bvh, const Config& cfg) {
    int rank = 0, world_size = 1;
#if defined(USE_MPI) && USE_MPI
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
#endif

    std::vector<double> theta_vals, phi_vals;
    make_angle_grid(cfg, theta_vals, phi_vals);
    int n_obs = (int)theta_vals.size();

    // --- PO part ---
    int obs_per_rank = (n_obs + world_size - 1) / world_size;
    int local_start = rank * obs_per_rank;
    int local_end = std::min(local_start + obs_per_rank, n_obs);
    int local_obs = std::max(local_end - local_start, 0);

    Vec3 inc_dir{0, 0, -1};
    if (cfg.bistatic) {
        double th = cfg.inc_theta * M_PI / 180.0;
        double ph = cfg.inc_phi * M_PI / 180.0;
        inc_dir = {std::sin(th) * std::cos(ph),
                   std::sin(th) * std::sin(ph),
                   std::cos(th)};
    }

    std::vector<std::complex<double>> local_vv(local_obs, 0);
    std::vector<std::complex<double>> local_hh(local_obs, 0);

    if (cfg.verbose && rank == 0)
        std::fprintf(stderr, "Computing PO scattering...\n");

    int progress_next = 0;
    for (int oi = 0; oi < local_obs; ++oi) {
        int global_oi = local_start + oi;
        double th = theta_vals[global_oi] * M_PI / 180.0;
        double ph = phi_vals[global_oi] * M_PI / 180.0;
        Vec3 obs_dir{std::sin(th) * std::cos(ph),
                     std::sin(th) * std::sin(ph),
                     std::cos(th)};
        Vec3 inc = cfg.bistatic ? inc_dir : -obs_dir;
        POField field = compute_po_scattering(bvh, cfg, inc, obs_dir);
        local_vv[oi] = field.E_theta;
        local_hh[oi] = field.E_phi;

        if (cfg.verbose && rank == 0 && local_obs >= 20) {
            int pct = (oi + 1) * 100 / local_obs;
            if (pct >= progress_next) {
                print_progress(oi + 1, local_obs, "PO sweep");
                progress_next = pct + 5;
            }
        }
    }

    // --- SBR part ---
    if (cfg.verbose && rank == 0) {
        if (local_obs >= 20) std::fprintf(stderr, "\n");
        std::fprintf(stderr, "Computing SBR scattering...\n");
    }

    SBRResult sbr = compute_sbr_scattering(mesh, bvh, cfg, rank, world_size);

    // Merge SBR fields into local arrays
    for (size_t i = 0; i < sbr.field_vv.size(); ++i) {
        local_vv[i] += sbr.field_vv[i];
        local_hh[i] += sbr.field_hh[i];
    }

    // Gather to rank 0
    std::vector<std::complex<double>> global_vv, global_hh;
#if defined(USE_MPI) && USE_MPI
    global_vv = mpi_gather_complex(local_vv, rank, world_size);
    global_hh = mpi_gather_complex(local_hh, rank, world_size);
#else
    global_vv = std::move(local_vv);
    global_hh = std::move(local_hh);
#endif

    if (rank == 0) {
        return compute_rcs(cfg, global_vv, global_hh, theta_vals, phi_vals);
    }
    return RCSResult{};
}

// ─── MPI helper functions ────────────────────────────────────────────
static int mpi_rank() {
#if defined(USE_MPI) && USE_MPI
    int r;
    MPI_Comm_rank(MPI_COMM_WORLD, &r);
    return r;
#else
    return 0;
#endif
}

static int mpi_size() {
#if defined(USE_MPI) && USE_MPI
    int s;
    MPI_Comm_size(MPI_COMM_WORLD, &s);
    return s;
#else
    return 1;
#endif
}

// ─── Pybind11 module ─────────────────────────────────────────────────
PYBIND11_MODULE(_core, m) {
    m.doc() = "RayCs C++ core: RCS computation using PO and SBR";

    // Initialize MPI if available
#if defined(USE_MPI) && USE_MPI
    int initialized;
    MPI_Initialized(&initialized);
    if (!initialized) {
        MPI_Init(nullptr, nullptr);
    }
#endif

    // ── Enum: Method ─────────────────────────────────────────────
    py::enum_<Method>(m, "Method")
        .value("PO", Method::PO)
        .value("SBR", Method::SBR)
        .value("BOTH", Method::BOTH)
        .export_values();

    // ── Struct: Config ───────────────────────────────────────────
    py::class_<Config>(m, "Config")
        .def(py::init<>())
        .def_readwrite("mesh_file", &Config::mesh_file)
        .def_readwrite("output_file", &Config::output_file)
        .def_readwrite("frequency", &Config::frequency)
        .def_readwrite("max_bounces", &Config::max_bounces)
        .def_readwrite("ray_density", &Config::ray_density)
        .def_readwrite("theta_min", &Config::theta_min)
        .def_readwrite("theta_max", &Config::theta_max)
        .def_readwrite("theta_steps", &Config::theta_steps)
        .def_readwrite("phi_min", &Config::phi_min)
        .def_readwrite("phi_max", &Config::phi_max)
        .def_readwrite("phi_steps", &Config::phi_steps)
        .def_readwrite("method", &Config::method)
        .def_readwrite("bistatic", &Config::bistatic)
        .def_readwrite("inc_theta", &Config::inc_theta)
        .def_readwrite("inc_phi", &Config::inc_phi)
        .def_readwrite("verbose", &Config::verbose);

    // ── Struct: Vec3 ─────────────────────────────────────────────
    py::class_<Vec3>(m, "Vec3")
        .def(py::init<>())
        .def(py::init<double, double, double>())
        .def_readwrite("x", &Vec3::x)
        .def_readwrite("y", &Vec3::y)
        .def_readwrite("z", &Vec3::z)
        .def(py::self + py::self)
        .def(py::self - py::self)
        .def(py::self * double())
        .def(py::self / double())
        .def(-py::self)
        .def("__getitem__", [](const Vec3& v, int i) { return v[i]; })
        .def("__setitem__", [](Vec3& v, int i, double val) { v[i] = val; })
        .def("dot", &Vec3::dot)
        .def("cross", &Vec3::cross)
        .def("norm", &Vec3::norm)
        .def("norm_sq", &Vec3::norm_sq)
        .def("normalized", &Vec3::normalized)
        .def("reflect", &Vec3::reflect)
        .def("__repr__", [](const Vec3& v) {
            return "Vec3(" + std::to_string(v.x) + ", "
                         + std::to_string(v.y) + ", "
                         + std::to_string(v.z) + ")";
        });

    m.def("dot", py::overload_cast<const Vec3&, const Vec3&>(&dot));
    m.def("cross", py::overload_cast<const Vec3&, const Vec3&>(&cross));

    // ── Struct: CVec3 ────────────────────────────────────────────
    py::class_<CVec3>(m, "CVec3")
        .def(py::init<>())
        .def(py::init<std::complex<double>, std::complex<double>, std::complex<double>>())
        .def_readwrite("x", &CVec3::x)
        .def_readwrite("y", &CVec3::y)
        .def_readwrite("z", &CVec3::z)
        .def(py::self + py::self)
        .def(py::self - py::self)
        .def(py::self * std::complex<double>())
        .def(py::self * double())
        .def(py::self / double())
        .def("mag_sq", &CVec3::mag_sq);

    // ── Struct: Mat3 ─────────────────────────────────────────────
    py::class_<Mat3>(m, "Mat3")
        .def(py::init<>())
        .def_static("identity", &Mat3::identity)
        .def_static("rotation", [](const Vec3& axis, double angle) {
            return Mat3::rotation(axis, angle);
        })
        .def("mul", &Mat3::mul);

    // ── Struct: Triangle ─────────────────────────────────────────
    py::class_<Triangle>(m, "Triangle")
        .def(py::init<>())
        .def_readonly("v0", &Triangle::v0)
        .def_readonly("v1", &Triangle::v1)
        .def_readonly("v2", &Triangle::v2)
        .def_readonly("normal", &Triangle::normal)
        .def_readonly("centroid", &Triangle::centroid)
        .def_readonly("area", &Triangle::area)
        .def_readonly("global_index", &Triangle::global_index);

    // ── Struct: AABB ─────────────────────────────────────────────
    py::class_<AABB>(m, "AABB")
        .def(py::init<>())
        .def(py::init<Vec3, Vec3>())
        .def_readwrite("min_pt", &AABB::min_pt)
        .def_readwrite("max_pt", &AABB::max_pt)
        .def("expand", py::overload_cast<const Vec3&>(&AABB::expand))
        .def("expand", py::overload_cast<const AABB&>(&AABB::expand))
        .def("surface_area", &AABB::surface_area)
        .def("center", &AABB::center)
        .def("intersects_ray", &AABB::intersects_ray)
        .def("intersects_ray_maxt", &AABB::intersects_ray_maxt);

    // ── Struct: Mesh ─────────────────────────────────────────────
    py::class_<Mesh>(m, "Mesh")
        .def(py::init<>())
        .def_readonly("triangles", &Mesh::triangles)
        .def_readonly("bounds", &Mesh::bounds)
        .def("compute_bounds", &Mesh::compute_bounds);

    // ── Struct: Ray ──────────────────────────────────────────────
    py::class_<Ray>(m, "Ray")
        .def(py::init<>())
        .def_readwrite("origin", &Ray::origin)
        .def_readwrite("direction", &Ray::direction)
        .def_readwrite("E_field", &Ray::E_field)
        .def_readwrite("phase", &Ray::phase)
        .def_readwrite("bounce_count", &Ray::bounce_count)
        .def_readwrite("active", &Ray::active);

    // ── Struct: HitRecord ────────────────────────────────────────
    py::class_<HitRecord>(m, "HitRecord")
        .def(py::init<>())
        .def_readonly("t", &HitRecord::t)
        .def_readonly("u", &HitRecord::u)
        .def_readonly("v", &HitRecord::v)
        .def_readonly("tri_index", &HitRecord::tri_index)
        .def_readonly("hit", &HitRecord::hit);

    // ── Struct: BVHNode ──────────────────────────────────────────
    py::class_<BVHNode>(m, "BVHNode")
        .def(py::init<>())
        .def_readonly("bounds", &BVHNode::bounds)
        .def("is_leaf", &BVHNode::is_leaf);

    // ── Class: BVH ───────────────────────────────────────────────
    py::class_<BVH>(m, "BVH")
        .def(py::init<>())
        .def("build", [](BVH& bvh, std::vector<Triangle>& tris, int max_leaf) {
            bvh.build(tris, max_leaf);
        }, py::arg("triangles"), py::arg("max_leaf") = 4)
        .def("closest_hit", &BVH::closest_hit)
        .def("any_hit", &BVH::any_hit)
        .def("nodes", &BVH::nodes, py::return_value_policy::reference_internal)
        .def("triangles", &BVH::triangles, py::return_value_policy::reference_internal);

    // ── Struct: POField ──────────────────────────────────────────
    py::class_<POField>(m, "POField")
        .def(py::init<>())
        .def_readwrite("E_theta", &POField::E_theta)
        .def_readwrite("E_phi", &POField::E_phi);

    // ── Struct: RCSResult ────────────────────────────────────────
    py::class_<RCSResult>(m, "RCSResult")
        .def(py::init<>())
        .def_readwrite("theta_vals", &RCSResult::theta_vals)
        .def_readwrite("phi_vals", &RCSResult::phi_vals)
        .def_readwrite("rcs_total_db", &RCSResult::rcs_total_db)
        .def_readwrite("rcs_vv_db", &RCSResult::rcs_vv_db)
        .def_readwrite("rcs_hh_db", &RCSResult::rcs_hh_db);

    // ── Free functions ───────────────────────────────────────────
    m.def("load_obj_mesh", &load_obj_mesh, "Load Wavefront OBJ mesh",
          py::arg("filename"));

    m.def("load_cgns_mesh", &load_cgns_mesh, "Load CGNS mesh",
          py::arg("filename"));

    m.def("compute_po_scattering", &compute_po_scattering,
          "Compute PO scattering for a single (incident, observation) pair",
          py::arg("bvh"), py::arg("cfg"),
          py::arg("inc_dir"), py::arg("obs_dir"));

    m.def("compute_rcs", &compute_rcs,
          "Convert scattered fields to RCS in dBsm",
          py::arg("cfg"), py::arg("field_vv"), py::arg("field_hh"),
          py::arg("theta_vals"), py::arg("phi_vals"));

    m.def("write_rcs_csv", &write_rcs_csv,
          "Write RCS results to CSV file",
          py::arg("filename"), py::arg("result"));

    // ── Sweep functions ──────────────────────────────────────────
    m.def("compute_po_sweep", &compute_po_sweep,
          "Compute PO over the full angle grid (MPI-distributed)",
          py::arg("bvh"), py::arg("cfg"));

    m.def("compute_sbr_sweep", &compute_sbr_sweep,
          "Compute SBR over the full angle grid (MPI-distributed)",
          py::arg("mesh"), py::arg("bvh"), py::arg("cfg"));

    m.def("compute_both_sweep", &compute_both_sweep,
          "Compute PO+SBR over the full angle grid (MPI-distributed)",
          py::arg("mesh"), py::arg("bvh"), py::arg("cfg"));

    // ── MPI helpers ──────────────────────────────────────────────
    m.def("mpi_rank", &mpi_rank, "MPI process rank (0 if no MPI)");
    m.def("mpi_size", &mpi_size, "Number of MPI processes (1 if no MPI)");
}
