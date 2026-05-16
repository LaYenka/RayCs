#pragma once
#include "mesh.hpp"
#include "vec3.hpp"
#include <vector>
#include <cstdint>
#include <iostream>

struct HitRecord {
    double t;
    double u, v;
    int tri_index;
    bool hit;
};

struct BVHNode {
    AABB bounds;
    int left;
    int right;
    int tri_start;
    int tri_count;

    bool is_leaf() const { return left == -1; }
};

class BVH {
public:
    BVH();
    void build(std::vector<Triangle>& triangles, int max_leaf = 4);
    HitRecord closest_hit(const Vec3& origin, const Vec3& dir) const;
    bool any_hit(const Vec3& origin, const Vec3& dir, double max_t) const;

    const std::vector<BVHNode>& nodes() const { return nodes_; }
    const std::vector<Triangle>& triangles() const { return triangles_; }

    size_t serialized_size() const;
    void serialize(char* buffer) const;
    void deserialize(const char* buffer);

private:
    int build_recursive(int start, int end, int depth);
    std::vector<BVHNode> nodes_;
    std::vector<Triangle> triangles_;
};
