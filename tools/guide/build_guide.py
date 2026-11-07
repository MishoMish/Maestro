#!/usr/bin/env python3
"""Builds the Маестро build guide from wiring.py, and refuses to if the wiring check fails.

    python3 tools/guide/build_guide.py

Writes docs/index.html, ready for GitHub Pages or any web host.
"""
import base64
import sys
from pathlib import Path

import draw
import wiring

ROOT = Path(__file__).resolve().parent.parent.parent
REPO = "https://github.com/MishoMish/Maestro"
BRANCH = "firmware"
PREVIEW = ROOT / "print" / "maestro_case" / "preview"


def image(name):
    return "data:image/png;base64," + base64.b64encode((PREVIEW / name).read_bytes()).decode()


STYLE = """
/* Layout: one column of numbered steps, like a printed assembly manual. Diagrams are the page's main content. */
:root {
  --paper: #f7f8fa; --sheet: #ffffff; --ink: #15181c; --muted: #5a626c; --line: #d5d9df;
  --blue: #0a4fb5; --blue-tint: #e6eefb; --go: #11703a; --go-tint: #e3f4e9; --warn: #8a5a00; --warn-tint: #fff3d0;
  --display: 'Archivo', 'Arial Narrow', sans-serif; --body: 'IBM Plex Sans', system-ui, sans-serif; --mono: 'IBM Plex Mono', ui-monospace, monospace;
  color-scheme: light;
}
body { background: var(--paper); color: var(--ink); font: 16px/1.55 var(--body); margin: 0; }
.wrap { max-width: 1040px; margin: 0 auto; padding-block: 28px 64px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 28px; }
.wrap > * { min-width: 0; }
h1, h2, h3 { font-family: var(--display); line-height: 1.08; margin: 0; text-wrap: balance; }
h1 { font-size: clamp(44px, 9vw, 86px); font-weight: 800; letter-spacing: -0.02em; }
h2 { font-size: clamp(28px, 5vw, 40px); font-weight: 800; }
h3 { font-size: 24px; font-weight: 700; }
p { margin: 0; max-width: 72ch; }
code, .mono { font-family: var(--mono); font-size: 0.92em; }
pre { font-family: var(--mono); font-size: 14px; background: #15181c; color: #f2f4f7; padding: 12px 14px; border-radius: 5px; margin: 0; overflow-x: auto; }
a { color: var(--blue); }
.stack { display: grid; gap: 14px; }
.stack > * { min-width: 0; }
.hero { display: grid; gap: 20px; grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr); align-items: center; background: var(--sheet); border: 1px solid var(--line); padding: 28px; border-radius: 8px; }
.hero img { width: 100%; display: block; }
.kicker { font: 700 14px var(--display); letter-spacing: .08em; text-transform: uppercase; color: var(--blue); }
.facts { display: flex; flex-wrap: wrap; gap: 8px 22px; font-size: 14px; color: var(--muted); margin: 0; padding: 0; list-style: none; }
.facts b { color: var(--ink); }
.sheet { background: var(--sheet); border: 1px solid var(--line); border-radius: 8px; padding: 24px; display: grid; gap: 16px; }
.sheet > * { min-width: 0; }
nav ol { margin: 0; padding-left: 22px; columns: 2; column-gap: 28px; }
nav li { margin-bottom: 3px; break-inside: avoid; }
.scroll { overflow-x: auto; }
.scroll svg:not(.ic) { display: block; width: 100%; height: auto; }
.fig { margin: 0; display: grid; gap: 8px; }
.fig > * { min-width: 0; }
.zoom { max-width: 620px; }
figcaption { color: var(--muted); font-size: 14px; max-width: 80ch; }
table { border-collapse: collapse; width: 100%; font-size: 15px; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: middle; }
th { font: 700 13px var(--display); letter-spacing: .04em; text-transform: uppercase; color: var(--muted); border-bottom: 2px solid var(--ink); }
.ic { width: 34px; height: 34px; display: block; flex: none; }
.step { background: var(--sheet); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.step-head { display: flex; gap: 16px; align-items: center; padding: 16px 24px; border-bottom: 1px solid var(--line); }
.num { font: 800 54px/1 var(--display); color: var(--blue); min-width: 62px; }
.step-body { padding: 20px 24px 24px; display: grid; gap: 16px; }
.step-body > * { min-width: 0; }
.parts { background: var(--blue-tint); border-radius: 6px; padding: 12px 14px; display: flex; flex-wrap: wrap; gap: 10px 20px; align-items: center; }
.parts h4 { margin: 0; font: 700 13px var(--display); letter-spacing: .06em; text-transform: uppercase; color: var(--blue); width: 100%; }
.part { display: flex; gap: 8px; align-items: center; font-size: 14px; line-height: 1.2; }
.part b { font: 800 19px var(--display); }
ol.do { margin: 0; padding-left: 22px; display: grid; gap: 7px; max-width: 76ch; }
.note { border-radius: 6px; padding: 11px 14px; font-size: 15px; }
.note b { font-family: var(--display); letter-spacing: .03em; }
.warn { background: var(--warn-tint); color: #4f3500; }
.test { background: var(--go-tint); color: #0a3d20; display: grid; gap: 8px; }
.test > * { min-width: 0; }
.test ul { margin: 0; padding-left: 20px; }
.part-title { display: grid; gap: 6px; padding-top: 14px; }
footer { color: var(--muted); font-size: 14px; display: grid; gap: 6px; }
:focus-visible { outline: 3px solid var(--blue); outline-offset: 2px; }
@media (max-width: 720px) {
  .hero { grid-template-columns: minmax(0, 1fr); padding: 18px; }
  .sheet, .step-body { padding: 16px; }
  .step-head { padding: 12px 16px; }
  .num { font-size: 42px; min-width: 46px; }
  nav ol { columns: 1; }
  .hide-narrow { display: none; }
}
"""


def parts_box(items):
    cells = "".join(f'<div class="part">{icon}<span><b>{qty}×</b> {name}</span></div>' for icon, qty, name in items)
    return f'<div class="parts"><h4>You need for this step</h4>{cells}</div>'


def step(number, title, parts, actions, figures="", warn=None, test=None):
    body = parts_box(parts) if parts else ""
    body += '<ol class="do">' + "".join(f"<li>{a}</li>" for a in actions) + "</ol>"
    if warn:
        body += f'<div class="note warn"><b>Careful:</b> {warn}</div>'
    body += figures
    if test:
        body += f'<div class="note test"><b>TEST NOW</b>{test}</div>'
    return (f'<section class="step" id="step-{number}"><div class="step-head"><div class="num">{number}</div><h3>{title}</h3></div>'
            f'<div class="step-body">{body}</div></section>')


def table(headers, rows, cls=""):
    head = "".join(f"<th>{h}</th>" for h in headers)
    rows_html = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{rows_html}</tbody></table></div>'


def overview(step_number, label, caption, **kw):
    return draw.figure(draw.board_figure("F", step_number, 1, 63, 14.6, label, minw=760, **kw), caption)


def zoom(step_number, label, caption, notes=None, c1=14, **kw):
    return draw.figure(draw.board_figure("F", step_number, 1, c1, 40, label, notes=notes, top_margin=70, minw=480, **kw), caption, "zoom")


def half(step_number, label, caption, notes=None):
    return draw.figure(draw.board_figure("H", step_number, 1, 30, 25, label, notes=notes, top_margin=108, tag_rotate=True, minw=640), caption)


def build(readings):
    ic = draw.icon
    out = []
    out.append(f"""
<header class="hero">
  <div class="stack">
    <div class="kicker">Build guide</div>
    <h1>Маестро</h1>
    <p>A standalone trainer for musical hearing and memory. It plays a melody by light, sound or both, and you repeat it on 8 piano keys. This guide takes you from a box of parts to a working device, one step at a time.</p>
    <ul class="facts"><li><b>12</b> wiring steps</li><li><b>0</b> soldering</li><li><b>1</b> Arduino Uno</li><li><b>Keys:</b> До Ре Ми Фа Сол Ла Си До</li></ul>
  </div>
  <img src="{image('assembled.png')}" alt="Computer render of the finished Маестро: a black sloped box with 8 white keys at the front and an LCD, speaker grille and knob on the sloped panel at the back.">
</header>
<nav class="sheet" aria-label="Contents"><h3>Contents</h3><ol>
  <li><a href="#parts">Parts: what's in the kit, what to buy</a></li>
  <li><a href="#how">How it works</a></li>
  <li><a href="#read">How to read the diagrams</a></li>
  <li><a href="#a">Part A: the key bed, steps 1–6</a></li>
  <li><a href="#b">Part B: power and the Uno, steps 7–9</a></li>
  <li><a href="#c">Part C: the panel, steps 10–12</a></li>
  <li><a href="#software">Upload the game</a></li>
  <li><a href="#case">Put it in the case</a></li>
  <li><a href="#help">If something doesn't work</a></li>
  <li><a href="#pins">Full pin table</a></li>
</ol></nav>""")

    kit = [
        (ic("uno"), "Arduino Uno", "1", "1"), (ic("usb"), "USB cable (A to B)", "1", "1"),
        (ic("button"), "Pushbuttons", "8", "10"),
        (ic("led", "red"), "LED, red", "2", "8"), (ic("led", "yellow"), "LED, yellow", "2", "8"),
        (ic("led", "green"), "LED, green", "2", "8"), (ic("led", "blue"), "LED, blue", "1", "3"),
        (ic("led", "white"), "LED, bright white", "1", "1"),
        (ic("res220"), "Resistor, 220 Ω (red, red, brown)", "17", "20"),
        (ic("res10k"), "Resistor, 10 kΩ (brown, black, orange)", "1", "20"),
        (ic("pot"), "Potentiometer, 10 kΩ", "2", "3"), (ic("lcd"), "LCD, 16×2, with its pins soldered on", "1", "1"),
        (ic("piezo"), "Piezo capsule", "1", "1"), (ic("wire"), "Solid-core jumper wires", "25", "70"),
    ]
    buy = [
        (ic("bbfull"), "Full-size breadboard, 830 holes", "1", "Sits under the keys. The kit's 400-hole board has 30 columns and the keys need 63."),
        (ic("bbhalf"), "Half-size breadboard, 400 holes", "1", "Holds the power rails and contrast pot. Skip this if you can take the kit's own 400-hole board off its base. Leave it on if the kit is borrowed."),
        (ic("fm"), "Female-to-male jumper wires, about 20 cm", "17", "They reach from the panel to the boards: LCD 12, piezo 2, knob 3. A pack of 20 or 40 is typical."),
        (ic("bank"), "USB power bank", "1", "To run it without a computer. Some banks switch off under a light load, so test yours (<a href='#software'>below</a>)."),
    ]
    out.append(f"""
<section class="sheet" id="parts"><h2>Parts</h2>
<p>This guide is written for the official <b>Arduino Starter Kit</b> (K000007), the one with the projects book and 16×2 LCD. Use the kit's parts wherever you can. You only need to buy what the second table lists.</p>
<h3>From the kit</h3>
{table(["", "Part", "You use", "Kit has"], kit)}
<h3>Buy these</h3>
{table(["", "Part", "How many", "Why"], buy)}
<h3>For the case</h3>
<p>You need a 3D printer, about 230 g of black PETG and up to 20 g of white filament for the keys. The <a href="#case">case section</a> has the details. The electronics work fine without a case, so you can test everything first.</p>
<h3>Handy tools</h3>
<p>Small pliers for bending leads and a small screwdriver for the contrast pot and for opening the case's clips. A multimeter helps with finding faults, but you don't strictly need one.</p>
<div class="note warn"><b>Check your kit first.</b> The "Kit has" counts come from two retailers' listings (<a href="https://botland.store/arduino-education-original-kits/4796-arduino-starterkit-k000007-the-official-starter-set-with-arduino-uno-a000066-7630049200081.html">Botland</a>, <a href="https://rapidonline.com/arduino-k000007-starter-kit-including-uno-board-73-4642">Rapid Online</a>), not from Arduino itself. Kit versions can differ, so count your parts before you buy anything.</div>
</section>""")

    out.append(f"""
<section class="sheet" id="how"><h2>How it works</h2>
<p>A 16×2 LCD, 8 LEDs, a piezo, a knob and 8 keys would need more pins than an Uno has if every key had its own. The trick is that all 8 keys share one pin.</p>
{draw.figure(draw.system_map("Block diagram. Keys, knob and power feed into the Arduino Uno. The Uno drives the key LEDs, LCD and piezo."), "What connects to what. The Uno has 20 pins and this design uses 17.")}
<h3>The resistor ladder</h3>
<p>The 8 keys sit along a chain of resistors between 5 V and GND. Each key connects a different point on the chain to pin A0, so each one gives a different voltage, and the Uno works out which key it is from that voltage.</p>
{draw.figure(draw.ladder_schematic("Schematic. Eight 220 ohm resistors in series from 5 volts to ground. Each junction connects through a key to a shared line going to Uno pin A0, with a 10 kilohm resistor from that line to ground."), "The whole keyboard. Pressing a key connects one point on the chain to A0.")}
{draw.figure(draw.a0_chart(readings, "Chart of the A0 reading for each key on a 0 to 1023 scale. До reads 1023, Ре 878, Ми 742, Фа 614, Сол 489, Ла 368, Си 247, До prime 125, and no key reads 0."), f"The reading for each key, worked out from this exact wiring: {', '.join(str(readings[k]) for k in range(1, 9))}. Real values land nearby. Each key has a wide window, so ordinary ±5% resistors are fine. Pressing two keys together can read as a third key, so the game treats one key at a time.")}
<h3>Each LED</h3>
<p>Each LED has its own Uno pin and its own resistor, which limits the current so that neither the LED nor the pin is damaged.</p>
{draw.figure(draw.led_schematic("Schematic. Uno pin to LED long leg, LED short leg to a 220 ohm resistor, resistor to ground."), "One of the 8 LED circuits. They're all the same.")}
</section>""")

    keys_rows = []
    for k in range(1, 9):
        n = wiring.key_n(k)
        name = wiring.KEYS[k - 1]
        keys_rows.append([k, f"{name[0]} ({name[1]})", name[2], f"{n - 1} and {n + 1}", n, n + 2, f"{n - 1}", f"{n + 1}", name[3]])
    out.append(f"""
<section class="sheet" id="read"><h2>How to read the diagrams</h2>
<p>Every diagram follows the same rules, so you always know what to do next:</p>
<ol class="do">
  <li><b>Full colour is new.</b> Faded parts are from earlier steps and are already on your board.</li>
  <li><b>Each hole has a name.</b> <code>c4</code> means row c, column 4.</li>
  <li><b>Zoomed views show key 1.</b> Then the overview shows all 8. Each key repeats the same pattern 8 columns further along.</li>
  <li><b>Labels at the edge of a board</b>, such as <code>D6</code>, tell you where that wire's other end goes.</li>
</ol>
<div class="note warn"><b>Trust the position, not the print.</b> In this guide, <b>row a is the row nearest the back</b>, and <b>column 1 is on the far left</b> as you face the board from the front. Some breadboards are printed the other way round. If yours is, ignore its printed letters and numbers and count from these edges. The same applies to the rails: use their position, whatever colour they're printed in.</div>
<p>Real boards group their rail holes in fives, so a rail hole won't always line up exactly with a column. Any hole in the correct rail works.</p>
<h3>Where each key goes</h3>
<p>Keep this table handy for steps 2 to 6. For key <i>k</i>, the base column is <i>n</i> = 8<i>k</i> − 4.</p>
{table(["Key", "Name", "LED", "Button columns", "LED long leg (row c)", "LED short leg (row c)", "Ladder starts (row h)", "A0 wire (row g)", "Uno pin"], keys_rows)}
<div class="note warn"><b>Power off while wiring.</b> Unplug the USB cable whenever you add or move a wire, and plug it back in only for a test.</div>
</section>""")

    out.append('<div class="part-title" id="a"><div class="kicker">Part A</div><h2>The key bed</h2><p>All of this goes on the full-size breadboard, which ends up under the keys. Everything must lie flat, under 3 mm tall, because the keys sit just 5 mm above the board. So keep leads short, press wires down, and use the kit\'s solid-core wires here, because tall plug ends won\'t fit.</p></div>')

    out.append(step(1, "Set up the board", [(ic("bbfull"), 1, "full-size breadboard"), (ic("wire"), 1, "solid wire")], [
        "Put the board in front of you with column 1 on the left.",
        "Note the four rails, from back to front: <b>5V</b>, <b>GND</b>, then after the holes <b>A0 bus</b> and <b>GND</b>.",
        "Connect the two GND rails with one long wire around the left end of the board, from the back GND rail to the front GND rail.",
    ], overview(1, "Full breadboard from above with the four rails labelled and one wire joining the back GND rail to the front GND rail at the left end.", "The board, seen from above. The back is at the top of the picture."),
        warn="On many full-size boards each rail is split in the middle, shown by a gap in the printed line. If yours is, bridge the gap in all four rails with a short wire. This is a common cause of \"half the keys don't work\"."))

    out.append(step(2, "Add the 8 buttons", [(ic("button"), 8, "pushbuttons")], [
        "Press each button across the centre channel, with its legs in columns <b>n−1</b> and <b>n+1</b>, in rows <b>e</b> and <b>f</b>. Key 1 goes in columns 3 and 5.",
        "If a button won't sit across the channel, turn it 90°. It only fits one way round, and that's the right one.",
    ], zoom(2, "Close-up of the first button across the channel, with legs in columns 3 and 5, rows e and f. A second button starts at column 11.", "Key 1 in close-up. The button's legs are in e3, f3, e5 and f5.",
            notes=[(3, "e", "e3", -44, -18, "end"), (5, "f", "f5", 44, 22, "start")]) +
        overview(2, "All eight buttons across the channel, 8 columns apart.", "All 8 buttons. They're exactly one key's width apart.")))

    colours = ", ".join(f"key {k}: {wiring.KEYS[k - 1][2]}" for k in range(1, 9))
    out.append(step(3, "Add the 8 LEDs", [(ic("led", "red"), 2, "red"), (ic("led", "yellow"), 2, "yellow"), (ic("led", "green"), 2, "green"), (ic("led", "blue"), 1, "blue"), (ic("led", "white"), 1, "white")], [
        f"Lay out your LEDs in key order: {colours}.",
        "Bend each LED's legs out so they're 5 mm apart, which is 2 columns.",
        "Put the <b>long leg (+)</b> in column <b>n</b> and the <b>short leg (−)</b> in column <b>n+2</b>, both in row <b>c</b>. Key 1 goes in c4 and c6.",
    ], zoom(3, "Close-up of the first LED behind the button, with its long leg in c4 and short leg in c6.", "Key 1: the long leg is on the left in c4, and the short leg in c6.",
            notes=[(4, "c", "long leg, c4", -60, -34, "end"), (6, "c", "short leg, c6", 60, -34, "start")]) +
        overview(3, "All eight LEDs in row c in key order: red, yellow, green, blue, white, yellow, green, red.", "The colours run symmetrically, with red at both ends."),
        warn="An LED in backwards won't light, but it won't be harmed either. If one stays dark in the test, turn it round."))

    out.append(step(4, "Add the LED resistors", [(ic("res220"), 8, "220 Ω resistors")], [
        "Connect column <b>n+2</b>, row <b>b</b> to the <b>back GND rail</b>, for each key. Key 1 uses b6.",
        "Bend the leads so that each resistor lies flat.",
    ], zoom(4, "Close-up of a 220 ohm resistor from hole b6 up to the back GND rail.", "Key 1: b6 to the back GND rail. b6 is in the same column as the LED's short leg, so they're connected.",
            notes=[(6, "b", "b6", 60, 4, "start")]) +
        overview(4, "Eight resistors, each from row b next to an LED up to the back GND rail.", "All 8 LED resistors.")))

    out.append(step(5, "Build the resistor ladder", [(ic("res220"), 8, "220 Ω resistors")], [
        "Connect the keys in a chain along the front half. For keys 1 to 7, one resistor goes from column <b>n−1</b>, row <b>h</b> to column <b>n+7</b>, row <b>i</b>. The first runs from h3 to i11, the next from h11 to i19.",
        "For key 8, the last resistor goes from <b>j59</b> to the <b>front GND rail</b>, near column 63.",
        "Trim nothing: bend the leads to fit, and lay the resistors flat. Don't let the bare leads touch each other.",
    ], zoom(5, "Close-up of a resistor from h3 to i11, with the next one starting at h11.", "The chain's first link. Rows h and i are connected to each other, so i11 and h11 are the same point, and each leg still gets its own hole.",
            notes=[(3, "h", "start: h3", -6, 96, "middle"), (11, "i", "end: i11", -30, 66, "middle"), (11, "h", "next starts: h11", 94, 76, "middle")]) +
        overview(5, "A chain of eight resistors across the front half of the board, ending at the front GND rail.", "The whole ladder: 7 links between keys, then one from key 8 down to GND.")))

    out.append(step(6, "Connect the keys to the A0 bus", [(ic("wire"), 9, "solid wires"), (ic("res10k"), 1, "10 kΩ resistor")], [
        "Connect the top of the chain to 5 V: one wire from <b>a3</b> to the <b>back 5V rail</b>.",
        "Connect each key to the A0 bus: one wire from column <b>n+1</b>, row <b>g</b> to the <b>front A0 rail</b>, 8 in total. Key 1 uses g5.",
        "Add the pull-down: the <b>10 kΩ</b> resistor from the <b>front A0 rail</b> to the <b>front GND rail</b>, at the left end. Lay it flat, for example from column 1 on one rail to column 5 on the other.",
    ], zoom(6, "Close-up: a wire from a3 to the back 5 volt rail, a wire from g5 to the A0 bus, and the 10 kilohm resistor between the A0 bus and the front GND rail.", "Key 1 in close-up, with the three new kinds of connection.",
            notes=[(3, "a", "a3 to 5V rail", -90, 10, "middle"), (5, "g", "g5 to A0 bus", 90, 10, "start")]) +
        overview(6, "The finished key bed, with eight orange wires going to the A0 bus.", "The finished key bed. It has no connection to the Uno yet."),
        warn="The 10 kΩ resistor has <b>brown, black, orange</b> bands, and the 220 Ω ones have <b>red, red, brown</b>. They look alike, so check before you press it in."))

    out.append('<div class="part-title" id="b"><div class="kicker">Part B</div><h2>Power and the Uno</h2><p>The half-size breadboard shares 5 V and GND with everything else. Keep it next to the Uno.</p></div>')

    out.append(step(7, "Bring in the power", [(ic("uno"), 1, "Uno"), (ic("bbhalf"), 1, "half-size breadboard"), (ic("wire"), 4, "solid wires")], [
        "Connect Uno <b>5V</b> to the half board's <b>5V rail</b>, and Uno <b>GND</b> to its <b>GND rail</b>.",
        "Connect the half board's 5V rail to the key bed's <b>back 5V rail</b>, and its GND rail to the key bed's <b>back GND rail</b>.",
    ], draw.figure(draw.uno_figure({"5V": "to half board 5V rail", "GND": "to half board GND rail"}, "Arduino Uno with the 5V and GND pins highlighted."), "Use either of the two GND pins next to 5V.") +
       half(7, "Half breadboard with its 5 volt and GND rails wired to the Uno and to the key bed.", "The half board's two rails, in and out.") +
       overview(7, "The key bed with 5 volts and ground arriving on its back rails at the left end.", "Where the power arrives on the key bed: 5V in and GND in, at the left end."),
        warn="Check these wires twice. 5V connected straight to GND is the one mistake in this guide that can cause real harm."))

    out.append(step(8, "Add the contrast pot and backlight resistor", [(ic("pot"), 1, "potentiometer"), (ic("wire"), 2, "solid wires"), (ic("res220"), 1, "220 Ω resistor")], [
        "Press the potentiometer into the half board so that its three legs are in <b>three different columns</b>. The diagram uses columns 8, 10 and 12. If your pot's legs are closer together, use the columns they fit and adjust the next two instructions to match.",
        "Connect one outer leg's column to the <b>5V rail</b> and the other outer leg's column to the <b>GND rail</b>.",
        "Add the backlight resistor: <b>220 Ω</b> from the <b>5V rail</b> to hole <b>c20</b>.",
    ], half(8, "Half breadboard with a potentiometer, two wires to the rails, and a resistor from the 5 volt rail to hole c20.", "The middle leg's column gets LCD V0 and column 20 gets LCD A in step 10.",
            notes=[(10, "a", "V0 goes here", 0, -14, "middle"), (20, "a", "A goes here", 34, -14, "start")])))

    wires_table = [[k, f"{wiring.KEYS[k - 1][0]} ({wiring.KEYS[k - 1][2]})", f"a{wiring.key_n(k)}", wiring.KEYS[k - 1][3]] for k in range(1, 9)]
    highlight = {wiring.KEYS[k - 1][3]: f"{wiring.KEYS[k - 1][0]}" for k in range(1, 9)}
    highlight["A0"] = "A0 bus"
    out.append(step(9, "Connect the key bed to the Uno", [(ic("wire"), 9, "long solid wires")], [
        "Connect each LED to its Uno pin: from column <b>n</b>, row <b>a</b> to the pin in the table below.",
        "Connect the <b>A0 bus</b> to Uno pin <b>A0</b>, from the left end of the front A0 rail.",
    ], table(["Key", "Name", "From hole", "To Uno pin"], wires_table) +
       draw.figure(draw.uno_figure(highlight, "Arduino Uno with the eight LED pins and A0 highlighted."), "The 9 Uno pins for this step. They aren't in order, so follow the labels. D8 stays free for the piezo.") +
       overview(9, "The key bed with an LED wire leaving each key, each labelled with its Uno pin, and the A0 bus labelled Uno A0.", "Each wire's label says where its other end goes. Wire colours are only a guide here."),
        warn="Use the kit's longest wires. If they don't reach once it's all in the case, buy some 20 cm male-to-male wires, but only for the longest runs and only if the plug end stays clear of the keys. Check this before you close the box.",
        test="""<p>Your first real test. The Uno needs the code from <a href="#software">Upload the game</a>. Plug in USB and run:</p><pre>./maestro hwtest</pre><ul>
        <li>Every LED lights once, in key order.</li>
        <li>With no key pressed, <code>A0</code> stays near 0.</li>
        <li>Pressing a key lights its LED, and your terminal shows its name, with <code>A0</code> near the values in the chart above. There's no sound or LCD text yet.</li></ul>
        <p>Fix anything here before moving on. It's much easier now.</p>"""))

    out.append('<div class="part-title" id="c"><div class="kicker">Part C</div><h2>The panel</h2><p>The LCD, piezo and knob sit on the sloped panel, so they connect with female-to-male wires, which also let you open the box. The female end goes on the part, and the male end goes into the Uno or half board.</p></div>')

    lcd_rows = []
    for number, name, to in wiring.LCD_PINS:
        if to is None:
            lcd_rows.append([number, name, "<span style='color:var(--muted)'>Nothing</span>", "<span style='color:var(--muted)'>Leave empty</span>"])
        else:
            where = {"GND rail": "Half board GND rail", "5V rail": "Half board 5V rail", "Contrast pot, middle leg": "Half board, a10 (pot's middle leg)", "Backlight resistor": "Half board, a20 (backlight resistor)"}.get(to, f"Uno {to}")
            lcd_rows.append([number, name, where, {"V0": "Sets contrast", "RS": "Command or text", "E": "Clocks in data", "VSS": "Ground", "VDD": "Power", "RW": "Ground: write only", "A": "Backlight +", "K": "Backlight −"}.get(name, "Data")])
    out.append(step(10, "Connect the LCD", [(ic("lcd"), 1, "LCD"), (ic("fm"), 12, "female-to-male wires")], [
        "Unplug USB, then connect the LCD's pins as in the table. Pin 1 is at the end marked on your LCD's board, usually labelled VSS or 1. Pins 7 to 10 stay empty.",
    ], draw.figure(draw.lcd_figure("LCD module with its sixteen pins labelled. Pins 7 to 10 are unused."), "The LCD's 16 pins. Red pins are power, violet pins are signals, and grey pins stay empty.") +
       table(["Pin", "Name", "Goes to", "What it does"], lcd_rows) +
       draw.figure(draw.uno_figure({"D12": "RS", "D11": "E", "D5": "LCD D4", "D4": "LCD D5", "D3": "LCD D6", "D2": "LCD D7"}, "Arduino Uno with the six LCD signal pins highlighted."), "The 6 signal wires. The D4 to D7 wires run in reverse order compared with the Uno pins, so go carefully.") +
       half(10, "Half breadboard with six LCD wires: VSS, RW and K on the GND rail, VDD on the 5 volt rail, V0 in column 10 and A in column 20.", "The other 6 LCD wires, on the half board."),
        test="""<p>Run <code>./maestro hwtest</code> again, and turn the contrast pot slowly with a small screwdriver until text appears. If you see only a row of blocks or nothing, it's almost always the contrast, or the RS and E wires.</p>"""))

    out.append(step(11, "Connect the piezo", [(ic("piezo"), 1, "piezo"), (ic("fm"), 2, "female-to-male wires")], [
        "Connect one leg to Uno <b>D8</b>.",
        "Connect the other leg to the half board's <b>GND rail</b>.",
    ], draw.figure(draw.legs_figure("piezo", [("One leg", "Uno D8"), ("Other leg", "Half board GND rail")], "A piezo with one leg wired to Uno D8 and the other to ground.", 460), "The piezo needs only two wires."),
        test="<p>Run <code>./maestro hwtest</code>. Each key now also plays its note, from low До to high До.</p>"))

    out.append(step(12, "Connect the knob", [(ic("pot"), 1, "potentiometer"), (ic("fm"), 3, "female-to-male wires")], [
        "Connect one outer leg to the half board's <b>5V rail</b>.",
        "Connect the other outer leg to its <b>GND rail</b>.",
        "Connect the <b>middle leg</b> to Uno <b>A1</b>.",
    ], draw.figure(draw.legs_figure("knob", [("Outer leg", "Half board 5V rail"), ("Middle leg", "Uno A1"), ("Outer leg", "Half board GND rail")], "A potentiometer with outer legs on 5 volts and ground, and the middle leg on Uno A1.", 460), "Swapping the two outer legs only reverses the knob's direction."),
        test="""<p>Run <code>./maestro hwtest</code> and turn the knob from end to end. <code>tick=</code> should count from 1 to 7. If it counts down, set <code>KNOB_REVERSED</code> to true in <code>code/src/config.h</code>, or swap the outer legs.</p>"""))

    out.append(f"""
<section class="sheet" id="software"><h2>Upload the game</h2>
<p>You need a computer with <a href="https://www.python.org/">Python 3</a> and <a href="https://platformio.org/install/ide?install=vscode">PlatformIO</a>, which is easiest to get as a VS Code extension. Then get the code:</p>
<pre>git clone -b {BRANCH} {REPO}.git
cd Maestro
./maestro</pre>
<p>A menu opens. Choose these in order, with the Uno connected by USB:</p>
<ol class="do">
  <li><b>Check that this computer is ready.</b> It tells you exactly what to fix.</li>
  <li><b>Allow uploads to the Uno</b> if the check asks for it. This is a one-time step on Linux.</li>
  <li><b>Test the Uno's own chip</b>, if you like, before wiring anything. It plays the real game with a scripted player for about 20 minutes, then puts the game back.</li>
  <li><b>Test the wiring.</b> This is the test used in the steps above.</li>
  <li><b>Upload the game.</b></li>
</ol>
<p>The code has been run on a real Uno and tested extensively in a simulator. The commands have been tried on Linux so far. Windows users should run <code>python tools\\maestro_cli.py</code> in place of <code>./maestro</code>.</p>
<h3>Test the power bank</h3>
<p>Run the device from your bank, untouched, for 10 minutes. Some banks switch off when too little current is drawn. If yours does, try another one.</p>
</section>
<section class="sheet" id="case"><h2>Put it in the case</h2>
{draw.figure(f'<img src="{image("exploded.png")}" alt="Exploded computer render of the case: box, key comb, deck plate, panel, knob, trays and boards." style="width:100%;display:block">', "How the parts fit together. Nothing is glued, screwed or soldered, and panels snap in, so you can always reopen it.")}
<p>Ready-to-print files and slicer settings are in the <a href="{REPO}/tree/{BRANCH}/print/maestro_case">project's print folder</a>. Print the test pieces first, to check key travel and LCD fit against your actual parts.</p>
{table(["Part", "Colour", "Print time"], [["Test pieces", "Black", "About 1 h"], ["Uno tray and lid", "Black", "About 2.5 h"], ["Breadboard tray", "Black", "About 1 h"], ["Box", "Black", "7–9 h"], ["Key-bed tray", "Black", "About 1.5 h"], ["Deck plate", "Black", "About 1.5 h"], ["Control panel", "Black", "About 2.5 h"], ["Pot holder, knob", "Black", "About 40 min"], ["Key comb", "White", "About 2 h"]])}
<h3>Assembly order</h3>
<ol class="do">
  <li>Put the Uno on the tray's pegs, slide the breadboard tray onto the dovetails, and put the half board in it.</li>
  <li>Drop both trays into the back of the box. The USB jack lines up with the hole in the left wall.</li>
  <li>Put the full board in the key-bed tray, and drop it into the front of the box, pushed against the front wall.</li>
  <li>Press the key comb's 3 pegs into the deck plate, then snap the plate in with its 4 hooks.</li>
  <li>Press the LCD into the panel until the clips snap over its board, and press the piezo into its cup.</li>
  <li>Slide the knob pot into its holder, push the holder into the panel's square socket, and put the knob on.</li>
  <li>Connect the female-to-male wires, then snap the panel in.</li>
  <li>Run <code>./maestro hwtest</code> once more, because wires can shift when you close the box. Then run <code>./maestro upload</code>.</li>
</ol>
</section>
<section class="sheet" id="help"><h2>If something doesn't work</h2>
{table(["Problem", "Most likely cause"], [
    ["<code>A0</code> wanders even with no key pressed", "The A0 wire or the 10 kΩ pull-down is loose."],
    ["Half the keys read wrongly", "A split in a rail (step 1), or a missing ladder link (step 5)."],
    ["One key reads as its neighbour", "That key's A0 wire or a ladder link is in the wrong hole."],
    ["All keys read about 1023", "The GND link (step 1) or key 8's last resistor (step 5) is missing."],
    ["A key's button does nothing", "It's turned 90°, or its A0 wire is loose."],
    ["One LED stays dark", "It's in backwards, or its resistor or Uno wire is loose."],
    ["LCD shows blocks or nothing", "Turn the contrast pot, then check the RS and E wires."],
    ["LCD shows random characters", "The D4 to D7 wires are swapped (step 10)."],
    ["No sound", "Check the piezo wires, D8 and GND."],
    ["Menu moves the wrong way", "Set <code>KNOB_REVERSED</code> to true in <code>code/src/config.h</code>."],
    ["Upload fails", "Run <code>./maestro check</code>, try another USB cable, and close any serial monitor. Nothing may be on pins D0 and D1."],
    ["Keys click by themselves or never click", "The key-bed height. See <code>btn_h</code> in the case's guide."],
])}
</section>""")

    pin_rows = [["A0", "Key ladder (A0 bus)"], ["A1", "Knob, middle leg"]]
    pin_rows += [[wiring.KEYS[k][3], f"LED, key {k + 1}: {wiring.KEYS[k][0]} ({wiring.KEYS[k][2]})"] for k in range(8)]
    pin_rows += [["D8", "Piezo"], ["D12", "LCD RS"], ["D11", "LCD E"], ["D5", "LCD D4"], ["D4", "LCD D5"], ["D3", "LCD D6"], ["D2", "LCD D7"], ["5V, GND", "Half board rails"], ["A5", "Free: left unconnected, used for randomness"], ["D0, D1", "Free: USB serial, used for uploads"]]
    out.append(f"""
<section class="sheet" id="pins"><h2>Full pin table</h2>
{table(["Uno pin", "Connected to"], pin_rows)}
</section>
<footer>
  <p><b>Маестро</b> is a university course project by Богомил Стоянов and Михаил Доброславски. Code and case files: <a href="{REPO}">{REPO.replace("https://", "")}</a>.</p>
  <p>The diagrams are generated from the project's wiring list, which is checked electrically each time this guide is built. The pictures of the case are computer renders.</p>
  <p>Arduino is a trademark of Arduino SA. This is an independent project, not made or endorsed by Arduino.</p>
</footer>""")
    return "\n".join(out)


def main():
    problems, readings = wiring.check()
    if problems:
        print("The wiring check failed, so the guide was not built:\n" + "\n".join(problems), file=sys.stderr)
        return 1
    head = ('<title>Маестро Build Guide</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            '<meta name="description" content="Step-by-step wiring guide for Маестро, an Arduino Uno trainer for musical hearing and memory.">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            'family=Archivo:wght@700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">\n'
            f"<style>{STYLE}</style>\n")
    body = f'<main class="wrap">\n{build(readings)}\n</main>'
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(
        f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n{head}</head>\n<body>\n{body}\n</body>\n</html>\n',
        encoding="utf-8")
    if len(sys.argv) > 1:      # a page fragment for hosts that add their own document skeleton
        Path(sys.argv[1]).write_text(head + body + "\n", encoding="utf-8")
    print(f"Wiring is correct. Wrote {docs / 'index.html'} ({(docs / 'index.html').stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
