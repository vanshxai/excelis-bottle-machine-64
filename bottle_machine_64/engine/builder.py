"""
Analyse -> validate -> build.

analyze():  reads STEP + BOM, matches them, proposes (never decides) part types.
validate(): checks the user's answers are complete; anything missing is reported, never filled in.
build():    writes the project folder (one folder per part, with its own generated code and stored
            simulation results), runs the per-part simulations in parallel, writes the signatures.
"""
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.environ["PYTHONPATH"] = HERE + os.pathsep + os.environ.get("PYTHONPATH", "")

import bom_reader  # noqa: E402
import formula_pack  # noqa: E402
import linking  # noqa: E402
import matching  # noqa: E402
import part_types  # noqa: E402
import rulebook  # noqa: E402
import runtime  # noqa: E402
import step_geometry  # noqa: E402
from part_types import TYPES, has_effort, is_motor  # noqa: E402


class BuildError(Exception):
    def __init__(self, problems):
        self.problems = problems
        super().__init__("; ".join(problems))


def _slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:40]


def cylinder_from_bbox(bbox):
    lo, hi = bbox
    dims = [h - l for l, h in zip(lo, hi)]
    order = sorted(range(3), key=lambda i: dims[i])
    a, b, c = (dims[i] for i in order)
    # two nearly equal dimensions (the circle) and one different (the length)
    for pair, odd in (((order[0], order[1]), order[2]), ((order[1], order[2]), order[0])):
        d1, d2 = dims[pair[0]], dims[pair[1]]
        if abs(d1 - d2) <= 0.03 * max(d1, d2) and abs(dims[odd] - (d1 + d2) / 2) > 0.03 * max(d1, d2):
            return {"radius_mm": round((d1 + d2) / 4, 3), "axis": "xyz"[odd]}
    return None


# --------------------------------------------------------------------------- analyze
def analyze(step_path, bom_path):
    geo = step_geometry.extract(step_path)
    bom = bom_reader.read(bom_path)
    m = matching.match(geo["parts"], bom["rows"])
    by_pn = {r["part_number"]: r for r in bom["rows"]}
    asm_desc = {r["part_number"]: r["description"] for r in bom["rows"] if r["is_assembly"]}
    gp = {p["id"]: p for p in geo["parts"]}

    parts = {}
    for mm in m["matched"]:
        pn = mm["part_number"]
        if pn in parts:
            parts[pn]["instances"].append(mm["step_id"])
            continue
        row = by_pn[pn]
        asm = [a for a in mm["path"] if a in asm_desc]
        section = asm[-1] if len(asm) > 1 else (asm[0] if asm else "")
        t, why = part_types.suggest_type(row["description"])
        parts[pn] = {
            "part_number": pn, "step_id": mm["step_id"], "instances": [mm["step_id"]], "description": row["description"],
            "material": row["material"], "section": section, "section_name": asm_desc.get(section, ""),
            "suggested_type": t, "suggest_reason": why, "cylinder": cylinder_from_bbox(gp[mm["step_id"]]["bbox_mm"]),
        }
    return {"geometry": geo, "bom": bom, "match": m, "parts": parts, "assemblies": asm_desc}


# --------------------------------------------------------------------------- requirements
def requirements(analysis, types, links):
    parts = analysis["parts"]
    motors, plist = {}, {}
    for pn, t in types.items():
        if t not in TYPES:
            continue
        spec = TYPES[t]
        if is_motor(t):
            motors[pn] = {"label": spec["label"], "fields": [
                {"key": "T_rated", "label": "Rated output torque from the nameplate", "unit": "N*m"},
                {"key": "I_rated", "label": "Rated current from the nameplate", "unit": "A"},
                {"key": "I_noload", "label": "Current with nothing attached (leave empty if unknown)", "unit": "A", "optional": True},
                {"key": "I_normal", "label": "Current it normally draws when the machine runs healthy", "unit": "A"},
            ]}
        elif spec["kind"] == "driven":
            cyl = parts[pn]["cylinder"]
            plist[pn] = {
                "type_label": spec["label"], "params": spec.get("params", []), "effort": spec.get("effort"),
                "needs_radius": "radius_mm" in spec.get("geometry", []),
                "radius_from_step": cyl["radius_mm"] if cyl else None,
            }
    return {"motors": motors, "parts": plist,
            "settings": [{"key": "tolerance_A", "label": "Smallest change in motor current you can trust from your sensor", "unit": "A"}]}


# --------------------------------------------------------------------------- validate
def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(analysis, answers, upto=None):
    problems = []
    parts = analysis["parts"]
    types = answers.get("types", {})
    for pn in parts:
        if types.get(pn) not in TYPES:
            problems.append(f"{pn} ({parts[pn]['description']}): choose what kind of part it is.")
    if problems:
        return problems
    typed = {pn: {"type": types[pn], "section": parts[pn]["section"]} for pn in parts}
    if not any(is_motor(t["type"]) for t in typed.values()):
        problems.append("No motor has been chosen - the machine needs at least one.")
    problems += linking.validate_links(typed, answers.get("links", {}))
    if problems or upto == "links":
        return problems

    req = requirements(analysis, types, answers["links"])
    tol = _num(answers.get("settings", {}).get("tolerance_A"))
    if not tol or tol <= 0:
        problems.append("Settings: enter the smallest current change you can trust (A).")
    for pn, spec in req["motors"].items():
        a = answers.get("motors", {}).get(pn, {})
        for f in spec["fields"]:
            v = _num(a.get(f["key"]))
            if v is None and not f.get("optional"):
                problems.append(f"{pn}: '{f['label']}' is empty.")
            elif v is not None and (v <= 0 and f["key"] != "I_noload" or v < 0):
                problems.append(f"{pn}: '{f['label']}' must be a positive number.")
        i_no, i_r = _num(a.get("I_noload")), _num(a.get("I_rated"))
        if i_no is not None and i_r is not None and i_no >= i_r:
            problems.append(f"{pn}: no-load current must be smaller than rated current.")
    for pn, spec in req["parts"].items():
        a = answers.get("parts", {}).get(pn, {})
        for p in spec["params"]:
            v = _num(a.get(p["key"]))
            if v is None or v <= 0:
                problems.append(f"{pn}: '{p['label']}' is empty or not positive.")
        if spec["needs_radius"] and spec["radius_from_step"] is None and not _num(a.get("radius_mm")):
            problems.append(f"{pn}: the STEP file does not show a clean round shape - enter its radius (mm).")
        if spec["effort"]:
            e = a.get("effort", {})
            ok, w, c = _num(e.get("ok_max")), _num(e.get("warning")), _num(e.get("critical"))
            if None in (ok, w, c):
                problems.append(f"{pn}: fill in all three levels for '{spec['effort']['label']}'.")
            elif not (0 <= ok < w < c):
                problems.append(f"{pn}: levels must increase: fine < warning < critical.")
    return problems


# --------------------------------------------------------------------------- code generation
HOP = {  # rule -> (needs, gives)
    "direct_torque": ("torque", "torque"), "force_to_torque_parent": ("force", "torque"),
    "torque_to_force_child": ("torque", "force"), "force_direct": ("force", "force"),
}


def render_code(pn, desc, t, role, chain, types, radii, own, answers_part):
    L = [f'"""Generated for {pn} ({desc}) - type: {TYPES[t]["label"]}, role: {role}.',
         f"Drive chain, this part to the motor: {' -> '.join(chain)}.",
         'Every value is either measured from the STEP file or typed in by the user; nothing is assumed."""',
         "from runtime import apply", ""]
    for name, (val, unit, src) in own.items():
        L.append(f"{name} = {val!r}  # {unit} - {src}")
    L += ["", "", "def motor_torque(effort):",
          f'    """Extra torque (N*m) the motor must supply when `effort` ({TYPES[t]["effort"]["unit"]}) is applied at this part."""']
    q = {"shaft": "torque", "rotary_disk": "torque", "idler_pulley": "torque", "belt": "force", "flipper_arm": "force"}[t]
    if t == "shaft":
        L.append("    q = apply('bearing_friction_torque', 'Tf', F=effort, mu=MU, r=R_SELF)  # torque at the shaft's bearings")
    elif t == "rotary_disk":
        L.append("    q = apply('disc_brake_torque', 'T_brake', F_brake=effort, R_brake=R_SELF, mu_brake=MU)  # drag torque at the disk rim")
    elif t == "idler_pulley":
        L.append("    q = effort  # drag torque turning the idler pulley (N*m)")
    else:
        L.append("    q = effort  # force acting along the belt (N)")
    for child, parent in zip(chain, chain[1:]):
        rule = linking.coupling(types[child], types[parent])
        need, give = HOP[rule]
        if need != q:
            raise BuildError([f"{child} -> {parent}: coupling '{rule}' needs {need} but this chain carries {q}."])
        if rule == "direct_torque":
            L.append(f"    # {child} turns with {parent} (same shaft): torque passes through unchanged")
        elif rule == "force_to_torque_parent":
            L.append(f"    q = apply('lever_torque', 'T_lever', F_tan=q, r_arm=R_{parent})  # belt force becomes torque on {parent}")
        elif rule == "torque_to_force_child":
            L.append(f"    q = apply('lever_torque', 'F_tan', T_lever=q, r_arm=R_{child})  # torque at {child} becomes belt force")
        elif rule == "force_direct":
            L.append(f"    # {child} pushes directly on {parent}: force passes through unchanged")
        q = give
    if q != "torque":
        raise BuildError([f"{pn}: the drive chain ends in a {q}, not a torque at the motor."])
    L.append("    return q  # N*m at the motor's output shaft")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- build
def build(analysis, answers, out_dir, step_path, bom_path, progress=lambda m: None):
    t0 = time.time()
    problems = validate(analysis, answers)
    if problems:
        raise BuildError(problems)
    parts, types, links = analysis["parts"], answers["types"], answers["links"]
    typed = {pn: {"type": types[pn], "section": parts[pn]["section"]} for pn in parts}
    req = requirements(analysis, types, links)

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(os.path.join(out_dir, "source"))
    os.makedirs(os.path.join(out_dir, "wireframe"))
    shutil.copy(step_path, os.path.join(out_dir, "source"))
    shutil.copy(bom_path, os.path.join(out_dir, "source"))
    with open(os.path.join(out_dir, "wireframe", "geometry.json"), "w") as f:
        json.dump(analysis["geometry"], f)
    with open(os.path.join(out_dir, "answers.json"), "w") as f:
        json.dump(answers, f, indent=1)
    stock = formula_pack.build_stock()
    with open(os.path.join(out_dir, "formulas_stock.json"), "w") as f:
        json.dump(stock, f, indent=1)
    runtime.set_project(out_dir)
    progress("formulas copied into the project")

    # motors
    motors = {}
    assumptions = [
        "Each fault is simulated alone: one part carrying extra load at a time.",
        "No losses are modelled between parts (transmission efficiency taken as 100%).",
        "Round-part radii are measured from the bounding box of the part in the STEP file.",
    ]
    for pn, spec in req["motors"].items():
        a = answers["motors"][pn]
        I_no = _num(a.get("I_noload"))
        if I_no is None:
            I_no = 0.0
            assumptions.append(f"{pn}: no-load current was left empty, so the torque-per-amp slope uses rated torque / rated current.")
        Kt = runtime.motor_kt(float(a["T_rated"]), float(a["I_rated"]), I_no)
        motors[pn] = {"T_rated": float(a["T_rated"]), "I_rated": float(a["I_rated"]), "I_noload": I_no,
                      "I_normal": float(a["I_normal"]), "Kt": Kt}
    if any(types[p] == "shaft" for p in parts):
        assumptions.append("Shaft bearing friction acts at the shaft's measured radius.")

    # folders: machine/<root>/<section>/<part>
    index = {"motors": motors, "settings": {"tolerance_A": float(answers["settings"]["tolerance_A"])}, "parts": {}, "sections": {}}
    sim_jobs, tree = [], []
    root_dir = os.path.join(out_dir, "machine")
    for pn, p in parts.items():
        t = types[pn]
        role = linking.role_of(pn, typed, links)
        chain = linking.chain_to_motor(pn, links) if role in ("active", "passive") else [pn]
        motor = chain[-1] if role in ("active", "passive") else (pn if role == "source" else None)
        sec_name = p["section_name"] or "Machine"
        sec_dir = os.path.join(root_dir, f"{p['section'] or 'MACHINE'}_{_slug(sec_name)}")
        part_dir = os.path.join(sec_dir, f"{pn}_{_slug(p['description'])}")
        os.makedirs(part_dir, exist_ok=True)
        # numbers this part needs, each with where it came from
        values = {}

        def radius(of_pn):
            a = answers.get("parts", {}).get(of_pn, {})
            cyl = parts[of_pn]["cylinder"]
            if cyl:
                return cyl["radius_mm"] / 1000.0, "m", f"measured from the STEP file ({of_pn}, round part)"
            return float(a["radius_mm"]) / 1000.0, "m", "typed in by the user"
        own = {}
        if role in ("active", "passive"):
            a = answers.get("parts", {}).get(pn, {})
            if "mu" in a:
                own["MU"] = (float(a["mu"]), "dimensionless", "typed in by the user")
            if "radius_mm" in TYPES[t].get("geometry", []):
                r, u, s = radius(pn)
                own["R_SELF"] = (r, u, s)
                own[f"R_{pn}"] = (r, u, s)
            for other in chain[1:]:
                if "radius_mm" in TYPES[types[other]].get("geometry", []) and f"R_{other}" not in own:
                    own[f"R_{other}"] = radius(other)
            for k, (v, u, s) in own.items():
                values[k] = {"value": v, "unit": u, "source": s}
        pjson = {"part_number": pn, "description": p["description"], "material": p["material"], "type": t,
                 "type_label": TYPES[t]["label"], "role": role, "section": p["section"], "section_name": sec_name,
                 "parent": links.get(pn), "motor": motor, "chain": chain, "step_instances": p["instances"],
                 "values": values, "effort": None}
        if has_effort(t) and role in ("active", "passive"):
            e = answers["parts"][pn]["effort"]
            pjson["effort"] = {"label": TYPES[t]["effort"]["label"], "unit": TYPES[t]["effort"]["unit"],
                               "ok_max": float(e["ok_max"]), "warning": float(e["warning"]), "critical": float(e["critical"])}
            code = render_code(pn, p["description"], t, role, chain, types, None, own, answers["parts"][pn])
            with open(os.path.join(part_dir, "part_code.py"), "w") as f:
                f.write(code)
            sim_jobs.append(part_dir)
        if role == "source":
            pjson["motor_model"] = motors[pn]
            with open(os.path.join(part_dir, "motor.json"), "w") as f:
                json.dump(motors[pn], f, indent=1)
        with open(os.path.join(part_dir, "part.json"), "w") as f:
            json.dump(pjson, f, indent=1)
        index["parts"][pn] = {"type": t, "role": role, "section": p["section"], "section_name": sec_name, "motor": motor,
                              "chain": chain, "dir": os.path.relpath(part_dir, out_dir), "description": p["description"],
                              "step_instances": p["instances"]}
        index["sections"].setdefault(p["section"], {"name": sec_name, "parts": []})["parts"].append(pn)
        tree.append(os.path.relpath(part_dir, out_dir))
    with open(os.path.join(out_dir, "machine_index.json"), "w") as f:
        json.dump(index, f, indent=1)
    with open(os.path.join(out_dir, "assumptions.json"), "w") as f:
        json.dump(assumptions, f, indent=1)
    progress(f"{len(parts)} part folders written")

    # simulate every part in its own process
    workers = max(1, min(os.cpu_count() or 1, len(sim_jobs)))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(runtime.run_part, out_dir, d) for d in sim_jobs]
        results = [fu.result() for fu in futs]
    progress(f"{len(results)} part simulations finished on {workers} processes")

    signatures = {"tolerance_A": index["settings"]["tolerance_A"], "motors": motors, "parts": {r["part_number"]: r for r in results}}
    with open(os.path.join(out_dir, "signatures.json"), "w") as f:
        json.dump(signatures, f, indent=1)
    rulebook.build(out_dir)
    summary = {"name": os.path.basename(out_dir), "built_seconds": round(time.time() - t0, 2), "parts": len(parts),
               "simulated_parts": len(results), "motors": list(motors), "workers": workers,
               "undetectable": [r["part_number"] for r in results if not r["detectable_at_critical"]],
               "assumptions": assumptions, "tree": sorted(tree)}
    with open(os.path.join(out_dir, "project.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return summary
