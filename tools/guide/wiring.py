"""The Маестро wiring as data: the one source for the build guide's diagrams and tables.

Run this file to check the wiring electrically. build_guide.py refuses to build if it fails.
"""
# Key k (1-8): name on the key, Latin name, LED colour, Uno pin.
KEYS = [("До", "Do", "red", "D6"), ("Ре", "Re", "yellow", "D7"), ("Ми", "Mi", "green", "D9"),
        ("Фа", "Fa", "blue", "D10"), ("Сол", "Sol", "white", "D13"), ("Ла", "La", "yellow", "A2"),
        ("Си", "Si", "green", "A3"), ("До'", "Do'", "red", "A4")]

# LCD pin number, name, where it goes. "H+"/"H-" are the half breadboard's rails.
LCD_PINS = [(1, "VSS", "GND rail"), (2, "VDD", "5V rail"), (3, "V0", "Contrast pot, middle leg"),
            (4, "RS", "D12"), (5, "RW", "GND rail"), (6, "E", "D11"), (7, "D0", None), (8, "D1", None),
            (9, "D2", None), (10, "D3", None), (11, "D4", "D5"), (12, "D5", "D4"), (13, "D6", "D3"),
            (14, "D7", "D2"), (15, "A", "Backlight resistor"), (16, "K", "GND rail")]


def key_n(k):
    return 8 * k - 4


class Part:
    def __init__(self, kind, step, a=None, b=None, **info):
        self.kind, self.step, self.a, self.b, self.info = kind, step, a, b, info


# Holes: ("F", col, row) on the full board, ("H", col, row) on the half board.
# Rails: ("F", col, "back5v"|"backgnd"|"fronta0"|"frontgnd"), ("H", col, "plus"|"minus").
# Off-board ends: ("U", pin) on the Uno, ("LCD", name), ("POT", leg), ("PIEZO", leg), ("KNOB", leg).
def build_parts():
    parts = [Part("wire", 1, ("F", 1, "backgnd"), ("F", 1, "frontgnd"), name="GND link", color="black", side=True)]
    for k in range(1, 9):
        n = key_n(k)
        parts.append(Part("button", 2, ("F", n - 1, "e"), ("F", n + 1, "f"), k=k))
    for k in range(1, 9):
        n = key_n(k)
        parts.append(Part("led", 3, ("F", n, "c"), ("F", n + 2, "c"), k=k, color=KEYS[k - 1][2]))
    for k in range(1, 9):
        n = key_n(k)
        parts.append(Part("res", 4, ("F", n + 2, "b"), ("F", n + 2, "backgnd"), ohm=220, name=f"LED resistor {k}"))
    for k in range(1, 8):
        n = key_n(k)
        # Starts in row h and ends in row i, so that two legs never share a hole.
        parts.append(Part("res", 5, ("F", n - 1, "h"), ("F", n + 7, "i"), ohm=220, name=f"Ladder {k}"))
    parts.append(Part("res", 5, ("F", 59, "j"), ("F", 63, "frontgnd"), ohm=220, name="Ladder 8"))
    parts.append(Part("wire", 6, ("F", 3, "a"), ("F", 3, "back5v"), name="Key 1 top", color="red"))
    for k in range(1, 9):
        n = key_n(k)
        parts.append(Part("wire", 6, ("F", n + 1, "g"), ("F", n + 1, "fronta0"), name=f"A0 wire {k}", color="orange"))
    parts.append(Part("res", 6, ("F", 1, "fronta0"), ("F", 5, "frontgnd"), ohm=10000, name="Pull-down"))

    parts.append(Part("wire", 7, ("U", "5V"), ("H", 1, "plus"), name="Uno 5V", color="red", tag="Uno 5V"))
    parts.append(Part("wire", 7, ("U", "GND"), ("H", 2, "minus"), name="Uno GND", color="black", tag="Uno GND"))
    parts.append(Part("wire", 7, ("H", 4, "plus"), ("F", 1, "back5v"), name="5V to key bed", color="red", tag="Key bed 5V", tag_F="5V in"))
    parts.append(Part("wire", 7, ("H", 5, "minus"), ("F", 2, "backgnd"), name="GND to key bed", color="black", tag="Key bed GND", tag_F="GND in"))

    parts.append(Part("pot", 8, ("H", 8, "e"), ("H", 12, "e"), wiper=("H", 10, "e"), name="Contrast pot"))
    parts.append(Part("wire", 8, ("H", 8, "plus"), ("H", 8, "a"), name="Pot end", color="red"))
    parts.append(Part("wire", 8, ("H", 12, "minus"), ("H", 12, "a"), name="Pot end", color="black"))
    parts.append(Part("res", 8, ("H", 16, "plus"), ("H", 20, "c"), ohm=220, name="Backlight"))

    for k in range(1, 9):
        n = key_n(k)
        pin = KEYS[k - 1][3]
        parts.append(Part("wire", 9, ("F", n, "a"), ("U", pin), name=f"LED wire {k}", color=KEYS[k - 1][2], tag=pin))
    parts.append(Part("wire", 9, ("F", 2, "fronta0"), ("U", "A0"), name="A0 bus", color="orange", tag="Uno A0"))

    lcd_ends = {"VSS": ("H", 22, "minus"), "VDD": ("H", 22, "plus"), "V0": ("H", 10, "a"), "RW": ("H", 23, "minus"),
                "A": ("H", 20, "a"), "K": ("H", 24, "minus"), "RS": ("U", "D12"), "E": ("U", "D11"),
                "D4": ("U", "D5"), "D5": ("U", "D4"), "D6": ("U", "D3"), "D7": ("U", "D2")}
    for name, end in lcd_ends.items():
        parts.append(Part("fm", 10, ("LCD", name), end, name=f"LCD {name}", tag=f"LCD {name}"))
    parts.append(Part("fm", 11, ("PIEZO", "1"), ("U", "D8"), name="Piezo signal", tag="Piezo"))
    parts.append(Part("fm", 11, ("PIEZO", "2"), ("H", 26, "minus"), name="Piezo GND", tag="Piezo"))
    parts.append(Part("fm", 12, ("KNOB", "1"), ("H", 28, "plus"), name="Knob end", tag="Knob"))
    parts.append(Part("fm", 12, ("KNOB", "3"), ("H", 28, "minus"), name="Knob end", tag="Knob"))
    parts.append(Part("fm", 12, ("KNOB", "2"), ("U", "A1"), name="Knob middle", tag="Knob"))
    return parts


# --- Electrical model ---
def base_net(end):
    board = end[0]
    if board in ("F", "H"):
        col, row = end[1], end[2]
        if len(row) > 1:
            return (board, row)                    # rails run the whole length
        return (board, col, "top" if row in "abcde" else "bottom")
    return end


class Nets:
    def __init__(self):
        self.parent = {}

    def find(self, node):
        self.parent.setdefault(node, node)
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def join(self, a, b):
        self.parent[self.find(a)] = self.find(b)


def build_nets(parts, pressed=None):
    nets = Nets()
    # A tact switch's legs on one side are joined inside it, across the channel.
    for part in parts:
        if part.kind == "button":
            n = key_n(part.info["k"])
            nets.join(("F", n - 1, "top"), ("F", n - 1, "bottom"))
            nets.join(("F", n + 1, "top"), ("F", n + 1, "bottom"))
            if part.info["k"] == pressed:
                nets.join(("F", n - 1, "bottom"), ("F", n + 1, "bottom"))
        elif part.kind == "wire":
            nets.join(base_net(part.a), base_net(part.b))
        elif part.kind == "fm":
            nets.join(base_net(part.a), base_net(part.b))
        elif part.kind == "pot":
            nets.join(("POT", 1), base_net(part.a))
            nets.join(("POT", 3), base_net(part.b))
            nets.join(("POT", 2), base_net(part.info["wiper"]))
    return nets


def solve_a0(parts, pressed):
    """A0 reading (0-1023) with one key pressed, by nodal analysis of the resistors."""
    nets = build_nets(parts, pressed)
    vcc, gnd, a0 = nets.find(("U", "5V")), nets.find(("U", "GND")), nets.find(("U", "A0"))
    resistors = [(nets.find(base_net(p.a)), nets.find(base_net(p.b)), p.info["ohm"])
                 for p in parts if p.kind == "res"]
    nodes = sorted({x for r in resistors for x in r[:2]} - {vcc, gnd}, key=str)
    index = {node: i for i, node in enumerate(nodes)}
    size = len(nodes)
    matrix = [[0.0] * (size + 1) for _ in range(size)]
    for x, y, ohm in resistors:
        g = 1 / ohm
        for here, there in ((x, y), (y, x)):
            if here in index:
                i = index[here]
                matrix[i][i] += g
                if there in index:
                    matrix[i][index[there]] -= g
                elif there == vcc:
                    matrix[i][size] += g * 5.0
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(matrix[r][col]))
        if abs(matrix[pivot][col]) < 1e-12:
            continue
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        for row in range(size):
            if row != col and matrix[row][col]:
                factor = matrix[row][col] / matrix[col][col]
                for c in range(col, size + 1):
                    matrix[row][c] -= factor * matrix[col][c]
    if a0 == vcc:
        return 1023
    if a0 == gnd or a0 not in index:
        return 0
    i = index[a0]
    return int(1023 * (matrix[i][size] / matrix[i][i]) / 5.0)


def decode(value):
    level = (value + 64) // 128
    return None if level < 1 else 8 - min(level, 8)


def check():
    """Returns a list of problems. Empty means the wiring is right."""
    parts = build_parts()
    problems = []

    # Every hole holds one thing.
    used = {}
    for part in parts:
        ends = [part.a, part.b] + ([part.info["wiper"]] if part.kind == "pot" else [])
        if part.kind == "button":
            n = key_n(part.info["k"])
            ends = [("F", n - 1, "e"), ("F", n - 1, "f"), ("F", n + 1, "e"), ("F", n + 1, "f")]
        for end in ends:
            if end[0] in ("F", "H"):
                if end in used:
                    problems.append(f"hole {end} used by both {used[end]} and {part.info.get('name', part.kind)}")
                used[end] = part.info.get("name", part.kind)
                if end[0] == "F" and not 1 <= end[1] <= 63:
                    problems.append(f"column out of range: {end}")
                if end[0] == "H" and not 1 <= end[1] <= 30:
                    problems.append(f"column out of range: {end}")

    # Keys: firmware must decode every key from the real ladder.
    readings = {}
    for k in range(1, 9):
        readings[k] = solve_a0(parts, k)
        if decode(readings[k]) != k - 1:
            problems.append(f"key {k} reads {readings[k]} and decodes as {decode(readings[k])}")
    if solve_a0(parts, None) != 0:
        problems.append(f"nothing pressed reads {solve_a0(parts, None)}, not 0")

    nets = build_nets(parts)
    gnd, vcc = nets.find(("U", "GND")), nets.find(("U", "5V"))

    # LEDs: Uno pin to long leg; short leg through 220 ohm to GND. Firmware pins.
    for part in parts:
        if part.kind == "led":
            k = part.info["k"]
            if nets.find(base_net(part.a)) != nets.find(("U", KEYS[k - 1][3])):
                problems.append(f"LED {k} long leg is not on {KEYS[k - 1][3]}")
            found = False
            for res in parts:
                if res.kind == "res" and res.info["ohm"] == 220:
                    ends = {nets.find(base_net(res.a)), nets.find(base_net(res.b))}
                    if ends == {nets.find(base_net(part.b)), gnd}:
                        found = True
            if not found:
                problems.append(f"LED {k} short leg has no 220 ohm path to GND")

    # LCD, against LiquidCrystal lcd(12, 11, 5, 4, 3, 2) in the firmware.
    for lcd, pin in {"RS": "D12", "E": "D11", "D4": "D5", "D5": "D4", "D6": "D3", "D7": "D2"}.items():
        if nets.find(("LCD", lcd)) != nets.find(("U", pin)):
            problems.append(f"LCD {lcd} is not on {pin}")
    for lcd, net in {"VSS": gnd, "RW": gnd, "K": gnd, "VDD": vcc}.items():
        if nets.find(("LCD", lcd)) != net:
            problems.append(f"LCD {lcd} is on the wrong power rail")
    if nets.find(("LCD", "V0")) != nets.find(("POT", 2)):
        problems.append("LCD V0 is not on the contrast pot's middle leg")
    if {nets.find(("POT", 1)), nets.find(("POT", 3))} != {vcc, gnd}:
        problems.append("Contrast pot ends are not on 5V and GND")
    backlight = [p for p in parts if p.info.get("name") == "Backlight"][0]
    if {nets.find(base_net(backlight.a)), nets.find(base_net(backlight.b))} != {vcc, nets.find(("LCD", "A"))}:
        problems.append("LCD A has no 220 ohm path to 5V")

    # Piezo and knob.
    if nets.find(("PIEZO", "1")) != nets.find(("U", "D8")) or nets.find(("PIEZO", "2")) != gnd:
        problems.append("Piezo is not between D8 and GND")
    if nets.find(("KNOB", "2")) != nets.find(("U", "A1")):
        problems.append("Knob middle leg is not on A1")
    if {nets.find(("KNOB", "1")), nets.find(("KNOB", "3"))} != {vcc, gnd}:
        problems.append("Knob ends are not on 5V and GND")

    # No shorts.
    if vcc == gnd:
        problems.append("5V and GND are shorted")
    for pin in ["A0", "A1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13", "A2", "A3", "A4"]:
        if nets.find(("U", pin)) in (vcc, gnd):
            problems.append(f"{pin} is shorted to power")

    # Counts match the parts list.
    count = {
        "220 ohm": sum(1 for p in parts if p.kind == "res" and p.info["ohm"] == 220),
        "10k": sum(1 for p in parts if p.kind == "res" and p.info["ohm"] == 10000),
        "female-male": sum(1 for p in parts if p.kind == "fm"),
        "buttons": sum(1 for p in parts if p.kind == "button"),
        "leds": sum(1 for p in parts if p.kind == "led"),
    }
    for name, want in {"220 ohm": 17, "10k": 1, "female-male": 17, "buttons": 8, "leds": 8}.items():
        if count[name] != want:
            problems.append(f"{name}: {count[name]} in the wiring, parts list says {want}")
    return problems, readings


if __name__ == "__main__":
    problems, readings = check()
    print("A0 readings:", [readings[k] for k in range(1, 9)])
    parts = build_parts()
    print("Solid wires:", sum(1 for p in parts if p.kind == "wire"), "| female-male:", sum(1 for p in parts if p.kind == "fm"))
    print("\n".join(problems) if problems else "Wiring is correct.")
    raise SystemExit(1 if problems else 0)
