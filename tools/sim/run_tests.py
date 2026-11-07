#!/usr/bin/env python3
"""Builds the firmware and runs every test on the virtual device, in parallel.

    python3 tools/sim/run_tests.py          everything except whole-piece games
    python3 tools/sim/run_tests.py --all    everything (allow 20+ minutes)
    python3 tools/sim/run_tests.py Rhythm   only tests whose name contains "Rhythm"
"""
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def run_one(test_id):
    result = subprocess.run([sys.executable, "-m", "unittest", test_id], cwd=HERE,
                            capture_output=True, text=True)
    return test_id, result.returncode == 0, result.stderr


def main():
    args = sys.argv[1:]
    everything = "--all" in args
    names = [a for a in args if a != "--all"]
    if not (HERE / ".deps" / "libharness.so").exists():
        subprocess.check_call([str(HERE / "setup.sh")])
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "make_songs.py")], stdout=subprocess.DEVNULL)
    subprocess.check_call(["pio", "run", "-d", str(ROOT / "code"), "-e", "uno", "-e", "debug", "-e", "hwtest", "-e", "selftest", "-e", "selftest_short"],
                          stdout=subprocess.DEVNULL)

    sys.path.insert(0, str(HERE))
    modules = ["test_guide", "test_menus", "test_game", "test_ear"] + (["test_full_games"] if everything or names else [])
    tests = []
    for suite in unittest.defaultTestLoader.loadTestsFromNames(modules):
        for group in suite:
            tests += [case.id() for case in group]
    if names:
        tests = [t for t in tests if any(n in t for n in names)]

    failed = []
    with ThreadPoolExecutor(os.cpu_count()) as pool:
        for count, (test_id, passed, output) in enumerate(pool.map(run_one, tests), 1):
            print(f"[{count}/{len(tests)}] {'ok  ' if passed else 'FAIL'} {test_id}", flush=True)
            if not passed:
                failed.append((test_id, output))
    for test_id, output in failed:
        print(f"\n===== {test_id}\n{output}")
    print(f"\n{len(tests) - len(failed)} of {len(tests)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
