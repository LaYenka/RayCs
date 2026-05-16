"""Tests for visualization functions (non-interactive, output check only)."""

import matplotlib
matplotlib.use("Agg")

import raycs
from raycs.visualize import (
    plot_2d, plot_3d, plot_polar, plot_radiation_pattern,
    plot_rotation_comparison,
)


class TestVisualize:
    def test_plot_2d(self, small_solver):
        result = small_solver.run()
        fig = plot_2d(result)
        assert fig is not None
        assert len(fig.axes) >= 1

    def test_plot_2d_with_ax(self, small_solver):
        import matplotlib.pyplot as plt
        result = small_solver.run()
        _, ax = plt.subplots()
        fig = plot_2d(result, ax=ax)
        assert fig is not None

    def test_plot_2d_custom_phi(self, small_solver):
        result = small_solver.run()
        fig = plot_2d(result, phi_cut=90)
        assert fig is not None

    def test_plot_3d(self, small_solver):
        result = small_solver.run()
        fig = plot_3d(result)
        assert fig is not None

    def test_plot_3d_with_incident(self, small_solver):
        result = small_solver.run()
        fig = plot_3d(result, show_incident=True)
        assert fig is not None

    def test_plot_polar(self, small_solver):
        result = small_solver.run()
        fig = plot_polar(result)
        assert fig is not None

    def test_plot_radiation_pattern(self, small_solver):
        result = small_solver.run()
        fig = plot_radiation_pattern(result)
        assert fig is not None

    def test_plot_rotation_comparison(self, small_solver):
        result = small_solver.run()
        fig = plot_rotation_comparison({"test": result})
        assert fig is not None

    def test_plot_rotation_comparison_theta(self, small_solver):
        result = small_solver.run()
        fig = plot_rotation_comparison({"test": result}, theta_cut=True)
        assert fig is not None

    def test_result_plot_methods(self, small_solver):
        """RCSResult.plot_* should work."""
        result = small_solver.run()
        fig = result.plot_2d()
        assert fig is not None
        fig = result.plot_3d()
        assert fig is not None
        fig = result.plot_polar()
        assert fig is not None

    def test_plot_with_tuple(self):
        """Should accept (theta, phi, rcs) tuples."""
        import numpy as np
        theta = np.linspace(0, 180, 37)
        phi = np.zeros_like(theta)
        rcs = -10 * np.ones_like(theta)
        fig = plot_2d((theta, phi, rcs))
        assert fig is not None

    def test_plot_saves_png(self, small_solver, tmp_path):
        import os
        result = small_solver.run()
        path = os.path.join(str(tmp_path), "test.png")
        fig = result.plot_2d()
        fig.savefig(path)
        assert os.path.exists(path)
