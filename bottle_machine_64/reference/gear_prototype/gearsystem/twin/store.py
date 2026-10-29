"""Twin Layer storage -- loading the constraint registry (nominal facts +
searchable ranges) and loading/saving the verified twin. Pure data I/O:
no physics, no simulation, no hardware.

load_registry() was gearsystem_roulette_metal.py's private _load_registry()
-- made public here since it was already being read directly by API-layer
code (api_gearsystem_motor_chain, _fill_dynamic_defaults) reaching into
another module's private function, a pre-existing "no hidden dependencies"
violation this move fixes for free. load_verified()/save_verified() were
gearsystem_roulette_metal.load_verified() and the file-write half of its
verify() -- relocated here since loading/saving a twin is this layer's
job even though the code that decides WHEN to save (calibration's
search.verify()) still lives in Calibration.
"""
import json
import os

from .. import PROJECT_ROOT

REGISTRY_PATH = os.path.join(PROJECT_ROOT, "constraint_registry_metal.json")
VERIFIED_PATH = os.path.join(PROJECT_ROOT, "gearsystem_metal_verified_twin.json")


def load_registry():
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def load_verified():
    if not os.path.exists(VERIFIED_PATH):
        return None
    with open(VERIFIED_PATH) as f:
        return json.load(f)


def save_verified(record):
    with open(VERIFIED_PATH, "w") as f:
        json.dump(record, f, indent=2)
