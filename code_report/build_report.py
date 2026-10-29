"""Turns files.json (from extract.py) into the readable report: CODE_REPORT.html, code_files.csv, code_folders.csv.
Nothing here changes any project file."""
import collections
import csv
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
files = json.load(open(os.path.join(HERE, "files.json")))
import extract  # for the folder list

FOLDER_PATHS = {fid: p for fid, p, *_ in extract.FOLDERS}
HOME = os.path.expanduser("~")

# ---------------------------------------------------------------------------------------------- hand-written folder notes
# status: current | frozen | copy | old | tool
META = {
    "F01": dict(name="Bottle Machine 64 app (new product)", family="Current product", status="current", machine="Bottle Machine 64 (rotary-disk unscrambler) + 10-part Mini Sorter test machine",
                what="The per-machine app being built now: the client uploads a STEP assembly + a BOM, the app checks them (exact matching, no guessing), asks you to confirm part types and drive links and to type the numbers, then builds a wireframe, one folder of generated code per part, simulated fault-current tables and a rulebook. The code is generic: the machine is only the input.",
                run="cd bottle_machine_64 && .venv/bin/python app/server.py  ->  http://localhost:8792   (Formula Flow dashboard: /flow?name=mini_sorter)",
                read=[("engine/builder.py", "The conductor: analyze() reads the files, validate() lists anything missing, build() writes the project folders and runs the simulations."),
                      ("app/server.py", "The web routes, one per screen. It only moves data; all logic is in engine/."),
                      ("engine/step_geometry.py", "STEP file -> parts with outline edges (uses the cascadio/OpenCascade library)."),
                      ("engine/bom_reader.py", "Reads the BOM (CSV/Excel) and checks the required columns."),
                      ("engine/matching.py", "Pairs STEP parts with BOM rows by exact part number only."),
                      ("engine/part_types.py", "The part-type table: which words suggest which type, what each type is asked, which load it adds."),
                      ("engine/linking.py", "What drives what, and how load passes from part to part."),
                      ("engine/formula_pack.py", "The 7 stock formulas a project is built from."),
                      ("engine/strict_solver.py", "The zero-guess solver: stops and reports what is missing."),
                      ("engine/runtime.py", "apply(): the only way a number is computed. Also the motor model and the per-part simulation."),
                      ("engine/live_match.py", "Extra current on a motor -> which parts could explain it -> smallest area."),
                      ("engine/rulebook.py", "Writes rulebook.json: fine / elevated / warning / critical ranges."),
                      ("engine/flow_trace.py", "Step-by-step trace used by the Formula Flow dashboard."),
                      ("app/static/index.html", "The 6-step screen flow and the 3D viewer."),
                      ("app/static/flow.html", "The Formula Flow dashboard."),
                      ("dev_checks/check_zero_guess.py", "Internal checks that the app refuses to guess."),
                      ("validation/validate_gear_prototype.py", "Physics check against the gear rig's real readings.")],
                note="Not listed here: the generated per-part code (projects/*/machine/**/part_code.py), the virtual environments, the STEP test files, and the copy of the gear prototype (see F14)."),
    "F02": dict(name="Formula candidates (staging)", family="Current product", status="current", machine="Machine-independent",
                what="Stages cited formulas (OpenStax/Wikipedia) outside the engine: checks units with sympy, removes ones already in the engine, writes pilot_100.json/csv.", run="python3 build_pilot.py", read=[("build_pilot.py", "The whole tool.")]),
    "F03": dict(name="Core formula engine (Yanthros Formula Brain)", family="Core engine", status="current", machine="Machine-independent: 333 formulas in 33 physics domains",
                what="The physics formula library and the service that chains formulas together. formulas.py holds the sympy symbols and the FORMULAS dictionary; brain.py builds a graph of which variables connect through which formulas and finds a path from known values to a target.",
                run="python3 brain.py  (service on port 5051)  -  warning: build_graph() rewrites brain_graph.json",
                read=[("formulas.py", "Symbols (top), FORMULAS dict (about line 390), FORMULA_DOMAINS (about line 923), mynja() solver helper (about line 1108)."),
                      ("brain.py", "build_graph (l.94), solve_path (l.270: wave/forward chaining), Flask routes /brain/understand, /brain/solve, /brain/extend, /brain/status."),
                      ("export_warehouse.py", "Exports each formula as a JSON file per domain into warehouse/ (the warehouse folders are currently empty).")],
                note="333 formulas and 33 domains were counted by importing formulas.py. Data files (brain_graph.json, esp32_specs.json) are not code and are not listed."),
    "F04": dict(name="YANTHROS CORE (copy of the engine)", family="Core engine", status="copy", machine="Machine-independent", copy_of="F03",
                what="Second copy of brain.py + formulas.py from Sep 17-18 (same files as F03). Its brain_graph.json is a different, older, larger file.", run="same as F03", read=[]),
    "F05": dict(name="PROTOTYPE_BACKUP: engine copy", family="Core engine", status="frozen", machine="Machine-independent", copy_of="F03",
                what="Frozen copy taken 2026-10-03 before the zero-guess work (see PROTOTYPE_BACKUP_2026-10-03/README.txt). Same disk as the original.", run="same as F03", read=[]),
    "F06": dict(name="License prototype: Software Packet Builder + dashboard", family="Packet builder prototype", status="old", machine="Machine-independent (demo used a bottle-machine component subset)",
                what="The first version of the product idea: a GUI that takes the minimum machine data (or a STEP file), selects a formula subset, generates a current-signature database, and wraps it in a signed license so the client's app can unlock only what was paid for. Also the local admin dashboard for the core engine (graph explorer, solver). Contains the ESP32 defaults and assumed constants that the new app removed.",
                run="python3 packet_builder_app.py   |   python3 dashboard/app.py  (dashboard on port 5090)",
                read=[("packet_builder_app.py", "The GUI (the tool we run per machine)."),
                      ("step_parser.py", "Lightweight STEP reader (no CAD kernel)."),
                      ("formula_selector.py", "Minimum data in -> formula subset out."),
                      ("fault_sweep_generator.py", "Builds the current-signature database (contains the assumed constants)."),
                      ("crypto_core.py", "Signing/verification primitives."),
                      ("issue_key.py", "Our side: issue a key file for a customer."),
                      ("unlock.py", "Their side: check the key at start-up."),
                      ("demo.py", "Five scenarios proving the lock works."),
                      ("dashboard/app.py", "Admin dashboard server."),
                      ("twin_viewer_build/twin_viewer_app.py", "The 'executable file' piece: the twin viewer.")],
                note="Not listed: build/, dist/ (generated app bundles), keys/ (signing keys), out/, step_test/."),
    "F07": dict(name="PROTOTYPE_BACKUP: license prototype copy", family="Packet builder prototype", status="frozen", machine="Machine-independent", copy_of="F06",
                what="Frozen copy of F06 from 2026-10-03.", run="same as F06", read=[]),
    "F08": dict(name="Servo Piston Filler twin", family="Digital twins", status="old", machine="Volumetric Technologies Servo Piston Filler / Depositor",
                what="A 3D wireframe twin of one filling machine, built by hand from the formula engine: build_twin.py computes values into twin_data.json, index.html shows them.", run="python3 build_twin.py, then open index.html (or python3 -m http.server)",
                read=[("build_twin.py", "Computes the twin's numbers by calling the brain."), ("index.html", "The 3D viewer."), ("brain_launch.py", "Starts an isolated brain on port 5052.")]),
    "F09": dict(name="Bottle unscrambler schematic twin", family="Digital twins", status="old", machine="Bottle unscrambler (schematic)",
                what="A single self-contained page drawing the unscrambler as a schematic 3D twin.", run="open index.html", read=[("index.html", "The whole page.")]),
    "F10": dict(name="Twin Forge", family="Digital twins", status="old", machine="Any machine; research examples: centrifugal pump (Goulds/Xylem NPE), ROBOWAY gearmotor",
                what="The Servo Piston Filler process turned repeatable: take a machine, drive the formula brain, produce a verified 3D twin. engine/ is the template, research/ holds two worked examples, pipeline-ui/ is a React page that shows the pipeline steps.",
                run="see twin-forge/README.md", read=[("brain_launch.py", "Starts the brain."), ("pipeline-ui/src/pipeline.js", "The pipeline modelled as data."), ("engine/template/index.html", "The twin viewer template.")]),
    "F11": dict(name="150 RPM gear system (the prototype that worked live)", family="Gear-motor prototype", status="frozen", machine="150 RPM metal internal gearbox, 12 V motor, ESP32 + INA228",
                what="Flask app (port 5053): 3D twin, physics formula chain, calibration, and the live 'Part Interruption' detection that reads motor current from an ESP32 + INA228 over USB serial and names which gear was touched.",
                run="pip install -r requirements.txt && python3 gearsystem150_app.py",
                read=[("gearsystem150_app.py", "Entry point and wiring."), ("gearsystem/detection/acquisition.py", "Reads the ESP32 over serial."), ("gearsystem/detection/signal_processing.py", "Raw blocks -> smoothed, classified live state."),
                      ("gearsystem/detection/live_state.py", "The measured current bands per gear (Red/Green/Blue/Yellow)."), ("gearsystem/physics/gear_train.py", "Gear kinematics and the RK4 dynamics model (found structurally wrong; see validation)."),
                      ("gearsystem/signature/dynamic.py", "Time-domain touch transients."), ("gearsystem/calibration/search.py", "The calibration loop."), ("esp32_ina228_reader/src/main.cpp", "The sensor firmware."),
                      ("gearsystem/api/templates.py", "2,666 lines of inline page HTML/JS (the UI).")],
                note="Git remote: the folder's .git points at the old 'yanthros' repo."),
    "F12": dict(name="GearTwinLive iPad app", family="Gear-motor prototype", status="frozen", machine="150 RPM gear rig", what="Standalone Swift app: talks to the ESP32 over Bluetooth, detects touches on-device, shows the 3D twin. Currently runs against a built-in simulated sensor. Paused.", run="open GearTwinLive.xcodeproj in Xcode",
                read=[("GearTwinLive/Detection/PartInterruptionDetector.swift", "Port of the Python detection."), ("GearTwinLive/BLE/GearSensorManager.swift", "Real Bluetooth path."), ("GearTwinLive/BLE/SimulatedSensorSource.swift", "Fake sensor.")]),
    "F13": dict(name="GearTwinDashboard iPad app", family="Gear-motor prototype", status="frozen", machine="150 RPM gear rig", what="Minimal SwiftUI shell: a full-screen web view pointed at the Flask dashboard plus an address settings sheet. Paused.", run="open GearTwinDashboard.xcodeproj in Xcode", read=[]),
    "F14": dict(name="Gear prototype read-only copy (inside bottle_machine_64)", family="Gear-motor prototype", status="copy", machine="150 RPM gear rig", copy_of="F11",
                what="Copy made on 2026-10-06 so the new app's validation can read the framework without touching the original.", run="not run", read=[]),
    "F15": dict(name="Zinaata Android + backend + Dorus", family="Zinaata (phones)", status="old", machine="Phones (worked example: Samsung Galaxy M13)",
                what="The same method applied to consumer electronics: Android app (Kotlin) scans phone hardware, a Python backend (relays to Supabase) receives scans, the DORUSSS engine and an RL diagnosis pipeline analyse them, plus a browser prototype.",
                run="backend: python3 backend/server.py   |   RL: see rl_diagnosis/DORUSSS_REPORT.md",
                read=[("backend/server.py", "API that receives scans."), ("backend/dorus_engine.py", "The Dorus engine."), ("rl_diagnosis/env.py", "The RL environment."), ("rl_diagnosis/agent.py", "The agent."), ("rl_diagnosis/train.py", "Training.")], note="Git remote: zinaata-android (private). Excluded: Android build output, phone_data/, research/."),
    "F16": dict(name="Zinaata macOS app", family="Zinaata (phones)", status="old", machine="This Mac's own hardware", what="SwiftUI Mac app: chat UI, Mac hardware snapshot via system tools, optional AI API client; scripts/watcher.sh runs as a background agent.", run="build.sh", read=[("Sources/Zinaata/Services/MacHardwareService.swift", "Reads this Mac's hardware."), ("scripts/watcher.sh", "Background watcher.")]),
    "F17": dict(name="BMS-faulter (business management site)", family="Business", status="old", machine="Not a machine: accounts/transactions", what="Small React + Node app: accounts and transactions pages, database_schema.sql, server.js. Local only (no .git here; a GitHub repo of the same name exists).", run="npm install && npm start (not tested)", read=[("App.js", "Pages and routes."), ("pages/AccountsPage.js", "Accounts page.")]),
    "F18": dict(name="Yanthros_fresh (July 31 snapshot)", family="Old Yanthros", status="old", machine="150 RPM gear system, RS-775 DC motor + tyre demo, Cybertruck 130-size DC motor, ESP32",
                what="The old all-in-one Yanthros: the core engine plus per-machine files side by side. app.py alone is about 12,000 lines (routes for every machine). Identical to F19.", run="python3 app.py (not tested)",
                read=[("Yanthros/app.py", "The monolith: look at its route list first."), ("Yanthros/brain.py", "Older brain."), ("Yanthros/rs775_faults.py", "RS-775 motor fault signatures."), ("Yanthros/cybertruck_faults.py", "Cybertruck motor fault simulation.")], copy_of=None),
    "F19": dict(name="Archive copy of Yanthros_fresh", family="Old Yanthros", status="copy", machine="same as F18", copy_of="F18", what="Byte-for-byte copy of F18 (23 of 23 code files identical).", run="not run", read=[]),
    "F20": dict(name="Archive: YANTHROS (earliest)", family="Old Yanthros", status="old", machine="DC motor physics notes", what="One HTML page plus motor physics notes (markdown, not listed).", run="open index.html", read=[("index.html", "The page.")]),
    "F21": dict(name="Archive: YANTHROS v2", family="Old Yanthros", status="old", machine="150 RPM gear system, RS-775 DC motor + tyre demo, Cybertruck, ESP32",
                what="Later version of the old all-in-one. app.py is about 13,400 lines. Includes the BVS calibration engine, the 'Magenta' simulator and a React fault dashboard. Contains a file named openai.key (not opened by this report).", run="python3 app.py (not tested)",
                read=[("app.py", "Monolith."), ("bvs_engine.py", "Population-based calibration engine."), ("simulate.py", "Execution-intelligence simulator."), ("fault-dashboard/src/App.jsx", "React fault dashboard.")],
                note="Git remote: yanthros. SECURITY: a file called openai.key sits in this folder. This report did not read it. If it is a live key, rotate it before pushing this folder anywhere."),
    "F22": dict(name="FAULTER-EI (Nassenger 8 twin with agents)", family="Nassenger 8 line", status="old", machine="Konica Minolta Nassenger 8 industrial inkjet textile printer",
                what="First big twin of the printer: FastAPI WebSocket server, an agent layer (core/), formula pathfinder, and many UI versions (3D twin v1/v2 + dated backups, website, JARVIS console).", run="python3 run.py", read=[("server/main.py", "FastAPI WebSocket server."), ("core/agent_layer.py", "Agent layer."), ("ui/nassenger_3d_v2.html", "Latest 3D twin page.")], note="Git remote: FAULTER-EI."),
    "F23": dict(name="Archive: faulter (formula deck)", family="Old Yanthros", status="old", machine="Machine-independent", what="One HTML formula deck page.", run="open formula_deck.html", read=[("formula_deck.html", "The page.")]),
    "F24": dict(name="DIVINE: faulter-wireless", family="Nassenger 8 line", status="old", machine="Nassenger 8 textile printer", what="ESP32 WiFi sketch + dashboard_server.py + a nested copy of the 17 'worker' station pages (unwinder, feed, tensioning ... control).", run="flash faulter-wireless.ino; python3 dashboard_server.py", read=[("faulter-wireless.ino", "The ESP32 sketch."), ("dashboard_server.py", "Dashboard server.")]),
    "F25": dict(name="DIVINE: faulter (index page)", family="Nassenger 8 line", status="old", machine="Nassenger 8 / Faulter site", what="One index.html.", run="open index.html", read=[("index.html", "The page.")]),
    "F26": dict(name="DIVINE: faulter-software (Nassenger 8 neuro-symbolic twin)", family="Nassenger 8 line", status="old", machine="Nassenger 8 textile printer",
                what="One HTML page per printer station ('worker'): unwinder, feed, tensioning, flattening, carriage, printhead, ink supply, nozzle health, head height, capping, RIP, dryer, rewinder, belt washing, environmental, maintenance, control. Built from a shared template (about 45% of lines shared between pages).", run="open dashboard.html", read=[("dashboard.html", "Entry."), ("refactor_all.py", "Script that regenerated the pages."), ("worker1/worker1_unwinder.html", "Largest station page.")], note="Git remote: faulter-nassenger8."),
    "F27": dict(name="faulter-app (node-graph calculator)", family="Other tools", status="old", machine="Machine-independent", what="FastAPI backend + React flow editor where formula nodes are wired together and calculated.", run="python3 run.py (starts backend + Vite)", read=[("faulter-app/backend/main.py", "Calculate API."), ("faulter-app/frontend/src/App.jsx", "Editor.")]),
    "F28": dict(name="dumpyard/faulter: AC-motor twin + Node-RED universal twin", family="Nassenger 8 line", status="old", machine="AC motor; Nassenger 8; 'any machine' (EV bike, drone...)",
                what="Two experiments: ac-motor-digital-twin (backend + React) and nodered-digital-twin (Node-RED flows, a formula engine and a 'universal' engine for any machine type, JARVIS console). Node-RED default settings.js files are third-party defaults.", run="see nodered-digital-twin/README.md", read=[("nodered-digital-twin/lib/universal-engine.js", "Machine-agnostic engine."), ("nodered-digital-twin/lib/formula-engine.js", "Printer formula engine.")]),
    "F29": dict(name="Multi-agent LLM scripts (inside the BitNet folder)", family="Other tools", status="tool", machine="Unrelated to machines", what="Your own multi-agent/orchestrator scripts sitting inside a downloaded BitNet (bitnet.cpp) clone (upstream files excluded from this report).", run="python3 orchestrator_v2.py (not tested)", read=[("orchestrator_v2.py", "Latest orchestrator.")], note="The BitNet repository itself is third-party and is not reported."),
}

STATUS_LABEL = {"current": "Current", "frozen": "Frozen / paused", "copy": "Exact copy", "old": "Older version", "tool": "Other tool"}


def git_remote(path):
    p = path
    for _ in range(4):
        cfg = os.path.join(p, ".git", "config")
        if os.path.exists(cfg):
            for line in open(cfg, errors="ignore"):
                m = re.search(r"url\s*=\s*(\S+)", line)
                if m:
                    return m.group(1).replace("https://github.com/", "github.com/").replace(".git", "")
            return ""
        if os.path.abspath(p) in (HOME + "/Desktop", HOME, "/"):
            break
        p = os.path.dirname(p)
    return ""


by_folder = collections.defaultdict(list)
for f in files:
    by_folder[f["folder"]].append(f)

# local imports / used-by (python files only, same folder, unique stem)
for fid, fl in by_folder.items():
    stems = collections.defaultdict(list)
    for f in fl:
        if f["lang"] == "Python":
            stems[os.path.splitext(os.path.basename(f["rel"]))[0]].append(f)
    for f in fl:
        f["local_imports"] = []
        f["used_by"] = []
    for f in fl:
        if f["lang"] != "Python":
            continue
        for imp in f["imports"]:
            if imp in stems and len(stems[imp]) == 1 and stems[imp][0] is not f:
                f["local_imports"].append(imp)
                stems[imp][0]["used_by"].append(os.path.splitext(os.path.basename(f["rel"]))[0])
for f in files:
    f["ext_imports"] = [i for i in f["imports"] if i not in f.get("local_imports", [])]

folders = []
for fid, path, *_ in extract.FOLDERS:
    fl = by_folder.get(fid, [])
    m = META[fid]
    langs = collections.Counter(f["lang"] for f in fl)
    read = [(r, why) for r, why in m.get("read", []) if any(f["rel"] == r or f["rel"].endswith(r) for f in fl)]
    note = m.get("note", "")
    folders.append({
        "id": fid, "path": path, "short": path.replace(HOME, "~"), "name": m["name"], "family": m["family"], "status": m["status"], "status_label": STATUS_LABEL[m["status"]],
        "machine": m["machine"], "what": m["what"], "run": m["run"], "read": read, "note": note, "copy_of": m.get("copy_of"),
        "files": len(fl), "lines": sum(f["lines"] for f in fl), "langs": ", ".join(f"{k} {v}" for k, v in langs.most_common(4)),
        "updated": max((f["mod"] for f in fl), default=""), "git": git_remote(path), "exists": os.path.exists(path),
        "undocumented": sum(1 for f in fl if not f["has_doc"]),
    })

# machine appearances
KEYS = {"Nassenger 8 (textile inkjet printer)": ["nassenger"], "150 RPM gear system": ["gearsystem", "gear system", "gear_train", "150rpm"],
        "RS-775 DC motor + tyre": ["rs775"], "Cybertruck DC motor": ["cybertruck"], "Servo Piston Filler": ["servo piston"], "Bottle machine / unscrambler": ["bottle", "unscrambler", "mini sorter", "mini_sorter"]}
machines = []
for label, keys in KEYS.items():
    hit = collections.Counter()
    for f in files:
        hay = (f["rel"] + " " + f["desc"]).lower()
        if any(k in hay for k in keys):
            hit[f["folder"]] += 1
    machines.append({"machine": label, "places": [{"id": k, "name": META[k]["name"], "files": v} for k, v in sorted(hit.items())]})

# exact duplicate groups
groups = collections.defaultdict(list)
for f in files:
    if f["dup"]:
        groups[f["dup"]["of"]].append({"in": f["folder"], "rel": f["rel"], "kind": f["dup"]["kind"], "pct": f["dup"]["pct"]})
dups = [{"original": k, "copies": v} for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))]

payload = {"generated": time.strftime("%Y-%m-%d %H:%M"), "folders": folders, "files": files, "machines": machines, "dups": dups,
           "totals": {"folders": len(folders), "files": len(files), "lines": sum(f["lines"] for f in files)}}

# ------------------------------------------------------------------------------------------------ CSVs
with open(os.path.join(HERE, "code_folders.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "name", "status", "family", "location", "machine", "what it is", "how to run", "files", "lines", "languages", "last changed", "git remote", "copy of"])
    for f in folders:
        w.writerow([f["id"], f["name"], f["status_label"], f["family"], f["path"], f["machine"], f["what"], f["run"], f["files"], f["lines"], f["langs"], f["updated"], f["git"], f["copy_of"] or ""])
with open(os.path.join(HERE, "code_files.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["folder id", "folder", "file (relative)", "full path", "language", "lines", "size KB", "last changed", "what it does (from the file's own docstring/comment/title)", "entry / how it runs", "duplicate of", "main definitions (name:line)", "web routes", "imports from other files in the folder", "external libraries", "used by"])
    names = {f["id"]: f["name"] for f in folders}
    for f in files:
        defs = "; ".join(f"{d['n']}:{d['l']}" for d in f["defs"][:25])
        routes = "; ".join(f"{r['m']} {r['p']}" for r in f["routes"][:25])
        dup = f"{f['dup']['kind']} {f['dup']['pct']}% of {f['dup']['of']}" if f["dup"] else ""
        w.writerow([f["folder"], names[f["folder"]], f["rel"], f["abs"], f["lang"], f["lines"], f["kb"], f["mod"], f["desc"], "; ".join(f["entry"]), dup, defs, routes,
                    ", ".join(f["local_imports"]), ", ".join(f["ext_imports"][:15]), ", ".join(sorted(set(f["used_by"])))])

# ------------------------------------------------------------------------------------------------ HTML
tmpl = open(os.path.join(HERE, "report_template.html")).read()
data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
open(os.path.join(HERE, "CODE_REPORT.html"), "w").write(tmpl.replace("/*__DATA__*/null", data))
print("folders", len(folders), "files", len(files), "html bytes", os.path.getsize(os.path.join(HERE, "CODE_REPORT.html")))
