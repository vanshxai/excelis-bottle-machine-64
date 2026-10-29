"""Gear Train -- kinematics (RPM chain, mesh frequencies, steady-state
signatures) and dynamics (RK4 backlash/mesh-stiffness/reflected-inertia
model) for the metal 150rpm internal gearbox rig. Relocated from
formula_chain_metal.py (run_formula_chain / run_formula_chain_capless) and
dynamic_gear_simulator.py (the RK4 mechanical model) -- merged into one
physics module since both operate on the same gear-train topology.
Formulas are unchanged from their original form; the only substantive
edit is routing the CURRENT_PER_NM conversion through
physics.current_model.torque_to_current() instead of repeating `* c[...]`
in five places (see that module's docstring).

Topology (confirmed by user's direct physical description and photo):
Yellow is the motor's OWN gear, sitting at the absolute center, directly
on the armature shaft. Yellow meshes Blue directly. Blue carries a
smaller coaxial gear that meshes Green. Green carries a smaller coaxial
gear that meshes Red. Red carries a smaller coaxial gear that meshes the
final Output gear, which extends a rotor rod exposed outside the plastic
casing -- MOTOR_RPM_OUTPUT_METAL=150 was read directly off the motor's
label, describing the exposed rod's (Output's) speed.

No motor datasheet/credentials exist for this rig, and reverse-engineering
its internal electrical design (voltage, winding resistance, torque
constant) from first-principles formulas isn't worth the time for what we
actually need: detecting which of the four gears was touched. Those three
separate electrical unknowns (MOTOR_VOLTAGE_V/MOTOR_Ra_OHM/MOTOR_Kt_NM_PER_A)
only ever combined into two things any current reading could actually
distinguish -- the idle baseline current, and one overall torque-to-current
gain -- so they're collapsed into exactly those two directly:
I_BASELINE_A (idle current) and CURRENT_PER_NM (gain, A per Nm of torque
at the touch point, replacing 1/Kt) -- see physics/current_model.py and
physics/electrical.py. The power-conservation check that used to validate
the V/Ra/Kt model is gone too -- nothing left for it to check.

Output is NOT a touch point -- it sits inside the closed plastic cap once
assembled, so it can never actually be touched. Its tooth count
(TEETH_OUTPUT_BIG) still matters -- it's the physical link between Red
and the known 150 RPM shaft -- so it's kept as a constant used in the RPM
chain, just excluded from TOUCH_POINTS. Yellow, unlike in earlier
versions of this file, IS a touch point now -- it's the biggest, most
exposed gear in the cluster and genuinely touchable.

Tooth counts for Yellow (9T), Blue (27T/8T), Green (27T/8T), and Red
(27T/16T) were physically counted by the user and confirmed 2026-07-31 --
constraint_registry_metal.json pins them (soft_constraints min==max) so
every sampled variant now gets the true value, no code changes needed
here. Only TEETH_OUTPUT_BIG (the single gear inside the removable cap)
remains unmeasured and is still searched via card-roulette, so
RPM_red/green/blue/yellow below are downstream of that one unknown.
Supply voltage (12V) is also now known but still isn't enough to recover
Ra/Kt individually -- see constraint_registry_metal.json's
motor_supply_voltage_note. constraint_registry_metal.json is the single
source of truth for every constant used here.

IMPACT-RESPONSE MODEL (added after real touch data): the first real touch
test used a flat screwdriver scraping/chattering against the spinning
teeth, not a static press. The recorded current showed brief high-
magnitude spikes (<10ms) with the mean barely moving -- an IMPACT
response, not the sustained-force response the delta_I_per_N model above
assumes. An impact's effect on a gear depends on that gear's rotational
inertia (I = 0.5 * mass * radius^2, mass = density * pi * radius^2 *
width) -- a heavier/larger gear absorbs more of a given impact with less
speed perturbation, producing a smaller transmitted current spike. This
is why MATERIAL_DENSITY_KG_M3 and GEAR_WIDTH_MM exist: they let each
gear's mass/inertia be computed from real physics (steel/alloy density x
geometry), not asserted. delta_I_per_impulse_A_per_Nms is the resulting
impulse-normalized sensitivity (like delta_I_per_N_A is force-normalized
for the steady-force model) -- force-and-duration independent, so it's
the number that should actually be compared against a real recorded
impact spike's magnitude.

CAPPED vs CAPLESS: the cap and Output gear physically came off the rig
2026-07-31, which invalidates run_formula_chain()'s 150-RPM anchor -- with
Output removed there's no output shaft, and the motor spins unloaded at
some unknown, higher speed. run_formula_chain_capless() re-anchors on
Yellow (the only shaft whose speed is still physically defined in the
capless rig) given an externally supplied rpm_yellow (a free parameter,
measurable only from the recorded spectrum). Both functions are kept --
see gearsystem/signature/dynamic.py and gearsystem/calibration/search.py
for which callers use which, and the refactor plan's "key interpretive
decisions" for why that split was not changed in this phase.

The RK4 dynamics below (build_gear_train, mesh_torque, equilibrium_state,
rk4_step, stable_dt -- relocated from dynamic_gear_simulator.py) answer a
different question than the steady-state chain above: what does a touch
TRANSIENT actually look like once backlash, mesh compliance, and
reflected inertia are allowed to act, instead of assuming instantaneous
quasi-static transmission? Yellow (the motor's own shaft) is driven at a
prescribed constant angular velocity (an ideal, infinitely-stiff speed
source) rather than integrated -- it can't show motor speed sag during a
touch, but the mesh/current response downstream of it (what the touch
signatures actually measure) is unaffected by that choice. Yellow's own
inertia DOES include the motor's rotor/armature (physics.motor) -- a
separate physical mass rigidly on the same shaft as the pinion gear, not
part of the (unimplemented) electrical model.

k_mesh (gear_5) is derived, not an independently swept constant -- see
_tooth_linear_stiffness_n_per_m() for the cantilever-beam model and
constraint_registry_metal.json's geometry_and_material_note for the
2026-07-31 measurement/assumption data it's built from.
"""
import math

from . import current_model, motor

F_TOUCH_N = 0.5
FORCE_TOUCH_MIN_N = 0.1
FORCE_TOUCH_MAX_N = 15.0
MOTOR_RPM_OUTPUT_METAL = 150  # hard constraint -- read off the motor's label, at the exposed rod (Output gear)

TOUCH_POINTS = [
    {"id": 1, "name": "Yellow", "surface": "metal_oiled"},
    {"id": 2, "name": "Blue", "surface": "metal_oiled"},
    {"id": 3, "name": "Green", "surface": "metal_oiled"},
    {"id": 4, "name": "Red", "surface": "metal_oiled"},
]
# Meshes between each touch point and Output (the known 150 RPM shaft) --
# Red is 1 mesh from Output, Green 2, Blue 3, Yellow 4.
N_STAGES = {1: 4, 2: 3, 3: 2, 4: 1}

NODES = ["Yellow", "Blue", "Green", "Red", "Output"]
STAGES_TOPOLOGY = [
    {"driving": "Yellow", "driven": "Blue"},
    {"driving": "Blue", "driven": "Green"},
    {"driving": "Green", "driven": "Red"},
    {"driving": "Red", "driven": "Output"},
]
# CAPLESS rig (2026-07-31: cap + Output gear physically removed). Red's
# small pinion meshes nothing -- Red is the free end of the train. The
# Output node and the Red->Output stage must NOT be simulated: they would
# add a phantom load and a phantom inertia to Red's dynamics.
NODES_CAPLESS = ["Yellow", "Blue", "Green", "Red"]
STAGES_TOPOLOGY_CAPLESS = STAGES_TOPOLOGY[:3]
# teeth constant used for each node's own radius/inertia -- the larger
# ("big") face of each compound gear, same convention run_formula_chain
# already uses for touch-point radius (its big_teeth map).
NODE_TEETH_KEY = {
    "Yellow": "TEETH_YELLOW", "Blue": "TEETH_BLUE_BIG", "Green": "TEETH_GREEN_BIG",
    "Red": "TEETH_RED_BIG", "Output": "TEETH_OUTPUT_BIG",
}
# teeth constants used for each stage's ratio, N = driven_big / driving_small
STAGE_RATIO_KEYS = [
    ("TEETH_BLUE_BIG", "TEETH_YELLOW"),
    ("TEETH_GREEN_BIG", "TEETH_BLUE_SMALL"),
    ("TEETH_RED_BIG", "TEETH_GREEN_SMALL"),
    ("TEETH_OUTPUT_BIG", "TEETH_RED_SMALL"),
]


class InvalidVariantError(Exception):
    """Raised when the RPM chain validation fails."""


def run_formula_chain(constants):
    """constants must include every SOFT constraint from
    constraint_registry_metal.json (concrete sampled values, not ranges).
    Returns the full result dict, or raises InvalidVariantError."""
    c = constants

    # ---- STEP 1: gear ratio chain, worked BACKWARD from the known output
    # (the exposed rod, at the Output gear's shaft) all the way to Yellow
    # (the motor's own shaft) ----
    RPM_output = float(MOTOR_RPM_OUTPUT_METAL)  # given -- the exposed rod
    RPM_red = RPM_output * (c["TEETH_OUTPUT_BIG"] / c["TEETH_RED_SMALL"])
    RPM_green = RPM_red * (c["TEETH_RED_BIG"] / c["TEETH_GREEN_SMALL"])
    RPM_blue = RPM_green * (c["TEETH_GREEN_BIG"] / c["TEETH_BLUE_SMALL"])
    RPM_yellow = RPM_blue * (c["TEETH_BLUE_BIG"] / c["TEETH_YELLOW"])

    rpm_chain = {
        "Output": RPM_output, "Red": RPM_red, "Green": RPM_green,
        "Blue": RPM_blue, "Yellow": RPM_yellow,
    }

    # ---- validation: every RPM finite, positive, within a sane bound ----
    for name, rpm in rpm_chain.items():
        val = abs(rpm)
        if not math.isfinite(val) or val <= 0.01 or val > MOTOR_RPM_OUTPUT_METAL * 200:
            raise InvalidVariantError(f"RPM validation failed at {name}: {val:.3f}")

    # ---- STEP 2: gear mesh frequencies -- each stage genuinely differs,
    # since RPM changes at every hop ----
    mesh_freqs = {
        "Yellow": RPM_yellow / 60 * c["TEETH_YELLOW"],
        "Blue": RPM_blue / 60 * c["TEETH_BLUE_BIG"],
        "Green": RPM_green / 60 * c["TEETH_GREEN_BIG"],
        "Red": RPM_red / 60 * c["TEETH_RED_BIG"],
    }

    # ---- STEP 3: baseline current -- set directly, not derived from
    # V/Ra/Kt (see physics/electrical.py) ----
    I_baseline = c["I_BASELINE_A"]

    # ---- STEP 4-5: per touch point ----
    big_teeth = {1: c["TEETH_YELLOW"], 2: c["TEETH_BLUE_BIG"], 3: c["TEETH_GREEN_BIG"], 4: c["TEETH_RED_BIG"]}
    RISE_TIME_BASE_S = 0.002  # fixed electrical rise-time reference (was Ra-derived but Ra canceled out algebraically anyway)

    signatures = []
    for tp in TOUCH_POINTS:
        tid = tp["id"]
        n = N_STAGES[tid]
        radius_mm = (big_teeth[tid] * c["MODULE_MM"]) / 2
        radius_m = radius_mm / 1000
        friction_coeff = c["METAL_OILED_FRICTION_COEFF"]
        efficiency_chain = c["GEAR_MESH_EFFICIENCY"] ** n

        # ---- steady-force model (a held press) ----
        tau_per_N = radius_m * friction_coeff * efficiency_chain
        delta_I_per_N = current_model.torque_to_current(tau_per_N, c["CURRENT_PER_NM"])
        tau_touch = F_TOUCH_N * radius_m * friction_coeff
        tau_at_motor = tau_touch * efficiency_chain
        delta_I = current_model.torque_to_current(tau_at_motor, c["CURRENT_PER_NM"])

        # ---- impact-response model (a screwdriver strike/scrape) ----
        gear_width_m = c["GEAR_WIDTH_MM"] / 1000
        mass_kg = c["MATERIAL_DENSITY_KG_M3"] * math.pi * (radius_m ** 2) * gear_width_m
        inertia_kgm2 = 0.5 * mass_kg * (radius_m ** 2)
        delta_I_per_impulse = efficiency_chain * c["CURRENT_PER_IMPULSE"] / inertia_kgm2

        rise_time = RISE_TIME_BASE_S * (1 + 0.15 * n)

        signatures.append({
            "touch_point_id": tid, "name": tp["name"],
            "delta_I_A": delta_I,
            "delta_I_per_N_A": delta_I_per_N,
            "mass_kg": mass_kg,
            "inertia_kgm2": inertia_kgm2,
            "delta_I_per_impulse_A_per_Nms": delta_I_per_impulse,
            "rise_time_s": rise_time,
            "dominant_frequency_hz": mesh_freqs[tp["name"]],
            "signature_shape": "spike_then_partial_recovery",
            "n_stages_from_motor": n,
            "P_losses_W": None,
        })

    return {
        "rpm_chain": rpm_chain,
        "mesh_frequencies_hz": mesh_freqs,
        "I_baseline_A": I_baseline,
        "signatures": signatures,
    }


def run_formula_chain_capless(constants, rpm_yellow):
    """CAPLESS configuration -- the cap and the Output gear physically came
    off the rig (2026-07-31), which invalidates run_formula_chain()'s anchor
    in two independent ways:

      1. The 150 RPM label describes the OUTPUT shaft under load. With the
         Output gear removed there is no output shaft, and the motor spins
         unloaded at some unknown, higher speed. Anchoring anything on 150
         is now a hard error.
      2. TEETH_OUTPUT_BIG was never measured while installed -- the roulette
         searched 24..40 teeth, but the user measured the removed gear at
         ~19T. So even historical runs of the old chain carried a ~40%
         absolute-frequency error. Ratios between the four surviving gears
         were never affected (they depend only on the measured 9/27/8/27/8/
         27/16 counts).

    The chain is therefore re-anchored at the only shaft whose speed is
    physically defined in the capless rig: Yellow, the motor's own armature.
    rpm_yellow is a FREE PARAMETER -- measurable only from the recorded
    spectrum, never predictable from the label. The cascade runs FORWARD
    (series, motor outward): Yellow -> Blue -> Green -> Red, and Red's small
    gear meshes nothing (free end).

    Execution-order contract, explicit per the 2026-08-01 audit:
      SERIES   -- the RPM cascade (each speed depends on the previous).
      PARALLEL -- per-gear mesh frequencies and per-gear touch signatures
                  (each depends only on already-fixed chain values, never on
                  another gear's signature).
    """
    c = constants
    if not (rpm_yellow and math.isfinite(rpm_yellow) and rpm_yellow > 0):
        raise InvalidVariantError(f"rpm_yellow must be a positive finite RPM, got {rpm_yellow!r}")

    # ---- STEP 1 (SERIES): forward cascade from the motor shaft ----
    RPM_yellow = float(rpm_yellow)
    RPM_blue = RPM_yellow * (c["TEETH_YELLOW"] / c["TEETH_BLUE_BIG"])
    RPM_green = RPM_blue * (c["TEETH_BLUE_SMALL"] / c["TEETH_GREEN_BIG"])
    RPM_red = RPM_green * (c["TEETH_GREEN_SMALL"] / c["TEETH_RED_BIG"])

    rpm_chain = {"Yellow": RPM_yellow, "Blue": RPM_blue,
                 "Green": RPM_green, "Red": RPM_red}
    for name, rpm in rpm_chain.items():
        if not math.isfinite(rpm) or rpm <= 0.01:
            raise InvalidVariantError(f"RPM validation failed at {name}: {rpm:.3f}")

    # ---- STEP 2 (PARALLEL): tooth-pass frequencies. Yellow/Blue share one
    # physical mesh so their values coincide by construction; ratio ladder
    # relative to Red is exactly 9 : 8/3 : 64/81 (tooth counts only). ----
    mesh_freqs = {
        "Yellow": RPM_yellow / 60 * c["TEETH_YELLOW"],
        "Blue": RPM_blue / 60 * c["TEETH_BLUE_BIG"],
        "Green": RPM_green / 60 * c["TEETH_GREEN_BIG"],
        "Red": RPM_red / 60 * c["TEETH_RED_BIG"],
    }
    # shaft-rotation frequencies too -- eccentricity/wobble sidebands live
    # at these, not at the mesh lines
    shaft_freqs = {name: rpm / 60.0 for name, rpm in rpm_chain.items()}

    I_baseline = c["I_BASELINE_A"]

    # ---- STEPS 3-4 (PARALLEL): per-gear signatures. Mesh count from the
    # motor: Yellow 0 hops, Blue 1, Green 2, Red 3 (Output stage GONE). ----
    n_stages_capless = {1: 0, 2: 1, 3: 2, 4: 3}
    big_teeth = {1: c["TEETH_YELLOW"], 2: c["TEETH_BLUE_BIG"],
                 3: c["TEETH_GREEN_BIG"], 4: c["TEETH_RED_BIG"]}
    RISE_TIME_BASE_S = 0.002

    signatures = []
    for tp in TOUCH_POINTS:
        tid = tp["id"]
        n = n_stages_capless[tid]
        radius_m = (big_teeth[tid] * c["MODULE_MM"]) / 2 / 1000
        friction_coeff = c["METAL_OILED_FRICTION_COEFF"]
        efficiency_chain = c["GEAR_MESH_EFFICIENCY"] ** n

        tau_per_N = radius_m * friction_coeff * efficiency_chain
        delta_I_per_N = current_model.torque_to_current(tau_per_N, c["CURRENT_PER_NM"])
        tau_at_motor = F_TOUCH_N * radius_m * friction_coeff * efficiency_chain
        delta_I = current_model.torque_to_current(tau_at_motor, c["CURRENT_PER_NM"])

        gear_width_m = c["GEAR_WIDTH_MM"] / 1000
        mass_kg = c["MATERIAL_DENSITY_KG_M3"] * math.pi * (radius_m ** 2) * gear_width_m
        inertia_kgm2 = 0.5 * mass_kg * (radius_m ** 2)
        delta_I_per_impulse = efficiency_chain * c["CURRENT_PER_IMPULSE"] / inertia_kgm2

        signatures.append({
            "touch_point_id": tid, "name": tp["name"],
            "delta_I_A": delta_I,
            "delta_I_per_N_A": delta_I_per_N,
            "mass_kg": mass_kg,
            "inertia_kgm2": inertia_kgm2,
            "delta_I_per_impulse_A_per_Nms": delta_I_per_impulse,
            "rise_time_s": RISE_TIME_BASE_S * (1 + 0.15 * n),
            "dominant_frequency_hz": mesh_freqs[tp["name"]],
            "shaft_frequency_hz": shaft_freqs[tp["name"]],
            "signature_shape": "spike_then_partial_recovery",
            "n_stages_from_motor": n,
            "P_losses_W": None,
        })

    return {
        "rpm_chain": rpm_chain,
        "mesh_frequencies_hz": mesh_freqs,
        "shaft_frequencies_hz": shaft_freqs,
        "I_baseline_A": I_baseline,
        "signatures": signatures,
        "capless": True,
    }


def gear_radius_m(teeth, c):
    return (teeth * c["MODULE_MM"] / 2) / 1000


def _gear_inertia_kgm2(teeth, c):
    """Same solid-disc idealization as run_formula_chain()'s impact model
    (FORMULA_DATABASE.md E2/E3) -- reused here as J_gear for gear_3."""
    r_m = gear_radius_m(teeth, c)
    w_m = c["GEAR_WIDTH_MM"] / 1000
    mass_kg = c["MATERIAL_DENSITY_KG_M3"] * math.pi * (r_m ** 2) * w_m
    return 0.5 * mass_kg * (r_m ** 2)


def _tooth_linear_stiffness_n_per_m(c):
    """Single-tooth bending stiffness via a cantilever-beam approximation --
    gear_5's k_mesh, derived rather than an independently swept unknown (see
    constraint_registry_metal.json's geometry_and_material_note). The tooth
    is treated as a rectangular cantilever: thickness = tooth thickness at
    the pitch circle (pi*m/2, a standard simplification), width = face
    width, length = full standard tooth height (addendum m + dedendum
    1.25m = 2.25m). k_linear = 3EI/L^3. This is the same simplified model
    for every tooth regardless of which gear it's on -- module, face width,
    and material are shared across the whole train -- so it's computed once
    and reused per-stage in build_gear_train(), scaled there by each
    stage's own driven-gear pitch radius."""
    E = c["MATERIAL_YOUNGS_MODULUS_PA"]
    m = c["MODULE_MM"] / 1000
    b = c["GEAR_WIDTH_MM"] / 1000
    t = math.pi * m / 2
    L = 2.25 * m
    I = b * t ** 3 / 12
    return 3 * E * I / L ** 3


def build_gear_train(constants, capless=False):
    """Resolves node inertias and per-stage ratios/params from sampled
    constants. Returns a fixed (non-time-varying) description of the train,
    reused across every simulate_touch() call for one variant.

    capless=True drops the Output node and the Red->Output stage (the gear
    left the machine with the cap); Red becomes the free end."""
    c = constants
    nodes = NODES_CAPLESS if capless else NODES
    topology = STAGES_TOPOLOGY_CAPLESS if capless else STAGES_TOPOLOGY
    ratio_keys = STAGE_RATIO_KEYS[:len(topology)]
    eta = c["GEAR_MESH_EFFICIENCY"]
    backlash = c["GEAR_BACKLASH_RAD"]
    b_shaft = c["GEAR_SHAFT_FRICTION_NM_S_PER_RAD"]
    tooth_k_linear = _tooth_linear_stiffness_n_per_m(c)

    J = {node: _gear_inertia_kgm2(c[NODE_TEETH_KEY[node]], c) for node in nodes}
    J["Yellow"] += motor.motor_rotor_inertia_kgm2(c)

    stages = []
    N_cum = 1.0
    for topo, (big_key, small_key) in zip(topology, ratio_keys):
        N = c[big_key] / c[small_key]
        N_cum *= N
        # k_mesh (gear_5) at this stage, referenced to the DRIVEN gear's own
        # angle (theta_gap is in the driven gear's frame -- see
        # mesh_torque()), so the linear-to-torsional conversion uses the
        # driven gear's own pitch radius: k_mesh = k_linear * r_driven^2.
        driven_radius_m = gear_radius_m(c[NODE_TEETH_KEY[topo["driven"]]], c)
        k_mesh = tooth_k_linear * driven_radius_m ** 2
        stages.append({
            "driving": topo["driving"], "driven": topo["driven"],
            "N": N, "N_cumulative": N_cum, "eta": eta,
            "backlash": backlash, "k_mesh": k_mesh,
        })

    # gear_3, generalized across however many hops separate a node from
    # Yellow (N_cumulative already compounds hop-by-hop, same convention the
    # existing RPM chain uses) -- exposed for anyone wiring up a future
    # motor torque/inertia balance (motor_3); the integration below tracks
    # each node's own physical inertia directly and doesn't need it.
    reflected_inertia_at_motor = {
        stage["driven"]: J[stage["driven"]] * stage["N_cumulative"] ** 2 for stage in stages
    }

    return {"J": J, "stages": stages, "b_shaft": b_shaft, "nodes": nodes,
            "reflected_inertia_at_motor_kgm2": reflected_inertia_at_motor}


def mesh_torque(theta_driving, theta_driven, N, backlash, k_mesh):
    """gear_4 (dead-zone) + gear_5 (stiffness beyond it) -- one function
    since gear_5's formula only applies outside gear_4's dead-band.
    Public (moved out of dynamic_gear_simulator.py's private _mesh_torque)
    since signature/dynamic.py now calls it from a different module."""
    theta_gap = theta_driving / N - theta_driven
    if abs(theta_gap) < backlash:
        return 0.0
    sign = 1.0 if theta_gap > 0 else -1.0
    return k_mesh * (theta_gap - sign * backlash)


def equilibrium_state(train, omega_rad):
    """Solves the theta_gap each mesh needs, at the nominal rigid-chain
    speed, so that every node's net torque is exactly zero with no touch
    applied -- gear_5 inverted, cascaded from Output (free end, only its own
    gear_6 friction) back to Yellow. Used as simulate_touch()'s starting
    condition instead of an all-zero twist, so the reported transient
    reflects the touch only, not an unrelated gear-train wind-up transient."""
    b_shaft = train["b_shaft"]
    downstream_reaction = 0.0
    gaps = {}
    for stage in reversed(train["stages"]):
        T_friction = b_shaft * omega_rad[stage["driven"]]
        T_mesh_needed = T_friction + downstream_reaction
        sign = 1.0 if T_mesh_needed >= 0 else -1.0
        gaps[stage["driven"]] = sign * (stage["backlash"] + abs(T_mesh_needed) / stage["k_mesh"])
        downstream_reaction = T_mesh_needed / (stage["N"] * stage["eta"])

    theta = {"Yellow": 0.0}
    for stage in train["stages"]:
        theta[stage["driven"]] = theta[stage["driving"]] / stage["N"] - gaps[stage["driven"]]

    return {node: (theta[node], omega_rad[node]) for node in train["nodes"]}


def _derivatives(state, train, disturb_torque):
    """One RHS evaluation for RK4: state -> d(state)/dt.
    state = {node: (theta, omega)}. Yellow's omega is prescribed (held
    constant, see module docstring), so its derivative is always
    (omega_nominal, 0)."""
    nodes = train["nodes"]
    theta = {n: state[n][0] for n in nodes}
    omega = {n: state[n][1] for n in nodes}
    b_shaft = train["b_shaft"]

    T_mesh_on_driven = {}
    T_reaction_on_driving = {}
    for stage in train["stages"]:
        T_mesh = mesh_torque(theta[stage["driving"]], theta[stage["driven"]],
                              stage["N"], stage["backlash"], stage["k_mesh"])
        T_mesh_on_driven[stage["driven"]] = T_mesh
        # gear_2 inverted: T_out = T_in*N*eta -> T_in = T_out/(N*eta), the
        # torque the driving node must supply to sustain T_mesh downstream.
        T_reaction_on_driving[stage["driving"]] = T_mesh / (stage["N"] * stage["eta"])

    deriv = {}
    for node in nodes:
        if node == "Yellow":
            deriv[node] = (omega[node], 0.0)
            continue
        T_in = T_mesh_on_driven.get(node, 0.0)
        T_out = T_reaction_on_driving.get(node, 0.0)
        T_friction = b_shaft * omega[node]
        T_disturb = disturb_torque.get(node, 0.0)
        net_T = T_in - T_out - T_friction + T_disturb
        deriv[node] = (omega[node], net_T / train["J"][node])
    return deriv


def rk4_step(state, train, disturb_torque, dt):
    """Public (moved out of dynamic_gear_simulator.py's private
    _rk4_step) since signature/dynamic.py now calls it from a different
    module."""
    nodes = train["nodes"]

    def add(s, d, h):
        return {n: (s[n][0] + h * d[n][0], s[n][1] + h * d[n][1]) for n in nodes}

    k1 = _derivatives(state, train, disturb_torque)
    k2 = _derivatives(add(state, k1, dt / 2), train, disturb_torque)
    k3 = _derivatives(add(state, k2, dt / 2), train, disturb_torque)
    k4 = _derivatives(add(state, k3, dt), train, disturb_torque)
    new_state = {}
    for n in nodes:
        dtheta = (k1[n][0] + 2 * k2[n][0] + 2 * k3[n][0] + k4[n][0]) / 6
        domega = (k1[n][1] + 2 * k2[n][1] + 2 * k3[n][1] + k4[n][1]) / 6
        new_state[n] = (state[n][0] + dt * dtheta, state[n][1] + dt * domega)
    return new_state


def stable_dt(train):
    """RK4 timestep sized off the train's own fastest mesh resonance
    (omega_n = sqrt(k_mesh/J)), ~30 samples per period -- comfortably
    inside RK4's stability region and enough to resolve the oscillation
    shape. Needed because k_mesh is derived (cantilever-beam model, see
    build_gear_train()) rather than a fixed placeholder -- it moved from an
    unverified ~0.05-5 Nm/rad guess to a physically-derived ~1e3-1e4
    Nm/rad for this gear/module size, an ~1000x stiffer mesh with a
    correspondingly much higher resonant frequency, so a single hardcoded
    dt across all variants (TEETH_OUTPUT_BIG still varies, changing the
    last stage's driven radius and hence its k_mesh) is not safe."""
    max_wn = 0.0
    for stage in train["stages"]:
        wn = math.sqrt(stage["k_mesh"] / train["J"][stage["driven"]])
        max_wn = max(max_wn, wn)
    if max_wn <= 0:
        return 1e-5
    return (2 * math.pi / max_wn) / 15
