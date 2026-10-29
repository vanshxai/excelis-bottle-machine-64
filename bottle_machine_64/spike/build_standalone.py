"""Bundle viewer.html + three.js + wireframe JSON files into ONE self-contained html
(double-click to open, no server). Usage: python build_standalone.py out.html a.wire.json b.wire.json ..."""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
files = sys.argv[2:]
html = open(os.path.join(here, "viewer.html"), encoding="utf-8").read()
three = open(os.path.join(here, "vendor", "three.min.js"), encoding="utf-8").read()

data = {}
for f in files:
    d = json.load(open(f))
    data[os.path.basename(f)] = d

opts = "".join(f'<option value="{k}">{v["source"]} - {v["part_count"]} parts</option>' for k, v in data.items())
start = html.index('<select id="file">')
end = html.index("</select>", start) + len("</select>")
html = html[:start] + f'<select id="file">{opts}</select>' + html[end:]
html = html.replace('<script src="vendor/three.min.js"></script>', "<script>" + three + "</script>\n<script>window.DATA=" + json.dumps(data) + ";</script>")
html = html.replace("await (await fetch(fn)).json()", "window.DATA[fn]")
first = next(iter(data))
html = html.replace("load('as1-oc-214.wire.json')", f"load('{first}')")
open(out, "w", encoding="utf-8").write(html)
print(out, round(os.path.getsize(out) / 1e6, 2), "MB")
