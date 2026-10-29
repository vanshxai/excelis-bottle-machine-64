"""
Faulter AI -- Core Engine Dashboard. Local-only (127.0.0.1), dark theme.

Shows the core engine's real live stats (recomputed from formulas.py every
request, not a stale cache) and lists released software packets -- built
and published here by us, downloaded and operated by the user from here.
We publish; the user runs their own machine's data through what they
download. This page does not run any pipeline itself.
"""
import json
import os
import sys
import threading

from flask import Flask, render_template, send_from_directory, abort, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASES_DIR = os.path.join(BASE_DIR, "releases")
RELEASES_JSON = os.path.join(BASE_DIR, "releases.json")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "faulter-formula-brain"))
import brain  # noqa: E402
from formulas import FORMULAS, FORMULA_DOMAINS  # noqa: E402

app = Flask(__name__)


def node_kinds():
    """source-only (leaf input, must be supplied), sink-only (terminal
    output, nothing downstream reads it), interior (both) -- same
    classification used earlier when explaining the graph's shape."""
    outputs, inputs = set(), set()
    for eq in FORMULAS.values():
        outputs.add(str(eq.lhs))
        inputs.update(str(s) for s in eq.rhs.free_symbols)
    source_only = inputs - outputs
    sink_only = outputs - inputs
    kind = {}
    for s in source_only:
        kind[s] = "source"
    for s in sink_only:
        kind[s] = "sink"
    for s in (outputs & inputs):
        kind[s] = "interior"
    return kind


NODE_KIND = node_kinds()


def formulas_touching(symbol: str):
    """Every formula where `symbol` appears as the output or as an input."""
    out = []
    for name, eq in FORMULAS.items():
        output = str(eq.lhs)
        inputs = [str(s) for s in eq.rhs.free_symbols]
        if symbol == output or symbol in inputs:
            out.append({
                "name": name,
                "domain": FORMULA_DOMAINS.get(name, "unknown"),
                "equation": f"{eq.lhs} = {eq.rhs}",
                "output": output,
                "inputs": inputs,
            })
    return out


# Second view of the same formulas: the engine tags each one with a physics
# domain (33 of them); this groups those into the engineering disciplines a
# client would name. Lives here, not in the engine -- it is a dashboard
# lens, and the engine's own domain tags stay the source of truth. A domain
# the engine adds later that is not listed lands in "Other" instead of
# silently vanishing from the totals.
ENGINEERING_DISCIPLINES = [
    ("Electrical Engineering", ["electrical", "power_systems", "transformer", "induction_motor",
                                "synchronous_machine", "dc_motor_industrial", "magnetic", "power",
                                "illumination", "renewable_energy"]),
    ("Electronics & Embedded", ["electronics", "rf", "gpio", "timing", "instrumentation"]),
    ("Control Engineering", ["control_systems"]),
    ("Mechanical Engineering", ["mechanical", "mechanical_drives", "welding_joints",
                                "pressure_vessels", "manufacturing", "design"]),
    ("Fluid & Thermal Engineering", ["hydraulics", "thermal", "thermodynamic_cycles",
                                     "hvac_refrigeration"]),
    ("Chemical & Materials Engineering", ["chemistry", "materials", "battery_chemistry"]),
    ("Civil & Structural Engineering", ["civil_structural"]),
    ("Aerospace Engineering", ["aerospace"]),
    ("Cross-cutting", ["universal", "fault_pattern"]),
]


def engineering_breakdown():
    """Formulas grouped by engineering discipline -> physics domain."""
    domain_to_disc = {d: name for name, doms in ENGINEERING_DISCIPLINES for d in doms}
    order = [name for name, _ in ENGINEERING_DISCIPLINES] + ["Other"]
    groups = {name: {"name": name, "domains": {}, "formulas": []} for name in order}
    for fname, eq in FORMULAS.items():
        dom = FORMULA_DOMAINS.get(fname, "unknown")
        g = groups[domain_to_disc.get(dom, "Other")]
        g["domains"][dom] = g["domains"].get(dom, 0) + 1
        g["formulas"].append({"name": fname, "domain": dom, "equation": f"{eq.lhs} = {eq.rhs}"})
    out = []
    for name in order:
        g = groups[name]
        if not g["formulas"]:
            continue
        g["count"] = len(g["formulas"])
        g["domains"] = sorted(g["domains"].items(), key=lambda x: -x[1])
        g["formulas"].sort(key=lambda f: (f["domain"], f["name"]))
        out.append(g)
    return sorted(out, key=lambda g: (g["name"] == "Other", -g["count"]))


def engine_stats():
    # Computed in memory from the live formula set. Deliberately NOT
    # brain.build_graph(): that also rewrites brain_graph.json inside the
    # core engine's own folder on every call, and a dashboard page view
    # must never write into the engine.
    from collections import Counter
    domain_counts = Counter(FORMULA_DOMAINS.get(n, "unknown") for n in FORMULAS)
    return {
        "formula_count": len(FORMULAS),
        "node_count": len(NODE_KIND),
        "domain_count": len(domain_counts),
        "domains": sorted(domain_counts.items(), key=lambda x: -x[1]),
        "disciplines": engineering_breakdown(),
    }


@app.context_processor
def inject_nav_stats():
    s = engine_stats()
    return {"nav_stats": {"formulas": s["formula_count"], "domains": s["domain_count"]}}


def load_releases():
    if not os.path.exists(RELEASES_JSON):
        return []
    with open(RELEASES_JSON) as f:
        releases = json.load(f)
    for r in releases:
        path = os.path.join(RELEASES_DIR, r["file"])
        r["size_mb"] = round(os.path.getsize(path) / (1024 * 1024), 1) if os.path.exists(path) else None
    return list(reversed(releases))  # newest first


@app.route("/")
def index():
    return render_template("index.html", stats=engine_stats(), releases=load_releases())


@app.route("/graph")
def graph_page():
    return render_template("graph.html")


@app.route("/api/search")
def api_search():
    q = (request.args.get("q") or "").strip().lower()
    if not q:
        return jsonify([])
    all_symbols = set(NODE_KIND.keys())
    for eq in FORMULAS.values():
        all_symbols.add(str(eq.lhs))
        all_symbols.update(str(s) for s in eq.rhs.free_symbols)
    matches = sorted(s for s in all_symbols if q in s.lower())[:20]
    formula_matches = sorted(n for n in FORMULAS if q in n.lower())[:10]
    return jsonify({"symbols": matches, "formulas": formula_matches})


@app.route("/api/expand")
def api_expand():
    symbol = request.args.get("node")
    formula_name = request.args.get("formula")

    if formula_name and formula_name in FORMULAS:
        eq = FORMULAS[formula_name]
        touching = [{
            "name": formula_name, "domain": FORMULA_DOMAINS.get(formula_name, "unknown"),
            "equation": f"{eq.lhs} = {eq.rhs}", "output": str(eq.lhs),
            "inputs": [str(s) for s in eq.rhs.free_symbols],
        }]
    elif symbol:
        touching = formulas_touching(symbol)
    else:
        return jsonify({"error": "need ?node= or ?formula="}), 400

    nodes, edges = {}, []
    for f in touching:
        for sym in [f["output"]] + f["inputs"]:
            nodes[sym] = NODE_KIND.get(sym, "interior")
        for inp in f["inputs"]:
            edges.append({"from": inp, "to": f["output"], "formula": f["name"],
                           "domain": f["domain"], "equation": f["equation"]})

    return jsonify({
        "nodes": [{"id": s, "kind": k} for s, k in nodes.items()],
        "edges": edges,
        "formulas": touching,
    })


@app.route("/solver")
def solver_page():
    return render_template("solver.html")


@app.route("/api/symbols")
def api_symbols():
    return jsonify(sorted(NODE_KIND.keys()))


_solve_lock = threading.Lock()


def _missing_inputs_for(target, known_syms):
    """When the solver can't reach a target: for each formula that produces
    it, which inputs are still unknown -- the immediate blockers."""
    out = []
    for name, eq in FORMULAS.items():
        if str(eq.lhs) != target:
            continue
        inputs = [str(s) for s in eq.rhs.free_symbols]
        missing = [i for i in inputs if i not in known_syms]
        out.append({"formula": name, "equation": f"{eq.lhs} = {eq.rhs}",
                    "domain": FORMULA_DOMAINS.get(name, "unknown"), "missing": missing})
    return sorted(out, key=lambda x: len(x["missing"]))


@app.route("/api/solve", methods=["POST"])
def api_solve():
    body = request.get_json(force=True, silent=True) or {}
    target = body.get("target")
    path_type = body.get("path_type", "shortest")
    use_defaults = bool(body.get("use_defaults", False))
    raw_known = body.get("known") or {}

    if target not in NODE_KIND:
        return jsonify({"error": f"unknown target variable: {target!r}"}), 400
    known = {}
    for k, v in raw_known.items():
        if k not in NODE_KIND:
            return jsonify({"error": f"unknown variable: {k!r}"}), 400
        try:
            known[k] = float(v)
        except (TypeError, ValueError):
            return jsonify({"error": f"value for {k} is not a number"}), 400
    if path_type not in ("shortest", "confident", "longest"):
        path_type = "shortest"

    # The engine injects ESP32 spec defaults (V, I_cpu, R_th...) into every
    # solve. That's invisible in a plain call, so this panel makes it an
    # explicit choice instead of a surprise.
    defaults = brain._default_esp32_knowns()[0] if use_defaults else {}
    with _solve_lock:
        original = brain._default_esp32_knowns
        if not use_defaults:
            brain._default_esp32_knowns = lambda: ({}, {})
        try:
            result = brain.solve_path(known, target, path_type)
        finally:
            brain._default_esp32_knowns = original

    produced = set()
    for step in result.get("trace", []):
        origin = {}
        for i in step["inputs"]:
            origin[i] = ("derived" if i in produced else "given" if i in known
                         else "default" if i in defaults else "unknown")
        step["input_origin"] = origin
        produced.add(step["output"])

    if result.get("result") is None:
        reached = set(known) | set(defaults) | set(result.get("partially_derived", []))
        result["blockers"] = _missing_inputs_for(target, reached)

    result["target"] = target
    result["given"] = known
    result["defaults_used"] = defaults
    return jsonify(result)


@app.route("/download/<release_id>")
def download(release_id):
    releases = {r["id"]: r for r in load_releases()}
    r = releases.get(release_id)
    if not r:
        abort(404)
    return send_from_directory(RELEASES_DIR, r["file"], as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5090, debug=False)
