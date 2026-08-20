from __future__ import annotations

import unittest
from typing import Any

from irongate_lab.config import EndpointConfig
from irongate_lab.errors import TransportError
from irongate_lab.gateway import PymodbusGateway
from irongate_lab.models import PlantSnapshot


class FakeResponse:
    def __init__(self, registers: list[int] | None = None, *, error: bool = False) -> None:
        self.registers = registers or []
        self._error = error

    def isError(self) -> bool:
        return self._error


class FakeClient:
    def __init__(self, *_args: Any, connect_result: bool = True, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.connect_result = connect_result
        self.closed = False
        self.read_response = FakeResponse([50, 0, 0])
        self.write_response = FakeResponse()
        self.read_calls: list[tuple[int, int, int]] = []
        self.write_calls: list[tuple[int, int, int]] = []

    def connect(self) -> bool:
        return self.connect_result

    def close(self) -> None:
        self.closed = True

    def read_holding_registers(
        self,
        address: int,
        *,
        count: int,
        device_id: int,
    ) -> FakeResponse:
        self.read_calls.append((address, count, device_id))
        return self.read_response

    def write_register(self, address: int, value: int, *, device_id: int) -> FakeResponse:
        self.write_calls.append((address, value, device_id))
        return self.write_response


class ClientFactory:
    def __init__(self, client: FakeClient) -> None:
        self.client = client
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def __call__(self, *args: Any, **kwargs: Any) -> FakeClient:
        self.calls.append((args, kwargs))
        return self.client


class GatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.endpoint = EndpointConfig(timeout=2.5)
        self.client = FakeClient()
        self.factory = ClientFactory(self.client)
        self.gateway = PymodbusGateway(self.endpoint, client_factory=self.factory)

    def test_connect_read_write_and_close(self) -> None:
        self.gateway.connect()
        self.assertEqual(self.gateway.read_snapshot(), PlantSnapshot(50, False, False))
        self.gateway.set_valve(True)
        self.gateway.close()

        self.assertEqual(self.client.read_calls, [(0, 3, 1)])
        self.assertEqual(self.client.write_calls, [(1, 1, 1)])
        self.assertTrue(self.client.closed)
        self.assertEqual(self.factory.calls[0][0], ("127.0.0.1",))
        self.assertEqual(self.factory.calls[0][1]["port"], 5020)
        self.assertEqual(self.factory.calls[0][1]["timeout"], 2.5)

    def test_rejects_failed_connection(self) -> None:
        client = FakeClient(connect_result=False)
        gateway = PymodbusGateway(self.endpoint, client_factory=ClientFactory(client))
        with self.assertRaisesRegex(TransportError, "could not connect"):
            gateway.connect()
        self.assertTrue(client.closed)

    def test_requires_connection_for_operations(self) -> None:
        with self.assertRaises(TransportError):
            self.gateway.read_snapshot()
        with self.assertRaises(TransportError):
            self.gateway.set_valve(True)

    def test_rejects_double_connect(self) -> None:
        self.gateway.connect()
        with self.assertRaises(TransportError):
            self.gateway.connect()
        self.gateway.close()

    def test_translates_error_and_malformed_responses(self) -> None:
        self.gateway.connect()
        for response in (
            FakeResponse(error=True),
            FakeResponse([50, 0]),
            FakeResponse([50, 2, 0]),
        ):
            self.client.read_response = response
            with self.subTest(response=response), self.assertRaises(TransportError):
                self.gateway.read_snapshot()
        self.client.write_response = FakeResponse(error=True)
        with self.assertRaises(TransportError):
            self.gateway.set_valve(False)
        self.gateway.close()

    def test_context_manager_closes_client(self) -> None:
        with self.gateway as connected:
            self.assertIs(connected, self.gateway)
        self.assertTrue(self.client.closed)


if __name__ == "__main__":
    unittest.main()
