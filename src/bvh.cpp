#include "bvh.hpp"
#include <algorithm>
#include <cstring>
#include <stack>
#include <iostream>

static const int MAX_STACK = 64;
static const double EPSILON = 1e-8;

static bool moeller_trumbore(const Vec3& v0, const Vec3& e1, const Vec3& e2,
                              const Vec3& origin, const Vec3& dir,
                              double& t, double& u, double& v) {
    Vec3 h = dir.cross(e2);
    double a = e1.dot(h);
    if (a > -EPSILON && a < EPSILON) return false;
    double f = 1.0 / a;
    Vec3 s = origin - v0;
    u = f * s.dot(h);
    if (u < 0.0 || u > 1.0) return false;
    Vec3 q = s.cross(e1);
    v = f * dir.dot(q);
    if (v < 0.0 || u + v > 1.0) return false;
    t = f * e2.dot(q);
    return t > 1e-6;
}

BVH::BVH() {}

void BVH::build(std::vector<Triangle>& triangles, int max_leaf) {
    triangles_ = std::move(triangles);
    if (!triangles_.empty()) {
        build_recursive(0, (int)triangles_.size(), 0);
    }
}

int BVH::build_recursive(int start, int end, int depth) {
    int node_idx = (int)nodes_.size();
    nodes_.push_back(BVHNode());
    BVHNode& node = nodes_[node_idx];
    node.left = -1;
    node.right = -1;
    node.tri_start = start;
    node.tri_count = end - start;

    AABB bounds;
    for (int i = start; i < end; ++i) {
        bounds.expand(triangles_[i].v0);
        bounds.expand(triangles_[i].v1);
        bounds.expand(triangles_[i].v2);
    }
    node.bounds = bounds;

    int ntri = end - start;
    if (ntri <= 4 || depth > 30) {
        return node_idx;
    }

    int best_axis = -1;
    int best_split = -1;
    double best_cost = 1e30;

    const double C_TRAV = 1.0;
    const double C_ISECT = 1.0;

    for (int axis = 0; axis < 3; ++axis) {
        double lo = bounds.min_pt[axis];
        double hi = bounds.max_pt[axis];
        if (hi - lo < 1e-10) continue;

        for (int s = 1; s < ntri; ++s) {
            AABB left_b, right_b;
            for (int i = start; i < start + s; ++i) {
                left_b.expand(triangles_[i].v0);
                left_b.expand(triangles_[i].v1);
                left_b.expand(triangles_[i].v2);
            }
            for (int i = start + s; i < end; ++i) {
                right_b.expand(triangles_[i].v0);
                right_b.expand(triangles_[i].v1);
                right_b.expand(triangles_[i].v2);
            }

            double sa = bounds.surface_area();
            if (sa < 1e-15) continue;

            double cost = C_TRAV + C_ISECT * (
                s * left_b.surface_area() / sa +
                (ntri - s) * right_b.surface_area() / sa
            );
            if (cost < best_cost) {
                best_cost = cost;
                best_axis = axis;
                best_split = s;
            }
        }
    }

    double leaf_cost = C_ISECT * ntri;
    if (best_axis == -1 || best_cost >= leaf_cost) {
        return node_idx;
    }

    std::nth_element(triangles_.begin() + start,
                     triangles_.begin() + start + best_split,
                     triangles_.begin() + end,
                     [best_axis](const Triangle& a, const Triangle& b) {
                         return a.centroid[best_axis] < b.centroid[best_axis];
                     });

    int mid = start + best_split;
    node.left = build_recursive(start, mid, depth + 1);
    node.right = build_recursive(mid, end, depth + 1);

    return node_idx;
}

HitRecord BVH::closest_hit(const Vec3& origin, const Vec3& dir) const {
    HitRecord best{1e30, 0, 0, -1, false};
    int stack[MAX_STACK];
    int sp = 0;
    stack[sp++] = 0;

    while (sp > 0) {
        int idx = stack[--sp];
        const BVHNode& node = nodes_[idx];

        if (!node.bounds.intersects_ray(origin, dir)) continue;

        if (node.is_leaf()) {
            for (int i = 0; i < node.tri_count; ++i) {
                const Triangle& tri = triangles_[node.tri_start + i];
                Vec3 le1 = tri.v1 - tri.v0;
                Vec3 le2 = tri.v2 - tri.v0;
                double t, u, v;
                if (moeller_trumbore(tri.v0, le1, le2, origin, dir, t, u, v)) {
                    if (t < best.t) {
                        best.t = t; best.u = u; best.v = v;
                        best.tri_index = tri.global_index;
                        best.hit = true;
                    }
                }
            }
        } else {
            if (sp + 2 < MAX_STACK) {
                stack[sp++] = node.right;
                stack[sp++] = node.left;
            }
        }
    }
    return best;
}

bool BVH::any_hit(const Vec3& origin, const Vec3& dir, double max_t) const {
    int stack[MAX_STACK];
    int sp = 0;
    stack[sp++] = 0;

    while (sp > 0) {
        int idx = stack[--sp];
        const BVHNode& node = nodes_[idx];

        if (!node.bounds.intersects_ray_maxt(origin, dir, max_t)) continue;

        if (node.is_leaf()) {
            for (int i = 0; i < node.tri_count; ++i) {
                const Triangle& tri = triangles_[node.tri_start + i];
                Vec3 le1 = tri.v1 - tri.v0;
                Vec3 le2 = tri.v2 - tri.v0;
                double t, u, v;
                if (moeller_trumbore(tri.v0, le1, le2, origin, dir, t, u, v) && t < max_t) {
                    return true;
                }
            }
        } else {
            if (sp + 2 < MAX_STACK) {
                stack[sp++] = node.right;
                stack[sp++] = node.left;
            }
        }
    }
    return false;
}

size_t BVH::serialized_size() const {
    return sizeof(size_t) * 2 +
           nodes_.size() * sizeof(BVHNode) +
           triangles_.size() * sizeof(Triangle);
}

void BVH::serialize(char* buffer) const {
    size_t nn = nodes_.size(), nt = triangles_.size();
    std::memcpy(buffer, &nn, sizeof(size_t));
    std::memcpy(buffer + sizeof(size_t), &nt, sizeof(size_t));
    char* p = buffer + 2 * sizeof(size_t);
    std::memcpy(p, nodes_.data(), nn * sizeof(BVHNode));
    p += nn * sizeof(BVHNode);
    std::memcpy(p, triangles_.data(), nt * sizeof(Triangle));
}

void BVH::deserialize(const char* buffer) {
    size_t nn, nt;
    std::memcpy(&nn, buffer, sizeof(size_t));
    std::memcpy(&nt, buffer + sizeof(size_t), sizeof(size_t));
    const char* p = buffer + 2 * sizeof(size_t);
    nodes_.resize(nn);
    std::memcpy(nodes_.data(), p, nn * sizeof(BVHNode));
    p += nn * sizeof(BVHNode);
    triangles_.resize(nt);
    std::memcpy(triangles_.data(), p, nt * sizeof(Triangle));
}
