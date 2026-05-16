#pragma once
#include "vec3.hpp"
#include <vector>
#include <algorithm>

struct Triangle {
    Vec3 v0, v1, v2;
    Vec3 normal;
    Vec3 centroid;
    double area;
    int global_index;
};

struct AABB {
    Vec3 min_pt, max_pt;
    AABB() {
        min_pt = Vec3(1e30, 1e30, 1e30);
        max_pt = Vec3(-1e30, -1e30, -1e30);
    }
    AABB(const Vec3& mn, const Vec3& mx) : min_pt(mn), max_pt(mx) {}

    void expand(const Vec3& p) {
        min_pt.x = std::min(min_pt.x, p.x);
        min_pt.y = std::min(min_pt.y, p.y);
        min_pt.z = std::min(min_pt.z, p.z);
        max_pt.x = std::max(max_pt.x, p.x);
        max_pt.y = std::max(max_pt.y, p.y);
        max_pt.z = std::max(max_pt.z, p.z);
    }
    void expand(const AABB& o) {
        expand(o.min_pt); expand(o.max_pt);
    }
    double surface_area() const {
        Vec3 d = max_pt - min_pt;
        return 2.0 * (d.x*d.y + d.y*d.z + d.z*d.x);
    }
    Vec3 center() const { return (min_pt + max_pt) * 0.5; }
    bool intersects_ray(const Vec3& origin, const Vec3& dir) const {
        double tmin = -1e30, tmax = 1e30;
        for (int i = 0; i < 3; ++i) {
            double inv_d = 1.0 / dir[i];
            double t0 = (min_pt[i] - origin[i]) * inv_d;
            double t1 = (max_pt[i] - origin[i]) * inv_d;
            if (inv_d < 0) { double tmp = t0; t0 = t1; t1 = tmp; }
            tmin = std::max(tmin, t0);
            tmax = std::min(tmax, t1);
            if (tmax < tmin || tmax < 1e-6) return false;
        }
        return true;
    }
    bool intersects_ray_maxt(const Vec3& origin, const Vec3& dir, double max_t) const {
        double tmin = -1e30, tmax = 1e30;
        for (int i = 0; i < 3; ++i) {
            double inv_d = 1.0 / dir[i];
            double t0 = (min_pt[i] - origin[i]) * inv_d;
            double t1 = (max_pt[i] - origin[i]) * inv_d;
            if (inv_d < 0) { double tmp = t0; t0 = t1; t1 = tmp; }
            tmin = std::max(tmin, t0);
            tmax = std::min(tmax, t1);
            if (tmax < tmin || tmax < 1e-6 || tmin > max_t) return false;
        }
        return true;
    }
};

struct Mesh {
    std::vector<Triangle> triangles;
    AABB bounds;

    void compute_bounds() {
        bounds = AABB();
        for (auto& t : triangles) {
            bounds.expand(t.v0);
            bounds.expand(t.v1);
            bounds.expand(t.v2);
        }
    }
};
