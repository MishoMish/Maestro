# Маестро – project context for the software / logic agent

> **Your job:** grill me (the student) relentlessly, one round at a time, until we agree on how the software and game logic will work. For every question, give your recommended answer. Ask only the questions whose prerequisites are already settled, then wait for my answers before the next round. **Do not write the final firmware until I confirm we have a shared understanding.**
> Everything below is **already decided** (hardware, physical design, pins, wiring). Treat it as fixed unless a software reason forces a change. If it does, flag it explicitly, because the printed case depends on it.

---

## 1. The project in one paragraph
A university course project by **Богомил Стоянов (ФН 7MI3400949)** and **Михаил Доброславски (ФН 4MI3401007)**, for **проф. Патиас**. An earlier "Simon Says" proposal was asked to be reworked so it is **simple to build but has clear practical value**.
The result is **"Маестро"**: a standalone device that trains **musical hearing and musical memory**. The device plays a melody and the user repeats it on 8 piano-style keys.
Famous pieces are simplified and revealed **progressively**: each level adds a longer fragment, until the user plays the whole piece. The pieces are Beethoven's *Für Elise* and *Ode to Joy* (*Ода на радостта*), and Mozart's *Turkish March* (*Турски марш*).
It's built for children and beginner musicians, at home, in music class, and in centres for children with sensory difficulties. **No computer, no internet.**

## 2. Features promised in the proposal (must exist)
| Feature | Description |
|---|---|
| **Mode: Light only** (само светлина) | Melody shown only by lighting the keys. Trains visual memory, accessible to users with hearing difficulties. |
| **Mode: Sound only** (само звук) | Melody played only by the piezo. Trains hearing, accessible to users with visual difficulties. |
| **Mode: Light + sound** | For beginners. |
| **Mode: "Слух" (Ear)** | Plays a **single tone**; the user identifies which note it is by pressing the key. |
| Progressive melody reveal | Each level = a longer fragment of the piece, until the whole piece is played. |
| LCD shows **level and points** | |
| **High scores per mode** saved in device memory (EEPROM) | So the user sees progress, and whether they remember visual or audio information better. |
| Standalone | Runs from a USB power bank. |

Development must be **staged**, so there is always a working version:
1. Core: play a sequence → read the keys → compare.
2. Then add the modes, melodies and records one at a time.

The modes are meant to be **settings of one shared engine** (light on/off, sound on/off), not separate programs. Melodies are **just note tables**.

## 3. Hardware (fixed)
### From the official Arduino Starter Kit (borrowed, so nothing may be soldered, glued or modified)
- **Arduino Uno R3**: ATmega328P, 32 KB flash, **2 KB SRAM**, **1 KB EEPROM**.
- **16×2 character LCD** (HD44780-compatible, parallel 4-bit). **The character ROM has no Cyrillic**, so text is Latin, or uses up to 8 custom characters.
- **Piezo capsule** (Murata PKM17EPP, 17 mm, passive). It is driven with `tone()`: **one tone at a time, no volume control**.
- **3 × 10 kΩ potentiometers**: one is the menu knob, one is the LCD contrast (set once, inside the box).
- Resistors used: 17 × 220 Ω (the kit has 22), 1 × 10 kΩ.
- The kit's own small breadboard stays stuck to its base plate and is **not used**.

### The student's own parts
- **Full-size breadboard** (key bed under the keys) and **half-size breadboard** (next to the Uno).
- 8+ tactile buttons (assumed 6×6 mm), LEDs in **R, G, B, W, Y**, jumpers including ~17 female–male.

### Power
**USB power bank** into the Uno's USB-B jack.
Known risk: some power banks switch off when less than ~100 mA is drawn. We decided to test first. Fallback: the kit's 9 V snap into VIN, but there is no battery bay in the case.
**Software question:** do we need a "keep-alive" load or blink pattern?

## 4. Inputs and outputs (exact counts)
| Element | Count | Details |
|---|---|---|
| **Piano keys** | **8** | White keys only: **До Ре Ми Фа Сол Ла Си До** (C4 → C5, one octave). **No black keys.** |
| **Key LEDs** | **8** | One LED under each translucent white key; the whole key glows. |
| **Knob** | **1** | 10 kΩ pot under the panel. The panel has **7 tick marks** (−120° … +120°, every 40°) around it. |
| **Display** | **1** | 16×2 LCD in the centre of the sloped panel. |
| **Speaker** | **1** | Piezo behind a grille, left of the LCD. |
| Other buttons | **0** | There is **no** separate Start / OK / Back / Reset button (except the Uno's own reset, which is inside the box). |

**Consequence for the logic:** all navigation must be done with **the knob + the 8 keys**.
My current suggestion: turn the knob to choose, press any key to confirm. **How to go "back"/exit a game is still open; grill me on it.**

### Key LED colours (fixed, one colour per note)
До **red** · Ре **yellow** · Ми **green** · Фа **blue** · Сол **white** · Ла **yellow** · Си **green** · До (high) **red**

### Melody constraint
Only the 8 white notes C4–C5 exist.
- *Ode to Joy* fits as written.
- *Für Elise* (D♯) and *Turkish March* (G♯) **must be adapted/transposed** to white keys only.
- Range is one octave, so melodies that go beyond it must be folded.

## 5. Pin map (fixed, matches the wiring in the case)
| Uno pin | Function |
|---|---|
| **A0** | All 8 keys through a **resistor ladder** (see §6) |
| **A1** | Knob (pot wiper; ends to 5 V / GND) |
| D12, D11, D5, D4, D3, D2 | LCD RS, E, D4, D5, D6, D7: `LiquidCrystal lcd(12, 11, 5, 4, 3, 2);` |
| **D8** | Piezo (+). `tone()` uses Timer2, so PWM on D3/D11 is lost, which doesn't matter here. |
| D6, D7, D9, D10, D13, A2, A3, A4 | LEDs До, Ре, Ми, Фа, Сол, Ла, Си, До (in key order). D13 also lights the Uno's on-board LED. |
| A5, D0, D1 | Free (D0/D1 = Serial, keep for debugging) |

## 6. Key reading: resistor ladder on A0 (fixed)
- **Chain:** 8 × 220 Ω from 5 V to GND. Each key connects one tap of the chain to A0. A 10 kΩ pull-down holds A0 at 0 when nothing is pressed.
- **Expected `analogRead(A0)`:** key 1 (До) ≈ **1023**, key 2 ≈ 895, key 3 ≈ 767, key 4 ≈ 639, key 5 ≈ 512, key 6 ≈ 384, key 7 ≈ 256, key 8 (high До) ≈ **128**, none ≈ 0. The pull-down shifts these by up to ~4 %.
- **Decode:** `level = (v + 64) / 128; key = 8 − level` (0-based), `level 0` = no key.
- **Limitation:** only **one key at a time** can be read reliably. Two keys pressed together give an undefined in-between value. The software must handle that (debounce / ignore / take the first stable value).
- Mechanical: the printed key comb moves about 1 mm; a tactile switch clicks under each key.

## 7. Existing code
`maestro_hw_test/maestro_hw_test.ino` is a hardware test, **not the game**. It does:
- light every LED in turn at start-up;
- while a key is held, light its LED and play its note with `tone()`. Frequencies: 262, 294, 330, 349, 392, 440, 494, 523 Hz;
- show the note name (`Do Re Mi Fa Sol La Si Do'`), the raw A0 value and the A1 knob value on the LCD.

It contains the `readKey()` decode above. It uses `delay(30)` polling; the game should probably be non-blocking (grill me).

## 8. Physical design (fixed, already modelled and exported for printing)
- **Console shape:** sloped "mini synth" box, ~**177 × 133 mm**, **30 mm** tall at the front and **64 mm** at the back. Black PETG, printed on an Ender-3 V3 SE.
- **Front: key deck.** The 8 keys are one white printed "comb" with flexible hinges at the back. Each key is **18.3 mm wide at 20.32 mm spacing**, stands 1 mm above the deck, and has its note name in Bulgarian engraved over its LED. Black walls between the keys stop light from one key spilling into the next.
- **Back: sloped control panel**, about 26°.
  - **"МАЕСТРО"** engraved at the bottom.
  - **LCD** in the centre.
  - **Speaker grille** (piezo) on the left.
  - **Knob** with 7 ticks on the right.
- **Inside:**
  - Full breadboard (key bed) under the keys on a printed riser.
  - A **reusable Uno tray** (board on printed pegs, snap-on lid for when it's carried) with a **reusable half-breadboard tray** dovetailed to it. They sit in ribs on the box floor. The half breadboard holds the LCD contrast pot, the backlight resistor and the 5 V/GND distribution.
- **USB cable** exits through the **left side wall**.
- Panels snap in with clips (no screws), so the box can be opened for wiring.

## 9. Constraints the software must respect
- **SRAM 2 KB:** melodies and strings should live in **PROGMEM / flash** (`F()` for LCD strings).
- **EEPROM 1 KB, ~100 000 write cycles per cell:** write high scores only when they change.
- **The LCD can't show Cyrillic.** Note names on screen are Latin (`Do Re Mi…`) or custom glyphs. The keys themselves carry the Bulgarian names.
- In **Sound only** mode the user may not see the LCD. In **Light only** mode the user may not hear the piezo. Menus and feedback (correct/wrong, level up, game over) need to make sense **in the mode being played**. *Grill me on this*: it's the accessibility core of the project.
- Must stay **simple to implement** (course project), with a **working version at every stage**.

## 10. Open decisions – grill me on these (non-exhaustive)
1. **Overall architecture:** state machine (menu → mode select → melody select → play → input → result → …), non-blocking `millis()` timing vs `delay()`, file/module layout. Arduino IDE vs **PlatformIO in VS Code**.
2. **Menu / navigation with only knob + keys:** how to confirm, how to go back or quit a game, what the 7 knob ticks map to, idle/attract screen.
3. **Game rules:**
   - how a level grows (+1 note? +1 phrase?);
   - lives or mistakes allowed;
   - what happens on a wrong note;
   - time limits per note;
   - replay ("show again") option;
   - winning the whole piece.
4. **Scoring:** what earns points, and how level, points and records relate.
5. **Ear mode ("Слух"):** random note or pattern, reference tone first?, scoring, difficulty (e.g. fewer candidate notes at first).
6. **Melody data format:** note + duration (+ rests?) tables, tempo, how playback timing works.
7. **Adapting the melodies:** how *Für Elise* and *Turkish March* are transposed or adapted to 8 white keys C4–C5, and how long each one is.
8. **Feedback design per mode:** correct/wrong/level-up signals in light-only vs sound-only vs both. Use of the 8 coloured LEDs for animations.
9. **EEPROM layout:** records per mode (and per melody?), a "reset records" feature, first-boot initialisation, wear.
10. **Input handling:** ladder debounce, held keys, two keys at once, calibration of thresholds (stored in EEPROM?).
11. **Knob handling:** hysteresis between positions, mapping 0–1023 to menu items.
12. **Power-bank auto-off:** keep-alive needed? Sleep / idle behaviour.
13. **Staged plan and testing:** milestones that each give a demo-able version; a serial debug mode.
14. **What to show the professor:** demo script and which features are "must" vs "nice to have".

---

### Appendix – the original proposal text (Bulgarian, as sent to the professor)
Тема: „Маестро" – интерактивен тренажор за музикален слух и памет.
**Проблем:** Началното музикално обучение (разпознаване на тонове и запаметяване на мелодии) се строи на много повторения, които бързо стават скучни, особено за деца. Повечето обучителни игри разчитат едновременно на звук и картина и така изключват хората със слухови или зрителни затруднения.
**Идея:** Малко устройство изсвирва мелодия, а потребителят я повтаря с бутони. Известни произведения („За Елиза", „Ода на радостта", „Турски марш") се адаптират в опростен вариант. Мелодията се разкрива постепенно: с всяко ниво фрагментът става по-дълъг, докато потребителят изсвири цялото произведение. От меню на дисплея се избира как се подава мелодията: само със светлина / само със звук / светлина и звук. Режимът „Слух" свири единичен тон и потребителят познава коя нота е. Дисплеят показва ниво и точки, а рекордите за всеки режим се пазят в паметта.
**Реалистичност:** базов хардуер; една обща логика „изсвири последователност → прочети бутоните → сравни", режимите са настройки на тази логика, мелодиите са таблици с ноти; поетапно изпълнение с винаги работеща версия.
**Среда:** самостоятелно устройство без компютър/интернет – у дома, в часовете по музика, в центрове за деца със сензорни затруднения.
