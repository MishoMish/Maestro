"""Whole pieces from level 1 to the win. Slow: several simulated minutes each."""
import unittest

from base import *  # noqa: F403


class FullGames(MaestroTest):
    def win(self, tick, piece, levels):
        song = self.start_game(tick, piece)
        total = 0
        for level in range(1, levels + 1):
            self.play(song, level)
            notes = song["cuts"][level - 1]
            total += notes * 10 + (notes - 1) * 5
            if level < levels:
                self.d.wait_lcd(f"L{level + 1}/{levels}", timeout=4000)
        return song, total

    def check_win(self, tick, piece, slot, sound, light):
        song = load_song(SONGS[piece])
        levels = len(song["cuts"])
        song, total = self.win(tick, piece, levels)
        total += 150                                 # 3 lives left
        self.d.wait_lcd("You win!", timeout=5000)
        start = self.d.now()
        self.d.run(1200)                             # end of the win signal
        self.d.wait_for(lambda: f"{total} pts" in self.d.lcd(1), timeout=80000, what="result")
        played = [k + 1 for k, _ in song["notes"]]
        if sound:
            heard = [hz_to_key(v) for _, v in self.d.tones_since(start) if v]
            heard = [k for k in heard if k]
            for index in range(len(heard) - len(played) + 1):
                if heard[index:index + len(played)] == played:
                    break
            else:
                self.fail(f"whole piece not heard: {heard}")
        if tick == LIGHT:      # silent until the result's happy cue (Q8, Q29), and no fanfare sound
            self.d.run(3000)
            self.assertEqual(len([v for _, v in self.d.tones_since(start) if v]), 4)
        if tick == SOUND:      # dark until the result's cues
            self.d.run(3000)
            lit = {m for _, m in self.d.leds_since(start) if m}
            self.assertTrue(lit <= {GREEN, 255}, lit)
        if light:
            lit = [m for _, m in self.d.leds_since(start) if m]
            wanted = [1 << (k - 1) for k in played]
            self.assertTrue(any(lit[i:i + len(wanted)] == wanted for i in range(len(lit))),
                            "whole piece not shown on the LEDs")
        self.assertEqual(self.record(slot), (total, levels))
        self.assertEqual(self.d.lcd(1), f"L{levels}  {total} pts")
        self.d.run(5000)
        # Enough stack left: RAM above the static data must never be reached.
        self.assertGreater(self.d.min_stack_pointer(), 0x100 + 480 + 256)
        self.d.tap(1)
        self.assertIn("Piece", self.d.lcd(0))

    def test_win_elise_light_and_sound(self):
        self.check_win(BOTH, ELISE, 6, True, True)

    def test_win_turkish_light_only(self):
        self.check_win(LIGHT, TURKISH, 2, False, True)

    def test_win_elise_sound_only(self):
        self.check_win(SOUND, ELISE, 3, True, False)

    def test_win_ode_sound_only(self):
        self.check_win(SOUND, ODE, 4, True, False)

    def test_easy_win_adds_no_bonus_and_no_record(self):
        song = self.start_game(BOTH, ELISE, easy=True)
        total = 0
        for level in range(1, 9):
            self.play(song, level, scale=3)            # bad rhythm never blocks in Easy
            total += song["cuts"][level - 1] * 10
            if level < 8:
                self.d.wait_lcd(f"L{level + 1}/8", timeout=4000)
        self.d.wait_lcd("You win!", timeout=5000)
        self.d.wait_for(lambda: f"{total} pts" in self.d.lcd(1), timeout=30000, what="result")
        self.assertEqual(self.record(6), (0, 0))

    def test_key_skips_the_win_playback(self):
        song = load_song("elise")
        self.win(BOTH, ELISE, len(song["cuts"]))
        self.d.wait_lcd("You win!", timeout=5000)
        self.d.run(1600)
        self.d.tap(1)
        self.d.run(100)
        self.assertRegex(self.d.lcd(1), r"L8  \d+ pts")


if __name__ == "__main__":
    unittest.main()
