# Маестро – printed case

Two OpenSCAD files:

| File | What it is |
|---|---|
| `uno_kit.scad` | **Reusable** for any project: Uno tray, snap-on lid, half-breadboard tray. |
| `maestro.scad` | **This project**: sloped box, key deck, white key comb, control panel, knob, key-bed tray, test pieces. It needs `uno_kit.scad` in the same folder. |

Open a file, choose `part` in the Customizer (Window → Customizer), press **F6**, then **F7** to export.
Ready-made STLs (default sizes) are in `stl/`, split into `1_arduino_case/` (♻), `2_breadboard_case/` (♻ half-breadboard tray + Маестро key-bed tray) and `3_maestro/`. The models were checked for collisions in their assembled positions.

Nothing gets glued, screwed or soldered to the kit. The Uno sits on printed pegs and everything is wired with jumpers.

---

## 1. Measure first (2 minutes)

These are the settings at the top of `maestro.scad`. The defaults are standard sizes.

| Setting | Default | Why it matters |
|---|---|---|
| `btn_h` | 5.0 mm | **Most important.** Button height on the breadboard, including the stem. It sets the height of the key-bed tray, so a wrong value only means reprinting that tray. |
| `fbb_l / fbb_w / fbb_h` | 165 / 55 / 8.5 | Full breadboard (sits under the keys). |
| `hbb_*` in `uno_kit.scad` | 82.5 / 55 / 8.5 | Half breadboard (next to the Uno). |
| `lcd_bezel`, `lcd_bezel_h` | 71.2 × 24.2, 7.0 | The black metal frame of the LCD and its height above the green PCB. |
| `pot_body`, `knob_mode` | 10×10×5, blade | Kit trimmer pot. If yours already has a round shaft, use `socket` and set `socket_d`. |

## 2. Test prints before using the white filament (black PETG, about 1 h total)

1. **`test_key_plate` + `test_key`**: push the test key's peg into the plate. Put one button and one LED on the real full breadboard (button across the middle channel, LED 3 rows behind it). Stand the test plate's legs on the breadboard over them.
   - The key should **click** after about 1 mm of travel. No click: lower `btn_h` by 0.3. Clicks by itself: raise it.
   - The key must not touch the LED.
2. **`test_lcd`**: the LCD should press in from below and the two side clips should snap over the PCB. If it's tight, change `lcd_bezel` and `lcd_holes`.

## 3. Print list

| Part | File | Filament | On the bed | Supports | Rough time |
|---|---|---|---|---|---|
| Uno tray ♻ | `reusable_uno_tray` | black | as exported | none | 1.5 h |
| Uno lid ♻ | `reusable_uno_lid` | black | top face down | none | 1 h |
| Breadboard tray ♻ | `reusable_bb_tray` | black | as exported | none | 1 h |
| Box | `maestro_box` | black | upright | none | 7–9 h |
| Key-bed tray | `maestro_keybed_tray` | black | as exported | none | 1.5 h |
| Deck plate | `maestro_deck_plate` | black | face down | none | 1.5 h |
| Control panel | `maestro_panel` | black | face down | none | 2.5 h |
| Pot holder | `maestro_pot_holder` | black | as exported | none | 10 min |
| Knob | `maestro_knob` | black | top face down | none | 30 min |
| **Key comb** | `maestro_key_comb` | **white** | flat side down | none | 2 h |

**Easiest way: open the ready-made build plates in `plates/`** (one `.3mf` per print job, with the Arduino case and the breadboard cases on their own plates; see `plates/HOW_TO_PRINT.md`). **Importable filament profiles and per-part slicer settings are in `print_profiles/`** (see `PROCESS_SETTINGS.md` there).

- **Black PETG**, about 230 g in total (spool label says PETG?): 235–240 °C nozzle, 75–80 °C bed, fan 30–50 %, 0.2 mm layers, 3 walls, 20 % infill. Rub glue stick on the build plate as a release layer, because PETG can stick to it too hard and pull pieces off the surface.
- **White key comb**: 16.3 cm³, so at most about 20 g. That leaves about 10 g spare, so don't print it twice. Use **2 walls** (the key sides are 0.8 mm = exactly 2 lines), 5 top layers, 15 % infill. Settings: PLA 205 °C / 60 °C, PETG same as above. A 3 mm brim helps the thin hinges stay down.
- The ♻ parts are the reusable ones.

## 4. Assembly

1. Put the **Uno** on the pegs of the Uno tray. Slide the **breadboard tray** down onto the tray's end (two dovetails), then put the half breadboard in it.
2. Drop both trays into the back of the box. The ribs on the floor lock into the grooves on the trays, and the USB jack lines up with the hole in the left wall.
3. Put the **full breadboard** into the key-bed tray and wire the key bed (section 5). Drop the tray into the front of the box, pushed against the front wall.
4. **Key comb → deck plate**: press the 3 pegs into the blind holes under the plate. Each key now sits in its window, with the black walls between keys stopping light from spilling over.
5. Snap the **deck plate** in: 4 hooks click into the slots in the side walls. To open it, push the hooks in through the slots with a small screwdriver.
6. **Panel**: press the LCD in from below (the clips snap over the PCB) and the piezo into its cup. Slide the pot into the pot holder (legs down, rotor up), push the holder into the square socket, and put the knob on from the top. Connect the female–male jumpers, then snap the panel in.

## 5. Wiring

### Uno pins

| Uno | Goes to |
|---|---|
| 5V / GND | power rails of the half breadboard, then on to the key bed |
| A0 | key ladder (all 8 keys) |
| A1 | knob wiper (pot ends to 5V / GND) |
| D12, D11, D5, D4, D3, D2 | LCD RS, E, D4, D5, D6, D7 (same as kit project 11) |
| D8 | piezo + (piezo − to GND) |
| D6, D7, D9, D10, D13, A2, A3, A4 | LEDs До, Ре, Ми, Фа, Сол, Ла, Си, До |

LCD (12 female–male jumpers): VSS→GND, VDD→5V, V0→contrast pot wiper (on the half breadboard), RS, RW→GND, E, D4–D7, A→220 Ω→5V, K→GND.
In total you need about **17 female–male jumpers** (LCD 12, piezo 2, knob 3).

### Key bed (full breadboard under the keys)

Put the breadboard in with **rows a–e toward the back** (Uno side) and **column 1 on the left**.
Rails: back outer = **5V**, back inner = **GND**, front inner = **A0 bus**, front outer = **GND**.

For key *k* = 1…8, let **n = 8k − 4** (columns 4, 12, 20, 28, 36, 44, 52, 60):

| What | Where |
|---|---|
| Button | across the channel, legs in columns **n−1** and **n+1** |
| LED | row c: long leg (+) in column **n**, short leg (−) in column **n+2** (bend the legs to 5 mm apart) |
| LED resistor 220 Ω | column n+2 row b → back GND rail |
| LED wire | column n row a → its Uno pin (table above) |
| A0 wire | column n+1 row g → front A0 rail |
| Ladder 220 Ω | column n−1 row i → column n+7 row i (to the next key), for keys 1–7 |
| Key 1 top | column 3 row a → back 5V rail |
| Key 8 bottom | column 59 row j → 220 Ω → front GND rail |
| Pull-down 10 kΩ | front A0 rail → front GND rail (left end) |
| GND link | front GND rail ↔ back GND rail at column 1 |

Expected A0 readings: key 1 ≈ 1023, key 2 ≈ 895, … key 8 ≈ 128, nothing pressed ≈ 0.
Kit parts used: 17 × 220 Ω and 1 × 10 kΩ (the kit has 22 and 22).

**Everything under the keys must lie flat (under 3 mm).** Bend the kit's solid-core wires flat, and don't use tall Dupont plugs on the key bed. The keys sit 5 mm above the board.

LED colours (one per note): До red, Ре yellow, Ми green, Фа blue, Сол white, Ла yellow, Си green, До red.

### Test sketch
`maestro_hw_test/maestro_hw_test.ino`: lights every LED, then each key lights its own LED and plays its note. The LCD shows the A0 reading and the knob value, so you can check all the wiring before writing the real game.

## 6. Reusing the Uno tray in the next project

In a new box: `use <uno_kit.scad>`, then call `kit_posts(x, y, uno_tray_size()[0], uno_tray_size()[1])` on the box floor. The tray then drops in and locks the same way as in this box. The lid is for when the board is stored or carried on its own.
