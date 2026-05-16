API Reference
=============

Data Structures
---------------

Vec3
~~~~

.. code-block:: cpp

   struct Vec3 {
       double x, y, z;
       Vec3();
       Vec3(double x, double y, double z);
       Vec3 operator+(const Vec3& rhs) const;
       Vec3 operator-(const Vec3& rhs) const;
       Vec3 operator*(double s) const;
       Vec3 operator/(double s) const;
       Vec3 operator-() const;
       double dot(const Vec3& rhs) const;
       Vec3 cross(const Vec3& rhs) const;
       double norm() const;
       double norm_sq() const;
       Vec3 normalized() const;
       Vec3 reflect(const Vec3& normal) const;
   };

Basic 3D vector with standard linear algebra operations.

CVec3
~~~~~

.. code-block:: cpp

   struct CVec3 {
       complex<double> x, y, z;
       double mag_sq() const;
   };

Complex 3D vector for electromagnetic field quantities.

Mat3
~~~~

.. code-block:: cpp

   struct Mat3 {
       double m[3][3];
       static Mat3 identity();
       static Mat3 rotation(const Vec3& axis, double angle);
       Vec3 mul(const Vec3& v) const;
   };

3x3 transformation matrix with rotation and identity operations.

Ray
~~~

.. code-block:: cpp

   struct Ray {
       Vec3 origin;
       Vec3 direction;
       CVec3 E_field;
       double phase;
       int bounce_count;
       bool active;
   };

Ray representation for SBR with electromagnetic field tracking.

Triangle
~~~~~~~~

.. code-block:: cpp

   struct Triangle {
       Vec3 v0, v1, v2;    // vertices
       Vec3 normal;         // unit normal
       Vec3 centroid;       // center point
       double area;         // surface area
       int global_index;    // unique identifier
   };

Triangle geometry with precomputed normal, centroid, and area.

AABB
~~~~

.. code-block:: cpp

   struct AABB {
       Vec3 min_pt, max_pt;
       void expand(const Vec3& p);
       void expand(const AABB& o);
       double surface_area() const;
       Vec3 center() const;
       bool intersects_ray(const Vec3& origin, const Vec3& dir) const;
       bool intersects_ray_maxt(const Vec3& origin, const Vec3& dir, double max_t) const;
   };

Axis-aligned bounding box for BVH nodes.

Mesh
~~~~

.. code-block:: cpp

   struct Mesh {
       vector<Triangle> triangles;
       AABB bounds;
       void compute_bounds();
   };

Triangle mesh container with bounding box.

HitRecord
~~~~~~~~~

.. code-block:: cpp

   struct HitRecord {
       double t;             // ray parameter at hit
       double u, v;          // barycentric coordinates
       int tri_index;        // triangle index
       bool hit;             // whether a hit occurred
   };

Ray-triangle intersection result.

BVH
~~~

.. code-block:: cpp

   class BVH {
   public:
       BVH();
       void build(vector<Triangle>& triangles, int max_leaf = 4);
       HitRecord closest_hit(const Vec3& origin, const Vec3& dir) const;
       bool any_hit(const Vec3& origin, const Vec3& dir, double max_t) const;
       const vector<BVHNode>& nodes() const;
       const vector<Triangle>& triangles() const;
       size_t serialized_size() const;
       void serialize(char* buffer) const;
       void deserialize(const char* buffer);
   };

Bounding Volume Hierarchy with SAH (Surface Area Heuristic) construction.
Uses the Möller-Trumbore ray-triangle intersection algorithm.

Config
~~~~~~

.. code-block:: cpp

   enum class Method { PO, SBR, BOTH };

   struct Config {
       string mesh_file;
       string output_file = "rcs.csv";
       double frequency = 10e9;
       int max_bounces = 3;
       double ray_density = 10.0;
       double theta_min = 0, theta_max = 180;
       int theta_steps = 180;
       double phi_min = 0, phi_max = 360;
       int phi_steps = 360;
       Method method = Method::SBR;
       bool bistatic = false;
       double inc_theta = 0.0, inc_phi = 0.0;
   };

Configuration struct populated from command-line arguments.

Mesh Loading
------------

.. code-block:: cpp

   Mesh load_cgns_mesh(const string& filename);
   Mesh load_obj_mesh(const string& filename);

Load CGNS or Wavefront OBJ mesh files. Quadrilateral faces are split into
two triangles. Returns a :cpp:class:`Mesh` with computed bounds.

Physical Optics
---------------

.. code-block:: cpp

   struct POField {
       complex<double> E_theta;
       complex<double> E_phi;
   };

   POField compute_po_scattering(
       const BVH& bvh,
       const Config& cfg,
       const Vec3& inc_dir,
       const Vec3& obs_dir
   );

Computes the Physical Optics scattered field for a single incident-observation
direction pair. Uses the tangent-plane approximation with equivalent surface
currents:

.. math::

   \mathbf{J}_s = 2\; \hat{n} \times \mathbf{H}_\text{inc}

   \mathbf{E}_\text{scat} = \frac{jk}{4\pi} \sum_i \mathbf{J}_{s,i} e^{jk\hat{r}\cdot\mathbf{r}'_i} \Delta A_i

Shooting & Bouncing Rays
------------------------

.. code-block:: cpp

   struct SBRResult {
       vector<double> theta_vals;
       vector<double> phi_vals;
       vector<complex<double>> field_vv;
       vector<complex<double>> field_hh;
   };

   SBRResult compute_sbr_scattering(
       const Mesh& mesh,
       const BVH& bvh,
       const Config& cfg,
       int rank,
       int world_size
   );

Performs SBR for monostatic RCS. Rays are launched from a plane perpendicular
to the incident direction, traced through the BVH, and field contributions are
accumulated with phase.

RCS Computation
---------------

.. code-block:: cpp

   struct RCSResult {
       vector<double> theta_vals;
       vector<double> phi_vals;
       vector<double> rcs_total_db;
       vector<double> rcs_vv_db;
       vector<double> rcs_hh_db;
   };

   RCSResult compute_rcs(
       const Config& cfg,
       const vector<complex<double>>& field_vv,
       const vector<complex<double>>& field_hh,
       const vector<double>& theta_vals,
       const vector<double>& phi_vals
   );

   void write_rcs_csv(const string& filename, const RCSResult& result);

Converts scattered fields to RCS in dBsm:

.. math::

   \sigma = \frac{4\pi |E_\text{scat}|^2}{k^2 |E_\text{inc}|^2}

   \sigma_\text{dBsm} = 10 \log_{10}(\sigma)

The CSV writer produces 5-column output with headers.
