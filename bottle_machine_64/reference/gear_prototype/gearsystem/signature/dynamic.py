"""Dynamic Signature -- time-domain (RK4) touch transients, using the real
gear_1..gear_6 dynamics in physics/gear_train.py instead of the hand-shaped
exponential in waveform_display.py. Relocated from
dynamic_gear_simulator.py (simulate_touch) and gearsystem_roulette_metal.py
(_compute_dynamic_signatures, renamed generate_signature_library -- its
job, "given a twin, produce a per-gear signature library," is this layer's
own stated contract even though it's triggered by Calibration's verify();
see the migration plan's "key interpretive decisions" #4).

Input: a twin's constants + a disturbance (gear, touch_type, force_n/
impulse_ns). Output: a current signature (delta_I_A, peak_A, rise_time_s,
waveform, ...). No hardware. No UI.
"""
import math

from ..physics import current_model, gear_train

TOUCHABLE_GEARS = ("Yellow", "Blue", "Green", "Red")


def simulate_touch(constants, gear, touch_type="impact", force_n=0.5, impulse_ns=5.0,
                    duration_s=0.01, dt=None, n_points=80,
                    capless=False, rpm_yellow=None):
    """Time-domain touch transient for one gear, using the real gear_1..gear_6
    dynamics instead of the hand-shaped exponential in
    waveform_display.py's _simulate_touch_waveform(). Returns a dict shaped
    to match the existing /api/gearsystem/touch_sim response (waveform =
    list of {t_ms, current_A}) so the frontend can render either
    interchangeably.

    touch_type is one of three physically distinct scenarios (a held
    surface/drag touch behaves nothing like a stationary tool tip being
    rapped by every passing tooth, which behaves nothing like a single
    strike):
      "steady"       -- a held drag/press (fingertip against the spinning
                         edge). Constant torque for the whole window.
      "impact"       -- one single strike. A brief one-shot torque pulse,
                         then the train rings freely.
      "tooth_strike" -- a stationary tool tip left resting against the
                         gear, struck once per tooth pass -- the "Trrrr"
                         buzz at the gear's own tooth-pass (mesh)
                         frequency (formula_chain_metal.py's
                         mesh_frequencies_hz), held for the whole window.
    """
    if gear not in ("Yellow", "Blue", "Green", "Red"):
        raise ValueError(f"gear must be one of Yellow/Blue/Green/Red (touchable nodes), got {gear!r}")

    c = constants
    if capless:
        # capless rig: motor speed is a free/measured parameter, Output gone
        result = gear_train.run_formula_chain_capless(c, rpm_yellow)
    else:
        result = gear_train.run_formula_chain(c)  # steady-state chain -> nominal speeds + I_baseline
    train = gear_train.build_gear_train(c, capless=capless)
    if dt is None:
        dt = gear_train.stable_dt(train)

    rpm_chain = result["rpm_chain"]
    omega_rad = {node: rpm_chain[node] * 2 * math.pi / 60 for node in train["nodes"]}
    state = gear_train.equilibrium_state(train, omega_rad)

    # Touch torque at the pitch radius of the touched node, same lever-arm
    # and friction convention as run_formula_chain's steady-force model
    # (FORMULA_DATABASE.md sec D) -- reused rather than inventing a new
    # touch constant.
    radius_m = gear_train.gear_radius_m(c[gear_train.NODE_TEETH_KEY[gear]], c)
    friction_coeff = c["METAL_OILED_FRICTION_COEFF"]

    # Three physically distinct touch scenarios, not two:
    #  - "steady": a held drag/press (fingertip against the spinning edge) --
    #    constant torque for the whole window.
    #  - "impact": one single off strike -- a brief one-shot torque pulse,
    #    then the train rings freely with nothing more applied.
    #  - "tooth_strike": a STATIONARY tool tip left resting against the gear,
    #    getting rapped by every passing tooth -- a repeated train of brief
    #    pulses at the touched gear's own tooth-pass (mesh) frequency, held
    #    for the whole window. This is the "Trrrr" buzz, not a single event.
    repeat_period_s = None
    if touch_type == "steady":
        T_touch = force_n * radius_m * friction_coeff
        pulse_end_s = duration_s  # held for the whole window
        pulse_duration_s = duration_s
    elif touch_type == "tooth_strike":
        mesh_freq_hz = result["mesh_frequencies_hz"][gear]
        if mesh_freq_hz <= 0:
            raise ValueError(f"non-positive mesh frequency for {gear!r}: {mesh_freq_hz}")
        repeat_period_s = 1.0 / mesh_freq_hz
        # Show several strike cycles even for slow-turning gears (Red's mesh
        # frequency can be an order of magnitude below Yellow's), without
        # shrinking the window for fast ones. Capped below by MAX_STEPS --
        # for the slowest gears this trades "fewer visible cycles" for
        # "responds in a few seconds instead of tens of seconds", since dt
        # is set by the mesh's (fast) resonance, not by this repetition rate.
        duration_s = max(duration_s, 6 * repeat_period_s)
        impulse_Ns = impulse_ns / 1000.0  # UI passes N*ms -> N*s, per-tooth rap impulse
        angular_impulse_Nms = impulse_Ns * radius_m
        pulse_duration_s = min(5 * dt, repeat_period_s / 4)  # brief rap, not a sustained push
        T_touch = angular_impulse_Nms / pulse_duration_s
        pulse_end_s = duration_s  # struck on every tooth pass for the whole window
    else:  # "impact" -- single one-off strike
        impulse_Ns = impulse_ns / 1000.0  # UI passes N*ms -> N*s, a linear impulse at the touch point
        angular_impulse_Nms = impulse_Ns * radius_m  # F*r, same lever-arm convention as the steady-force model
        # Short relative to the mesh's own resonant period (a handful of
        # timesteps) so the pulse reads as an impulsive strike rather than a
        # sustained push -- with k_mesh now derived (much stiffer, much
        # faster resonance than the old placeholder), a fixed 1ms pulse
        # would span dozens of oscillation cycles instead of being brief.
        pulse_duration_s = 5 * dt
        T_touch = angular_impulse_Nms / pulse_duration_s
        pulse_end_s = pulse_duration_s

    # Hard cap regardless of touch_type/duration_s -- dt is set by the mesh's
    # own (fast, ~kHz-scale) resonance, not by how long a caller asked to
    # simulate, so a long duration_s (e.g. tooth_strike's multi-period
    # window on a slow-turning gear) can otherwise mean tens of thousands of
    # RK4 steps and a multi-second-to-a-minute response. Trades simulated
    # duration for staying responsive as a web request.
    MAX_STEPS = 6000
    n_steps = min(max(int(duration_s / dt), 1), MAX_STEPS)
    bucket_steps = max(n_steps // n_points, 1)  # integration steps per reported waveform point

    I_baseline = result["I_baseline_A"]
    current_per_nm = c["CURRENT_PER_NM"]
    yellow_stage = train["stages"][0]  # Yellow -> Blue, the only mesh Yellow drives

    # I_baseline_A already IS the idle current (run_formula_chain's sec C:
    # "set directly, not derived"). The equilibrium state's own mesh
    # torque (gear_6 friction, chained through gear_5) is a separate,
    # steady no-touch reaction that exists whether or not I_baseline_A was
    # sampled to match it -- so it has to be subtracted back out here, or
    # every touch would start with a spurious jump at t=0 before any
    # dynamics have run. Only the CHANGE relative to this reference is the
    # touch's actual signature.
    T_mesh_yellow_eq = gear_train.mesh_torque(state["Yellow"][0], state["Blue"][0],
                                               yellow_stage["N"], yellow_stage["backlash"], yellow_stage["k_mesh"])
    T_yellow_motor_eq = T_mesh_yellow_eq / (yellow_stage["N"] * yellow_stage["eta"])

    # k_mesh is derived (~1e3-1e4 Nm/rad, see gear_train.build_gear_train())
    # instead of the old ~0.05-5 placeholder, so the mesh resonance is a
    # ~10-30kHz ring, not a slow ms-scale rise -- WAY faster than a
    # human-readable n_points=80 chart can sample without aliasing (a
    # handful of point samples across thousands of oscillation cycles
    # would just catch essentially-random phases, producing spurious
    # spikes and missing the true peak entirely). So current_A is
    # evaluated at every dt step (not just at reported points),
    # true_peak_A/t track the real extremum across the WHOLE simulation
    # regardless of reporting resolution, and each reported waveform point
    # is the peak-magnitude deviation seen within its bucket of steps (an
    # envelope of the ringdown) rather than one aliased instantaneous
    # sample.
    waveform = []
    true_peak_A = I_baseline
    true_peak_t_s = 0.0
    bucket_extreme_A = I_baseline
    t = 0.0
    for step in range(n_steps + 1):
        if touch_type == "tooth_strike":
            # A brief rap at the START of every tooth-pass period, held for
            # the whole window -- not one event, a repeated buzz.
            struck = t < pulse_end_s and (t % repeat_period_s) < pulse_duration_s
        else:
            struck = t < pulse_end_s
        disturb_torque = {gear: T_touch} if struck else {}

        T_mesh_yellow = gear_train.mesh_torque(state["Yellow"][0], state["Blue"][0],
                                                yellow_stage["N"], yellow_stage["backlash"], yellow_stage["k_mesh"])
        T_reaction_on_yellow = T_mesh_yellow / (yellow_stage["N"] * yellow_stage["eta"])
        # Yellow's own speed is prescribed (see gear_train module
        # docstring), so a disturbance applied directly to it never shows
        # up in its equation of motion (there isn't one) -- it must be
        # subtracted here instead, as the extra torque the idealized
        # speed-holding motor has to supply to keep Yellow's omega exactly
        # constant against it.
        T_yellow_motor = T_reaction_on_yellow - disturb_torque.get("Yellow", 0.0)
        current_A = current_model.torque_to_current(
            T_yellow_motor - T_yellow_motor_eq, current_per_nm, i_baseline=I_baseline)

        if abs(current_A - I_baseline) > abs(true_peak_A - I_baseline):
            true_peak_A, true_peak_t_s = current_A, t
        if abs(current_A - I_baseline) > abs(bucket_extreme_A - I_baseline):
            bucket_extreme_A = current_A

        if step % bucket_steps == 0 or step == n_steps:
            waveform.append({"t_ms": round(t * 1000, 4), "current_A": bucket_extreme_A})
            bucket_extreme_A = I_baseline

        state = gear_train.rk4_step(state, train, disturb_torque, dt)
        t += dt

    delta_I_A = true_peak_A - I_baseline
    peak_A = true_peak_A
    shape = {"steady": "steady_dynamic", "tooth_strike": "tooth_strike_dynamic"}.get(touch_type, "impact_dynamic")

    return {
        "gear": gear, "touch_type": touch_type,
        "I_baseline_A": I_baseline, "delta_I_A": delta_I_A, "peak_A": peak_A,
        "rise_time_s": true_peak_t_s,
        "signature_shape": shape,
        "mesh_frequency_hz": result["mesh_frequencies_hz"][gear] if touch_type == "tooth_strike" else None,
        "waveform": waveform,
        "reflected_inertia_at_motor_kgm2": train["reflected_inertia_at_motor_kgm2"],
    }


def generate_signature_library(constants, touch_type="impact", impulse_ns=5.0, force_n=2.0):
    """Runs simulate_touch() for all 4 touchable gears against one
    already-chosen (verified) variant -- expensive per call (~1-3s/gear,
    capped by MAX_STEPS in simulate_touch) so this is ONLY done here, once,
    at verify time, never inside the calibration search sweep itself
    (calibration/search.py's _build_cards/generate_twin_batch stay on the
    fast steady-state gear_train.run_formula_chain -- see their docstrings
    and this module's docstring for why). The result is cached in the
    verified-twin JSON so the live model-comparison gateway
    (detection/matching.py's live/model_compare) can read it instantly
    instead of re-running the simulation on every live poll.

    Relocated from gearsystem_roulette_metal.py::_compute_dynamic_signatures,
    renamed -- its job is this layer's own stated contract (twin ->
    signature library) even though it's triggered by Calibration's
    verify(); see the migration plan's "key interpretive decisions" #4."""
    sigs = {}
    for gear in TOUCHABLE_GEARS:
        try:
            sigs[gear] = simulate_touch(
                constants, gear, touch_type=touch_type, force_n=force_n, impulse_ns=impulse_ns,
            )
        except (ValueError, ZeroDivisionError) as e:
            sigs[gear] = {"error": str(e)}
    return sigs
