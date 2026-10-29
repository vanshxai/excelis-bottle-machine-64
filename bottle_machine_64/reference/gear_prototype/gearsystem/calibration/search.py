"""Calibration Layer -- the closed optimization loop for the METAL
internal-gearbox rig. Relocated from gearsystem_roulette_metal.py.

Workflow (unchanged from before this refactor -- see the migration plan's
"Do NOT change the optimization algorithm yet" constraint):
  Load Initial Twin (twin.store.load_registry)
    -> Identify Unknown Parameters (calibration.sampling.soft_ranges)
    -> Generate N Candidate Twins (calibration.sampling.sample_variant, in _build_cards)
    -> Run identical disturbance simulations on every candidate (signature.steady_state)
    -> Generate signature library for every candidate (the same call, steady-state signatures ARE the library used during search)
    -> Receive real sensor signature (real_delta, passed into guess_for_card)
    -> Compare every candidate / Score every candidate (physics.current_model.rank_candidates_by_force_fit)
    -> Choose best candidate (pick_closer)
    -> Shrink parameter ranges (_narrow_directional)
    -> Generate next candidate generation (pick_closer -> _build_cards again)
    -> Repeat until convergence (repeated pick_closer calls from the UI)
    -> Save Verified Twin (verify -> twin.store.save_verified)
"""
import time

from . import sampling
from .state import load_state, save_state
from ..physics import current_model, gear_train
from ..signature import dynamic, steady_state
from ..twin import store as twin_store

N_CARDS = 20
NARROW_FRACTION = 0.20


def _build_cards(ranges, max_attempts=None):
    if max_attempts is None:
        max_attempts = N_CARDS * 40
    cards = []
    attempts = 0
    while len(cards) < N_CARDS and attempts < max_attempts:
        attempts += 1
        constants = sampling.sample_variant(ranges)
        try:
            result = steady_state.generate_steady_signature(constants)
        except gear_train.InvalidVariantError:
            continue
        cards.append({
            "variant_id": len(cards) + 1, "constants": constants, "valid": True,
            "signatures": result["signatures"], "I_baseline_A": result["I_baseline_A"],
        })
    return cards


def generate_twin_batch(n=20, max_attempts=None):
    """Independent batch of N digital twins -- each with its own sampled
    constants (same registry/ranges as the roulette cards), run through the
    full physics chain. Not tied to roulette state; purely for inspection."""
    if max_attempts is None:
        max_attempts = n * 40
    registry = twin_store.load_registry()
    ranges = sampling.soft_ranges(registry)
    twins = []
    attempts = 0
    while len(twins) < n and attempts < max_attempts:
        attempts += 1
        constants = sampling.sample_variant(ranges)
        try:
            result = steady_state.generate_steady_signature(constants)
        except gear_train.InvalidVariantError:
            continue
        twins.append({
            "twin_id": len(twins) + 1,
            "constants": constants,
            "rpm_chain": result["rpm_chain"],
            "mesh_frequencies_hz": result["mesh_frequencies_hz"],
            "I_baseline_A": result["I_baseline_A"],
            "signatures": result["signatures"],
        })
    return twins


def start_round():
    registry = twin_store.load_registry()
    ranges = sampling.soft_ranges(registry)
    state = {
        "round": 1, "cards": _build_cards(ranges), "current_ranges": ranges,
        "prev_winner_constants": None, "direction": {}, "started_at": time.time(),
    }
    save_state(state)
    return state


def guess_for_card(card, real_delta):
    """Single best-fit gear for one candidate card -- steps 1-2 (compute
    implied force per gear, filter to the plausible range) are shared with
    detection.matching._ina228_gear_matches() via
    physics.current_model.rank_candidates_by_force_fit(); this function's
    own step 3-4 (round, sort by distance to FORCE_REFERENCE_N, take the
    single best) is kept separate and unchanged, since the two callers
    genuinely produce different results (this one returns one match,
    detection's returns a tolerance-clustered set) -- see the migration
    plan's "duplicated logic to merge" section."""
    if not card["valid"]:
        return None
    candidates = current_model.rank_candidates_by_force_fit(
        real_delta, card["signatures"], gear_train.FORCE_TOUCH_MIN_N, gear_train.FORCE_TOUCH_MAX_N,
    )
    if not candidates:
        return None
    for c in candidates:
        c["implied_force_N"] = round(c["implied_force_N"], 4)
    candidates.sort(key=lambda c: abs(c["implied_force_N"] - current_model.FORCE_REFERENCE_N))
    return candidates[0]


def _narrow_directional(ranges, winner_constants, hard_bounds, direction):
    new_ranges = {}
    for k, r in ranges.items():
        span = (hard_bounds[k]["max"] - hard_bounds[k]["min"]) * NARROW_FRACTION
        d = direction.get(k, 0)
        center = winner_constants[k] + d * span
        lo, hi = center - span, center + span
        orig_lo, orig_hi = hard_bounds[k]["min"], hard_bounds[k]["max"]
        lo, hi = max(lo, orig_lo), min(hi, orig_hi)
        if sampling.is_int_range(orig_lo, orig_hi):
            lo, hi = int(round(lo)), int(round(hi))
            if hi <= lo:
                hi = lo + 1 if lo < orig_hi else lo
                lo = hi - 1 if hi > orig_lo else lo
        else:
            if hi <= lo:
                lo, hi = orig_lo, orig_hi
        new_ranges[k] = {"min": lo, "max": hi}
    return new_ranges


def pick_closer(variant_id):
    state = load_state()
    if state is None:
        raise ValueError("no active roulette round -- call start_round first")
    card = next((c for c in state["cards"] if c["variant_id"] == variant_id and c["valid"]), None)
    if card is None:
        raise ValueError(f"card {variant_id} not found or invalid")

    registry = twin_store.load_registry()
    hard_bounds = sampling.soft_ranges(registry)
    winner_constants = card["constants"]
    prev = state.get("prev_winner_constants")
    direction = dict(state.get("direction", {}))

    if prev is not None:
        for k, v in winner_constants.items():
            if k not in prev:
                continue
            if v > prev[k]:
                direction[k] = 1
            elif v < prev[k]:
                direction[k] = -1

    new_ranges = _narrow_directional(state["current_ranges"], winner_constants, hard_bounds, direction)
    state = {
        "round": state["round"] + 1, "cards": _build_cards(new_ranges), "current_ranges": new_ranges,
        "prev_winner_constants": winner_constants, "direction": direction, "started_at": time.time(),
        "last_picked_card": {"variant_id": variant_id, "constants": winner_constants},
    }
    save_state(state)
    return state


def verify(variant_id):
    state = load_state()
    if state is None:
        raise ValueError("no active roulette round")
    card = next((c for c in state["cards"] if c["variant_id"] == variant_id and c["valid"]), None)
    if card is None:
        raise ValueError(f"card {variant_id} not found or invalid")
    record = {
        "constants": card["constants"], "signatures": card["signatures"],
        "I_baseline_A": card["I_baseline_A"], "verified_at": time.time(), "round": state["round"],
        # Real time-domain predictions (backlash/mesh-stiffness/reflected
        # inertia) for the confirmed twin -- "signatures" above is still the
        # fast steady-state model used during the search itself.
        "dynamic_signatures": dynamic.generate_signature_library(card["constants"]),
    }
    twin_store.save_verified(record)
    return record
