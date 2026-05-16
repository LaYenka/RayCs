# Cylinder Scattering Example for RayCs

This example demonstrates electromagnetic scattering from a PEC (Perfect Electric Conductor) cylinder using RayCs, including rotation studies.

## Quick Start

### Method 1: Using the Python Script (Recommended)

The `cylinder_scattering.py` script handles everything automatically:

```bash
cd /opt/dev/RayCs/examples/cylinder_scattering

# Generate all plots (auto-runs RayCs if needed)
python3 cylinder_scattering.py

# Specific plot methods
python3 cylinder_scattering.py --method 3d
python3 cylinder_scattering.py --method polar
python3 cylinder_scattering.py --method 2d

# Rotation comparison
python3 cylinder_scattering.py --rotation all

# Specific rotation
python3 cylinder_scattering.py --rotation 0 --method all
```

### Method 2: Manual Workflow

**Step 1: Build RayCs**
```bash
cd /opt/dev/RayCs
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j4
```

**Step 2: Generate Cylinder Mesh**
```bash
cd /opt/dev/RayCs/examples/cylinder_scattering
python3 generate_cylinder.py --radius 0.1 --length 0.5 --rotation 0
```

**Step 3: Run Simulation**
```bash
# Physical Optics (recommended - full angular coverage)
../build/raycs --mesh cylinder_0deg.obj --freq 3e9 --method po --output rcs_0deg.csv
```

**Step 4: Plot Results**
```bash
python3 cylinder_scattering.py --rotation 0 --method all
```

## Script Options

The `cylinder_scattering.py` script supports:

```bash
python3 cylinder_scattering.py [options]

Options:
  --method {2d,3d,polar,all}  Plot method (default: all)
  --rotation {0,30,45,all}     Rotation study (default: all)
  --phi-cut PHI_CUT            Phi angle for 2D cut (default: 0)
  --orientations               Show cylinder orientations plot
  --no-auto-run                Skip auto-run of RayCs
  --output, -o OUTPUT         Output file prefix

Examples:
  # Generate all plots with rotation comparison
  python3 cylinder_scattering.py

  # Only 3D plot
  python3 cylinder_scattering.py --method 3d

  # Only rotation comparison
  python3 cylinder_scattering.py --rotation all

  # Specific rotation
  python3 cylinder_scattering.py --rotation 0 --method all

  # Show cylinder orientations
  python3 cylinder_scattering.py --orientations
```

## Generated Plots

| Plot | File | Description |
|------|------|-------------|
| Cylinder Orientations | `cylinder_orientations.png` | 3D view of cylinder at 0°, 30°, 45° rotations |
| Rotation Comparison | `cylinder_rotation_comparison.png` | Compare 0°, 30°, 45° rotations |
| Combined Pattern | `cylinder_rcs_pattern.png` | 2D + polar + 3D + info |
| 3D Pattern | `cylinder_3d.png` | 3D radiation pattern |
| Polar Plot | `cylinder_polar.png` | Polar radiation pattern |
| 2D Cut | `cylinder_2d.png` | RCS vs theta at phi=0 |

## Generated Data

| File | Description |
|------|-------------|
| `cylinder_0deg.obj` | Cylinder mesh (0° rotation) |
| `cylinder_30deg.obj` | Cylinder mesh (30° rotation) |
| `cylinder_45deg.obj` | Cylinder mesh (45° rotation) |
| `rcs_0deg.csv` | RCS data (0° rotation) |
| `rcs_30deg.csv` | RCS data (30° rotation) |
| `rcs_45deg.csv` | RCS data (45° rotation) |

## Physics Background

### Incident Wave Direction

In monostatic mode (default), the plane wave is incident from the **+Z direction** toward the origin:

```
                    +Z (toward observer)
                     |
                     |
                     |      theta = 0°  ← Incident wave from +Z
                     |
         ← ← ← ← ← ←← Cylinder (along X axis)
                     |
                     |
                     +X

 θ = 0°   → Wave hits end cap (minimum RCS)
 θ = 90°  → Broadside (maximum RCS)
 θ = 180° → Wave hits other end cap
```

### Cylinder RCS Characteristics

For a PEC cylinder at 3 GHz (radius=10cm, length=50cm):

| Orientation | End-on (θ=0°) | Broadside (θ=90°) |
|------------|----------------|------------------|
| 0° rotation | ~-66 dBsm | ~-10 dBsm |
| 30° rotation | ~-28 dBsm | varies |
| 45° rotation | ~-24 dBsm | varies |

- **Broadside**: Maximum - wave hits full side of cylinder
- **End-on**: Minimum - wave hits small end cap

### Rotation Study

The cylinder shows **different RCS patterns** at different rotations:
- **0°**: Symmetric around theta=90°
- **30°**: Asymmetric - end-on direction has higher RCS
- **45°**: Maximum RCS shifted from broadside

This demonstrates that **non-spherical objects have angle-dependent RCS**.

**Visualize Cylinder Orientations:**
```bash
python3 cylinder_scattering.py --orientations
```

This generates `cylinder_orientations.png` showing the actual cylinder meshes at 0°, 30°, and 45° rotations, with the incident wave direction marked.

## Custom Parameters

### Generate Custom Mesh
```bash
python3 generate_cylinder.py --radius 0.05 --length 1.0 --rotation 45 --output custom.obj
```

### Run Custom Simulation
```bash
../build/raycs --mesh custom.obj --freq 5e9 --method po --theta-steps 72 --phi-steps 72 --output custom_rcs.csv
```

## Method Comparison

| Method | Command | Coverage | Best For |
|--------|---------|----------|---------|
| `po` | `--method po` | All angles | Validation, pattern analysis |
| `sbr` | `--method sbr` | Backscatter only | Complex targets, multiple bounces |

**Recommended**: Use `--method po` for full angular coverage.

## Notes

- Use `--method po` for full angular coverage (recommended)
- Use higher `--theta-steps` (e.g., 72 or 180) for smoother patterns
- The script auto-detects missing data and regenerates it
- Use `--no-auto-run` to skip RayCs execution (use existing data only)