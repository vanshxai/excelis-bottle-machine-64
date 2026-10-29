"""
Digital twin builder -- Volumetric Technologies Servo Piston Filler / Depositor.

Talks to the isolated Formula Brain on 5052. Two phases:

  1. EXTEND -- teach the Brain the physics its 333-formula library was missing
     for this machine (ball-screw thrust conversion, power-law non-Newtonian
     nozzle flow, RSS accuracy budget, trapezoidal piston kinematics, hopper
     sizing). Every added formula is a published, verifiable engineering
     relation -- sources are cited inline.

  2. SOLVE -- hand the Brain the machine's INPUT spec and ask it to
     forward-chain to each OUTPUT. The Brain returns the full formula
     chain it walked, which is what makes this a twin rather than a
     spreadsheet: every number carries its derivation.

Writes twin_data.json, consumed by the Three.js wireframe page.
"""
import json
import os
import urllib.request

BRAIN = "http://127.0.0.1:5052"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twin_data.json")


def post(route, payload):
    req = urllib.request.Request(
        BRAIN + route,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


# ---------------------------------------------------------------------------
# PHASE 1 -- formulas the Brain did not have.
#
# Naming: every symbol carries a _pf suffix. The Brain merges variables onto
# shared graph nodes by name, so reusing bare `T`/`P`/`V` would silently fuse
# this machine's torque with the DC-motor and ESP32 nodes already in the
# library. The _pf namespace keeps the piston filler a separate physical
# instance, matching the convention formulas.py already uses for its own
# expansion passes.
# ---------------------------------------------------------------------------

NEW_FORMULAS = [
    # --- A0. INVERSE DESIGN -- bore/stroke derived, not assumed --------------
    # Volume V = (pi/4) D^2 S has infinite (D,S) solutions. The accuracy spec
    # breaks the tie because the two geometric error terms pull opposite ways:
    #
    #   e_stroke = 100*dS/S  and S = 4V/(pi D^2)   ->  grows as D^2
    #   e_bore   = 200*dD/D  (volume ~ D^2, so 2x the diameter error) -> falls as 1/D
    #
    # Minimising e_stroke^2 + e_bore^2 gives a closed-form optimum bore.
    # (dV/V = 2 dD/D is why the bore term carries the factor 200, not 100.)
    ("pf_optimal_bore",
     "D_bore_pf = (8*dD_bore_pf*V_disp_pf/(sqrt(2)*pi*dS_pos_pf))**(1/3)", "piston_filler"),

    # Nozzle bore is set by the shear-rate ceiling the product tolerates, not
    # chosen. Invert the Rabinowitsch-corrected wall shear rate at PEAK flow.
    ("pf_peak_flow", "Q_pk_pf = 1.5 * V_net_pf / t_disch_pf", "piston_filler"),
    ("pf_nozzle_from_shear_limit",
     "D_nz_pf = (32*Q_pk_pf*((3*n_pl_pf+1)/(4*n_pl_pf))/(pi*gdot_max_pf))**(1/3)", "piston_filler"),

    # Turndown: how small a deposit this one cylinder can still hold to spec.
    ("pf_fixed_error_terms",
     "e_fixed_pf = sqrt(e_valve_pf**2 + e_thermal_pf**2 + e_loadcell_pf**2)", "piston_filler"),
    ("pf_geometric_error_budget",
     "e_geo_pf = sqrt(e_spec_pf**2 - e_fixed_pf**2)", "piston_filler"),
    ("pf_min_stroke_allowance",
     "e_smin_pf = sqrt(e_geo_pf**2 - e_bore_pf**2)", "piston_filler"),
    ("pf_minimum_stroke", "S_min_pf = 100 * dS_pos_pf / e_smin_pf", "piston_filler"),
    ("pf_minimum_volume", "V_min_pf = A_piston_pf * S_min_pf", "piston_filler"),
    ("pf_turndown_ratio", "TD_pf = S_stroke_pf / S_min_pf", "piston_filler"),

    # --- A. volumetric displacement -----------------------------------------
    ("pf_piston_bore_area", "A_piston_pf = pi/4 * D_bore_pf**2", "piston_filler"),
    ("pf_stroke_required", "S_stroke_pf = V_disp_pf / A_piston_pf", "piston_filler"),
    ("pf_net_fill_volume", "V_net_pf = V_disp_pf * eta_vol_pf", "piston_filler"),
    ("pf_fill_mass", "m_fill_pf = rho_prod_pf * V_net_pf", "piston_filler"),

    # --- B. cycle timing / throughput ---------------------------------------
    ("pf_cycle_time", "t_cycle_pf = 60 / n_cycles_pf", "piston_filler"),
    ("pf_discharge_time", "t_disch_pf = t_cycle_pf * f_disch_pf", "piston_filler"),
    ("pf_flow_rate", "Q_pf = V_net_pf / t_disch_pf", "piston_filler"),
    ("pf_containers_per_hour", "N_cph_pf = n_cycles_pf * 60 * n_heads_pf", "piston_filler"),
    ("pf_volume_per_hour", "Vdot_hr_pf = n_cycles_pf * 60 * V_net_pf * n_heads_pf", "piston_filler"),

    # --- C. trapezoidal piston kinematics (1/3-1/3-1/3 accel-cruise-decel) ---
    # v_pk = 1.5*d/t and a = 4.5*d/t^2 are the standard closed forms for a
    # symmetric trapezoid where each phase takes one third of the move time.
    ("pf_peak_velocity", "v_pk_pf = 1.5 * S_stroke_pf / t_disch_pf", "piston_filler"),
    ("pf_peak_acceleration", "a_pk_pf = 4.5 * S_stroke_pf / t_disch_pf**2", "piston_filler"),

    # --- D. power-law non-Newtonian nozzle flow ------------------------------
    # The Brain's hydraulics domain (orifice_flow, darcy_weisbach) assumes a
    # Newtonian fluid. This machine is sold specifically for shear-thinning
    # product (sauces, pastes, creams), so Newtonian pressure drop would be
    # materially wrong. Weissenberg-Rabinowitsch-Mooney correction + Ostwald-
    # de Waele power law is the standard treatment.
    ("pf_nozzle_area", "A_nz_pf = pi/4 * D_nz_pf**2", "piston_filler"),
    ("pf_nozzle_velocity", "v_nz_pf = Q_pf / A_nz_pf", "piston_filler"),
    ("pf_apparent_wall_shear_rate", "gdot_app_pf = 32 * Q_pf / (pi * D_nz_pf**3)", "piston_filler"),
    ("pf_rabinowitsch_correction", "gdot_w_pf = gdot_app_pf * (3*n_pl_pf + 1) / (4*n_pl_pf)", "piston_filler"),
    ("pf_power_law_wall_stress", "tau_w_pf = K_pl_pf * gdot_w_pf**n_pl_pf", "piston_filler"),
    ("pf_apparent_viscosity", "mu_app_pf = tau_w_pf / gdot_w_pf", "piston_filler"),
    ("pf_nozzle_pressure_drop", "dP_nz_pf = 4 * tau_w_pf * L_nz_pf / D_nz_pf", "piston_filler"),
    # Metzner-Reed generalized Reynolds number -- tells us whether the deposit
    # stays laminar (it must, or the product shears and the fill degrades).
    ("pf_generalized_reynolds",
     "Re_gen_pf = rho_prod_pf * v_nz_pf**(2-n_pl_pf) * D_nz_pf**n_pl_pf / "
     "(K_pl_pf * ((3*n_pl_pf+1)/(4*n_pl_pf))**n_pl_pf * 8**(n_pl_pf-1))", "piston_filler"),

    # --- E. thrust build-up --------------------------------------------------
    ("pf_pressure_force", "F_press_pf = dP_nz_pf * A_piston_pf", "piston_filler"),
    ("pf_seal_friction_force",
     "F_seal_pf = mu_seal_pf * P_seal_pf * pi * D_bore_pf * w_seal_pf", "piston_filler"),
    ("pf_inertia_force", "F_inertia_pf = m_piston_pf * a_pk_pf", "piston_filler"),
    ("pf_total_thrust", "F_thrust_pf = F_press_pf + F_seal_pf + F_inertia_pf", "piston_filler"),

    # --- F. ball screw -> servo ---------------------------------------------
    # F = 2*pi*eta*T/p  =>  T = F*p/(2*pi*eta). Standard screw work-conservation
    # relation; the Brain had gears/belts/chains but no screw drive at all.
    ("pf_ballscrew_torque",
     "T_screw_pf = F_thrust_pf * p_lead_pf / (2*pi*eta_screw_pf)", "piston_filler"),
    ("pf_screw_angular_velocity", "omega_screw_pf = 2*pi*v_pk_pf / p_lead_pf", "piston_filler"),
    ("pf_screw_rpm", "N_screw_pf = 60 * v_pk_pf / p_lead_pf", "piston_filler"),
    ("pf_screw_angular_accel", "alpha_pf = 2*pi*a_pk_pf / p_lead_pf", "piston_filler"),
    # Reflected inertia of a linear load through a screw: J = m*(p/2pi)^2
    ("pf_reflected_load_inertia",
     "J_load_pf = m_piston_pf * (p_lead_pf/(2*pi))**2", "piston_filler"),
    ("pf_screw_inertia",
     "J_screw_pf = pi * rho_steel_pf * L_screw_pf * D_screw_pf**4 / 32", "piston_filler"),
    ("pf_total_inertia", "J_tot_pf = J_load_pf + J_screw_pf + J_rotor_pf", "piston_filler"),
    ("pf_accel_torque", "T_acc_pf = J_tot_pf * alpha_pf", "piston_filler"),
    ("pf_peak_motor_torque", "T_pk_pf = T_screw_pf + T_acc_pf", "piston_filler"),
    ("pf_servo_power", "P_servo_pf = T_pk_pf * omega_screw_pf", "piston_filler"),
    # Inertia ratio -- servo tuning stability check, 10:1 is the usual ceiling.
    ("pf_inertia_ratio", "R_inertia_pf = (J_load_pf + J_screw_pf) / J_rotor_pf", "piston_filler"),

    # --- F2. suction side -- the real speed limit on viscous product --------
    # A piston filler is usually suction-limited, not discharge-limited: the
    # cylinder can only pull down to vacuum, so available driving pressure is
    # atmospheric + hopper static head. This is why the inlet port is far
    # larger than the nozzle and why the hopper sits high.
    ("pf_suction_shear_rate",
     "gdot_in_pf = 32*Q_pk_pf/(pi*D_in_pf**3) * ((3*n_pl_pf+1)/(4*n_pl_pf))", "piston_filler"),
    ("pf_suction_wall_stress", "tau_in_pf = K_pl_pf * gdot_in_pf**n_pl_pf", "piston_filler"),
    ("pf_suction_pressure_drop", "dP_in_pf = 4 * tau_in_pf * L_in_pf / D_in_pf", "piston_filler"),
    ("pf_suction_available", "dP_avail_pf = P_atm_pf + P_head_pf", "piston_filler"),
    ("pf_suction_margin", "SM_pf = dP_avail_pf / dP_in_pf", "piston_filler"),

    # --- G. accuracy budget (RSS) -------------------------------------------
    # sigma_sys = sqrt(sum(sigma_i^2)). This is what actually justifies the
    # published +/-0.25% -- the Brain had no error-stacking formula at all.
    # Encoder resolution (10mm/2^17 = 76 nm) is NOT the driver; servo
    # positional repeatability -- screw lead grade + preload backlash +
    # following error at stop -- is roughly 300x larger and dominates.
    ("pf_stroke_position_error",
     "e_stroke_pf = 100 * dS_pos_pf / S_stroke_pf", "piston_filler"),
    ("pf_bore_tolerance_error",
     "e_bore_pf = 200 * dD_bore_pf / D_bore_pf", "piston_filler"),
    ("pf_rss_fill_accuracy",
     "e_tot_pf = sqrt(e_stroke_pf**2 + e_bore_pf**2 + e_valve_pf**2 + "
     "e_thermal_pf**2 + e_loadcell_pf**2)", "piston_filler"),
    ("pf_fill_mass_tolerance", "dm_fill_pf = m_fill_pf * e_tot_pf / 100", "piston_filler"),

    # --- H. servo thermal ----------------------------------------------------
    ("pf_servo_heat_loss", "P_loss_pf = P_servo_pf * (1 - eta_motor_pf)", "piston_filler"),
    ("pf_motor_temp_rise", "dT_motor_pf = P_loss_pf * Rth_motor_pf", "piston_filler"),

    # --- I. piston rod buckling (Euler) --------------------------------------
    ("pf_rod_second_moment", "I_rod_pf = pi * D_rod_pf**4 / 64", "piston_filler"),
    ("pf_rod_buckling_load",
     "P_crit_pf = pi**2 * E_rod_pf * I_rod_pf / Le_rod_pf**2", "piston_filler"),
    ("pf_rod_buckling_safety", "n_buckling_pf = P_crit_pf / F_thrust_pf", "piston_filler"),

    # --- J. hopper -----------------------------------------------------------
    ("pf_hopper_cone_volume", "V_cone_pf = pi * D_hop_pf**2 * H_cone_pf / 12", "piston_filler"),
    ("pf_hopper_cyl_volume", "V_hcyl_pf = pi * D_hop_pf**2 * H_cyl_pf / 4", "piston_filler"),
    ("pf_hopper_total_volume", "V_hop_pf = V_cone_pf + V_hcyl_pf", "piston_filler"),
    ("pf_machine_consumption", "Qdot_mach_pf = V_net_pf * n_cycles_pf * n_heads_pf / 60", "piston_filler"),
    ("pf_hopper_refill_interval", "t_refill_pf = V_hop_pf / Qdot_mach_pf", "piston_filler"),
    ("pf_hopper_static_head", "P_head_pf = rho_prod_pf * g_pf * H_cyl_pf", "piston_filler"),

    # --- K. whole-machine electrical ----------------------------------------
    ("pf_machine_power", "P_mach_pf = n_heads_pf * P_servo_pf / eta_drive_pf", "piston_filler"),
    ("pf_machine_current",
     "I_mach_pf = P_mach_pf / (V_line_pf * sqrt(3) * pf_pf)", "piston_filler"),
]


# ---------------------------------------------------------------------------
# PHASE 2 -- the machine's INPUT spec.
#
# confidence tags:
#   oem       = published by Volumetric Technologies / Excelis
#   estimated = industry-typical, NOT vendor-confirmed
#   material  = textbook property
# ---------------------------------------------------------------------------

INPUTS = {
    # --- geometry: bore, stroke and nozzle are now DERIVED, not assumed -----
    "V_disp_pf":    (946.35e-6, "m^3",    "oem",       "32 US fl oz nominal deposit, inside the published 0.05-156.64 oz range"),
    "dS_pos_pf":    (2.5e-5,    "m",      "estimated", "servo positional repeatability: C5 screw lead grade + preload backlash + following error"),
    "dD_bore_pf":   (1.27e-5,   "m",      "estimated", "bore machining tolerance, half of a 0.001 in band"),
    "e_spec_pf":    (0.25,      "%",      "oem",       "the published accuracy the machine must hold -- drives the whole geometry"),
    "gdot_max_pf":  (2000.0,    "1/s",    "estimated", "wall shear ceiling before shear-sensitive product degrades"),
    "eta_vol_pf":   (0.985,     "-",      "estimated", "volumetric efficiency: valve leak-back + product compressibility"),
    "D_rod_pf":     (0.032,     "m",      "estimated", "piston rod diameter"),
    "Le_rod_pf":    (0.400,     "m",      "estimated", "rod effective buckling length"),
    "E_rod_pf":     (193e9,     "Pa",     "material",  "elastic modulus, 316L stainless (OEM-confirmed material)"),
    "m_piston_pf":  (4.5,       "kg",     "estimated", "piston + rod + carriage moving mass"),

    # --- product rheology (estimated: pasta sauce, a named OEM application) --
    "K_pl_pf":      (15.0,      "Pa*s^n", "estimated", "power-law consistency index, pasta sauce"),
    "n_pl_pf":      (0.40,      "-",      "estimated", "flow behaviour index (<1 = shear-thinning)"),
    "rho_prod_pf":  (1100.0,    "kg/m^3", "estimated", "product density"),

    # --- nozzle (bore derived from the shear ceiling) + inlet port ----------
    "L_nz_pf":      (0.150,     "m",      "estimated", "nozzle + valve passage length"),
    "D_in_pf":      (0.060,     "m",      "estimated", "hopper-to-cylinder inlet port bore"),
    "L_in_pf":      (0.150,     "m",      "estimated", "inlet drop-tube length"),
    "P_atm_pf":     (101325.0,  "Pa",     "material",  "atmospheric pressure -- the ceiling on suction driving force"),

    # --- seals --------------------------------------------------------------
    "mu_seal_pf":   (0.12,      "-",      "material",  "PTFE-on-steel friction coefficient (OEM lists PTFE seals)"),
    "P_seal_pf":    (0.35e6,    "Pa",     "estimated", "seal contact pressure"),
    "w_seal_pf":    (0.008,     "m",      "estimated", "seal contact width"),

    # --- servo + ball screw drive -------------------------------------------
    "p_lead_pf":    (0.010,     "m/rev",  "estimated", "ball screw lead"),
    "eta_screw_pf": (0.90,      "-",      "material",  "ball screw efficiency (typical 85-95%)"),
    "D_screw_pf":   (0.025,     "m",      "estimated", "screw shaft diameter"),
    "L_screw_pf":   (0.400,     "m",      "estimated", "screw shaft length"),
    "rho_steel_pf": (7850.0,    "kg/m^3", "material",  "steel density"),
    "J_rotor_pf":   (0.42e-4,   "kg*m^2", "estimated", "servo rotor inertia, ~400 W frame"),
    "N_enc_pf":     (131072.0,  "cnt/rev","estimated", "17-bit absolute encoder"),
    "eta_motor_pf": (0.90,      "-",      "estimated", "servo motor efficiency"),
    "Rth_motor_pf": (1.2,       "C/W",    "estimated", "motor thermal resistance to ambient"),

    # --- error budget terms (bore + stroke terms are now derived) -----------
    "e_valve_pf":    (0.10,     "%",      "estimated", "valve cut-off repeatability -- dominant term"),
    "e_thermal_pf":  (0.08,     "%",      "estimated", "product thermal expansion during run"),
    "e_loadcell_pf": (0.05,     "%",      "estimated", "load-cell feedback error (OEM lists load cell feedback)"),

    # --- duty ---------------------------------------------------------------
    "n_cycles_pf":  (40.0,      "1/min",  "estimated", "cycle rate for a 32 oz deposit (OEM ceiling is 90/min at small fills)"),
    "f_disch_pf":   (0.40,      "-",      "estimated", "fraction of cycle spent on the discharge stroke"),
    "n_heads_pf":   (4.0,       "-",      "oem",       "4 heads, inside the published 1-24 head range"),

    # --- hopper -------------------------------------------------------------
    "D_hop_pf":     (0.610,     "m",      "estimated", "24 in hopper diameter"),
    "H_cone_pf":    (0.450,     "m",      "estimated", "hopper cone height"),
    "H_cyl_pf":     (0.300,     "m",      "estimated", "hopper straight-wall height"),
    "g_pf":         (9.80665,   "m/s^2",  "material",  "standard gravity"),

    # --- container: the one real dimensional ruler we have ------------------
    # A 32 oz jar is a standardised part, so it -- not guesswork -- sets head
    # pitch, nozzle height, and the whole vertical stack of the machine.
    "D_cont_pf":    (0.100,     "m",      "estimated", "32 oz jar outside diameter (standard part)"),
    "H_cont_pf":    (0.142,     "m",      "estimated", "32 oz jar height (standard part)"),
    "H_belt_pf":    (0.900,     "m",      "estimated", "conveyor surface height -- ergonomic standard, not a fill parameter"),
    "clr_cont_pf":  (0.050,     "m",      "estimated", "clearance between adjacent containers"),

    # --- line power ---------------------------------------------------------
    "V_line_pf":    (480.0,     "V",      "oem",       "480 V 3-phase (OEM lists 120/220/480 V)"),
    "pf_pf":        (0.85,      "-",      "estimated", "drive power factor"),
    "eta_drive_pf": (0.92,      "-",      "estimated", "servo drive/amplifier efficiency"),
}

TARGETS = [
    ("D_bore_pf",    "m",      "DERIVED optimal bore (min RSS geometric error)"),
    ("S_stroke_pf",  "m",      "DERIVED stroke for the nominal deposit"),
    ("D_nz_pf",      "m",      "DERIVED nozzle bore (shear ceiling)"),
    ("S_min_pf",     "m",      "Minimum stroke still holding the spec"),
    ("V_min_pf",     "m^3",    "Smallest deposit this cylinder can hold to spec"),
    ("TD_pf",        ":1",     "Turndown ratio on one cylinder"),
    ("A_piston_pf",  "m^2",    "Piston bore area"),
    ("V_net_pf",     "m^3",    "Net delivered volume per cycle"),
    ("m_fill_pf",    "kg",     "Delivered mass per cycle"),
    ("t_cycle_pf",   "s",      "Full cycle time"),
    ("t_disch_pf",   "s",      "Discharge stroke time"),
    ("Q_pf",         "m^3/s",  "Mean flow rate over discharge stroke"),
    ("v_pk_pf",      "m/s",    "Peak piston velocity"),
    ("a_pk_pf",      "m/s^2",  "Peak piston acceleration"),
    ("v_nz_pf",      "m/s",    "Nozzle exit velocity at mean flow"),
    ("gdot_w_pf",    "1/s",    "True wall shear rate, Rabinowitsch-corrected"),
    ("tau_w_pf",     "Pa",     "Wall shear stress at the nozzle"),
    ("mu_app_pf",    "Pa*s",   "Apparent viscosity at operating shear rate"),
    ("dP_nz_pf",     "Pa",     "Nozzle pressure drop at mean flow"),
    ("Re_gen_pf",    "-",      "Generalized Reynolds number (Metzner-Reed)"),
    ("F_press_pf",   "N",      "Thrust to overcome nozzle pressure"),
    ("F_seal_pf",    "N",      "Thrust to overcome seal friction"),
    ("F_inertia_pf", "N",      "Thrust to accelerate the piston"),
    ("F_thrust_pf",  "N",      "Total piston thrust"),
    ("T_screw_pf",   "N*m",    "Motor torque to hold thrust through the screw"),
    ("T_acc_pf",     "N*m",    "Motor torque to accelerate rotating inertia"),
    ("T_pk_pf",      "N*m",    "Peak motor torque"),
    ("N_screw_pf",   "rpm",    "Peak servo speed"),
    ("J_tot_pf",     "kg*m^2", "Total reflected inertia"),
    ("R_inertia_pf", "-",      "Inertia ratio (load:rotor)"),
    ("P_servo_pf",   "W",      "Peak servo shaft power, one head"),
    ("P_loss_pf",    "W",      "Servo heat loss"),
    ("dT_motor_pf",  "C",      "Motor temperature rise"),
    ("e_stroke_pf",  "%",      "Stroke repeatability error term"),
    ("e_bore_pf",    "%",      "Bore tolerance error term"),
    ("e_fixed_pf",   "%",      "Process error terms (valve+thermal+load cell)"),
    ("e_tot_pf",     "%",      "RSS total fill accuracy"),
    ("dm_fill_pf",   "kg",     "Fill mass tolerance band"),
    ("gdot_in_pf",   "1/s",    "Inlet-port wall shear rate on suction"),
    ("dP_in_pf",     "Pa",     "Suction pressure drop required"),
    ("dP_avail_pf",  "Pa",     "Suction pressure available (atm + head)"),
    ("SM_pf",        ":1",     "Suction margin -- >1 means no starvation"),
    ("I_rod_pf",     "m^4",    "Rod second moment of area"),
    ("P_crit_pf",    "N",      "Rod Euler buckling load"),
    ("n_buckling_pf","-",      "Rod buckling safety factor"),
    ("V_hop_pf",     "m^3",    "Hopper capacity"),
    ("Qdot_mach_pf", "m^3/s",  "Whole-machine product consumption"),
    ("t_refill_pf",  "s",      "Hopper refill interval"),
    ("P_head_pf",    "Pa",     "Hopper static head at the cylinder inlet"),
    ("N_cph_pf",     "1/h",    "Containers per hour"),
    ("Vdot_hr_pf",   "m^3/h",  "Product throughput per hour"),
    ("P_mach_pf",    "W",      "Whole-machine electrical demand"),
    ("I_mach_pf",    "A",      "Line current draw"),
]


def main():
    print(f"Brain status: {json.loads(urllib.request.urlopen(BRAIN + '/brain/status', timeout=10).read())}")

    print(f"\n--- PHASE 1: extending the Brain with {len(NEW_FORMULAS)} formulas ---")
    added = []
    for name, formula, domain in NEW_FORMULAS:
        variables = sorted(set(
            t for t in __import__("re").findall(r"[A-Za-z_][A-Za-z0-9_]*", formula)
            if t.endswith("_pf")
        ))
        r = post("/brain/extend", {
            "name": name, "formula": formula, "domain": domain, "variables": variables,
        })
        if not r.get("ok"):
            raise SystemExit(f"FAILED to add {name}: {r}")
        added.append(name)
    status = json.loads(urllib.request.urlopen(BRAIN + "/brain/status", timeout=10).read())
    print(f"  added {len(added)} formulas -> graph now {status['nodes']} nodes / {status['edges']} edges")

    known = {k: v[0] for k, v in INPUTS.items()}

    print(f"\n--- PHASE 2: solving {len(TARGETS)} outputs ---")
    results, failures = {}, []
    for target, unit, label in TARGETS:
        r = post("/brain/solve", {"known": known, "target": target, "path_type": "shortest"})
        if r.get("result") is None:
            failures.append((target, r.get("note")))
            continue
        results[target] = {
            "value": r["result"], "unit": unit, "label": label,
            "confidence": r["confidence"], "path": r["path"],
            "trace": [
                {"formula": t["formula"], "equation": t["equation"],
                 "output": t["output"], "value": t["value"]}
                for t in r["trace"]
            ],
        }
        print(f"  {target:16s} = {r['result']:>16.6g} {unit:8s} [{len(r['path'])} formula chain]")

    if failures:
        print("\n  UNSOLVED:")
        for t, note in failures:
            print(f"    {t}: {note}")

    payload = {
        "machine": {
            "name": "Servo Piston Filler / Depositor",
            "manufacturer": "Volumetric Technologies (an Excelis Packaging Automation company)",
            "category": "Liquid Filling Machines > Piston Fillers > Servo Series",
            "source_url": "https://volumetrictechnologies.com/piston-filler-machines/servo-series-filler-depositor",
            "oem_published": {
                "accuracy": "+/- 0.25% of 1% on homogeneous products",
                "deposit_volume": "0.05 oz - 156.64 oz",
                "heads": "1 - 24",
                "speed": "up to 90 cycles/min",
                "particulate": "up to 4 in diameter",
                "materials": "316L / 304 stainless, USDA/FDA contact surfaces",
                "power": "120 / 220 / 480 V + clean compressed air",
                "control": "servo drive + touchscreen HMI, PLC in UL-listed panel",
                "feedback": "load cell feedback control",
                "cycle_profile": "soft start, fast fill, soft end",
            },
        },
        "inputs": {
            k: {"value": v[0], "unit": v[1], "confidence": v[2], "note": v[3]}
            for k, v in INPUTS.items()
        },
        "outputs": results,
        "formulas_added": [
            {"name": n, "equation": f, "domain": d} for n, f, d in NEW_FORMULAS
        ],
        "brain": {
            "base_formulas": 333,
            "added_formulas": len(added),
            "total_nodes": status["nodes"],
            "total_edges": status["edges"],
        },
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nwrote {OUT}")
    print(f"solved {len(results)}/{len(TARGETS)} targets")


if __name__ == "__main__":
    main()
