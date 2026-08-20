"""Thread-safe in-memory register bank used by the local simulator."""

from __future__ import annotations

from threading import Lock

from .models import REGISTER_COUNT, PlantSnapshot, Register
from .process import WaterPressureProcess


class RegisterBank:
    """Own the synthetic registers while keeping process updates atomic."""

    def __init__(self, process: WaterPressureProcess | None = None) -> None:
        self._process = process or WaterPressureProcess()
        self._lock = Lock()
        self._values = PlantSnapshot(50, False, False).to_registers()

    def read(self, address: int, count: int = 1) -> list[int]:
        if address < 0 or count < 1 or address + count > REGISTER_COUNT:
            raise ValueError("register read is outside the lab register map")
        with self._lock:
            return list(self._values[address : address + count])

    def write(self, address: int, values: list[int]) -> None:
        if address != Register.VALVE_COMMAND or len(values) != 1:
            raise ValueError("only the valve command register is writable")
        value = values[0]
        if value not in (0, 1):
            raise ValueError("valve command must be 0 or 1")
        with self._lock:
            self._values[Register.VALVE_COMMAND] = value

    def advance(self, *, disturbance: float = 0.0) -> PlantSnapshot:
        with self._lock:
            valve_open = bool(self._values[Register.VALVE_COMMAND])
            snapshot = self._process.step(
                valve_open=valve_open,
                disturbance=disturbance,
            )
            self._values = snapshot.to_registers()
            return snapshot

    def snapshot(self) -> PlantSnapshot:
        with self._lock:
            return PlantSnapshot.from_registers(self._values)
