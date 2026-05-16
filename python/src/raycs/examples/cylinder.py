#!/usr/bin/env python3
"""
Cylinder scattering example using the RayCs Python API.
Demonstrates rotation-dependent RCS of a non-spherical target.
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import raycs
from raycs.visualize import plot_rotation_comparison, plot_radiation_pattern


def main():
    frequency = 3e9  # 3 GHz

    print("Cylinder RCS Simulation")
    print("=" * 40)
    print(f"Frequency: {frequency/1e9:.1f} GHz")
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ex_dir = os.path.join(os.path.dirname(script_dir), "..", "..", "..",
                          "examples", "cylinder_scattering")

    # Single rotation examples
    for rot in [0, 30]:
        mesh_file = os.path.join(ex_dir, f"cylinder_{rot}deg.obj")
        if not os.path.exists(mesh_file):
            print(f"Mesh not found: {mesh_file}")
            continue

        print(f"\nCylinder at {rot}° rotation:")
        solver = raycs.Solver(
            mesh_file=mesh_file,
            frequency=frequency,
            method="po",
            theta_steps=36,
            phi_steps=36,
        )
        result = solver.run()
        if result:
            max_rcs = np.max(result.rcs_total_db)
            print(f"  Max RCS: {max_rcs:.2f} dBsm")
            fig = plot_radiation_pattern(result, title=f"Rotation {rot}°")
            out = os.path.join(script_dir, f"cylinder_{rot}deg_py.png")
            fig.savefig(out, dpi=150)
            print(f"  Saved: {out}")


if __name__ == "__main__":
    main()
