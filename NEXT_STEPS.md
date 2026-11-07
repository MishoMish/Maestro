# Steps to finish Маестро

Work from top to bottom and tick things off. Skip anything you've already done, such as printing. Commands are explained in the [README](README.md).

**Already done:** the design, all the firmware, the song tools and 93 tests on a simulated Uno. The game is uploaded and starts on the real Uno, tested with nothing wired, so the keys, knob, LCD, LEDs and piezo are still unproven.

## 1. Set up your computers

- [x] Run `./maestro check`, then `./maestro fix-permissions` if it asks you to (done on Михаил's computer; log out and in once to finish).
- [ ] Give Богомил the code and have them run `./maestro check` too. On Windows, use `python tools\maestro_cli.py check`; this hasn't been tried on Windows yet.

- [x] Test the bare Uno with `./maestro selftest` (100 of 100 passed on Михаил's board).

## 2. Approve the songs

The songs were written from memory, so they may have wrong notes.

- [x] Listen to all three with `./maestro listen` (approved by Михаил).
- [ ] Have someone who knows *Turkish March* listen to it, or compare it with a recording of Mozart's "Rondo alla Turca".
- [ ] Check the songs against a score, especially *Turkish March*, and *Ode to Joy*'s middle section.
- [ ] Fix anything wrong, using [the song guide](tools/songs/README.md).

## 3. Review the small choices

- [ ] Read section 3 of [DECISIONS.md](DECISIONS.md), which lists details that were chosen for you, and change any you dislike.

## 4. Print the case

Follow [HOW_TO_PRINT.md](print/maestro_case/plates/HOW_TO_PRINT.md).

- [ ] Print plate 0, the test pieces, first. Check the key and LCD fit before printing the rest.
- [ ] Print plates 1 to 5.

## 5. Wire and test

Follow [the build guide](docs/index.html), which has a diagram for every step. Test before closing the box.

- [ ] Run `./maestro hwtest`. Every LED should light once, in key order.
- [ ] Adjust the LCD contrast pot until text is visible.
- [ ] Press each key: it should light its own LED and play its own note.
- [ ] Note the `A0` value for all 8 keys. Expected: 1023, 878, 742, 614, 489, 368, 247, 125, within about 30.
- [ ] Turn the knob to all 7 ticks: `tick=` should show 1 to 7, in order. If it runs backwards, set `KNOB_REVERSED` in [config.h](code/src/config.h).
- [ ] Add the measured values to "Findings" in [DECISIONS.md](DECISIONS.md).

## 6. Assemble

- [ ] Finish the assembly, following [the case guide](print/maestro_case/README.md).
- [ ] Run `./maestro hwtest` again, because wires can come loose when closing the box.

## 7. Play it on the real device

Run `./maestro upload`. These are what the simulator can't check:

- [ ] **Sound:** is the piezo loud enough, and do the happy and sad cues sound right?
- [ ] **Light:** are the LEDs bright enough through the keys, with no glow into the next key?
- [ ] **Keys:** does every press count, with no double presses?
- [ ] **Knob:** does each tick mark line up with its menu item?
- [ ] **LCD:** is it readable at the panel's angle?
- [ ] **Light only:** silent during play, in a full game?
- [ ] **Sound only:** can you play with your eyes closed, and are the LEDs dark?
- [ ] **Ear:** can you tell the notes apart?
- [ ] **Records:** do they survive unplugging?
- [ ] **Reset records:** does tick 7 clear them?

## 8. Test the power bank

- [ ] Run it from the bank, untouched, for 10 minutes.
- [ ] If it switches off, try another bank. The firmware has no keep-alive, because flashing the LEDs to draw current would break the dark-LED rule in Sound only.

## 9. Try it on people

- [ ] Have a beginner, ideally a child, play without help.
- [ ] Is the rhythm rule fair, or too strict? Are the tempos comfortable? Adjust `tempo=` in the song files if needed. The rhythm limits are in `handleMelodyPress` in [main.cpp](code/src/main.cpp).
- [ ] Do they understand the menu?

## 10. Finish the code

- [ ] Run `./maestro test --all`. Some tests expect the current songs and rules, so after changing those, update the tests or check that any failures are expected.
- [ ] Merge the `firmware` branch into `main` and push.
- [ ] Run `./maestro upload`, then clear your test scores with tick 7.

## 11. Write the report

These need stating plainly:

- [ ] What the project is and how it meets the proposal, feature by feature.
- [ ] The songs are simplified: main themes only, adapted to 8 white keys ([DECISIONS.md](DECISIONS.md) Q15, Q16).
- [ ] The records use one score per mode per piece, not only per mode, and why (Q19).
- [ ] Limitations: the Records screen is LCD only (Q20), and pressing two keys at once can read as a third key.
- [ ] How it was tested: simulated first, then on the device.
- [ ] Photos of the device.

## 12. Publish the build guide

- [ ] Take real photos of each stage and add them to [the guide](docs/index.html). It only has generated diagrams and computer renders so far.
- [ ] Update the guide if building it for real showed any step was wrong, especially the contrast pot's leg spacing and whether the kit's wires are long enough.
- [ ] After merging to `main`, change `BRANCH` in [build_guide.py](tools/guide/build_guide.py) and rebuild, so that its download command stays right.
- [ ] To publish it on GitHub, turn on Pages for the `/docs` folder in the repository's settings.

## 13. Prepare the demo

- [ ] Rehearse the script, about 3 minutes:
  1. Start from the power bank.
  2. Play *Ode to Joy* in Light + sound.
  3. Play Sound only with eyes closed, including a mistake for the sad cue.
  4. Play Light only in silence.
  5. Play Ear mode.
  6. Unplug and replug to show that the records survive.
- [ ] Earn a real record beforehand, so the Records screen isn't empty.
- [ ] Bring a spare power bank, a USB cable, and a laptop that can run `./maestro upload`.

## 14. After the demo

- [ ] Return the borrowed kit parts unmodified. Nothing may be soldered or glued.

## If time runs out

Cut these first, in any order: rhythm judging, Easy, Free play, the idle screen and polish (Q31). The proposal doesn't depend on them.
