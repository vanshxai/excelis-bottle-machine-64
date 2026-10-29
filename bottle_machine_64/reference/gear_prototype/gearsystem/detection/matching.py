"""Signature Matching -- turns a live current delta into a gear
classification. Two independent algorithms live here, both relocated
unchanged from gearsystem150_app.py: gear_matches() (best-fit +
tolerance-clustering, drives the main live UI) and
compare_to_dynamic_model() (magnitude-nearest-neighbor against cached RK4
signatures, drives the live-model page). They are NOT unified -- see the
migration plan's "duplicated logic to merge" section for why: they
produce genuinely different results today, and the user's explicit
constraint is to preserve current behavior, not improve classification.
"""
from ..physics import current_model, gear_train
from ..twin import store as twin_store
from . import live_state

MATCH_TOLERANCE = 0.25  # a candidate gear must be within this fraction of the best-fit gear's implied force


def gear_matches(delta_a):
    """Fault-o-meter lookup (2026-08-06 redesign): a pure function of the
    current reading, nothing else -- no baseline tracking, no memory
    between calls, exactly a speedometer reading against a pre-built
    scale rather than a live computation. The "scale" is the verified
    twin's own per-gear sensitivities (delta_I_per_N_A).

    Bug found live: the first version only checked each gear's implied
    force against the wide sanity bound (0.1-15N) -- that bound exists to
    reject physically absurd numbers, not to discriminate between gears,
    and it's so wide that nearly any real touch computes a "plausible"
    force for all four gears simultaneously (everything lit up, every
    time). Fixed: first find the best-fit gear (closest implied force to
    the reference touch force), then only include OTHER gears whose
    implied force is within MATCH_TOLERANCE of THAT gear's -- i.e. "close
    enough to the best answer to be genuinely ambiguous", not "not
    impossible". Blue/Green/Red's sensitivities sit within ~10% of each
    other, comfortably inside that tolerance, so they correctly cluster
    together on a touch; Yellow's sensitivity is ~2.5-2.8x off from the
    other three, comfortably outside it, so it correctly stands alone.

    This replaces the earlier stateful EMA-baseline detector, which had
    to track a slow-adapting baseline and freeze it while "touched" --
    and got stuck permanently the one time a motor power-cycle looked
    like an ongoing touch. A stateless per-reading lookup can't get stuck
    that way; every block is judged fresh.

    Steps 1-2 (compute implied force per gear, filter to the physically
    plausible range) are shared with calibration.search.guess_for_card()
    via physics.current_model.rank_candidates_by_force_fit() -- see that
    module's docstring. The clustering below (step 3-4) is specific to
    this function and NOT shared -- guess_for_card returns a single best
    match instead."""
    verified = twin_store.load_verified()
    if verified is None:
        return []
    candidates = current_model.rank_candidates_by_force_fit(
        delta_a, verified["signatures"], gear_train.FORCE_TOUCH_MIN_N, gear_train.FORCE_TOUCH_MAX_N,
    )
    if not candidates:
        return []
    candidates.sort(key=lambda c: abs(c["implied_force_N"] - current_model.FORCE_REFERENCE_N))
    best_force_N = candidates[0]["implied_force_N"]
    matches = [c for c in candidates if abs(c["implied_force_N"] - best_force_N) <= MATCH_TOLERANCE * best_force_N]
    matches.sort(key=lambda c: c["implied_force_N"])
    return [{"component": c["component"], "implied_force_N": round(c["implied_force_N"], 4)} for c in matches]


def compare_to_dynamic_model(dynamic_sigs):
    """Detection result for the live<->model comparison gateway: real
    ESP32 sensor delta next to the verified twin's real-physics
    (signature.dynamic RK4 model) predicted delta per gear, so the two
    can be read side by side. dynamic_sigs is the cached
    dynamic_signatures block from the verified twin -- computed ONCE at
    verify time (signature.dynamic.generate_signature_library), not
    re-simulated on every poll, so this stays cheap enough to actually
    poll live.

    Reads live state directly (same style gear_matches() uses for the
    verified twin) -- relocated from
    gearsystem150_app.py::api_gearsystem_live_model_compare, split from
    its HTTP response shaping (which stays in api/detection_routes.py:
    the "no verified twin" / "predates dynamic_signatures" branches, and
    the outer "available" key)."""
    if live_state.real_zero_A is None:
        return {"calibrated": False}

    with live_state.lock:
        live_val = live_state.state["current_A"]
    if live_val is None:
        return {"calibrated": True, "error": "no live reading yet"}

    real_delta_A = live_val - live_state.real_zero_A
    noise_floor = live_state.noise_floor_at_cal or live_state.NOISE_FLOOR_MIN
    detected = "no_touch" if abs(real_delta_A) < noise_floor else "touch"

    predictions = []
    for gear, sig in dynamic_sigs.items():
        if "error" in sig:
            continue
        predictions.append({
            "gear": gear, "predicted_delta_I_A": sig["delta_I_A"],
            "predicted_touch_type": sig["touch_type"],
            "diff_from_live_A": abs(sig["delta_I_A"] - real_delta_A),
        })
    predictions.sort(key=lambda p: p["diff_from_live_A"])

    return {
        "calibrated": True,
        "live_current_A": round(live_val, 6), "real_delta_A": round(real_delta_A, 6),
        "noise_floor_A": round(noise_floor, 6), "detected": detected,
        # Closest-by-magnitude is a hint, not a verdict -- the dynamic model
        # was run at one reference touch magnitude/type at verify time, and
        # a real touch could be a different type/strength (see
        # signature/dynamic.py's simulate_touch() docstring on the three
        # distinct touch scenarios).
        "closest_gear": predictions[0]["gear"] if predictions and detected == "touch" else None,
        "model_predictions": predictions,
    }
