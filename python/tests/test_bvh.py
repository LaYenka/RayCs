"""Tests for BVH acceleration structure and ray intersection."""

import raycs


class TestBVH:
    def test_build(self, cylinder_mesh):
        bvh = raycs.BVH()
        bvh.build(cylinder_mesh.triangles)
        assert len(bvh.nodes()) > 0
        assert len(bvh.triangles()) == len(cylinder_mesh.triangles)

    def test_closest_hit(self, box_mesh_obj):
        bvh = raycs.BVH()
        bvh.build(box_mesh_obj.triangles)

        # Shoot ray from +Z toward origin
        origin = raycs.Vec3(0, 0, 2)
        direction = raycs.Vec3(0, 0, -1)
        hit = bvh.closest_hit(origin, direction)
        assert hit.hit
        assert hit.tri_index >= 0
        assert 1.4 < hit.t < 2.6  # distance from z=2 to box at z=0.5

    def test_closest_hit_miss(self, box_mesh_obj):
        bvh = raycs.BVH()
        bvh.build(box_mesh_obj.triangles)

        # Shoot ray that misses
        origin = raycs.Vec3(10, 10, 2)
        direction = raycs.Vec3(0, 0, -1)
        hit = bvh.closest_hit(origin, direction)
        assert not hit.hit

    def test_any_hit(self, box_mesh_obj):
        bvh = raycs.BVH()
        bvh.build(box_mesh_obj.triangles)

        origin = raycs.Vec3(0, 0, 2)
        direction = raycs.Vec3(0, 0, -1)
        assert bvh.any_hit(origin, direction, 10.0)

    def test_any_hit_miss(self, box_mesh_obj):
        bvh = raycs.BVH()
        bvh.build(box_mesh_obj.triangles)

        origin = raycs.Vec3(10, 10, 2)
        direction = raycs.Vec3(0, 0, -1)
        assert not bvh.any_hit(origin, direction, 10.0)

    def test_hit_on_simple_triangle(self, simple_triangle):
        bvh = raycs.BVH()
        bvh.build(simple_triangle.triangles)

        # Triangle at z=0, shoot from +Z
        origin = raycs.Vec3(0.1, 0.1, 1)
        direction = raycs.Vec3(0, 0, -1)
        hit = bvh.closest_hit(origin, direction)
        assert hit.hit
        assert hit.t == 1.0  # distance to z=0 plane
        assert hit.tri_index == 0

    def test_hit_record_data(self, simple_triangle):
        bvh = raycs.BVH()
        bvh.build(simple_triangle.triangles)

        origin = raycs.Vec3(0.1, 0.1, 1)
        direction = raycs.Vec3(0, 0, -1)
        hit = bvh.closest_hit(origin, direction)
        assert hit.t == 1.0
        assert hit.u >= 0  # barycentric
        assert hit.v >= 0
        assert hit.tri_index == 0
