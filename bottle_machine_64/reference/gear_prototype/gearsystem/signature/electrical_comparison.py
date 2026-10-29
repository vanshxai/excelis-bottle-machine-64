"""Stage 2 -- Parallel Electrical Validation. Runs the EXISTING, UNCHANGED
torque-to-current model (Model A -- signature.dynamic.simulate_touch(),
untouched by this module) and the NEW, EXPERIMENTAL electrical armature
model (Model B -- physics.electrical.simulate_armature_current(), from
Stage 1, also untouched by this module) side by side, against the exact
same touch scenario, for comparison only.

Nothing here modifies, replaces, or is consumed by any existing code path.
This module is called by exactly one new, additive route
(api/signature_routes.py::api_gearsystem_touch_sim_electrical_comparison)
and nothing else -- gear_train.py, signature/dynamic.py, and
physics/current_model.py are all imported read-only, called exactly as
they already are elsewhere, never edited.

Data flow, matching the requested diagram:
    Touch Simulation -> Mechanical Simulation (unchanged simulate_touch())
        -> Motor Speed omega(t)
        -> Branch: existing current model (already computed, inside
           simulate_touch()) / electrical model (computed here, fed the
           same omega(t))
        -> both waveforms returned together for the caller to overlay.

IMPORTANT finding this module makes directly visible, not something to
paper over: "Motor Speed omega(t)" for Yellow is a CONSTANT in the
existing mechanical model (see the physics audit -- Yellow's angular
velocity is prescribed, never integrated). So Model B here is genuinely
fed a flat omega(t), exactly as faithfully carried through from the
existing simulation, not a synthesized substitute. That means Model B's
response will generally look like a plain RC-style charge to its own
equilibrium, largely independent of which gear was touched or how hard --
because the existing model has no mechanism for a touch to reach Yellow's
speed at all. That's not a bug in this module or in Stage 1's equation
(both verified independently); it's the concrete answer to "observe how
the electrical model differs from the existing model" that Stage 2 asks
for, and it's exactly the gap Stage 3 (mechanical-electrical coupling,
NOT implemented here) would need to close.
"""
import math

from ..physics import electrical, gear_train
from ..signature import dynamic
from ..twin import store as twin_store


def simulate_touch_with_electrical_comparison(constants, gear, touch_type="impact", force_n=0.5,
                                               impulse_ns=5.0, duration_s=0.01, dt=None, n_points=80,
                                               capless=False, rpm_yellow=None, electrical_dt_s=1e-5):
    """Runs Model A (existing) and Model B (electrical, experimental)
    against the identical touch scenario (gear, touch_type, force_n,
    impulse_ns, constants). Returns both, plus the shared omega(t) value
    they're compared against. Neither model's own code is modified by
    this call -- see module docstring."""
    # Model A -- the existing, unchanged torque-to-current model. Called
    # exactly as every other caller of simulate_touch() already does.
    existing_model = dynamic.simulate_touch(
        constants, gear, touch_type=touch_type, force_n=force_n, impulse_ns=impulse_ns,
        duration_s=duration_s, dt=dt, n_points=n_points, capless=capless, rpm_yellow=rpm_yellow,
    )

    # Motor Speed omega(t) -- re-derived the same way simulate_touch()
    # itself derives it internally (same steady-state RPM chain, same
    # formula), not recomputed differently and not extracted by modifying
    # simulate_touch()'s return value. Yellow's omega is prescribed
    # constant in the existing model -- see module docstring.
    c = constants
    if capless:
        steady_result = gear_train.run_formula_chain_capless(c, rpm_yellow)
    else:
        steady_result = gear_train.run_formula_chain(c)
    omega_yellow_rad_s = steady_result["rpm_chain"]["Yellow"] * 2 * math.pi / 60

    def omega_fn(_t):
        return omega_yellow_rad_s

    registry = twin_store.load_registry()
    supply_voltage_v = registry["hard_constraints"]["MOTOR_SUPPLY_VOLTAGE_V"]

    # Model B -- the new, experimental electrical model (Stage 1),
    # started from the same idle baseline current as Model A so the
    # overlay compares the touch response, not an unrelated initial-
    # condition mismatch.
    t_s, current_a = electrical.simulate_armature_current(
        supply_voltage_v=supply_voltage_v,
        omega_fn=omega_fn,
        resistance_ohm=c["MOTOR_Ra_OHM"],
        inductance_h=c["MOTOR_La_H"],
        back_emf_v_s_per_rad=c["MOTOR_Ke_V_S_PER_RAD"],
        initial_current_a=existing_model["I_baseline_A"],
        dt_s=electrical_dt_s,
        duration_s=duration_s,
    )
    electrical_waveform = [{"t_ms": round(t * 1000, 4), "current_A": i} for t, i in zip(t_s, current_a)]

    return {
        "gear": gear,
        "touch_type": touch_type,
        "omega_yellow_rad_s": omega_yellow_rad_s,
        "existing_model": existing_model,
        "electrical_model": {
            "waveform": electrical_waveform,
            "I_baseline_A": existing_model["I_baseline_A"],
            "supply_voltage_v": supply_voltage_v,
            "resistance_ohm": c["MOTOR_Ra_OHM"],
            "inductance_h": c["MOTOR_La_H"],
            "back_emf_v_s_per_rad": c["MOTOR_Ke_V_S_PER_RAD"],
        },
    }
