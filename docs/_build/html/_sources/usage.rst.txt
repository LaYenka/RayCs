Command-Line Usage
==================

Synopsis
--------

.. code-block:: bash

   raycs --mesh <file> [options]

Required Arguments
------------------

.. option:: --mesh <file>

   Input mesh file path. Supports CGNS (``.cgns``, ``.h5``) and Wavefront OBJ
   (``.obj``) formats. Auto-detected from extension.

Options
-------

.. option:: --freq <Hz>

   Frequency in Hertz. Default: ``10e9``.

.. option:: --method <po|sbr|both>

   Scattering method:

   * ``po`` -- Physical Optics (full angular coverage)
   * ``sbr`` -- Shooting & Bouncing Rays (backscatter only)
   * ``both`` -- PO + SBR combined

   Default: ``sbr``.

.. option:: --bounces <N>

   Maximum number of ray bounces for SBR. Default: ``3``.

.. option:: --ray-density <N>

   Rays per wavelength for SBR ray grid. Higher values increase resolution but
   reduce performance. Default: ``10``.

Observation Angles
~~~~~~~~~~~~~~~~~~

.. option:: --theta-min <deg>

   Starting theta angle in degrees. Default: ``0``.

.. option:: --theta-max <deg>

   Ending theta angle in degrees. Default: ``180``.

.. option:: --theta-steps <N>

   Number of theta steps. Default: ``180``.

.. option:: --phi-min <deg>

   Starting phi angle in degrees. Default: ``0``.

.. option:: --phi-max <deg>

   Ending phi angle in degrees. Default: ``360``.

.. option:: --phi-steps <N>

   Number of phi steps. Default: ``360``.

Scattering Mode
~~~~~~~~~~~~~~~

.. option:: --bistatic

   Enable bistatic mode. In bistatic mode the incident wave direction is
   fixed and the scattered field is computed at all observation angles.
   By default monostatic mode is used (incident direction = :math:`-` observation direction).

.. option:: --inc-theta <deg>

   Incident direction theta for bistatic mode. Default: ``0``.

.. option:: --inc-phi <deg>

   Incident direction phi for bistatic mode. Default: ``0``.

Output
~~~~~~

.. option:: --output <file>

   Output CSV file path. Default: ``rcs.csv``.

Other
~~~~~

.. option:: --help

   Print usage information and exit.

Examples
--------

.. code-block:: bash

   # Monostatic PO with default parameters
   raycs --mesh target.obj --freq 3e9 --method po

   # Monostatic SBR with custom angles
   raycs --mesh target.obj --freq 10e9 --method sbr \
       --theta-steps 90 --phi-steps 180

   # Bistatic PO with fixed incident direction
   raycs --mesh target.obj --freq 3e9 --method po --bistatic \
       --inc-theta 45 --inc-phi 0

   # Both methods combined
   raycs --mesh target.obj --freq 3e9 --method both

   # High-resolution with custom output
   raycs --mesh target.obj --freq 10e9 --method po \
       --theta-steps 360 --phi-steps 360 --output results.csv

Output Format
-------------

The CSV output has the following columns:

.. code-block:: text

   theta_deg, phi_deg, RCS_total_dBsm, RCS_VV_dBsm, RCS_HH_dBsm

Each row corresponds to one observation angle pair :math:`(\theta, \phi)`.
RCS values are in dBsm (decibels relative to one square meter).

Polarization conventions:

* **VV**: Vertical transmit, vertical receive (:math:`E_\theta`)
* **HH**: Horizontal transmit, horizontal receive (:math:`E_\phi`)
* **Total**: :math:`\sigma_\text{total} = \sigma_\text{VV} + \sigma_\text{HH}`

MPI Parallelism
---------------

When compiled with MPI support, observation angles are distributed across
ranks. Run with:

.. code-block:: bash

   mpirun -np 4 raycs --mesh target.obj --freq 3e9 --method sbr
