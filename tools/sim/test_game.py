"""Melody games: channels, lives, rhythm, replay, pause, scoring, records."""
import random
import unittest

from base import *  # noqa: F403


def level_points(notes, good_gaps=None):
    gaps = notes - 1 if good_gaps is None else good_gaps
    return notes * 10 + gaps * 5


class Channels(MaestroTest):
    """Q8: strict separation of light and sound."""

    def expected(self, song):
        return [key for key, _ in self.fragment(song, 1)]

    def test_light_only_prompt_lights_keys_at_real_timing_in_silence(self):
        song = self.start_game(LIGHT, ODE)
        start = self.d.now()
        self.d.wait_lcd("Play!")
        self.assertEqual(self.d.tones_since(start), [])
        ons = [(t, mask) for t, mask in self.d.leds_since(start) if mask]
        offs = [(t, mask) for t, mask in self.d.leds_since(start) if not mask]
        self.assertEqual([mask for _, mask in ons], [1 << (k - 1) for k in self.expected(song)])
        # Repeated notes (Ми Ми) must show as two separate flashes.
        for (on_t, _), (off_t, _) in zip(ons, offs):
            self.assertAlmostEqual(off_t - on_t, 510, delta=15)    # 85% of 600 ms
        self.assertAlmostEqual(ons[1][0] - ons[0][0], 600, delta=10)

    def test_sound_only_prompt_plays_notes_with_dark_leds(self):
        song = self.start_game(SOUND, ODE)
        start = self.d.now()
        self.d.wait_lcd("Play!")
        self.assertEqual([m for _, m in self.d.leds_since(start) if m], [])
        self.assert_tones(self.d.tones_since(start), self.expected(song))

    def test_light_and_sound_uses_both(self):
        song = self.start_game(BOTH, ODE)
        start = self.d.now()
        self.d.wait_lcd("Play!")
        self.assert_tones(self.d.tones_since(start), self.expected(song))
        ons = [mask for _, mask in self.d.leds_since(start) if mask]
        self.assertEqual(ons, [1 << (k - 1) for k in self.expected(song)])

    def test_prompt_data_matches_song_file_for_all_three_pieces(self):
        for piece in (ELISE, ODE, TURKISH):
            self.setUp()
            song = self.start_game(SOUND, piece)
            start = self.d.now()
            self.d.wait_lcd("Play!")
            self.assert_tones(self.d.tones_since(start), [k for k, _ in self.fragment(song, 1)])

    def test_light_only_whole_level_including_feedback_is_silent(self):
        song = self.start_game(LIGHT, ODE)
        start = self.d.now()
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.play(song, 2, scale=3)         # bad rhythm signal
        self.d.wait_lcd("Rhythm")
        self.lose_lives(song, 1)            # wrong note signal
        self.d.run(500)
        self.assertEqual(self.d.tones_since(start), [])

    def test_sound_only_whole_level_including_feedback_is_dark(self):
        song = self.start_game(SOUND, ODE)
        start = self.d.now()
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.play(song, 2, scale=3)
        self.d.wait_lcd("Rhythm")
        self.lose_lives(song, 1)
        self.d.run(500)
        self.assertEqual([m for _, m in self.d.leds_since(start) if m], [])

    def test_echo_follows_the_mode_while_key_is_held(self):
        for tick, light, sound in [(LIGHT, True, False), (SOUND, False, True), (BOTH, True, True)]:
            self.setUp()
            song = self.start_game(tick, ODE)
            self.d.wait_lcd("Play!")
            key = song["notes"][0][0] + 1
            self.d.press(key)
            self.d.run(100)
            self.assertEqual(self.d.leds() == 1 << (key - 1), light)
            self.assertEqual(hz_to_key(self.d.tone()) == key, sound)
            self.d.release()
            self.d.run(50)
            self.assertEqual(self.d.leds(), 0)
            self.assertEqual(self.d.tone(), 0)

    def test_lcd_never_shows_note_names_during_play(self):
        song = self.start_game(SOUND, ODE)
        names = ("Do", "Re", "Mi", "Fa", "Sol", "La", "Si")
        for _ in range(40):
            self.d.run(100)
            for name in names:
                self.assertNotIn(name, " ".join(self.d.lcd()))


class Lives(MaestroTest):
    def test_game_screen_starts_with_three_lives(self):
        self.start_game(BOTH, ODE)
        self.assertEqual(self.d.lcd(), ["L1/12 Lives:3", "Pts 0     Listen"])

    def test_wrong_note_costs_a_life_and_replays_same_fragment(self):
        song = self.start_game(BOTH, ODE)
        self.lose_lives(song, 1)
        self.assertIn("Lives:2", self.d.lcd(0))
        self.assertIn("Wrong!", self.d.lcd(1))
        start = self.d.now()
        self.d.wait_lcd("Play!")
        played = [hz_to_key(v) for _, v in self.d.tones_since(start) if v and hz_to_key(v)]
        self.assertEqual(played, [k for k, _ in self.fragment(song, 1)])
        self.assertIn("L1/12", self.d.lcd(0))

    def test_wrong_cue_uses_red_leds_and_low_tone(self):
        song = self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        start = self.d.now()
        self.d.tap((song["notes"][0][0] + 1) % 8 + 1, hold=60, after=60)
        masks = [m for _, m in self.d.leds_since(start) if m]
        tones = [v for _, v in self.d.tones_since(start) if v]
        self.assertEqual(masks[0], RED)
        self.assertLess(tones[0], 200)

    def test_mistake_mid_fragment_restarts_from_first_note(self):
        song = self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        notes = self.fragment(song, 1)
        self.d.tap(notes[0][0], hold=200, after=400)
        self.d.tap(notes[1][0] % 8 + 1)
        self.assertIn("Lives:2", self.d.lcd(0))
        self.play(song, 1)     # the full fragment again
        self.d.wait_lcd("L2/12")

    def test_three_mistakes_end_the_game_with_sad_cue_in_light_only(self):
        song = self.start_game(LIGHT, ODE)
        start = self.d.now()
        self.lose_lives(song, 3)
        self.d.wait_lcd("Game over")
        self.assertEqual(self.d.tones_since(start), [])     # still silent during the signal
        self.d.wait_for(lambda: self.d.tone() > 0, timeout=3000, what="sad cue")
        self.d.run(1000)
        tones = [v for _, v in self.d.tones_since(start) if v]
        self.assertEqual(len(tones), 3)                     # Q29, no level beeps
        for tone, target in zip(tones, [392, 311, 262]):
            self.assertTrue(near(tone, target), tones)

    def test_lives_do_not_refill_on_level_up(self):
        song = self.start_game(BOTH, ODE)
        self.lose_lives(song, 1)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.assertIn("Lives:2", self.d.lcd(0))


class Easy(MaestroTest):
    def test_no_life_limit_and_shows_easy(self):
        song = self.start_game(BOTH, ODE, easy=True)
        self.lose_lives(song, 5)
        self.d.wait_lcd("Listen")
        self.assertEqual(self.d.lcd(0), "L1/12 EASY")

    def test_saves_no_records(self):
        song = self.start_game(BOTH, ODE, easy=True)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.assertEqual(self.record(2 * 3 + 1), (0, 0))

    def test_bad_rhythm_passes_with_fewer_points(self):
        song = self.start_game(BOTH, ODE, easy=True)
        self.play(song, 1, scale=3)
        self.d.wait_lcd("L2/12")
        self.assertIn("Pts 40", self.d.lcd(1))     # 4 notes, no good gaps


class Rhythm(MaestroTest):
    """Q12, Q13. Ode level 1: 4 notes, 3 gaps of 600 ms."""

    def outcome(self, scales):
        song = self.start_game(BOTH, ODE)
        self.play(song, 1, scales=scales)
        self.d.wait_for(lambda: "L2/12" in self.d.lcd(0) or "Rhythm" in self.d.lcd(1),
                        timeout=2000, what="judged")
        return "pass" if "L2/12" in self.d.lcd(0) else "rhythm"

    def test_exact_rhythm_passes_with_full_points(self):
        self.assertEqual(self.outcome([1, 1, 1]), "pass")
        self.assertIn("Pts 55", self.d.lcd(1))

    def test_one_bad_gap_of_three_still_passes_with_fewer_points(self):
        self.assertEqual(self.outcome([1, 3, 1]), "pass")
        self.assertIn("Pts 50", self.d.lcd(1))

    def test_two_bad_gaps_of_three_is_marked_bad(self):
        self.assertEqual(self.outcome([3, 3, 1]), "rhythm")

    def test_bad_rhythm_retries_level_with_no_life_lost_and_yellow_leds(self):
        song = self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        self.play(song, 1, scale=3)
        start = self.d.now() - 300
        self.d.wait_lcd("Rhythm")
        self.d.run(200)
        self.assertIn(YELLOW, [m for _, m in self.d.leds_since(start)])
        self.assertEqual(self.d.lcd(0), "L1/12 Lives:3")
        self.assertIn("Pts 0", self.d.lcd(1))
        self.play(song, 1)
        self.d.wait_lcd("L2/12")

    def test_half_and_double_are_the_limits(self):
        for scale, expected in [(0.55, "pass"), (0.40, "rhythm"), (1.9, "pass"), (2.2, "rhythm")]:
            self.setUp()
            self.assertEqual(self.outcome([scale] * 3), expected, f"scale {scale}")

    def test_human_timing_within_a_third_passes_in_every_piece(self):
        rng = random.Random(3)
        for piece in (ELISE, ODE, TURKISH):
            self.setUp()
            song = self.start_game(BOTH, piece)
            notes = len(self.fragment(song, 1))
            self.play(song, 1, scales=[rng.uniform(0.67, 1.33) for _ in range(notes)])
            self.d.wait_for(lambda: "L2/" in self.d.lcd(0), timeout=3000, what=song["title"])

    def test_slow_even_playing_fails_because_speed_counts(self):
        self.assertEqual(self.outcome([2.5, 2.5, 2.5]), "rhythm")


class Replay(MaestroTest):
    """Q6, Q17."""

    def test_no_press_for_8_seconds_replays_with_no_life_lost(self):
        self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        start = self.d.now()
        self.d.wait_lcd("Listen", timeout=8300)
        self.assertGreaterEqual(self.d.now() - start, 7900)
        self.assertEqual(self.d.lcd(0), "L1/12 Lives:3")

    def test_pause_mid_fragment_restarts_it(self):
        song = self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        notes = self.fragment(song, 1)
        self.d.tap(notes[0][0], hold=200, after=400)
        self.d.wait_lcd("Listen", timeout=8300)
        self.assertEqual(self.d.lcd(0), "L1/12 Lives:3")
        self.play(song, 1)
        self.d.wait_lcd("L2/12")

    def test_holding_a_key_is_not_idle_and_does_not_repeat(self):
        song = self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        self.d.press(song["notes"][0][0] + 1)
        self.d.run(9000)
        self.assertIn("Play!", self.d.lcd(1))
        self.assertEqual(self.d.lcd(0), "L1/12 Lives:3")
        self.d.release()

    def test_three_replays_with_no_input_return_to_menu(self):
        self.start_game(BOTH, ODE)
        self.d.wait_lcd("MAESTRO", timeout=60000)
        self.assertGreater(self.d.now(), 32000)

    def test_a_press_resets_the_replay_count(self):
        song = self.start_game(BOTH, ODE)
        for _ in range(2):
            self.d.wait_lcd("Play!")
            self.d.wait_lcd("Listen", timeout=8300)
        self.d.wait_lcd("Play!")
        self.d.tap(song["notes"][0][0] + 1)
        for _ in range(3):
            self.d.wait_lcd("Listen", timeout=8300)
            self.d.wait_lcd("Play!")
        self.assertIn("Lives:3", self.d.lcd(0))


class Pause(MaestroTest):
    """Q9, Q35."""

    def test_knob_during_prompt_opens_quit_on_no(self):
        self.start_game(LIGHT, ODE)
        self.d.wait_lcd("Watch")
        self.d.run(800)
        start = self.d.now()
        self.d.nudge()
        self.assertEqual(self.d.lcd(), ["Quit game?", "> No        Yes"])
        self.assertEqual(self.d.leds(), RED)
        self.assertTrue(self.d.tones_since(start))      # menus use every channel, even in Light only

    def test_no_resumes_by_replaying_with_no_life_lost(self):
        song = self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        self.d.nudge()
        self.d.wait_lcd("Quit game?")
        self.d.tap(1)
        start = self.d.now()
        self.d.wait_lcd("Play!")
        self.assertEqual(self.d.lcd(0), "L1/12 Lives:3")
        self.assert_tones([t for t in self.d.tones_since(start) if hz_to_key(t[1]) or not t[1]],
                          [k for k, _ in self.fragment(song, 1)])

    def test_strict_mode_returns_after_no(self):
        self.start_game(LIGHT, ODE)
        self.d.wait_lcd("Play!")
        self.d.nudge()
        self.d.wait_lcd("Quit game?")
        self.d.tap(1)
        self.d.run(400)                                  # confirm cue finished
        start = self.d.now()
        self.d.wait_lcd("Play!")
        self.assertEqual(self.d.tones_since(start), [])

    def test_yes_quits_to_menu_at_the_current_tick(self):
        self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        self.d.nudge()
        self.d.nudge()
        self.assertEqual(self.d.lcd(1), "  No      > Yes")
        self.d.tap(1)
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_pause_during_last_wrong_cue_still_ends_the_game_after_no(self):
        song = self.start_game(BOTH, ODE)
        self.lose_lives(song, 2)
        self.d.wait_lcd("Play!")
        self.d.tap(song["notes"][0][0] % 8 + 2, hold=40, after=20)
        self.d.nudge()
        self.d.wait_lcd("Quit game?")
        self.d.tap(1)
        self.d.wait_lcd("Game over", timeout=2000)

    def test_pause_during_level_up_resumes_at_the_new_level(self):
        song = self.start_game(BOTH, ODE)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.d.nudge()
        self.d.wait_lcd("Quit game?")
        self.d.tap(1)
        self.d.wait_lcd("Play!")
        self.assertEqual(self.d.lcd(0), "L2/12 Lives:3")

    def test_paused_game_left_alone_goes_to_idle(self):
        self.start_game(BOTH, ODE)
        self.d.wait_lcd("Play!")
        self.d.nudge()
        self.d.wait_lcd("Quit game?")
        self.d.wait_lcd("Turn or press", timeout=62000)
        self.d.nudge()
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_quitting_keeps_saved_records(self):
        song = self.start_game(BOTH, ODE)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.d.nudge()
        self.d.nudge()
        self.d.tap(1)
        self.assertEqual(self.record(2 * 3 + 1), (55, 2))

    def test_keys_do_not_count_while_prompt_plays_or_while_held_past_it(self):
        song = self.start_game(BOTH, ODE)
        self.d.wait_lcd("Listen")
        self.d.run(700)
        self.d.tap(8)
        self.assertEqual(self.d.lcd(0), "L1/12 Lives:3")
        self.d.press(8)
        self.d.wait_lcd("Play!")
        self.d.run(200)
        self.d.release()
        self.d.run(100)
        self.assertEqual(self.d.lcd(0), "L1/12 Lives:3")
        for key, gap in self.fragment(song, 1):
            self.d.press(key)
            self.d.run(gap * 0.5)
            self.d.release()
            self.d.run(gap * 0.5 - 4)
        self.d.wait_lcd("L2/12", timeout=2000)


class Results(MaestroTest):
    """Q18-Q21, Q29, Q30."""

    def test_points_and_levels_add_up_and_save_on_each_level(self):
        song = self.start_game(BOTH, ODE)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.assertIn("Pts 55", self.d.lcd(1))
        self.assertEqual(self.record(2 * 3 + 1), (55, 2))
        self.play(song, 2)
        self.d.wait_lcd("L3/12")
        total = 55 + level_points(8)
        self.assertIn(f"Pts {total}", self.d.lcd(1))
        self.assertEqual(self.record(2 * 3 + 1), (total, 3))

    def test_record_slot_is_per_mode_and_piece(self):
        for tick, piece, slot in [(LIGHT, ELISE, 0), (SOUND, TURKISH, 5), (BOTH, ODE, 7)]:
            self.setUp()
            song = self.start_game(tick, piece)
            self.play(song, 1)
            self.d.wait_for(lambda: "L2/" in self.d.lcd(0), timeout=3000, what="level 2")
            data = self.d.eeprom()
            filled = [i for i in range(10) if data[1 + i * 3] or data[2 + i * 3]]
            self.assertEqual(filled, [slot])

    def test_record_survives_power_cycle_and_shows_on_page(self):
        song = self.start_game(SOUND, ODE)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        d = self.d.power_cycle()
        self.d = d
        d.run(900)
        d.wait_lcd("MAESTRO")
        self.assertEqual(self.record(1 * 3 + 1), (55, 2))
        self.choose(RECORDS)
        d.knob_to_item(2, 5)
        d.wait_lcd("ODE")
        self.assertEqual(d.lcd(1), "S 55     B 0")

    def test_lower_score_does_not_overwrite_record(self):
        data = bytearray(self.d.eeprom())
        data[1 + 7 * 3:4 + 7 * 3] = bytes([200, 0, 9])
        from device import Device
        self.d = Device(eeprom=bytes(data))
        self.d.run(900)
        song = self.start_game(BOTH, ODE)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.assertEqual(self.record(7), (200, 9))

    def test_game_over_beeps_once_per_level_and_fanfare_for_new_record(self):
        song = self.start_game(SOUND, ODE)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        start = self.d.now()
        self.lose_lives(song, 3)
        self.d.wait_lcd("Game over")
        self.d.run(5000)
        tones = [v for _, v in self.d.tones_since(start) if v]
        self.assertEqual(len([t for t in tones if near(t, 880)]), 2)   # level 2
        self.assertTrue(near(tones[-1], 1047), tones)                   # fanfare
        self.assertEqual(self.d.lcd(1), "L2  55 pts")

    def test_new_record_text_alternates(self):
        song = self.start_game(BOTH, ODE)
        self.play(song, 1)
        self.d.wait_lcd("L2/12")
        self.lose_lives(song, 3)
        self.d.wait_lcd("NEW RECORD!", timeout=6000)
        self.d.wait_lcd("Game over", timeout=2000)

    def test_no_fanfare_without_a_new_record(self):
        song = self.start_game(BOTH, ODE)
        start = self.d.now()
        self.lose_lives(song, 3)
        self.d.wait_lcd("Game over")
        self.d.run(4000)
        tones = [v for _, v in self.d.tones_since(start) if v]
        self.assertFalse([t for t in tones if near(t, 1047)], tones)
        self.assertEqual(len([t for t in tones if near(t, 880)]), 1)

    def test_result_ignores_keys_for_one_second_then_returns_to_piece_list(self):
        song = self.start_game(BOTH, ODE)
        self.lose_lives(song, 3)
        self.d.wait_for(lambda: self.d.lcd(1).startswith("L1"), timeout=4000, what="result")
        self.d.run(200)
        self.d.tap(1, hold=50, after=50)
        self.assertEqual(self.d.lcd(0), "Game over")
        self.d.run(1000)
        self.d.tap(1)
        self.assertIn("Piece", self.d.lcd(0))

    def test_result_left_alone_goes_to_idle(self):
        song = self.start_game(BOTH, ODE)
        self.lose_lives(song, 3)
        self.d.wait_lcd("Game over")
        self.d.wait_lcd("Turn or press", timeout=70000)
        self.d.tap(1)
        self.assertIn("MAESTRO", self.d.lcd(0))

    def test_turkish_has_eight_levels_on_screen(self):
        self.start_game(LIGHT, TURKISH)
        self.d.wait_lcd("L1/8")


if __name__ == "__main__":
    unittest.main()
