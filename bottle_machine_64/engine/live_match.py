"""
Live matching: observed change in each motor's current -> which parts could explain it -> the smallest
area worth looking at. Works from the stored simulation tables only.

Honest by design: if several parts could cause the same change, it says so and points at the
smallest enclosing area (a section, or the motor's whole branch) instead of naming one part.
"""
import json
import os

import numpy as np

BAND_ORDER = ["fine", "elevated", "warning", "critical"]


def load(project_root):
    with open(os.path.join(project_root, "signatures.json")) as f:
        sig = json.load(f)
    with open(os.path.join(project_root, "machine_index.json")) as f:
        index = json.load(f)
    return sig, index


def band(effort, levels):
    if effort <= levels["ok_max"]["effort"]:
        return "fine"
    if effort < levels["warning"]["effort"]:
        return "elevated"
    if effort < levels["critical"]["effort"]:
        return "warning"
    return "critical"


def match(project_root, observed, tol=None):
    sig, index = load(project_root)
    tol = sig["tolerance_A"] if tol is None else tol
    findings, channels = [], {}
    for m, mm in sig["motors"].items():
        obs = float(observed.get(m, 0.0))
        channels[m] = {"delta_A": obs, "normal_A": mm["I_normal"], "now_A": mm["I_normal"] + obs, "quiet": abs(obs) <= tol}
        if abs(obs) <= tol:
            continue
        cands = []
        if obs > 0:
            for pn, r in sig["parts"].items():
                if r["motor"] != m:
                    continue
                eff = np.array([row["effort"] for row in r["sweep"]])
                dI = np.array([row["delta_current_A"] for row in r["sweep"]])
                if dI.max() < obs - tol:
                    continue
                lo, hi = max(obs - tol, 0.0), min(obs + tol, float(dI.max()))
                e_lo, e_hi = float(np.interp(lo, dI, eff)), float(np.interp(hi, dI, eff))
                e_mid = float(np.interp(min(obs, float(dI.max())), dI, eff))
                cands.append({
                    "part": pn, "description": index["parts"][pn]["description"], "section": index["parts"][pn]["section_name"],
                    "effort_label": r["effort_label"], "unit": r["effort_unit"],
                    "effort_estimate": e_mid, "effort_range": [e_lo, e_hi],
                    "band": band(e_mid, r["levels"]), "band_range": [band(e_lo, r["levels"]), band(e_hi, r["levels"])],
                })
        finding = {"motor": m, "observed_A": obs, "candidates": cands}
        if not cands:
            finding["area"] = {"kind": "branch", "name": f"everything driven by {m}",
                               "parts": [p for p, d in index["parts"].items() if d["motor"] == m]}
            finding["note"] = ("The current went down - none of the modelled faults lower it." if obs < 0 else
                               "The change is larger than any single modelled fault on this motor (or too small for any part to explain).")
        elif len(cands) == 1:
            pn = cands[0]["part"]
            finding["area"] = {"kind": "part", "name": f"{pn} {index['parts'][pn]['description']}", "parts": [pn]}
        else:
            secs = {index["parts"][c["part"]]["section"] for c in cands}
            if len(secs) == 1:
                s = next(iter(secs))
                finding["area"] = {"kind": "section", "name": index["sections"][s]["name"], "parts": index["sections"][s]["parts"]}
            else:
                finding["area"] = {"kind": "branch", "name": f"everything driven by {m}",
                                   "parts": [p for p, d in index["parts"].items() if d["motor"] == m]}
        finding["worst_band"] = max((c["band"] for c in cands), key=BAND_ORDER.index) if cands else "critical"
        findings.append(finding)
    return {"tolerance_A": tol, "channels": channels, "findings": findings}


def replay(project_root, part, level, noise_A=0.0, seed=1):
    """Fake what a sensor would see if `part` carried `level` ('ok_max'|'warning'|'critical' or a number)."""
    sig, _ = load(project_root)
    rng = np.random.default_rng(seed)
    observed = {m: 0.0 for m in sig["motors"]}
    if part:
        r = sig["parts"][part]
        eff = float(r["levels"][level]["effort"]) if isinstance(level, str) else float(level)
        dI = float(np.interp(eff, [row["effort"] for row in r["sweep"]], [row["delta_current_A"] for row in r["sweep"]]))
        observed[r["motor"]] = dI
    for m in observed:
        observed[m] += float(rng.normal(0.0, noise_A)) if noise_A > 0 else 0.0
    return observed
