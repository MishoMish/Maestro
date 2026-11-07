"""The build guide, checked against the firmware, and the simulator's own honesty.

Every test in this suite runs on a device wired from the guide's list, so here deliberately
wrong wiring must visibly break the device. If it doesn't, the other tests prove nothing.
"""
import re
import unittest

from base import *  # noqa: F403
from device import ROOT, Device, wiring


def named(parts, name):
    return [p for p in parts if p.info.get("name") == name][0]


class GuideMatchesFirmware(unittest.TestCase):
    def source(self, name):
        return (ROOT / "code" / name).read_text(encoding="utf-8")

    def test_guide_led_pins_are_the_firmwares(self):
        found = re.search(r"LED_PINS\[8\] = \{([^}]*)\}", self.source("src/config.h")).group(1)
        firmware = [f"D{p.strip()}" if p.strip().isdigit() else p.strip() for p in found.split(",")]
        self.assertEqual(wiring.uno_map()["leds"], firmware)

    def test_guide_lcd_pins_are_the_firmwares(self):
        found = re.search(r"LiquidCrystal lcd\(([^)]*)\)", self.source("src/output.cpp")).group(1)
        pins = [f"D{p.strip()}" for p in found.split(",")]
        lcd = wiring.uno_map()["lcd"]
        self.assertEqual([lcd[n] for n in ("RS", "E", "D4", "D5", "D6", "D7")], pins)

    def test_guide_piezo_and_knob_pins_are_the_firmwares(self):
        config = self.source("src/config.h")
        uno = wiring.uno_map()
        self.assertEqual(uno["piezo"], "D" + re.search(r"PIN_PIEZO = (\d+)", config).group(1))
        self.assertEqual(uno["knob"], re.search(r"PIN_KNOB = (A\d)", config).group(1))

    def test_self_test_uses_the_guides_key_values(self):
        found = re.search(r"KEY_A0\[8\] = \{([^}]*)\}", self.source("selftest/selftest.cpp")).group(1)
        _, readings = wiring.check()
        self.assertEqual([int(v) for v in found.split(",")], [readings[k] for k in range(1, 9)])

    def test_guide_passes_its_electrical_check(self):
        self.assertEqual(wiring.check()[0], [])


class WrongWiringBreaksTheDevice(unittest.TestCase):
    """Boots a device built from a guide with one deliberate mistake."""

    def boot(self, mutate):
        parts = wiring.build_parts()
        mutate(parts)
        d = Device(parts=parts)
        d.run(1100)
        return d

    def free_play(self, d):
        d.knob_to_tick(FREE)
        d.tap(1)
        d.run(200)

    def test_correct_wiring_shows_the_menu(self):
        d = self.boot(lambda parts: None)
        self.assertIn("MAESTRO", d.lcd(0))

    def test_swapped_lcd_data_wires_garble_the_screen(self):
        def swap(parts):
            named(parts, "LCD D4").b = ("U", "D4")
            named(parts, "LCD D5").b = ("U", "D5")
        self.assertNotIn("MAESTRO", self.boot(swap).lcd(0))

    def test_swapped_rs_and_e_kill_the_screen(self):
        def swap(parts):
            named(parts, "LCD RS").b = ("U", "D11")
            named(parts, "LCD E").b = ("U", "D12")
        self.assertNotIn("MAESTRO", self.boot(swap).lcd(0))

    def test_swapped_led_wires_light_the_wrong_keys(self):
        def swap(parts):
            named(parts, "LED wire 1").b = ("U", "D7")
            named(parts, "LED wire 2").b = ("U", "D6")
        d = self.boot(swap)
        self.free_play(d)
        d.press(1)
        d.run(100)
        self.assertEqual(d.leds(), 0b10)      # key 1's note, key 2's LED

    def test_piezo_on_the_wrong_pin_is_silent(self):
        def wrong(parts):
            named(parts, "Piezo signal").b = ("U", "A5")
        d = self.boot(wrong)
        self.free_play(d)
        d.press(1)
        d.run(100)
        self.assertEqual(d.tone(), 0)

    def test_broken_ladder_link_reads_the_wrong_key(self):
        def broken(parts):
            parts[:] = [p for p in parts if p.info.get("name") != "Ladder 3"]
        d = self.boot(broken)
        self.free_play(d)
        d.press(4, bounce=False)
        d.run(100)
        self.assertNotEqual(hz_to_key(d.tone()), 4)

    def test_missing_gnd_link_breaks_the_keys(self):
        def broken(parts):
            parts[:] = [p for p in parts if p.info.get("name") != "GND link"]
        d = self.boot(broken)
        self.free_play(d)
        d.press(5, bounce=False)
        d.run(100)
        self.assertNotEqual(hz_to_key(d.tone()), 5)

    def test_knob_on_the_wrong_pin_does_nothing(self):
        def wrong(parts):
            named(parts, "Knob middle").b = ("U", "A5")
        d = self.boot(wrong)
        d.knob_to_tick(4)
        self.assertNotIn("4/7", d.lcd(0))


class OnChipSelfTest(unittest.TestCase):
    """The program ./maestro selftest puts on a real Uno, without its whole-piece games."""

    def test_self_test_passes_in_the_simulator(self):
        d = Device(elf=ROOT / "code" / ".pio" / "build" / "selftest_short" / "firmware.elf")
        while "RESULT" not in d.serial() or not d.serial().rstrip().endswith("failed"):
            d.run(1000)
            self.assertLess(d.now(), 1500000, d.serial()[-800:])
        report = d.serial()
        self.assertNotIn("FAIL ", report, report)
        self.assertRegex(report, r"RESULT \d+ passed, 0 failed")


if __name__ == "__main__":
    unittest.main()
