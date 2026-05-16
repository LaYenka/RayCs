#include "cgns_mesh.hpp"
#include <cgnslib.h>
#include <iostream>
#include <vector>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <array>

#define CGNS_CALL(call) do { \
    int err = (call); \
    if (err != CG_OK) { \
        throw std::runtime_error(std::string("CGNS error code ") + std::to_string(err) + " at " + __FILE__ + ":" + std::to_string(__LINE__)); \
    } \
} while(0)

static Triangle make_triangle(const Vec3& a, const Vec3& b, const Vec3& c, int idx) {
    Triangle tri;
    tri.v0 = a; tri.v1 = b; tri.v2 = c;
    Vec3 e1 = b - a;
    Vec3 e2 = c - a;
    Vec3 n = e1.cross(e2);
    double area = 0.5 * n.norm();
    tri.normal = (area > 1e-15) ? n / n.norm() : Vec3{0, 0, 1};
    tri.centroid = (a + b + c) / 3.0;
    tri.area = area;
    tri.global_index = idx;
    return tri;
}

Mesh load_cgns_mesh(const std::string& filename) {
    int cg_file = 0;
    CGNS_CALL(cg_open(filename.c_str(), CG_MODE_READ, &cg_file));

    int nbases = 0;
    CGNS_CALL(cg_nbases(cg_file, &nbases));

    Mesh mesh;
    int tri_idx = 0;

    for (int b = 1; b <= nbases; ++b) {
        int nzones = 0;
        CGNS_CALL(cg_nzones(cg_file, b, &nzones));

        for (int z = 1; z <= nzones; ++z) {
            cgsize_t isize[3][3];
            CGNS_CALL(cg_zone_read(cg_file, b, z, nullptr, isize[0]));

            cgsize_t nverts = isize[0][0];

            std::vector<double> x(nverts), y(nverts), zc(nverts);
            cgsize_t rmin[3] = {1, 1, 1};
            cgsize_t rmax[3] = {(cgsize_t)nverts, 1, 1};
            CGNS_CALL(cg_coord_read(cg_file, b, z, "CoordinateX", CGNS_ENUMV(RealDouble), rmin, rmax, x.data()));
            CGNS_CALL(cg_coord_read(cg_file, b, z, "CoordinateY", CGNS_ENUMV(RealDouble), rmin, rmax, y.data()));
            CGNS_CALL(cg_coord_read(cg_file, b, z, "CoordinateZ", CGNS_ENUMV(RealDouble), rmin, rmax, zc.data()));

            int nsections = 0;
            CGNS_CALL(cg_nsections(cg_file, b, z, &nsections));

            for (int s = 1; s <= nsections; ++s) {
                char sec_name[64];
                ElementType_t etype = ElementTypeNull;
                cgsize_t start_elem = 0, end_elem = 0;
                int nbndry = 0, parent_flag = 0;
                CGNS_CALL(cg_section_read(cg_file, b, z, s, sec_name, &etype, &start_elem, &end_elem, &nbndry, &parent_flag));

                bool is_surface = (etype == CGNS_ENUMV(TRI_3) || etype == CGNS_ENUMV(QUAD_4));
                if (!is_surface) continue;

                cgsize_t nelems = end_elem - start_elem + 1;
                int stride = (etype == CGNS_ENUMV(TRI_3)) ? 3 : 4;
                cgsize_t nconn = nelems * stride;

                std::vector<cgsize_t> conn(nconn);
                CGNS_CALL(cg_elements_read(cg_file, b, z, s, conn.data(), nullptr));

                for (cgsize_t e = 0; e < nelems; ++e) {
                    cgsize_t base = e * stride;
                    int i0 = (int)conn[base] - 1;
                    int i1 = (int)conn[base+1] - 1;
                    int i2 = (int)conn[base+2] - 1;

                    if (i0 < 0 || i0 >= (int)nverts || i1 < 0 || i1 >= (int)nverts || i2 < 0 || i2 >= (int)nverts) continue;

                    Vec3 v0{x[i0], y[i0], zc[i0]};
                    Vec3 v1{x[i1], y[i1], zc[i1]};
                    Vec3 v2{x[i2], y[i2], zc[i2]};
                    mesh.triangles.push_back(make_triangle(v0, v1, v2, tri_idx++));

                    if (etype == CGNS_ENUMV(QUAD_4)) {
                        int i3 = (int)conn[base+3] - 1;
                        if (i3 >= 0 && i3 < (int)nverts) {
                            Vec3 v3{x[i3], y[i3], zc[i3]};
                            mesh.triangles.push_back(make_triangle(v0, v2, v3, tri_idx++));
                        }
                    }
                }
            }
        }
    }

    CGNS_CALL(cg_close(cg_file));

    if (mesh.triangles.empty()) {
        throw std::runtime_error("No surface triangles found in CGNS file: " + filename);
    }

    mesh.compute_bounds();
    std::cout << "Loaded " << mesh.triangles.size() << " triangles from " << filename << "\n";
    return mesh;
}

Mesh load_obj_mesh(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open OBJ file: " + filename);
    }

    std::vector<Vec3> vertices;
    std::vector<std::array<int, 3>> faces;

    std::string line;
    while (std::getline(file, line)) {
        std::istringstream iss(line);
        std::string type;
        iss >> type;
        if (type == "v") {
            double x, y, z;
            iss >> x >> y >> z;
            vertices.push_back({x, y, z});
        } else if (type == "f") {
            std::string token;
            std::vector<int> idx;
            while (iss >> token) {
                int vi = std::stoi(token) - 1;
                idx.push_back(vi);
            }
            if (idx.size() >= 3) {
                faces.push_back({idx[0], idx[1], idx[2]});
                if (idx.size() == 4) {
                    faces.push_back({idx[0], idx[2], idx[3]});
                }
            }
        }
    }

    Mesh mesh;
    for (size_t i = 0; i < faces.size(); ++i) {
        const auto& f = faces[i];
        Vec3 v0 = vertices[f[0]];
        Vec3 v1 = vertices[f[1]];
        Vec3 v2 = vertices[f[2]];
        mesh.triangles.push_back(make_triangle(v0, v1, v2, (int)i));
    }

    mesh.compute_bounds();
    std::cout << "Loaded " << mesh.triangles.size() << " triangles from " << filename << "\n";
    return mesh;
}
