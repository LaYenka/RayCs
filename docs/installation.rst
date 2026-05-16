Installation
============

Requirements
------------

* CMake >= 3.16
* C++17 compiler (GCC >= 8, Clang >= 7, MSVC >= 2019)
* OpenMP (required)
* CGNS library (required)
* MPI (optional, for distributed parallelism)

Building
--------

.. code-block:: bash

   cd /opt/dev/RayCs
   mkdir -p build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   make -j$(nproc)

The executable is created at ``build/raycs``.

Build Options
~~~~~~~~~~~~~

.. code-block:: bash

   # Debug build
   cmake .. -DCMAKE_BUILD_TYPE=Debug

   # With MPI support
   cmake .. -DCMAKE_BUILD_TYPE=Release -DUSE_MPI=ON

Dependencies
------------

Ubuntu / Debian
~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo apt install build-essential cmake libomp-dev libcgns-dev

macOS (Homebrew)
~~~~~~~~~~~~~~~~

.. code-block:: bash

   brew install cmake libomp cgns

Python (Examples)
-----------------

The example scripts require:

.. code-block:: bash

   pip install numpy matplotlib

Verifying the Build
-------------------

.. code-block:: bash

   ../build/raycs --help
