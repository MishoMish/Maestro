# Маестро – decision log

The record of what has been decided about the software and game logic, and what is still open.
Hardware, pins and the case are described in [HANDOFF_FOR_SOFTWARE_AGENT.md](HANDOFF_FOR_SOFTWARE_AGENT.md).
If the two files disagree about the software, this one wins. Section 5 lists the known corrections to the handoff.

**Last updated:** 2026-11-07

## How to keep this file (AI agents: this applies to you)

- **Read this file before you design or write any firmware.** Do not ask again about anything under "Decided".
- **Only the students make decisions.** A recommendation stays under "Open" until a student accepts it. "All recommended" counts as accepting it.
- **Update this file in the same turn a decision is made,** and change the "Last updated" date.
- **Move a question** from "Open" to "Decided" once it is answered, and keep its ID. Use the next free Q number for new questions.
- **Record what the student actually said,** including any changes they made to the recommendation. If you had to interpret an answer, say so.
- **Do not delete a decision that changes.** Move it to "Superseded" and say what replaced it and why.
- **If a software decision would change the wiring or the printed case,** flag it to the students first. The case depends on the pin map.
- **Add verified facts to "Findings",** and say how each was checked (measured, calculated or from memory).
- **Git:** agents may commit and push with clear messages, but **never add a `Co-Authored-By: Claude` line or any other Claude attribution.** Commits are credited to the student alone.

## 1. Decided

| ID | Topic | Decision | Notes |
| --- | --- | --- | --- |
| Q1 | Toolchain | PlatformIO in VS Code, with the project in `code/`. | The students asked if the difference was big. It is not: the logic is the same, and `.cpp` files only need `#include <Arduino.h>` and functions declared before use. |
| Q2 | Timing | One non-blocking `loop()` with a single `enum State`, timed with `millis()`. No long `delay()`. | A very short wait inside a library call, such as an LCD command, is fine. |
| Q3 | Navigation | Turn the knob to choose, press any key to confirm. Yes/No choices also light the LEDs: **green = yes, red = no**. | The LED rule was added by the students. Details are in Q9. |
| Q4 | Level growth | Each melody has a table of musical cut points (for example 4, 8, 12, 15…), about 8–12 levels per piece. | |
| Q5 | Lives | 3 lives per game, not refilled on level-up. A wrong note costs a life, stops the attempt, plays the feedback and replays the same fragment from its first note. 0 lives = game over. | The students added a way to play with no life limit, which became Easy mode (Q11). |
| Q6 | Time limits and replay | No separate countdown; speed is measured through rhythm (Q12). After 8 s with no key press, the fragment replays and input restarts from its first note, with no life lost. | The students replied that this "will be important regarding speed and rhythm". They then accepted Q12, which states this rule. |
| Q7 | Rhythm | Notes are judged strictly. Rhythm is judged too, at **low priority**: if the playing stops sounding like the song, the attempt is marked as bad. | Replaces the recommendation to judge note order only. The rule is in Q12 and the consequence in Q13. |
| Q8 | Channels in each mode | See the table below. Separation is strict: the piezo is **silent** throughout Light only games, and the key LEDs are **dark** throughout Sound only games. Menus always use every channel. | Keeps the comparison between visual and audio memory fair. |
| Q9 | Navigation rules | Lists end with a Back item. Yes/No screens open on No (red: До, До'). Each knob tick switches between No and Yes (green: Ми, Си), and each choice also has its own tone and LCD text. Turning the knob one tick during a game pauses and opens "Quit?". No resumes by replaying the fragment, with no life lost. | |
| Q10 | The 7 knob ticks | 1 Light only, 2 Sound only, 3 Light + sound, 4 Ear, 5 Free play, 6 Records, 7 Reset records. Moving to tick *n* plays note *n* and lights key *n*. | Free play was not in the proposal. |
| Q11 | Easy mode | Chosen on an "Easy?" Yes/No screen after picking a piece. No life limit, shows `EASY` in place of lives, saves no records. Ends when the piece is finished or the player quits. | |
| Q12 | Measuring rhythm | Compare the time between key presses with the written gap, at the piece's real tempo, so speed counts too. A gap is bad if it is under half or over double the written length. Only the press counts, not how long the key is held. Tempos are set slowly enough for beginners. | |
| Q13 | Result of bad rhythm | Normal: if more than a third of the gaps are bad, a distinct rhythm signal plays (yellow LEDs: Ре, Ла) and the level is retried with no life lost. Easy: it only affects the score, so a player never gets stuck. | |
| Q14 | Ear mode | Each question plays a low До, then the mystery note; auto-replay repeats both. Start with 3 notes (До Ми Сол) and add one per level, with 5 correct answers to move up. Each level starts by playing its possible notes in ascending order. No note twice in a row; random seed from unconnected A5. Same lives and Easy rules, no rhythm judging. Continues at all 8 notes until lives run out. | |
| Q15 | Adapting melodies | Shift *Für Elise* and *Turkish March* along the scale so their key figures fall on real half steps. Leave *Ode to Joy* in C and change only its low G3. Move out-of-range notes by an octave or drop them. Students approve WAV previews by ear before anything goes into the firmware. | The students also asked for a script on the computer that makes every song and exports it for the Arduino. Its design is in Q22. |
| Q16 | Meaning of "whole piece" | The recognisable main theme only: 30–40 notes for *Für Elise*, 30–40 for *Turkish March*, up to 60 for *Ode to Joy*. The report states that these are simplified versions. Finishing a piece counts as winning it. | |
| Q17 | Abandoned game | After 3 auto-replays in a row with no key press, the game returns to the menu. Any record earned is already saved. | |
| Q18 | Scoring | 10 points per note in a passed level, plus 5 per good rhythm gap. Finishing a piece adds 50 per remaining life. Ear: 10 per correct answer. Mistakes subtract nothing. Every game starts at level 1. | |
| Q19 | Records | One record per mode per piece: 9 for the melody modes, 1 for Ear, 10 in total. Each stores best points and best level. The Records screen has one page per piece with Light, Sound and Light + sound side by side, a page for Ear, and Back. | |
| Q20 | Results and sound cues | At the end of a game that uses sound, play one beep per level reached, then a fanfare for a new record. The Records screen stays LCD only; the report states this limitation. **Use sound cues wherever possible, with distinct happy and sad ones.** | The bold rule was added by the students ("I WANT SOUND CUES WHERE POSSIBLE"). Q8's silent Light only games still apply, unless changed; see Q29. |
| Q21 | End of a game | The LCD shows the result and any new record, and keys are ignored for the first second. Any key then returns to the piece list (main menu after Ear). Winning plays the whole piece in the mode's own channels first. | |
| Q22 | Melody script and format | Python, standard library only: `tools/make_songs.py`, with one text file per song in `tools/songs/`. Checks range, lengths and level counts. Generates `code/src/melodies_data.h` and square-wave WAV previews; `--upload` also uploads. One byte per note in PROGMEM (3 bits note, 5 bits length). No separate rests: a rest is added to the previous note's length. Notes sound for about 85% of their length. Built before the firmware. | The students left the tool choice to the agent ("use whatever is best"). Built on 2026-11-07. |
| Q23 | Feedback signals | Correct note: echo only. Wrong: red LEDs and a low buzz. Bad rhythm: yellow LEDs and a wobbling tone. Level up: green LEDs and three rising notes. Game over: LEDs off in sequence and falling notes. Win: LED chase and the whole piece. Each mode uses only its own channels (Q8). **Colour signals light only the keys that have that colour: red = До, До'; yellow = Ре, Ла; green = Ми, Си.** Blue (Фа) and white (Сол) are not used for signals. | The students noted that not every key has every colour. **Interpretation:** this is the bold rule. |
| Q24 | Reading the keys | Read about every 5 ms; a press counts after 3 matching reads, timed from the first. A new press requires a full release. Holding never repeats. Keys are ignored while the prompt plays. A two-key press counts as whatever stable key it reads. No stored calibration; adjust a constant if hardware readings require it. | |
| Q25 | Reading the knob | Split 0–1023 evenly into the list's items, with about 20 counts of hysteresis and a little averaging. One constant reverses direction. Measure A1 at all 7 ticks with the test sketch and adjust if needed. | |
| Q26 | Power bank | Test first: run the test sketch from the bank, untouched, for 10 minutes. Add no keep-alive unless it switches off. No sleep mode. | |
| Q27 | Idle screen | After 60 s with no input in a menu, show a short prompt and a slow LED chase with no sound. The first touch only wakes the device. | |
| Q28 | Code layout and milestones | Small modules: `main.cpp` for the state machine, plus input, output, records and generated melodies. Serial debug behind a compile flag. Milestones: (0) melody script; (1) core engine with one piece in Light + sound; (2) menus and knob; (3) all modes, lives and Easy; (4) rhythm; (5) Ear; (6) scoring and records; (7) feedback polish, idle screen. Each one is a working version. | |
| Q29 | Sound after a Light only game | The piezo stays silent during Light only play (Q8), but the result screen plays the happy or sad cue, because the game is over and it cannot affect the score. | |
| Q30 | EEPROM layout | One version byte, then 10 records of 3 bytes each (2 for points, 1 for level): 31 bytes. A wrong version byte on start-up clears the records. A record is written when a passed level beats it, using `EEPROM.put`, which skips unchanged bytes. Reset is tick 7 with a Yes/No screen. | |
| Q31 | Must-have, nice-to-have and demo | Must: milestones 0–3, 5 and 6, which cover the proposal. Cut first if time runs out: rhythm (4), Easy, Free play, idle screen, polish. Demo of about 3 minutes: power bank start; Ode in Light + sound; Sound only with eyes closed, including a mistake; Light only in silence; Ear; records surviving a power-off. | The students did ask for rhythm and Easy, so the cut list is only a fallback. |
| Q32 | *Ode to Joy* length | Keep the full theme at 62 notes. This changes the "up to 60" limit in Q16 for this piece. | Answered "whatever - yes". |
| Q33 | Leaving Free play | Turning the knob one tick leaves Free play at once, with no "Quit?" screen, because there is nothing to lose. | |
| Q34 | Easy in Ear mode | Ear has no piece list, so the "Easy?" screen appears right after choosing Ear. | |
| Q35 | "Quit?" screen in strict modes | The pause screen counts as a menu, so it uses every channel (Q8), even in Light only and Sound only games. Play resumes in strict mode after No. | |

### Q8: what each mode may use during play

| | Light only | Sound only | Light + sound | Ear |
| --- | --- | --- | --- | --- |
| **Prompt** | LEDs | Piezo | Both | One tone from the piezo |
| **Echo on key press** | LED | Note | Both | Nothing until judged |
| **Correct / wrong / level-up** | LED patterns | Sound cues | Both | Sound cues, then the correct key's LED |
| **LCD** | Level, lives, points | Same, never note names | Same | Same |

## 2. Open: waiting for a student answer

No design questions are open. The students confirmed the design ("You can start cooking") on 2026-11-07.

- **Song approval (Q15):** Михаил approved the songs by ear on 2026-11-07. *Turkish March* still needs checking by someone who knows the tune, because Михаил said they may not know it. No song has been checked against a score.
- **Possible 4th song:** Михаил asked for Azis's "Sen Trope". The agent does not reliably know its notes and did not invent any. Waiting for a student to choose a way forward. This repo is public, so a transcription of that song should not be pushed without thinking about copyright.
- **Agent's implementation choices:** see below. A student can overrule any of them.

## 3. Implementation choices made by the agent

The students asked the agent to iterate to a finished product, so these small details were chosen without asking. They are not student decisions.

| Topic | Choice | Why |
| --- | --- | --- |
| Boot | A short rising scale and LED sweep, then the main menu. | Shows that the device is on, by light and by sound. |
| Menu sounds | Confirm is a short rising cue and Back a short falling cue, on every press. | Q20 asks for sound cues wherever possible. |
| Ear intro | Lights each possible key as it plays. The LCD lists the note names at this point only. | The mystery note is not known yet, so nothing is revealed. |
| Ear order | Notes are added in the order До Ми Сол, then До', Ла, Ре, Фа, Си. | Wide, easy intervals first. |
| Ear answers | Pressing a key outside the current notes counts as wrong. | Simplest rule. |
| Ear levels | Levels keep counting after all 8 notes are in play, and each still takes 5 right answers. | Gives a longer game a higher level. |
| Win playback | Any key skips the whole-piece playback. | *Ode to Joy* takes 38 s. |
| New record | Judged on points only; the level is stored as its own best. | A single clear rule. |
| Light only ending | New-record fanfare is LED only; sad or happy cue is audible (Q29); no level beeps. | Q20 limits beeps and fanfare to games that use sound. |
| Quit or abandon | Partial Ear points are also saved. | Points earned should not be lost. |
| Idle | Also applies after 60 s on the result, Free play and "Quit?" screens. | A forgotten device should not stay on those screens. |

## Status and hardware checks

- **Milestones 0–7:** all built. See [README.md](README.md) for how to use everything and [NEXT_STEPS.md](NEXT_STEPS.md) for what remains.
- **Tools:** `./maestro` does everything, with matching VS Code tasks. Added at the students' request to make uploading and song changes as easy as possible.
- **Tests:** 93 of 93 passed on 2026-11-07, running the real firmware on a simulated ATmega328P, including whole-piece wins. Build size: 46% of flash, 23% of static RAM.
- **Tested on a real Uno R3 with nothing wired (2026-11-07):** see "Findings". How it sounds, the real wiring, switches and knob, the LCD, LEDs and the power bank are all unverified.
- **Students to do on hardware:** follow the checklist in `code/README.md`: A0 at all 8 keys, A1 at all 7 ticks (Q24, Q25), and the 10-minute power-bank test (Q26).
- **Михаил's machine:** `./maestro fix-permissions` has been run. Logging out and in finishes it, and until then `./maestro` works around it.
- **Not tested:** Windows. The live readout in `./maestro hwtest` and `./maestro monitor` was confirmed by Михаил in a real terminal on 2026-11-07.

## 4. Superseded

| ID | Earlier proposal | Replaced by | Why |
| --- | --- | --- | --- |
| Q3 | A one-tick knob turn during a game exits at once. | Q9: the turn opens a "Quit?" screen. | The knob now also chooses Yes or No. |
| Q3 | Keys 1–3 start a piece directly. | Q9: every list item is chosen with the knob. | The students asked for selection with the knob. |
| Q7 | Judge note order only. | Q7 as decided above. | The students want rhythm to matter, at low priority. |

## 5. Findings and corrections to the handoff

| Finding | How it was checked |
| --- | --- |
| **Two keys cannot be detected reliably, so a two-key gesture cannot be used.** Two pressed keys short part of the ladder and can read as a valid third key. Ми + Сол reads about 682, which decodes as Фа. До + any other key reads 1023, which is just До. | Calculated from the ladder design, not yet measured on hardware. |
| **The 10 kΩ pull-down leaves enough margin for decoding keys.** It shifts a reading by about 25 counts at most, leaving at least 38 of the ±64 window. With random ±5% resistors, every key still decoded correctly across 20,000 sets, with at least 21 counts to spare. Expected A0 values: 1023, 878, 742, 614, 489, 368, 247, 125. | Calculated and simulated, not yet measured on hardware. This corrects an earlier figure of 21 counts. |
| **The knob's total travel is not known.** The case only fixes the ticks at −120° to +120°. If the pot turns 270°, 7 even zones are about 38° each, close to the 40° tick spacing. | Ticks checked in `maestro.scad`; the 270° is an assumption. Measure A1 at each tick. |
| **The real Uno accepts and runs the firmware.** Genuine Uno R3 detected on `/dev/ttyACM0` (USB ID 2341:0043). `./maestro upload` and `hwtest` wrote and verified flash, and the serial debug output worked. The debug game reached the main menu at 655 ms, matching the 630 ms boot cue. The game's first start wrote version byte 0x43 and 30 zero bytes to the real EEPROM. | Measured on the real board with nothing wired, 2026-11-07. |
| **The pin count is sufficient, with 3 pins to spare.** The Uno has 20 pins and the design uses 17: keys 1, knob 1, LCD 6, piezo 1, LEDs 8. A5 (random seed), D0 and D1 (Serial) stay free. Without the ladder, the keys would need 8 pins: 24 in total, too many. | Counted from the handoff pin map. |
| **All 8 LEDs can be on at once.** About 100 mA in total: about 14 mA for each red, yellow and green, 9 mA for blue and white. Under the chip's 200 mA total, and A2–A4 are well under their port group's limit. | Calculated from typical LED voltages and datasheet limits from memory, not measured. |
| **LED load should not disturb key or knob decoding.** The ladder and pot run from the same 5 V as the ADC reference, so readings follow any supply dip. | Reasoned from the circuit, not measured. |
| **Only D6, D9 and D10 can fade with PWM among the LED pins,** so LED signals are on/off only. | From the Uno pinout. |
| **The hardware test sketch is at** `print/maestro_case/maestro_hw_test/maestro_hw_test.ino`, not `maestro_hw_test/` as the handoff says. | Checked in the repo. |
| ***Ode to Joy* may not fit as written, contrary to the handoff.** Its middle section normally drops to a low G3, below the keyboard. See Q15. | From memory; confirm against a score. |
| ***Für Elise* can keep its half-step trill on white keys.** See `tools/songs/1_elise.txt` and Q15. | Draft from memory; check it by ear. |
| **All three songs are drafted from memory:** *Für Elise* 33 notes, 8 levels; *Ode to Joy* 62 notes, 12 levels; *Turkish March* 38 notes, 8 levels. | Counts from the script. The notes need checking by ear and against a score. |
| **Adding or removing a song clears all records,** because the layout and version byte change. Adding a 4th song worked on the simulated Uno: it appeared in the piece list, played, and saved to its own record slot. | Simulated with a temporary song on 2026-11-07. |
| **A fast knob turn passes through the ticks in between,** so it plays each one's cue on the way. It always ends on the right item. | Simulated. |
| The melody script can run on Михаил's machine: Python 3.12.3 with the standard `wave` module. | Checked on 2026-11-07. |
| PlatformIO Core 6.2.0 is installed on Михаил's machine. The AVR platform is not, but downloads on the first build.  | Checked on 2026-11-07. |
