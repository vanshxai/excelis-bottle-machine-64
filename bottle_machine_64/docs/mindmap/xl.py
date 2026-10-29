"""Tiny Excalidraw file writer used only to draw the software mind maps (dev tool, not part of the product)."""
import json
import random
import uuid

from PIL import ImageFont

_F = {}


def _font(fs):
    if fs not in _F:
        _F[fs] = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", fs)
    return _F[fs]


def tw(s, fs, family=2):
    if family == 2:
        return _font(fs).getlength(s) * 1.04
    if family == 3:
        return 0.62 * fs * len(s)
    return 0.62 * fs * len(s)


def wrap(text, width, fs, family=2):
    out = []
    for para in text.split("\n"):
        if not para.strip():
            out.append("")
            continue
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if tw(t, fs, family) <= width or not line:
                line = t
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


KINDS = {  # fill, stroke
    "file": ("#dbe4ff", "#3b5bdb"),
    "auto": ("#e5dbff", "#6741d9"),
    "user": ("#ffe8cc", "#e8590c"),
    "store": ("#d3f9d8", "#2b8a3e"),
    "stop": ("#ffe3e3", "#c92a2a"),
    "plain": ("#f1f3f5", "#495057"),
}
BANDS = {"fine": "#8ce99a", "elevated": "#ffec99", "warning": "#ffd8a8", "critical": "#ffa8a8"}
INK = "#1e1e1e"


class Board:
    def __init__(self, seed=7):
        self.els = []
        self.rng = random.Random(seed)
        self.by_id = {}

    def _base(self, t, x, y, w, h, stroke, fill, sw=2, dashed=False, group=None, round_=True):
        e = {"id": uuid.uuid4().hex[:20], "type": t, "x": x, "y": y, "width": w, "height": h, "angle": 0,
             "strokeColor": stroke, "backgroundColor": fill, "fillStyle": "solid", "strokeWidth": sw,
             "strokeStyle": "dashed" if dashed else "solid", "roughness": 0, "opacity": 100,
             "groupIds": [group] if group else [], "frameId": None,
             "roundness": {"type": 3} if (round_ and t == "rectangle") else None,
             "seed": self.rng.randint(1, 2**31 - 1), "version": 1, "versionNonce": self.rng.randint(1, 2**31 - 1),
             "isDeleted": False, "boundElements": [], "updated": 1, "link": None, "locked": False}
        self.els.append(e)
        self.by_id[e["id"]] = e
        return e

    def rect(self, x, y, w, h, stroke, fill, sw=2, dashed=False, group=None, round_=True):
        return self._base("rectangle", x, y, w, h, stroke, fill, sw, dashed, group, round_)

    def text(self, x, y, s, fs=16, color=INK, family=2, align="left", group=None, width=None):
        lines = s.split("\n")
        w = width or max(tw(l, fs, family) for l in lines)
        h = len(lines) * fs * 1.25
        e = self._base("text", x, y, w, h, color, "transparent", 1, False, group)
        e.update({"text": s, "fontSize": fs, "fontFamily": family, "textAlign": align, "verticalAlign": "top",
                  "baseline": int(fs * 0.9), "containerId": None, "originalText": s, "lineHeight": 1.25, "autoResize": True})
        e["boundElements"] = None
        return e

    # ------------------------------------------------------------------ card
    def card(self, x, y, w, kind, title, body="", tag=None, fs_title=20, fs_body=15, pad=16, title_family=2,
             dashed=False, hub=False, min_h=0):
        fill, stroke = KINDS[kind]
        g = uuid.uuid4().hex[:12]
        inner = w - 2 * pad
        yy = y + pad
        parts = []
        if tag:
            parts.append(("tag", yy, tag))
            yy += 14 * 1.25 + 4
        tl = wrap(title, inner, fs_title, title_family)
        parts.append(("title", yy, "\n".join(tl)))
        yy += len(tl) * fs_title * 1.25 + (8 if body else 0)
        if body:
            bl = wrap(body, inner, fs_body)
            parts.append(("body", yy, "\n".join(bl)))
            yy += len(bl) * fs_body * 1.25
        h = max(yy + pad - y, min_h)
        if hub:
            r = self.rect(x, y, w, h, stroke, stroke, 2, dashed, g)
        else:
            r = self.rect(x, y, w, h, stroke, fill, 2, dashed, g)
        for k, ty, s in parts:
            if k == "tag":
                self.text(x + pad, ty, s, 14, stroke if not hub else "#ffffff", 3, group=g)
            elif k == "title":
                self.text(x + pad, ty, s, fs_title, "#ffffff" if hub else INK, title_family, group=g)
            else:
                self.text(x + pad, ty, s, fs_body, "#ffffff" if hub else "#343a40", 2, group=g)
        return {"id": r["id"], "x": x, "y": y, "w": w, "h": h, "kind": kind}

    def note(self, x, y, s, fs=15, color="#495057", width=None, family=2):
        t = self.text(x, y, s, fs, color, family, width=width)
        return {"id": t["id"], "x": x, "y": y, "w": t["width"], "h": t["height"]}

    # ------------------------------------------------------------------ arrows
    def arrow(self, a, b, mode="h", label=None, color="#495057", dashed=False, label_dx=0, label_dy=-22, elbow=True, fs=14):
        if mode == "h":
            x0, y0 = a["x"] + a["w"], a["y"] + a["h"] / 2
            x1, y1 = b["x"], b["y"] + b["h"] / 2
        elif mode == "v":
            x0, y0 = a["x"] + a["w"] / 2, a["y"] + a["h"]
            x1, y1 = b["x"] + b["w"] / 2, b["y"]
        elif mode == "vl":  # bottom of a to left-mid of b
            x0, y0 = a["x"] + a["w"] / 2, a["y"] + a["h"]
            x1, y1 = b["x"], b["y"] + b["h"] / 2
        else:
            raise ValueError(mode)
        dx, dy = x1 - x0, y1 - y0
        if mode == "h" and elbow and abs(dy) > 2:
            mx = dx / 2
            pts = [[0, 0], [mx, 0], [mx, dy], [dx, dy]]
        elif mode == "v" and elbow and abs(dx) > 2:
            my = dy / 2
            pts = [[0, 0], [0, my], [dx, my], [dx, dy]]
        elif mode == "vl":
            pts = [[0, 0], [0, dy], [dx, dy]]
        else:
            pts = [[0, 0], [dx, dy]]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        e = self._base("arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys), color, "transparent", 2, dashed, None, False)
        e.update({"points": pts, "lastCommittedPoint": None, "startArrowhead": None, "endArrowhead": "arrow",
                  "startBinding": {"elementId": a["id"], "focus": 0, "gap": 1},
                  "endBinding": {"elementId": b["id"], "focus": 0, "gap": 1}, "elbowed": False})
        for s in (a, b):
            self.by_id[s["id"]]["boundElements"].append({"id": e["id"], "type": "arrow"})
        if label:
            lx = x0 + (dx / 2 if mode != "h" or not elbow or abs(dy) <= 2 else dx / 2) + label_dx
            ly = y0 + (dy / 2 if mode != "h" or abs(dy) <= 2 else 0) + label_dy
            self.text(lx - tw(label, fs) / 2, ly, label, fs, color)
        return e

    def legend(self, x, y, items=("file", "auto", "user", "store", "stop")):
        names = {"file": "Client's file", "auto": "Software does it by itself", "user": "You confirm or type it",
                 "store": "Saved on disk", "stop": "Stops / not built yet"}
        self.text(x, y, "COLOUR KEY", 13, "#868e96", 2)
        yy = y + 24
        for k in items:
            fill, stroke = KINDS[k]
            self.rect(x, yy, 22, 22, stroke, fill, 2)
            self.text(x + 32, yy + 2, names[k], 15, "#343a40")
            yy += 32
        return yy

    def save(self, path):
        for e in self.els:
            if e["type"] != "text" and e["boundElements"] == []:
                e["boundElements"] = None
        doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": self.els,
               "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}
        with open(path, "w") as f:
            json.dump(doc, f)
