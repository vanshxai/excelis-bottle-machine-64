"""
Zero-guess forward-chaining solver.

Same wave mechanism as the core engine's solve_path() (fire every formula
whose inputs are all known, repeat), with every source of guessing removed:

- No default values are ever injected. Only what the caller passes in is known.
- No tie-breaking heuristics. If two formulas can both produce the same
  variable and give different numbers, the solver stops (AmbiguousFormulas)
  instead of silently picking "shortest" or "most confident".
- If the target cannot be reached it stops (MissingInputs) and says exactly
  which source values still have to be supplied, so the app can ask for them.

Takes a plain dict of {name: sympy.Eq}; it does not import the core engine,
so it can be bundled with whatever formula subset a machine is built from.
"""
import re

import sympy as sp

# sympy built-ins that collide with real symbol names in this formula set
# (Q, E, I, S, N, beta, gamma...). Only real math functions keep their sympy
# meaning; every other identifier is forced into a plain Symbol.
_MATH_FUNCS = {"sin", "cos", "tan", "asin", "acos", "atan", "atan2",
               "exp", "log", "sqrt", "pi", "Abs", "Max", "Min"}
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class MissingInputs(Exception):
    """Target not reachable.
    needs = {formula that could produce the target:
               {missing input: {other formula that could derive it: [what that one still needs]}}}
    An empty inner dict means nothing can derive it: it must be supplied by a person."""

    def __init__(self, target, needs):
        self.target = target
        self.needs = needs
        lines = [f"cannot compute '{target}' - missing values:"]
        if not needs:
            lines.append("  no formula in this set produces it")
        for formula, entries in needs.items():
            lines.append(f"  via {formula}:")
            for sym, alts in entries.items():
                if alts:
                    how = "; or derive via " + ", ".join(f"{g} (needs {v})" for g, v in alts.items())
                else:
                    how = " (no formula derives it - must be supplied)"
                lines.append(f"    - {sym}{how}")
        super().__init__("\n".join(lines))

    def ask_for(self):
        """Smallest set of values to ask a person for, taken directly from the
        cheapest formula route."""
        if not self.needs:
            return {self.target}
        return set(min(self.needs.values(), key=len).keys())


class AmbiguousFormulas(Exception):
    """Two or more formulas can produce the same variable and disagree."""

    def __init__(self, output, values):
        self.output = output
        self.values = values
        super().__init__(f"'{output}' can be computed by several formulas that disagree: {values}. "
                         "A person must choose which one applies.")


def parse_formula_strings(formula_strings: dict) -> dict:
    """{'name': 'lhs = rhs'} -> {'name': sympy.Eq} with collision-safe symbols."""
    out = {}
    for name, text in formula_strings.items():
        lhs_s, rhs_s = text.split("=", 1)
        tokens = set(_IDENT_RE.findall(text)) - _MATH_FUNCS
        syms = {t: sp.Symbol(t) for t in tokens}
        out[name] = sp.Eq(sp.sympify(lhs_s.strip(), locals=syms), sp.sympify(rhs_s.strip(), locals=syms))
    return out


def _inputs(eq):
    return [str(s) for s in eq.rhs.free_symbols]


def _evaluate(eq, known):
    return float(eq.rhs.subs({sp.Symbol(i): known[i] for i in _inputs(eq)}))


def producers(formulas: dict) -> dict:
    """output symbol -> list of formula names that produce it"""
    out = {}
    for name, eq in formulas.items():
        out.setdefault(str(eq.lhs), []).append(name)
    return out


def explain_missing(formulas: dict, known: dict, target: str) -> dict:
    """See MissingInputs.needs. Routes that loop back through the target are dropped."""
    prod = producers(formulas)
    result = {}
    for fname in prod.get(target, []):
        entries = {}
        for inp in _inputs(formulas[fname]):
            if inp in known:
                continue
            alts = {}
            for g in prod.get(inp, []):
                g_in = _inputs(formulas[g])
                if g == fname or target in g_in:
                    continue
                alts[g] = sorted(i for i in g_in if i not in known)
            entries[inp] = alts
        result[fname] = entries
    return result


def solve_strict(formulas: dict, given: dict, target: str, rel_tol=1e-6, max_waves=60) -> dict:
    """Return {'result', 'values', 'trace'}; raise MissingInputs / AmbiguousFormulas
    instead of ever guessing."""
    known = dict(given)
    origin = {k: "given" for k in known}
    trace = []

    if target in known:
        return {"result": known[target], "values": known, "trace": trace}

    for _ in range(max_waves):
        if target in known:
            break
        candidates = {}
        for name, eq in formulas.items():
            out = str(eq.lhs)
            ins = _inputs(eq)
            if out in known or not ins or not all(i in known for i in ins):
                continue
            candidates.setdefault(out, []).append(name)
        if not candidates:
            break
        for out, names in candidates.items():
            values = {n: _evaluate(formulas[n], known) for n in names}
            ref = values[names[0]]
            if any(abs(v - ref) > rel_tol * max(1.0, abs(ref)) for v in values.values()):
                raise AmbiguousFormulas(out, values)
            first = formulas[names[0]]
            known[out] = ref
            origin[out] = "derived"
            trace.append({
                "formula": names[0],
                "also_agrees": names[1:],
                "output": out,
                "value": ref,
                "inputs": {i: {"value": known[i], "origin": origin[i]} for i in _inputs(first)},
            })

    if target not in known:
        raise MissingInputs(target, explain_missing(formulas, known, target))
    return {"result": known[target], "values": known, "trace": trace}
