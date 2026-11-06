# Маестро firmware

## First time on the real device

1. **Wire it** as in `print/maestro_case/README.md`, section 5.
2. **Install PlatformIO** if needed. On Linux, also add yourself to the serial port group once, then log out and back in:
   ```
   sudo usermod -aG dialout $USER
   ```
3. **Connect the Uno by USB and upload the hardware test:**
   ```
   pio run -d code -e hwtest -t upload
   ```
4. **Check the hardware.** Every LED lights once in key order. Then, with the LCD contrast pot adjusted until text is visible:

   | Check | Expected | If not |
   | --- | --- | --- |
   | Press each key | Its own LED, note and name | Note the `A0=` value, then see "Troubleshooting" |
   | Nothing pressed | `-` and `A0` near 0 | A0 wire or the 10 kΩ pull-down is loose |
   | Turn the knob to each of the 7 ticks | `tick=` shows 1 to 7, in order | See "Troubleshooting" |

5. **Upload the game:**
   ```
   pio run -d code -t upload
   ```
6. **Test the power bank:** run it from the bank, untouched, for 10 minutes. If it switches off, try another bank; the firmware has no keep-alive (DECISIONS.md, Q26).

Records survive uploads, so use tick 7 (Reset records) to clear any from testing.

## Using it

Turn the knob to choose and press any key to confirm. Turning the knob one tick during a game opens "Quit?".

| Tick | Item |
| --- | --- |
| 1 | Light only |
| 2 | Sound only |
| 3 | Light + sound |
| 4 | Ear |
| 5 | Free play |
| 6 | Records |
| 7 | Reset records |

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Menu moves the wrong way | Set `KNOB_REVERSED = true` in `src/config.h` |
| A tick shows the wrong item | Note the `knob=` value at each tick. Zones are 146 counts wide; the knob may need re-seating on the pot |
| A key reads as its neighbour | Note `A0=` for all 8 keys (expected: 1023, 878, 743, 614, 490, 368, 248, 125, within about 30) and check the ladder |
| Keys trigger by themselves | A0 wire or pull-down is loose |
| LCD shows blocks or nothing | Adjust the contrast pot, then check the RS, E and D4–D7 wires |
| A note or LED is on the wrong key | Check the LED pin order in `src/config.h` against the wiring |
| Upload fails with a port error | Check the USB cable and the `dialout` group; close any open serial monitor |
| Upload fails with a sync error | Nothing may be connected to D0 and D1 |

For a log of game state changes over USB:
```
pio run -d code -e debug -t upload
pio device monitor -d code -e debug
```

## Changing things

- **Songs:** edit `tools/songs/*.txt`, then run `python3 tools/make_songs.py --upload`. Never edit `src/melodies_data.h`, which is generated.
- **Rules and timings:** the constants are in `src/config.h`.
- **Code layout:** `main.cpp` is the state machine, `input` reads the keys and knob, `output` drives the LEDs, piezo and LCD, and `records` stores high scores in EEPROM.
- **Tests:** `python3 tools/sim/run_tests.py`; see `tools/sim/README.md`.
