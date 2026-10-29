"""
Runtime used by the generated per-part code files.

apply() is the only way a number is computed: it takes ONE formula from the project's stock, solves it
for the variable asked, and refuses (MissingInputs) if any value is not supplied or if a value is
supplied that the formula does not use. No defaults exist anywhere.
"""
import importlib.util
import json
import os

import numpy as np
import sympy as sp

from strict_solver import AmbiguousFormulas, MissingInputs, parse_formula_strings

_STOCK_CACHE = {}
_EXPR_CACHE = {}


def load_stock(project_root):
    if project_root not in _STOCK_CACHE:
        with open(os.path.join(project_root, "formulas_stock.json")) as f:
            raw = json.load(f)
        _STOCK_CACHE[project_root] = parse_formula_strings({k: v["equation"] for k, v in raw.items()})
    return _STOCK_CACHE[project_root]


_ACTIVE_ROOT = {"root": None}
TRACE = None  # when a list, apply() appends one record per formula step


def start_trace():
    global TRACE
    TRACE = []


def stop_trace():
    global TRACE
    t, TRACE = TRACE, None
    return t


def set_project(project_root):
    _ACTIVE_ROOT["root"] = project_root


def apply(formula, solve_for, **vals):
    root = _ACTIVE_ROOT["root"]
    eq = load_stock(root)[formula]
    key = (root, formula, solve_for)
    expr = _EXPR_CACHE.get(key)
    if expr is None:  # solving the equation for the asked variable is the slow part, so remember it
        target = sp.Symbol(solve_for)
        if str(eq.lhs) == solve_for:
            expr = eq.rhs
        else:
            sols = sp.solve(eq, target)
            if len(sols) != 1:
                raise AmbiguousFormulas(solve_for, {str(s): None for s in sols})
            expr = sols[0]
        _EXPR_CACHE[key] = expr
    need = sorted(str(s) for s in expr.free_symbols)
    missing = [n for n in need if n not in vals]
    if missing:
        raise MissingInputs(solve_for, {formula: {m: {} for m in missing}})
    unused = [k for k in vals if k not in need]
    if unused:
        raise ValueError(f"{formula} (solving for {solve_for}) does not use: {unused}")
    value = float(expr.subs({sp.Symbol(k): v for k, v in vals.items()}))
    if TRACE is not None:
        TRACE.append({"formula": formula, "equation": f"{eq.lhs} = {eq.rhs}", "solved": f"{solve_for} = {expr}",
                      "inputs": dict(vals), "output": {"name": solve_for, "value": value}})
    return value


# ---- motor model: output-shaft torque <-> current, from the nameplate ---------------------
def motor_kt(T_rated, I_rated, I_noload):
    """Torque per amp at the output shaft, from rated torque and rated current minus no-load current."""
    return apply("torque", "Kt", T=T_rated, I=I_rated - I_noload)


def motor_delta_current(dT, Kt):
    return apply("torque", "I", T=dT, Kt=Kt)


# ---- one part's simulation (run in its own process) --------------------------------------
def run_part(project_root, part_dir, n_points=26):
    set_project(project_root)
    with open(os.path.join(part_dir, "part.json")) as f:
        part = json.load(f)
    with open(os.path.join(project_root, "machine_index.json")) as f:
        index = json.load(f)
    motor = index["motors"][part["motor"]]
    spec = importlib.util.spec_from_file_location("part_code_" + part["part_number"], os.path.join(part_dir, "part_code.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    eff = part["effort"]
    efforts = np.linspace(0.0, 1.25 * eff["critical"], n_points)
    rows = []
    for e in efforts:
        dT = mod.motor_torque(float(e))
        dI = motor_delta_current(dT, motor["Kt"])
        rows.append({"effort": float(e), "motor_torque_Nm": dT, "delta_current_A": dI})
    levels = {}
    for name in ("ok_max", "warning", "critical"):
        dT = mod.motor_torque(float(eff[name]))
        levels[name] = {"effort": eff[name], "motor_torque_Nm": dT, "delta_current_A": motor_delta_current(dT, motor["Kt"])}
    tol = index["settings"]["tolerance_A"]
    out = {
        "part_number": part["part_number"], "motor": part["motor"], "effort_label": eff["label"], "effort_unit": eff["unit"],
        "levels": levels, "sweep": rows,
        "detectable_at_critical": levels["critical"]["delta_current_A"] > tol,
        "critical_over_tolerance": levels["critical"]["delta_current_A"] / tol,
    }
    with open(os.path.join(part_dir, "results.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out
