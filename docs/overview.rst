Overview
========

RayCs computes the monostatic or bistatic Radar Cross Section of arbitrary 3D
targets. The incident plane wave propagates from the :math:`+Z` direction toward
the origin by default.

Two scattering methods are implemented:

.. list-table::
   :header-rows: 1

   * - Method
     - Description
     - Coverage
     - Best For
   * - **PO** (Physical Optics)
     - Surface current integration, tangent-plane approximation
     - All observation angles
     - Smooth PEC targets, validation
   * - **SBR** (Shooting & Bouncing Rays)
     - Ray tracing with geometric optics
     - Backscatter only (monostatic)
     - Complex geometries, multiple reflections
   * - **BOTH**
     - PO + SBR combined
     - All angles (PO) + multiple bounces (SBR)
     - General purpose

Project Structure
-----------------

.. code-block:: text

   RayCs/
   ├── src/
   │   ├── main.cpp          # Entry point and CLI parsing
   │   ├── config.hpp        # Configuration struct
   │   ├── vec3.hpp          # 3D vector math
   │   ├── mat3.hpp          # 3x3 matrix math
   │   ├── mesh.hpp          # Mesh and triangle data structures
   │   ├── ray.hpp           # Ray definition
   │   ├── bvh.{hpp,cpp}    # BVH acceleration structure
   │   ├── cgns_mesh.{hpp,cpp}  # Mesh loading (CGNS + OBJ)
   │   ├── po.{hpp,cpp}     # Physical Optics scattering
   │   ├── sbr.{hpp,cpp}    # Shooting & Bouncing Rays
   │   └── rcs.{hpp,cpp}    # RCS computation and CSV output
   ├── examples/
   │   ├── sphere_scattering/  # Sphere validation example
   │   └── cylinder_scattering/ # Cylinder rotation study
   ├── build/                  # Build output directory
   └── docs/                   # Sphinx documentation
