"""Tests for RCSResult class."""

import os
import tempfile
import numpy as np
import raycs


class TestRCSResult:
    def test_result_attributes(self, small_solver):
        result = small_solver.run()
        assert result is not None
        assert hasattr(result, "theta_deg")
        assert hasattr(result, "phi_deg")
        assert hasattr(result, "rcs_total_db")
        assert hasattr(result, "rcs_vv_db")
        assert hasattr(result, "rcs_hh_db")
        # All arrays should be numpy float64
        assert result.theta_deg.dtype == np.float64
        assert result.rcs_total_db.dtype == np.float64

    def test_result_shape(self, small_solver):
        result = small_solver.run()
        n_expected = 18 * 18
        assert len(result.theta_deg) == n_expected
        assert len(result.phi_deg) == n_expected
        assert len(result.rcs_total_db) == n_expected
        assert len(result.rcs_vv_db) == n_expected
        assert len(result.rcs_hh_db) == n_expected

    def test_result_bool(self, small_solver):
        result = small_solver.run()
        assert bool(result) is True

    def test_empty_result_bool(self):
        r = raycs.RCSResult()
        assert bool(r) is False

    def test_to_numpy(self, small_solver):
        result = small_solver.run()
        arr = result.to_numpy()
        assert arr.dtype.names == ("theta_deg", "phi_deg", "rcs_total_db",
                                    "rcs_vv_db", "rcs_hh_db")
        assert len(arr) == 18 * 18

    def test_to_csv(self, small_solver):
        result = small_solver.run()
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="r", delete=False) as f:
            path = f.name
        result.to_csv(path)
        try:
            with open(path) as f:
                lines = f.readlines()
            assert len(lines) == 18 * 18 + 1  # header + data
            header = lines[0].strip().split(",")
            assert header == ["theta_deg", "phi_deg", "RCS_total_dBsm",
                              "RCS_VV_dBsm", "RCS_HH_dBsm"]
            # Check data row
            row = lines[1].strip().split(",")
            assert len(row) == 5
            float(row[2])  # should parse
        finally:
            os.unlink(path)

    def test_to_csv_empty_raises(self):
        r = raycs.RCSResult()
        import pytest
        with pytest.raises(ValueError):
            r.to_csv("/tmp/nonexistent.csv")

    def test_rcs_values_reasonable(self, small_solver):
        result = small_solver.run()
        # Cylinder at 3 GHz should not have extreme values
        valid = result.rcs_total_db > -300
        if np.any(valid):
            assert np.all(result.rcs_total_db[valid] > -60)
            assert np.all(result.rcs_total_db[valid] < 20)
