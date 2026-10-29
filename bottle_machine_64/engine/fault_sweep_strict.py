"""
Zero-guess fault sweep.

The prototype version carried a table of assumed constants (R0 = 5 ohm,
T_final, tau_thermal ...) and fixed sweep ranges. This version carries none:
the caller supplies every constant and the sweep range (in the app these come
from the user's answers and the part's plain-language form). If something is
missing it raises MissingInputs listing exactly what to ask for.
"""
import sympy as sp

from strict_solver import MissingInputs, solve_strict, _inputs, _evaluate


def required_inputs(formulas: dict, fault_name: str, sweep_var: str, known: dict) -> set:
    """Source values still needed (besides the swept one) to evaluate this fault formula."""
    eq = formulas[fault_name]
    target = str(eq.lhs)
    others = {n: e for n, e in formulas.items() if str(e.lhs) != target}
    probe = dict(known)
    probe[sweep_var] = 0.0  # placeholder only to ask "what else is missing?"; never used as a result
    need = set()
    for inp in _inputs(eq):
        if inp in probe:
            continue
        try:
            solve_strict(others, probe, inp)
        except MissingInputs as e:
            need |= e.ask_for()
    return need


def sweep(formulas: dict, fault_name: str, sweep_var: str, lo: float, hi: float, steps: int, known: dict) -> list:
    """Evaluate one fault formula while `sweep_var` runs lo..hi. Every other value
    must be in `known` or derivable from it through the other formulas."""
    if steps < 2:
        raise ValueError("steps must be at least 2")
    eq = formulas[fault_name]
    target = str(eq.lhs)
    # formulas sharing this fault formula's output symbol are excluded so a sibling
    # can never silently stand in for the one being swept
    others = {n: e for n, e in formulas.items() if str(e.lhs) != target}

    missing = required_inputs(formulas, fault_name, sweep_var, known)
    if missing:
        raise MissingInputs(target, {fault_name: {sym: {} for sym in missing}})

    rows = []
    for i in range(steps):
        val = lo + (hi - lo) * i / (steps - 1)
        k = dict(known)
        k[sweep_var] = val
        for inp in _inputs(eq):
            if inp not in k:
                k[inp] = solve_strict(others, k, inp)["result"]
        rows.append({"fault": fault_name, "sweep_var": sweep_var, "sweep_value": val,
                     "signature_var": target, "signature_value": _evaluate(eq, k)})
    return rows
