"""Finite, auditable scenarios for the synthetic localhost process."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from typing import Protocol

from .config import ScenarioConfig
from .errors import ScenarioError
from .models import PlantSnapshot, ScenarioObservation


class LabGateway(Protocol):
    def connect(self) -> None: ...

    def read_snapshot(self) -> PlantSnapshot: ...

    def set_valve(self, open_: bool) -> None: ...

    def close(self) -> None: ...


class ScenarioRunner:
    """Run a bounded observation or explicitly confirmed local write scenario."""

    def __init__(
        self,
        gateway: LabGateway,
        config: ScenarioConfig,
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._gateway = gateway
        self._config = config
        self._sleep = sleep

    def run(self) -> list[ScenarioObservation]:
        observations: list[ScenarioObservation] = []
        owns_open_command = False
        cleanup_errors: list[Exception] = []
        try:
            self._gateway.connect()
            for iteration in range(1, self._config.iterations + 1):
                snapshot = self._gateway.read_snapshot()
                action = "observe"
                if self._config.apply:
                    if snapshot.pressure < self._config.open_below and not snapshot.valve_open:
                        # Treat the command as ours before sending it: a transport error can
                        # occur after the simulator has already applied the write.
                        owns_open_command = True
                        self._gateway.set_valve(True)
                        action = "open_simulated_valve"
                    elif snapshot.pressure >= self._config.close_at and owns_open_command:
                        self._gateway.set_valve(False)
                        owns_open_command = False
                        action = "close_simulated_valve"
                observations.append(ScenarioObservation(iteration, snapshot, action))
                if iteration < self._config.iterations:
                    self._sleep(self._config.interval)
            return observations
        finally:
            active_error = sys.exc_info()[0] is not None
            if owns_open_command:
                try:
                    self._gateway.set_valve(False)
                except Exception as exc:
                    cleanup_errors.append(exc)
            try:
                self._gateway.close()
            except Exception as exc:
                cleanup_errors.append(exc)
            if cleanup_errors and not active_error:
                raise ScenarioError("scenario cleanup could not be completed") from cleanup_errors[
                    0
                ]
