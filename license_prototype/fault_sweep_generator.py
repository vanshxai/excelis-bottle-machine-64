"""
Fault-sweep generator -- turns a solved/licensed formula subset into the
actual current-signature database: for every motor-type component in the
machine, sweep each applicable fault mode (severity growth, resistance
drift, torque ripple) across a realistic range and record what happens at
every reachable sink variable (current, torque, resistance...).

Deliberately scoped to ONLY the formulas in the subset that was actually
selected/licensed for this machine (out/subset_*.json) -- not the full
333-formula Brain. This is what the customer's own local run would
actually have available, so the sweep has to be faithful to that, not to
an idealized full engine.

The forward-chain solver here is a standalone reimplementation of
brain.py's solve_path() wave logic (same mechanism: fire every formula
whose inputs are all known, repeat until nothing new fires), so this
runs without needing a live Brain server -- appropriate for a batch job
that calls it hundreds of times across a sweep.
"""
import argparse
import json
import re

import sympy as sp

# ---------------------------------------------------------------------------
# Fault-relevant formulas already confirmed in the core engine (see the
# critical-thinking pass a few messages back). Each entry: which symbol is
# the "knob" to sweep, and its severity/degradation range.
# ---------------------------------------------------------------------------
FAULT_FORMULAS = {
    "severity_growth_asymptotic": {"sweep_var": "s_sev", "range": (0.0, 0.9, 10)},
    "severity_growth_linear": {"sweep_var": "s_sev", "range": (0.0, 0.9, 10)},
    "resistance_temperature": {"sweep_var": "T_temp", "range": (25.0, 120.0, 10)},  # deg C, ambient to hot
    "torque_ripple": {"sweep_var": "k_unbal", "range": (0.0, 0.3, 10)},  # 0 = balanced, 0.3 = significant eccentricity
    "flux_thermal_derating": {"sweep_var": "T_temp", "range": (25.0, 150.0, 10)},
}

MOTOR_TYPES = {"dc_motor", "servo", "induction_motor", "synchronous_motor"}


# sympy has built-in globals that collide with real symbol names in this
# formula set -- Q (heat/flow) collides with sympy.Q (assumptions), E
# (back-emf) with Euler's number, I (current) with the imaginary unit,
# S with sympy.S, N with sympy.N, beta/gamma with special functions.
# Only actual math functions/constants used in these formulas should
# resolve to sympy's real meaning; every other bare identifier must be
# forced into a plain Symbol via explicit locals, or sympify silently
# picks the wrong one and breaks downstream .subs()/.free_symbols calls.
_MATH_FUNCS = {"sin", "cos", "tan", "asin", "acos", "atan", "atan2",
               "exp", "log", "sqrt", "pi", "Abs", "Max", "Min"}
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_subset_formulas(subset: dict) -> dict:
    """Reconstruct sympy Eq objects from the subset's 'lhs = rhs' strings."""
    formulas = {}
    for name, eq_str in subset["formulas"].items():
        lhs_str, rhs_str = eq_str.split("=", 1)
        tokens = set(_IDENT_RE.findall(eq_str)) - _MATH_FUNCS
        local_syms = {t: sp.Symbol(t) for t in tokens}
        lhs = sp.sympify(lhs_str.strip(), locals=local_syms)
        rhs = sp.sympify(rhs_str.strip(), locals=local_syms)
        formulas[name] = sp.Eq(lhs, rhs)
    return formulas


def forward_chain_all(formulas: dict, known: dict, max_waves=30) -> dict:
    """Standalone wave-based forward chain, scoped to `formulas` only --
    same mechanism as brain.py's solve_path() (fire every formula whose
    inputs are all known, repeat until nothing new fires), reimplemented
    so this can run in a batch loop without a live server. Returns the
    FULL expanded known-dict (every symbol reached), not just one target
    -- callers that want everything reachable, not one value, use this."""
    known = dict(known)
    wave = 0
    while wave < max_waves:
        fired_any = False
        for name, eq in formulas.items():
            output = str(eq.lhs)
            if output in known:
                continue
            inputs = [str(s) for s in eq.rhs.free_symbols]
            if inputs and all(i in known for i in inputs):
                try:
                    known[output] = float(eq.rhs.subs({sp.Symbol(i): known[i] for i in inputs}))
                    fired_any = True
                except Exception:
                    continue
        if not fired_any:
            break
        wave += 1
    return known


# Reasonable defaults for the OTHER variables each fault formula needs,
# beyond the swept one. These are ESTIMATED, not measured -- flagged as
# such deliberately. Real per-component values (from a real nameplate)
# should override these when known.
DEFAULT_KNOWNS = {
    "R0": 5.0,          # ohms, nominal winding resistance -- estimated
    "alpha_temp": 0.00393,  # /degC, copper winding temp coefficient -- real physical constant, not a guess
    "T0_temp": 25.0,    # deg C, reference temp -- standard assumption
    "T_amb": 25.0,      # deg C
    "T_final": 90.0,    # deg C, thermal steady-state target -- estimated
    "t_time": 600.0,    # s, 10 min into a thermal transient -- arbitrary checkpoint
    "tau_thermal": 300.0,  # s, thermal time constant -- estimated
    "k_growth": 0.5,    # linear severity growth rate -- estimated
    "T_nom": 1.0,        # N*m, nominal torque -- placeholder, should come from real motor rating
    "omega_t": 1.0,
    "t_ripple": 1.5707963,  # pi/(2*omega_t) -- evaluates sin() at its peak, so the
                            # swept k_unbal actually shows up as peak ripple amplitude
                            # instead of always landing on sin(0)=0 and looking flat
    "Phi0": 1.0,
    "k_demag": 0.3,
    "T_max_demag": 180.0,
}


def sweep_component(formulas: dict, component_name: str, confidence_note: str) -> list:
    rows = []
    for fault_name, spec in FAULT_FORMULAS.items():
        if fault_name not in formulas:
            continue  # this fault mode's formula isn't in the licensed subset for this machine
        sweep_var = spec["sweep_var"]
        lo, hi, steps = spec["range"]
        target = str(formulas[fault_name].lhs)

        for i in range(steps):
            val = lo + (hi - lo) * i / (steps - 1)
            known = dict(DEFAULT_KNOWNS)
            known[sweep_var] = val

            # Solve for any needed UPSTREAM inputs using every formula
            # EXCEPT ones that share this fault formula's own output --
            # several fault formulas collide on the same symbol (e.g.
            # severity_growth_asymptotic/_linear/resistance_temperature
            # all produce R). Without this exclusion, the generic wave
            # solver can silently fire a sibling formula instead of the
            # one actually being swept, mislabeling the result.
            other_formulas = {n: eq for n, eq in formulas.items()
                               if str(eq.lhs) != target}
            expanded = forward_chain_all(other_formulas, known)  # any indirect/upstream inputs the fault formula needs

            fault_eq = formulas[fault_name]
            fault_inputs = [str(s) for s in fault_eq.rhs.free_symbols]
            result = None
            if all(i in expanded for i in fault_inputs):
                try:
                    result = float(fault_eq.rhs.subs({sp.Symbol(i): expanded[i] for i in fault_inputs}))
                except Exception:
                    result = None

            if result is not None:
                rows.append({
                    "component": component_name,
                    "fault_type": fault_name,
                    "sweep_variable": sweep_var,
                    "sweep_value": round(val, 4),
                    "signature_variable": target,
                    "signature_value": round(result, 6),
                    "defaults_used": confidence_note,
                })
    return rows


def generate(subset_path: str, out_path: str):
    with open(subset_path) as f:
        subset = json.load(f)
    formulas = parse_subset_formulas(subset)

    motor_components = [c for c in subset["input_components"] if c["type"] in MOTOR_TYPES]

    all_rows = []
    for c in motor_components:
        rows = sweep_component(formulas, c["name"], confidence_note="estimated defaults, not real nameplate data")
        all_rows.extend(rows)

    database = {
        "machine": subset["machine"],
        "motor_components_swept": [c["name"] for c in motor_components],
        "fault_formulas_available": [f for f in FAULT_FORMULAS if f in formulas],
        "row_count": len(all_rows),
        "signature_rows": all_rows,
    }
    with open(out_path, "w") as f:
        json.dump(database, f, indent=2)

    print(f"{subset['machine']}: swept {len(motor_components)} motor component(s)")
    print(f"fault formulas available in this subset: {database['fault_formulas_available']}")
    print(f"{len(all_rows)} signature rows -> {out_path}")
    return database


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    generate(args.subset, args.out)
