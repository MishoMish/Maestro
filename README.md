# Маестро

A standalone device that trains musical hearing and memory. It plays a melody by light, sound or both, and you repeat it on 8 piano keys. Built on an Arduino Uno by Богомил Стоянов and Михаил Доброславски.

**What to do next:** see [NEXT_STEPS.md](NEXT_STEPS.md). **To build one:** see the [build guide](docs/index.html).

## Quick start

Open this folder in VS Code, open a terminal, and run:

```
./maestro
```

A menu opens, and you type a number. The first time, do these in order:

1. **Check that this computer is ready.** It says exactly what to fix.
2. **Allow uploads to the Uno.** Asks for your password, once only.
3. **Test the wiring**, with the Uno plugged in.
4. **Upload the game.**

To upload from VS Code without a terminal, press **Ctrl+Shift+B**. Other actions are under **Terminal → Run Task**, each starting with `Maestro:`.

## All commands

| Command | What it does | Uno needed? |
| --- | --- | --- |
| `./maestro` | Opens the menu | |
| `./maestro check` | Checks this computer and says what to fix | |
| `./maestro fix-permissions` | Allows uploads on Linux, once only | |
| `./maestro hwtest` | Uploads the hardware test and shows live key and knob readings | Yes |
| `./maestro upload` | Checks the songs, then uploads the game | Yes |
| `./maestro selftest` | Plays the real game on the Uno's own chip with a scripted player, about 20 minutes. Nothing needs to be wired. Puts the game back afterwards | Yes |
| `./maestro songs` | Checks every song and rebuilds the previews | |
| `./maestro listen` | Plays every song | |
| `./maestro listen ode` | Plays one song; part of its name is enough | |
| `./maestro listen ode 3` | Plays level 3 of a song and prints its notes | |
| `./maestro build` | Checks that the firmware compiles | |
| `./maestro monitor` | Uploads the game with a log of state changes | Yes |
| `./maestro test` | Runs the tests on a simulated Uno, wired exactly as the build guide says | |
| `./maestro test --all` | Also plays whole pieces; takes about 15 minutes | |
| `./maestro help` | Lists the commands | |

Press **Ctrl+C** to stop anything that keeps running. On Windows, use `python tools\maestro_cli.py` in place of `./maestro`; this has not been tried on Windows yet.

## Common jobs

### Change a song

1. Open its file in [tools/songs/](tools/songs/), such as `2_ode.txt`.
2. Change it. Each note looks like `Mi/4`: the name, then the length. [The song guide](tools/songs/README.md) has examples.
3. Listen with `./maestro listen ode`.
4. Upload with `./maestro upload`.

### Change a rule or timing

Open [code/src/config.h](code/src/config.h), change the number, and run `./maestro upload`.

| To change | Setting |
| --- | --- |
| Knob runs backwards | `KNOB_REVERSED` |
| Number of lives | `START_LIVES` |
| Wait before a replay | `REPLAY_AFTER_MS` |
| Idle replays before giving up | `MAX_IDLE_REPLAYS` |
| Points | `POINTS_PER_NOTE`, `POINTS_PER_GOOD_GAP`, `POINTS_PER_LIFE_LEFT`, `POINTS_PER_EAR_ANSWER` |
| Ear mode difficulty | `EAR_START_NOTES`, `EAR_CORRECT_TO_LEVEL` |
| Idle screen delay | `IDLE_AFTER_MS` |

The sounds and LED signals are the `S_...` tables at the top of [code/src/output.cpp](code/src/output.cpp). Each step is `{frequency in Hz, milliseconds, LEDs}`.

### Change the build guide

Edit [tools/guide/build_guide.py](tools/guide/build_guide.py) for the text, or [tools/guide/wiring.py](tools/guide/wiring.py) for the wiring, then run `python3 tools/guide/build_guide.py`. It won't build if the wiring fails its electrical check.

### If something goes wrong

Run `./maestro check` first. Then see [the troubleshooting table](code/README.md#troubleshooting).

## Using the device

Turn the knob to choose and press any key to confirm. Turning the knob one tick during a game opens "Quit?". On Yes/No screens, each tick switches between No (red keys) and Yes (green keys).

| Tick | Item | What it does |
| --- | --- | --- |
| 1 | Light only | Melody on the keys' lights, in silence |
| 2 | Sound only | Melody on the speaker, with the key lights off |
| 3 | Light + sound | Both |
| 4 | Ear | A low До, then a mystery note: find its key |
| 5 | Free play | Plays like a small piano |
| 6 | Records | Best scores, per mode and piece |
| 7 | Reset records | Clears all records |

You have 3 lives, and Easy mode has no limit. If you stop playing for 8 s, the melody replays with no life lost.

## What's where

| Path | What it is |
| --- | --- |
| [NEXT_STEPS.md](NEXT_STEPS.md) | The list of steps to finish the project |
| [DECISIONS.md](DECISIONS.md) | Every design decision and why |
| [HANDOFF_FOR_SOFTWARE_AGENT.md](HANDOFF_FOR_SOFTWARE_AGENT.md) | Hardware, pins and the original proposal |
| [maestro](maestro), [tools/maestro_cli.py](tools/maestro_cli.py) | The `./maestro` command |
| [.vscode/tasks.json](.vscode/tasks.json) | The VS Code tasks |
| [tools/songs/](tools/songs/) | The songs: **edit these** |
| [tools/make_songs.py](tools/make_songs.py) | Turns song files into firmware data and WAV previews |
| [code/src/config.h](code/src/config.h) | Pins, rules and timings |
| [code/src/](code/src/) | The firmware |
| [code/hwtest/](code/hwtest/) | The hardware test |
| [tools/sim/](tools/sim/) | The simulated Uno and its tests |
| [docs/index.html](docs/index.html) | The step-by-step build guide, ready to publish |
| [tools/guide/](tools/guide/) | Generates the guide. `wiring.py` is the wiring as data, and it's checked electrically on every build |
| [print/maestro_case/](print/maestro_case/) | The 3D-printed case: [assembly and wiring](print/maestro_case/README.md), [print plates](print/maestro_case/plates/HOW_TO_PRINT.md) |
