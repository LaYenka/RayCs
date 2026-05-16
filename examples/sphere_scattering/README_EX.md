# Sphere Scattering Example for RayCs

This example demonstrates electromagnetic scattering from a PEC (Perfect Electric Conductor) sphere using RayCs, validated against Mie theory.

## Quick Start

```bash
cd /opt/dev/RayCs/examples/sphere_scattering
python3 sphere_scattering.py
```

This script automatically:
1. Generates sphere meshes at 0°, 30°, 45° rotations (if needed)
2. Runs RayCs PO simulations for each rotation
3. Generates comparison plots validating axisymmetric behavior

## Generated Files

| File | Description |
|------|-------------|
| `sphere_0deg.obj`, `sphere_30deg.obj`, `sphere_45deg.obj` | Rotated sphere meshes |
| `rcs_0deg.csv`, `rcs_30deg.csv`, `rcs_45deg.csv` | RCS data at each rotation |
| `sphere_rotation_comparison.png` | All rotations overlap (axisymmetric) |
| `sphere_validation.png` | PO results vs Mie theory |
| `sphere_orientations.png` | 3D visualization of mesh orientations |
| `sphere_rcs_pattern.png` | Combined 2D, 3D, polar plots |

## Command-Line Options

```bash
# 3D pattern only
python3 sphere_scattering.py --method 3d

# Polar plot only
python3 sphere_scattering.py --method polar

# Validation (PO vs Mie theory)
python3 sphere_scattering.py --validation

# Show mesh orientations
python3 sphere_scattering.py --orientations

# Use existing data (skip RayCs run)
python3 sphere_scattering.py --no-auto-run
```

## Axisymmetric Validation

The sphere is **axisymmetric** - rotating the mesh should NOT change the RCS pattern.
All three rotations (0°, 30°, 45°) produce identical results, confirming correct physics.

```
Difference 0° vs 30°: < 0.1 dB
Difference 0° vs 45°: < 0.1 dB
```

## Physics Background

### Incident Wave Direction

In **monostatic mode**, the plane wave is incident from **+Z direction**:

```
                    +Z (incident wave)
                     |
                     |
                     |      theta = 0°
                     |
                     |
                     O--------+X
```

### PEC Sphere Parameters

| Parameter | Value |
|-----------|-------|
| Radius | 10 cm |
| Frequency | 3 GHz |
| Wavelength | 10 cm |
| ka | 6.28 (optical region) |
| Geometric cross-section | πr² = 0.0314 m² |
| RCS (Mie theory) | ~-15 dBsm |
| RCS (PO simulation) | ~-15 to -17 dBsm |

### PO vs Mie Theory

Physical Optics approximates scattering using tangent plane assumption.
For a sphere, PO slightly underestimates RCS compared to exact Mie theory.
This is expected because PO ignores edge diffraction and creeping waves.

## Manual Simulation

```bash
# Build RayCs
cd /opt/dev/RayCs/build && cmake .. && make

# Run PO simulation
../build/raycs --mesh ../examples/sphere_scattering/sphere_0deg.obj \
    --freq 3e9 --theta-steps 36 --phi-steps 36 --method po \
    --output ../examples/sphere_scattering/rcs_0deg.csv
```

## Notes

- Sphere RCS is **axisymmetric** (same at all observation angles)
- Small differences (<0.1 dB) between rotations are numerical noise
- PO gives full angular coverage
- Expected value: ~-15 dBsm (matches Mie theory)
