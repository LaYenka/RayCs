Examples
========

RayCs includes two validation examples for sphere and cylinder scattering.

Sphere Scattering
-----------------

The sphere example validates Physical Optics against analytical Mie theory.
A PEC sphere is axisymmetric -- rotating the mesh produces identical RCS.

.. code-block:: bash

   cd examples/sphere_scattering
   python3 sphere_scattering.py

This script automatically generates meshes at 0\ :math:`^\circ`, 30\ :math:`^\circ`,
and 45\ :math:`^\circ` rotations, runs RayCs for each, and produces comparison plots.

Generated files:

* ``sphere_0deg.obj``, ``sphere_30deg.obj``, ``sphere_45deg.obj`` -- rotated meshes
* ``rcs_0deg.csv``, ``rcs_30deg.csv``, ``rcs_45deg.csv`` -- RCS results
* ``sphere_rotation_comparison.png`` -- all rotations overlap (axisymmetric)
* ``sphere_validation.png`` -- PO vs Mie theory comparison
* ``sphere_orientations.png`` -- 3D mesh visualization

.. rubric:: Options

.. code-block:: bash

   # Validation plot (PO vs Mie theory)
   python3 sphere_scattering.py --validation

   # 3D pattern only
   python3 sphere_scattering.py --method 3d

   # Show mesh orientations
   python3 sphere_scattering.py --orientations

   # Use existing data, skip RayCs
   python3 sphere_scattering.py --no-auto-run

Cylinder Scattering
-------------------

The cylinder example demonstrates rotation-dependent RCS for a non-spherical
target. The cylinder has flat circular end caps with proper surface normals.

.. code-block:: bash

   cd examples/cylinder_scattering
   python3 cylinder_scattering.py

Generated files:

* ``cylinder_0deg.obj``, ``cylinder_30deg.obj``, ``cylinder_45deg.obj`` -- rotated meshes
* ``rcs_0deg.csv``, ``rcs_30deg.csv``, ``rcs_45deg.csv`` -- RCS results
* ``cylinder_rotation_comparison.png`` -- RCS varies with rotation angle
* ``cylinder_rcs_pattern.png`` -- combined 2D, 3D, polar plots
* ``cylinder_orientations.png`` -- 3D mesh visualization

.. rubric:: Options

.. code-block:: bash

   # 3D pattern
   python3 cylinder_scattering.py --method 3d

   # Rotation comparison only
   python3 cylinder_scattering.py --rotation all

   # Show mesh orientations
   python3 cylinder_scattering.py --orientations

   # Use existing data, skip RayCs
   python3 cylinder_scattering.py --no-auto-run
