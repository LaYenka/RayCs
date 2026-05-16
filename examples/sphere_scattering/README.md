# Sphere Scattering Example for RayCs
# 
# This directory contains the complete workflow for simulating
# EM scattering from a PEC sphere and plotting the radiation pattern.

## Files

- `generate_sphere.py` - Generate sphere mesh in various formats
- `sphere.obj`       - UV sphere mesh (861 vertices, 1600 triangles)
- `run_simulation.sh` - Complete workflow script
- `plot_rcs.py`      - Plot RCS patterns from CSV output
- `sphere_scattering.py` - Analytical comparison (no C++ required)

## Quick Start

### Option 1: Analytical Only (no compilation needed)

```bash
cd examples/sphere_scattering
python3 sphere_scattering.py
```

This generates:
- `sphere_rcs_pattern.png` - 3D radiation pattern plot
- `rcs_analytical.csv` - RCS data (theta, phi, dBsm)

### Option 2: Full RayCs Simulation

First, build RayCs:

```bash
cd /opt/dev/RayCs
g++ -std=c++17 -O3 -fopenmp -DUSE_MPI=0 -Isrc src/*.cpp -lcgns -o raycs
```

Then run the sphere simulation:

```bash
cd examples/sphere_scattering
python3 sphere_scattering.py   # Generate mesh
./run_simulation.sh            # Run RayCs
python3 plot_rcs.py rcs.csv    # Plot results
```

## Physics Background

### PEC Sphere RCS

For a perfectly conducting sphere of radius `a` at frequency `f`:

- **Wavenumber**: k = 2πf/c
- **Size parameter**: ka = k·a
- **Geometric RCS**: πa² (physical cross-section)

For large spheres (ka >> 1), the RCS oscillates around πa² 
with ripple frequency proportional to ka.

### Example Parameters

| Parameter | Value |
|---|---|
| Sphere radius | 10 cm |
| Frequency | 3 GHz (X-band) |
| Wavelength | 10 cm |
| ka | 6.28 |
| Expected RCS | ~5 dBsm |

## Output Format

CSV file with columns:
```
theta_deg, phi_deg, RCS_total_dBsm, RCS_VV_dBsm, RCS_HH_dBsm
```

## Visualization

The `plot_rcs.py` script supports multiple visualization modes:

```bash
python3 plot_rcs.py rcs.csv --method 2d   # 2D cuts
python3 plot_rcs.py rcs.csv --method 3d   # 3D surface
python3 plot_rcs.py rcs.csv --method polar  # Polar plot
```

## Notes

- The sphere mesh is scaled so that radius = 1 wavelength at the simulation frequency
- SBR provides accurate results for multiple reflections
- PO is faster but limited to single-bounce approximation
- For accurate sphere RCS, use high ray_density (≥10 rays per wavelength)
