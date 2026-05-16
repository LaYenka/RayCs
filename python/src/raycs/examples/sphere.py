#!/usr/bin/env python3
"""
Sphere scattering example using the RayCs Python API.
Validates axisymmetric behavior of a PEC sphere.
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import raycs
from raycs.visualize import plot_rotation_comparison


def main():
    radius = 0.1  # 10 cm
    frequency = 3e9  # 3 GHz

    print("Sphere RCS Simulation")
    print("=" * 40)
    print(f"Radius: {radius*100:.0f} cm")
    print(f"Frequency: {frequency/1e9:.1f} GHz")
    print(f"ka = {2*np.pi*radius*frequency/299792458:.2f}")
    print()

    rotations = [0, 30, 45]
    results = {}

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ex_dir = os.path.join(os.path.dirname(script_dir), "..", "..", "..",
                          "examples", "sphere_scattering")

    for rot in rotations:
        mesh_file = os.path.join(ex_dir, f"sphere_{rot}deg.obj")
        if not os.path.exists(mesh_file):
            print(f"Mesh not found: {mesh_file}")
            print("Run generate_sphere.py first")
            continue

        print(f"Running simulation for {rot}° rotation...")
        solver = raycs.Solver(
            mesh_file=mesh_file,
            frequency=frequency,
            method="po",
            theta_steps=36,
            phi_steps=36,
        )
        result = solver.run()
        if result:
            results[str(rot)] = result
            max_rcs = np.max(result.rcs_total_db)
            print(f"  Max RCS: {max_rcs:.2f} dBsm")
        else:
            print("  (non-root MPI rank, no result)")

    if results and len(results) > 1:
        print("\nGenerating rotation comparison...")
        fig = plot_rotation_comparison(results, title="Sphere Axisymmetry Validation")
        out = os.path.join(script_dir, "sphere_comparison_py.png")
        fig.savefig(out, dpi=150)
        print(f"Saved: {out}")


if __name__ == "__main__":
    main()
