#!/bin/bash
#
# Sphere scattering example - complete workflow
#

set -e

echo "=========================================="
echo "Sphere Scattering RCS Simulation"
echo "=========================================="

# Parameters
SPHERE_RADIUS=0.1      # meters
FREQUENCY=3e9          # 3 GHz (X-band)
METHOD="sbr"           # or "po" or "both"
MAX_BOUNCES=2
RAY_DENSITY=10

# Derived
WAVELENGTH=$(python3 -c "print(${WAVELENGTH:-0.1})")

echo "Parameters:"
echo "  Sphere radius: $SPHERE_RADIUS m"
echo "  Frequency: $(echo "scale=1; $FREQUENCY/1e9" | bc) GHz"
echo "  Wavelength: $WAVELENGTH m"
echo "  Method: $METHOD"
echo "  Max bounces: $MAX_BOUNCES"
echo ""

# Step 1: Generate sphere mesh
echo "[1/4] Generating sphere mesh..."
if [ ! -f "sphere.obj" ]; then
    python3 -c "
import numpy as np
r = $SPHERE_RADIUS
n_theta, n_phi = 20, 40
vertices, faces = [], []
for i in range(n_theta + 1):
    for j in range(n_phi + 1):
        vertices.append((r*np.sin(np.pi*i/n_theta)*np.cos(2*np.pi*j/n_phi),
                        r*np.sin(np.pi*i/n_theta)*np.sin(2*np.pi*j/n_phi),
                        r*np.cos(np.pi*i/n_theta)))
for i in range(n_theta):
    for j in range(n_phi):
        p0, p1 = i*(n_phi+1)+j, i*(n_phi+1)+j+1
        p2, p3 = (i+1)*(n_phi+1)+j+1, (i+1)*(n_phi+1)+j
        faces.append((p0+1,p1+1,p2+1))
        faces.append((p0+1,p2+1,p3+1))
with open('sphere.obj', 'w') as f:
    f.write(f'# Sphere r={r}m\n')
    for v in vertices: f.write(f'v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n')
    for t in faces: f.write(f'f {t[0]} {t[1]} {t[2]}\n')
print(f'Created: {len(vertices)}V, {len(faces)}F')
"
fi

# Step 2: Convert OBJ to CGNS (requires meshio)
echo "[2/4] Converting OBJ to CGNS..."
if command -v meshio &> /dev/null; then
    python3 -c "
import meshio
mesh = meshio.read('sphere.obj')
meshio.write('sphere.cgns', mesh)
print('Converted to CGNS')
"
else
    echo "Warning: meshio not installed. Using OBJ directly."
    echo "To convert: pip install meshio && meshio convert sphere.obj sphere.cgns"
    # Create symlink for testing
    ln -sf sphere.obj sphere.cgns 2>/dev/null || true
fi

# Step 3: Run RayCs
echo "[3/4] Running RayCs simulation..."
cd ../..

RAYCS_EXE="${RAYCS_EXE:-./raycs}"

if [ -f "$RAYCS_EXE" ]; then
    $RAYCS_EXE \
        --mesh "examples/sphere_scattering/sphere.cgns" \
        --freq $FREQUENCY \
        --method $METHOD \
        --bounces $MAX_BOUNCES \
        --ray-density $RAY_DENSITY \
        --theta-min 0 --theta-max 180 --theta-steps 90 \
        --phi-min 0 --phi-max 360 --phi-steps 180 \
        --output "examples/sphere_scattering/rcs.csv"
    
    echo "RCS computation complete!"
else
    echo "Error: RayCs executable not found at $RAYCS_EXE"
    echo "Build with: g++ -std=c++17 -O3 -fopenmp -DUSE_MPI=0 -Isrc src/*.cpp -lcgns -o raycs"
    exit 1
fi

# Step 4: Plot results
echo "[4/4] Plotting results..."
cd examples/sphere_scattering
python3 plot_rcs.py rcs.csv --method 3d -o rcs_pattern.png

echo ""
echo "=========================================="
echo "Done! Results:"
echo "  - RCS data: rcs.csv"
echo "  - Plot: rcs_pattern.png"
echo "=========================================="
