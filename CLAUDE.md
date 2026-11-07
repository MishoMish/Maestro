# Маестро

Standalone Arduino Uno device that trains musical hearing and memory. University course project.

- **[README.md](README.md):** how to use everything, starting with the `./maestro` command. Keep it true when commands or files change.
- **[NEXT_STEPS.md](NEXT_STEPS.md):** the steps to finish the project. Tick items off as they are done.
- **[DECISIONS.md](DECISIONS.md):** the decision log. Read it before designing or writing firmware. Update it in the same turn any decision is made, following the rules at the top of that file.
- **[HANDOFF_FOR_SOFTWARE_AGENT.md](HANDOFF_FOR_SOFTWARE_AGENT.md):** the hardware, pin map, wiring, case and promised features. Treat the hardware as fixed.
- **`code/`:** the firmware (PlatformIO).
- **`./maestro` (`tools/maestro_cli.py`):** the one command for uploading, songs and tests; `./maestro test` runs the simulated Uno.
- **`tools/guide/`:** generates the build guide in `docs/index.html`. If the wiring changes, change `wiring.py` and rebuild; it checks the wiring electrically.
- **`tools/make_songs.py`:** turns `tools/songs/*.txt` into `code/src/melodies_data.h` and WAV previews. Edit the song files, never the generated header.
- **Git:** agents may commit and push with clear commit messages. **Never add a `Co-Authored-By: Claude` line or any other Claude attribution**; commits are credited to the student alone.
