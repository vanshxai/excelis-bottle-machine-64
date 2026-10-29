"""Draws FOR_MANUFACTURER_motors_and_unsupported_parts.jpg: two CAD views with every motor and every
unsupported-looking part labelled, plus the numbered questions. Positions are in 1800-px-wide frame coordinates."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bottlemachine64-images")
OUT = os.path.join(ROOT, "motor_location", "FOR_MANUFACTURER_motors_and_unsupported_parts.jpg")
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

W = 1800
GREEN, ORANGE, RED, GREY, INK, BLUE = (18, 140, 66), (222, 105, 8), (200, 30, 30), (70, 70, 70), (35, 35, 35), (30, 100, 210)

def wrap(text, font, width):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if font.getlength(t) <= width: cur = t
        else: lines.append(cur); cur = word
    return lines + [cur] if cur else lines

def dashed_rect(d, box, color, w=5, dash=14):
    x0, y0, x1, y1 = box
    for (a, b, c, e) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        L = max(abs(c - a), abs(e - b)); n = int(L // dash)
        for i in range(0, n, 2):
            t0, t1 = i * dash / L, min((i + 1) * dash / L, 1)
            d.line([(a + (c - a) * t0, b + (e - b) * t0), (a + (c - a) * t1, b + (e - b) * t1)], fill=color, width=w)

def badge(d, cx, cy, text, color, r=22):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    f = F(28 if len(text) == 1 else 21, True); d.text((cx - f.getlength(text) / 2, cy - (16 if len(text) == 1 else 12)), text, fill=(255, 255, 255), font=f)

class Panel:
    def __init__(self, n, y0, y1, title):
        im = Image.open(f"{SRC}/IMG_{n}.JPG").convert("RGB")
        im = im.resize((W, int(im.height * W / im.width)))
        self.y0 = y0; self.img = im.crop((0, y0, W, y1)); self.d = ImageDraw.Draw(self.img); self.title = title

    def p(self, x, y): return (x, y - self.y0)

    def outline(self, kind, box, color, dashed=False):
        x0, y0, x1, y1 = box; b = (x0, y0 - self.y0, x1, y1 - self.y0)
        if dashed: dashed_rect(self.d, b, (255, 255, 255), w=11); dashed_rect(self.d, b, color)
        elif kind == "ellipse": self.d.ellipse(b, outline=color, width=6)
        else: self.d.rectangle(b, outline=color, width=6)

    def label(self, x, y, w, tag, title, body, color, anchor=None, dashed=False):
        ft, fb, pad, tx = F(27, True), F(24), 12, 62
        tl, bl = wrap(title, ft, w - tx - pad), wrap(body, fb, w - tx - pad)
        h = 2 * pad + len(tl) * 33 + len(bl) * 30 + 2
        x0, y0 = x, y - self.y0
        if anchor:
            ax, ay = anchor[0], anchor[1] - self.y0
            sx = min(max(ax, x0 + 40), x0 + w - 40); sy = y0 + h if ay > y0 + h else (y0 if ay < y0 else y0 + h / 2)
            if y0 <= ay <= y0 + h: sx = x0 + w if ax > x0 + w else x0
            self.d.line([(sx, sy), (ax, ay)], fill=color, width=5)
            self.d.ellipse([ax - 8, ay - 8, ax + 8, ay + 8], fill=color)
        self.d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=10, fill=(255, 255, 255), outline=color, width=4)
        if dashed: dashed_rect(self.d, (x0, y0, x0 + w, y0 + h), color, w=4, dash=12)
        badge(self.d, x0 + 32, y0 + 32, tag, color)
        yy = y0 + pad
        for t in tl: self.d.text((x0 + tx, yy), t, fill=color, font=ft); yy += 33
        for t in bl: self.d.text((x0 + tx, yy), t, fill=INK, font=fb); yy += 30
        return h

def build():
    A = Panel("4124", 130, 1130, "View 1")
    A.outline("rect", (1178, 478, 1368, 596), GREEN)
    A.outline("rect", (730, 662, 870, 792), GREEN)
    A.outline("rect", (606, 275, 716, 492), ORANGE, dashed=True)
    A.outline("rect", (1320, 288, 1476, 472), BLUE, dashed=True)
    A.label(40, 150, 470, "A", "Knock-down wheel assembly", "Why is it in the air? What holds it?", ORANGE, anchor=(640, 285))
    A.label(800, 150, 420, "1", "Disc drive motor", "Under the disc. Is this the right motor, in the right place?", GREEN, anchor=(1250, 478))
    A.label(1360, 150, 420, "?", "Grey box on the drum", "Is this a motor? If yes, what does it drive?", BLUE, anchor=(1400, 288))
    A.label(40, 840, 640, "2", "Belt drive motor", "Marked on its mount plate under the conveyor. Is this the right motor, in the right place?", GREEN, anchor=(745, 790))
    A.label(930, 880, 700, "3 4", "Third and fourth motors: where?", "Only two motors are clearly in the model. Where are the other two?", RED, dashed=True)

    B = Panel("4123", 130, 1150, "View 2")
    B.outline("rect", (580, 610, 668, 688), GREEN)
    B.outline("rect", (1045, 737, 1168, 842), GREEN)
    B.outline("rect", (1168, 372, 1268, 566), ORANGE, dashed=True)
    B.label(1310, 150, 470, "A", "Knock-down wheel assembly", "Why is it in the air? What holds it?", ORANGE, anchor=(1230, 372))
    B.label(40, 720, 420, "1", "Disc drive motor", "Behind the control box, under the disc. Is this the right motor, in the right place?", GREEN, anchor=(600, 688))
    B.label(1170, 880, 610, "2", "Belt drive motor", "Square flange on the mount plate under the conveyor. Is this the right motor, in the right place?", GREEN, anchor=(1160, 842))
    B.label(60, 1000, 720, "3 4", "Third and fourth motors: where?", "Only two motors are clearly in the model. Where are the other two?", RED, dashed=True)
    return A, B

QUESTIONS = [
    ("1", GREEN, ["Disc drive motor: is this the right motor, in the position marked?"]),
    ("2", GREEN, ["Belt drive motor: is this the right motor, on the mount plate under the conveyor?"]),
    ("3 4", RED, ["Where are the third and fourth motors?"]),
    ("?", BLUE, ["Grey box on the drum (blue box, View 1): is it a motor? If yes, what does it drive?"]),
    ("A", ORANGE, ["Knock-down wheel assembly: why is it in the air? What holds it?"]),
]

def main():
    A, B = build()
    qh = 40 + sum(len(ls) * 34 + 22 for _, _, ls in QUESTIONS)
    H = 118 + 74 + 50 + A.img.height + 50 + B.img.height + 30 + qh + 70
    c = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(c)
    d.rectangle([0, 0, W, 118], fill=(24, 26, 30))
    d.text((24, 14), "Bottle Machine 3D model: are the motors in the right place?", fill=(255, 255, 255), font=F(40, True))
    d.text((24, 70), "Photos of the 3D model on a screen. Please check the marked positions and answer the five questions below.", fill=(190, 195, 205), font=F(25))
    y = 118 + 14
    chips = [(GREEN, False, "Motor position to check"), (BLUE, True, "Grey box: motor or not?"), (RED, True, "Motors 3 and 4: not found"), (ORANGE, True, "In the air")]
    x = 24
    for col, dash, txt in chips:
        (dashed_rect(d, (x, y + 6, x + 52, y + 40), col, w=5, dash=10) if dash else d.rectangle([x, y + 6, x + 52, y + 40], outline=col, width=6))
        d.text((x + 64, y + 8), txt, fill=INK, font=F(24)); x += 64 + int(F(24).getlength(txt)) + 36
    y = 118 + 74
    for P, name in ((A, "View 1"), (B, "View 2: the same machine from the other side")):
        d.rectangle([0, y, W, y + 50], fill=(235, 236, 238)); d.text((24, y + 8), name, fill=INK, font=F(30, True)); y += 50
        c.paste(P.img, (0, y)); y += P.img.height
    y += 24
    d.text((24, y), "Questions", fill=INK, font=F(34, True)); y += 52
    for tag, col, lines in QUESTIONS:
        badge(d, 46, y + 18, tag, col)
        for i, t in enumerate(lines):
            d.text((90, y + i * 34), t, fill=INK, font=F(26))
        y += len(lines) * 34 + 22
    y += 4
    d.text((24, y), "Positions are read from the screen photos. The red bodies on the belts are test bottles.", fill=GREY, font=F(23))
    c = c.crop((0, 0, W, y + 44))
    c.save(OUT, quality=90); print(OUT, c.size)

if __name__ == "__main__":
    main()
