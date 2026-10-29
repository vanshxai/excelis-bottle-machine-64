"""Electrical Model.

Stage 1 of the ideal-motor -> dynamic-motor migration (see the physics
audit and impact-analysis review, 2026-08-08/09): implements the standard
DC motor electrical equation

    V = R*i + L*(di/dt) + Ke*omega
    =>  di/dt = (V - R*i - Ke*omega) / L

as a single, standalone, reusable function. This module imports nothing
from elsewhere in gearsystem/ -- no gear_train, no signature/dynamic, no
current_model, no twin/calibration/detection -- and nothing elsewhere in
gearsystem/ imports this module yet. Not called by simulate_touch(), not
called by torque_to_current(), not wired into the live simulator in any
way. See verify_electrical_model.py (project root) for standalone
verification, and the migration plan's Stage 2/3 for when/how this
eventually gets wired in -- explicitly NOT done here.

Field correspondence for a future caller (this module itself only takes
plain scalars -- it does not read the twin or the registry):
    V        <- registry hard_constraints["MOTOR_SUPPLY_VOLTAGE_V"] (12V, measured)
    R        <- twin constants["MOTOR_Ra_OHM"]             (Stage 0 placeholder, estimated)
    L        <- twin constants["MOTOR_La_H"]               (Stage 0 placeholder, estimated)
    Ke       <- twin constants["MOTOR_Ke_V_S_PER_RAD"]      (Stage 0 placeholder, assumed = Kt)
    omega(t) <- supplied by the caller. Nothing in this codebase currently
                produces a real motor-speed trajectory to feed it -- the
                live simulator prescribes Yellow's omega as a constant
                (see the physics audit). verify_electrical_model.py uses
                synthetic trajectories instead.

T=Kt*i (motor_2) and the mechanical coupling (motor_3:
Jmotor*domega/dt = T-Tload-b*omega-Tstatic) are Stage 3 concerns, not
Stage 1 -- not implemented here. The placeholders below remain None,
deliberately, for exactly the reason they were None before this stage.
"""

# Still-unimplemented -- Stage 3 (mechanical coupling) concern, out of
# scope for Stage 1 (the electrical equation only, in isolation).
KT_NM_PER_A = None
J_MOTOR_KGM2 = None
B_MOTOR_NM_S_PER_RAD = None
T_STATIC_NM = None


def _di_dt(current_a, omega_rad_s, resistance_ohm, inductance_h, back_emf_v_s_per_rad, supply_voltage_v):
    """di/dt = (V - R*i - Ke*omega) / L -- the ODE's right-hand side at
    one instant, given the current state and inputs."""
    return (supply_voltage_v - resistance_ohm * current_a - back_emf_v_s_per_rad * omega_rad_s) / inductance_h


def simulate_armature_current(supply_voltage_v, omega_fn, resistance_ohm, inductance_h,
                               back_emf_v_s_per_rad, initial_current_a, dt_s, duration_s):
    """Integrates V = R*i + L*(di/dt) + Ke*omega for i(t), given omega(t)
    (any callable t -> rad/s) as the forcing input. Fixed-timestep RK4 --
    a completely separate integrator from gear_train.py's mechanical RK4:
    no shared code, no shared state. That integrator steps a (theta,
    omega) pair per gear-train node against mesh/backlash/friction
    torques; this one steps a single scalar current against this one
    linear electrical equation.

    Returns (t_s, current_a) -- two same-length lists: current(t) sampled
    every dt_s from 0 to duration_s inclusive. Nothing else -- no derived
    peak/rise-time/summary fields. That's a caller's job, if and when
    this is ever wired into something that needs it (not yet).
    """
    if inductance_h <= 0:
        raise ValueError(f"inductance_h must be positive, got {inductance_h!r}")
    if dt_s <= 0:
        raise ValueError(f"dt_s must be positive, got {dt_s!r}")

    n_steps = max(int(round(duration_s / dt_s)), 1)
    t = 0.0
    i = initial_current_a
    t_s = [t]
    current_a = [i]

    for _ in range(n_steps):
        k1 = _di_dt(i, omega_fn(t),
                    resistance_ohm, inductance_h, back_emf_v_s_per_rad, supply_voltage_v)
        k2 = _di_dt(i + dt_s / 2 * k1, omega_fn(t + dt_s / 2),
                    resistance_ohm, inductance_h, back_emf_v_s_per_rad, supply_voltage_v)
        k3 = _di_dt(i + dt_s / 2 * k2, omega_fn(t + dt_s / 2),
                    resistance_ohm, inductance_h, back_emf_v_s_per_rad, supply_voltage_v)
        k4 = _di_dt(i + dt_s * k3, omega_fn(t + dt_s),
                    resistance_ohm, inductance_h, back_emf_v_s_per_rad, supply_voltage_v)
        i = i + (dt_s / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        t = t + dt_s
        t_s.append(t)
        current_a.append(i)

    return t_s, current_a
