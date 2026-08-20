"""Local-only Modbus/TCP server backed by the synthetic process model."""

from __future__ import annotations

import random
from collections.abc import Callable
from threading import Event, Thread
from typing import Any

from .bank import RegisterBank
from .config import SimulatorConfig
from .errors import ConfigurationError


def _process_loop(
    bank: RegisterBank,
    stop_event: Event,
    *,
    interval: float,
    seed: int,
    disturbance_source: Callable[[], float] | None = None,
) -> None:
    rng = random.Random(seed)
    next_disturbance = disturbance_source or (lambda: rng.uniform(-1.0, 1.0))
    while not stop_event.is_set():
        bank.advance(disturbance=next_disturbance())
        stop_event.wait(interval)


def _build_context(bank: RegisterBank, device_id: int) -> Any:
    try:
        from pymodbus.datastore import (
            ModbusDeviceContext,
            ModbusSequentialDataBlock,
            ModbusServerContext,
        )
        from pymodbus.exceptions import ParameterException
    except ImportError as exc:  # pragma: no cover - covered by installed-package smoke test
        raise ConfigurationError(
            "PyModbus is not installed; run: python -m pip install -e ."
        ) from exc

    class LabHoldingRegisters(ModbusSequentialDataBlock):
        """Expose only three synthetic registers; only the valve is writable."""

        def __init__(self) -> None:
            # ModbusDeviceContext adds one to protocol addresses in PyModbus 3.11.
            super().__init__(1, bank.snapshot().to_registers())  # type: ignore[no-untyped-call]

        def getValues(self, address: int, count: int = 1) -> list[int]:
            try:
                return bank.read(address - 1, count)
            except ValueError as exc:
                raise ParameterException(str(exc)) from exc  # type: ignore[no-untyped-call]

        def setValues(self, address: int, values: list[int]) -> None:
            try:
                bank.write(address - 1, list(values))
            except ValueError as exc:
                raise ParameterException(str(exc)) from exc  # type: ignore[no-untyped-call]

    class ReadOnlyDataBlock(ModbusSequentialDataBlock):
        """Provide inert non-holding-register spaces and reject their writes."""

        def __init__(self) -> None:
            super().__init__(1, [0, 0, 0])  # type: ignore[no-untyped-call]

        def setValues(self, address: int, values: list[int]) -> None:
            raise ParameterException(  # type: ignore[no-untyped-call]
                "only the synthetic valve holding register is writable"
            )

    device = ModbusDeviceContext(
        di=ReadOnlyDataBlock(),
        co=ReadOnlyDataBlock(),
        ir=ReadOnlyDataBlock(),
        hr=LabHoldingRegisters(),
    )
    return ModbusServerContext(  # type: ignore[no-untyped-call]
        devices={device_id: device},
        single=False,
    )


def run_simulator(config: SimulatorConfig) -> None:
    """Run until interrupted; the validated endpoint can only be a loopback address."""

    try:
        from pymodbus.server import StartTcpServer
    except ImportError as exc:  # pragma: no cover - covered by installed-package smoke test
        raise ConfigurationError(
            "PyModbus is not installed; run: python -m pip install -e ."
        ) from exc

    bank = RegisterBank()
    context = _build_context(bank, config.endpoint.device_id)
    stop_event = Event()
    worker = Thread(
        target=_process_loop,
        args=(bank, stop_event),
        kwargs={"interval": config.tick_interval, "seed": config.seed},
        name="irongate-lab-process",
        daemon=True,
    )
    worker.start()
    try:
        StartTcpServer(
            context=context,
            address=(config.endpoint.host, config.endpoint.port),
        )
    finally:
        stop_event.set()
        worker.join(timeout=max(1.0, config.tick_interval * 2))
