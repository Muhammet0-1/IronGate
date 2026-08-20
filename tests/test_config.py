from __future__ import annotations

import math
import unittest

from irongate_lab.config import (
    EndpointConfig,
    ScenarioConfig,
    SimulatorConfig,
    normalize_loopback_host,
)
from irongate_lab.errors import ConfigurationError


class EndpointConfigTests(unittest.TestCase):
    def test_normalizes_localhost_and_loopback_addresses(self) -> None:
        self.assertEqual(normalize_loopback_host(" localhost "), "127.0.0.1")
        self.assertEqual(normalize_loopback_host(" 127.0.0.1 "), "127.0.0.1")

    def test_accepts_ipv4_and_ipv6_loopback(self) -> None:
        self.assertEqual(EndpointConfig(host="127.0.0.2").host, "127.0.0.2")
        self.assertEqual(EndpointConfig(host="::1").label, "[::1]:5020")

    def test_rejects_non_loopback_and_hostnames(self) -> None:
        for host in ("192.0.2.1", "0.0.0.0", "example.com", "", " ::1%lo "):
            with self.subTest(host=host), self.assertRaises(ConfigurationError):
                EndpointConfig(host=host)

    def test_validates_port_device_and_timeout(self) -> None:
        invalid = (
            {"port": 1023},
            {"port": 65536},
            {"port": True},
            {"device_id": 0},
            {"device_id": 248},
            {"timeout": 0.0},
            {"timeout": math.nan},
            {"timeout": math.inf},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ConfigurationError):
                EndpointConfig(**values)


class ScenarioConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.endpoint = EndpointConfig()

    def test_observation_mode_needs_no_confirmation(self) -> None:
        config = ScenarioConfig(endpoint=self.endpoint)
        self.assertFalse(config.apply)
        self.assertEqual(config.iterations, 10)

    def test_write_mode_requires_exact_endpoint_confirmation(self) -> None:
        for confirmation in (None, "localhost:5020", "127.0.0.1:5021"):
            with self.subTest(confirmation=confirmation), self.assertRaises(ConfigurationError):
                ScenarioConfig(
                    endpoint=self.endpoint,
                    apply=True,
                    confirmation=confirmation,
                )
        accepted = ScenarioConfig(
            endpoint=self.endpoint,
            apply=True,
            confirmation="127.0.0.1:5020",
        )
        self.assertTrue(accepted.apply)

    def test_rejects_unbounded_or_invalid_scenario_values(self) -> None:
        invalid = (
            {"iterations": 0},
            {"iterations": 1001},
            {"interval": -0.1},
            {"interval": math.nan},
            {"open_below": -1},
            {"close_at": 151},
            {"open_below": 55, "close_at": 55},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ConfigurationError):
                ScenarioConfig(endpoint=self.endpoint, **values)

    def test_validates_simulator_controls(self) -> None:
        self.assertEqual(SimulatorConfig(self.endpoint).seed, 0)
        for values in ({"tick_interval": 0.0}, {"seed": -1}, {"seed": True}):
            with self.subTest(values=values), self.assertRaises(ConfigurationError):
                SimulatorConfig(self.endpoint, **values)


if __name__ == "__main__":
    unittest.main()
