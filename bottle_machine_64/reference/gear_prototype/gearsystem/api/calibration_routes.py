"""Calibration (card-roulette) routes -- thin wrappers over
calibration/search.py. Relocated from gearsystem150_app.py."""
from flask import Blueprint, jsonify, request

from ..calibration import search
from ..calibration import state as calib_state
from ..detection import live_state
from ..twin import store as twin_store

bp = Blueprint("gearsystem_calibration", __name__)


@bp.route("/api/gearsystem/twin_batch")
def api_gearsystem_twin_batch():
    twins = search.generate_twin_batch(20)
    return jsonify({"twins": twins})


@bp.route("/api/gearsystem/roulette_metal/start", methods=["POST"])
def api_gearsystem_roulette_metal_start():
    return jsonify(search.start_round())


@bp.route("/api/gearsystem/roulette_metal/state")
def api_gearsystem_roulette_metal_state():
    state = calib_state.load_state()
    if state is None:
        return jsonify({"round": None})
    return jsonify(state)


@bp.route("/api/gearsystem/roulette_metal/guesses")
def api_gearsystem_roulette_metal_guesses():
    state = calib_state.load_state()
    if state is None:
        return jsonify({"calibrated": False, "guesses": []})
    if live_state.real_zero_A is None:
        return jsonify({"calibrated": False, "guesses": []})

    with live_state.lock:
        live_val = live_state.state["current_A"]
    if live_val is None:
        return jsonify({"calibrated": True, "guesses": [], "error": "no live reading yet"})

    real_delta = live_val - live_state.real_zero_A
    noise_floor = live_state.noise_floor_at_cal or live_state.NOISE_FLOOR_MIN

    guesses = []
    for card in state["cards"]:
        if not card["valid"]:
            guesses.append({"variant_id": card["variant_id"], "status": "invalid", "guess": None})
            continue
        if abs(real_delta) < noise_floor:
            guesses.append({"variant_id": card["variant_id"], "status": "no_touch", "guess": None})
            continue
        guess = search.guess_for_card(card, real_delta)
        guesses.append({
            "variant_id": card["variant_id"],
            "status": "guessing" if guess else "implausible",
            "guess": guess,
        })
    return jsonify({
        "calibrated": True, "real_delta_A": round(real_delta, 6),
        "noise_floor_A": round(noise_floor, 6), "guesses": guesses,
    })


@bp.route("/api/gearsystem/roulette_metal/pick_closer", methods=["POST"])
def api_gearsystem_roulette_metal_pick_closer():
    body = request.get_json(silent=True) or {}
    variant_id = body.get("variant_id")
    try:
        return jsonify(search.pick_closer(variant_id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/gearsystem/roulette_metal/verify", methods=["POST"])
def api_gearsystem_roulette_metal_verify():
    body = request.get_json(silent=True) or {}
    variant_id = body.get("variant_id")
    try:
        return jsonify(search.verify(variant_id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/gearsystem/roulette_metal/verified")
def api_gearsystem_roulette_metal_verified():
    v = twin_store.load_verified()
    return jsonify(v if v else {})
