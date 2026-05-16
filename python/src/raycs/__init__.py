"""
RayCs — Radar Cross Section computation using Physical Optics (PO)
and Shooting & Bouncing Rays (SBR).

Usage:
    >>> import raycs
    >>> s = raycs.Solver(mesh_file="target.obj", frequency=3e9, method="po")
    >>> result = s.run()
    >>> result.plot_3d()
"""

import numpy as np
from . import _core
from .visualize import plot_2d, plot_3d, plot_polar, plot_radiation_pattern, plot_rotation_comparison

__version__ = "0.1.0"

# Re-export core types and functions
Method = _core.Method
Vec3 = _core.Vec3
CVec3 = _core.CVec3
Mat3 = _core.Mat3
AABB = _core.AABB
Mesh = _core.Mesh
Triangle = _core.Triangle
Ray = _core.Ray
BVH = _core.BVH
HitRecord = _core.HitRecord
Config = _core.Config
POField = _core.POField
dot = _core.dot
cross = _core.cross
load_obj_mesh = _core.load_obj_mesh
load_cgns_mesh = _core.load_cgns_mesh
compute_po_scattering = _core.compute_po_scattering
compute_rcs = _core.compute_rcs


class RCSResult:
    """Container for RCS results with numpy arrays and convenience methods.

    Attributes:
        theta_deg (ndarray): Observation theta angles (degrees)
        phi_deg (ndarray): Observation phi angles (degrees)
        rcs_total_db (ndarray): Total RCS (dBsm)
        rcs_vv_db (ndarray): VV-polarized RCS (dBsm)
        rcs_hh_db (ndarray): HH-polarized RCS (dBsm)
    """

    def __init__(self, core_result=None, theta_deg=None, phi_deg=None,
                 rcs_total_db=None, rcs_vv_db=None, rcs_hh_db=None):
        if core_result is not None:
            self.theta_deg = np.array(core_result.theta_vals, dtype=np.float64)
            self.phi_deg = np.array(core_result.phi_vals, dtype=np.float64)
            self.rcs_total_db = np.array(core_result.rcs_total_db, dtype=np.float64)
            self.rcs_vv_db = np.array(core_result.rcs_vv_db, dtype=np.float64)
            self.rcs_hh_db = np.array(core_result.rcs_hh_db, dtype=np.float64)
        else:
            self.theta_deg = np.asarray(theta_deg, dtype=np.float64) if theta_deg is not None else np.array([])
            self.phi_deg = np.asarray(phi_deg, dtype=np.float64) if phi_deg is not None else np.array([])
            self.rcs_total_db = np.asarray(rcs_total_db, dtype=np.float64) if rcs_total_db is not None else np.array([])
            self.rcs_vv_db = np.asarray(rcs_vv_db, dtype=np.float64) if rcs_vv_db is not None else np.array([])
            self.rcs_hh_db = np.asarray(rcs_hh_db, dtype=np.float64) if rcs_hh_db is not None else np.array([])

    def __bool__(self):
        return len(self.theta_deg) > 0

    def to_csv(self, path):
        """Write RCS to CSV file."""
        if not self:
            raise ValueError("No RCS data to write")
        core_result = _core.RCSResult()
        core_result.theta_vals = self.theta_deg.tolist()
        core_result.phi_vals = self.phi_deg.tolist()
        core_result.rcs_total_db = self.rcs_total_db.tolist()
        core_result.rcs_vv_db = self.rcs_vv_db.tolist()
        core_result.rcs_hh_db = self.rcs_hh_db.tolist()
        _core.write_rcs_csv(path, core_result)

    def to_numpy(self):
        """Return structured numpy array with columns."""
        arr = np.zeros(len(self.theta_deg), dtype=[
            ("theta_deg", "f8"), ("phi_deg", "f8"),
            ("rcs_total_db", "f8"), ("rcs_vv_db", "f8"), ("rcs_hh_db", "f8"),
        ])
        arr["theta_deg"] = self.theta_deg
        arr["phi_deg"] = self.phi_deg
        arr["rcs_total_db"] = self.rcs_total_db
        arr["rcs_vv_db"] = self.rcs_vv_db
        arr["rcs_hh_db"] = self.rcs_hh_db
        return arr

    def plot_2d(self, phi_cut=0, **kwargs):
        """2D RCS cut at constant phi."""
        return plot_2d(self, phi_cut=phi_cut, **kwargs)

    def plot_3d(self, **kwargs):
        """3D radiation pattern."""
        return plot_3d(self, **kwargs)

    def plot_polar(self, **kwargs):
        """Polar radiation pattern."""
        return plot_polar(self, **kwargs)


class Solver:
    """High-level solver for RCS computation.

    Args:
        mesh: A Mesh object, or None if loading from mesh_file.
        mesh_file: Path to mesh file (.obj or .cgns).
        frequency: Frequency in Hz (default 10e9).
        method: Scattering method — "po", "sbr", or "both" (default "po").
        theta_steps: Number of theta steps (default 180).
        phi_steps: Number of phi steps (default 360).
        max_bounces: Max ray bounces for SBR (default 3).
        ray_density: Rays per wavelength for SBR (default 10).
        verbose: Print progress (default False).

    Usage:
        >>> s = Solver(mesh_file="target.obj", frequency=3e9, method="po")
        >>> result = s.run()
        >>> result.plot_3d()
    """

    def __init__(self, mesh=None, mesh_file=None, frequency=10e9,
                 method="po", theta_steps=180, phi_steps=360,
                 max_bounces=3, ray_density=10.0, verbose=False):
        # Load mesh
        if mesh is None and mesh_file is not None:
            if mesh_file.endswith(".obj"):
                mesh = _core.load_obj_mesh(mesh_file)
            else:
                mesh = _core.load_cgns_mesh(mesh_file)
        elif mesh is None:
            raise ValueError("Either mesh or mesh_file must be provided")
        self._mesh = mesh

        # Build BVH
        if self._mesh.triangles:
            self._bvh = _core.BVH()
            self._bvh.build(self._mesh.triangles)
        else:
            self._bvh = None

        # Build config
        method_map = {"po": Method.PO, "sbr": Method.SBR, "both": Method.BOTH}
        self._cfg = _core.Config()
        self._cfg.frequency = frequency
        self._cfg.method = method_map.get(method.lower(), Method.PO)
        self._cfg.theta_steps = theta_steps
        self._cfg.phi_steps = phi_steps
        self._cfg.max_bounces = max_bounces
        self._cfg.ray_density = ray_density
        self._cfg.verbose = verbose
        self._cfg.theta_min = 0.0
        self._cfg.theta_max = 180.0
        self._cfg.phi_min = 0.0
        self._cfg.phi_max = 360.0

    @property
    def verbose(self):
        return self._cfg.verbose

    @verbose.setter
    def verbose(self, val):
        self._cfg.verbose = bool(val)

    def run(self):
        """Run the simulation and return RCSResult.

        Returns RCSResult on rank 0, or None on non-root MPI ranks.
        """
        if self._bvh is None:
            raise RuntimeError("No mesh triangles loaded")

        method = self._cfg.method
        if method == Method.PO:
            core_result = _core.compute_po_sweep(self._bvh, self._cfg)
        elif method == Method.SBR:
            core_result = _core.compute_sbr_sweep(self._mesh, self._bvh, self._cfg)
        elif method == Method.BOTH:
            core_result = _core.compute_both_sweep(self._mesh, self._bvh, self._cfg)
        else:
            raise ValueError(f"Unknown method: {method}")

        if core_result.theta_vals:
            return RCSResult(core_result=core_result)
        return None  # non-root MPI rank

    def run_bistatic(self, inc_theta=0, inc_phi=0):
        """Run bistatic PO sweep."""
        self._cfg.bistatic = True
        self._cfg.inc_theta = inc_theta
        self._cfg.inc_phi = inc_phi
        self._cfg.method = Method.PO
        core_result = _core.compute_po_sweep(self._bvh, self._cfg)
        if core_result.theta_vals:
            return RCSResult(core_result=core_result)
        return None


def load_mesh(path):
    """Load a mesh from file (.obj or .cgns).

    Args:
        path: Path to mesh file.

    Returns:
        Mesh object.
    """
    if path.endswith(".obj"):
        return _core.load_obj_mesh(path)
    return _core.load_cgns_mesh(path)
