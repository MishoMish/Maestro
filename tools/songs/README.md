# Song files

Each `.txt` file is one piece. Files are used in name order, which is the order on the device.

```
title=Ode to Joy     # name on the LCD, up to 16 Latin characters
short=ODE            # name on the Records page, up to 5 characters
tempo=100            # quarter notes per minute
max_notes=62         # the check fails above this

Mi/4 Mi/4 Fa/4 Sol/4 |
```

- **Notes:** `Do Re Mi Fa Sol La Si Do'`, the 8 keys.
- **Length:** the number after `/` is in sixteenths, so 4 = quarter note and 2 = eighth note. It runs until the next note, so add any rest to the previous note.
- **`|`:** ends a level. The next level adds everything up to the next `|`.
- **`#`:** starts a comment.

After a change, run `python3 tools/make_songs.py`, then listen to the WAV in `tools/preview/`.
