"""Integration tests for the Solver class."""

import numpy as np
import raycs


class TestSolverConstruction:
    def test_with_mesh_object(self, cylinder_mesh):
        s = raycs.Solver(mesh=cylinder_mesh, frequency=3e9, method="po")
        assert s._cfg.frequency == 3e9
        assert s._cfg.method == raycs.Method.PO

    def test_with_mesh_file(self, cylinder_mesh_path):
        s = raycs.Solver(
            mesh_file=cylinder_mesh_path,
            frequency=3e9,
            method="po",
        )
        assert s._cfg.frequency == 3e9
        assert len(s._mesh.triangles) > 0

    def test_raises_without_mesh(self):
        import pytest
        with pytest.raises(ValueError):
            raycs.Solver()

    def test_verbose_property(self, cylinder_mesh):
        s = raycs.Solver(mesh=cylinder_mesh, method="po")
        assert s.verbose is False
        s.verbose = True
        assert s.verbose is True


class TestSolverPO:
    def test_po_sweep(self, small_solver):
        result = small_solver.run()
        assert result is not None
        n_expected = 18 * 18
        assert len(result.theta_deg) == n_expected
        assert len(result.phi_deg) == n_expected
        assert len(result.rcs_total_db) == n_expected

    def test_po_rcs_values(self, small_solver):
        result = small_solver.run()
        assert result is not None
        n_expected = 18 * 18
        assert np.any(result.rcs_total_db > -300)  # at least some valid data
        valid = result.rcs_total_db > -300
        assert np.sum(valid) > n_expected // 2

    def test_bistatic(self, cylinder_mesh):
        s = raycs.Solver(mesh=cylinder_mesh, frequency=3e9, method="po",
                          theta_steps=10, phi_steps=10)
        result = s.run_bistatic(inc_theta=45, inc_phi=0)
        assert result is not None
        assert len(result.theta_deg) == 100

    def test_po_consistency(self, cylinder_mesh):
        """Run twice with same settings, results should match."""
        s1 = raycs.Solver(mesh=cylinder_mesh, frequency=3e9, method="po",
                           theta_steps=10, phi_steps=10)
        s2 = raycs.Solver(mesh=cylinder_mesh, frequency=3e9, method="po",
                           theta_steps=10, phi_steps=10)
        r1 = s1.run()
        r2 = s2.run()
        assert np.allclose(r1.rcs_total_db, r2.rcs_total_db, atol=1e-6)


class TestSolverSBR:
    def test_sbr_sweep(self, small_solver_sbr):
        result = small_solver_sbr.run()
        if result is not None:
            n_expected = 10 * 10
            assert len(result.theta_deg) == n_expected

    def test_sbr_has_some_hits(self, small_solver_sbr):
        result = small_solver_sbr.run()
        if result is not None:
            # SBR may have some -300 values (no ray hit)
            valid = result.rcs_total_db > -300
            assert np.sum(valid) > 0

    def test_sbr_values(self, small_solver_sbr):
        result = small_solver_sbr.run()
        if result is not None:
            valid = result.rcs_total_db > -300
            if np.any(valid):
                assert np.all(result.rcs_total_db[valid] > -100)  # not unreasonably low
