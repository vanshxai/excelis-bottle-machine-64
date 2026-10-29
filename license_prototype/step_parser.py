"""
Lightweight STEP (ISO 10303 AP214) parser -- no CAD kernel, no pythonocc
dependency. STEP is plain ASCII text with numbered entities, so PRODUCT
names and assembly parent-child links (NEXT_ASSEMBLY_USAGE_OCCURRENCE)
are extractable with plain text parsing. This does NOT extract 3D
geometry/mesh -- only component identity and assembly structure, which
is exactly what formula_selector.py needs (it works off component TYPE,
not mesh).

This is the first real, automated "Geometry Extractor + Structure
Builder" step -- replacing what was done by hand (82 phone photos) for
the bottle machine, against a real external file this time.
"""
import argparse
import json
import re

PRODUCT_RE = re.compile(r"PRODUCT\(\s*'([^']*)'\s*,\s*'([^']*)'")
NAUO_RE = re.compile(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\(\s*'[^']*'\s*,\s*'([^']*)'")

# Component-name keyword -> our controlled vocabulary type (formula_selector.py's
# COMPONENT_TYPE_TO_DOMAINS keys). Real assemblies won't say "dc_motor" in plain
# text often -- this is the practical "Phenomena Mapper" heuristic: keyword match
# on the PRODUCT name against known mechanical/electrical vocabulary.
KEYWORD_TO_TYPE = {
    "servo": "servo", "motor": "dc_motor", "gearbox": "gearbox", "gear": "gearbox",
    "belt": "belt", "chain": "chain", "bearing": "bearing",
    "shaft": "shaft", "rod": "shaft", "disk": "disk_rotor", "rotor": "disk_rotor",
    "transformer": "transformer", "driver": "driver_vfd", "vfd": "driver_vfd",
    "sensor": "sensor", "battery": "battery", "pump": "pump_hydraulic",
    "valve": "pump_hydraulic", "heater": "heater_hvac",
    "bracket": "structure_frame", "plate": "structure_frame", "frame": "structure_frame",
    "panel": "electrical_panel", "bolt": "fastener", "nut": "fastener", "screw": "fastener",
    "microcontroller": "microcontroller", "esp32": "microcontroller",
}


def classify(name: str, fallback_text: str = "") -> str:
    """Try the component's own internal STEP name first. Real exports vary
    wildly -- SolidWorks assemblies (like as1) keep real part names, but
    Fusion 360 single-body exports often just say 'body'/'spline'. When the
    internal name is useless, fall back to the source filename, which is
    usually still descriptive (confirmed on a real Adafruit servo export)."""
    for text in (name, fallback_text):
        n = text.lower()
        for kw, ctype in KEYWORD_TO_TYPE.items():
            if kw in n:
                return ctype
    return "unclassified"


def parse_step(path: str) -> dict:
    import os
    filename_hint = os.path.splitext(os.path.basename(path))[0]

    with open(path, "r", errors="ignore") as f:
        text = f.read()
    # STEP entities often wrap across lines for readability -- collapse all
    # whitespace so an entity split mid-string still matches as one line.
    # (Found live: the servo file's root PRODUCT name splits right after the
    # opening quote, which silently produced zero matches before this fix.)
    text = re.sub(r"\s+", " ", text)

    products = {}  # name -> count of instances (from NAUO references)
    for m in PRODUCT_RE.finditer(text):
        name = m.group(1)
        products.setdefault(name, 0)

    instance_names = [m.group(1) for m in NAUO_RE.finditer(text)]
    # instance names look like 'bolt_1' (SolidWorks-style) or 'body:1'
    # (seen live in an Autodesk export) -- strip either trailing separator+number
    for inst in instance_names:
        base = re.sub(r"[_:]\d+$", "", inst)
        if base in products:
            products[base] += 1

    has_assembly_structure = len(instance_names) > 0

    components = []
    for name, count in products.items():
        if name.endswith("-assembly"):
            continue  # sub-assembly groupings, not physical parts themselves
        if count == 0:
            if has_assembly_structure:
                continue  # a real assembly file where this product is just never instanced
            count = 1  # single-part file (no NAUO at all) -- the product itself IS the one part
        ctype = classify(name, fallback_text=filename_hint)
        components.append({"name": name, "type": ctype, "instances_found": count})

    return {
        "root_product": next(iter(products), None),
        "unique_part_types": len(components),
        "total_instances": sum(c["instances_found"] for c in components),
        "components": components,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = parse_step(args.step)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    print(f"root product: {result['root_product']}")
    print(f"{result['unique_part_types']} unique part types, {result['total_instances']} total instances")
    for c in result["components"]:
        flag = "  <-- unclassified, needs vocabulary entry" if c["type"] == "unclassified" else ""
        print(f"  {c['name']:20s} type={c['type']:16s} x{c['instances_found']}{flag}")
