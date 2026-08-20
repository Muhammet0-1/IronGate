from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from threading import Event
from unittest.mock import Mock, patch

from irongate_lab.bank import RegisterBank
from irongate_lab.cli import _print_observations, build_parser, main
from irongate_lab.errors import TransportError
from irongate_lab.models import PlantSnapshot, ScenarioObservation
from irongate_lab.simulator import _process_loop


class CliTests(unittest.TestCase):
    def test_parser_exposes_three_explicit_modes(self) -> None:
        parser = build_parser()
        for command in ("simulate", "observe", "scenario"):
            with self.subTest(command=command):
                args = parser.parse_args([command])
                self.assertEqual(args.command, command)

    def test_non_loopback_target_returns_configuration_exit_code(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main(["observe", "--host", "192.0.2.10"])
        self.assertEqual(result, 2)
        self.assertIn("only connects to loopback", stderr.getvalue())

    def test_unconfirmed_apply_returns_configuration_exit_code(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main(["scenario", "--apply"])
        self.assertEqual(result, 2)
        self.assertIn("--confirm-lab-target", stderr.getvalue())

    @patch("irongate_lab.cli.ScenarioRunner")
    @patch("irongate_lab.cli.PymodbusGateway")
    def test_observe_prints_runner_output(self, gateway_type: Mock, runner_type: Mock) -> None:
        gateway_type.return_value = object()
        runner_type.return_value.run.return_value = [
            ScenarioObservation(1, PlantSnapshot(50, False, False), "observe")
        ]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(["observe", "--iterations", "1"])
        self.assertEqual(result, 0)
        self.assertIn("pressure= 50", stdout.getvalue())

    @patch("irongate_lab.cli.run_simulator")
    def test_simulate_passes_validated_configuration(self, run: Mock) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(["simulate", "--seed", "9"])
        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.args[0].seed, 9)
        self.assertIn("127.0.0.1:5020", stdout.getvalue())

    @patch("irongate_lab.cli.ScenarioRunner")
    @patch("irongate_lab.cli.PymodbusGateway")
    def test_expected_runtime_error_returns_one(
        self,
        gateway_type: Mock,
        runner_type: Mock,
    ) -> None:
        gateway_type.return_value = object()
        runner_type.return_value.run.side_effect = TransportError("offline")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main(["observe"])
        self.assertEqual(result, 1)
        self.assertIn("offline", stderr.getvalue())

    def test_json_output_is_valid_json_lines(self) -> None:
        stdout = io.StringIO()
        observation = ScenarioObservation(1, PlantSnapshot(50, False, False), "observe")
        with redirect_stdout(stdout):
            _print_observations([observation], as_json=True)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["mode"], "local_lab")
        self.assertEqual(data["snapshot"]["pressure"], 50)


class SimulatorLoopTests(unittest.TestCase):
    def test_process_loop_can_stop_without_network_access(self) -> None:
        bank = RegisterBank()
        bank.write(1, [1])
        stop_event = Event()

        def one_disturbance() -> float:
            stop_event.set()
            return 0.0

        _process_loop(
            bank,
            stop_event,
            interval=1,
            seed=0,
            disturbance_source=one_disturbance,
        )
        self.assertEqual(bank.snapshot(), PlantSnapshot(55, True, False))


if __name__ == "__main__":
    unittest.main()
