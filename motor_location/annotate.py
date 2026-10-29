"""Draws the motor locations onto the CAD screen photos. Positions were measured on 1800-px-wide copies of the photos."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bottlemachine64-images")
OUT = os.path.join(ROOT, "motor_location")
def _font_path():
    for p in ("/System/Library/Fonts/Helvetica.ttc", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p): return p
    return "Helvetica.ttc"
FONT = _font_path()
def F(sz, bold=False):
    try:
        return ImageFont.truetype(FONT, sz, index=1 if bold and FONT.endswith(".ttc") else 0)
    except Exception:
        return ImageFont.truetype(FONT, sz)

COL = {"belt": (30, 100, 210), "flap": (230, 110, 10), "elev": (110, 110, 110), "disc": (20, 150, 70), "bottle": (200, 30, 30)}
NAME = {"belt": "1  Belt drive motor", "flap": "2  Flapper (paddle wheel) motor", "elev": "3  Elevator motor", "disc": "4  Round sorter disc motor"}

def load(n):
    im = Image.open(f"{SRC}/IMG_{n}.JPG").convert("RGB")
    return im.resize((1800, int(im.height * 1800 / im.width)))

def dashed_rect(d, box, color, w=5, dash=14):
    x0, y0, x1, y1 = box
    for (a, b, c, e) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        L = max(abs(c - a), abs(e - b)); n = int(L // dash)
        for i in range(0, n, 2):
            t0, t1 = i * dash / L, min((i + 1) * dash / L, 1)
            d.line([(a + (c - a) * t0, b + (e - b) * t0), (a + (c - a) * t1, b + (e - b) * t1)], fill=color, width=w)

def mark(d, key, shape, box, dashed=False):
    c = COL[key]
    if shape == "rect":
        (dashed_rect(d, box, c) if dashed else d.rectangle(box, outline=c, width=6))
    else:
        d.ellipse(box, outline=c, width=6)

def tag(d, xy, lines, key, anchor=None, width=520, size=26, fill=(255, 255, 255)):
    c = COL[key]; x, y = xy
    f, fb = F(size), F(size + 2, True)
    h = 12 + sum((size + 8) for _ in lines)
    d.rounded_rectangle([x, y, x + width, y + h], radius=10, fill=fill, outline=c, width=4)
    yy = y + 8
    for i, t in enumerate(lines):
        d.text((x + 12, yy), t, fill=c if i == 0 else (40, 40, 40), font=fb if i == 0 else f); yy += size + 8
    if anchor:
        cx = x + width / 2 if anchor[0] > x + width else (x if anchor[0] < x else anchor[0])
        cy = y + h if anchor[1] > y + h else (y if anchor[1] < y else anchor[1])
        d.line([(cx, cy), anchor], fill=c, width=5)
        d.ellipse([anchor[0] - 7, anchor[1] - 7, anchor[0] + 7, anchor[1] + 7], fill=c)

def banner(im, title, sub):
    W = im.width; band = Image.new("RGB", (W, 120), (24, 26, 30)); d = ImageDraw.Draw(band)
    d.text((24, 16), title, fill=(255, 255, 255), font=F(40, True)); d.text((24, 70), sub, fill=(190, 195, 205), font=F(26))
    out = Image.new("RGB", (W, im.height + 120), (255, 255, 255)); out.paste(band, (0, 0)); out.paste(im, (0, 120)); return out

def footer(im, lines):
    d0 = ImageDraw.Draw(im); W = im.width; h = 20 + 36 * len(lines)
    out = Image.new("RGB", (W, im.height + h), (245, 245, 242)); out.paste(im, (0, 0)); d = ImageDraw.Draw(out)
    for i, t in enumerate(lines): d.text((24, im.height + 14 + 36 * i), t, fill=(40, 40, 40), font=F(26))
    return out

# ----------------------------------------------------------------------------------- side view A (IMG_4124)
def side_a():
    im = load(4124); d = ImageDraw.Draw(im)
    mark(d, "disc", "rect", (1178, 478, 1368, 596))
    mark(d, "flap", "ell", (796, 345, 874, 432))
    mark(d, "belt", "rect", (730, 662, 870, 792))
    mark(d, "bottle", "rect", (545, 515, 660, 612), dashed=True)
    tag(d, (1000, 60), [NAME["disc"], "Under the tilted 36-inch disk, next to the driver", "cabinet. Drawn as a box-shaped motor + gearbox."], "disc", anchor=(1275, 478), width=760)
    tag(d, (190, 130), [NAME["flap"], "Looks like the gearmotor on top of the upright post", "at the belt entrance (Paddle Wheel Assembly)."], "flap", anchor=(796, 380), width=700)
    tag(d, (40, 830), [NAME["belt"], "Looks like the motor mount under the conveyor (BOM: US05601).", "The motor body itself is not clearly drawn in this view."], "belt", anchor=(730, 760), width=790)
    tag(d, (1010, 880), [NAME["elev"], "NOT in this CAD. Only three motors are modelled,", "so there is nothing to mark here."], "elev", width=640)
    tag(d, (150, 440), ["Red objects = red spray bottles", "(test bottles in the CAD). Not motors."], "bottle", anchor=(560, 545), width=450, size=24)
    return footer(banner(im, "Where the motors are: side view A", "CAD render (photo of the computer screen, IMG_4124). Boxes mark where each motor sits."),
                  ["Solid boxes: shapes seen in this render. Dashed red: spray bottles (not motors).","Positions are read from the shapes; the CAD component tree says which assembly each motor belongs to.","Nobody has clicked each motor in the CAD viewer to highlight it yet: treat these as very likely, not proven."])

# ----------------------------------------------------------------------------------- side view B (IMG_4123)
def side_b():
    im = load(4123); d = ImageDraw.Draw(im)
    mark(d, "disc", "rect", (580, 610, 668, 690))
    mark(d, "flap", "rect", (985, 452, 1095, 515))
    mark(d, "belt", "rect", (1044, 736, 1168, 842))
    mark(d, "bottle", "rect", (855, 565, 960, 645), dashed=True)
    mark(d, "bottle", "rect", (1205, 580, 1300, 640), dashed=True)
    tag(d, (60, 300), [NAME["disc"], "Behind the control box, under the low side of", "the tilted disk (same motor as in view A)."], "disc", anchor=(625, 612), width=620)
    tag(d, (700, 120), [NAME["flap"], "Gear/motor block on the upright post at the belt entrance.", "The round plate to its right is a wheel, not a motor."], "flap", anchor=(1040, 452), width=780)
    tag(d, (1180, 880), [NAME["belt"], "Square motor flange on the mount plate under the", "conveyor (BOM: US05601)."], "belt", anchor=(1168, 790), width=610)
    tag(d, (60, 1000), [NAME["elev"], "NOT in this CAD. Nothing to mark."], "elev", width=470)
    return footer(banner(im, "Where the motors are: side view B", "Same machine seen from the other side (IMG_4123)."),
                  ["Dashed red boxes are red spray bottles (test bottles), not motors.","Positions are read from the shapes in the render, not from clicking each motor in the CAD viewer."])

# ----------------------------------------------------------------------------------- isometric (IMG_4122)
def iso():
    im = load(4122); d = ImageDraw.Draw(im)
    mark(d, "flap", "ell", (995, 525, 1095, 610))
    mark(d, "disc", "rect", (690, 780, 860, 860), dashed=True)
    mark(d, "belt", "rect", (1000, 845, 1150, 935), dashed=True)
    mark(d, "bottle", "rect", (905, 670, 985, 725), dashed=True)
    mark(d, "bottle", "rect", (1130, 530, 1230, 600), dashed=True)
    tag(d, (1060, 120), [NAME["flap"], "Upright post at the belt entrance: the", "paddle wheel assembly. Seen here."], "flap", anchor=(1050, 527), width=560)
    tag(d, (60, 120), [NAME["disc"], "Hidden under the tilted disk. Dashed = approximate", "spot; see the side views for where it really shows."], "disc", anchor=(775, 780), width=700)
    tag(d, (1130, 1010), [NAME["belt"], "Hidden under the conveyor frame. Dashed =", "approximate; see the side views."], "belt", anchor=(1075, 935), width=600)
    tag(d, (60, 1120), [NAME["elev"], "Not in this CAD. Cannot be marked."], "elev", width=470)
    return footer(banner(im, "Where the motors are: whole machine", "CAD render (photo of the computer screen, IMG_4122). Dashed outlines are approximate or hidden from this angle."),
                  ["Red parts on the belts are red spray bottles (test bottles), not motors."])

# ----------------------------------------------------------------------------------- close-ups
def closeups():
    items = [("4  Round sorter disc motor (view A)", 4124, (1130, 430, 1400, 640), "disc"), ("2  Flapper motor on the post (view A)", 4124, (760, 290, 980, 500), "flap"),
             ("1  Belt drive motor mount plate (view B)", 4123, (1020, 720, 1200, 870), "belt")]
    W = 640; tiles = []
    for title, n, box, key in items:
        src = Image.open(f"{SRC}/IMG_{n}.JPG").convert("RGB"); s = src.width / 1800
        c = src.crop(tuple(int(v * s) for v in box)); c = c.resize((W, int(c.height * W / c.width)))
        t = Image.new("RGB", (W, c.height + 52), (255, 255, 255)); t.paste(c, (0, 52)); dd = ImageDraw.Draw(t)
        dd.rectangle([0, 0, W, 52], fill=COL[key]); dd.text((12, 10), title, fill=(255, 255, 255), font=F(26, True)); dd.rectangle([0, 52, W - 1, t.height - 1], outline=COL[key], width=5)
        tiles.append(t)
    H = max(t.height for t in tiles); sheet = Image.new("RGB", (3 * W + 40, H), (245, 245, 242))
    for i, t in enumerate(tiles): sheet.paste(t, (i * (W + 20), 0))
    return footer(banner(sheet, "Close-ups of the three motor spots", "Zoomed from the screen photos, so they look blocky. Shapes, not detail, are what matters."),
                  ["Not shown: elevator motor (not in the CAD)."])

for name, fn in (("MOTORS_1_whole_machine", iso), ("MOTORS_2_side_view_A", side_a), ("MOTORS_3_side_view_B", side_b), ("MOTORS_4_closeups", closeups)):
    img = fn(); img.save(f"{OUT}/{name}.jpg", quality=90); print(name, img.size)
