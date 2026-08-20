"""Typed domain models and the intentionally small register contract."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import IntEnum
from typing import Any

from .errors import TransportError


class Register(IntEnum):
    """Zero-based Modbus holding-register addresses used by the lab."""

    PRESSURE = 0
    VALVE_COMMAND = 1
    ALARM = 2


REGISTER_COUNT = len(Register)


@dataclass(frozen=True, slots=True)
class PlantSnapshot:
    """Current synthetic process state."""

    pressure: int
    valve_open: bool
    alarm: bool

    def __post_init__(self) -> None:
        if isinstance(self.pressure, bool) or not 0 <= self.pressure <= 150:
            raise ValueError("pressure must be between 0 and 150")

    @classmethod
    def from_registers(cls, registers: Sequence[int]) -> PlantSnapshot:
        if len(registers) < REGISTER_COUNT:
            raise TransportError("simulator returned an incomplete register snapshot")
        pressure, valve, alarm = registers[:REGISTER_COUNT]
        if valve not in (0, 1) or alarm not in (0, 1):
            raise TransportError("simulator returned an invalid boolean register")
        try:
            return cls(pressure=int(pressure), valve_open=bool(valve), alarm=bool(alarm))
        except (TypeError, ValueError) as exc:
            raise TransportError("simulator returned an invalid register snapshot") from exc

    def to_registers(self) -> list[int]:
        return [self.pressure, int(self.valve_open), int(self.alarm)]


@dataclass(frozen=True, slots=True)
class ScenarioObservation:
    """One auditable step from a bounded lab run."""

    iteration: int
    snapshot: PlantSnapshot
    action: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["mode"] = "local_lab"
        return data
