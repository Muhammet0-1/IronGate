"""Synchronous PyModbus gateway with a small testable surface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, cast

from .config import EndpointConfig
from .errors import TransportError
from .models import REGISTER_COUNT, PlantSnapshot, Register


class ResponseLike(Protocol):
    registers: list[int]

    def isError(self) -> bool:
        """Return whether the Modbus response represents an error."""


class ClientLike(Protocol):
    def connect(self) -> bool:
        """Connect to the local simulator."""

    def close(self) -> None:
        """Close the transport."""

    def read_holding_registers(
        self,
        address: int,
        *,
        count: int,
        device_id: int,
    ) -> ResponseLike:
        """Read holding registers."""

    def write_register(
        self,
        address: int,
        value: int,
        *,
        device_id: int,
    ) -> ResponseLike:
        """Write one holding register."""


ClientFactory = Callable[..., ClientLike]


class PymodbusGateway:
    """Talk only to an already validated loopback simulator endpoint."""

    def __init__(
        self,
        endpoint: EndpointConfig,
        *,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._client_factory = client_factory
        self._client: ClientLike | None = None

    def _factory(self) -> ClientFactory:
        if self._client_factory is not None:
            return self._client_factory
        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError as exc:  # pragma: no cover - exercised by installation smoke test
            raise TransportError(
                "PyModbus is not installed; run: python -m pip install -e ."
            ) from exc
        return cast(ClientFactory, ModbusTcpClient)

    def connect(self) -> None:
        if self._client is not None:
            raise TransportError("gateway is already connected")
        try:
            client = self._factory()(
                self._endpoint.host,
                port=self._endpoint.port,
                timeout=self._endpoint.timeout,
                retries=1,
            )
            if not client.connect():
                client.close()
                raise TransportError(
                    f"could not connect to local simulator at {self._endpoint.label}"
                )
        except TransportError:
            raise
        except Exception as exc:
            raise TransportError("local Modbus connection failed") from exc
        self._client = client

    def _connected_client(self) -> ClientLike:
        if self._client is None:
            raise TransportError("gateway is not connected")
        return self._client

    @staticmethod
    def _validate_response(response: ResponseLike, operation: str) -> None:
        try:
            failed = response.isError()
        except Exception as exc:
            raise TransportError(f"invalid response while attempting to {operation}") from exc
        if failed:
            raise TransportError(f"simulator rejected request to {operation}")

    def read_snapshot(self) -> PlantSnapshot:
        client = self._connected_client()
        try:
            response = client.read_holding_registers(
                Register.PRESSURE,
                count=REGISTER_COUNT,
                device_id=self._endpoint.device_id,
            )
            self._validate_response(response, "read process state")
            return PlantSnapshot.from_registers(response.registers)
        except TransportError:
            raise
        except Exception as exc:
            raise TransportError("failed to read local simulator state") from exc

    def set_valve(self, open_: bool) -> None:
        client = self._connected_client()
        try:
            response = client.write_register(
                Register.VALVE_COMMAND,
                int(open_),
                device_id=self._endpoint.device_id,
            )
            self._validate_response(response, "change the simulated valve")
        except TransportError:
            raise
        except Exception as exc:
            raise TransportError("failed to update the simulated valve") from exc

    def close(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            try:
                client.close()
            except Exception as exc:
                raise TransportError("failed to close the local Modbus connection") from exc

    def __enter__(self) -> PymodbusGateway:
        self.connect()
        return self

    def __exit__(self, *_exc_info: Any) -> None:
        self.close()
