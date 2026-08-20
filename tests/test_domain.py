from __future__ import annotations

import unittest

from irongate_lab.bank import RegisterBank
from irongate_lab.errors import TransportError
from irongate_lab.models import PlantSnapshot, ScenarioObservation
from irongate_lab.process import WaterPressureProcess


class PlantSnapshotTests(unittest.TestCase):
    def test_round_trips_register_values(self) -> None:
        snapshot = PlantSnapshot.from_registers([51, 1, 0])
        self.assertEqual(snapshot, PlantSnapshot(51, True, False))
        self.assertEqual(snapshot.to_registers(), [51, 1, 0])

    def test_rejects_incomplete_or_invalid_registers(self) -> None:
        for registers in ([50, 0], [50, 2, 0], [151, 0, 0]):
            with self.subTest(registers=registers), self.assertRaises(TransportError):
                PlantSnapshot.from_registers(registers)

    def test_observation_serialization_is_explicit(self) -> None:
        data = ScenarioObservation(2, PlantSnapshot(50, False, False), "observe").to_dict()
        self.assertEqual(data["mode"], "local_lab")
        self.assertEqual(data["snapshot"]["pressure"], 50)


class WaterPressureProcessTests(unittest.TestCase):
    def test_open_valve_increases_pressure(self) -> None:
        process = WaterPressureProcess(pressure=50)
        self.assertEqual(process.step(valve_open=True).pressure, 55)

    def test_closed_valve_converges_toward_target(self) -> None:
        process = WaterPressureProcess(pressure=70, target_pressure=50)
        self.assertEqual(process.step(valve_open=False).pressure, 65)

    def test_process_clamps_pressure_and_sets_alarm(self) -> None:
        high = WaterPressureProcess(pressure=149, valve_gain=10)
        snapshot = high.step(valve_open=True, disturbance=5)
        self.assertEqual(snapshot.pressure, 150)
        self.assertTrue(snapshot.alarm)

        low = WaterPressureProcess(pressure=1, target_pressure=0, settle_rate=1)
        self.assertEqual(low.step(valve_open=False, disturbance=-10).pressure, 0)


class RegisterBankTests(unittest.TestCase):
    def test_only_valve_register_is_writable(self) -> None:
        bank = RegisterBank()
        bank.write(1, [1])
        self.assertTrue(bank.snapshot().valve_open)
        for address, values in ((0, [10]), (2, [1]), (1, [2]), (1, [0, 1])):
            with self.subTest(address=address, values=values), self.assertRaises(ValueError):
                bank.write(address, values)

    def test_reads_are_copied_and_range_checked(self) -> None:
        bank = RegisterBank()
        values = bank.read(0, 3)
        values[0] = 999
        self.assertEqual(bank.read(0, 1), [50])
        for address, count in ((-1, 1), (0, 0), (2, 2)):
            with self.subTest(address=address, count=count), self.assertRaises(ValueError):
                bank.read(address, count)

    def test_advance_applies_valve_state_atomically(self) -> None:
        bank = RegisterBank()
        bank.write(1, [1])
        snapshot = bank.advance(disturbance=0)
        self.assertEqual(snapshot, PlantSnapshot(55, True, False))
        self.assertEqual(bank.read(0, 3), [55, 1, 0])


if __name__ == "__main__":
    unittest.main()
