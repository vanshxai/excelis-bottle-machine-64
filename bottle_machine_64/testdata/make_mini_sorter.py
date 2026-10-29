"""
Dev-only generator (run with .venv_gen, not shipped): a tiny 10-part machine as a STEP
assembly + a SolidWorks-style indented BOM, plus the answers we expect the software to find.

Mini Sorter = two drive branches on a base plate
  Disk branch : disk drive motor -> disk shaft -> rotary disk
  Belt branch : belt drive motor -> drive pulley -> timing belt -> idler pulley, flipper arm rides the belt
  plus a photoeye bracket (sensor mount, no motion)
"""
import csv
import json
import os

from build123d import Box, Compound, Cylinder, Pos, export_step

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mini_sorter")
os.makedirs(OUT, exist_ok=True)


def part(shape, name):
    shape.label = name
    return shape


# --- parts (mm) ---------------------------------------------------------------
base = part(Pos(200, 125, 5) * Box(400, 250, 10), "MS00101")
disk_motor = part(Pos(100, 125, 50) * Cylinder(30, 80), "MS00201")
disk_shaft = part(Pos(100, 125, 120) * Cylinder(8, 60), "MS00202")
rotary_disk = part(Pos(100, 125, 153) * Cylinder(90, 6), "MS00203")

belt_motor = part(Pos(300, 60, 40) * Cylinder(25, 60), "MS00301")
drive_pulley = part(Pos(300, 60, 76) * Cylinder(22, 12), "MS00302")
idler_pulley = part(Pos(300, 200, 76) * Cylinder(22, 12), "MS00303")
belt = part(Pos(322, 130, 76) * Box(6, 140, 10), "MS00304")
flipper = part(Pos(270, 130, 100) * Box(80, 8, 20), "MS00305")

photoeye = part(Pos(190, 40, 30) * Box(30, 20, 40), "MS00401")

disk_section = Compound(label="MS00200", children=[disk_motor, disk_shaft, rotary_disk])
belt_section = Compound(label="MS00300", children=[belt_motor, drive_pulley, idler_pulley, belt, flipper])
machine = Compound(label="MS00001", children=[base, disk_section, belt_section, photoeye])

export_step(machine, os.path.join(OUT, "mini_sorter.step"))

# --- SolidWorks-style indented BOM -------------------------------------------
rows = [
    ("1", "MS00001", "Mini Sorter Assembly", "", 1),
    ("1.1", "MS00101", "Base Plate", "Aluminum 6061", 1),
    ("1.2", "MS00200", "Disk Section", "", 1),
    ("1.2.1", "MS00201", "Disk Drive Motor, DC gearmotor 90VDC", "", 1),
    ("1.2.2", "MS00202", "Disk Shaft", "Steel 1018", 1),
    ("1.2.3", "MS00203", "Rotary Disk, 180mm", "Aluminum 6061", 1),
    ("1.3", "MS00300", "Belt Section", "", 1),
    ("1.3.1", "MS00301", "Belt Drive Motor, brushless gearmotor", "", 1),
    ("1.3.2", "MS00302", "Drive Pulley", "Aluminum 6061", 1),
    ("1.3.3", "MS00303", "Idler Pulley", "Aluminum 6061", 1),
    ("1.3.4", "MS00304", "Timing Belt", "Rubber", 1),
    ("1.3.5", "MS00305", "Flipper Arm", "Steel 1018", 1),
    ("1.4", "MS00401", "Photoeye Bracket", "Steel 1018", 1),
]
with open(os.path.join(OUT, "mini_sorter_bom.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ITEM NO.", "PART NUMBER", "DESCRIPTION", "MATERIAL", "QTY."])
    w.writerows(rows)

# --- what the software should discover (used only by our own checks) -----------
expected = {
    "parts_total": 10,
    "assemblies": {"MS00200": ["MS00201", "MS00202", "MS00203"],
                   "MS00300": ["MS00301", "MS00302", "MS00303", "MS00304", "MS00305"]},
    "motors": {"MS00201": "disk drive motor", "MS00301": "belt drive motor"},
    "drive_chains": {"MS00201": ["MS00202", "MS00203"],
                     "MS00301": ["MS00302", "MS00304", "MS00303", "MS00305"]},
    "no_motion": ["MS00101", "MS00401"],
}
json.dump(expected, open(os.path.join(OUT, "expected.json"), "w"), indent=2)
print("written to", OUT, os.listdir(OUT))
