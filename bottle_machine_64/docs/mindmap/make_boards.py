"""Builds the three Excalidraw boards that explain the Bottle Machine 64 software. Run with the project venv."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xl
from xl import Board, KINDS, BANDS

xl.KINDS["ink"] = ("#1e1e1e", "#1e1e1e")
OUT = os.path.dirname(os.path.abspath(__file__))


def title(b, s, sub):
    b.text(0, -120, s, 34, "#1e1e1e", 1)
    b.text(0, -70, sub, 17, "#495057")


# ======================================================================= BOARD 1
def board1():
    b = Board(1)
    title(b, "Bottle Machine 64 software - the whole thing on one page",
          "Read left to right. Purple = the software does it. Orange = you do it. Green = it is saved on disk.")
    HUB_X, HUB_W, CH_X, CH_W = 470, 300, 880, 700
    groups = [
        ("1  Files in", "what the client gives us", "file", [
            ("file", None, "STEP assembly file", "The client's 3D CAD export: every part's shape and where it sits in the assembly. Used to draw the wireframe."),
            ("file", None, "BOM file (CSV or Excel)", "The parts list. Needs 4 columns: item, part number, description, qty. Material is read if it is there."),
            ("stop", None, "Both files, or nothing starts", "A missing file, a missing column or a part that cannot be matched stops the app with a plain list of what to fix. It never fills a gap by itself."),
        ]),
        ("2  Read and check", "automatic, takes seconds", "auto", [
            ("auto", "step_geometry.py", "Opens the STEP file", "OpenCascade turns the 3D model into triangles. The app splits it into parts and keeps each part's name, size box (mm) and outline edges. Mini sorter: 0.3 s. The 179 MB Voron test: 4-7 minutes, once."),
            ("auto", "bom_reader.py", "Reads the BOM", "Checks the required columns exist. Item numbers such as 1, 1.1, 1.2 show which parts sit inside which assembly."),
            ("auto", "matching.py", "Pairs STEP parts with BOM rows", "Exact part number only. The one allowed variation is the suffix CAD adds to copies (-1, <1>, :1, _1). No fuzzy guessing. Lists unmatched parts and wrong quantities."),
        ]),
        ("3  You confirm and type", "the app suggests, you decide", "user", [
            ("user", "part_types.py", "What is each part?", "The app suggests from BOM words ('belt', 'disk', 'brushless'); you confirm. 9 types so far: DC motor, brushless motor, shaft, rotating disk, drive pulley, idler pulley, belt, flipper arm, fixed part."),
            ("user", "linking.py", "What drives what?", "The app suggests (disk -> shaft -> motor); you confirm. A part turned directly by a motor is ACTIVE; a part turned by another part is PASSIVE."),
            ("user", None, "Type the numbers", "Per motor: rated torque, rated current, normal running current. Per part: friction and three levels (fine / warning / critical). Plus the smallest current change your sensor can trust. Radii come from the STEP file, not from you."),
        ]),
        ("4  Build", "one click, locked until complete", "auto", [
            ("auto", "builder.validate()", "Gate: nothing may be missing", "Build stays locked until every value is filled in. It lists exactly what is missing."),
            ("auto", "builder.render_code()", "Writes a code file for every part", "Each part gets its own part_code.py: the formula steps from that part down to its motor, using only the 7 stock formulas."),
            ("auto", "runtime.run_part()", "Simulates every part side by side", "Each part's extra load is swept from 0 to 125% of critical in 26 steps, one CPU process per part. Mini sorter: 5 parts in 3-5 s."),
            ("auto", "rulebook.py", "Writes the rulebook", "Turns the stored tables into fine / elevated / warning / critical current ranges per part, plus a ladder saying which area to inspect."),
        ]),
        ("5  What gets saved", "one project folder per machine", "store", [
            ("store", "wireframe/geometry.json", "The 3D picture", "Every part's outline edges and position, for the 3D view."),
            ("store", "machine/ section / part /", "One folder per part", "part.json (its numbers and where each came from), part_code.py, results.json (its simulated table). Motors get motor.json."),
            ("store", "signatures.json, rulebook.json", "All tables and the rulebook", "Every simulated table in one place, and the fault-current ranges with warning levels."),
            ("store", "answers.json, assumptions.json, source/", "The paper trail", "Everything you typed, the short list of modelling assumptions, and a copy of the two uploaded files."),
        ]),
        ("6  Live use", "when real sensor readings arrive", "auto", [
            ("auto", "live_match.py", "Reads the current change", "Takes the extra current on each motor, lists the parts that could cause that much, and names the smallest area it is sure of: one part, one section, or everything on that motor."),
            ("auto", "app/static/index.html", "Result screen", "The 3D wireframe lights up that area. A replay button tests it with faked readings."),
            ("auto", "flow_trace.py", "Formula Flow dashboard", "Pick a part, change any number, and every formula downstream re-runs in 5-20 ms."),
            ("stop", None, "Not built yet", "Loads adding up at a shared driver, two faults at once, loops, speed / frequency patterns, gear and chain ratios, sensor ports, Windows installer."),
        ]),
    ]
    GAP_C, GAP_G = 14, 46
    y = 0
    laid = []
    for hub_title, hub_sub, hub_kind, kids in groups:
        ys = y
        cards = []
        for kind, tag, ttl, body in kids:
            c = b.card(CH_X, y, CH_W, kind, ttl, body, tag=tag, fs_title=19, fs_body=15)
            cards.append(c)
            y += c["h"] + GAP_C
        y -= GAP_C
        span = (ys, y)
        hh = 96
        hub = b.card(HUB_X, (ys + y) / 2 - hh / 2, HUB_W, hub_kind, hub_title, hub_sub, fs_title=24, fs_body=15, hub=True, title_family=1, min_h=hh)
        laid.append((hub, cards))
        y += GAP_G
    total_h = y - GAP_G
    root = b.card(0, total_h / 2 - 120, 330, "ink", "Bottle Machine 64", "One app, installed on the client's PC. Works offline.\n\nMakes zero guesses: if any value is missing it stops and asks.", fs_title=26, fs_body=16, hub=True, title_family=1)
    for hub, cards in laid:
        b.arrow(root, hub, "h", color="#1e1e1e")
        for c in cards:
            b.arrow(hub, c, "h", color=KINDS[hub["kind"]][1])
    b.legend(0, total_h / 2 + 160)
    b.save(os.path.join(OUT, "1_whole_software.excalidraw"))


# ======================================================================= BOARD 2
def board2():
    b = Board(2)
    title(b, "From two uploaded files to a checked part list",
          "What happens the moment the STEP and BOM files are submitted. Example parts are from the 10-part mini sorter test machine.")
    W, G, H = 300, 46, 175
    xs = [i * (W + G) for i in range(5)]
    # lane 1: STEP
    y1 = 0
    s0 = b.card(xs[0], y1, W, "file", "STEP file", "The client's assembly from CAD. Test file: mini_sorter.step, 10 parts.", min_h=H)
    s1 = b.card(xs[1], y1, W, "auto", "1  Convert to triangles", "OpenCascade (through the cascadio library) reads the STEP and builds a triangle mesh. Detail finer than 0.2 mm is dropped.", tag="step_geometry.extract()", min_h=H)
    s2 = b.card(xs[2], y1, W, "auto", "2  Split into parts", "One entry per solid body. Its place in the assembly tree is kept: Mini Sorter -> Belt Section -> Timing Belt.", tag="trimesh", min_h=H)
    s3 = b.card(xs[3], y1, W, "auto", "3  Find the outline", "Keeps sharp folds, open boundaries and a thinned set of curved edges. This is the wireframe, not the full surface.", tag="numpy", min_h=H)
    s4 = b.card(xs[4], y1, W, "store", "Parts from STEP", "For each part: name, assembly path, size box in mm, outline edges.", min_h=H)
    for a, c in ((s0, s1), (s1, s2), (s2, s3), (s3, s4)):
        b.arrow(a, c, "h")
    # lane 2: BOM
    y2 = H + 70
    b0 = b.card(xs[0], y2, W, "file", "BOM file", "The client's parts list. Test file: mini_sorter_bom.csv.", min_h=H)
    b1 = b.card(xs[1], y2, W, "auto", "1  Read the sheet", "CSV or Excel is turned into rows.", tag="bom_reader.read()", min_h=H)
    b2 = b.card(xs[2], y2, W, "auto", "2  Check the columns", "Needs: item, part number, description, qty. If one is missing the app says which and stops (BomError).", tag="bom_reader.read()", min_h=H)
    b3 = b.card(xs[3], y2, W, "auto", "3  Read the levels", "Item numbers 1, 1.1, 1.2: a row that has children is an assembly (a section); the others are parts.", tag="bom_reader.read()", min_h=H)
    b4 = b.card(xs[4], y2, W, "store", "Rows from BOM", "For each row: part number, description, qty, material, is-assembly.", min_h=H)
    for a, c in ((b0, b1), (b1, b2), (b2, b3), (b3, b4)):
        b.arrow(a, c, "h")
    # matching
    mx = xs[4] + W + 90
    MH = 2 * H + 70
    m = b.card(mx, 0, 470, "auto",
               "Pair every STEP part with a BOM row",
               "For each STEP part, in this order:\n1  its name equals a BOM part number -> matched\n2  else remove a CAD copy-suffix (-1, <1>, :1, _1); if the rest equals a part number -> matched\n3  else its name equals exactly one BOM description -> matched\n4  else -> unmatched\n\nNothing else. No fuzzy matching, no 'closest name'.",
               tag="matching.match()", fs_body=15, min_h=MH)
    b.arrow(s4, m, "h", elbow=True)
    b.arrow(b4, m, "h", elbow=True)
    p = b.card(mx, m["y"] + m["h"] + 60, 470, "stop", "Any of these stops everything",
               "- a STEP part with no BOM row\n- a BOM part that is not in the STEP\n- a quantity that differs (BOM says 2, STEP has 1)\n\nA pop-up lists exactly which part and why. You fix the file and upload again. The app never carries on 'hoping it is fine'.", fs_title=18)
    b.arrow(m, p, "v", color="#c92a2a", dashed=True)
    # analyze
    ax = mx + 470 + 90
    a = b.card(ax, 0, 470, "auto", "Build the part list",
               "One line per part number, with:\n- description and material from the BOM\n- section = the nearest assembly above it in the STEP tree\n- copies = how many times it appears\n- suggested type + the reason (word found)\n- radius: a round part has two equal sides and one different side; radius = half of an equal side, measured from the STEP file",
               tag="builder.analyze()", min_h=MH)
    b.arrow(m, a, "h", label="clean match", label_dy=-26)
    nx = b.card(ax, a["y"] + a["h"] + 60, 470, "user", "Then: three screens for you",
                "1  confirm each part's type\n2  confirm what drives what\n3  type the numbers (motor nameplate, friction, three levels per part, sensor tolerance)\n\nBuild stays locked until all three are complete. Next page: what Build does with the answers.", fs_title=18)
    b.arrow(a, nx, "v", color="#e8590c")
    # row 3: example + rule tables
    ty = max(p["y"] + p["h"], nx["y"] + nx["h"]) + 110
    b.text(0, ty - 46, "How the suggestions are made (the app suggests, you always confirm)", 22, INK, 1)
    ex = b.card(0, ty, 520, "plain", "Example: part MS00203",
                "STEP name MS00203 equals BOM part number MS00203 -> matched\nBOM description: Rotary Disk, 180mm\nSection: Disk Section\nWord 'disk' found -> suggests 'Rotating disk'\nSize box has two equal sides of 179.9 mm -> round, radius 89.96 mm (measured, not typed)", tag="one line of the part list", fs_title=19)
    t1 = b.card(580, ty, 640, "auto", "Suggesting a part type (first matching word wins)",
                "'brushless' or 'bldc'  ->  Brushless gearmotor\n'motor'  ->  DC gearmotor\n'idler'  ->  Idler pulley\n'drive pulley' or 'pulley'  ->  Drive pulley\n'belt'  ->  Belt\n'shaft'  ->  Shaft\n'disk' or 'disc'  ->  Rotating disk\n'flipper' or 'paddle'  ->  Flipper arm\n'bracket', 'plate', 'frame'  ->  Fixed part\nno known word  ->  the app leaves it blank and asks you",
                tag="part_types.suggest_type()", fs_body=15, fs_title=19)
    t2 = b.card(1280, ty, 760, "auto", "Suggesting what drives what, and how the load passes up",
                "shaft  ->  motor: same shaft, torque passes unchanged\ndrive pulley  ->  motor: same shaft, torque passes unchanged\nrotating disk  ->  shaft: same shaft, torque passes unchanged\nbelt  ->  drive pulley: belt force x pulley radius = torque\nidler pulley  ->  belt: torque / pulley radius = belt force\nflipper arm  ->  belt: force passes unchanged\n\nIf only one candidate parent exists the app proposes it; if several, you choose.",
                tag="linking.COUPLINGS", fs_body=15, fs_title=19)
    b.legend(0, ty + max(ex["h"], t1["h"], t2["h"]) + 70)
    b.save(os.path.join(OUT, "2_files_to_part_list.excalidraw"))


# ======================================================================= BOARD 3
def band_rows(b, x, y, w, rows, unit):
    for band, rng, amps in rows:
        b.rect(x, y, w, 34, "#495057", BANDS[band], 1)
        b.text(x + 10, y + 7, band.capitalize(), 16, INK)
        b.text(x + 120, y + 7, f"{rng} {unit}", 16, INK)
        b.text(x + 270, y + 7, f"up to +{amps} A", 16, INK)
        y += 38
    return y


INK = "#1e1e1e"


def board3():
    b = Board(3)
    title(b, "How one part becomes a fault-current range - and how it is used live",
          "All numbers on this page are made-up test values for the 10-part mini sorter. They are NOT Bottle Machine 64 data.")
    W, G = 330, 56
    ys = 0
    names = [
        ("user", None, "Your answers", "Motor nameplate numbers, friction, three levels (fine / warning / critical) for the part."),
        ("store", "part.json", "Part card", "All numbers for this part. Each one says where it came from: typed in, or measured from the STEP file."),
        ("auto", "builder.render_code()", "Part code file", "Writes part_code.py. It answers one question: if this much extra load lands on this part, how much extra torque must the motor give?"),
        ("auto", "runtime.run_part()", "26-point sweep", "Load goes from 0 to 125% of critical. At each point: load -> torque -> motor current."),
        ("store", "results.json", "Part table", "Load against extra current, plus the three levels converted to amps."),
        ("store", "rulebook.json", "Rulebook", "Four bands in amps per part, and the ladder saying which area to look at."),
        ("auto", "live_match.match()", "Live match", "Real extra current on a motor -> parts that could cause it -> smallest area."),
    ]
    row = []
    for i, (k, tag, t, bd) in enumerate(names):
        c = b.card(i * (W + G), ys, W, k, t, bd, tag=tag, min_h=210, fs_body=15)
        row.append(c)
    for a, c in zip(row, row[1:]):
        b.arrow(a, c, "h")
    # who conducts
    cond = b.card(0, 330, 1000, "plain", "Who runs what, and when",
                  "builder.build() is the conductor. It validates, writes the folders, then starts one process per part and runs them side by side (parallel across parts).\nInside one part the formula steps always run in a fixed order, one after another (series): load -> torque at the part -> torque at the motor -> current.\nToday parts never feed each other, so nothing has to wait. Loads adding up at a shared driver are the next thing to build.", tag="orchestration", min_h=0)
    guard = b.card(1060, 330, 1000, "stop", "The zero-guess guard inside every calculation",
                   "Every number is computed through one function, apply(). It takes ONE formula from the project's stock, solves it for the asked variable, and refuses if an input is missing or if an input is passed that the formula does not use. There are no default values anywhere.", tag="runtime.apply()", min_h=0)
    # worked example A (disk)
    ax, ay, aw = 0, cond["y"] + cond["h"] + 100, 470
    b.text(ax, ay - 46, "Example A: rotating disk", 22, INK, 1)
    A = []
    spec = [
        ("plain", None, "Start: a stuck bottle presses 20 N on the disk rim", "20 N is the 'warning' level typed in for this part."),
        ("auto", "formula: disc_brake_torque", "Torque at the disk rim", "T = F x R x mu\n= 20 x 0.0900 x 0.3 = 0.540 N*m\nR measured from the STEP file, mu typed in"),
        ("plain", None, "Disk -> shaft -> motor", "Same shaft all the way: 0.540 N*m passes through unchanged."),
        ("auto", "formula: torque  (motor constant)", "N*m the motor gives per amp", "Kt = rated torque / (rated current - no-load current)\n= 11.3 / (2.61 - 0.4) = 5.11 N*m per A\nfrom the nameplate numbers typed in"),
        ("auto", "formula: torque  (solved for current)", "Extra motor current", "dI = T / Kt = 0.540 / 5.11 = +0.106 A"),
        ("store", None, "Result", "20 N on the disk shows up as +0.106 A on the disk motor."),
    ]
    yy = ay
    for k, tag, t, bd in spec:
        c = b.card(ax, yy, aw, k, t, bd, tag=tag, fs_title=17, fs_body=15, pad=14)
        A.append(c)
        yy += c["h"] + 34
    for u, v in zip(A, A[1:]):
        b.arrow(u, v, "v")
    endA = yy
    # example B (flipper)
    bx = aw + 90
    b.text(bx, ay - 46, "Example B: flipper arm", 22, INK, 1)
    spec = [
        ("plain", None, "Start: 20 N from a bottle on the flipper", "20 N is the 'warning' level typed in for this part."),
        ("plain", None, "Flipper pushes straight on the belt", "Force passes unchanged: 20 N."),
        ("auto", "formula: lever_torque", "Belt force becomes torque on the drive pulley", "T = F x r\n= 20 x 0.02196 = 0.439 N*m\nr measured from the STEP file"),
        ("plain", None, "Drive pulley sits on the motor shaft", "Torque passes through unchanged: 0.439 N*m."),
        ("auto", "formula: torque  (motor constant)", "N*m the motor gives per amp", "Kt = 5.0 / (2.4 - 0.3) = 2.38 N*m per A"),
        ("auto", "formula: torque  (solved for current)", "Extra motor current", "dI = 0.439 / 2.38 = +0.184 A"),
        ("store", None, "Result", "20 N on the flipper shows up as +0.184 A on the belt motor."),
    ]
    yy = ay
    B = []
    for k, tag, t, bd in spec:
        c = b.card(bx, yy, aw, k, t, bd, tag=tag, fs_title=17, fs_body=15, pad=14)
        B.append(c)
        yy += c["h"] + 34
    for u, v in zip(B, B[1:]):
        b.arrow(u, v, "v")
    # bands
    cx = bx + aw + 90
    b.text(cx, ay - 46, "The rulebook it produces", 22, INK, 1)
    cw = 520
    y = ay
    b.text(cx, y, "Rotating disk (disk motor)  -  extra force on the rim", 16, INK)
    y += 30
    y = band_rows(b, cx, y, cw, [("fine", "0 - 5 N", "0.026"), ("elevated", "5 - 20 N", "0.106"), ("warning", "20 - 40 N", "0.211"), ("critical", "40 - 50 N", "0.264")], "")
    y += 22
    b.text(cx, y, "Belt motor - which area to inspect for a given extra current", 16, INK)
    y += 30
    ladder = [("+0.02 to +0.263 A", "Belt Section (flipper, belt or idler could do it)"),
              ("+0.263 to +0.461 A", "Belt Section (flipper or belt)"),
              ("+0.461 to +0.922 A", "Timing Belt (only it is big enough)")]
    for r, area in ladder:
        b.rect(cx, y, cw, 52, "#6741d9", "#f3f0ff", 1)
        b.text(cx + 10, y + 5, r, 16, INK)
        b.text(cx + 10, y + 27, area, 15, "#495057")
        y += 58
    y += 18
    nd = b.card(cx, y, cw, "stop", "Reported, never hidden",
                "Disk shaft at its critical bearing load adds only +0.003 A. That is below the 0.02 A the sensor can be trusted to see, so the rulebook marks it NOT DETECTABLE.", fs_title=17, fs_body=15, pad=14)
    # live match
    lx = cx + cw + 90
    b.text(lx, ay - 46, "Live use (replayed with faked readings)", 22, INK, 1)
    lw = 540
    l0 = b.card(lx, ay, lw, "plain", "Belt motor current rises by +0.30 A", "The sensor says the belt motor draws 0.30 A more than its normal 0.9 A.", fs_title=17, pad=14)
    l1 = b.card(lx, l0["y"] + l0["h"] + 34, lw, "auto", "Which parts could explain 0.30 A?",
                "Flipper arm: yes, at about 32.5 N (warning band)\nTiming belt: yes, at about 32.5 N (elevated band)\nIdler pulley: no, its biggest possible is +0.263 A\nDrive pulley: has no load model of its own", tag="live_match.match()", fs_title=17, pad=14)
    l2 = b.card(lx, l1["y"] + l1["h"] + 34, lw, "store", "Answer: Belt Section",
                "Two parts could do it, both in the Belt Section, so it names the section instead of picking one. The wireframe lights up the whole Belt Section.", fs_title=17, pad=14)
    l3 = b.card(lx, l2["y"] + l2["h"] + 34, lw, "store", "If it were +0.60 A instead",
                "Only the Timing Belt is big enough. The answer is that one part, and only it lights up.", fs_title=17, pad=14)
    for u, v in ((l0, l1), (l1, l2), (l2, l3)):
        b.arrow(u, v, "v")
    # honest limits
    hx = lx + lw + 90
    lim = b.card(hx, ay, 520, "stop", "What this does not do yet",
                 "- Loads adding up where two parts share one driver\n- Two faults at the same time\n- Loops in the drive chain\n- Speed and vibration patterns (only the size of the current change is used, so parts near each other cannot be told apart)\n- Gear and chain ratios between motor and part (the validated gear model is not wired in)\n- Only 9 part types; the Bottle Machine 64 needs more (gearheads, chain, slew-bearing disk)\n- The touch force scale itself is unproven until a recording with known forces is made\n- Reading real sensor ports (only replay exists)", fs_title=18, fs_body=15, pad=16)
    b.legend(0, endA + 40)
    b.save(os.path.join(OUT, "3_part_to_fault_ranges.excalidraw"))


if __name__ == "__main__":
    board1()
    board2()
    board3()
    print("written")
