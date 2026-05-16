# RayCs — EM Radar Scattering Ray Tracer

A C++ ray tracer with OpenMP and MPI for computing electromagnetic radar cross-section (RCS) from 3D meshes. Supports **Physical Optics (PO)** and **Shooting & Bouncing Rays (SBR)** with SAH-based BVH acceleration. Includes a **Python API** with pybind11 bindings for interactive use and visualization.

## Architecture

```
RayCs/
├── CMakeLists.txt              # Builds both CLI and Python _core
├── src/
│   ├── main.cpp                # Entry point, CLI parsing
│   ├── config.hpp              # Runtime configuration
│   ├── vec3.hpp                # 3D vector math
│   ├── mat3.hpp                # 3D matrix math
│   ├── mesh.hpp                # Mesh representation
│   ├── cgns_mesh.hpp/cpp       # CGNS/OBJ mesh reader
│   ├── bvh.hpp/cpp             # SAH-based BVH acceleration
│   ├── ray.hpp                 # Ray structure
│   ├── po.hpp/cpp              # Physical Optics engine
│   ├── sbr.hpp/cpp             # SBR ray tracing engine
│   └── rcs.hpp/cpp             # RCS computation & CSV output
├── python/
│   ├── pyproject.toml          # scikit-build-core config
│   └── src/raycs/
│       ├── __init__.py         # Solver, RCSResult classes
│       ├── _core/bindings.cpp  # pybind11 bindings
│       ├── visualize.py        # matplotlib helpers
│       ├── examples/           # Example scripts
│       └── tests/              # pytest suite (72 tests)
├── build/                      # CLI build output
└── examples/                   # Mesh files and plotting scripts
```

## Dependencies

| Component | Required | Notes |
|-----------|----------|-------|
| C++17 compiler | Yes | GCC ≥ 8, Clang ≥ 7 |
| CMake ≥ 3.16 | Yes | |
| OpenMP | Yes | Shared-memory parallelism |
| CGNS library | Yes | Mesh I/O (`libcgns-dev`) |
| MPI | Optional | Distributed parallelism |
| Python ≥ 3.8 | Optional | For Python bindings |
| pybind11 | Optional | Fetched by CMake when `BUILD_PYTHON=ON` |

## Installation

### CLI Tool

```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

With MPI:

```bash
cmake .. -DCMAKE_BUILD_TYPE=Release
# CMake auto-detects MPI; if found, USE_MPI=1 is defined
make -j$(nproc)
```

### Python Package

```bash
pip install ./python/
```

Or editable (for development):

```bash
pip install -e ./python/
```

With MPI (requires MPI development packages):

```bash
pip install -e ./python/ --config-settings=cmake.args="-DBUILD_PYTHON=ON;-DCMAKE_BUILD_TYPE=Release"
```

This builds the `_core` extension module using the root `CMakeLists.txt` with `-DBUILD_PYTHON=ON`.

## CLI Usage

```bash
./raycs --mesh <file.obj> [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mesh <file>` | Mesh file (.obj or .cgns) | **required** |
| `--freq <Hz>` | Frequency | 10e9 |
| `--method <po\|sbr\|both>` | Scattering method | sbr |
| `--bounces <N>` | Max ray bounces (SBR) | 3 |
| `--ray-density <N>` | Rays per wavelength (SBR) | 10 |
| `--theta-min/max <deg>` | Theta range | 0 / 180 |
| `--theta-steps <N>` | Theta resolution | 180 |
| `--phi-min/max <deg>` | Phi range | 0 / 360 |
| `--phi-steps <N>` | Phi resolution | 360 |
| `--bistatic` | Enable bistatic mode | monostatic |
| `--inc-theta <deg>` | Incident theta (bistatic) | 0 |
| `--inc-phi <deg>` | Incident phi (bistatic) | 0 |
| `--output <file>` | Output CSV | rcs.csv |

### Examples

```bash
# Monostatic SBR
./raycs --mesh aircraft.obj --freq 10e9 --method sbr

# Physical Optics
./raycs --mesh aircraft.obj --freq 10e9 --method po

# Bistatic
./raycs --mesh aircraft.obj --freq 10e9 --method po \
    --bistatic --inc-theta 45 --inc-phi 0

# MPI parallel
mpirun -np 4 ./raycs --mesh aircraft.obj --freq 10e9 --method sbr
```

## Python API Usage

### Quick Start

```python
import raycs

# Basic monostatic PO simulation
solver = raycs.Solver(
    mesh_file="cylinder.obj",
    frequency=3e9,
    method="po",
    theta_steps=36,
    phi_steps=36,
    verbose=True,
)
result = solver.run()

# Print peak RCS
import numpy as np
idx = np.argmax(result.rcs_total_db)
print(f"Peak RCS: {result.rcs_total_db[idx]:.1f} dBsm "
      f"at theta={result.theta_deg[idx]:.0f}°, phi={result.phi_deg[idx]:.0f}°")

# Visualization
result.plot_3d()
result.plot_polar()
result.plot_2d(phi_cut=0)
```

### Solver API

```python
class Solver:
    def __init__(self, mesh=None, mesh_file=None, frequency=10e9,
                 method="po", theta_steps=180, phi_steps=360,
                 max_bounces=3, ray_density=10.0, verbose=False): ...

    def run(self) -> RCSResult:
        """Run PO, SBR, or BOTH sweep (MPI-distributed in C++)."""

    def run_bistatic(self, inc_theta=0, inc_phi=0) -> RCSResult:
        """Run bistatic PO sweep."""
```

### RCSResult

```python
class RCSResult:
    # Numpy arrays
    theta_deg, phi_deg       # observation angles
    rcs_total_db, rcs_vv_db, rcs_hh_db  # RCS in dBsm

    def to_csv(self, path): ...
    def to_numpy(self): ...           # Structured array
    def plot_2d(self, phi_cut=0): ...
    def plot_3d(self): ...
    def plot_polar(self): ...
```

### MPI Parallelism

MPI is handled **inside the C++ sweep functions** — no mpi4py needed:

```bash
# Run transparently under MPI
mpirun -np 4 python -c "
import raycs
s = raycs.Solver(mesh_file='target.obj', frequency=3e9, method='sbr')
result = s.run()
if result:
    print(f'RCS range: {result.rcs_total_db.min():.1f} to {result.rcs_total_db.max():.1f} dBsm')
"
```

Non-root ranks receive `None` from `solver.run()` — only rank 0 gets the full result.

### Visualization

```python
from raycs.visualize import (
    plot_2d, plot_3d, plot_polar,
    plot_radiation_pattern, plot_rotation_comparison,
)

# Combined 2x2 figure
fig = plot_radiation_pattern(result)
fig.savefig("pattern.png", dpi=150)

# Rotation comparison
results = {"0°": result_0, "30°": result_30, "45°": result_45}
fig = plot_rotation_comparison(results, title="Rotation Study")
```

### Low-Level Access

The Python bindings expose all C++ types directly:

```python
from raycs import Vec3, Mat3, Mesh, BVH, Config

v = Vec3(1, 2, 3)
v.normalized()

mesh = raycs.load_mesh("target.obj")
bvh = BVH()
bvh.build(mesh.triangles)
hit = bvh.closest_hit(Vec3(0, 0, 1), Vec3(0, 0, -1))
```

## Output Format

CSV columns: `theta_deg, phi_deg, RCS_total_dBsm, RCS_VV_dBsm, RCS_HH_dBsm`

## Physics

- **Incident wave**: from +Z direction toward origin (monostatic: `inc_dir = -obs_dir`)
- **PEC bodies**: Perfect electric conductor assumption
- **Far-field**: Source and observer in far-field zone
- **Ray tube divergence**: Accounts for spherical wave spreading

### Parallelization

| Layer | Technology | Granularity |
|-------|-----------|-------------|
| Per-angle PO | OpenMP | Triangles |
| Per-angle SBR | OpenMP | Rays |
| Angle distribution | MPI | Observation angles |

## Testing

```bash
cd python
python3 -m pytest tests/ -v
```

## Project Status

Version 0.1.0 — Linux only. Python API with pybind11 bindings, scikit-build-core packaging, 72 pytest tests.
