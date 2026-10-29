"""Reads every code file in the listed project folders and records what is in it (no file is changed).
Only structure is recorded: docstring/leading comment, functions, classes, routes, imports, entry points."""
import ast
import collections
import hashlib
import json
import os
import re
import sys
import time

HOME = os.path.expanduser("~")
D, DL, DOC = HOME + "/Desktop", HOME + "/Downloads", HOME + "/Documents"
AR = D + "/Archive - older projects"
EX = D + "/excelis"

# (id, path, extra_exclude_dirs, extra_exclude_files)
FOLDERS = [
    ("F01", EX + "/bottle_machine_64", {"projects", "ext"}, set()),
    ("F02", EX + "/formula_candidates", set(), set()),
    ("F03", D + "/faulter-formula-brain", set(), set()),
    ("F04", D + "/YANTHROS CORE", set(), set()),
    ("F05", EX + "/PROTOTYPE_BACKUP_2026-10-03/faulter-formula-brain", set(), set()),
    ("F06", EX + "/license_prototype", {"build", "dist", "out", "keys", "step_test"}, set()),
    ("F07", EX + "/PROTOTYPE_BACKUP_2026-10-03/license_prototype", {"build", "dist", "out", "keys", "step_test"}, set()),
    ("F08", EX + "/twin", {"vendor"}, set()),
    ("F09", EX + "/bottle_twin", {"vendor"}, set()),
    ("F10", D + "/twin-forge", {"vendor"}, set()),
    ("F11", D + "/150rpm gear motor prototype/Vansh/150rpm gear system", set(), set()),
    ("F12", D + "/150rpm gear motor prototype/Vansh/GearTwinLive-iPad", {"dist"}, set()),
    ("F13", D + "/150rpm gear motor prototype/Vansh/GearTwinDashboard-iPad", set(), set()),
    ("F14", EX + "/bottle_machine_64/reference/gear_prototype", set(), set()),
    ("F15", D + "/ZinaataAndroid", {"phone_data", "research", "build", "static"}, set()),
    ("F16", D + "/Zinaata", {"dist", "Resources"}, set()),
    ("F17", DOC + "/BMS-faulter", set(), set()),
    ("F18", DL + "/Yanthros_fresh", set(), set()),
    ("F19", AR + "/untitled folder/150rpm motor prototype", set(), set()),
    ("F20", AR + "/YANTHROS", set(), set()),
    ("F21", AR + "/YANTHROS v2", {"archive"}, set()),
    ("F22", AR + "/FAULTER-EI", set(), set()),
    ("F23", AR + "/faulter", set(), set()),
    ("F24", AR + "/DIVINE INDUSTRIES/faulter-wireless", set(), set()),
    ("F25", AR + "/DIVINE INDUSTRIES/faulter", set(), set()),
    ("F26", AR + "/DIVINE INDUSTRIES/faulter-software", set(), set()),
    ("F27", AR + "/dumpyard/faulter-software", set(), set()),
    ("F28", AR + "/dumpyard/faulter", {"BitNet"}, set()),
    ("F29", AR + "/dumpyard/faulter/BitNet", {"3rdparty", "build", "gpu", "include", "src", "utils", "preset_kernels", "assets", "docs", "media", "models", "logs", "__pycache__"},
     {"setup_env.py", "run_inference.py", "run_inference_server.py", "generate-dummy-bitnet-model.py", "e2e_benchmark.py"}),
]
EXC_ALWAYS = {".venv", ".venv_gen", "node_modules", "__pycache__", ".git", ".build", "DerivedData", "Pods", "site-packages", ".pio", ".gradle", ".idea", ".github", "venv"}
EXT = {".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".jsx": "JavaScript (React)", ".ts": "TypeScript", ".tsx": "TypeScript (React)",
       ".html": "HTML", ".ino": "Arduino (ESP32)", ".cpp": "C++", ".c": "C", ".h": "C/C++ header", ".swift": "Swift", ".kt": "Kotlin", ".java": "Java",
       ".cs": "C#", ".sh": "Shell"}
STD = set(sys.stdlib_module_names)


def first_para(s, n=300):
    s = " ".join((s or "").strip().split("\n\n")[0].split())
    return s if len(s) <= n else s[: n - 1] + "…"


def lead_comment(text, lang):
    lines = text.splitlines()[:40]
    out = []
    if lang == "Python":
        for l in lines:
            if l.startswith("#!") or not l.strip():
                if out:
                    break
                continue
            if l.lstrip().startswith("#"):
                out.append(l.lstrip("# ").rstrip())
            else:
                break
    else:
        t = text.lstrip()
        m = re.match(r"/\*+\s*(.*?)\*/", t, re.S) or None
        if m:
            out = [re.sub(r"^\s*\*\s?", "", x).strip() for x in m.group(1).splitlines()]
        else:
            for l in lines:
                if l.strip().startswith("//"):
                    out.append(l.strip().lstrip("/ ").rstrip())
                elif not l.strip() and not out:
                    continue
                else:
                    if out:
                        break
                    if l.strip().startswith("<!--"):
                        break
    return first_para(" ".join(x for x in out if x), 300)


def py_info(text):
    info = {"defs": [], "routes": [], "imports": [], "entry": [], "desc": "", "has_doc": False}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        info["desc"] = "(file could not be parsed as Python 3)"
        return info
    doc = ast.get_docstring(tree)
    if doc:
        info["desc"] = first_para(doc)
        info["has_doc"] = True
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    info["imports"] = sorted(m for m in mods if m not in STD)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            d = ast.get_docstring(node)
            info["defs"].append({"k": "def", "n": node.name, "l": node.lineno, "d": first_para(d, 110) if d else ""})
        elif isinstance(node, ast.ClassDef):
            d = ast.get_docstring(node)
            meths = [b.name for b in node.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))]
            info["defs"].append({"k": "class", "n": node.name, "l": node.lineno, "d": first_para(d, 110) if d else "", "m": len(meths)})
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                call = dec if isinstance(dec, ast.Call) else None
                f = call.func if call else dec
                if isinstance(f, ast.Attribute) and f.attr in ("route", "get", "post", "put", "delete", "websocket") and call and call.args:
                    a0 = call.args[0]
                    if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                        meth = f.attr.upper() if f.attr != "route" else "ANY"
                        for kw in call.keywords:
                            if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                                meth = "/".join(e.value for e in kw.value.elts if isinstance(e, ast.Constant))
                        info["routes"].append({"p": a0.value, "m": meth, "l": node.lineno, "f": node.name})
    if re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]", text):
        info["entry"].append("runs as a script (has a __main__ block)")
    if re.search(r"\bFlask\(", text):
        info["entry"].append("Flask web server")
    if "http.server" in text or "HTTPServer" in text:
        info["entry"].append("simple HTTP server")
    if "argparse" in text:
        info["entry"].append("takes command-line arguments")
    if not info["desc"]:
        lc = lead_comment(text, "Python")
        if lc:
            info["desc"] = lc
            info["has_doc"] = True
    if not info["desc"]:
        names = [d["n"] for d in info["defs"] if d["k"] == "def"][:8]
        cl = [d["n"] for d in info["defs"] if d["k"] == "class"][:5]
        bits = []
        if cl:
            bits.append("classes " + ", ".join(cl))
        if names:
            bits.append("functions " + ", ".join(names))
        info["desc"] = ("(no description in the file) Defines " + "; ".join(bits)) if bits else "(no description in the file)"
    return info


def html_info(text):
    info = {"defs": [], "routes": [], "imports": [], "entry": ["web page (open in a browser)"], "desc": "", "has_doc": False}
    t = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    title = " ".join(t.group(1).split()) if t else ""
    c = re.search(r"<!--(.*?)-->", text, re.S)
    com = first_para(c.group(1), 200) if c and len(c.group(1).strip()) > 15 else ""
    srcs = re.findall(r"<script[^>]+src=[\"']([^\"']+)", text, re.I)
    info["imports"] = sorted({s.split("/")[-1].split("?")[0] for s in srcs})[:12]
    funcs = re.findall(r"function\s+([A-Za-z_]\w*)\s*\(", text) + re.findall(r"(?:const|let|var)\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>", text)
    seen = []
    for f in funcs:
        if f not in seen:
            seen.append(f)
    for f in seen[:40]:
        m = re.search(r"function\s+" + re.escape(f) + r"\s*\(", text)
        ln = text[: m.start()].count("\n") + 1 if m else 0
        info["defs"].append({"k": "js", "n": f, "l": ln, "d": ""})
    api = sorted(set(re.findall(r"fetch\(\s*[`'\"](/?[^`'\"?]*)", text)))[:10]
    api = [a for a in api if a]
    desc = title or "(no <title>)"
    if com:
        desc += " - " + com
        info["has_doc"] = True
    if api:
        desc += " | calls: " + ", ".join(api)
    info["desc"] = first_para(desc, 320)
    info["has_doc"] = info["has_doc"] or bool(title)
    return info


def js_info(text, lang):
    info = {"defs": [], "routes": [], "imports": [], "entry": [], "desc": "", "has_doc": False}
    lc = lead_comment(text, lang)
    if lc:
        info["desc"] = lc
        info["has_doc"] = True
    reqs = re.findall(r"require\(['\"]([^'\"]+)", text) + re.findall(r"from\s+['\"]([^'\"]+)['\"]", text)
    info["imports"] = sorted({r for r in reqs if not r.startswith(".")})[:12]
    for m in re.finditer(r"\b(?:app|router)\.(get|post|put|delete|use)\(\s*['\"]([^'\"]+)", text):
        info["routes"].append({"p": m.group(2), "m": m.group(1).upper(), "l": text[: m.start()].count("\n") + 1, "f": ""})
    names = re.findall(r"(?:export\s+default\s+)?function\s+([A-Za-z_]\w*)", text)
    names += re.findall(r"(?:const|let)\s+([A-Z]\w*)\s*=\s*(?:\([^)]*\)|\w+)\s*=>", text)
    seen = []
    for f in names:
        if f not in seen:
            seen.append(f)
    for f in seen[:30]:
        m = re.search(r"(?:function\s+|(?:const|let)\s+)" + re.escape(f) + r"\b", text)
        info["defs"].append({"k": "js", "n": f, "l": text[: m.start()].count("\n") + 1 if m else 0, "d": ""})
    if "express" in info["imports"]:
        info["entry"].append("Node/Express server")
    if "react" in info["imports"]:
        info["entry"].append("React component(s)")
    if not info["desc"]:
        n = [d["n"] for d in info["defs"]][:8]
        info["desc"] = ("(no description in the file) Defines " + ", ".join(n)) if n else "(no description in the file)"
    return info


def c_info(text, lang):
    info = {"defs": [], "routes": [], "imports": [], "entry": [], "desc": "", "has_doc": False}
    lc = lead_comment(text, lang)
    if lc:
        info["desc"] = lc
        info["has_doc"] = True
    info["imports"] = sorted(set(re.findall(r"#include\s*[<\"]([^>\"]+)", text)))[:14]
    for m in re.finditer(r"^\s*(?:static\s+)?(?:void|int|float|double|bool|uint\w+|String|char\s*\*?|size_t)\s+([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{", text, re.M):
        info["defs"].append({"k": "fn", "n": m.group(1), "l": text[: m.start()].count("\n") + 1, "d": ""})
    if re.search(r"void\s+setup\s*\(", text) and re.search(r"void\s+loop\s*\(", text):
        info["entry"].append("Arduino sketch (setup/loop) - flash to the board")
    bauds = re.findall(r"Serial\.begin\((\d+)", text)
    if bauds:
        info["entry"].append("serial baud " + "/".join(sorted(set(bauds))))
    hints = []
    for k in ("INA228", "INA229", "ACS712", "Wire.", "WiFi", "BLE", "WebServer", "ADS1115", "esp_now", "AsyncWebServer"):
        if k in text:
            hints.append(k.rstrip("."))
    if hints:
        info["entry"].append("uses: " + ", ".join(hints))
    if not info["desc"]:
        n = [d["n"] for d in info["defs"]][:8]
        info["desc"] = ("(no description in the file) Defines " + ", ".join(n)) if n else "(no description in the file)"
    return info


def swift_info(text):
    info = {"defs": [], "routes": [], "imports": [], "entry": [], "desc": "", "has_doc": False}
    lc = lead_comment(text, "Swift")
    if lc and not lc.lower().startswith("created by"):
        info["desc"] = lc
        info["has_doc"] = True
    info["imports"] = sorted(set(re.findall(r"^import\s+(\w+)", text, re.M)))
    for m in re.finditer(r"^\s*(?:final\s+|public\s+|private\s+|fileprivate\s+)*(struct|class|enum|protocol|actor)\s+(\w+)", text, re.M):
        info["defs"].append({"k": m.group(1), "n": m.group(2), "l": text[: m.start()].count("\n") + 1, "d": ""})
    if "@main" in text:
        info["entry"].append("app entry point (@main)")
    if not info["desc"]:
        n = [d["n"] for d in info["defs"]][:8]
        info["desc"] = ("(no description in the file) Defines " + ", ".join(n)) if n else "(no description in the file)"
    return info


def kt_info(text, lang):
    info = {"defs": [], "routes": [], "imports": [], "entry": [], "desc": "", "has_doc": False}
    lc = lead_comment(text, lang)
    if lc:
        info["desc"] = lc
        info["has_doc"] = True
    info["imports"] = sorted({m.split(".")[0] + "." + m.split(".")[1] if "." in m else m for m in re.findall(r"^import\s+([\w.]+)", text, re.M)})[:10]
    for m in re.finditer(r"^\s*(?:(?:public|private|internal|data|sealed|open|abstract|final|static)\s+)*(class|object|interface|enum class)\s+(\w+)", text, re.M):
        info["defs"].append({"k": m.group(1), "n": m.group(2), "l": text[: m.start()].count("\n") + 1, "d": ""})
    nfun = len(re.findall(r"^\s*(?:override\s+|private\s+|suspend\s+)*fun\s+\w+", text, re.M)) if lang == "Kotlin" else 0
    if nfun:
        info["entry"].append(f"{nfun} functions")
    if "AndroidManifest" in text or "Activity" in text and "onCreate" in text:
        info["entry"].append("Android screen/activity")
    if not info["desc"]:
        n = [d["n"] for d in info["defs"]][:8]
        info["desc"] = ("(no description in the file) Defines " + ", ".join(n)) if n else "(no description in the file)"
    return info


def sh_info(text):
    info = {"defs": [], "routes": [], "imports": [], "entry": ["shell script"], "desc": "", "has_doc": False}
    lc = lead_comment(text, "Python")
    info["desc"] = lc or "(no description in the file)"
    info["has_doc"] = bool(lc)
    return info


def analyse(path, lang):
    text = open(path, encoding="utf-8", errors="ignore").read()
    if lang == "Python":
        i = py_info(text)
    elif lang == "HTML":
        i = html_info(text)
    elif lang.startswith(("JavaScript", "TypeScript")):
        i = js_info(text, lang)
    elif lang in ("Arduino (ESP32)", "C++", "C", "C/C++ header"):
        i = c_info(text, lang)
    elif lang == "Swift":
        i = swift_info(text)
    elif lang in ("Kotlin", "Java", "C#"):
        i = kt_info(text, lang)
    else:
        i = sh_info(text)
    return text, i


def jaccard_lines(a, b):
    A = {l.strip() for l in a.splitlines() if l.strip()}
    B = {l.strip() for l in b.splitlines() if l.strip()}
    return len(A & B) / len(A | B) if A and B else 0.0


def run():
    files = []
    texts = {}
    for fid, root, xdirs, xfiles in FOLDERS:
        if not os.path.exists(root):
            print("MISSING", fid, root)
            continue
        for dp, dn, fn in os.walk(root):
            dn[:] = sorted(d for d in dn if d not in EXC_ALWAYS and d not in xdirs)
            if fid == "F01" and os.path.relpath(dp, root).startswith(("reference", "spike/ext", "spike" + os.sep + "ext")):
                dn[:] = []
                continue
            if fid == "F28" and os.path.abspath(dp).startswith(AR + "/dumpyard/faulter/BitNet"):
                dn[:] = []
                continue
            for f in sorted(fn):
                ext = os.path.splitext(f)[1].lower()
                if ext not in EXT or ".min." in f or f in xfiles or f in ("three.min.js", "three.module.js", "OrbitControls.js", "problems-report.html"):
                    continue
                p = os.path.join(dp, f)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if st.st_size > 3_000_000 or st.st_size < 10:
                    continue
                lang = EXT[ext]
                try:
                    text, info = analyse(p, lang)
                except Exception as e:  # keep going, record the problem
                    text, info = "", {"defs": [], "routes": [], "imports": [], "entry": [], "desc": f"(could not read: {e})", "has_doc": False}
                rel = os.path.relpath(p, root)
                files.append({"folder": fid, "rel": rel, "abs": p, "lang": lang, "lines": text.count("\n") + 1, "kb": round(st.st_size / 1024, 1),
                              "mod": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime)), "sha": hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest(), **info})
                texts[p] = text
    # duplicates: first folder in FOLDERS order is the original
    order = {fid: i for i, (fid, *_r) in enumerate(FOLDERS)}
    seen = {}
    byname = collections.defaultdict(list)
    for f in sorted(files, key=lambda x: order[x["folder"]]):
        f["dup"] = None
        if f["sha"] in seen:
            o = seen[f["sha"]]
            f["dup"] = {"kind": "exact", "of": o["folder"] + ":" + o["rel"], "pct": 100}
        else:
            seen[f["sha"]] = f
            base = os.path.basename(f["rel"])
            if f["lines"] >= 25:
                best = None
                for o in byname[base]:
                    if o["folder"] == f["folder"]:
                        continue
                    j = jaccard_lines(texts[f["abs"]], texts[o["abs"]])
                    if j >= 0.6 and (best is None or j > best[0]):
                        best = (j, o)
                if best:
                    f["dup"] = {"kind": "near", "of": best[1]["folder"] + ":" + best[1]["rel"], "pct": round(best[0] * 100)}
            byname[base].append(f)
    for f in files:
        f.pop("sha", None)
    return files


if __name__ == "__main__":
    fs = run()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files.json")
    json.dump(fs, open(out, "w"))
    c = collections.Counter(f["folder"] for f in fs)
    print(len(fs), "files")
    for fid, *_ in FOLDERS:
        print(fid, c.get(fid, 0))
