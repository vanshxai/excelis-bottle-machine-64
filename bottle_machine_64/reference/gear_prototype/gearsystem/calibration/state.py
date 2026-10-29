"""Calibration round/card state -- persisted between HTTP requests so a
roulette round survives across multiple API calls (start -> guesses ->
pick_closer -> ... -> verify). Relocated from gearsystem_roulette_metal.py
(STATE_PATH, load_state, _save_state -- renamed save_state, now public
since it's called from search.py, a different module)."""
import json
import os

from .. import PROJECT_ROOT

STATE_PATH = os.path.join(PROJECT_ROOT, "gearsystem_roulette_metal_state.json")


def load_state():
    if not os.path.exists(STATE_PATH):
        return None
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
