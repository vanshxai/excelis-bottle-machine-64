"""
Rulebook: the machine's fault-current ranges and warning levels, written as one readable file at build time
(rulebook.json), built only from the stored simulation tables and the user's own three levels per part.
Nothing here is invented: the four level names come from the user's fine / warning / critical answers.
"""
import json
import os

STYLE = {
    "fine": {"label": "Fine", "color": "#5ec269", "rule": "load is at or below the level you called fine"},
    "elevated": {"label": "Elevated", "color": "#e8cf5a", "rule": "load is above fine but below your warning level"},
    "warning": {"label": "Warning", "color": "#e0a940", "rule": "load has reached your warning level"},
    "critical": {"label": "Critical", "color": "#e5534b", "rule": "load has reached your critical level"},
}


def build(root, write=True):
    with open(os.path.join(root, "signatures.json")) as f:
        sig = json.load(f)
    with open(os.path.join(root, "machine_index.json")) as f:
        index = json.load(f)
    tol = sig["tolerance_A"]
    motors = {}
    for m, mm in sig["motors"].items():
        parts = []
        for pn, r in sig["parts"].items():
            if r["motor"] != m:
                continue
            L = r["levels"]
            d = {k: L[k]["delta_current_A"] for k in L}
            e = {k: L[k]["effort"] for k in L}
            dmax = r["sweep"][-1]["delta_current_A"]
            parts.append({
                "part": pn, "description": index["parts"][pn]["description"], "section": index["parts"][pn]["section_name"],
                "effort_label": r["effort_label"], "unit": r["effort_unit"], "detectable": r["detectable_at_critical"],
                "max_modelled_delta_A": dmax,
                "bands": [
                    {"band": "fine", "effort": [0.0, e["ok_max"]], "delta_A": [0.0, d["ok_max"]]},
                    {"band": "elevated", "effort": [e["ok_max"], e["warning"]], "delta_A": [d["ok_max"], d["warning"]]},
                    {"band": "warning", "effort": [e["warning"], e["critical"]], "delta_A": [d["warning"], d["critical"]]},
                    {"band": "critical", "effort": [e["critical"], 1.25 * e["critical"]], "delta_A": [d["critical"], dmax]},
                ],
            })
        # where more than one part could explain the same current change -> the area to look at
        cuts = sorted({0.0, tol} | {b for p in parts for bd in p["bands"] for b in bd["delta_A"]})
        shared = []
        for a, b in zip(cuts, cuts[1:]):
            if b <= a or b <= tol:
                continue
            mid = (a + b) / 2
            who = [p for p in parts if p["max_modelled_delta_A"] >= mid]
            names = [p["part"] for p in who]
            if not names:
                continue
            secs = {index["parts"][n]["section"] for n in names}
            area = (index["parts"][names[0]]["description"] if len(names) == 1 else
                    (index["sections"][next(iter(secs))]["name"] if len(secs) == 1 else f"everything driven by {m}"))
            if shared and shared[-1]["parts"] == names:
                shared[-1]["delta_A"][1] = b
            else:
                shared.append({"delta_A": [a, b], "parts": names, "area": area, "kind": "part" if len(names) == 1 else "area"})
        motors[m] = {"normal_A": mm["I_normal"], "description": index["parts"][m]["description"], "parts": parts, "current_ladder": shared}
    out = {"tolerance_A": tol, "style": STYLE,
           "reading": "extra current over the motor's normal running current; a change smaller than tolerance_A is treated as noise",
           "motors": motors}
    if write:
        with open(os.path.join(root, "rulebook.json"), "w") as f:
            json.dump(out, f, indent=1)
    return out
