# Virtual device tests

These tests run the real compiled firmware (`firmware.elf`) on a simulated ATmega328P, using [simavr](https://github.com/buserror/simavr). `harness.c` emulates the LCD, 8 LEDs, piezo and EEPROM, and every part is connected by following the build guide's wiring list (`tools/guide/wiring.py`), so a mistake in the guide makes the tests fail. They need no Arduino.

```
./maestro test            # several minutes on 14 cores
./maestro test --all      # adds whole-piece games: about 15 minutes
./maestro test Rhythm     # tests whose name contains "Rhythm"
```

The first run calls `setup.sh`, which downloads simavr into `tools/sim/.deps` without needing root. It works on Ubuntu or Debian only, and uploading to the Uno does not need any of this.

| File | Covers |
| --- | --- |
| `test_guide.py` | The build guide against the firmware's real pins, deliberately wrong wiring, and the on-chip self-test in the simulator |
| `test_menus.py` | Menus, Yes/No, knob, key reading, resistor tolerance, idle screen, Free play, Records |
| `test_game.py` | Channels per mode, lives, Easy, rhythm, replay, pause, scoring, records |
| `test_ear.py` | Ear mode |
| `test_full_games.py` | Whole pieces from level 1 to the win |

**After changing songs or rules:** some tests expect the current songs, rules and 3-song list, so they can fail even when the change is fine. Update those tests, or check that the failures are expected.

**What this cannot check:** how it sounds and looks, real wiring, real switch and knob behaviour, and power-bank behaviour.
