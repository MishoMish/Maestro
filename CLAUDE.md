# Маестро

Standalone Arduino Uno device that trains musical hearing and memory. University course project.

- **[DECISIONS.md](DECISIONS.md):** the decision log. Read it before designing or writing firmware. Update it in the same turn any decision is made, following the rules at the top of that file.
- **[HANDOFF_FOR_SOFTWARE_AGENT.md](HANDOFF_FOR_SOFTWARE_AGENT.md):** the hardware, pin map, wiring, case and promised features. Treat the hardware as fixed.
- **`code/`:** the firmware (PlatformIO). Do not write the final firmware until the students confirm that the design is settled.
- **`tools/make_songs.py`:** turns `tools/songs/*.txt` into `code/src/melodies_data.h` and WAV previews. Edit the song files, never the generated header.
