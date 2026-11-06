# Virtual device tests

These tests run the real compiled firmware (`firmware.elf`) on a simulated ATmega328P, using [simavr](https://github.com/buserror/simavr). `harness.c` emulates the case's wiring: the LCD, 8 LEDs, piezo, resistor ladder, knob and EEPROM. They need no Arduino.

```
python3 tools/sim/run_tests.py            # several minutes on 14 cores
python3 tools/sim/run_tests.py --all      # adds whole-piece games: about 15 minutes
python3 tools/sim/run_tests.py Rhythm     # tests whose name contains "Rhythm"
```

The first run calls `setup.sh`, which downloads simavr into `tools/sim/.deps` without needing root. It works on Ubuntu or Debian only, and uploading to the Uno does not need any of this.

| File | Covers |
| --- | --- |
| `test_menus.py` | Menus, Yes/No, knob, key reading, resistor tolerance, idle screen, Free play, Records |
| `test_game.py` | Channels per mode, lives, Easy, rhythm, replay, pause, scoring, records |
| `test_ear.py` | Ear mode |
| `test_full_games.py` | Whole pieces from level 1 to the win |

**What this cannot check:** how it sounds and looks, real wiring, real switch and knob behaviour, and power-bank behaviour.
