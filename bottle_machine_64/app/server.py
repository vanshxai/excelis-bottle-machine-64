"""
Local web app for the trial: upload -> check -> classify -> link -> inputs -> build -> result.
All logic lives in ../engine; this file only moves data between the page and the engine.
"""
import json
import os
import sys

from flask import Flask, jsonify, request, send_from_directory

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "engine"))

import bom_reader  # noqa: E402
import builder  # noqa: E402
import linking  # noqa: E402
import flow_trace  # noqa: E402
import live_match  # noqa: E402
import rulebook  # noqa: E402
import step_geometry  # noqa: E402
from part_types import TYPES  # noqa: E402

PROJECTS = os.path.join(ROOT, "projects")
UPLOAD = os.path.join(PROJECTS, "_upload")
TEST = os.path.join(ROOT, "testdata", "mini_sorter")
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"), static_url_path="/static")
STATE = {"analysis": None, "step": None, "bom": None}


def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/analyze")
def api_analyze():
    os.makedirs(UPLOAD, exist_ok=True)
    if request.form.get("use_test") == "1":
        step, bom = os.path.join(TEST, "mini_sorter.step"), os.path.join(TEST, "mini_sorter_bom.csv")
    else:
        fs, fb = request.files.get("step"), request.files.get("bom")
        if not fs or not fb:
            return err("Choose both files: the STEP file and the BOM spreadsheet.")
        step, bom = os.path.join(UPLOAD, "upload.step"), os.path.join(UPLOAD, "upload_bom" + os.path.splitext(fb.filename)[1].lower())
        fs.save(step)
        fb.save(bom)
    try:
        an = builder.analyze(step, bom)
    except (step_geometry.StepReadError, bom_reader.BomError) as e:
        return err(str(e))
    STATE.update(analysis=an, step=step, bom=bom)
    order = {r["part_number"]: i for i, r in enumerate(an["bom"]["rows"])}
    parts = sorted(an["parts"].values(), key=lambda p: order[p["part_number"]])
    return jsonify({
        "ok": True,
        "step": {"file": an["geometry"]["source"], "parts": an["geometry"]["part_count"]},
        "bom": {"rows": len(an["bom"]["rows"]), "columns": an["bom"]["columns_found"]},
        "match": {"ok": an["match"]["ok"], "problems": an["match"]["problems"], "matched": len(an["match"]["matched"])},
        "parts": [{k: p[k] for k in ("part_number", "description", "material", "section", "section_name", "suggested_type",
                                     "suggest_reason", "instances")} for p in parts],
        "types": [{"id": k, "label": v["label"], "kind": v["kind"]} for k, v in TYPES.items()],
        "test_files": request.form.get("use_test") == "1",
    })


@app.get("/api/geometry")
def api_geometry():
    if not STATE["analysis"]:
        return err("Upload files first.")
    return jsonify(STATE["analysis"]["geometry"])


@app.post("/api/links")
def api_links():
    an = STATE["analysis"]
    types = request.json["types"]
    typed = {pn: {"type": types[pn], "section": an["parts"][pn]["section"]} for pn in an["parts"] if types.get(pn) in TYPES}
    sug = linking.suggest_parents(typed)
    return jsonify({"suggest": {pn: {"parent": par, "reason": why} for pn, (par, why) in sug.items()},
                    "driven": [pn for pn, t in typed.items() if TYPES[t["type"]]["kind"] == "driven"]})


@app.post("/api/requirements")
def api_requirements():
    an = STATE["analysis"]
    d = request.json
    return jsonify(builder.requirements(an, d["types"], d.get("links", {})))


@app.get("/api/test_answers")
def api_test_answers():
    with open(os.path.join(TEST, "test_answers.json")) as f:
        return jsonify(json.load(f))


@app.post("/api/validate")
def api_validate():
    return jsonify({"problems": builder.validate(STATE["analysis"], request.json["answers"], request.json.get("upto"))})


@app.post("/api/build")
def api_build():
    d = request.json
    name = "".join(c for c in d.get("name", "mini_sorter") if c.isalnum() or c in "_-") or "project"
    log = []
    try:
        summary = builder.build(STATE["analysis"], d["answers"], os.path.join(PROJECTS, name), STATE["step"], STATE["bom"], progress=log.append)
    except builder.BuildError as e:
        return jsonify({"ok": False, "problems": e.problems})
    return jsonify({"ok": True, "name": name, "log": log, "summary": summary})


def _pdir(name):
    p = os.path.join(PROJECTS, "".join(c for c in name if c.isalnum() or c in "_-"))
    if not os.path.isdir(p):
        raise FileNotFoundError(name)
    return p


@app.get("/flow")
def flow_page():
    return send_from_directory(app.static_folder, "flow.html")


@app.post("/api/trace")
def api_trace():
    d = request.json
    try:
        return jsonify({"ok": True, **flow_trace.trace_part(_pdir(d["name"]), d["part"], d.get("effort"), d.get("overrides"))})
    except Exception as e:  # shown to the user in the dashboard
        return jsonify({"ok": False, "error": str(e)})


@app.get("/api/rulebook")
def api_rulebook():
    p = _pdir(request.args["name"])
    return jsonify({"ok": True, "rulebook": rulebook.build(p, write=False)})


@app.get("/api/rulebook_file")
def api_rulebook_file():
    return send_from_directory(_pdir(request.args["name"]), "rulebook.json", as_attachment=True)


@app.get("/api/project")
def api_project():
    p = _pdir(request.args["name"])
    out = {}
    for k, fn in (("summary", "project.json"), ("index", "machine_index.json"), ("signatures", "signatures.json"), ("assumptions", "assumptions.json")):
        with open(os.path.join(p, fn)) as f:
            out[k] = json.load(f)
    out["ok"] = True
    return jsonify(out)


@app.get("/api/project_geometry")
def api_project_geometry():
    with open(os.path.join(_pdir(request.args["name"]), "wireframe", "geometry.json")) as f:
        return jsonify(json.load(f))


@app.get("/api/file")
def api_file():
    p = _pdir(request.args["name"])
    full = os.path.abspath(os.path.join(p, request.args["path"]))
    if not full.startswith(os.path.abspath(p) + os.sep) or not os.path.isfile(full):
        return err("No such file.", 404)
    with open(full, errors="replace") as f:
        return jsonify({"ok": True, "text": f.read()[:60000]})


@app.get("/api/files")
def api_files():
    p = _pdir(request.args["name"])
    d = os.path.abspath(os.path.join(p, request.args["dir"]))
    if not d.startswith(os.path.abspath(p)):
        return err("No such folder.", 404)
    return jsonify({"files": sorted(f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))})


@app.post("/api/replay")
def api_replay():
    d = request.json
    p = _pdir(d["name"])
    observed = live_match.replay(p, d.get("part"), d.get("level", "warning"), float(d.get("noise_A", 0.0)), int(d.get("seed", 1)))
    return jsonify({"ok": True, "observed": observed, "match": live_match.match(p, observed)})


@app.post("/api/match")
def api_match():
    d = request.json
    return jsonify({"ok": True, "match": live_match.match(_pdir(d["name"]), {k: float(v) for k, v in d["observed"].items()})})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8792)), debug=False)
