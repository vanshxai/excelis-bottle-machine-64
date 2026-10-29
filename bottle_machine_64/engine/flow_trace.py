"""
Step-by-step trace of one part's calculation, recomputed from scratch for whatever values are passed in.

Used by the Formula Flow dashboard: change any value (the load, a friction coefficient, a radius, the motor
nameplate, the warning levels) and every formula downstream is run again, so nothing is stale.
"""
import importlib.util
import inspect
import json
import os
import threading

import runtime

_LOCK = threading.Lock()
BANDS = ["fine", "elevated", "warning", "critical"]


def _load(root, pn):
    with open(os.path.join(root, "machine_index.json")) as f:
        index = json.load(f)
    pdir = os.path.join(root, index["parts"][pn]["dir"])
    with open(os.path.join(pdir, "part.json")) as f:
        part = json.load(f)
    spec = importlib.util.spec_from_file_location("trace_" + pn, os.path.join(pdir, "part_code.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return index, part, mod


def _groups(values):
    """Constants that hold the same number from the same source are one physical quantity (e.g. R_SELF and
    R_MS00303); edit them together."""
    out = {}
    for name, v in values.items():
        out.setdefault((v["value"], v["source"], v["unit"]), []).append(name)
    return list(out.values())


def _band(effort, lv):
    if effort <= lv["ok_max"]:
        return "fine"
    if effort < lv["warning"]:
        return "elevated"
    if effort < lv["critical"]:
        return "warning"
    return "critical"


def trace_part(root, pn, effort=None, overrides=None):
    ov = overrides or {}
    with _LOCK:
        runtime.set_project(root)
        index, part, mod = _load(root, pn)
        if not part.get("effort"):
            raise ValueError(f"{pn} has no load model of its own (it only passes load along).")
        motor = dict(index["motors"][part["motor"]])
        for k, v in (ov.get("motor") or {}).items():
            motor[k] = float(v)
        lv = {k: float(part["effort"][k]) for k in ("ok_max", "warning", "critical")}
        for k, v in (ov.get("levels") or {}).items():
            lv[k] = float(v)
        groups = _groups(part["values"])
        for k, v in (ov.get("constants") or {}).items():
            for g in groups:
                if k in g:
                    for name in g:
                        setattr(mod, name, float(v))
        e = float(effort) if effort is not None else lv["warning"]

        runtime.start_trace()
        try:
            Kt = runtime.motor_kt(motor["T_rated"], motor["I_rated"], motor["I_noload"])
            n_kt = len(runtime.TRACE)
            dT = mod.motor_torque(e)
            n_chain = len(runtime.TRACE)
            dI = runtime.motor_delta_current(dT, Kt)
            steps = runtime.stop_trace()
        except Exception:
            runtime.stop_trace()
            raise
        for i, s in enumerate(steps):
            s["stage"] = "motor_constant" if i < n_kt else ("chain" if i < n_chain else "current")
        levels_A = {}
        for k in ("ok_max", "warning", "critical"):
            levels_A[k] = runtime.motor_delta_current(mod.motor_torque(lv[k]), Kt)

        variables = [{"key": "effort", "group": "load", "label": part["effort"]["label"], "unit": part["effort"]["unit"], "value": e,
                      "min": 0.0, "max": 1.25 * lv["critical"]}]
        src = inspect.getsource(mod.motor_torque)
        for g in _groups(part["values"]):
            used = [n for n in g if n in src]
            if not used:
                continue
            v = part["values"][used[0]]
            label = {"MU": "Friction coefficient"}.get(used[0], "Radius (m)" if used[0].startswith("R_") else used[0])
            if used[0].startswith("R_") and used[0] != "R_SELF":
                label = f"Radius of {used[0][2:]} (m)"
            elif used[0] == "R_SELF":
                label = f"Radius of {pn} (m)"
            variables.append({"key": g[0], "group": "part", "label": label, "unit": v["unit"], "value": float(getattr(mod, used[0])),
                              "note": v["source"], "also": g[1:]})
        for k, label, unit in (("T_rated", "Motor rated output torque", "N*m"), ("I_rated", "Motor rated current", "A"),
                               ("I_noload", "Motor no-load current", "A")):
            variables.append({"key": k, "group": "motor", "label": label, "unit": unit, "value": motor[k]})
        for k, label in (("ok_max", "Still fine up to"), ("warning", "Warning at"), ("critical", "Critical at")):
            variables.append({"key": k, "group": "levels", "label": label, "unit": part["effort"]["unit"], "value": lv[k]})
        return {
            "part": pn, "description": part["description"], "type": part["type_label"], "role": part["role"], "chain": part["chain"],
            "motor": part["motor"], "effort_label": part["effort"]["label"], "effort_unit": part["effort"]["unit"], "effort": e,
            "steps": steps, "Kt": Kt, "motor_torque_Nm": dT, "delta_current_A": dI, "levels_A": levels_A,
            "band": _band(e, lv), "variables": variables,
        }
