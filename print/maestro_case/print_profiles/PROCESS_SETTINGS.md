# Print settings per part (Ender 3 V3 SE, 0.4 mm nozzle)

## Filament profiles (import these)
In Creality Print, open the filament settings, then **Import** and pick the file:

| File | Use for |
|---|---|
| `Maestro_PETG_Black.cxfilament` | every black part |
| `Maestro_PLA_White_keys.cxfilament` | the key comb, if the white filament is PLA |
| `Maestro_PETG_White_keys.cxfilament` | the key comb, if the white filament is PETG |

These were built from your own CR-PETG export (same keys, same order). Only the values below were changed:
- **Black PETG:** 235 °C (240 °C first layer), bed 75 °C, fan 40–60 %, 80 % fan on bridges, 1.2 mm retraction plus a 0.2 mm Z-hop against stringing, max 12 mm³/s.
- **White PLA:** 210 °C, bed 60 °C, fan 100 %, 0.8 mm retraction.
- **White PETG:** same as black PETG, but 100 % fan on bridges for the key tops.

## Process profiles (import these too)
Built from your `testexport-params.cxprofile`: same sections, keys, order and Windows line endings. Only the values below were changed.
Import them the same way you exported. Each profile also carries its own material and retraction block, so the temperatures are right even if you forget to switch the filament.

| Profile | Print these parts with it | Main settings |
|---|---|---|
| `Maestro_1_Box_PETG` | box | 0.20 mm, 3 walls, 4 top / 3 bottom, 15 % infill, skirt, 120 mm/s (outer wall 50) |
| `Maestro_2_Plates_FaceDown_PETG` | deck plate, panel, Uno lid, test_lcd | as above + 25 % infill, **first layer 20 mm/s** (it's the visible face), elephant-foot compensation −0.15 mm |
| `Maestro_3_Trays_PETG` | Uno tray, bb tray, key-bed tray, test_key_plate | 20 % infill, elephant-foot compensation −0.15 mm (dovetails, snap groove) |
| `Maestro_4_SmallParts_PETG` | knob, pot holder, test_key | 0.16 mm layers, 40 % infill, 80 mm/s |
| `Maestro_5_Keys_White_PLA` / `_PETG` | **key comb** (pick the one matching the white filament) | **2 walls**, 5 top layers, 15 % infill, **3 mm brim**, 100 mm/s (outer wall 40) |

PETG profiles: 235 °C, bed 75 °C, fan 40–60 %, 80 % fan on bridges, 1.2 mm retraction plus a 0.2 mm Z-hop.
PLA keys: 210 °C, bed 60 °C, fan 100 %, 0.8 mm retraction.
Supports are **off** in every profile. No part needs them.

If a value looks wrong after importing, the table above is the reference.
