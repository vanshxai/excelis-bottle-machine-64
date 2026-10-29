"""
THE MISSING PIECE from last time: given the MINIMUM data an industrialist
would actually hand over -- a short list of "this machine has a motor, a
belt, a bearing, a sensor" -- automatically identify which slice of the
333-formula Brain that machine needs, and emit it in exactly the JSON
shape issue_key.py already consumes.

Input (per machine): a plain list of components, each just a name + a
type from a small controlled vocabulary (COMPONENT_TYPE_TO_DOMAINS below).
No CAD, no assembly file, no geometry -- this is deliberately the
lightest input that still lets us reason about physics domains.

Output: subset.json (machine name + {formula_name: "lhs = rhs", ...}),
pulled LIVE from formulas.py -- not hand-typed.

This IS the "phenomena mapper" from the framework brainstorm, built as a
real rule table instead of a concept.
"""
import argparse
import json
import os
import sys

BRAIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "faulter-formula-brain")
sys.path.insert(0, BRAIN_DIR)
from formulas import FORMULAS, FORMULA_DOMAINS  # noqa: E402

# ---------------------------------------------------------------------------
# The controlled vocabulary. An industrialist describing their machine in
# plain terms ("motor", "belt", "bearing") maps to real Brain domains here.
# universal + fault_pattern are added to EVERY machine automatically --
# vibration/fatigue/heat-transfer and the degradation-growth models apply
# to anything mechanical, regardless of what it is. manufacturing/design/
# power/illumination joined them 2026-09-17: verified against the real
# domain list that NOTHING in the vocabulary below reached them (dead
# code, unreachable regardless of any answer) -- each is small (2-6
# formulas) and broadly applicable enough that always-including is
# cheaper and safer than inventing a question to gate them.
# ---------------------------------------------------------------------------
ALWAYS_INCLUDE = {"universal", "fault_pattern", "manufacturing", "design", "power", "illumination"}

COMPONENT_TYPE_TO_DOMAINS = {
    # magnetic added to every motor/transformer type below -- same 2026-09-17
    # sweep found it was verified-unreachable (flux/permeability formulas
    # that clearly apply to any magnetic-circuit component, but nothing
    # pointed to them).
    "dc_motor":          {"dc_motor_industrial", "electrical", "mechanical", "thermal", "magnetic"},
    "servo":             {"dc_motor_industrial", "control_systems", "electrical", "mechanical", "thermal", "magnetic"},
    "induction_motor":   {"induction_motor", "electrical", "power_systems", "thermal", "magnetic"},
    "synchronous_motor": {"synchronous_machine", "electrical", "power_systems", "magnetic"},
    "gearbox":           {"mechanical_drives", "materials", "mechanical"},
    "belt":              {"mechanical_drives", "materials"},
    "chain":             {"mechanical_drives", "materials"},
    "bearing":           {"mechanical_drives", "materials", "thermal"},
    "shaft":             {"mechanical", "materials"},
    "disk_rotor":        {"mechanical", "materials"},
    "transformer":       {"transformer", "electrical", "power_systems", "magnetic"},
    "driver_vfd":        {"electronics", "control_systems", "power_systems"},
    "sensor":            {"instrumentation", "electronics"},
    "battery":           {"battery_chemistry", "electrical"},
    # chemistry added here 2026-09-17 -- previously verified-unreachable.
    # Chemical dosing/mixing in an industrial machine is most often done
    # through a pump, so this is where "yes" to a chemical-process question
    # actually lands, rather than leaving chemistry with no trigger at all.
    "pump_hydraulic":    {"hydraulics", "mechanical", "chemistry"},
    "heater_hvac":       {"hvac_refrigeration", "thermal", "thermodynamic_cycles"},
    "structure_frame":   {"civil_structural", "materials", "welding_joints"},
    "electrical_panel":  {"electrical", "power_systems"},
    "microcontroller":   {"gpio", "electronics", "timing"},
    "rf_module":         {"rf", "electronics"},
    "pressure_vessel":   {"pressure_vessels", "thermodynamic_cycles"},
    "fastener":          {"welding_joints", "materials"},
    # aerospace, renewable_energy: deliberately left unreachable. No current
    # customer profile needs them, and inventing a placeholder component
    # type (e.g. "solar_panel") with no real Q&A question behind it would
    # be guessing, not a fix. The formulas themselves are untouched in the
    # core engine -- wiring real types for them is future work when an
    # actual aerospace/renewable customer is in front of us, not now.
}


def domains_for_machine(components: list) -> set:
    domains = set(ALWAYS_INCLUDE)
    unknown_types = []
    for c in components:
        ctype = c["type"]
        if ctype in COMPONENT_TYPE_TO_DOMAINS:
            domains |= COMPONENT_TYPE_TO_DOMAINS[ctype]
        else:
            unknown_types.append(ctype)
    return domains, unknown_types


def select_formulas(domains: set) -> dict:
    return {
        name: f"{FORMULAS[name].lhs} = {FORMULAS[name].rhs}"
        for name, dom in FORMULA_DOMAINS.items()
        if dom in domains
    }


def build_subset(machine_name: str, components: list) -> dict:
    domains, unknown = domains_for_machine(components)
    formulas = select_formulas(domains)
    return {
        "machine": machine_name,
        "input_components": components,
        "domains_identified": sorted(domains),
        "unrecognized_component_types": unknown,
        "formula_count": f"{len(formulas)} of {len(FORMULAS)} total",
        "formulas": formulas,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--components", required=True, help="path to a components.json list")
    ap.add_argument("--machine-name", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.components) as f:
        components = json.load(f)

    subset = build_subset(args.machine_name, components)
    with open(args.out, "w") as f:
        json.dump(subset, f, indent=2)

    print(f"{args.machine_name}: identified domains {subset['domains_identified']}")
    print(f"-> {subset['formula_count']} formulas selected -> {args.out}")
    if subset["unrecognized_component_types"]:
        print(f"!! unrecognized component types (ignored): {subset['unrecognized_component_types']}")
