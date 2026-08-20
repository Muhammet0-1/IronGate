"""Pure synthetic water-pressure process model."""

from __future__ import annotations

from dataclasses import dataclass

from .models import PlantSnapshot


@dataclass(slots=True)
class WaterPressureProcess:
    """Small deterministic model suitable for tests and local demonstrations."""

    pressure: float = 50.0
    target_pressure: float = 50.0
    valve_gain: float = 5.0
    settle_rate: float = 0.25
    alarm_threshold: float = 90.0

    def step(self, *, valve_open: bool, disturbance: float = 0.0) -> PlantSnapshot:
        if valve_open:
            self.pressure += self.valve_gain
        else:
            self.pressure += (self.target_pressure - self.pressure) * self.settle_rate
        self.pressure = min(150.0, max(0.0, self.pressure + disturbance))
        rounded = round(self.pressure)
        return PlantSnapshot(
            pressure=rounded,
            valve_open=valve_open,
            alarm=self.pressure >= self.alarm_threshold,
        )
