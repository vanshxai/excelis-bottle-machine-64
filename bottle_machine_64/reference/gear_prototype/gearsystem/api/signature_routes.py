"""Signature-generation routes -- motor/gear physics chain, and both the
cosmetic and real-physics touch simulators. Relocated from
gearsystem150_app.py (api_gearsystem_motor_chain, api_gearsystem_touch_sim,
_fill_dynamic_defaults, api_gearsystem_touch_sim_dynamic).

Both /touch_sim (cosmetic, fast) and /touch_sim_dynamic (real RK4 physics,
slower) stay -- they're genuinely separate UI features, not a stale
duplicate to remove; see the migration plan's "APIs that remain
unchanged" section.
"""
from flask import Blueprint, jsonify, request

from ..physics import gear_train
from ..signature import dynamic, electrical_comparison, steady_state, waveform_display
from ..twin import store as twin_store

bp = Blueprint("gearsystem_signature", __name__)

_DYNAMIC_ONLY_KEYS = [
    "GEAR_BACKLASH_RAD", "GEAR_SHAFT_FRICTION_NM_S_PER_RAD",
    "MATERIAL_YOUNGS_MODULUS_PA", "MOTOR_ROTOR_RADIUS_MM", "MOTOR_ROTOR_LENGTH_MM",
]


@bp.route("/api/gearsystem/motor_chain")
def api_gearsystem_motor_chain():
    """Real motor+gear physics chain for the motor-click popup AND the
    dedicated /twin/gearsystem150/motor page: RPM chain -> mesh frequency ->
    baseline current -> per-gear delta-I signature -> rise time, computed
    from the verified metal-twin's constants. Also includes the hard
    (unsampled) motor nameplate facts -- MOTOR_SUPPLY_VOLTAGE_V and
    MOTOR_RPM_OUTPUT_METAL live in the registry's hard_constraints, not the
    per-twin sampled constants dict, so they aren't in `constants` below --
    and the cached dynamic-model signatures from verify time, if present."""
    verified = twin_store.load_verified()
    if verified is None:
        return jsonify({"available": False})
    result = steady_state.generate_steady_signature(verified["constants"])
    registry = twin_store.load_registry()
    hard = registry["hard_constraints"]
    return jsonify({
        "available": True,
        "constants": verified["constants"],
        "nameplate": {
            "MOTOR_SUPPLY_VOLTAGE_V": hard.get("MOTOR_SUPPLY_VOLTAGE_V"),
            "MOTOR_RPM_OUTPUT_METAL": hard.get("MOTOR_RPM_OUTPUT_METAL"),
        },
        "rpm_chain": result["rpm_chain"],
        "mesh_frequencies_hz": result["mesh_frequencies_hz"],
        "I_baseline_A": result["I_baseline_A"],
        "signatures": result["signatures"],
        "dynamic_signatures": verified.get("dynamic_signatures"),
    })


@bp.route("/api/gearsystem/touch_sim", methods=["POST"])
def api_gearsystem_touch_sim():
    body = request.get_json(silent=True) or {}
    constants = body.get("constants")
    gear = body.get("gear", "Yellow")
    touch_type = body.get("touch_type", "impact")
    force_n = float(body.get("force_n", 0.5))
    impulse_ns = float(body.get("impulse_ns", 5.0))
    if not constants:
        return jsonify({"error": "constants required"}), 400
    try:
        result = steady_state.generate_steady_signature(constants)
    except gear_train.InvalidVariantError as e:
        return jsonify({"error": str(e)}), 400

    def sim_for(sig):
        if touch_type == "steady":
            delta_I = sig["delta_I_per_N_A"] * force_n
        else:
            delta_I = sig["delta_I_per_impulse_A_per_Nms"] * impulse_ns
        waveform = waveform_display.simulate_touch_waveform(
            result["I_baseline_A"], delta_I, sig["rise_time_s"], touch_type)
        return {
            "gear": sig["name"], "delta_I_A": delta_I,
            "peak_A": result["I_baseline_A"] + delta_I,
            "rise_time_s": sig["rise_time_s"], "signature_shape": sig["signature_shape"],
            "waveform": waveform,
        }

    if gear == "all":
        sims = [sim_for(s) for s in result["signatures"]]
    else:
        sig = next((s for s in result["signatures"] if s["name"] == gear), None)
        if sig is None:
            return jsonify({"error": "unknown gear"}), 400
        sims = [sim_for(sig)]

    return jsonify({"I_baseline_A": result["I_baseline_A"], "touch_type": touch_type, "sims": sims})


def _fill_dynamic_defaults(constants):
    """Twins sampled before the dynamic simulator's constants existed
    won't have these keys -- fall back to the registry's range midpoint for
    whichever are missing, rather than forcing a fresh roulette round just
    to touch-sim an older twin."""
    missing = [k for k in _DYNAMIC_ONLY_KEYS if k not in constants]
    if not missing:
        return constants
    registry = twin_store.load_registry()
    filled = dict(constants)
    for k in missing:
        rng = registry["soft_constraints"][k]
        filled[k] = (rng["min"] + rng["max"]) / 2
    return filled


@bp.route("/api/gearsystem/touch_sim_dynamic", methods=["POST"])
def api_gearsystem_touch_sim_dynamic():
    """Same request/response shape as /api/gearsystem/touch_sim, but the
    waveform comes from the real time-domain gear_1..gear_6 model
    (backlash, mesh stiffness, reflected inertia, shaft friction) instead
    of the hand-shaped exponential curve -- see signature/dynamic.py and
    FORMULA_DATABASE.md sec G."""
    body = request.get_json(silent=True) or {}
    constants = body.get("constants")
    gear = body.get("gear", "Yellow")
    touch_type = body.get("touch_type", "impact")
    force_n = float(body.get("force_n", 0.5))
    impulse_ns = float(body.get("impulse_ns", 5.0))
    if not constants:
        return jsonify({"error": "constants required"}), 400
    constants = _fill_dynamic_defaults(constants)
    try:
        steady_state.generate_steady_signature(constants)  # validity check, same gate as the steady-state endpoint
    except gear_train.InvalidVariantError as e:
        return jsonify({"error": str(e)}), 400

    gears = ["Yellow", "Blue", "Green", "Red"] if gear == "all" else [gear]
    try:
        sims = [dynamic.simulate_touch(
            constants, g, touch_type=touch_type, force_n=force_n, impulse_ns=impulse_ns,
        ) for g in gears]
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    I_baseline = sims[0]["I_baseline_A"] if sims else None
    return jsonify({"I_baseline_A": I_baseline, "touch_type": touch_type, "sims": sims})


@bp.route("/api/gearsystem/touch_sim_electrical_comparison", methods=["POST"])
def api_gearsystem_touch_sim_electrical_comparison():
    """Stage 2 -- runs the existing torque-to-current model (unchanged)
    and the new experimental electrical armature model (Stage 1) against
    the same touch scenario, side by side. Does not replace or modify
    /touch_sim_dynamic -- that route, and the functions it calls, are
    untouched. See signature/electrical_comparison.py."""
    body = request.get_json(silent=True) or {}
    constants = body.get("constants")
    gear = body.get("gear", "Yellow")
    touch_type = body.get("touch_type", "impact")
    force_n = float(body.get("force_n", 0.5))
    impulse_ns = float(body.get("impulse_ns", 5.0))
    if not constants:
        return jsonify({"error": "constants required"}), 400
    constants = _fill_dynamic_defaults(constants)
    try:
        steady_state.generate_steady_signature(constants)  # validity check, same gate as the other touch-sim endpoints
    except gear_train.InvalidVariantError as e:
        return jsonify({"error": str(e)}), 400

    if gear == "all":
        return jsonify({"error": "gear='all' not supported for the electrical comparison -- pick one gear"}), 400
    try:
        result = electrical_comparison.simulate_touch_with_electrical_comparison(
            constants, gear, touch_type=touch_type, force_n=force_n, impulse_ns=impulse_ns,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)
