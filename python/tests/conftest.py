"""Shared fixtures for RayCs tests."""

import os
import tempfile
import pytest
import raycs


@pytest.fixture(scope="session")
def cylinder_mesh_path():
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "examples",
        "cylinder_scattering", "cylinder_0deg.obj"
    )


@pytest.fixture(scope="session")
def sphere_mesh_path():
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "examples",
        "sphere_scattering", "sphere_0deg.obj"
    )


@pytest.fixture(scope="session")
def simple_triangle_mesh():
    """Single triangle mesh for BVH/intersection tests."""
    obj = (
        "# Simple test triangle\n"
        "v 0 0 0\n"
        "v 1 0 0\n"
        "v 0 1 0\n"
        "f 1 2 3\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as f:
        f.write(obj)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture(scope="session")
def box_mesh():
    """Simple unit cube mesh (2 triangles per face = 12 triangles)."""
    lines = ["# Unit cube\n"]
    # 8 vertices
    verts = [
        (-0.5, -0.5, -0.5), ( 0.5, -0.5, -0.5),
        ( 0.5,  0.5, -0.5), (-0.5,  0.5, -0.5),
        (-0.5, -0.5,  0.5), ( 0.5, -0.5,  0.5),
        ( 0.5,  0.5,  0.5), (-0.5,  0.5,  0.5),
    ]
    for v in verts:
        lines.append(f"v {v[0]} {v[1]} {v[2]}\n")
    # 12 triangles (2 per face)
    faces = [
        (1,2,3), (1,3,4),  # -Z
        (5,7,6), (5,8,7),  # +Z
        (1,5,6), (1,6,2),  # -X
        (3,7,8), (3,8,4),  # +X
        (1,4,8), (1,8,5),  # -Y
        (2,6,7), (2,7,3),  # +Y
    ]
    for f in faces:
        lines.append(f"f {f[0]} {f[1]} {f[2]}\n")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".obj", delete=False) as fp:
        fp.writelines(lines)
        path = fp.name
    yield path
    os.unlink(path)


@pytest.fixture(scope="session")
def cylinder_mesh(cylinder_mesh_path):
    return raycs.load_mesh(cylinder_mesh_path)


@pytest.fixture(scope="session")
def sphere_mesh(sphere_mesh_path):
    return raycs.load_mesh(sphere_mesh_path)


@pytest.fixture(scope="session")
def box_mesh_obj(box_mesh):
    return raycs.load_mesh(box_mesh)


@pytest.fixture(scope="session")
def simple_triangle(simple_triangle_mesh):
    return raycs.load_mesh(simple_triangle_mesh)


@pytest.fixture
def small_solver(cylinder_mesh):
    """Solver with a fast 18x18 PO sweep."""
    return raycs.Solver(
        mesh=cylinder_mesh,
        frequency=3e9,
        method="po",
        theta_steps=18,
        phi_steps=18,
    )


@pytest.fixture
def small_solver_sbr(cylinder_mesh):
    """Solver with a fast SBR sweep."""
    return raycs.Solver(
        mesh=cylinder_mesh,
        frequency=3e9,
        method="sbr",
        theta_steps=10,
        phi_steps=10,
    )
