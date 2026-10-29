"""Check image only (not the manufacturer sheet): the five things around the hand crank at the drum exit, View 1."""
import os
from PIL import Image, ImageDraw
from annotate_for_manufacturer import F, wrap, badge, GREEN, ORANGE, RED, BLUE, INK

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bottlemachine64-images") + "/IMG_4124.JPG"
OUT = os.path.join(ROOT, "motor_location", "CHECK_handle_area.jpg")
S = 1.064
im = Image.open(SRC).convert("RGB").crop((1440, 490, 1740, 960))
im = im.resize((int(im.width * 2.2 * S), int(im.height * 2.2 * S)), Image.LANCZOS)
W, H = 1500, 80 + im.height + 40
c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
d.rectangle([0, 0, W, 64], fill=(24, 26, 30)); d.text((20, 14), "Check only, not the sheet: which number is your grey box?", fill=(255, 255, 255), font=F(32, True))
ox, oy = 380, 80
c.paste(im, (ox, oy)); d.rectangle([ox, oy, ox + im.width, oy + im.height], outline=(180, 180, 180), width=2)

def item(n, x, y, w, title, body, color, ax, ay, left):
    ft, fb = F(26, True), F(23)
    tl, bl = wrap(title, ft, w - 66), wrap(body, fb, w - 66)
    h = 24 + len(tl) * 32 + len(bl) * 28
    pt = (ox + ax * S * 1.0, oy + ay * S)
    ex = x + w if left else x
    d.line([(ex, y + h / 2), pt], fill=color, width=5)
    d.ellipse([pt[0] - 9, pt[1] - 9, pt[0] + 9, pt[1] + 9], fill=color)
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=(255, 255, 255), outline=color, width=4)
    badge(d, x + 32, y + 32, str(n), color)
    yy = y + 10
    for t in tl: d.text((x + 64, yy), t, fill=color, font=ft); yy += 32
    for t in bl: d.text((x + 64, yy), t, fill=INK, font=fb); yy += 28

# anchors are in the 2.2x crop coordinates of pad_A (before the extra S scale is applied inside item())
item(1, 1100, 500, 380, "Hand crank", "Bent lever with a handle, pointing at the drum wall.", ORANGE, 484, 526, False)
item(2, 1100, 290, 380, "Grey block with a slot", "On the bracket, just under the top rod.", BLUE, 360, 447, False)
item(3, 20, 380, 340, "Black round body", "On the left end of the bracket.", GREEN, 150, 475, True)
item(4, 1100, 740, 380, "Tall post", "Runs down to the belt plate.", RED, 412, 700, False)
item(5, 20, 820, 340, "Hanging arm", "Grey paddle blade at its lower end.", GREEN, 232, 850, True)
d.text((20, H - 32), "Close-up of View 1 at the drum exit, above the first red bottle.", fill=INK, font=F(22))
c.save(OUT, quality=90); print(OUT, c.size)
