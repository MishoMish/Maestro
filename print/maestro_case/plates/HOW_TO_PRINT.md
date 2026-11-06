# Ready-made build plates

Each `.3mf` file is one full print job. The parts are already turned the right way up, spaced out and centred on a 220 × 220 mm bed.
Open it in your slicer (Creality Print: *File → Open*, OrcaSlicer: drag it in). You don't need to move or rotate anything.

| # | File | Contents | Profile (Creality Print) |
|---|---|---|---|
| 0 | `0_TESTS_black.3mf` | test key plate, test key, LCD test frame. **Print this first.** | `Maestro_2_Plates_FaceDown_PETG` |
| 1 | `1_ARDUINO_CASE_black.3mf` | ♻ **Arduino case**: Uno tray + snap-on lid | `Maestro_3_Trays_PETG` |
| 2 | `2_BREADBOARD_CASES_black.3mf` | **Breadboard cases**: ♻ half-breadboard tray (clips onto the Uno tray) + full-breadboard key-bed tray (sets the key height for Маестро) | `Maestro_3_Trays_PETG` |
| 3 | `3_MAESTRO_BOX_black.3mf` | box (longest print) | `Maestro_1_Box_PETG` |
| 4 | `4_MAESTRO_PLATES_black.3mf` | deck plate + control panel (face down), knob, pot holder | `Maestro_2_Plates_FaceDown_PETG` |
| 5 | `5_MAESTRO_KEYS_white.3mf` | key comb, **white** filament | `Maestro_5_Keys_White_PLA` or `_PETG` |

♻ = reusable in later projects. The same split is in `stl/`: `1_arduino_case/`, `2_breadboard_case/`, `3_maestro/`.

Order: **0 → check the fit → 1 → 2 → 4 → 3 → 5**. The cases are quick, so you can put the electronics in while the box prints.
If the test print shows the button height needs changing, edit `btn_h` and re-export only `maestro_keybed_tray`.

## In OrcaSlicer
**Ready-made presets:** `print_profiles/orcaslicer/Maestro_Orca_Process_presets.zip`. Import it with **File → Import → Import Configs…**.
It adds 4 process presets built on the stock *0.20mm Standard @Creality Ender3V3SE 0.4*:

| Preset | Plates |
|---|---|
| Maestro 0+4 Tests & Plates face-down | 0, 4 |
| Maestro 1+2 Arduino & breadboard cases | 1, 2 |
| Maestro 3 Box | 3 |
| Maestro 5 Keys white | 5 |

Filament presets: `print_profiles/orcaslicer/Maestro_Orca_Filament_presets.zip`, imported the same way:
**Maestro PETG Black** (235/240 °C, bed 75 °C, fan 40–60 %, 1.2 mm retraction + 0.2 mm Z-hop), **Maestro PLA White keys** (210 °C, bed 60 °C, fan 100 %) and **Maestro PETG White keys** (black settings, more fan for the key tops).
They are built on Orca's own *Creality Generic PETG / PLA @Ender-3V3-all*, so anything not listed stays as Creality set it.
If you'd rather set it by hand, these are the values:

Pick the built-in printer **Creality Ender-3 V3 SE 0.4 nozzle** and the **Generic PETG** or **Generic PLA** filament. Then set these in the process tab:

| Plate | Layer | Walls | Top / bottom | Infill | Adhesion | Extra |
|---|---|---|---|---|---|---|
| 0, 4 | 0.20 | 3 | 4 / 3 | 25 % | skirt | first layer 20 mm/s, elephant foot 0.15 |
| 1, 2 | 0.20 | 3 | 4 / 3 | 20 % | skirt | elephant foot 0.15 |
| 3 | 0.20 | 3 | 4 / 3 | 15 % | skirt | outer wall 50 mm/s |
| 5 | 0.20 | **2** | **5** / 3 | 15 % | **brim 3 mm** | outer wall 40 mm/s |

PETG: 235 °C nozzle, 75 °C bed. PLA: 210 °C / 60 °C. Supports off for everything.

### Exporting your Orca settings (so they can be turned into importable presets)
1. Pick printer **Creality Ender-3 V3 SE 0.4 nozzle**, process **0.20mm Standard**, filament **Generic PETG**.
2. **Make them your own presets.** Export only lists presets you've saved yourself, so change any one value (e.g. infill 15 → 16 %) and click the save icon next to the process name. Save it as `test`. Do the same for the filament.
3. **File → Export → Export Preset Bundle…**, choose **Process presets (.zip)**, tick `test`, OK, save.
4. Repeat for **Filament presets (.zip)**.
5. Send both `.zip` files.

To import presets later: **File → Import → Import Configs…** and pick the `.zip`.
