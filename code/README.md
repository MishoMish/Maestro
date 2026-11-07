# Маестро firmware

All the usual commands are in the [main README](../README.md). This page covers first-time setup and troubleshooting.

## First time on the real device

1. **Wire it** as in `print/maestro_case/README.md`, section 5.
2. **Prepare this computer:**
   ```
   ./maestro check
   ./maestro fix-permissions    # only if check asks for it
   ```
3. **Connect the Uno by USB and run the hardware test:**
   ```
   ./maestro hwtest
   ```
4. **Check the hardware.** Every LED lights once in key order. Then, with the LCD contrast pot adjusted until text is visible:

   | Check | Expected | If not |
   | --- | --- | --- |
   | Press each key | Its own LED, note and name | Note the `A0=` value, then see "Troubleshooting" |
   | Nothing pressed | `-` and `A0` near 0 | A0 wire or the 10 kΩ pull-down is loose |
   | Turn the knob to each of the 7 ticks | `tick=` shows 1 to 7, in order | See "Troubleshooting" |

5. **Upload the game:**
   ```
   ./maestro upload
   ```
6. **Test the power bank:** run it from the bank, untouched, for 10 minutes. If it switches off, try another bank; the firmware has no keep-alive (DECISIONS.md, Q26).

Records survive uploads, so use tick 7 (Reset records) to clear any from testing.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Menu moves the wrong way | Set `KNOB_REVERSED = true` in `src/config.h` |
| A tick shows the wrong item | Note the `knob=` value at each tick. Zones are 146 counts wide; the knob may need re-seating on the pot |
| A key reads as its neighbour | Note `A0=` for all 8 keys (expected: 1023, 878, 743, 614, 490, 368, 248, 125, within about 30) and check the ladder |
| Keys trigger by themselves | A0 wire or pull-down is loose |
| LCD shows blocks or nothing | Adjust the contrast pot, then check the RS, E and D4–D7 wires |
| A note or LED is on the wrong key | Check the LED pin order in `src/config.h` against the wiring |
| Upload fails with a port error | Run `./maestro check`, try another USB cable, and close any open serial monitor |
| Upload fails with a sync error | Nothing may be connected to D0 and D1 |

For a log of game state changes over USB, run `./maestro monitor`.

## How the code is laid out

- `src/main.cpp`: the state machine, with all the game rules
- `src/input.cpp`: reads the keys and knob
- `src/output.cpp`: drives the LEDs, piezo and LCD, and holds the sound and light signals
- `src/records.cpp`: stores high scores in EEPROM
- `src/config.h`: pins and every tunable number
- `src/melodies_data.h`: generated from `tools/songs/`, so never edit it
- `hwtest/main.cpp`: the hardware test
