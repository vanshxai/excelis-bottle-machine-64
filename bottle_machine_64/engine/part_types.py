"""
Part-type library (v0, enough for the mini sorter; the Bottle Machine 64 types are added later).

Each type says, in plain language:
  - how to recognise it from a BOM description (a SUGGESTION - the user always confirms),
  - what the user is asked about it,
  - what physical quantity ("effort") a fault adds, and which formulas turn that effort
    into a torque the motor has to supply.
"""

TYPES = {
    "motor_dc": {
        "label": "DC gearmotor", "kind": "motor",
        "words": ["dc gearmotor", "dc motor", "gearmotor, dc", "vdc"],
    },
    "motor_bldc": {
        "label": "Brushless gearmotor", "kind": "motor",
        "words": ["brushless", "bldc"],
    },
    "shaft": {
        "label": "Shaft", "kind": "driven", "words": ["shaft"],
        "params": [{"key": "mu", "label": "Friction coefficient of the shaft's bearings",
                    "unit": "", "hint": "e.g. 0.002 for a ball bearing"}],
        "effort": {"label": "Extra sideways load on the shaft's bearings", "unit": "N",
                   "ask": "How much extra sideways load is still fine, when does it become a warning, and when is it critical?"},
        "geometry": ["radius_mm"], "quantity": "torque",
    },
    "rotary_disk": {
        "label": "Rotating disk", "kind": "driven", "words": ["disk", "disc"],
        "params": [{"key": "mu", "label": "Friction between a stuck bottle (or hand) and the disk",
                    "unit": "", "hint": "e.g. 0.3"}],
        "effort": {"label": "Extra force pressing against the disk's rim", "unit": "N",
                   "ask": "How much extra force against the disk is fine, a warning, and critical?"},
        "geometry": ["radius_mm"], "quantity": "torque",
    },
    "drive_pulley": {
        "label": "Drive pulley (on the motor shaft)", "kind": "driven", "words": ["drive pulley"],
        "geometry": ["radius_mm"], "quantity": None,
    },
    "idler_pulley": {
        "label": "Idler pulley", "kind": "driven", "words": ["idler"],
        "effort": {"label": "Extra drag turning the idler pulley", "unit": "N*m",
                   "ask": "How much extra drag on the idler is fine, a warning, and critical?"},
        "geometry": ["radius_mm"], "quantity": "torque",
    },
    "belt": {
        "label": "Belt", "kind": "driven", "words": ["belt"],
        "effort": {"label": "Extra pull in the belt", "unit": "N",
                   "ask": "How much extra belt pull is fine, a warning, and critical?"},
        "quantity": "force",
    },
    "flipper_arm": {
        "label": "Flipper arm", "kind": "driven", "words": ["flipper", "paddle"],
        "effort": {"label": "Extra force a bottle puts on the belt through the flipper", "unit": "N",
                   "ask": "How much extra force from the flipper is fine, a warning, and critical?"},
        "quantity": "force",
    },
    "static": {
        "label": "Fixed part (frame, plate, bracket)", "kind": "static",
        "words": ["plate", "bracket", "frame", "cover"],
    },
}

# order matters: first rule that matches wins
_RULES = [
    ("brushless", "motor_bldc"), ("bldc", "motor_bldc"),
    ("motor", "motor_dc"),
    ("idler", "idler_pulley"), ("drive pulley", "drive_pulley"), ("pulley", "drive_pulley"),
    ("belt", "belt"), ("shaft", "shaft"), ("disk", "rotary_disk"), ("disc", "rotary_disk"),
    ("flipper", "flipper_arm"), ("paddle", "flipper_arm"),
    ("bracket", "static"), ("plate", "static"), ("frame", "static"),
]


def suggest_type(description):
    d = description.lower()
    for word, t in _RULES:
        if word in d:
            return t, f"description contains '{word}'"
    return None, "no known word in the description"


def is_motor(t):
    return TYPES.get(t, {}).get("kind") == "motor"


def has_effort(t):
    return "effort" in TYPES.get(t, {})
