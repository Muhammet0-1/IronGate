"""Command-line interface for the localhost-only IronGate Lab."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from . import __version__
from .config import EndpointConfig, ScenarioConfig, SimulatorConfig
from .errors import ConfigurationError, IronGateError
from .gateway import PymodbusGateway
from .models import ScenarioObservation
from .scenario import ScenarioRunner
from .simulator import run_simulator


def _add_endpoint_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1", help="loopback IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5020, help="unprivileged TCP port")
    parser.add_argument("--device-id", type=int, default=1, help="Modbus device ID")
    parser.add_argument("--timeout", type=float, default=3.0, help="client timeout in seconds")


def _add_observation_arguments(parser: argparse.ArgumentParser) -> None:
    _add_endpoint_arguments(parser)
    parser.add_argument("--iterations", type=int, default=10, help="bounded sample count")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between samples")
    parser.add_argument("--json", action="store_true", help="emit JSON Lines")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="irongate-lab",
        description="Localhost-only Modbus/TCP process-security training lab.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="run the synthetic PLC on loopback")
    _add_endpoint_arguments(simulate)
    simulate.add_argument("--tick-interval", type=float, default=1.0)
    simulate.add_argument("--seed", type=int, default=0)

    observe = subparsers.add_parser("observe", help="read a bounded number of snapshots")
    _add_observation_arguments(observe)

    scenario = subparsers.add_parser(
        "scenario",
        help="run a bounded scenario; writes require explicit confirmation",
    )
    _add_observation_arguments(scenario)
    scenario.add_argument("--open-below", type=int, default=45)
    scenario.add_argument("--close-at", type=int, default=55)
    scenario.add_argument(
        "--apply",
        action="store_true",
        help="allow valve writes to the loopback simulator",
    )
    scenario.add_argument(
        "--confirm-lab-target",
        metavar="HOST:PORT",
        help="exact endpoint confirmation required with --apply",
    )
    return parser


def _endpoint_from_args(args: argparse.Namespace) -> EndpointConfig:
    return EndpointConfig(
        host=args.host,
        port=args.port,
        device_id=args.device_id,
        timeout=args.timeout,
    )


def _scenario_from_args(args: argparse.Namespace, endpoint: EndpointConfig) -> ScenarioConfig:
    return ScenarioConfig(
        endpoint=endpoint,
        iterations=args.iterations,
        interval=args.interval,
        open_below=getattr(args, "open_below", 45),
        close_at=getattr(args, "close_at", 55),
        apply=getattr(args, "apply", False),
        confirmation=getattr(args, "confirm_lab_target", None),
    )


def _print_observations(
    observations: Sequence[ScenarioObservation],
    *,
    as_json: bool,
) -> None:
    for item in observations:
        data = item.to_dict()
        if as_json:
            print(json.dumps(data, sort_keys=True))
        else:
            snapshot = data["snapshot"]
            print(
                f"[{data['iteration']:03d}] pressure={snapshot['pressure']:3d} "
                f"valve_open={str(snapshot['valve_open']).lower():5s} "
                f"alarm={str(snapshot['alarm']).lower():5s} action={data['action']}"
            )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        endpoint = _endpoint_from_args(args)
        if args.command == "simulate":
            simulator_config = SimulatorConfig(
                endpoint=endpoint,
                tick_interval=args.tick_interval,
                seed=args.seed,
            )
            print(f"Starting synthetic PLC at {endpoint.label} (Ctrl+C to stop)")
            run_simulator(simulator_config)
            return 0

        scenario_config = _scenario_from_args(args, endpoint)
        gateway = PymodbusGateway(endpoint)
        observations = ScenarioRunner(gateway, scenario_config).run()
        _print_observations(observations, as_json=args.json)
        return 0
    except ConfigurationError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 130
    except (IronGateError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
