"""Internal dev check (not shipped). Run: python3 dev_checks/check_zero_guess.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "faulter-formula-brain"))

import sympy as sp  # noqa: E402
from formulas import FORMULAS  # noqa: E402  (read from the frozen backup; engine copy stays untouched)
from strict_solver import AmbiguousFormulas, MissingInputs, parse_formula_strings, solve_strict  # noqa: E402
from fault_sweep_strict import required_inputs, sweep  # noqa: E402

passed = 0


def check(label, ok):
    global passed
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        sys.exit(1)
    passed += 1


# 1. nothing is filled in behind our back
try:
    solve_strict(FORMULAS, {}, "T_chip")
    check("T_chip with no inputs must not solve", False)
except MissingInputs as e:
    check("T_chip with no inputs stops and lists what to ask", len(e.ask_for()) > 0)

# 2. the prototype engine WOULD have silently filled gaps here; strict does not
import brain  # noqa: E402
proto = brain.solve_path({"P": 1.5, "T_amb": 25.0}, "T_chip")
strict_stopped = False
try:
    solve_strict(FORMULAS, {"P": 1.5, "T_amb": 25.0}, "T_chip")
except MissingInputs as e:
    strict_stopped = "R_th" in e.ask_for()
check("prototype answers T_chip from P and T_amb alone (it fills R_th itself); strict stops and asks for R_th",
      proto.get("result") is not None and strict_stopped)

# 3. a fully specified chain solves and tracks where every number came from
r = solve_strict(FORMULAS, {"I": 2.0, "R": 5.0}, "V")
check("V = I*R solves with given values (V=10)", abs(r["result"] - 10.0) < 1e-9)
check("trace marks inputs as 'given'", r["trace"][0]["inputs"]["I"]["origin"] == "given")

# 4. disagreeing formulas are an error, agreeing ones are fine
toy = parse_formula_strings({"a": "X = A*B", "b": "X = C*D"})
try:
    solve_strict(toy, {"A": 2.0, "B": 3.0, "C": 4.0, "D": 5.0}, "X")
    check("disagreeing formulas must stop", False)
except AmbiguousFormulas:
    check("disagreeing formulas stop instead of picking one", True)
ok = solve_strict(toy, {"A": 2.0, "B": 3.0, "C": 3.0, "D": 2.0}, "X")
check("agreeing formulas are accepted (X=6)", abs(ok["result"] - 6.0) < 1e-9 and ok["trace"][0]["also_agrees"] == ["b"])

# 5. sweeps ask instead of assuming
fs = {k: FORMULAS[k] for k in ("resistance_temperature", "torque_ripple")}
need = required_inputs(fs, "resistance_temperature", "T_temp", {"R0": 4.0})
check("sweep reports missing alpha_temp and T0_temp", need == {"alpha_temp", "T0_temp"})
try:
    sweep(fs, "resistance_temperature", "T_temp", 25, 120, 5, {"R0": 4.0})
    check("sweep with gaps must stop", False)
except MissingInputs:
    check("sweep with gaps stops", True)
rows = sweep(fs, "resistance_temperature", "T_temp", 25, 125, 3, {"R0": 4.0, "alpha_temp": 0.00393, "T0_temp": 25.0})
check("sweep with every value supplied runs (R at 125C = 4*(1+0.393))",
      abs(rows[-1]["signature_value"] - 4.0 * 1.393) < 1e-9)

print(f"\n{passed} checks passed - zero defaults, zero silent choices.")
