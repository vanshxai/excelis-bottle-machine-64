"""Live detection routes -- thin wrappers over detection/. Relocated from
gearsystem150_app.py (api_gearsystem_live_zero_calibrate,
api_gearsystem_live_state, api_gearsystem_live_detect,
api_gearsystem_live_model_compare)."""
import time

from flask import Blueprint, jsonify

from ..detection import live_state, matching, signal_processing
from ..twin import store as twin_store

bp = Blueprint("gearsystem_detection", __name__)


@bp.route("/api/gearsystem/live/zero_calibrate", methods=["POST"])
def api_gearsystem_live_zero_calibrate():
    ok, info = signal_processing.run_zero_calibrate()
    return jsonify({"ok": ok, **info}), (200 if ok else 400)


@bp.route("/api/gearsystem/live/state")
def api_gearsystem_live_state():
    with live_state.lock:
        state = dict(live_state.state)
        state["history"] = list(state["history"])
    state["stale"] = state["last_update"] is None or (time.time() - state["last_update"] > 5)
    return jsonify(state)


@bp.route("/api/gearsystem/live/detect")
def api_gearsystem_live_detect():
    """Overall calibration/delta status for the live gauge widget -- per-card
    guesses against the active roulette round come from
    /api/gearsystem/roulette_metal/guesses separately."""
    if live_state.real_zero_A is None:
        return jsonify({"calibrated": False})
    with live_state.lock:
        live_val = live_state.state["current_A"]
    if live_val is None:
        return jsonify({"calibrated": True, "error": "no live reading yet"})
    real_delta = live_val - live_state.real_zero_A
    noise_floor = live_state.noise_floor_at_cal or live_state.NOISE_FLOOR_MIN
    return jsonify({"calibrated": True, "real_delta_A": round(real_delta, 6), "noise_floor_A": round(noise_floor, 6)})


@bp.route("/api/gearsystem/live/raw_waveform")
def api_gearsystem_live_raw_waveform():
    """Direct dump of the raw per-sample ring buffer -- no block-meaning,
    no smoothing, no classification. See detection/live_state.py's
    raw_buffer and CLASSIFY_ENABLED (temporarily False -- see that
    module's docstring)."""
    samples = list(live_state.raw_buffer)
    with live_state.lock:
        connected = live_state.state["connected"]
        port = live_state.state["port"]
    return jsonify({
        "connected": connected,
        "port": port,
        "n_samples": len(samples),
        "samples": [{"t": t, "current_A": mA / 1000.0} for t, mA in samples],
    })


@bp.route("/api/gearsystem/live/model_compare")
def api_gearsystem_live_model_compare():
    """The live<->model gateway: real ESP32 sensor delta next to the
    verified twin's real-physics (signature.dynamic) predicted delta per
    gear, so the two can be read side by side. Reads dynamic_signatures
    from the verified-twin JSON -- computed ONCE at verify time
    (signature.dynamic.generate_signature_library), not re-simulated on
    every poll, so this stays cheap enough to actually poll live."""
    verified = twin_store.load_verified()
    if verified is None:
        return jsonify({"available": False, "error": "no verified twin -- verify a roulette card first"})
    dynamic_sigs = verified.get("dynamic_signatures")
    if not dynamic_sigs:
        return jsonify({
            "available": False,
            "error": "verified twin predates dynamic_signatures -- re-verify a card to add them",
        })
    result = matching.compare_to_dynamic_model(dynamic_sigs)
    return jsonify({"available": True, **result})
