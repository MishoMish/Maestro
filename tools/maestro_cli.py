#!/usr/bin/env python3
"""Маестро helper: upload, check the hardware, work on songs, run the tests.

Linux/macOS:  ./maestro [command]
Windows:      python tools\\maestro_cli.py [command]
"""
import getpass
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import make_songs

ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / "code"
PREVIEW = ROOT / "tools" / "preview"
USB_IDS = ("2341", "2A03", "1A86", "10C4", "0403")  # Arduino and common USB-serial chips


def say(text=""):
    print(text, flush=True)


def fail(text):
    say(f"\nPROBLEM: {text}")
    return 1


# --- Finding things ---
def find_pio():
    candidates = [shutil.which("pio"), Path.home() / ".local/bin/pio",
                  Path.home() / ".platformio/penv/bin/pio",
                  Path.home() / ".platformio/penv/Scripts/pio.exe"]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def need_pio():
    pio = find_pio()
    if not pio:
        fail("PlatformIO is not installed.\n"
             "Fix: in VS Code, open Extensions, install \"PlatformIO IDE\", wait for it to finish, "
             "then restart VS Code.")
        return None
    os.environ["PATH"] = str(Path(pio).parent) + os.pathsep + os.environ.get("PATH", "")
    return pio


def find_uno(pio):
    """The Uno's port, or None."""
    try:
        output = subprocess.run([pio, "device", "list", "--serial", "--json-output"],
                                capture_output=True, text=True, check=True).stdout
        ports = json.loads(output)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None
    for port in ports:
        hwid = port.get("hwid", "").upper()
        if any(f"VID:PID={usb}" in hwid for usb in USB_IDS):
            return port["port"]
    return None


def user_in_dialout():
    """True, False, or None where the group does not exist (macOS, Windows)."""
    try:
        import grp
        import pwd
        user = getpass.getuser()
        group = grp.getgrnam("dialout")
        return user in group.gr_mem or pwd.getpwnam(user).pw_gid == group.gr_gid
    except (ImportError, KeyError):
        return None


def port_ready(port):
    """Returns (can use, needs the sg wrapper)."""
    if os.access(port, os.R_OK | os.W_OK):
        return True, False
    return (True, True) if user_in_dialout() and shutil.which("sg") else (False, False)


def run_on_port(command, port):
    """Runs a command that needs the port, even if a new group has not reached this login yet."""
    usable, wrap = port_ready(port)
    if not usable:
        return fail(f"No permission to use {port}.\nFix: run ./maestro fix-permissions")
    if wrap:
        return subprocess.call(["sg", "dialout", "-c", shlex.join(command)])
    return subprocess.call(command)


def need_uno(pio):
    port = find_uno(pio)
    if not port:
        fail("No Arduino found.\n"
             "Fix: plug the Uno into this computer with a USB cable that carries data, then try again.\n"
             "Close any open serial monitor too.")
    return port


# --- Commands ---
def cmd_check(_args):
    """Checks that this computer is ready, and says exactly what to fix."""
    problems = 0

    def report(good, text, fix=""):
        nonlocal problems
        say(f"  [{'ok' if good else '!!'}] {text}")
        if not good:
            problems += 1
            if fix:
                say(f"       Fix: {fix}")

    say("Checking this computer:")
    report(sys.version_info >= (3, 8), f"Python {sys.version.split()[0]}")
    pio = find_pio()
    report(bool(pio), "PlatformIO" + (f" ({pio})" if pio else ""),
           "in VS Code, install the \"PlatformIO IDE\" extension, then restart VS Code")
    in_group = user_in_dialout()
    if in_group is not None:
        report(in_group, "Permission to use USB serial ports", "run ./maestro fix-permissions")
    try:
        songs = make_songs.load_songs()
        report(True, f"{len(songs)} songs are valid")
    except make_songs.SongError as err:
        report(False, f"Songs have errors:\n{err}", "edit the file named above")
    if pio:
        os.environ["PATH"] = str(Path(pio).parent) + os.pathsep + os.environ.get("PATH", "")
        port = find_uno(pio)
        if port:
            usable, _ = port_ready(port)
            report(usable, f"Uno found on {port}", "run ./maestro fix-permissions")
        else:
            say("  [--] No Uno plugged in right now (only needed for uploading)")
    say()
    say("Everything is ready." if not problems else f"{problems} thing(s) to fix, listed above.")
    return 1 if problems else 0


def cmd_fix_permissions(_args):
    """Lets this user upload to the Uno. Asks for your password, and only needs doing once."""
    state = user_in_dialout()
    if state is None:
        say("This system has no dialout group, so nothing needs doing.")
        return 0
    if state:
        say("Already set up. If uploads still fail, log out and back in.")
        return 0
    command = ["sudo", "usermod", "-aG", "dialout", getpass.getuser()]
    say(f"Running: {shlex.join(command)}")
    if subprocess.call(command) != 0:
        return fail("That did not work, so nothing changed.")
    say("Done. Uploads work now from ./maestro; log out and back in to finish the setup.")
    return 0


def regenerate_songs():
    try:
        songs = make_songs.load_songs()
    except make_songs.SongError as err:
        fail(f"A song has an error, so nothing was changed:\n{err}\nSong help: tools/songs/README.md")
        return None
    make_songs.HEADER.parent.mkdir(parents=True, exist_ok=True)
    make_songs.HEADER.write_text(make_songs.header_text(songs), encoding="utf-8")
    return songs


def cmd_build(_args):
    """Checks that the firmware compiles. No Uno needed."""
    pio = need_pio()
    if not pio or regenerate_songs() is None:
        return 1
    return subprocess.call([pio, "run", "-d", str(CODE), "-e", "uno"])


def cmd_upload(_args):
    """Checks the songs, then uploads the game to the Uno."""
    pio = need_pio()
    if not pio or regenerate_songs() is None:
        return 1
    port = need_uno(pio)
    if not port:
        return 1
    result = run_on_port([pio, "run", "-d", str(CODE), "-e", "uno", "-t", "upload",
                          "--upload-port", port], port)
    if result == 0:
        say("\nDone. The game is running on the Uno. You can unplug it and use the power bank.")
        return 0
    return fail("The upload failed; see the messages above.\n"
                "Check: the USB cable, nothing wired to D0 or D1, and no serial monitor open.")


def cmd_hwtest(_args):
    """Uploads the hardware test, then shows live key and knob readings. Ctrl+C to stop."""
    pio = need_pio()
    if not pio:
        return 1
    port = need_uno(pio)
    if not port:
        return 1
    result = run_on_port([pio, "run", "-d", str(CODE), "-e", "hwtest", "-t", "upload",
                          "--upload-port", port], port)
    if result != 0:
        return fail("The upload failed; see the messages above.")
    say("\nHardware test running. Press each key and turn the knob to every tick.")
    say("Expected A0: 1023 878 742 614 489 368 247 125, within about 30. Ctrl+C to stop.")
    say("Put the game back afterwards with ./maestro upload\n")
    return run_on_port([pio, "device", "monitor", "-d", str(CODE), "-e", "hwtest", "--port", port], port)


def cmd_monitor(_args):
    """Uploads the game with a log of state changes, then shows the log. Ctrl+C to stop."""
    pio = need_pio()
    if not pio or regenerate_songs() is None:
        return 1
    port = need_uno(pio)
    if not port:
        return 1
    result = run_on_port([pio, "run", "-d", str(CODE), "-e", "debug", "-t", "upload",
                          "--upload-port", port], port)
    if result != 0:
        return fail("The upload failed; see the messages above.")
    return run_on_port([pio, "device", "monitor", "-d", str(CODE), "-e", "debug", "--port", port], port)


def serial_lines(port):
    """Starts reading the Uno's serial output. Returns (process, queue of lines). Linux and macOS."""
    flag = "-f" if sys.platform == "darwin" else "-F"
    script = f"stty {flag} {shlex.quote(port)} 115200 raw -echo -hupcl; exec cat {shlex.quote(port)}"
    _, wrap = port_ready(port)
    command = ["sg", "dialout", "-c", script] if wrap else ["sh", "-c", script]
    # Its own process group, so that stopping it also stops cat. A leftover cat holds the port
    # and makes the next upload fail.
    process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, errors="replace", start_new_session=True)
    lines = queue.Queue()

    def pump():
        for line in process.stdout:
            lines.put(line.rstrip())
        lines.put(None)
    threading.Thread(target=pump, daemon=True).start()
    return process, lines


def stop_serial(process):
    """Stops a serial reader from serial_lines, including its cat, and waits for the port to free up."""
    import signal
    import time
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
    time.sleep(1)


def cmd_selftest(_args):
    """Runs the real game on the Uno's own processor with a scripted player. Needs nothing wired."""
    pio = need_pio()
    if not pio or regenerate_songs() is None:
        return 1
    port = need_uno(pio)
    if not port:
        return 1
    if sys.platform == "win32":
        return fail("The self-test reader needs Linux or macOS. Upload the selftest build and open a serial monitor instead.")
    say("Uploading the self-test...")
    build = subprocess.run(["sg", "dialout", "-c", shlex.join([pio, "run", "-d", str(CODE), "-e", "selftest", "-t", "upload", "--upload-port", port])]
                           if port_ready(port)[1] else [pio, "run", "-d", str(CODE), "-e", "selftest", "-t", "upload", "--upload-port", port],
                           capture_output=True, text=True)
    if build.returncode != 0:
        say(build.stdout[-1500:])
        return fail("The upload failed; see the messages above.")
    say("Running. It takes about 20 minutes, and each result prints as it happens. Ctrl+C stops it.\n")
    process, lines = serial_lines(port)
    failures, summary, stopped = [], None, False
    try:
        while True:
            try:
                line = lines.get(timeout=300)
            except queue.Empty:
                failures.append("The board stopped reporting for 5 minutes, so it may have frozen.")
                break
            if line is None:
                failures.append("The serial connection closed early.")
                break
            say(line)
            if line.startswith("FAIL"):
                failures.append(line[5:])
            if line.startswith("RESULT"):
                summary = line
                break
    except KeyboardInterrupt:
        stopped = True
        say("\nStopped.")
    stop_serial(process)
    say("\nPutting the normal game back on the Uno...")
    upload = [pio, "run", "-d", str(CODE), "-e", "uno", "-t", "upload", "--upload-port", port]
    result = run_on_port(upload, port)
    if result != 0:
        say("Trying once more...")
        result = run_on_port(upload, port)
    if result != 0:
        failures.append("Putting the normal game back failed, so the Uno still has the self-test on it. "
                        "Run ./maestro upload.")
    if stopped:
        say("\nThe self-test was stopped midway, so test scores may be in the records. Run it again to restore "
            "them, or clear them with tick 7.")
        return 1
    say("\n" + "=" * 60)
    if summary and not failures:
        say(f"ALL GOOD: {summary[7:]}. The chip and the game's logic work on this board.")
    else:
        say(f"{summary[7:] if summary else 'Did not finish'}. These need a look:")
        for failure in failures:
            say(f"  - {failure}")
    say("This doesn't test the wiring. Use ./maestro hwtest for that once it's wired.")
    say("=" * 60)
    return 0 if summary and not failures and result == 0 else 1


def cmd_songs(_args):
    """Checks every song and rebuilds its data and WAV previews."""
    songs = regenerate_songs()
    if songs is None:
        return 1
    PREVIEW.mkdir(parents=True, exist_ok=True)
    say(f"{'Song':<16}{'Notes':>6}{'Levels':>8}{'Length':>9}")
    for song in songs:
        seconds = make_songs.render_wav(song, PREVIEW / f"{song['stem']}.wav")
        say(f"{song['title']:<16}{len(song['notes']):>6}{len(song['cuts']):>8}{seconds:>8.1f}s")
    say("\nAll songs are valid. Hear one with ./maestro listen <song>, for example: ./maestro listen ode")
    say("Send them to the Uno with ./maestro upload")
    return 0


def play_wav(path):
    players = [["pw-play"], ["paplay"], ["aplay", "-q"], ["afplay"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]]
    for player in players:
        if shutil.which(player[0]):
            return subprocess.call(player + [str(path)])
    if sys.platform == "win32":
        import winsound
        winsound.PlaySound(str(path), winsound.SND_FILENAME)
        return 0
    say(f"No audio player found. Open this file yourself: {path}")
    return 0


def match_song(songs, name):
    name = name.lower()
    return [s for s in songs if name in s["stem"].lower() or name in s["title"].lower()]


def cmd_listen(args):
    """Plays a song as the piezo would: listen, listen ode, or listen ode 3 for one level."""
    songs = regenerate_songs()
    if songs is None:
        return 1
    PREVIEW.mkdir(parents=True, exist_ok=True)
    chosen = songs
    if args:
        chosen = match_song(songs, args[0])
        if len(chosen) != 1:
            names = ", ".join(s["stem"] for s in songs)
            return fail(f"No single song matches \"{args[0]}\". Songs: {names}")
    level = None
    if len(args) > 1:
        if not args[1].isdigit() or not 1 <= int(args[1]) <= len(chosen[0]["cuts"]):
            return fail(f"{chosen[0]['title']} has levels 1 to {len(chosen[0]['cuts'])}.")
        level = int(args[1])
    for song in chosen:
        notes = song["notes"][:song["cuts"][level - 1]] if level else song["notes"]
        names = " ".join(make_songs.NOTES[key] for key, _ in notes)
        say(f"{song['title']}" + (f", level {level}" if level else "") + f": {names}")
        path = PREVIEW / (f"{song['stem']}_level{level}.wav" if level else f"{song['stem']}.wav")
        make_songs.render_wav({**song, "notes": notes}, path)
        play_wav(path)
    return 0


def cmd_test(args):
    """Runs the simulated device tests: test, test --all, or test Rhythm."""
    if not need_pio():
        return 1
    return subprocess.call([sys.executable, str(ROOT / "tools" / "sim" / "run_tests.py")] + list(args))


COMMANDS = {
    "check": cmd_check, "fix-permissions": cmd_fix_permissions, "hwtest": cmd_hwtest, "upload": cmd_upload,
    "selftest": cmd_selftest, "songs": cmd_songs, "listen": cmd_listen, "build": cmd_build, "monitor": cmd_monitor,
    "test": cmd_test,
}

MENU = [
    ("Check that this computer is ready", "check", []),
    ("Allow uploads to the Uno (once only)", "fix-permissions", []),
    ("Test the wiring (uploads the hardware test)", "hwtest", []),
    ("Upload the game to the Uno", "upload", []),
    ("Test the Uno's own chip (nothing wired, about 20 minutes)", "selftest", []),
    ("Check all songs", "songs", []),
    ("Listen to a song", "listen", None),
    ("Run the tests (no Uno needed)", "test", []),
]


def menu():
    while True:
        say("\nМАЕСТРО\n")
        for index, (label, _, _) in enumerate(MENU, 1):
            say(f"  {index}. {label}")
        say("  q. Quit\n")
        try:
            choice = input("Choose: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            say()
            return 0
        if choice == "q":
            return 0
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            say("Type a number from the list, or q.")
            continue
        _, name, args = MENU[int(choice) - 1]
        if args is None:
            try:
                songs = make_songs.load_songs()
            except make_songs.SongError as err:
                fail(str(err))
                continue
            say("Songs: " + ", ".join(s["stem"] for s in songs))
            args = input("Song, and optionally a level (for example: ode 3): ").split()
        try:
            COMMANDS[name](args)
        except KeyboardInterrupt:
            say("\nStopped.")


def show_help():
    say(__doc__)
    say("Commands:")
    for name, function in COMMANDS.items():
        say(f"  {name:<17}{function.__doc__}")
    say("\nWith no command, a menu opens. Everything is explained in README.md")


def main():
    args = sys.argv[1:]
    if not args:
        return menu()
    if args[0] in ("help", "-h", "--help"):
        show_help()
        return 0
    if args[0] not in COMMANDS:
        show_help()
        return fail(f"Unknown command \"{args[0]}\".")
    try:
        function = COMMANDS[args[0]]
        return function(args[1:])
    except KeyboardInterrupt:
        say("\nStopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
