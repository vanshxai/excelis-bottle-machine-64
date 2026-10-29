"""
Yanthros Formula Brain -- a local background service (port 5051).

Turns formulas.py into a queryable graph instead of a static file:
every unique variable symbol across every formula becomes a node; every
formula becomes an edge from its input variables to its output variable
(a hyperedge -- one formula, many inputs, one output). Given a set of
known variables and a target, it forward-chains through whatever
formulas become solvable, exactly the "Pathfinder" idea discussed for
Yanthros: pick any known engineering inputs, ask for any output, and it
finds the chain of formulas connecting them.

Not user facing -- only app.py (and Claude Code, during development)
talk to this. Three endpoints only: /brain/understand, /brain/solve,
/brain/extend.
"""
import json
import os
import re
import threading

import sympy as sp
from flask import Flask, jsonify, request

from formulas import FORMULAS, FORMULA_DOMAINS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_FILE = os.path.join(BASE_DIR, "brain_graph.json")
EXTENSIONS_FILE = os.path.join(BASE_DIR, "brain_extensions.json")
ESP32_SPECS_FILE = os.path.join(BASE_DIR, "esp32_specs.json")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

_extension_formulas = {}   # name -> sp.Eq, added live via /brain/extend
_extension_domains = {}    # name -> domain string
_extension_sources = {}    # name -> citation string (textbook/standard/paper), required on /brain/extend
_symbol_table = {}         # name -> sp.Symbol, shared across built-in + extended formulas


def _all_formulas():
    merged = dict(FORMULAS)
    merged.update(_extension_formulas)
    return merged


def _all_domains():
    merged = dict(FORMULA_DOMAINS)
    merged.update(_extension_domains)
    return merged


def _all_sources():
    """Built-in formulas (formulas.py) predate the citation requirement and
    have no recorded source; extended formulas (/brain/extend) always do,
    since the route rejects a missing one."""
    merged = {name: "builtin (formulas.py)" for name in FORMULAS}
    merged.update(_extension_sources)
    return merged


def load_extensions():
    """Formulas added at runtime via /brain/extend persist across restarts."""
    if not os.path.exists(EXTENSIONS_FILE):
        return
    with open(EXTENSIONS_FILE, "r") as f:
        saved = json.load(f)
    for name, entry in saved.items():
        try:
            lhs = sp.sympify(entry["lhs"])
            rhs = sp.sympify(entry["rhs"])
            _extension_formulas[name] = sp.Eq(lhs, rhs)
            _extension_domains[name] = entry.get("domain", "custom")
            _extension_sources[name] = entry.get("source", "")
        except Exception as e:
            print(f"brain: failed to restore extension formula '{name}': {e}")


def save_extensions():
    out = {}
    for name, eq in _extension_formulas.items():
        out[name] = {
            "lhs": str(eq.lhs), "rhs": str(eq.rhs),
            "domain": _extension_domains.get(name, "custom"),
            "source": _extension_sources.get(name, ""),
        }
    with open(EXTENSIONS_FILE, "w") as f:
        json.dump(out, f, indent=2)


def build_graph():
    """Nodes = every unique variable symbol. Edges = one per formula,
    connecting its input variables to its output variable."""
    formulas = _all_formulas()
    domains = _all_domains()
    sources = _all_sources()
    nodes = set()
    edges = []
    for name, eq in formulas.items():
        output = str(eq.lhs)
        inputs = sorted(str(s) for s in eq.rhs.free_symbols)
        nodes.add(output)
        nodes.update(inputs)
        edges.append({
            "formula": name,
            "domain": domains.get(name, "unknown"),
            "source": sources.get(name, "builtin (formulas.py)"),
            "inputs": inputs,
            "output": output,
            "equation": f"{eq.lhs} = {eq.rhs}",
        })
    graph = {
        "nodes": sorted(nodes),
        "edges": edges,
        "domains": sorted(set(domains.values())),
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
    with open(GRAPH_FILE, "w") as f:
        json.dump(graph, f, indent=2)
    return graph


GRAPH = None


def get_graph(rebuild=False):
    global GRAPH
    if GRAPH is None or rebuild:
        GRAPH = build_graph()
    return GRAPH


# ---------------------------------------------------------------------------
# Natural-language understanding -- honest keyword/phrase matching, not a
# claimed neural NLU. Maps phrases people actually say to graph variable
# names, plus a couple of regexes for pulling numbers out of a sentence.
# ---------------------------------------------------------------------------

VARIABLE_SYNONYMS = {
    "T_chip": ["chip temperature", "chip temp", "junction temperature", "soc temperature"],
    "T_amb": ["ambient temperature", "room temperature", "ambient temp"],
    "I_wifi": ["wifi current", "wifi load", "wifi power draw", "full wifi load", "wifi tx current"],
    "I_cpu": ["cpu current", "cpu load", "processor current"],
    "I_gpio": ["gpio current", "pin current"],
    "I_total": ["total current", "total current draw", "supply current"],
    "C_battery": ["battery capacity", "mah battery", "battery"],
    "t_batt": ["battery life", "battery last", "how long will the battery", "runtime"],
    "V_in": ["input voltage", "usb voltage", "supply voltage", "powered from usb"],
    "V": ["supply voltage", "input voltage"],
    "P": ["power consumption", "power dissipated", "power draw", "wattage"],
    "R_th": ["thermal resistance"],
    "f_crystal": ["crystal frequency", "oscillator frequency", "40mhz"],
    "f_cpu": ["cpu frequency", "clock speed", "processor speed"],
    "f_rf": ["wifi frequency", "rf frequency", "2.4ghz", "carrier frequency"],
    "dist_rf": ["distance", "range"],
    "PL": ["path loss", "signal loss"],
    "L_ant": ["antenna length"],
}

_NUMBER_NEAR = re.compile(r"(-?\d+(?:\.\d+)?)\s*(mah|ma|a|v|ghz|mhz|hz|c|°c|m|db)?", re.IGNORECASE)


def extract_known_values(query):
    """Best-effort pull of (variable, value) pairs out of a plain sentence.
    Deliberately simple: looks for a synonym phrase, then the nearest
    number in the same sentence, with unit-aware scaling."""
    q = query.lower()
    knowns = {}
    notes = []

    if "ambient temperature" in q or "ambient" in q:
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:degrees?|°)?\s*c", q)
        if m:
            knowns["T_amb"] = float(m.group(1))

    if re.search(r"\busb\b.*\b5v\b|\b5v\b.*\busb\b|usb 5v", q):
        knowns["V_in"] = 5.0
    else:
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*v\b", q)
        if m and "V_in" not in knowns:
            knowns["V_in"] = float(m.group(1))

    if "full wifi" in q or "full power" in q or "max wifi" in q:
        specs = load_esp32_specs()
        if specs:
            knowns["I_wifi"] = specs["chip_electrical"]["current_active_wifi_tx_mA"]["value"] / 1000.0
            notes.append("I_wifi taken from esp32_specs.json rated WiFi TX current (full load)")

    m = re.search(r"(-?\d+(?:\.\d+)?)\s*mah", q)
    if m:
        knowns["C_battery"] = float(m.group(1)) / 1000.0  # mAh -> Ah
        notes.append("C_battery converted from mAh to Ah")

    return knowns, notes


def identify_targets(query):
    """A query can ask for more than one thing at once (e.g. chip temp AND
    battery life) -- returns every target recognized, in the order asked."""
    q = query.lower()
    targets = []
    if "chip temperature" in q or "chip temp" in q or "junction temp" in q:
        targets.append("T_chip")
    if "battery" in q and ("last" in q or "life" in q or "long" in q):
        targets.append("t_batt")
    if "power consumption" in q or "how much power" in q:
        targets.append("P")
    if "total current" in q:
        targets.append("I_total")
    return targets


def identify_target(query):
    """Back-compat single-target accessor -- returns the first target found."""
    targets = identify_targets(query)
    return targets[0] if targets else None


def load_esp32_specs():
    if not os.path.exists(ESP32_SPECS_FILE):
        return None
    with open(ESP32_SPECS_FILE, "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Forward-chaining solver (the actual "Pathfinder")
# ---------------------------------------------------------------------------

CONFIRMED_CONFIDENCE = 0.95
ESTIMATED_CONFIDENCE = 0.75
GIVEN_CONFIDENCE = 1.0
HOP_DECAY = 0.98


def _default_esp32_knowns():
    """Pull sensible default constants from esp32_specs.json (chip_electrical
    block) so a solve can proceed even if the query didn't state everything.
    Each default is tagged with its confirmed/estimated confidence."""
    specs = load_esp32_specs()
    defaults, confidence = {}, {}
    if not specs:
        return defaults, confidence
    ce = specs.get("chip_electrical", {})
    field_map = {
        "cpu_freq_MHz": ("f_cpu", 1e6), "current_modem_sleep_mA": ("I_cpu", 1e-3),
        "thermal_resistance_junction_ambient_C_per_W": ("R_th", 1),
        "typical_gpio_current_mA": ("I_gpio", 1e-3), "typical_peripheral_current_mA": ("I_peripherals", 1e-3),
        # power_consumption's P=V*I_total is chip-side power, so V is the
        # regulated 3.3V logic rail -- NOT the raw 5V USB input (that's
        # V_in, which only feeds voltage_drop across the AMS1117).
        "operating_voltage_V": ("V", 1),
    }
    for spec_key, (symbol, scale) in field_map.items():
        entry = ce.get(spec_key)
        if entry:
            defaults[symbol] = entry["value"] * scale
            confidence[symbol] = CONFIRMED_CONFIDENCE if entry.get("confirmed") else ESTIMATED_CONFIDENCE
    crystal = specs.get("crystal_oscillator", {})
    if "frequency_MHz" in crystal:
        defaults["f_crystal"] = crystal["frequency_MHz"] * 1e6
        confidence["f_crystal"] = CONFIRMED_CONFIDENCE if crystal.get("confirmed") else ESTIMATED_CONFIDENCE
    return defaults, confidence


def solve_path(known_values, target, path_type="shortest"):
    """
    Forward-chains from `known_values` through every formula whose inputs
    all become known, until `target` is reached or nothing new fires.
    Returns a dict with the ordered trace, all intermediate values, the
    final result, and a confidence score.
    """
    formulas = _all_formulas()
    domains = _all_domains()
    sources = _all_sources()

    defaults, default_conf = _default_esp32_knowns()
    known = dict(defaults)
    known.update(known_values)
    confidence = {k: GIVEN_CONFIDENCE for k in known_values}
    for k in defaults:
        if k not in known_values:
            confidence[k] = default_conf.get(k, ESTIMATED_CONFIDENCE)

    if target in known:
        return {
            "path": [], "trace": [], "computed": {}, "result": known[target],
            "confidence": round(confidence.get(target, GIVEN_CONFIDENCE), 4),
            "note": "target was already a known value, no formula chain needed",
        }

    trace = []
    produced_by = {}
    wave = 0
    while target not in known:
        fired_this_wave = []
        for name, eq in formulas.items():
            output = str(eq.lhs)
            if output in known:
                continue
            inputs = [str(s) for s in eq.rhs.free_symbols]
            if not inputs or not all(i in known for i in inputs):
                continue
            # candidate formula could fire this wave -- collect all candidates
            # that produce a not-yet-known variable, resolve ties below
            fired_this_wave.append((name, eq, output, inputs))

        if not fired_this_wave:
            break  # dead end -- nothing more can be derived

        # group candidates by output variable in case >1 formula can produce it
        by_output = {}
        for name, eq, output, inputs in fired_this_wave:
            by_output.setdefault(output, []).append((name, eq, inputs))

        for output, candidates in by_output.items():
            if len(candidates) == 1:
                name, eq, inputs = candidates[0]
            elif path_type == "confident":
                name, eq, inputs = max(candidates, key=lambda c: sum(confidence.get(i, ESTIMATED_CONFIDENCE) for i in c[2]) / len(c[2]))
            elif path_type == "longest":
                name, eq, inputs = max(candidates, key=lambda c: len(c[2]))
            else:  # shortest (default) -- fewest inputs = simplest hop
                name, eq, inputs = min(candidates, key=lambda c: len(c[2]))

            subs = {sp.Symbol(i): known[i] for i in inputs}
            try:
                value = float(eq.rhs.subs(subs))
            except Exception:
                continue
            known[output] = value
            produced_by[output] = name
            input_conf = [confidence.get(i, ESTIMATED_CONFIDENCE) for i in inputs]
            confidence[output] = (sum(input_conf) / len(input_conf)) * (HOP_DECAY ** (wave + 1))
            trace.append({
                "step": len(trace) + 1, "formula": name, "domain": domains.get(name, "unknown"),
                "source": sources.get(name, "builtin (formulas.py)"),
                "equation": f"{eq.lhs} = {eq.rhs}",
                "inputs": {i: round(known[i], 8) for i in inputs},
                "output": output, "value": round(value, 8),
            })
        wave += 1
        if wave > 30:
            break  # safety valve against pathological cycles

    if target not in known:
        reached = sorted(v for v in known if v not in known_values and v not in defaults)
        return {
            "path": [], "trace": [], "computed": {},
            "result": None, "confidence": 0.0,
            "note": f"could not reach '{target}' from the given knowns -- missing an input somewhere in the chain",
            "partially_derived": reached,
        }

    # The forward sweep computes everything REACHABLE, which includes
    # formulas unrelated to this particular target (e.g. a temperature
    # query would also fire clock_period if a crystal frequency happened
    # to be known). Backtrack from the target through produced_by so the
    # returned path/trace only contains what's actually on the chain to it.
    trace_by_output = {t["output"]: t for t in trace}
    relevant = []
    visited = set()

    def backtrack(var):
        if var in visited or var not in produced_by:
            return
        visited.add(var)
        step = trace_by_output[var]
        for i in step["inputs"]:
            backtrack(i)
        relevant.append(step)

    backtrack(target)

    return {
        "path": [t["formula"] for t in relevant], "trace": relevant,
        "computed": {t["output"]: t["value"] for t in relevant},
        "result": round(known[target], 8),
        "confidence": round(confidence.get(target, ESTIMATED_CONFIDENCE), 4),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/brain/understand", methods=["POST"])
def brain_understand():
    body = request.get_json(force=True, silent=True) or {}
    query = body.get("query", "")
    knowns, notes = extract_known_values(query)
    targets = identify_targets(query)

    q = query.lower()
    variables_identified = list(knowns.keys()) + list(targets)
    for symbol, phrases in VARIABLE_SYNONYMS.items():
        if symbol in variables_identified:
            continue
        if any(p in q for p in phrases):
            variables_identified.append(symbol)

    graph = get_graph()
    node_set = set(graph["nodes"])
    unknowns = [v for v in variables_identified if v not in knowns]

    suggested_paths = []
    for target in targets:
        result = solve_path(knowns, target, "shortest")
        if result["path"]:
            suggested_paths.append({"target": target, "path": result["path"], "path_type": "shortest"})

    return jsonify({
        "query": query,
        "variables_identified": [v for v in variables_identified if v in node_set],
        "known_values": knowns,
        "target_variable": targets[0] if targets else None,
        "target_variables": targets,
        "unknowns": unknowns,
        "suggested_paths": suggested_paths,
        "notes": notes,
    })


@app.route("/brain/solve", methods=["POST"])
def brain_solve():
    body = request.get_json(force=True, silent=True) or {}
    known = body.get("known", {}) or {}
    target = body.get("target")
    path_type = body.get("path_type", "shortest")
    if not target:
        return jsonify({"error": "missing 'target' variable"}), 400
    if path_type not in ("shortest", "confident", "longest"):
        path_type = "shortest"
    result = solve_path(known, target, path_type)
    result["target"] = target
    result["path_type"] = path_type
    return jsonify(result)


@app.route("/brain/extend", methods=["POST"])
def brain_extend():
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("name")
    formula_str = body.get("formula", "")
    domain = body.get("domain", "custom")
    variables = body.get("variables", [])
    source = (body.get("source") or "").strip()
    if not name or "=" not in formula_str:
        return jsonify({"ok": False, "error": "expected 'name' and 'formula' as 'lhs = rhs'"}), 400
    if not source:
        return jsonify({
            "ok": False,
            "error": "expected non-empty 'source' -- a citation for where this formula comes "
                     "(textbook, standard, paper, or manufacturer datasheet). Formulas without "
                     "a traceable origin don't get to influence a solve.",
        }), 400

    lhs_str, rhs_str = formula_str.split("=", 1)
    local_syms = {v: sp.Symbol(v) for v in variables}
    try:
        lhs = sp.sympify(lhs_str.strip(), locals=local_syms)
        rhs = sp.sympify(rhs_str.strip(), locals=local_syms)
    except Exception as e:
        return jsonify({"ok": False, "error": f"could not parse formula: {e}"}), 400

    before_nodes = set(get_graph()["nodes"])
    _extension_formulas[name] = sp.Eq(lhs, rhs)
    _extension_domains[name] = domain
    _extension_sources[name] = source
    save_extensions()
    graph = get_graph(rebuild=True)
    new_nodes = set(graph["nodes"]) - before_nodes

    return jsonify({
        "ok": True, "formula": name, "domain": domain, "source": source,
        "equation": f"{lhs} = {rhs}",
        "new_connections_formed": sorted(new_nodes),
        "graph_node_count": graph["node_count"], "graph_edge_count": graph["edge_count"],
    })


@app.route("/brain/status")
def brain_status():
    graph = get_graph()
    return jsonify({"status": "ready", "nodes": graph["node_count"], "edges": graph["edge_count"], "domains": graph["domains"]})


def _print_banner():
    graph = get_graph(rebuild=True)
    print("Yanthros Formula Brain running on port 5051")
    print(f"Nodes loaded: {graph['node_count']}")
    print(f"Edges loaded: {graph['edge_count']}")
    print(f"Domains detected: {', '.join(graph['domains'])}")
    print("Ready.")


def start_in_thread():
    """Called by app.py to run the Brain's Flask app in a background
    thread inside the same process -- no subprocess management needed."""
    load_extensions()
    _print_banner()
    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5051, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    return thread


if __name__ == "__main__":
    load_extensions()
    _print_banner()
    app.run(host="127.0.0.1", port=5051, debug=False, use_reloader=False)
