from __future__ import annotations

import unittest

from irongate_lab.config import EndpointConfig, ScenarioConfig
from irongate_lab.errors import TransportError
from irongate_lab.models import PlantSnapshot
from irongate_lab.scenario import ScenarioRunner


class AmbiguousWriteGateway:
    """Model a write that reaches the PLC before the response is lost."""

    def __init__(self) -> None:
        self.write_attempts: list[bool] = []
        self.closed = False

    def connect(self) -> None:
        return None

    def read_snapshot(self) -> PlantSnapshot:
        return PlantSnapshot(40, False, False)

    def set_valve(self, open_: bool) -> None:
        self.write_attempts.append(open_)
        if open_:
            raise TransportError("response lost after write")

    def close(self) -> None:
        self.closed = True


class CleanupRegressionTests(unittest.TestCase):
    def test_ambiguous_open_write_triggers_best_effort_close(self) -> None:
        endpoint = EndpointConfig()
        config = ScenarioConfig(
            endpoint=endpoint,
            iterations=1,
            interval=0,
            apply=True,
            confirmation=endpoint.label,
        )
        gateway = AmbiguousWriteGateway()
        with self.assertRaisesRegex(TransportError, "response lost"):
            ScenarioRunner(gateway, config, sleep=lambda _: None).run()
        self.assertEqual(gateway.write_attempts, [True, False])
        self.assertTrue(gateway.closed)


if __name__ == "__main__":
    unittest.main()
