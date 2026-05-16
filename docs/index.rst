Welcome to RayCs's documentation!
====================================

RayCs is a **computational electromagnetics** (CEM) tool for computing
**Radar Cross Section (RCS)** of arbitrary 3D targets using **Physical Optics
(PO)** and **Shooting & Bouncing Rays (SBR)** methods.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   installation
   usage
   api
   examples
   physics
   references


Features
========

* **Physical Optics (PO)** -- full angular coverage for monostatic and bistatic RCS
* **Shooting & Bouncing Rays (SBR)** -- backscatter with ray tracing
* **CGNS and OBJ mesh** input formats
* **SAH-based BVH** acceleration for ray-triangle intersection
* **OpenMP** shared-memory parallelism
* **MPI** distributed-memory parallelism (optional)
* **CSV output** with theta, phi, and RCS (total, VV, HH)
* **Python visualization scripts** for sphere and cylinder examples
