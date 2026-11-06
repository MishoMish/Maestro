"""Boot, menus, knob and Yes/No screens (Q9, Q10, Q25, Q27, Q33)."""
import unittest

import random

from base import *  # noqa: F403
from device import ROOT, Device, key_voltage_mv


class Menus(MaestroTest):
    def test_boot_shows_menu_and_initialises_records(self):
        self.assertEqual(self.d.lcd(), ["MAESTRO     1/7", "Light only"])
        data = self.d.eeprom()
        self.assertEqual(data[0], 0x43)
        self.assertEqual(data[1:31], bytes(30))

    def test_all_seven_ticks_have_name_note_and_led(self):
        names = ["Light only", "Sound only", "Light + sound", "Ear", "Free play", "Records", "Reset records"]
        for tick in list(range(2, 8)) + list(range(6, 0, -1)):   # one tick at a time, both ways
            start = self.d.now()
            self.d.knob_to_tick(tick)
            self.assertEqual(self.d.lcd(), [f"MAESTRO     {tick}/7", names[tick - 1]])
            self.assertEqual(self.d.leds(), 1 << (tick - 1))
            self.assert_tones(self.d.tones_since(start), [tick])

    def test_fast_turn_ends_on_the_right_item(self):
        self.d.knob_to_tick(7)
        self.assertEqual(self.d.lcd(1), "Reset records")
        self.d.knob_to_tick(1)
        self.assertEqual(self.d.lcd(1), "Light only")
        self.assertEqual(self.d.leds(), 1)

    def test_real_pot_angles_reach_every_tick_with_noise(self):
        # Ticks at -120..+120 degrees on an assumed 270 degree pot.
        for tick, angle in enumerate(range(-120, 121, 40), 1):
            value = 512 + angle * 1023 / 270
            self.d.knob_raw(value)
            for noise in (6, -6, 6, -6):
                self.d.knob_raw(value + noise, settle=False)
                self.d.run(100)
                self.assertIn(f"{tick}/7", self.d.lcd(0), f"angle {angle}")

    def test_knob_boundary_does_not_flicker(self):
        self.d.knob_to_tick(3)
        boundary = 3 * 1024 // 7
        self.d.knob_raw(boundary - 5)
        start = self.d.now()
        for noise in (10, -10) * 10:
            self.d.knob_raw(boundary + noise, settle=False)
            self.d.run(60)
        self.assertEqual(self.d.tones_since(start), [])

    def test_piece_list_and_back(self):
        self.choose(LIGHT)
        for item, title in [(1, "Fur Elise"), (2, "Ode to Joy"), (3, "Turkish March")]:
            self.d.knob_to_item(item, 4)
            self.assertEqual(self.d.lcd(1), title)
            self.assertEqual(self.d.leds(), 1 << (item - 1))
        self.d.knob_to_item(4, 4)
        self.assertEqual(self.d.lcd(1), "Back")
        self.assertEqual(self.d.leds(), RED)
        self.d.tap(5)
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_confirm_cue_is_heard_before_the_next_screen(self):
        self.d.knob_to_tick(LIGHT)
        start = self.d.now()
        self.d.tap(1)
        tones = [value for _, value in self.d.tones_since(start) if value]
        self.assertTrue(near(tones[0], 523) and near(tones[1], 784), tones)

    def test_yes_no_opens_on_no_and_each_tick_switches(self):
        self.start_to_reset()
        self.assertEqual(self.d.lcd(), ["Clear records?", "> No        Yes"])
        self.assertEqual(self.d.leds(), RED)
        self.d.nudge()
        self.assertEqual(self.d.lcd(1), "  No      > Yes")
        self.assertEqual(self.d.leds(), GREEN)
        self.d.nudge()
        self.assertEqual(self.d.lcd(1), "> No        Yes")
        self.assertEqual(self.d.leds(), RED)

    def test_yes_and_no_have_different_tones(self):
        self.start_to_reset()
        start = self.d.now()
        self.d.nudge()
        yes = [value for _, value in self.d.tones_since(start) if value]
        start = self.d.now()
        self.d.nudge()
        no = [value for _, value in self.d.tones_since(start) if value]
        self.assertGreater(yes[0], no[0] * 2)

    def start_to_reset(self):
        self.choose(RESET)
        self.d.wait_lcd("Clear records?")
        self.d.run(100)

    def test_reset_no_keeps_records(self):
        data = bytearray(self.d.eeprom())
        data[1:4] = bytes([100, 0, 3])
        self.d = Device(eeprom=bytes(data))
        self.d.run(900)
        self.start_to_reset()
        self.d.tap(1)
        self.assertEqual(self.record(0), (100, 3))
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_reset_yes_clears_records(self):
        data = bytearray(self.d.eeprom())
        data[1:4] = bytes([100, 0, 3])
        self.d = Device(eeprom=bytes(data))
        self.d.run(900)
        self.start_to_reset()
        self.d.nudge()
        self.d.tap(1)
        self.d.wait_lcd("Records cleared")
        self.assertEqual(self.record(0), (0, 0))
        self.d.wait_lcd("MAESTRO", timeout=3000)

    def test_free_play_notes_and_exit_without_quit_screen(self):
        self.choose(FREE)
        self.d.wait_lcd("Free play")
        for key, name in enumerate(["Do", "Re", "Mi", "Fa", "Sol", "La", "Si", "Do'"], 1):
            self.d.press(key)
            self.d.run(60)
            self.assertEqual(self.d.lcd(1), name)
            self.assertEqual(self.d.leds(), 1 << (key - 1))
            self.assertEqual(hz_to_key(self.d.tone()), key)
            self.d.release()
            self.d.run(60)
            self.assertEqual(self.d.leds(), 0)
            self.assertEqual(self.d.tone(), 0)
        self.d.nudge()
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_idle_screen_after_a_minute_silent_and_wake_does_not_select(self):
        self.d.knob_to_tick(EAR)
        self.d.run(59000)
        self.assertIn("MAESTRO", self.d.lcd(0))
        self.d.wait_lcd("Turn or press", timeout=2500)
        start = self.d.now()
        seen = set()
        for _ in range(9):
            self.d.run(400)
            seen.add(self.d.leds())
        self.assertEqual(len(seen), 8)
        self.assertEqual(self.d.tones_since(start), [])
        self.d.tap(1)
        self.assertEqual(self.d.lcd(), ["MAESTRO     4/7", "Ear"])

    def test_knob_also_wakes_from_idle(self):
        self.d.run(60500)
        self.d.wait_lcd("Turn or press", timeout=2000)
        self.d.nudge()
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_records_pages(self):
        data = bytearray(self.d.eeprom())
        data[1:4] = bytes([0xD2, 0x04, 5])    # Light, Elise: 1234
        data[10:13] = bytes([0xD4, 0x03, 4])  # Sound, Elise: 980
        data[19:22] = bytes([0xE6, 0x05, 6])  # Both, Elise: 1510
        data[28:31] = bytes([120, 0, 3])      # Ear
        self.d = Device(eeprom=bytes(data))
        self.d.run(900)
        self.choose(RECORDS)
        self.d.knob_to_item(1, 5)
        self.d.wait_lcd("pts")
        self.assertEqual(self.d.lcd(), ["ELISE pts L 1234", "S 980    B 1510"])
        self.d.run(2100)
        self.assertEqual(self.d.lcd(), ["ELISE lvl L 5", "S 4      B 6"])
        self.d.knob_to_item(4, 5)
        self.assertEqual(self.d.lcd(), ["EAR 120 pts", "Best level 3"])
        self.d.knob_to_item(5, 5)
        self.assertEqual(self.d.lcd(1), "Back")
        self.d.tap(1)
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_wrong_version_byte_clears_records_but_right_one_keeps_them(self):
        data = bytearray(b"\xff" * 1024)
        data[0:4] = bytes([0x99, 50, 0, 1])
        self.d = Device(eeprom=bytes(data))
        self.d.run(900)
        self.assertEqual(self.record(0), (0, 0))
        data[0:4] = bytes([0x43, 50, 0, 1])
        self.d = Device(eeprom=bytes(data))
        self.d.run(900)
        self.assertEqual(self.record(0), (50, 1))


class Keys(MaestroTest):
    """Q24, in Free play, where every press is visible."""

    def setUp(self):
        super().setUp()
        self.choose(FREE)
        self.d.wait_lcd("Free play")

    def test_all_keys_decode_through_the_real_ladder_voltages(self):
        for key in range(1, 9):
            self.d.press(key, bounce=False)
            self.d.run(40)
            self.assertEqual(hz_to_key(self.d.tone()), key)
            self.d.release()
            self.d.run(40)

    def test_bounce_gives_one_note(self):
        start = self.d.now()
        self.d.tap(3)
        self.assertEqual(len([v for _, v in self.d.tones_since(start) if v]), 1)

    def test_glitch_shorter_than_debounce_is_ignored(self):
        start = self.d.now()
        self.d.press(3, bounce=False)
        self.d.run(6)
        self.d.release()
        self.d.run(60)
        self.assertEqual(self.d.tones_since(start), [])

    def test_second_key_while_holding_is_ignored_until_release(self):
        self.d.press(2)
        self.d.run(50)
        self.d.press(2, 6, bounce=False)
        self.d.run(100)
        self.assertEqual(hz_to_key(self.d.tone()), 2)
        self.d.release()
        self.d.run(50)
        self.assertEqual(self.d.tone(), 0)

    def test_two_keys_together_read_as_one_stable_key(self):
        # Finding from the ladder maths: Ми + Сол reads as Фа, До + any reads as До.
        self.d.press(3, 5, bounce=False)
        self.d.run(50)
        self.assertEqual(self.d.lcd(1), "Fa")
        self.d.release()
        self.d.run(50)
        self.d.press(1, 8, bounce=False)
        self.d.run(50)
        self.assertEqual(self.d.lcd(1), "Do")


class LadderTolerance(unittest.TestCase):
    """Real resistors are not exact. Firmware decode logic, against random parts."""

    @staticmethod
    def decode(value):
        level = (value + 64) // 128
        return None if level < 1 else 8 - min(level, 8)

    def reading(self, key, ladder, pull_down):
        above = sum(ladder[:key - 1])
        below = sum(ladder[key - 1:])
        if above == 0:
            return 1023
        load = 1 / (1 / below + 1 / pull_down)
        return int(1023 * load / (above + load))

    def test_all_keys_decode_with_5_percent_resistors(self):
        rng = random.Random(1)
        worst = 1000
        for _ in range(20000):
            ladder = [220 * rng.uniform(0.95, 1.05) for _ in range(8)]
            pull_down = 10000 * rng.uniform(0.95, 1.05)
            for key in range(1, 9):
                value = self.reading(key, ladder, pull_down)
                self.assertEqual(self.decode(value), key - 1)
                if key > 1:     # key 1 sits at the top of the range and cannot read too high
                    offset = (value + 64) % 128
                    worst = min(worst, offset, 128 - offset)
        self.assertGreater(worst, 20)      # counts of margin left for ADC noise


class Noise(MaestroTest):
    def test_noisy_a0_within_margin_still_reads_one_key(self):
        self.choose(FREE)
        self.d.wait_lcd("Free play")
        rng = random.Random(2)
        for key in range(1, 9):
            start = self.d.now()
            base = key_voltage_mv(key)
            for _ in range(60):
                noise = rng.randint(-125, 125)     # +-25 counts
                self.d.set_adc(0, min(5000, max(0, base + noise)))
                self.d.run(2)
            self.assertEqual(hz_to_key(self.d.tone()), key)
            self.d.release()
            self.d.run(40)
            self.assertEqual(len([v for _, v in self.d.tones_since(start) if v]), 1)


class HardwareTest(unittest.TestCase):
    def test_hardware_test_build_runs(self):
        d = Device(elf=ROOT / "code" / ".pio" / "build" / "hwtest" / "firmware.elf")
        d.knob_to_tick(4, settle=False)
        d.run(1500)
        d.press(3)
        d.run(200)
        self.assertEqual(hz_to_key(d.tone()), 3)
        self.assertEqual(d.leds(), 4)
        self.assertIn("Mi", d.lcd(0))
        self.assertIn("tick=4", d.lcd(1))


class Power(unittest.TestCase):
    def test_knob_position_at_power_on_is_used(self):
        d = Device(knob_tick=6)
        d.run(900)
        d.wait_lcd("Records")
        self.assertIn("6/7", d.lcd(0))


if __name__ == "__main__":
    unittest.main()
