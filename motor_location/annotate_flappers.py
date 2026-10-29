"""Draws MOTORS_5_the_two_flappers.jpg: the two floating units, and the CAD parts list of the second one (IMG_4086)."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bottlemachine64-images")
OUT = os.path.join(ROOT, "motor_location", "MOTORS_5_the_two_flappers.jpg")
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

GREEN, RED, GREY, INK = (20, 150, 70), (200, 30, 30), (110, 110, 110), (40, 40, 40)

def box(d, xy, lines, color, size=25, anchor=None):
    x, y, w = xy
    h = 16 + sum(size + 8 for _ in lines)
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=(255, 255, 255), outline=color, width=4)
    yy = y + 8
    for i, t in enumerate(lines):
        d.text((x + 12, yy), t, fill=color if i == 0 else INK, font=F(size + 2, True) if i == 0 else F(size)); yy += size + 8
    if anchor:
        d.line([(x + w / 2, y + h), anchor], fill=color, width=5)
        d.ellipse([anchor[0] - 8, anchor[1] - 8, anchor[0] + 8, anchor[1] + 8], fill=color)
    return h

W, H = 1800, 1500
canvas = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(canvas)
d.rectangle([0, 0, W, 120], fill=(24, 26, 30))
d.text((24, 16), "The two flappers: only one of them has a motor", fill=(255, 255, 255), font=F(40, True))
d.text((24, 70), "Left: the two floating units in the CAD render (IMG_4124). Right: the CAD parts list of the second unit (IMG_4086).", fill=(190, 195, 205), font=F(26))

# left panel: both floating units
a = Image.open(f"{SRC}/IMG_4124.JPG").convert("RGB").crop((1000, 450, 1800, 1000))
a = a.resize((880, int(a.height * 880 / a.width)))
top = 290
canvas.paste(a, (10, top)); d.rectangle([10, top, 890, top + a.height], outline=(180, 180, 180), width=2)
s = 880 / 800
box(d, (10, 140, 430), ["Flapper 2: Knock-down wheel", "NO motor. A plain wheel", "on a pivot bolt."], RED, anchor=(10 + 200 * s, top + 350 * s))
box(d, (460, 140, 430), ["Flapper 1: Paddle wheel", "HAS a motor: the black", "gearmotor UP00601."], GREEN, anchor=(10 + 520 * s, top + 245 * s))
d.ellipse([10 + 115 * s, top + 270 * s, 10 + 290 * s, top + 440 * s], outline=RED, width=5)
d.ellipse([10 + 465 * s, top + 195 * s, 10 + 580 * s, top + 310 * s], outline=GREEN, width=5)

# right panel: tree photo of the knock-down wheel assembly
t = Image.open(f"{SRC}/IMG_4086.JPG").convert("RGB").crop((80, 690, 2900, 1900))
td = ImageDraw.Draw(t); td.rectangle([250, 240, 2820, 1150], outline=RED, width=12)
t = t.resize((880, int(t.height * 880 / t.width)))
box(d, (910, 140, 880), ["What the knock-down wheel is made of (CAD component list)", "Slotted bracket, the wheel, a 1/2-inch shoulder bolt, an L-bracket."], RED)
canvas.paste(t, (910, top)); d.rectangle([910, top, 1790, top + t.height], outline=(180, 180, 180), width=2)
d.text((920, top + t.height + 8), "No motor, gearbox or coupling in its list.", fill=INK, font=F(25))

# bottom: the fourth motor
y = top + max(a.height, t.height) + 40
d.rounded_rectangle([10, y, 1790, y + 245], radius=10, fill=(245, 245, 242), outline=GREEN, width=4)
d.text((28, y + 12), "So where is the fourth motor?", fill=GREEN, font=F(32, True))
rows = [
    "The motor on the post above the red bottle is flapper 1's motor (UP00601). It is already one of the three.",
    "The same CAD's electrical panel has 4 speed knobs, 4 speed pots and 5 driver boards, but only 3 motors are drawn.",
    "Your own list has a fourth motor: the elevator (same catalog link as the belt drive). It is not drawn here.",
    "That is an inference from the panel and your list. The CAD does not show the fourth motor, so it is not proven.",
]
for i, r in enumerate(rows):
    d.text((28, y + 62 + 42 * i), r, fill=INK, font=F(27))
canvas = canvas.crop((0, 0, W, y + 265))
canvas.save(OUT, quality=90); print(OUT, canvas.size)
