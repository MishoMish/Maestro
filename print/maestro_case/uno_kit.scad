// =====================================================================
//  uno_kit.scad  --  REUSABLE parts for an Arduino Uno R3 project
//  * uno_tray : open-top tray, board sits on printed pegs (no screws)
//  * uno_lid  : snap-on lid with slots for jumper wires
//  * bb_tray  : half-size breadboard tray, slides onto the Uno tray
//               with two vertical dovetails
//
//  Nothing is glued or screwed to the board or the breadboard, so the
//  kit stays exactly as you got it.
//
//  Project boxes can `use <uno_kit.scad>` and call kit_posts() to get
//  matching posts that lock into the vertical grooves on the trays.
// =====================================================================

part = "uno_tray"; // [uno_tray, uno_lid, bb_tray, all]

/* [Arduino Uno R3 - standard, do not change] */
uno_l   = 68.58;
uno_w   = 53.34;
uno_pcb = 1.6;
// mounting holes, origin = PCB corner next to the power jack
uno_holes = [[13.97, 2.54], [15.24, 50.8], [66.04, 7.62], [66.04, 35.56]];
usb_y  = [32.0, 44.0];   // USB-B jack span along the short edge
usb_h  = 11.0;           // jack height above PCB top
pwr_y  = [3.64, 12.64];  // barrel jack span
pwr_h  = 11.0;
hdr_h  = 8.5;            // female header height above PCB

/* [Tray] */
wall       = 2.0;
floor_t    = 2.0;
standoff_h = 3.0;
clr        = 0.6;    // gap PCB <-> wall
tray_h     = 14.0;
peg_d      = 2.8;    // hole is 3.2

/* [Half breadboard - measure yours] */
hbb_l   = 82.5;
hbb_w   = 55.0;
hbb_h   = 8.5;
hbb_clr = 0.3;
hbb_wall_h = 6.0;    // how high the tray walls hug the breadboard

/* [Fit tuning] */
fit = 0.25;          // dovetail / snap clearance; raise to 0.3 if tight

/* [Rail-groove interface used by project boxes] */
groove_w = 3.0;
groove_d = 1.0;

$fn = 40;

// ---------- derived ----------
function uno_tray_size() = [uno_l + 2*clr + 2*wall, uno_w + 2*clr + 2*wall, tray_h];
function bb_tray_size()  = [hbb_l + 2*hbb_clr + 2*wall, hbb_w + 2*hbb_clr + 2*wall, floor_t + hbb_wall_h];
function dt_depth()      = 4;             // dovetail boss sticks out this far
function uno_board_z()   = floor_t + standoff_h;      // PCB underside, from tray bottom
function uno_board_xy()  = [wall + clr, wall + clr];  // PCB corner inside tray
function kit_groove()    = [groove_w, groove_d];

T  = uno_tray_size();
B  = bb_tray_size();
dt_h = 8;
dt_ys = [T[1]*0.27, T[1]*0.73];
snap_z = [8.2, 10.4];           // lid snap groove on the long walls

// ---------- helpers ----------
module rgroove(len_x, size_y, h) {          // vertical grooves, long walls
    for (y = [-0.01, size_y - groove_d + 0.01])
        translate([len_x/2 - groove_w/2, y, -1]) cube([groove_w, groove_d, h + 2]);
}
module feet(len_x, size_y) {                // 1 mm recesses for rubber feet
    for (x = [8, len_x - 8], y = [8, size_y - 8])
        translate([x, y, -0.01]) cylinder(d = 10, h = 1);
}
module dovetail2d(narrow, wide, depth) {
    polygon([[0, -narrow/2], [depth, -wide/2], [depth, wide/2], [0, narrow/2]]);
}

// =====================================================================
module uno_tray() {
    bx = uno_board_xy();
    difference() {
        union() {
            cube(T);
            // dovetail bosses at the far end (opposite USB)
            for (y = dt_ys) translate([T[0] - 0.01, y - 6, 0]) cube([dt_depth(), 12, dt_h]);
        }
        // pocket
        translate([wall, wall, floor_t]) cube([T[0] - 2*wall, T[1] - 2*wall, tray_h]);
        // USB + power jack cut-outs (open to the top so the board drops in)
        translate([-1, bx[1] + usb_y[0] - 0.75, uno_board_z() + uno_pcb - 0.5])
            cube([wall + 2, usb_y[1] - usb_y[0] + 1.5, 50]);
        translate([-1, bx[1] + pwr_y[0] - 0.75, uno_board_z() + uno_pcb - 0.5])
            cube([wall + 2, pwr_y[1] - pwr_y[0] + 1.5, 50]);
        // female dovetail slots (closed 1 mm at the bottom = stop)
        for (y = dt_ys) translate([T[0] + dt_depth() + 0.01, y, 1])
            mirror([1, 0, 0]) linear_extrude(dt_h) dovetail2d(5 + 2*fit, 8 + 2*fit, 3 + fit);
        rgroove(T[0], T[1], tray_h);
        // lid snap groove on both long walls
        for (y = [-0.01, T[1] - 0.8 + 0.01])
            translate([wall + 4, y, snap_z[0]]) cube([T[0] - 2*wall - 8, 0.8, snap_z[1] - snap_z[0]]);
        feet(T[0], T[1]);
        // save plastic + airflow under the board
        translate([T[0]/2, T[1]/2, -1]) linear_extrude(floor_t + 2)
            offset(r = 3) square([26, 22], center = true);
    }
    // stand-offs with locating pegs
    for (h = uno_holes) translate([bx[0] + h[0], bx[1] + h[1], 0]) {
        cylinder(d = 5.5, h = uno_board_z());
        cylinder(d = peg_d, h = uno_board_z() + uno_pcb + 1.0);
        translate([0, 0, uno_board_z() + uno_pcb + 1.0])
            cylinder(d1 = peg_d, d2 = peg_d - 0.8, h = 0.6);
    }
}

// =====================================================================
module uno_lid() {
    bx = uno_board_xy();
    lid_z = uno_board_z() + uno_pcb + usb_h + 0.4;   // underside of lid
    lt = 1.8; sk = 1.6; g = 0.25;
    difference() {
        union() {
            translate([0, -g - sk, lid_z]) cube([T[0], T[1] + 2*(g + sk), lt]);
            for (side = [0, 1]) {
                y0 = side == 0 ? -g - sk : T[1] + g;
                translate([4, y0, 8.4]) cube([T[0] - 8, sk, lid_z - 8.4 + 0.01]);
                // barb, pointing into the tray groove
                translate([6.5, side == 0 ? -g : T[1] + g, 0])
                    rotate([90, 0, 90]) linear_extrude(T[0] - 13)
                        polygon(side == 0 ?
                            [[0, 8.4], [0.7 + g, 9.4], [0.7 + g, 10.2], [0, 10.2]] :
                            [[0, 8.4], [-0.7 - g, 9.4], [-0.7 - g, 10.2], [0, 10.2]]);
            }
        }
        // jumper slots above the two header rows
        translate([bx[0] + 16.5, bx[1] + 47.8, lid_z - 1]) cube([49.5, 6.1, 5]);
        translate([bx[0] + 25.0, bx[1] - 0.6,  lid_z - 1]) cube([41.0, 6.2, 5]);
        // vent slots
        for (i = [0:4]) translate([bx[0] + 22 + i*8, bx[1] + 15, lid_z - 1]) cube([3, 22, 5]);
    }
}

// =====================================================================
module bb_tray() {
    difference() {
        union() {
            cube(B);
            // male dovetails on the x = 0 end, mate with the Uno tray bosses
            for (y = dt_ys) translate([0.01, y + (B[1] - T[1])/2, 1.2])
                mirror([1, 0, 0]) linear_extrude(dt_h - 1.2) dovetail2d(5, 8, 3 - fit);
        }
        translate([wall, wall, floor_t]) cube([B[0] - 2*wall, B[1] - 2*wall, 50]);
        // finger notch on the free end
        translate([B[0] - wall - 1, B[1]/2 - 10, floor_t + 1]) cube([wall + 2, 20, 50]);
        // push-out hole
        translate([B[0]/2, B[1]/2, -1]) cylinder(d = 22, h = 10);
        rgroove(B[0], B[1], B[2]);
        feet(B[0], B[1]);
    }
}

// =====================================================================
// For project boxes: posts that key into the vertical grooves of a tray
// whose outer footprint starts at [x0, y0] with size [lx, ly].
// front/back posts are 'depth' deep and 'h' tall.
module kit_posts(x0, y0, lx, ly, h = 12, depth = 3, gap = 0.3) {
    for (side = [0, 1]) {
        yp = side == 0 ? y0 - gap - depth : y0 + ly + gap;
        translate([x0 + lx/2 - 4, yp, 0]) cube([8, depth, h]);
        // tongue
        yt = side == 0 ? y0 - gap - 0.01 : y0 + ly - groove_d + fit;
        translate([x0 + lx/2 - (groove_w - 2*fit)/2, yt, 0])
            cube([groove_w - 2*fit, groove_d - fit + gap + 0.01, h]);
    }
}

// =====================================================================
if (part == "uno_tray") uno_tray();
if (part == "uno_lid")  translate([0, 0, uno_board_z() + uno_pcb + usb_h + 0.4 + 1.8]) rotate([180, 0, 0]) uno_lid();
if (part == "bb_tray")  bb_tray();
if (part == "all") {
    color("dimgray") uno_tray();
    color("gray", 0.5) translate([0, 0, 6]) uno_lid();
    color("darkslategray") translate([T[0] + dt_depth(), (T[1] - B[1])/2, 0]) bb_tray();
}
