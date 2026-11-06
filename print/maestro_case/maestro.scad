// =====================================================================
//  maestro.scad  --  "Маестро" music trainer console
//  Uses the reusable trays from uno_kit.scad (keep both files together).
//
//  Coordinates: X = left/right (keys run along X), Y = front(0) -> back,
//  Z = up.  Pick a part below and press F6, then F7 to export the STL.
// =====================================================================
use <uno_kit.scad>

part = "assembly"; // [assembly, box, deck_plate, key_comb, panel, knob, pot_holder, keybed_tray, test_key_plate, test_key, test_lcd]

/* [MEASURE THESE - parts you have] */
btn_h    = 5.0;    // tactile button height on the breadboard, incl. the stem
fbb_l    = 165.0;  // full breadboard length
fbb_w    = 55.0;   // full breadboard width
fbb_h    = 8.5;    // full breadboard height
led_h    = 8.6;    // 5 mm LED height above the breadboard

/* [LCD 16x2 module] */
lcd_pcb     = [80.0, 36.0];
lcd_holes   = [75.0, 31.0];   // hole centre spacing
lcd_hole_d  = 3.0;
lcd_bezel   = [71.2, 24.2];   // black metal frame around the glass
lcd_bezel_h = 7.0;            // frame height above the PCB
lcd_bezel_off = [0, 0];       // if the frame is not centred on the PCB

/* [Piezo (kit: Murata PKM17EPP, 17 mm)] */
piezo_d = 17.0;
piezo_h = 7.0;

/* [Potentiometer + knob] */
pot_body   = [10.0, 10.0, 5.0];  // kit trimmer is ~10x10x5
knob_mode  = "blade";            // [blade, socket]
blade      = [2.4, 0.9, 1.5];    // width, thickness, depth (fits slot / cross rotors)
socket_d   = 6.0;                // for pots that already have a round shaft

/* [Fit] */
pc  = 0.3;   // plate-to-wall clearance
fit = 0.25;

/* [Hidden] */
$fn = 48;
font_b = "Liberation Sans:style=Bold";
note_names = ["До", "Ре", "Ми", "Фа", "Сол", "Ла", "Си", "До"];
note_led   = ["red", "yellow", "green", "blue", "white", "yellow", "green", "red"];

// ---------------- box geometry ----------------
wall = 2.4;  floor_t = 2.0;
W_in = 172;  W = W_in + 2*wall;
Df = 64;     D = 133.4;            // deck depth / total depth
Hf = 30;     Hb = 64;              // front / back height
plate_t = 2.5;
alpha = atan((Hb - Hf) / (D - Df));
L_panel = (D - wall - Df) / cos(alpha);   // panel length along the slope

// ---------------- key geometry ----------------
p       = 8 * 2.54;      // 20.32 mm = 8 breadboard columns per key
nk      = 8;
key_w   = 18.3;
key_len = 38;
key_proud = 1.0;         // keys stand 1 mm above the deck
kt      = 1.4;           // key top thickness (thin = brighter glow)
ksk     = 0.8;           // key skirt (2 perimeters with a 0.4 nozzle)
comb_drop = 8;           // comb bottom plane is this far below the deck top
function xk(k) = (k - (nk + 1)/2) * p;    // k = 1..8, key = button centre

kbt_w   = 1.6;  kbt_clr = 0.3;
bb_front_y = wall + 0.5 + kbt_w + kbt_clr;
ch      = bb_front_y + fbb_w/2;           // breadboard centre channel = button row
key_back_y  = ch + 16;
key_front_y = key_back_y - key_len;
led_dy  = 8.89;                           // LED in row c, behind the button
zb      = Hf - comb_drop;                 // comb bottom plane = push-pin tip
bb_top_z = zb - 0.3 - btn_h;
kb_base = bb_top_z - fbb_h - floor_t;     // height of the key-bed riser
fin_bot = bb_top_z + 3.5;
deck_hooks  = [18, 50];
panel_hooks = [14, L_panel - 14];

// ---------------- back row (reusable trays) ----------------
T = uno_tray_size();  B = bb_tray_size();
row_y = 68;
xu0   = -W_in/2 + 3.9;                    // USB jack ends 0.3 mm inside the wall
xb0   = xu0 + T[0] + dt_depth();
yb0   = row_y + (T[1] - B[1]) / 2;
usb_c = [row_y + uno_board_xy()[1] + 38.0, floor_t + uno_board_z() + 1.6 + 5.5];

// ---------------- panel layout (local: x, s along slope) ----------------
s_lcd = 44;  x_piezo = -62;  x_knob = 62;  s_text = 10;

echo(str("slope = ", alpha, " deg, panel length = ", L_panel, " mm, key-bed riser = ", kb_base, " mm"));
assert(kb_base >= 1.0, "Buttons are too tall for this layout - lower comb_drop or raise Hf");

module panel_frame() { translate([0, Df, Hf]) rotate([alpha, 0, 0]) children(); }

// =====================================================================
//  helpers
// =====================================================================
// 45-degree ledge along a side wall (sgn = +1 right, -1 left), along y
module tri_ledge(sgn, y0, y1, ztop, w = 2.5) {
    xi = sgn * W_in/2;
    hull() {
        translate([sgn > 0 ? xi - w : xi - 0.5, y0, ztop - 0.01]) cube([w + 0.5, y1 - y0, 0.01]);
        translate([sgn > 0 ? xi - 0.01 : xi - 0.5, y0, ztop - w]) cube([0.51, y1 - y0, w]);
    }
}
module ledge_with_gaps(sgn, y0, y1, ztop, gaps) {
    difference() {
        tri_ledge(sgn, y0, y1, ztop);
        for (g = gaps) translate([-W, g - 6, ztop - 10]) cube([2*W, 12, 20]);
    }
}
// snap hook hanging from a plate; local frame: plate underside at z = 0
module hook(sgn, c) {
    xe = W_in/2 - pc;
    mirror([sgn < 0 ? 1 : 0, 0, 0]) {
        translate([xe - 1.6, c - 4, -9]) cube([1.6, 8, 9.01]);
        translate([0, c + 4, 0]) rotate([90, 0, 0]) linear_extrude(8)
            polygon([[xe - 0.01, -9], [xe + 1.0, -7.8], [xe + 1.0, -7.0], [xe - 0.01, -7.0]]);
    }
}
module hook_window(sgn, c) {   // same local frame as hook()
    translate([sgn > 0 ? W_in/2 - 1 : -W/2 - 1, c - 4.5, -9.5]) cube([wall + 2, 9, 2.7]);
}

// =====================================================================
//  BOX  (black PETG, printed upright, no supports)
// =====================================================================
module box() {
    difference() {
        union() {
            difference() {
                translate([-W/2, 0, 0]) rotate([90, 0, 90]) linear_extrude(W)
                    polygon([[0, 0], [D, 0], [D, Hb], [Df, Hf], [0, Hf]]);
                translate([-W_in/2, wall, floor_t]) cube([W_in, D - 2*wall, 300]);
            }
            // ledges: deck (sides + front) and panel (sides)
            for (sg = [-1, 1]) {
                ledge_with_gaps(sg, wall, Df - 0.5, Hf - plate_t, deck_hooks);
                panel_frame() ledge_with_gaps(sg, 3, L_panel - 4, -plate_t, panel_hooks);
            }
            hull() {
                translate([-W_in/2, wall - 0.5, Hf - plate_t - 0.01]) cube([W_in, 3, 0.01]);
                translate([-W_in/2, wall - 0.5, Hf - plate_t - 2.5]) cube([W_in, 0.51, 2.5]);
            }
            // posts that key into the reusable trays
            translate([0, 0, floor_t]) {
                kit_posts(xu0, row_y, T[0], T[1], h = 12);
                kit_posts(xb0, yb0, B[0], B[1], h = 8);
                // stops behind the key-bed tray
                for (x = [-60, 0, 60]) translate([x - 5, kbt_back() + 0.3, 0]) cube([10, 2.5, 6]);
            }
        }
        // snap windows
        for (sg = [-1, 1]) {
            for (c = deck_hooks) translate([0, 0, Hf - plate_t]) hook_window(sg, c);
            for (c = panel_hooks) panel_frame() translate([0, 0, -plate_t]) hook_window(sg, c);
        }
        // USB cable opening, left wall
        hull() for (dy = [-6, 6], dz = [-5, 5])
            translate([-W/2 - 1, usb_c[0] + dy, usb_c[1] + dz]) rotate([0, 90, 0]) cylinder(r = 3, h = wall + 2);
        // feet recesses
        for (x = [-W/2 + 12, W/2 - 12], y = [12, D - 12]) translate([x, y, -0.01]) cylinder(d = 10, h = 1);
        // name on the bottom
        translate([0, D/2, 0.59]) rotate([180, 0, 0]) linear_extrude(1)
            text("МАЕСТРО", size = 12, font = font_b, halign = "center", valign = "center");
    }
}
function kbt_back() = wall + 0.5 + fbb_w + 2*kbt_clr + 2*kbt_w;

// =====================================================================
//  DECK PLATE  (black PETG, print face down)
// =====================================================================
module deck_plate() {
    difference() {
        translate([-W_in/2 + pc, wall + pc, Hf - plate_t]) cube([W_in - 2*pc, Df - 2*pc - wall, plate_t]);
        for (k = [1:nk]) translate([xk(k) - 9.5, key_front_y - 0.4, Hf - plate_t - 1]) cube([19, key_len + 0.8, plate_t + 2]);
        for (x = [-60, 0, 60]) translate([x, key_back_y + 10, Hf - plate_t - 1]) cylinder(d = 3.3, h = 1 + plate_t - 0.7);  // blind: 0.7 mm skin on top
    }
    // light walls between the keys
    for (i = [0:nk]) translate([(i - nk/2) * p - 0.6, key_front_y, fin_bot])
        cube([1.2, key_len - 2, Hf - plate_t - fin_bot + 0.01]);
    for (sg = [-1, 1], c = deck_hooks) translate([0, 0, Hf - plate_t]) hook(sg, c);
}

// =====================================================================
//  KEY COMB  (WHITE, print as positioned: flat bottom on the bed)
// =====================================================================
module key(k) {
    x = xk(k);  top = Hf + key_proud;
    difference() {
        translate([x - key_w/2, key_front_y, zb]) cube([key_w, key_len, top - zb]);
        translate([x - key_w/2 + ksk, key_front_y + ksk, zb - 1]) cube([key_w - 2*ksk, key_len - 2*ksk, top - kt - zb + 1]);
        // note name, engraved 0.6 mm: glows brighter than the rest of the key
        translate([x + 1, ch + led_dy, top - 0.6]) linear_extrude(1)
            text(note_names[k - 1], size = 5.5, font = font_b, halign = "center", valign = "center");
    }
    // push-pin onto the button
    translate([x, ch, zb]) cylinder(d = 4, h = top - kt - zb + 0.01);
    // flexible hinge to the rail
    translate([x - 4, key_back_y - 0.01, zb]) cube([8, 8.02, 0.8]);
}
module key_comb() {
    for (k = [1:nk]) key(k);
    // rail: low beam + 5 posts that press against the deck plate (saves white filament)
    translate([-80, key_back_y + 8, zb]) cube([160, 4, 3]);
    for (x = [-78, -60, 0, 60, 78]) translate([x - 2, key_back_y + 8, zb]) cube([4, 4, Hf - plate_t - zb]);
    for (x = [-60, 0, 60]) translate([x, key_back_y + 10, Hf - plate_t - 0.01])
        cylinder(d = 3.0, h = plate_t - 0.9);
}

// =====================================================================
//  CONTROL PANEL  (black PETG, print face down)
// =====================================================================
module panel_cutouts() {
    // title
    translate([0, s_text, -0.8]) linear_extrude(1)
        text("МАЕСТРО", size = 8, font = font_b, halign = "center", valign = "center", spacing = 1.15);
    // LCD window
    translate([lcd_bezel_off[0], s_lcd + lcd_bezel_off[1], 0])
        cube([lcd_bezel[0] + 1, lcd_bezel[1] + 1, 10], center = true);
    // speaker grille
    translate([x_piezo, s_lcd, -5]) {
        cylinder(d = 2.4, h = 10, $fn = 16);
        for (r = [3.4, 6.6]) for (a = [0 : 360 / (r < 4 ? 6 : 12) : 359])
            rotate(a + (r < 4 ? 0 : 15)) translate([r, 0, 0]) cylinder(d = 2.4, h = 10, $fn = 16);
    }
    translate([x_piezo, s_lcd, -0.5]) difference() { cylinder(d = 21, h = 1); cylinder(d = 19.6, h = 1); }
    // knob shaft hole + tick marks
    translate([x_knob, s_lcd, -5]) cylinder(d = 7.5, h = 10);
    for (a = [-120 : 40 : 120]) translate([x_knob, s_lcd, -0.5]) rotate(a) translate([-0.5, 13, 0]) cube([1, 2.5, 1]);
}
module panel_underside() {
    z0 = -plate_t;
    // LCD: 4 spacer posts with pins + 2 snap clips on the short edges
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * lcd_holes[0]/2, s_lcd + sy * lcd_holes[1]/2, 0]) {
        translate([0, 0, -lcd_bezel_h]) cylinder(d = 5, h = lcd_bezel_h - plate_t + 0.01);
        translate([0, 0, -lcd_bezel_h - 1.6 - 1.2]) cylinder(d = lcd_hole_d - 0.4, h = 2.81);
    }
    for (sx = [-1, 1]) mirror([sx < 0 ? 1 : 0, 0, 0]) {
        xe = lcd_pcb[0]/2 + 0.2;
        cb = -lcd_bezel_h - 1.6;               // PCB back face
        translate([xe, s_lcd - 5, cb - 1.4]) cube([1.5, 10, z0 - cb + 1.4 + 0.01]);
        translate([0, s_lcd + 5, 0]) rotate([90, 0, 0]) linear_extrude(10)
            polygon([[xe + 0.01, cb - 1.4], [xe - 1.0, cb - 0.3], [xe - 1.0, cb - 0.1], [xe + 0.01, cb - 0.1]]);
    }
    // piezo cup with 0.8 mm air gap behind the grille
    translate([x_piezo, s_lcd, 0]) difference() {
        translate([0, 0, -plate_t - 0.8 - piezo_h]) cylinder(d = piezo_d + 0.4 + 3.2, h = piezo_h + 0.8 + 0.01);
        translate([0, 0, -plate_t - 0.8 - piezo_h - 1]) cylinder(d = piezo_d + 0.4, h = piezo_h + 1);
        translate([0, 0, -plate_t - 0.81]) cylinder(d = 15, h = 1);
    }
    for (a = [0, 120, 240]) translate([x_piezo, s_lcd, 0]) rotate(a)
        translate([(piezo_d + 0.4)/2 - 0.3, -0.6, -plate_t - 0.8 - piezo_h]) cube([0.6, 1.2, piezo_h]);
    // socket for the replaceable pot holder
    translate([x_knob, s_lcd, 0]) difference() {
        translate([-9.8, -9.8, -plate_t - 6]) cube([19.6, 19.6, 6.01]);
        translate([-8.2, -8.2, -plate_t - 7]) cube([16.4, 16.4, 7]);
    }
    for (sg = [-1, 1], c = panel_hooks) translate([0, 0, -plate_t]) hook(sg, c);
}
module panel() {
    difference() {
        intersection() {
            panel_frame() translate([-W_in/2 + pc, -10, -plate_t]) cube([W_in - 2*pc, L_panel + 20, plate_t]);
            translate([-W/2, Df, -50]) cube([W, D - wall - pc - Df, 300]);
        }
        panel_frame() panel_cutouts();
    }
    panel_frame() panel_underside();
}

// =====================================================================
//  KNOB + POT HOLDER  (any colour)
// =====================================================================
module knob() {
    h = 12;
    difference() {
        union() {
            cylinder(d = 22, h = h);
            for (a = [0 : 15 : 359]) rotate(a) translate([11, 0, 0]) cylinder(d = 1.6, h = h, $fn = 8);
        }
        translate([0, 0, h - 0.8]) linear_extrude(1) offset(r = 0.3) square([1.8, 18], center = true);
        translate([0, 0, h - 0.6]) difference() { cylinder(d = 16, h = 1); cylinder(d = 14.8, h = 1); }
    }
    // stem: from cap underside through the panel down to the pot rotor
    stem = 0.5 + plate_t + 0.8;
    translate([0, 0, -stem]) cylinder(d = 6.4, h = stem + 0.01);
    if (knob_mode == "blade")
        translate([-blade[0]/2, -blade[1]/2, -stem - blade[2]]) cube([blade[0], blade[1], blade[2] + 0.01]);
    else
        translate([0, 0, -stem - 3]) difference() { cylinder(d = socket_d + 2.4, h = 3.01); translate([0, 0, -1]) cylinder(d = socket_d + 0.15, h = 4); }
}
module pot_holder() {   // print as is; the closed face goes against the panel, pot slides in from the side
    difference() {
        cube([16, 16, pot_body[2] + 0.8]);
        translate([8 - (pot_body[0] + 0.3)/2, 8 - (pot_body[1] + 0.3)/2, -0.01]) cube([pot_body[0] + 0.3, 20, pot_body[2] + 0.01]);
        translate([8, 8, -1]) cylinder(d = 7.5, h = 20);
    }
}

// =====================================================================
//  KEY-BED TRAY  (black, holds the full breadboard at the right height)
// =====================================================================
module keybed_tray() {
    x0 = -(fbb_l/2 + kbt_clr + kbt_w);  y0 = wall + 0.5;
    lx = fbb_l + 2*(kbt_clr + kbt_w);   ly = fbb_w + 2*(kbt_clr + kbt_w);
    translate([x0, y0, floor_t]) difference() {
        union() {
            // riser: perimeter + ribs
            difference() { cube([lx, ly, kb_base]); translate([3, 3, -1]) cube([lx - 6, ly - 6, kb_base + 2]); }
            for (i = [1:5]) translate([i * lx/6 - 1, 0, 0]) cube([2, ly, kb_base]);
            translate([0, ly/2 - 1, 0]) cube([lx, 2, kb_base]);
            // walls hugging the breadboard
            difference() {
                cube([lx, ly, kb_base + 4]);
                translate([kbt_w, kbt_w, kb_base]) cube([lx - 2*kbt_w, ly - 2*kbt_w, 10]);
                translate([3, 3, -1]) cube([lx - 6, ly - 6, kb_base + 2]);
            }
        }
        // finger notches + wire exits at the back
        for (x = [lx * 0.25, lx * 0.75]) translate([x - 10, -1, kb_base + 1]) cube([20, ly + 2, 10]);
    }
}

// =====================================================================
//  TEST PRINTS (black, before using the white filament)
// =====================================================================
// one key window of the deck, with legs that stand on the breadboard
module test_key_plate() {
    yA = key_front_y - 6;  yB = key_back_y + 13;
    leg = Hf - plate_t - bb_top_z;
    difference() {
        translate([-p/2 - 4, yA, Hf - plate_t]) cube([p + 8, yB - yA, plate_t]);
        translate([-9.5, key_front_y - 0.4, Hf - plate_t - 1]) cube([19, key_len + 0.8, plate_t + 2]);
        translate([0, key_back_y + 10, Hf - plate_t - 1]) cylinder(d = 3.3, h = 1 + plate_t - 0.7);
    }
    for (i = [0, 1]) translate([(i - 0.5) * p - 0.6, key_front_y, fin_bot]) cube([1.2, key_len - 2, Hf - plate_t - fin_bot + 0.01]);
    for (sx = [-1, 1], y = [yA, yB - 4]) translate([sx * (p/2 + 2) - 2, y, bb_top_z]) cube([4, 4, leg + 0.01]);
}
module test_key() {
    translate([-xk(1), 0, 0]) key(1);
    translate([-10, key_back_y + 8, zb]) cube([20, 4, Hf - plate_t - zb]);
    translate([0, key_back_y + 10, Hf - plate_t - 0.01]) cylinder(d = 3.0, h = plate_t - 0.9);
}
module test_lcd() {
    difference() {
        translate([-50, s_lcd - 26, -plate_t]) cube([100, 52, plate_t]);
        translate([lcd_bezel_off[0], s_lcd + lcd_bezel_off[1], 0]) cube([lcd_bezel[0] + 1, lcd_bezel[1] + 1, 10], center = true);
    }
    intersection() { panel_underside(); translate([-50, s_lcd - 26, -30]) cube([100, 52, 30]); }
}

// =====================================================================
//  stand-ins for the electronics (assembly view only)
// =====================================================================
module phantoms() {
    // full breadboard + buttons + LEDs
    color("white") translate([-fbb_l/2, bb_front_y, bb_top_z - fbb_h]) cube([fbb_l, fbb_w, fbb_h]);
    for (k = [1:nk]) {
        color("black") translate([xk(k) - 3, ch - 3, bb_top_z]) cube([6, 6, btn_h - 1.5]);
        color("darkgray") translate([xk(k), ch, bb_top_z]) cylinder(d = 3.5, h = btn_h);
        color(note_led[k - 1]) translate([xk(k) + 2.54, ch + led_dy, bb_top_z]) { cylinder(d = 5.8, h = 1); cylinder(d = 5, h = led_h - 2.5); translate([0, 0, led_h - 2.5]) sphere(d = 5); }
    }
    // Uno + half breadboard in their trays
    color("teal") translate([xu0 + uno_board_xy()[0], row_y + uno_board_xy()[1], floor_t + uno_board_z()]) cube([68.58, 53.34, 1.6]);
    color("silver") translate([xu0 - 3.6, usb_c[0] - 6, floor_t + uno_board_z() + 1.6]) cube([16, 12, 11]);
    color("white") translate([xb0 + 2.3, yb0 + 2.3, floor_t + 2]) cube([82.5, 55, 8.5]);
    // LCD
    panel_frame() {
        color("green") translate([-lcd_pcb[0]/2, s_lcd - lcd_pcb[1]/2, -lcd_bezel_h - 1.6]) cube([lcd_pcb[0], lcd_pcb[1], 1.6]);
        color("#203060") translate([-lcd_bezel[0]/2, s_lcd - lcd_bezel[1]/2, -lcd_bezel_h]) cube([lcd_bezel[0], lcd_bezel[1], lcd_bezel_h - 0.05]);
        color("black") translate([x_piezo, s_lcd, -plate_t - 0.8 - piezo_h]) cylinder(d = piezo_d, h = piezo_h);
    }
}

// =====================================================================
if (part == "box")            box();
if (part == "deck_plate")     translate([0, 0, Hf]) rotate([180, 0, 0]) deck_plate();
if (part == "key_comb")       translate([0, 0, -zb]) key_comb();
if (part == "panel")          rotate([180, 0, 0]) rotate([-alpha, 0, 0]) translate([0, -Df, -Hf]) panel();
if (part == "knob")           translate([0, 0, 12]) rotate([180, 0, 0]) knob();
if (part == "pot_holder")     pot_holder();
if (part == "keybed_tray")    translate([0, 0, -floor_t]) keybed_tray();
if (part == "test_key_plate") translate([0, 0, Hf]) rotate([180, 0, 0]) test_key_plate();
if (part == "test_key")       translate([0, 0, -zb]) test_key();
if (part == "test_lcd")       rotate([180, 0, 0]) test_lcd();
if (part == "assembly") {
    color("#2a2a2a") box();
    color("#3a3a3a") deck_plate();
    color("#f4f4f0") key_comb();
    color("#333333") panel();
    color("#555555") panel_frame() translate([x_knob, s_lcd, 0.5]) knob();
    color("#444444") keybed_tray();
    color("#505050") translate([xu0, row_y, floor_t]) uno_tray();
    color("#505050") translate([xb0, yb0, floor_t]) bb_tray();
    phantoms();
}
