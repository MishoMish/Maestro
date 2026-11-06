"""Python driver for the virtual Маестро (tools/sim/harness.c)."""
import ctypes
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_songs  # noqa: E402

LIB = Path(__file__).resolve().parent / ".deps" / "libharness.so"
ELF = ROOT / "code" / ".pio" / "build" / "uno" / "firmware.elf"
LADDER_OHMS = 220.0
PULL_DOWN_OHMS = 10000.0


class Event(ctypes.Structure):
    _fields_ = [("t_ms", ctypes.c_double), ("kind", ctypes.c_int), ("value", ctypes.c_int)]


_lib = ctypes.CDLL(str(LIB))
_lib.sim_now_ms.restype = ctypes.c_double
_lib.sim_run_ms.argtypes = [ctypes.c_double]
_lib.sim_open.argtypes = [ctypes.c_char_p]
_lib.sim_events.restype = ctypes.c_size_t
_lib.sim_events.argtypes = [ctypes.POINTER(Event), ctypes.c_size_t]


def key_voltage_mv(*keys):
    """A0 voltage for the pressed keys (1-8), solving the real ladder with its pull-down.

    Two pressed keys short the resistors between their taps, so only the top and
    bottom taps matter.
    """
    if not keys:
        return 0
    above = (min(keys) - 1) * LADDER_OHMS     # from 5 V to the highest tap
    below = (9 - max(keys)) * LADDER_OHMS     # from the lowest tap to GND
    if above == 0:
        return 5000
    load = 1 / (1 / below + 1 / PULL_DOWN_OHMS)
    return int(5000 * load / (above + load))


class Device:
    """One Uno running firmware.elf. Keys are numbered 1-8, ticks 1-7, as printed."""

    def __init__(self, elf=ELF, eeprom=None, knob_tick=1):
        self.events = []
        result = _lib.sim_open(str(elf).encode())
        if result != 0:
            raise RuntimeError(f"cannot load {elf}: {result}")
        if eeprom is not None:
            buffer = (ctypes.c_ubyte * len(eeprom)).from_buffer_copy(eeprom)
            _lib.sim_eeprom_set(0, buffer, len(eeprom))
        self.set_adc(0, 0)
        self.knob_to_tick(knob_tick, settle=False)

    # --- Time ---
    def run(self, ms):
        state = _lib.sim_run_ms(ms)
        if state:
            raise RuntimeError(f"CPU stopped: state {state} at {self.now():.0f} ms")
        self._pull_events()

    def now(self):
        return _lib.sim_now_ms()

    def _pull_events(self):
        buffer = (Event * 4096)()
        while True:
            count = _lib.sim_events(buffer, 4096)
            self.events += [(buffer[i].t_ms, buffer[i].kind, buffer[i].value) for i in range(count)]
            if count < 4096:
                return

    # --- Outputs ---
    def lcd(self, row=None):
        text = []
        for r in (0, 1):
            out = ctypes.create_string_buffer(17)
            _lib.sim_lcd(r, out)
            text.append(out.value.decode("latin-1").rstrip())
        return text if row is None else text[row]

    def leds(self):
        return _lib.sim_leds()

    def tone(self):
        return _lib.sim_tone_hz()

    def min_stack_pointer(self):
        return _lib.sim_min_sp()

    def tones_since(self, t):
        return [(when, value) for when, kind, value in self.events if kind == 1 and when >= t]

    def leds_since(self, t):
        """LED changes. Pins change one at a time, so changes within 0.3 ms count as one."""
        merged = []
        for when, kind, value in self.events:
            if kind != 0 or when < t:
                continue
            if merged and when - merged[-1][0] < 0.3:
                merged[-1] = (merged[-1][0], value)
            else:
                merged.append((when, value))
        return merged

    def eeprom(self):
        buffer = (ctypes.c_ubyte * 1024)()
        _lib.sim_eeprom_get(0, buffer, 1024)
        return bytes(buffer)

    def power_cycle(self, knob_tick=1):
        """Power off and on: RAM is lost, EEPROM stays."""
        return Device(eeprom=self.eeprom(), knob_tick=knob_tick)

    # --- Inputs ---
    def set_adc(self, channel, millivolts):
        _lib.sim_set_adc(channel, millivolts)

    def press(self, *keys, bounce=True):
        """Press with contact bounce (about 4 ms of chatter), then stay down."""
        mv = key_voltage_mv(*keys)
        if bounce:
            for level in (mv, 0, mv, 0):
                self.set_adc(0, level)
                self.run(1)
        self.set_adc(0, mv)

    def release(self):
        self.set_adc(0, 0)

    def tap(self, key, hold=80, after=120):
        self.press(key)
        self.run(hold)
        self.release()
        self.run(after)

    def _track_tick(self, value):
        """Follows the firmware's tick, including its dead zone, along the knob's path."""
        old = getattr(self, "knob_value", value)
        tick = getattr(self, "knob_tick", None)
        step = 1 if value >= old else -1
        for point in range(int(old), int(value) + step, step):
            if tick is None or not (tick * 1024 // 7 - 20 <= point < (tick + 1) * 1024 // 7 + 20):
                tick = point * 7 // 1024
        self.knob_tick = tick

    def knob_raw(self, value, settle=True):
        self._track_tick(value)
        self.knob_value = value
        self.set_adc(1, int(value * 5000 / 1023))
        if settle:
            self.run(300)

    def knob_to_item(self, item, count, settle=True):
        """Centre of item (1-based) in a list of count items."""
        self.knob_raw(int((item - 0.5) * 1024 / count), settle)

    def knob_to_tick(self, tick, settle=True):
        self.knob_to_item(tick, 7, settle)

    def nudge(self):
        """Turn the knob exactly one tick, to the centre of the neighbouring tick."""
        tick = self.knob_tick + 1 if self.knob_tick < 6 else self.knob_tick - 1
        self.knob_to_tick(tick + 1)

    def wait_for(self, predicate, timeout=30000, step=10, what="condition"):
        waited = 0
        while not predicate():
            if waited >= timeout:
                raise TimeoutError(f"{what} not reached in {timeout} ms. LCD={self.lcd()} "
                                   f"LEDs={self.leds():08b} tone={self.tone()}")
            self.run(step)
            waited += step
        return waited

    def wait_lcd(self, text, row=None, timeout=30000):
        """The LCD is written one character at a time, so a match only counts if it
        still holds 20 ms later, once the whole screen has been updated."""
        def shown():
            lines = self.lcd() if row is None else [self.lcd(row)]
            return any(text in line for line in lines)

        def settled():
            if not shown():
                return False
            self.run(20)
            return shown()
        return self.wait_for(settled, timeout, what=f"LCD '{text}'")


def load_song(name):
    """Song dict from tools/songs, for checking the firmware against the source."""
    for song in make_songs.load_songs():
        if name in song["stem"]:
            return song
    raise KeyError(name)
