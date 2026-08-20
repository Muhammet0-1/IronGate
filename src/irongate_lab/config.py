"""Validated, fail-closed configuration for the localhost-only lab."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from math import isfinite

from .errors import ConfigurationError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5020
DEFAULT_DEVICE_ID = 1


def _validate_int(name: str, value: int, minimum: int, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum} and {maximum}")


def _validate_float(name: str, value: float, minimum: float, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{name} must be a number")
    if not isfinite(float(value)) or not minimum <= float(value) <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum:g} and {maximum:g}")


def normalize_loopback_host(host: str) -> str:
    """Return a canonical loopback address and reject every non-loopback target."""

    candidate = host.strip()
    if not candidate:
        raise ConfigurationError("host must not be empty")
    if candidate.casefold() == "localhost":
        return DEFAULT_HOST
    if "%" in candidate:
        raise ConfigurationError("scoped IPv6 addresses are not supported")
    try:
        address = ip_address(candidate)
    except ValueError as exc:
        raise ConfigurationError("host must be localhost or a loopback IP address") from exc
    if not address.is_loopback:
        raise ConfigurationError("IronGate Lab only connects to loopback addresses")
    return address.compressed


@dataclass(frozen=True, slots=True)
class EndpointConfig:
    """Validated endpoint for the local Modbus simulator."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    device_id: int = DEFAULT_DEVICE_ID
    timeout: float = 3.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "host", normalize_loopback_host(self.host))
        _validate_int("port", self.port, 1024, 65535)
        _validate_int("device_id", self.device_id, 1, 247)
        _validate_float("timeout", self.timeout, 0.1, 60.0)

    @property
    def label(self) -> str:
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{host}:{self.port}"


@dataclass(frozen=True, slots=True)
class ScenarioConfig:
    """Controls a finite observation or explicit local write scenario."""

    endpoint: EndpointConfig
    iterations: int = 10
    interval: float = 1.0
    open_below: int = 45
    close_at: int = 55
    apply: bool = False
    confirmation: str | None = None

    def __post_init__(self) -> None:
        _validate_int("iterations", self.iterations, 1, 1_000)
        _validate_float("interval", self.interval, 0.0, 60.0)
        _validate_int("open_below", self.open_below, 0, 149)
        _validate_int("close_at", self.close_at, 1, 150)
        if self.close_at <= self.open_below:
            raise ConfigurationError("close_at must be greater than open_below")
        if self.apply and self.confirmation != self.endpoint.label:
            raise ConfigurationError(
                "write mode requires --confirm-lab-target " + self.endpoint.label
            )


@dataclass(frozen=True, slots=True)
class SimulatorConfig:
    """Controls the deterministic localhost simulator."""

    endpoint: EndpointConfig
    tick_interval: float = 1.0
    seed: int = 0

    def __post_init__(self) -> None:
        _validate_float("tick_interval", self.tick_interval, 0.01, 60.0)
        _validate_int("seed", self.seed, 0, 2_147_483_647)
