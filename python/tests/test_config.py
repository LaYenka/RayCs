"""Tests for Config struct and Method enum."""

import raycs


class TestConfig:
    def test_default_values(self):
        cfg = raycs.Config()
        assert cfg.frequency == 10e9
        assert cfg.max_bounces == 3
        assert cfg.ray_density == 10.0
        assert cfg.theta_min == 0.0
        assert cfg.theta_max == 180.0
        assert cfg.theta_steps == 180
        assert cfg.phi_min == 0.0
        assert cfg.phi_max == 360.0
        assert cfg.phi_steps == 360
        assert cfg.method == raycs.Method.SBR
        assert cfg.bistatic is False
        assert cfg.inc_theta == 0.0
        assert cfg.inc_phi == 0.0
        assert cfg.verbose is False
        assert cfg.output_file == "rcs.csv"

    def test_set_and_get(self):
        cfg = raycs.Config()
        cfg.frequency = 3e9
        cfg.theta_steps = 36
        cfg.phi_steps = 72
        cfg.method = raycs.Method.PO
        cfg.verbose = True
        assert cfg.frequency == 3e9
        assert cfg.theta_steps == 36
        assert cfg.phi_steps == 72
        assert cfg.method == raycs.Method.PO
        assert cfg.verbose is True


class TestMethod:
    def test_enum_values(self):
        assert raycs.Method.PO == raycs.Method.PO
        assert raycs.Method.SBR == raycs.Method.SBR
        assert raycs.Method.BOTH == raycs.Method.BOTH
        assert raycs.Method.PO != raycs.Method.SBR

    def test_enum_from_string(self):
        method_map = {"po": raycs.Method.PO, "sbr": raycs.Method.SBR, "both": raycs.Method.BOTH}
        assert method_map["po"] == raycs.Method.PO
        assert method_map["sbr"] == raycs.Method.SBR
        assert method_map["both"] == raycs.Method.BOTH
