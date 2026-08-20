from __future__ import annotations

import importlib.util
import unittest

from irongate_lab.bank import RegisterBank
from irongate_lab.models import PlantSnapshot
from irongate_lab.simulator import _build_context

PYMODBUS_AVAILABLE = importlib.util.find_spec("pymodbus") is not None


@unittest.skipUnless(PYMODBUS_AVAILABLE, "PyModbus is not installed")
class PymodbusContextTests(unittest.TestCase):
    def test_protocol_addresses_map_to_the_documented_registers(self) -> None:
        bank = RegisterBank()
        context = _build_context(bank, 7)
        device = context[7]

        self.assertEqual(device.getValues(3, 0, 3), [50, 0, 0])
        device.setValues(6, 1, [1])
        self.assertEqual(bank.snapshot(), PlantSnapshot(50, True, False))

    def test_protocol_rejects_writes_outside_the_valve_register(self) -> None:
        from pymodbus.exceptions import ParameterException

        context = _build_context(RegisterBank(), 1)
        with self.assertRaises(ParameterException):
            context[1].setValues(6, 0, [99])
        with self.assertRaises(ParameterException):
            context[1].setValues(5, 0, [True])


if __name__ == "__main__":
    unittest.main()
