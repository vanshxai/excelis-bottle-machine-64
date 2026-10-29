"""Stage 1 verification -- standalone check that
gearsystem/physics/electrical.py's simulate_armature_current() correctly
implements V = R*i + L*(di/dt) + Ke*omega, in complete isolation from the
rest of the codebase. Not wired into the app, not imported by anything
else, not called automatically. Run directly:

    python3 verify_electrical_model.py

Checks performed:
  1. Isolation -- confirms (by reading the actual source, not just
     trusting the docstring) that physics/electrical.py imports nothing
     from elsewhere in gearsystem/.
  2. Synthetic omega(t) trajectories -- constant, ramp, step, sinusoidal
     -- printed, and plotted if matplotlib is available.
  3. Analytic agreement -- for the constant-omega case there's a closed-
     form solution, i(t) = i_ss + (i0-i_ss)*exp(-t/tau); the RK4 output is
     compared against it directly, not just eyeballed for plausibility.
  4. Parameter sanity checks, exactly as requested: increasing R reduces
     steady-state current; increasing L slows the response; increasing Ke
     reduces steady-state current.
"""
import math
import sys

sys.path.insert(0, ".")
from gearsystem.physics import electrical

# Example values only -- this script does not read the twin or registry
# (that would violate the isolation this stage is proving). They happen to
# match the Stage 0 placeholders in constraint_registry_metal.json purely
# for continuity, not because this script depends on that file.
V_BASE = 12.0       # MOTOR_SUPPLY_VOLTAGE_V
R_BASE = 5.0         # MOTOR_Ra_OHM
L_BASE = 0.001       # MOTOR_La_H
KE_BASE = 0.14524    # MOTOR_Ke_V_S_PER_RAD
DT = 1e-5
DURATION = 0.02


def omega_constant(t):
    return 100.0


def omega_ramp(t):
    return 50.0 + 5000.0 * t


def omega_step(t):
    return 0.0 if t < 0.005 else 150.0


def omega_sinusoidal(t):
    return 100.0 + 40.0 * math.sin(2 * math.pi * 200 * t)


def print_series(label, t_s, current_a, n_points=8):
    print(f"  {label}:")
    stride = max(len(t_s) // n_points, 1)
    for i in range(0, len(t_s), stride):
        print(f"    t={t_s[i] * 1000:7.3f}ms  i={current_a[i]:+.6f}A")
    print(f"    t={t_s[-1] * 1000:7.3f}ms  i={current_a[-1]:+.6f}A  (final)")


def maybe_plot(trajectories):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (matplotlib not installed -- printed output above only, no plot)")
        return
    fig, ax = plt.subplots()
    for label, (t_s, current_a) in trajectories.items():
        ax.plot([t * 1000 for t in t_s], current_a, label=label)
    ax.set_xlabel("t (ms)")
    ax.set_ylabel("current (A)")
    ax.set_title("Stage 1 standalone electrical model -- synthetic omega trajectories")
    ax.legend()
    out_path = "electrical_model_verification.png"
    fig.savefig(out_path, dpi=120)
    print(f"  (plot saved to {out_path})")


def check_isolation():
    """Parses the actual source with ast (not a naive line-prefix scan --
    that approach's first draft false-flagged the module's own docstring,
    which contains the English word "from" at the start of a line) to list
    every genuine import statement in physics/electrical.py."""
    import ast

    src_path = electrical.__file__
    with open(src_path) as f:
        tree = ast.parse(f.read(), filename=src_path)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported.extend(f"{module}.{alias.name}" if module else alias.name for alias in node.names)
    forbidden = ("gear_train", "signature", "calibration", "detection", "twin", "current_model", "motor", "api")
    violating = [name for name in imported if any(f in name for f in forbidden)]
    print("  actual import statements in physics/electrical.py:", imported or "(none)")
    print("  violating (references other gearsystem/ modules):", violating or "(none)")
    return not violating


def analytic_constant_omega_response(t, i0, V, R, L, Ke, omega):
    """Closed-form i(t) when omega/V/R/L/Ke are all held constant:
    tau = L/R, i_ss = (V - Ke*omega)/R, i(t) = i_ss + (i0-i_ss)*exp(-t/tau).
    Used to check the RK4 integrator against an exact answer, not just a
    plausible-looking curve."""
    tau = L / R
    i_ss = (V - Ke * omega) / R
    return i_ss + (i0 - i_ss) * math.exp(-t / tau)


def final_current(R=R_BASE, L=L_BASE, Ke=KE_BASE, V=V_BASE, omega_fn=omega_constant):
    _, i = electrical.simulate_armature_current(
        supply_voltage_v=V, omega_fn=omega_fn, resistance_ohm=R,
        inductance_h=L, back_emf_v_s_per_rad=Ke, initial_current_a=0.0,
        dt_s=DT, duration_s=DURATION,
    )
    return i[-1]


def time_to_fraction(t_s, current_a, target_value):
    for t, i in zip(t_s, current_a):
        if abs(i) >= abs(target_value):
            return t
    return None


def main():
    print("=" * 72)
    print("Stage 1 -- standalone electrical model verification")
    print("=" * 72)

    print("\n[1] Isolation check")
    ok_isolation = check_isolation()
    print(f"  PASS: {ok_isolation}")

    print("\n[2] Synthetic omega(t) trajectories")
    trajectories = {}
    for label, omega_fn in [
        ("constant", omega_constant), ("ramp", omega_ramp),
        ("step", omega_step), ("sinusoidal", omega_sinusoidal),
    ]:
        t_s, current_a = electrical.simulate_armature_current(
            supply_voltage_v=V_BASE, omega_fn=omega_fn, resistance_ohm=R_BASE,
            inductance_h=L_BASE, back_emf_v_s_per_rad=KE_BASE, initial_current_a=0.0,
            dt_s=DT, duration_s=DURATION,
        )
        trajectories[label] = (t_s, current_a)
        print_series(label, t_s, current_a)
    maybe_plot(trajectories)

    print("\n[3] Analytic agreement (constant omega=100 rad/s)")
    t_s, current_a = trajectories["constant"]
    max_err = max(
        abs(i_sim - analytic_constant_omega_response(t, 0.0, V_BASE, R_BASE, L_BASE, KE_BASE, 100.0))
        for t, i_sim in zip(t_s, current_a)
    )
    i_ss_exact = (V_BASE - KE_BASE * 100.0) / R_BASE
    print(f"  simulated final current: {current_a[-1]:.8f}A")
    print(f"  analytic steady-state:   {i_ss_exact:.8f}A")
    print(f"  max abs error vs closed-form, whole trajectory: {max_err:.3e}A")
    analytic_ok = max_err < 1e-4
    print(f"  PASS (RK4 matches the exact solution): {analytic_ok}")

    print("\n[4] Parameter sanity checks (constant omega=100 rad/s baseline)")
    i_low_R, i_high_R = final_current(R=2.0), final_current(R=10.0)
    check_R = abs(i_high_R) < abs(i_low_R)
    print(f"  R=2ohm  -> steady current {i_low_R:+.6f}A")
    print(f"  R=10ohm -> steady current {i_high_R:+.6f}A")
    print(f"  increasing R reduces |current|: {check_R}")

    t_low_L, i_low_L = electrical.simulate_armature_current(
        supply_voltage_v=V_BASE, omega_fn=omega_constant, resistance_ohm=R_BASE,
        inductance_h=0.0005, back_emf_v_s_per_rad=KE_BASE, initial_current_a=0.0,
        dt_s=DT, duration_s=DURATION,
    )
    t_high_L, i_high_L = electrical.simulate_armature_current(
        supply_voltage_v=V_BASE, omega_fn=omega_constant, resistance_ohm=R_BASE,
        inductance_h=0.005, back_emf_v_s_per_rad=KE_BASE, initial_current_a=0.0,
        dt_s=DT, duration_s=DURATION,
    )
    i_ss_ref = (V_BASE - KE_BASE * 100.0) / R_BASE
    t90_low = time_to_fraction(t_low_L, i_low_L, 0.90 * i_ss_ref)
    t90_high = time_to_fraction(t_high_L, i_high_L, 0.90 * i_ss_ref)
    check_L = t90_low is not None and (t90_high is None or t90_high > t90_low)
    print(f"  L=0.5mH -> time to reach 90% of steady-state: {t90_low}")
    print(f"  L=5mH   -> time to reach 90% of steady-state: {t90_high}")
    print(f"  increasing L slows the response: {check_L}")

    # Ke values chosen to stay in the "forward-driven" regime (Ke*omega <
    # V, i.e. back-EMF below supply voltage) -- that's where "increasing
    # Ke reduces current" actually holds. i_ss=(V-Ke*omega)/R: once Ke is
    # large enough that Ke*omega exceeds V, (V-Ke*omega) flips sign and
    # then grows in MAGNITUDE as Ke keeps increasing, so |i_ss| goes back
    # up -- not a bug (confirmed: an earlier version of this exact check
    # used Ke=0.05/0.5 at omega=100, i.e. Ke*omega=5 and 50 against V=12,
    # straddling that crossover, and correctly reported the relationship
    # as false for that range: -1.4A -> -7.6A, |current| UP not down).
    # That's the equation behaving correctly outside the regime the claim
    # is actually about (a motor being overdriven by an external torque
    # into its regenerative/braking regime), not a defect in it -- but it
    # means the sanity check has to stay inside the regime it's testing.
    i_low_Ke, i_high_Ke = final_current(Ke=0.02), final_current(Ke=0.08)
    check_Ke = abs(i_high_Ke) < abs(i_low_Ke)
    print(f"  Ke=0.02 -> steady current {i_low_Ke:+.6f}A  (Ke*omega=2, well below V={V_BASE})")
    print(f"  Ke=0.08 -> steady current {i_high_Ke:+.6f}A  (Ke*omega=8, still below V={V_BASE})")
    print(f"  increasing Ke reduces |current| (within the forward-driven regime): {check_Ke}")

    print("\n" + "=" * 72)
    all_ok = ok_isolation and analytic_ok and check_R and check_L and check_Ke
    print(f"ALL CHECKS PASSED: {all_ok}")
    print("=" * 72)
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
