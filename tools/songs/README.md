# Song guide

Each `.txt` file here is one piece. After any change:

```
./maestro listen ode     # hear it; part of the name is enough
./maestro upload         # send it to the Uno
```

You don't need to rebuild anything by hand: both commands check the songs first and tell you the line of any mistake.

## A song file

```
# Ode to Joy, full theme in C.
title=Ode to Joy     # name on the LCD, up to 16 Latin characters
short=ODE            # name on the Records page, up to 5 characters
tempo=100            # quarter notes per minute
max_notes=62         # the check fails above this

Mi/4 Mi/4 Fa/4 Sol/4 |
Sol/4 Fa/4 Mi/4 Re/4 |
```

## Notes

A note is a key name, then `/`, then its length: `Mi/4`.

**Keys:** `Do Re Mi Fa Sol La Si Do'`. Capitals matter. There are no black keys, so `Do#` isn't possible.

| Number | Length |
| --- | --- |
| 1 | Sixteenth |
| 2 | Eighth |
| 3 | Dotted eighth |
| 4 | Quarter |
| 6 | Dotted quarter |
| 8 | Half |
| 12 | Dotted half |
| 16 | Whole |

**Rests:** a rest is added to the note before it, because nobody can press a rest. A quarter note followed by a quarter rest is `Do/8`.

## Recipes

| To | Do this |
| --- | --- |
| Fix a wrong note | Change its name: `Fa/4` to `Sol/4` |
| Fix its rhythm | Change its number: `Fa/4` to `Fa/2` |
| Make it slower or easier | Lower `tempo=` |
| Move where a level ends | Move the `\|`. Each level adds everything up to the next `\|` |
| Hear one level | `./maestro listen ode 3` |
| Add a song | Copy a file, give it a new number and name, and change its `title=` and `short=` |
| Remove a song | Delete its file |
| Change the order on the device | Rename the files: they're used in name order |

**Warning:** adding or removing a song **clears all records**, because the storage layout changes. Reordering songs moves each record to the wrong song. Changing notes keeps the records, but old scores may no longer be comparable. Clear them with tick 7 if so.

## The rules a song must follow

| Rule | Limit | If it fails |
| --- | --- | --- |
| Levels | 8 to 12 | Add or remove `\|` marks |
| Notes | Up to `max_notes`, and at most 255 | Raise `max_notes` or remove notes |
| Fastest gap between notes | At least 200 ms, so a beginner can press it | Lower `tempo=` |
| Note length | 1 to 31 | Use a smaller number |
| Songs in total | At most 7 | Remove one |

## Good to know

- **The previews** in `tools/preview/` use a square wave, close to the piezo's sound. The real piezo will still sound different.
- **Tests:** some tests in `./maestro test` expect the current songs, so they may fail after you edit a song even though the song is fine. The upload doesn't depend on them.
- **`code/src/melodies_data.h`** is generated. Never edit it, because your changes would be overwritten.
