from __future__ import annotations

import unittest

from irongate_lab.config import EndpointConfig, ScenarioConfig
from irongate_lab.errors import ScenarioError, TransportError
from irongate_lab.models import PlantSnapshot
from irongate_lab.scenario import ScenarioRunner


class FakeGateway:
    def __init__(self, snapshots: list[PlantSnapshot]) -> None:
        self.snapshots = list(snapshots)
        self.connected = False
        self.closed = False
        self.writes: list[bool] = []
        self.close_error: Exception | None = None
        self.write_error: Exception | None = None

    def connect(self) -> None:
        self.connected = True

    def read_snapshot(self) -> PlantSnapshot:
        if not self.snapshots:
            raise TransportError("no more snapshots")
        return self.snapshots.pop(0)

    def set_valve(self, open_: bool) -> None:
        if self.write_error is not None:
            raise self.write_error
        self.writes.append(open_)

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


def config(*, iterations: int, apply: bool = False) -> ScenarioConfig:
    endpoint = EndpointConfig()
    return ScenarioConfig(
        endpoint=endpoint,
        iterations=iterations,
        interval=0,
        open_below=45,
        close_at=55,
        apply=apply,
        confirmation=endpoint.label if apply else None,
    )


class ScenarioRunnerTests(unittest.TestCase):
    def test_observation_mode_never_writes(self) -> None:
        gateway = FakeGateway([PlantSnapshot(20, False, False)] * 2)
        observations = ScenarioRunner(gateway, config(iterations=2), sleep=lambda _: None).run()
        self.assertEqual(gateway.writes, [])
        self.assertEqual([item.action for item in observations], ["observe", "observe"])
        self.assertTrue(gateway.connected)
        self.assertTrue(gateway.closed)

    def test_apply_mode_opens_and_then_closes_simulated_valve(self) -> None:
        gateway = FakeGateway(
            [
                PlantSnapshot(40, False, False),
                PlantSnapshot(50, True, False),
                PlantSnapshot(56, True, False),
            ]
        )
        observations = ScenarioRunner(
            gateway,
            config(iterations=3, apply=True),
            sleep=lambda _: None,
        ).run()
        self.assertEqual(gateway.writes, [True, False])
        self.assertEqual(
            [item.action for item in observations],
            ["open_simulated_valve", "observe", "close_simulated_valve"],
        )

    def test_cleanup_closes_valve_opened_by_runner(self) -> None:
        gateway = FakeGateway([PlantSnapshot(40, False, False)])
        ScenarioRunner(gateway, config(iterations=1, apply=True), sleep=lambda _: None).run()
        self.assertEqual(gateway.writes, [True, False])

    def test_runner_does_not_claim_preexisting_open_valve(self) -> None:
        gateway = FakeGateway([PlantSnapshot(40, True, False)])
        ScenarioRunner(gateway, config(iterations=1, apply=True), sleep=lambda _: None).run()
        self.assertEqual(gateway.writes, [])

    def test_sleep_occurs_only_between_iterations(self) -> None:
        sleeps: list[float] = []
        gateway = FakeGateway([PlantSnapshot(50, False, False)] * 3)
        ScenarioRunner(gateway, config(iterations=3), sleep=sleeps.append).run()
        self.assertEqual(sleeps, [0, 0])

    def test_cleanup_failure_is_reported_without_active_error(self) -> None:
        gateway = FakeGateway([PlantSnapshot(50, False, False)])
        gateway.close_error = OSError("close failed")
        with self.assertRaises(ScenarioError):
            ScenarioRunner(gateway, config(iterations=1), sleep=lambda _: None).run()

    def test_primary_read_error_is_not_masked_by_close_error(self) -> None:
        gateway = FakeGateway([])
        gateway.close_error = OSError("close failed")
        with self.assertRaisesRegex(TransportError, "no more snapshots"):
            ScenarioRunner(gateway, config(iterations=1), sleep=lambda _: None).run()


if __name__ == "__main__":
    unittest.main()
