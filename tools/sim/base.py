"""Shared helpers for the Маестро tests."""
import unittest

from device import Device, load_song

NOTE_HZ = [262, 294, 330, 349, 392, 440, 494, 523]
LIGHT, SOUND, BOTH, EAR, FREE, RECORDS, RESET = 1, 2, 3, 4, 5, 6, 7
ELISE, ODE, TURKISH = 1, 2, 3
SONGS = {ELISE: "elise", ODE: "ode", TURKISH: "turkish"}
RED, YELLOW, GREEN = 0b10000001, 0b00100010, 0b01000100


def near(hz, target):
    """The timer cannot hit every frequency exactly. The real error is under 1%."""
    return abs(hz - target) <= target * 0.01 + 1


def hz_to_key(hz):
    """1-8 for a note frequency, or None."""
    for index, note in enumerate(NOTE_HZ):
        if abs(hz - note) <= note * 0.02:
            return index + 1
    return None


class MaestroTest(unittest.TestCase):
    def setUp(self):
        self.d = Device()
        self.d.run(900)
        self.d.wait_lcd("MAESTRO")

    def choose(self, tick):
        self.d.knob_to_tick(tick)
        self.d.tap(1)

    def start_game(self, tick, piece=None, easy=False):
        """From the main menu to the first melody or Ear intro. Returns the song."""
        self.choose(tick)
        if tick != EAR:
            self.d.knob_to_item(piece, 4)
            self.d.tap(1)
        self.d.wait_lcd("Easy mode?")
        if easy:
            self.d.nudge()
            self.assertIn("> Yes", self.d.lcd(1))
        self.d.tap(1)
        return load_song(SONGS[piece]) if piece else None

    def fragment(self, song, level):
        """(key 1-8, gap ms) for the notes of a 1-based level."""
        count = song["cuts"][level - 1]
        return [(key + 1, length * song["sixteenth_ms"]) for key, length in song["notes"][:count]]

    def play(self, song, level, scale=1.0, scales=None):
        """Wait for the turn, then play a level. scales overrides the timing per gap."""
        self.d.wait_lcd("Play!", timeout=120000)
        notes = self.fragment(song, level)
        for index, (key, gap) in enumerate(notes):
            factor = scales[index] if scales and index < len(scales) else scale
            total = gap * factor
            if index == len(notes) - 1:
                self.d.tap(key)
            else:
                hold = max(30, total * 0.5)
                self.d.press(key)
                self.d.run(hold)
                self.d.release()
                self.d.run(total - hold - 4)

    def lose_lives(self, song, count):
        """Press a wrong key count times, waiting for the turn each time."""
        for _ in range(count):
            self.d.wait_lcd("Play!", timeout=120000)
            first = song["notes"][0][0] + 1
            self.d.tap(first % 8 + 1)
            self.d.run(100)

    def record(self, index):
        data = self.d.eeprom()
        offset = 1 + index * 3
        return data[offset] | data[offset + 1] << 8, data[offset + 2]

    def assert_tones(self, tones, expected_keys):
        played = [hz_to_key(value) or value for _, value in tones if value]
        self.assertEqual(played, expected_keys)
