"""Tests for mesh loading and geometry."""

import raycs


class TestMeshLoading:
    def test_load_obj(self, cylinder_mesh_path):
        mesh = raycs.load_mesh(cylinder_mesh_path)
        assert len(mesh.triangles) > 0

    def test_load_obj_function(self, cylinder_mesh_path):
        mesh = raycs.load_obj_mesh(cylinder_mesh_path)
        assert len(mesh.triangles) > 0

    def test_mesh_bounds(self, cylinder_mesh):
        b = cylinder_mesh.bounds
        assert b.min_pt.x < b.max_pt.x
        assert b.min_pt.y < b.max_pt.y
        assert b.min_pt.z < b.max_pt.z

    def test_triangle_properties(self, simple_triangle):
        t = simple_triangle.triangles[0]
        # Normal should point in +Z (positive z = CCW from XY plane)
        assert t.normal.z > 0
        assert t.area > 0
        assert t.global_index == 0

    def test_box_triangles(self, box_mesh_obj):
        assert len(box_mesh_obj.triangles) == 12
        # Cube face is 1x1 = 1.0, each triangle half = 0.5
        for t in box_mesh_obj.triangles:
            assert abs(t.area - 0.5) < 1e-10


class TestAABB:
    def test_default_constructor(self):
        aabb = raycs.AABB()
        assert aabb.min_pt.x == 1e30
        assert aabb.max_pt.x == -1e30

    def test_expand_point(self):
        aabb = raycs.AABB()
        aabb.expand(raycs.Vec3(-1, -1, -1))
        aabb.expand(raycs.Vec3(1, 1, 1))
        assert aabb.min_pt.x == -1.0
        assert aabb.max_pt.x == 1.0

    def test_center(self):
        aabb = raycs.AABB(raycs.Vec3(-1, -1, -1), raycs.Vec3(1, 1, 1))
        c = aabb.center()
        assert c.x == 0.0
        assert c.y == 0.0
        assert c.z == 0.0

    def test_surface_area(self):
        aabb = raycs.AABB(raycs.Vec3(0, 0, 0), raycs.Vec3(1, 1, 1))
        assert aabb.surface_area() == 6.0

    def test_intersects_ray(self):
        aabb = raycs.AABB(raycs.Vec3(-1, -1, -1), raycs.Vec3(1, 1, 1))
        origin = raycs.Vec3(0, 0, 5)
        direction = raycs.Vec3(0, 0, -1)
        assert aabb.intersects_ray(origin, direction)

    def test_intersects_ray_miss(self):
        aabb = raycs.AABB(raycs.Vec3(-1, -1, -1), raycs.Vec3(1, 1, 1))
        origin = raycs.Vec3(10, 10, 5)
        direction = raycs.Vec3(0, 0, -1)
        assert not aabb.intersects_ray(origin, direction)
