"""SVG drawings for the build guide. All positions come from wiring.py."""
from html import escape

import wiring

LED_FILL = {"red": "#e5302a", "yellow": "#f6c21c", "green": "#27a845", "blue": "#2a6be0", "white": "#ffffff"}
WIRE_FILL = {"red": "#d92b25", "black": "#20242a", "orange": "#ee7d11", "yellow": "#e3ae00", "green": "#1e9a3c",
             "blue": "#2563d6", "white": "#f4f4f2", "violet": "#7a3fc4"}
RAIL = {"back5v": ("5V", "#d92b25"), "backgnd": ("GND", "#20242a"), "fronta0": ("A0 bus", "#ee7d11"),
        "frontgnd": ("GND", "#20242a"), "plus": ("5V", "#d92b25"), "minus": ("GND", "#20242a")}
BANDS = {220: ["#d92b25", "#d92b25", "#7a4a1e", "#c9a227"], 10000: ["#7a4a1e", "#20242a", "#ee7d11", "#c9a227"]}
INK, MUTED = "#15181c", "#5a626c"
_uid = [0]


def uid():
    _uid[0] += 1
    return f"g{_uid[0]}"


def figure(svg, caption, cls=""):
    return f'<figure class="fig {cls}"><div class="scroll">{svg}</div><figcaption>{caption}</figcaption></figure>'


def svg_open(w, h, label, minw=None):
    style = f' style="min-width:{minw}px"' if minw else ""
    return (f'<svg viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="{escape(label)}"{style} '
            f'font-family="\'IBM Plex Sans\',system-ui,sans-serif">')


def text(x, y, s, size=12, fill=INK, anchor="middle", weight=400, rotate=None, mono=False, halo=None):
    extra = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ""
    family = ' font-family="\'IBM Plex Mono\',monospace"' if mono else ""
    if halo:
        extra += f' stroke="{halo}" stroke-width="4" stroke-linejoin="round" paint-order="stroke"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{family}{extra}>{escape(str(s))}</text>')


class Board:
    """A breadboard drawn top-down. The back is at the top, and you sit below it."""
    ROWS = {**{c: 3 + i for i, c in enumerate("abcde")}, **{c: 9 + i for i, c in enumerate("fghij")},
            "back5v": 0, "backgnd": 1, "plus": 0, "minus": 1, "fronta0": 15, "frontgnd": 16}

    def __init__(self, name, c0, c1, pitch, top_margin=60, bottom_margin=42, tag_rotate=False):
        self.name, self.c0, self.c1, self.p = name, c0, c1, pitch
        self.left, self.right = 84, 34
        self.top, self.bottom = top_margin, max(bottom_margin, pitch * 0.9 + 40)
        self.tag_rotate = tag_rotate
        self.w = self.left + (c1 - c0) * pitch + self.right
        self.h = self.top + 16 * pitch + self.bottom

    def x(self, col):
        return self.left + (col - self.c0) * self.p

    def y(self, row):
        return self.top + self.ROWS[row] * self.p

    def visible(self, end):
        return end[0] == self.name and self.c0 <= end[1] <= self.c1

    def base(self):
        p, out, pid = self.p, [], uid()
        hole = max(1.2, p * 0.13)
        x0, x1 = self.x(self.c0) - p * 0.8, self.x(self.c1) + p * 0.8
        y0, y1 = self.y("back5v") - p * 0.9, self.y("frontgnd") + p * 0.9
        out.append(f'<defs><pattern id="{pid}" width="{p}" height="{p}" patternUnits="userSpaceOnUse" '
                   f'patternTransform="translate({self.x(self.c0) - p / 2} {self.y("back5v") - p / 2})">'
                   f'<rect x="{p / 2 - hole}" y="{p / 2 - hole}" width="{2 * hole}" height="{2 * hole}" rx="0.8" fill="#8e8b80"/>'
                   f'</pattern></defs>')
        out.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="5" fill="#f1efe7" stroke="#c9c5b6"/>')
        # channel
        ch = self.y("e") + p
        out.append(f'<rect x="{x0}" y="{ch - p * 0.28}" width="{x1 - x0}" height="{p * 0.56}" fill="#dcd8ca"/>')
        for top, rows in ((self.y("a"), 5), (self.y("f"), 5), (self.y("back5v"), 2), (self.y("fronta0"), 2)):
            out.append(f'<rect x="{self.x(self.c0) - p / 2}" y="{top - p / 2}" width="{(self.c1 - self.c0 + 1) * p}" '
                       f'height="{rows * p}" fill="url(#{pid})"/>')
        rails = ("back5v", "backgnd", "fronta0", "frontgnd") if self.name == "F" else ("plus", "minus")
        for rail in rails:
            label, color = RAIL[rail]
            y = self.y(rail)
            out.append(f'<line x1="{self.x(self.c0) - p * 0.5}" x2="{self.x(self.c1) + p * 0.5}" y1="{y}" y2="{y}" '
                       f'stroke="{color}" stroke-width="{max(2, p * 0.5)}" stroke-opacity="0.13"/>')
            out.append(text(x0 - 14, y + 4, label, 11, color, "end", 600))
        if self.name == "H":
            for rail in ("fronta0", "frontgnd"):
                out.append(text(x0 - 14, self.y(rail) + 4, "unused", 10, MUTED, "end"))
        size = max(9, min(12, p * 0.5))
        if self.name == "F":
            mid = (self.x(self.c0) + self.x(self.c1)) / 2
            out.append(text(self.x(self.c1), 12, "BACK (Uno side)", 11, MUTED, "end", 600))
            out.append(text(mid, self.h - 6, "FRONT: you sit here", 11, MUTED, "middle", 600))
        step = 1 if p >= 20 else 5
        for col in range(self.c0, self.c1 + 1):
            if col == self.c0 or col % step == 0 or (step == 5 and col == self.c1 and self.c1 % 5 and self.c1 - self.c1 % 5 < self.c1 - 2):
                out.append(text(self.x(col), ch + 4, col, size, MUTED))
        if p >= 11:
            for c in "abcdefghij":
                out.append(text(self.x(self.c0) - p * 0.72, self.y(c) + 3.5, c, min(size, 10), MUTED, weight=500))
        return "".join(out)

    def end_xy(self, end):
        return self.x(end[1]), self.y(end[2])


def lead(x1, y1, x2, y2, p):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#8a8f96" stroke-width="{max(1.3, p * 0.1):.1f}" stroke-linecap="round"/>'


def dot(x, y, p, fill="#6e737a"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{max(1.8, p * 0.15):.1f}" fill="{fill}"/>'


def draw_resistor(b, part):
    x1, y1 = b.end_xy(part.a)
    x2, y2 = b.end_xy(part.b)
    p = b.p
    length, width = p * 2.3, p * 0.82
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    import math
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    bands = "".join(f'<rect x="{-length / 2 + length * pos:.1f}" y="{-width / 2:.1f}" width="{length * 0.09:.1f}" height="{width:.1f}" fill="{c}"/>'
                    for pos, c in zip((0.14, 0.31, 0.48, 0.8), BANDS[part.info["ohm"]]))
    body = (f'<g transform="translate({cx:.1f} {cy:.1f}) rotate({angle:.1f})"><rect x="{-length / 2:.1f}" y="{-width / 2:.1f}" '
            f'width="{length:.1f}" height="{width:.1f}" rx="{width / 2:.1f}" fill="#d8bd8d" stroke="#8f7a50" stroke-width="0.7"/>{bands}</g>')
    return lead(x1, y1, x2, y2, p) + dot(x1, y1, p) + dot(x2, y2, p) + body


def draw_button(b, part):
    n = wiring.key_n(part.info["k"])
    p = b.p
    cx, cy = b.x(n), (b.y("e") + b.y("f")) / 2
    half = p * 1.18
    out = (f'<rect x="{cx - half:.1f}" y="{cy - half:.1f}" width="{2 * half:.1f}" height="{2 * half:.1f}" rx="{p * 0.15:.1f}" fill="#2b2f36"/>'
           f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{p * 0.62:.1f}" fill="#5a606a" stroke="#171a1e"/>')
    for col in (n - 1, n + 1):
        for row in "ef":
            out += dot(b.x(col), b.y(row), p, "#c7ccd2")
    return out


def draw_led(b, part):
    x1, y = b.end_xy(part.a)
    x2 = b.x(part.b[1])
    p = b.p
    color = LED_FILL[part.info["color"]]
    cx = (x1 + x2) / 2
    out = lead(x1, y, x2, y, p) + dot(x1, y, p, "#c7ccd2") + dot(x2, y, p, "#c7ccd2")
    out += (f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="{p * 0.86:.1f}" fill="{color}" stroke="#20242a" stroke-opacity="0.65" stroke-width="1"/>'
            f'<circle cx="{cx - p * 0.25:.1f}" cy="{y - p * 0.27:.1f}" r="{p * 0.2:.1f}" fill="#fff" fill-opacity="0.65"/>')
    if p >= 20:
        out += text(x1 - p * 0.05, y - p * 1.0, "+", p * 0.62, INK, weight=700)
    return out


def draw_pot(b, part):
    p = b.p
    x1, y = b.end_xy(part.a)
    x2 = b.x(part.b[1])
    xm = b.x(part.info["wiper"][1])
    top = b.y("c") - p * 0.4
    out = (f'<rect x="{x1 - p * 0.7:.1f}" y="{top:.1f}" width="{x2 - x1 + p * 1.4:.1f}" height="{y - top + p * 0.4:.1f}" rx="3" fill="#3a6fb5" stroke="#21477a"/>'
           f'<circle cx="{xm:.1f}" cy="{(top + y) / 2:.1f}" r="{p * 0.95:.1f}" fill="#f2f2ee" stroke="#21477a"/>'
           f'<line x1="{xm - p * 0.6:.1f}" x2="{xm + p * 0.6:.1f}" y1="{(top + y) / 2:.1f}" y2="{(top + y) / 2:.1f}" stroke="#21477a" stroke-width="2"/>')
    for x in (x1, xm, x2):
        out += dot(x, y, p, "#c7ccd2")
    return out


def wire_line(points, color, p, dashed=False):
    width = max(2.4, p * 0.2)
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)
    edge = "#8a8f96" if color == WIRE_FILL["white"] else "#000"
    dash = f' stroke-dasharray="{width * 2.2:.1f} {width * 1.2:.1f}"' if dashed else ""
    return (f'<path d="{path}" fill="none" stroke="{edge}" stroke-opacity="0.45" stroke-width="{width + 1.4:.1f}" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width:.1f}" stroke-linejoin="round" stroke-linecap="round"{dash}/>')


def draw_wire(b, part, tag_slots):
    """Wires and female-male jumpers. An end on another board or part becomes a labelled stub."""
    p = b.p
    dashed = part.kind == "fm"
    color = WIRE_FILL["violet"] if dashed else WIRE_FILL.get(part.info.get("color", "black"), "#20242a")
    a_on, b_on = part.a[0] == b.name, part.b[0] == b.name
    if a_on and b_on:
        x1, y1 = b.end_xy(part.a)
        x2, y2 = b.end_xy(part.b)
        if part.info.get("side"):
            xs = b.x(b.c0) - p * 0.8 - 6
            pts = [(x1, y1), (xs, y1), (xs, y2), (x2, y2)]
            return wire_line(pts, color, p) + dot(x1, y1, p, "#20242a") + dot(x2, y2, p, "#20242a")
        return wire_line([(x1, y1), (x2, y2)], color, p) + dot(x1, y1, p, "#20242a") + dot(x2, y2, p, "#20242a")
    on = part.a if a_on else part.b
    x, y = b.end_xy(on)
    label = part.info.get(f"tag_{b.name}") or part.info.get("tag") or part.info.get("name")
    if on[2] in ("fronta0", "frontgnd"):       # goes off the front edge, then is labelled below
        ye = b.h - 24
        return wire_line([(x, y), (x, ye)], color, p, dashed) + dot(x, y, p, "#20242a") + text(x, ye + 15, label, 11, INK, "middle", 600)
    level = tag_slots.get(part.info.get("name"), 0)
    if b.tag_rotate:
        ye = 72
        out = wire_line([(x, y), (x, ye)], color, p, dashed) + dot(x, y, p, "#20242a")
        return out + text(x + 3.5, ye - 4, label, 10.5, INK, "start", 600, rotate=-55)
    ye = 42 - 16 * level
    out = wire_line([(x, y), (x, ye + 4)], color, p, dashed) + dot(x, y, p, "#20242a")
    return out + text(x, ye, label, 11, INK, "middle", 600)


def draw_part(b, part, tag_slots):
    ends = [part.a, part.b]
    if not any(b.visible(e) for e in ends):
        return ""
    kind = part.kind
    if kind == "res":
        return draw_resistor(b, part)
    if kind == "button":
        return draw_button(b, part)
    if kind == "led":
        return draw_led(b, part)
    if kind == "pot":
        return draw_pot(b, part)
    return draw_wire(b, part, tag_slots)


ORDER = {"pot": 0, "button": 1, "res": 2, "led": 3, "wire": 4, "fm": 5}


def board_figure(name, step, c0, c1, pitch, label, notes=None, minw=None, keep_steps=None, top_margin=60,
                 tag_rotate=False, tag_slots=None):
    """Earlier steps fade back; this step's parts are drawn at full strength."""
    b = Board(name, c0, c1, pitch, top_margin=top_margin, tag_rotate=tag_rotate)
    parts = wiring.build_parts()
    tag_slots = tag_slots or {"GND to key bed": 1}      # lifts one of two neighbouring labels
    out = [svg_open(b.w, b.h, label, minw), b.base()]
    old = [p for p in parts if p.step < step and (keep_steps is None or p.step in keep_steps)]
    new = [p for p in parts if p.step == step]
    in_range = lambda p: any(b.visible(e) for e in (p.a, p.b))
    for group, opacity in ((old, 0.34), (new, 1)):
        body = "".join(draw_part(b, p, tag_slots) for p in sorted(group, key=lambda q: ORDER[q.kind]) if in_range(p))
        out.append(f'<g opacity="{opacity}">{body}</g>')
    for col, row, note, dx, dy, anchor in notes or []:
        x, y = b.x(col), b.y(row)
        out.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + dx:.1f}" y2="{y + dy:.1f}" stroke="#0a4fb5" stroke-width="1.3"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{b.p * 0.3:.1f}" fill="none" stroke="#0a4fb5" stroke-width="1.5"/>')
        tx, ty = x + dx, y + dy + (-4 if dy < 0 else 13)
        out.append(text(tx, ty, note, 13, "#0a4fb5", anchor, 700, halo="#f1efe7"))
    out.append("</svg>")
    return "".join(out)


# --- Uno ---
TOP_PINS = ["AREF", "GND3", "D13", "D12", "D11", "D10", "D9", "D8", None, "D7", "D6", "D5", "D4", "D3", "D2", "D1", "D0"]
BOTTOM_PINS = ["IOREF", "RST", "3V3", "5V", "GND", "GND2", "VIN", None, "A0", "A1", "A2", "A3", "A4", "A5"]


def uno_figure(highlight, label, minw=620):
    """highlight: pin name -> text to show. Other pins stay plain."""
    w, h = 760, 420
    bx, by, bw, bh = 110, 120, 560, 180
    out = [svg_open(w, h, label, minw)]
    out.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="9" fill="#0d7a86" stroke="#075860" stroke-width="2"/>')
    out.append(f'<rect x="{bx - 26}" y="{by + 18}" width="58" height="46" rx="3" fill="#b8bdc4" stroke="#6e737a"/>')
    out.append(text(bx + 3, by + 46, "USB", 12, INK, "middle", 700))
    out.append(f'<rect x="{bx - 14}" y="{by + 118}" width="50" height="42" rx="3" fill="#2b2f36"/>')
    out.append(f'<rect x="{bx + 240}" y="{by + 92}" width="240" height="38" rx="3" fill="#20242a"/>')
    out.append(text(bx + 360, by + 116, "ATmega328P", 12, "#d9dde2", "middle", 500))
    out.append(text(bx + 160, by + 86, "Arduino Uno", 15, "#eaf6f7", "middle", 700))
    pitch = 25

    def header(names, start, y, up):
        x = start
        res = ""
        for name in names:
            if name is None:
                x += pitch * 0.6
                continue
            shown = name.replace("GND2", "GND").replace("GND3", "GND")
            on = name in highlight
            res += (f'<rect x="{x - 9}" y="{y - 9}" width="18" height="18" rx="2" fill="{"#ffd21f" if on else "#23272d"}" '
                    f'stroke="{"#20242a" if on else "#0b0d10"}" stroke-width="{1.6 if on else 1}"/>')
            res += text(x, y + (22 if up else -15), shown, 9.5, "#f2fbfb", "middle", 700 if on else 400)
            if on:
                edge = y - 9 if up else y + 9
                end = edge - 28 if up else edge + 28
                res += f'<line x1="{x}" x2="{x}" y1="{edge}" y2="{end}" stroke="#0a4fb5" stroke-width="1.5"/>'
                res += text(x + (4 if up else 4), end - 5 if up else end + 5, highlight[name], 12, "#0a4fb5", "start", 700,
                            rotate=-45 if up else 45)
            x += pitch
        return res

    out.append(header(TOP_PINS, bx + 150, by + 15, True))
    out.append(header(BOTTOM_PINS, bx + 210, by + bh - 15, False))
    out.append("</svg>")
    return "".join(out)


# --- LCD ---
def lcd_figure(label, minw=620):
    w, h = 760, 300
    bx, by, bw, bh = 80, 100, 600, 165
    out = [svg_open(w, h, label, minw)]
    out.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="6" fill="#117a3f" stroke="#0b5a2d" stroke-width="2"/>')
    out.append(f'<rect x="{bx + 50}" y="{by + 42}" width="{bw - 100}" height="100" rx="3" fill="#22262b"/>')
    out.append(f'<rect x="{bx + 68}" y="{by + 58}" width="{bw - 136}" height="68" fill="#2d5fd0"/>')
    out.append(text(bx + bw / 2, by + 88, "MAESTRO     1/7", 22, "#e8f0ff", "middle", 500, mono=True))
    out.append(text(bx + bw / 2, by + 116, "Light only", 22, "#e8f0ff", "middle", 500, mono=True))
    pitch = 28
    start = bx + 90
    groups = {"power": "#d92b25", "signal": "#7a3fc4", "unused": "#9aa0a8"}
    for number, name, to in wiring.LCD_PINS:
        x = start + (number - 1) * pitch
        kind = "unused" if to is None else ("signal" if to.startswith("D") else "power")
        color = groups[kind]
        out.append(f'<rect x="{x - 7}" y="{by + 12}" width="14" height="14" rx="2" fill="{color if kind != "unused" else "#d9dbde"}" stroke="#0b5a2d"/>')
        out.append(text(x, by + 41, number, 9.5, "#eafbef", "middle"))
        out.append(f'<line x1="{x}" x2="{x}" y1="{by + 12}" y2="{by - 8}" stroke="{color}" stroke-width="{1 if kind == "unused" else 2.2}"/>')
        out.append(text(x + 3, by - 13, name + ("" if to else ""), 11.5, INK if to else MUTED, "start", 700 if to else 400, rotate=-50))
    out.append("</svg>")
    return "".join(out)


# --- Simple connection drawing: a part with legs going to named places ---
def legs_figure(kind, legs, label, minw=None):
    """legs: list of (leg name, destination)."""
    w, h = 620, 60 + 62 * len(legs)
    out = [svg_open(w, h, label, minw)]
    cy = h / 2
    if kind == "piezo":
        out.append(f'<circle cx="90" cy="{cy}" r="52" fill="#20242a"/><circle cx="90" cy="{cy}" r="18" fill="#5a606a"/>')
        out.append(text(90, cy + 76, "Piezo", 12, INK, "middle", 600))
    else:
        out.append(f'<rect x="46" y="{cy - 50}" width="96" height="100" rx="5" fill="#3a6fb5" stroke="#21477a"/>'
                   f'<circle cx="90" cy="{cy}" r="31" fill="#f2f2ee" stroke="#21477a" stroke-width="2"/>'
                   f'<line x1="90" x2="90" y1="{cy - 26}" y2="{cy - 5}" stroke="#21477a" stroke-width="4" stroke-linecap="round"/>')
        out.append(text(90, cy + 70, "Knob potentiometer", 12, INK, "middle", 600))
    for i, (name, to) in enumerate(legs):
        y = 62 * i + 62
        start = (142, cy + (i - (len(legs) - 1) / 2) * 24)
        out.append(wire_line([start, (240, y), (405, y)], WIRE_FILL["violet"], 18, dashed=True))
        out.append(text(250, y - 11, name, 12, MUTED, "start"))
        out.append(f'<rect x="405" y="{y - 15}" width="190" height="30" rx="4" fill="#fff4c2" stroke="#b08a00"/>')
        out.append(text(500, y + 5, to, 13, INK, "middle", 700))
    out.append("</svg>")
    return "".join(out)


# --- System map ---
def system_map(label):
    w, h = 900, 400
    out = [svg_open(w, h, label, 700)]
    out.append('<defs><marker id="sysarrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
               '<path d="M0 0 L10 5 L0 10 z" fill="#15181c"/></marker></defs>')

    def box(x, y, bw, bh, title, sub="", fill="#eef3fb", stroke="#0a4fb5"):
        res = f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
        res += text(x + bw / 2, y + bh / 2 + (-3 if sub else 5), title, 15, INK, "middle", 700)
        if sub:
            res += text(x + bw / 2, y + bh / 2 + 16, sub, 12, MUTED)
        return res

    def arrow(x1, y1, x2, y2, note, nx, ny, anchor="middle", both=False):
        start = ' marker-start="url(#sysarrow)"' if both else ""
        res = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#15181c" stroke-width="1.8" marker-end="url(#sysarrow)"{start}/>'
        return res + text(nx, ny, note, 12.5, INK, anchor, 500, halo="#ffffff")

    out.append(box(350, 150, 200, 100, "Arduino Uno", "reads, decides, plays", "#d9f0f2", "#075860"))
    out.append(box(30, 30, 210, 66, "8 piano keys", "buttons on a resistor ladder"))
    out.append(box(30, 165, 210, 66, "Knob", "10 kΩ potentiometer"))
    out.append(box(30, 300, 210, 66, "Power bank or USB", "5 V"))
    out.append(box(660, 30, 210, 66, "8 key LEDs", "one under each key"))
    out.append(box(660, 165, 210, 66, "LCD, 16×2", "4-bit wiring"))
    out.append(box(660, 300, 210, 66, "Piezo", "one tone at a time"))
    out.append(arrow(240, 70, 362, 150, "A0: one voltage per key", 300, 100, "start"))
    out.append(arrow(240, 198, 350, 198, "A1: position", 295, 188))
    out.append(arrow(240, 330, 362, 250, "5 V through the USB jack", 305, 304, "start"))
    out.append(arrow(538, 150, 660, 70, "8 pins, one per LED", 598, 100, "end"))
    out.append(arrow(550, 198, 660, 198, "6 signal pins", 605, 188))
    out.append(arrow(538, 250, 660, 330, "D8: tones", 590, 304, "end"))
    out.append("</svg>")
    return "".join(out)


# --- Ladder schematic ---
def ladder_schematic(label):
    w, h = 720, 500
    out = [svg_open(w, h, label, 560)]
    x = 130
    top, step = 60, 44

    def res_h(xc, y, note):
        r = f'<line x1="{xc}" x2="{xc}" y1="{y}" y2="{y + 11}" stroke="{INK}" stroke-width="1.6"/>'
        r += f'<rect x="{xc - 8}" y="{y + 11}" width="16" height="22" fill="#fff" stroke="{INK}" stroke-width="1.6"/>'
        r += f'<line x1="{xc}" x2="{xc}" y1="{y + 33}" y2="{y + 44}" stroke="{INK}" stroke-width="1.6"/>'
        r += text(xc - 15, y + 26, note, 11, MUTED, "end")
        return r

    out.append(text(x, top - 18, "5 V", 14, WIRE_FILL["red"], "middle", 700))
    bus = 450
    for k in range(1, 9):
        y = top + (k - 1) * step
        name = wiring.KEYS[k - 1]
        out.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="{INK}"/>')
        out.append(f'<line x1="{x}" x2="{bus - 74}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.6"/>')
        out.append(f'<circle cx="{bus - 74}" cy="{y}" r="3.2" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
        out.append(f'<line x1="{bus - 72}" x2="{bus - 38}" y1="{y}" y2="{y - 14}" stroke="{INK}" stroke-width="1.8"/>')
        out.append(f'<circle cx="{bus - 36}" cy="{y}" r="3.2" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
        out.append(f'<line x1="{bus - 33}" x2="{bus}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.6"/>')
        out.append(f'<circle cx="{bus}" cy="{y}" r="3.2" fill="{INK}"/>')
        out.append(text(bus - 170, y - 6, f"Key {k}: {name[0]} ({name[1]})", 12, INK, "middle", 500))
        out.append(res_h(x, y, "220 Ω"))
    y8 = top + 8 * step
    out.append(text(x, y8 + 17, "GND", 14, INK, "middle", 700))
    out.append(f'<line x1="{bus}" x2="{bus}" y1="{top}" y2="{top + 7 * step + 18}" stroke="{WIRE_FILL["orange"]}" stroke-width="2.4"/>')
    out.append(f'<line x1="{bus}" x2="{bus + 80}" y1="{top + 90}" y2="{top + 90}" stroke="{WIRE_FILL["orange"]}" stroke-width="2.4"/>')
    out.append(f'<rect x="{bus + 80}" y="{top + 73}" width="90" height="34" rx="4" fill="#fff4c2" stroke="#b08a00"/>')
    out.append(text(bus + 125, top + 95, "Uno A0", 14, INK, "middle", 700))
    res_y = top + 7 * step + 18
    out.append(res_h(bus, res_y, "10 kΩ"))
    out.append(text(bus, res_y + 62, "GND", 14, INK, "middle", 700))
    out.append(text(bus + 18, res_y + 26, "holds A0 at 0 V when no key is pressed", 12, MUTED, "start"))
    out.append("</svg>")
    return "".join(out)


# --- LED circuit, one key ---
def led_schematic(label):
    w, h = 720, 110
    out = [svg_open(w, h, label, 560)]
    y = 54
    out.append(f'<rect x="20" y="{y - 18}" width="120" height="36" rx="4" fill="#fff4c2" stroke="#b08a00"/>')
    out.append(text(80, y + 5, "Uno pin (D6…)", 13, INK, "middle", 700))
    out.append(f'<line x1="140" x2="270" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.8"/>')
    out.append(f'<polygon points="270,{y - 16} 270,{y + 16} 302,{y}" fill="{LED_FILL["red"]}" stroke="{INK}" stroke-width="1.6"/>')
    out.append(f'<line x1="302" x2="302" y1="{y - 16}" y2="{y + 16}" stroke="{INK}" stroke-width="2"/>')
    out.append(text(254, y - 22, "long leg", 12, MUTED, "end"))
    out.append(text(318, y - 22, "short leg", 12, MUTED, "start"))
    out.append(f'<line x1="302" x2="420" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.8"/>')
    out.append(f'<rect x="420" y="{y - 11}" width="62" height="22" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
    out.append(text(451, y + 30, "220 Ω", 12, MUTED))
    out.append(f'<line x1="482" x2="590" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.8"/>')
    out.append(text(622, y + 5, "GND", 14, INK, "middle", 700))
    out.append("</svg>")
    return "".join(out)


# --- A0 chart: where each key lands on the 0-1023 scale ---
def a0_chart(readings, label):
    w, h = 900, 150
    left, right, base = 24, 24, 90
    span = w - left - right
    sx = lambda v: left + v * span / 1024
    out = [svg_open(w, h, label, 700)]
    out.append(text(left, 22, "A0 reading (0 to 1023). Each key has its own window; the mark is its expected value.", 13, MUTED, "start"))
    for level in range(0, 9):
        lo = max(0, level * 128 - 64)
        hi = min(1024, level * 128 + 64) if level < 8 else 1024
        key = None if level == 0 else 8 - level
        fill = "#e7e8ea" if level == 0 else ("#d6e4f8" if level % 2 else "#eaf1fb")
        name = "none" if key is None else wiring.KEYS[key][0]
        value = 0 if key is None else readings[key + 1]
        out.append(f'<g><title>{escape(name)}: expected {value}, accepted {lo} to {hi - 1}</title>'
                   f'<rect x="{sx(lo):.1f}" y="{base - 40}" width="{sx(hi) - sx(lo) - 2:.1f}" height="40" fill="{fill}" rx="2"/>')
        out.append(text((sx(lo) + sx(hi)) / 2, base - 15, name, 13, INK, "middle", 600) + "</g>")
        out.append(f'<line x1="{sx(value):.1f}" x2="{sx(value):.1f}" y1="{base - 44}" y2="{base + 6}" stroke="#0a4fb5" stroke-width="2"/>')
        out.append(text(sx(value), base + 21, value, 12, INK, "middle" if 30 < value < 1000 else ("start" if value <= 30 else "end"), 500))
    for v in (64, 192, 320, 448, 576, 704, 832, 960):
        out.append(text(sx(v), base + 42, v, 10, MUTED))
    out.append("</svg>")
    return "".join(out)


# --- Part icons for the parts lists ---
def icon(kind, color=None):
    s = '<svg class="ic" viewBox="0 0 44 44" aria-hidden="true">'
    if kind == "button":
        s += '<rect x="9" y="9" width="26" height="26" rx="3" fill="#2b2f36"/><circle cx="22" cy="22" r="8" fill="#5a606a" stroke="#111"/>'
        for x, y in ((5, 13), (39, 13), (5, 31), (39, 31)):
            s += f'<rect x="{x - 3}" y="{y - 1.5}" width="6" height="3" fill="#a9aeb5"/>'
    elif kind == "led":
        s += f'<line x1="18" y1="28" x2="18" y2="42" stroke="#8a8f96" stroke-width="2"/><line x1="26" y1="28" x2="26" y2="38" stroke="#8a8f96" stroke-width="2"/>'
        s += f'<path d="M10 28 V18 a12 12 0 0 1 24 0 V28 z" fill="{LED_FILL[color]}" stroke="#20242a" stroke-opacity=".6"/>'
    elif kind == "res220" or kind == "res10k":
        bands = BANDS[220 if kind == "res220" else 10000]
        s += '<line x1="2" x2="42" y1="22" y2="22" stroke="#8a8f96" stroke-width="2"/><rect x="9" y="14" width="26" height="16" rx="8" fill="#d8bd8d" stroke="#8f7a50"/>'
        for x, c in zip((13, 18, 23, 30), bands):
            s += f'<rect x="{x}" y="14" width="3" height="16" fill="{c}"/>'
    elif kind == "wire":
        s += '<path d="M5 34 C14 6 30 38 39 10" fill="none" stroke="#2563d6" stroke-width="3.5" stroke-linecap="round"/>'
    elif kind == "fm":
        s += '<path d="M9 33 C16 8 28 36 35 11" fill="none" stroke="#7a3fc4" stroke-width="3.5"/><rect x="3" y="30" width="11" height="10" fill="#20242a"/><rect x="33" y="3" width="7" height="9" fill="#20242a"/><line x1="36.5" x2="36.5" y1="12" y2="15" stroke="#a9aeb5" stroke-width="2"/>'
    elif kind == "pot":
        s += '<rect x="7" y="7" width="30" height="30" rx="3" fill="#3a6fb5"/><circle cx="22" cy="22" r="10" fill="#f2f2ee"/><line x1="22" x2="22" y1="14" y2="22" stroke="#21477a" stroke-width="3"/>'
    elif kind == "lcd":
        s += '<rect x="3" y="11" width="38" height="22" rx="2" fill="#117a3f"/><rect x="8" y="16" width="28" height="12" fill="#2d5fd0"/>'
    elif kind == "piezo":
        s += '<circle cx="22" cy="22" r="16" fill="#20242a"/><circle cx="22" cy="22" r="5" fill="#5a606a"/>'
    elif kind == "uno":
        s += '<rect x="4" y="9" width="36" height="26" rx="3" fill="#0d7a86"/><rect x="2" y="13" width="9" height="8" fill="#b8bdc4"/><rect x="20" y="20" width="16" height="6" fill="#20242a"/>'
    elif kind == "usb":
        s += '<path d="M9 22 H30" stroke="#20242a" stroke-width="4"/><rect x="2" y="16" width="10" height="12" fill="#b8bdc4"/><rect x="30" y="15" width="11" height="14" fill="#6e737a"/>'
    elif kind == "bbfull" or kind == "bbhalf":
        width = 40 if kind == "bbfull" else 24
        x = 22 - width / 2
        s += f'<rect x="{x}" y="10" width="{width}" height="24" rx="2" fill="#f1efe7" stroke="#a7a395"/><line x1="{x}" x2="{x + width}" y1="22" y2="22" stroke="#c9c5b6" stroke-width="3"/>'
    elif kind == "bank":
        s += '<rect x="11" y="4" width="22" height="36" rx="4" fill="#3b4048"/><rect x="17" y="10" width="10" height="4" fill="#27a845"/>'
    elif kind == "print":
        s += '<path d="M6 30 L22 12 L38 30 z" fill="#2b2f36"/><rect x="13" y="28" width="18" height="6" fill="#fff" stroke="#2b2f36"/>'
    elif kind == "tool":
        s += '<path d="M13 40 L31 15" stroke="#6e737a" stroke-width="5" stroke-linecap="round"/><path d="M29 8 l9 6 -5 7 -9 -6 z" fill="#d92b25"/>'
    return s + "</svg>"
