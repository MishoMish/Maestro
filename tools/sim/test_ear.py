"""Ear mode (Q14, Q34)."""
import unittest

from base import *  # noqa: F403


class Ear(MaestroTest):
    def start(self, easy=False):
        self.mark = self.d.now()
        self.start_game(EAR, easy=easy)

    def question(self):
        """Wait for the answer turn. Returns (reference key, mystery key)."""
        start = self.d.now()
        self.d.wait_lcd("Play!", timeout=30000)
        keys = [hz_to_key(v) for _, v in self.d.tones_since(start) if v]
        keys = [k for k in keys if k]
        return keys[-2], keys[-1]

    def answer(self, right=True):
        reference, mystery = self.question()
        self.assertEqual(reference, 1)
        key = mystery if right else mystery % 8 + 1
        self.d.tap(key, hold=60, after=60)
        return mystery

    def test_easy_screen_comes_right_after_choosing_ear(self):
        self.choose(EAR)
        self.d.wait_lcd("Easy mode?")

    def test_intro_plays_and_lights_the_starting_notes(self):
        self.start()
        start = self.d.now()
        self.d.wait_lcd("Do Mi Sol")
        self.d.wait_for(lambda: hz_to_key(self.d.tone()) == 1, timeout=2000, what="intro")
        self.d.run(1200)
        tones = [hz_to_key(v) for _, v in self.d.tones_since(start) if v]
        self.assertEqual(tones[:3], [1, 3, 5])
        lit = [m for _, m in self.d.leds_since(start) if m]
        self.assertEqual(lit[:3], [1, 4, 16])

    def test_question_has_no_lights_or_note_name_until_judged(self):
        self.start()
        self.d.wait_lcd("Listen", timeout=5000)
        start = self.d.now()
        self.question()
        self.assertEqual([m for _, m in self.d.leds_since(start) if m], [])

    def test_mystery_is_always_one_of_the_candidates_and_never_repeats(self):
        self.start(easy=True)
        seen = []
        for _ in range(12):
            seen.append(self.answer())
            self.d.run(100)
        for first, second in zip(seen, seen[1:]):
            self.assertNotEqual(first, second)
        self.assertTrue(set(seen[:5]) <= {1, 3, 5}, seen)

    def test_right_answer_scores_and_shows_the_key(self):
        self.start()
        _, mystery = self.question()
        start = self.d.now()
        self.d.tap(mystery, hold=60, after=60)
        self.assertIn("Pts 10", self.d.lcd(1))
        self.assertIn(1 << (mystery - 1), [m for _, m in self.d.leds_since(start)])
        self.assertEqual(self.d.lcd(0), "Ear L1 Lives:3")

    def test_wrong_answer_costs_a_life_and_reveals_the_note(self):
        self.start()
        _, mystery = self.question()
        start = self.d.now()
        self.d.tap(mystery % 8 + 1, hold=60, after=60)
        self.assertEqual(self.d.lcd(0), "Ear L1 Lives:2")
        self.assertIn("Pts 0", self.d.lcd(1))
        self.d.run(900)
        self.assertIn(1 << (mystery - 1), [m for _, m in self.d.leds_since(start)])
        self.assertEqual(hz_to_key([v for _, v in self.d.tones_since(start) if v][-1]), mystery)

    def test_five_right_answers_level_up_and_add_a_note(self):
        self.start()
        for _ in range(5):
            self.answer()
            self.d.run(100)
        self.d.wait_lcd("Do Mi Sol Do'", timeout=3000)
        self.d.wait_lcd("Ear L2", timeout=6000)
        self.assertEqual(self.record(9), (50, 2))

    def test_all_eight_notes_by_level_six_and_it_keeps_going(self):
        self.start()
        for _ in range(25):
            self.answer()
            self.d.run(100)
        self.d.wait_lcd("Do Re Mi Fa Sol", timeout=3000)
        self.assertEqual(self.d.lcd(1), "La Si Do'")
        for _ in range(5):
            self.answer()
            self.d.run(100)
        self.d.wait_lcd("Ear L7", timeout=8000)
        self.assertEqual(self.record(9), (300, 7))

    def test_three_wrong_answers_end_the_game_and_save_points(self):
        self.start()
        self.answer()
        self.d.run(100)
        for _ in range(3):
            self.answer(right=False)
            self.d.run(100)
        self.d.wait_lcd("Game over", timeout=4000)
        self.d.wait_lcd("L1  10 pts", timeout=4000)
        self.assertEqual(self.record(9), (10, 1))
        self.d.run(1500)
        self.d.tap(1)
        self.assertIn("MAESTRO", self.d.lcd(0))      # main menu after Ear (Q21)

    def test_easy_has_no_life_limit_and_saves_nothing(self):
        self.start(easy=True)
        for _ in range(5):
            self.answer(right=False)
            self.d.run(100)
        self.assertEqual(self.d.lcd(0), "Ear L1 EASY")
        self.assertEqual(self.record(9), (0, 0))

    def test_idle_replays_the_question_with_same_note(self):
        self.start()
        _, first = self.question()
        self.d.wait_lcd("Listen", timeout=8300)
        _, second = self.question()
        self.assertEqual(first, second)
        self.assertEqual(self.d.lcd(0), "Ear L1 Lives:3")

    def test_pause_during_intro_restarts_the_intro(self):
        self.start()
        self.d.wait_lcd("Do Mi Sol")
        self.d.nudge()
        self.d.wait_lcd("Quit game?")
        self.d.tap(1)
        self.d.wait_lcd("Do Mi Sol", timeout=1000)
        self.d.wait_lcd("Listen", timeout=4000)

    def test_three_idle_replays_return_to_menu(self):
        self.start()
        self.d.wait_lcd("MAESTRO", timeout=60000)

    def test_pause_no_replays_same_question(self):
        self.start()
        _, first = self.question()
        self.d.nudge()
        self.d.wait_lcd("Quit game?")
        self.d.tap(1)
        _, second = self.question()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
