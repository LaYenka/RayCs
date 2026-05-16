Physics Background
==================

Radar Cross Section
-------------------

Radar Cross Section (RCS) is a measure of how detectable an object is by radar.
It is defined as the equivalent area that would produce the same scattered power
as an isotropic scatterer:

.. math::

   \sigma = \lim_{R\to\infty} 4\pi R^2 \frac{|\mathbf{E}_\text{scat}|^2}{|\mathbf{E}_\text{inc}|^2}

RCS is typically expressed in dBsm (decibels relative to one square meter):

.. math::

   \sigma_\text{dBsm} = 10 \log_{10}(\sigma)

Coordinate System
-----------------

Observation angles are defined in the standard spherical coordinate system:

* :math:`\theta` (theta): elevation angle from :math:`+Z` axis (0\ :math:`^\circ` to 180\ :math:`^\circ`)
* :math:`\phi` (phi): azimuth angle around :math:`Z` axis (0\ :math:`^\circ` to 360\ :math:`^\circ`)

.. code-block:: text

                    +Z (incident wave)
                    |
                    |
                    |    theta
                    |
                    |
                    O---------> X
                   /
                  / phi
                 /
                Y

Physical Optics (PO)
--------------------

Physical Optics approximates scattering from PEC targets using the
tangent-plane approximation. The equivalent surface current is:

.. math::

   \mathbf{J}_s = 2\; \hat{n} \times \mathbf{H}_\text{inc}

where :math:`\hat{n}` is the surface normal and :math:`\mathbf{H}_\text{inc}`
is the incident magnetic field. The scattered far-field is:

.. math::

   \mathbf{E}_\text{scat} = \frac{jk}{4\pi} \sum_{i=1}^{N} \mathbf{J}_{s,i} \, e^{jk\hat{r}\cdot\mathbf{r}'_i} \Delta A_i

where:

* :math:`k = 2\pi/\lambda` is the wavenumber
* :math:`\hat{r}` is the observation direction
* :math:`\mathbf{r}'_i` is the centroid of triangle :math:`i`
* :math:`\Delta A_i` is the area of triangle :math:`i`

PO provides full angular coverage but ignores edge diffraction and multiple
reflections.

Shooting & Bouncing Rays (SBR)
------------------------------

SBR traces rays from a launch plane toward the target. Each ray represents a
tube of the incident plane wave. The ray-object intersection is found using
the BVH, and the scattered field is accumulated:

.. math::

   \mathbf{E}_\text{scat} = \sum_\text{rays} \mathbf{J}_s \, e^{jk(\hat{r} \cdot \mathbf{r}')} \Delta A

SBR captures multiple reflections (ray bouncing) but only produces
backscatter contributions. It is complementary to PO for complex targets.

BVH Acceleration
----------------

The Bounding Volume Hierarchy (BVH) accelerates ray-triangle intersection
queries using SAH (Surface Area Heuristic) binning. Each BVH node stores an
AABB; leaves contain up to 4 triangles. The Möller-Trumbore algorithm is used
for per-triangle intersection.

Polarization
------------

RCS is computed for two linear polarizations:

* **VV**: Vertical transmit, vertical receive. The incident field is
  :math:`\mathbf{E}_\text{inc} = \hat{\mathbf{e}}_\theta` and the scattered
  field is projected onto :math:`\hat{\mathbf{e}}_\theta`.
* **HH**: Horizontal transmit, horizontal receive. The scattered field is
  projected onto :math:`\hat{\mathbf{e}}_\phi`.

Monostatic vs Bistatic
----------------------

* **Monostatic** (default): The observation direction is the negative of
  the incident direction. The incident wave comes from :math:`+Z` and the
  receiver is co-located with the transmitter.
* **Bistatic**: The incident wave direction is fixed
  (:math:`\theta_\text{inc}`, :math:`\phi_\text{inc}`) and the scattered
  field is computed at all observation angles.
