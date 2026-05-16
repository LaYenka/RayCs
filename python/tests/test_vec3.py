"""Tests for Vec3 math operations."""

import math
import raycs


def test_default_constructor():
    v = raycs.Vec3()
    assert v.x == 0.0
    assert v.y == 0.0
    assert v.z == 0.0


def test_parameter_constructor():
    v = raycs.Vec3(1.0, 2.0, 3.0)
    assert v.x == 1.0
    assert v.y == 2.0
    assert v.z == 3.0


def test_add():
    a = raycs.Vec3(1, 2, 3)
    b = raycs.Vec3(4, 5, 6)
    c = a + b
    assert c.x == 5.0
    assert c.y == 7.0
    assert c.z == 9.0


def test_sub():
    a = raycs.Vec3(4, 5, 6)
    b = raycs.Vec3(1, 2, 3)
    c = a - b
    assert c.x == 3.0
    assert c.y == 3.0
    assert c.z == 3.0


def test_mul_scalar():
    v = raycs.Vec3(1, 2, 3)
    r = v * 2.0
    assert r.x == 2.0
    assert r.y == 4.0
    assert r.z == 6.0


def test_div_scalar():
    v = raycs.Vec3(2, 4, 6)
    r = v / 2.0
    assert r.x == 1.0
    assert r.y == 2.0
    assert r.z == 3.0


def test_neg():
    v = raycs.Vec3(1, -2, 3)
    r = -v
    assert r.x == -1.0
    assert r.y == 2.0
    assert r.z == -3.0


def test_getitem():
    v = raycs.Vec3(1, 2, 3)
    assert v[0] == 1.0
    assert v[1] == 2.0
    assert v[2] == 3.0


def test_setitem():
    v = raycs.Vec3()
    v[0] = 5.0
    v[1] = 6.0
    v[2] = 7.0
    assert v.x == 5.0
    assert v.y == 6.0
    assert v.z == 7.0


def test_dot():
    a = raycs.Vec3(1, 2, 3)
    b = raycs.Vec3(4, 5, 6)
    assert a.dot(b) == 4 + 10 + 18  # 32


def test_cross():
    a = raycs.Vec3(1, 0, 0)
    b = raycs.Vec3(0, 1, 0)
    c = a.cross(b)
    assert c.x == 0.0
    assert c.y == 0.0
    assert c.z == 1.0


def test_norm():
    v = raycs.Vec3(3, 4, 0)
    assert v.norm() == 5.0


def test_norm_sq():
    v = raycs.Vec3(1, 2, 3)
    assert v.norm_sq() == 14.0


def test_normalized():
    v = raycs.Vec3(3, 4, 0)
    n = v.normalized()
    assert abs(n.norm() - 1.0) < 1e-12
    assert abs(n.x - 0.6) < 1e-12
    assert abs(n.y - 0.8) < 1e-12


def test_normalized_zero():
    v = raycs.Vec3(0, 0, 0)
    n = v.normalized()
    assert n.x == 0.0
    assert n.y == 0.0
    assert n.z == 0.0


def test_reflect():
    v = raycs.Vec3(0, 0, -1)  # incoming from +Z
    n = raycs.Vec3(0, 0, 1)   # surface normal pointing +Z
    r = v.reflect(n)
    assert abs(r.x) < 1e-12
    assert abs(r.y) < 1e-12
    assert r.z == 1.0  # reflects back to +Z direction


def test_free_function_dot():
    a = raycs.Vec3(1, 0, 0)
    b = raycs.Vec3(0, 1, 0)
    assert raycs.dot(a, b) == 0.0


def test_free_function_cross():
    a = raycs.Vec3(1, 0, 0)
    b = raycs.Vec3(0, 1, 0)
    c = raycs.cross(a, b)
    assert c.z == 1.0


def test_repr():
    v = raycs.Vec3(1.0, 2.0, 3.0)
    s = repr(v)
    assert "Vec3" in s
