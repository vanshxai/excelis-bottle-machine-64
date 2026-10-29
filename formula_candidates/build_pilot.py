"""
Pilot batch of candidate formulas for the Yanthros core engine.

STAGING ONLY -- nothing here is written into faulter-formula-brain. Each entry
carries the page it came from (fetched 2026-09-21), the section, and three
automatic checks:
  parses      the equation is valid sympy with a single symbol on the left
  dimensions  left and right sides have the same SI dimensions, and every
              exp/log/trig argument is dimensionless (catches mis-extractions)
  dedupe      a formula whose name or shape already exists in the engine is moved
              to already_in_engine.json instead of the candidate list
Status stays "candidate" (or "needs_review") until a person approves it.

Run:  python3 build_pilot.py     -> pilot_100.json, pilot_100.csv, rejected.json, already_in_engine.json
"""
import csv
import json
import os
import sys

import sympy as sp
from sympy.physics import units as U
from sympy.physics.units.systems.si import SI

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "faulter-formula-brain"))
from formulas import FORMULAS as ENGINE, FORMULA_DOMAINS as ENGINE_DOMAINS  # noqa: E402

ACCESSED = "2026-09-21"
WIKI = "Wikipedia (CC BY-SA 4.0)"
OSX = "OpenStax University Physics Vol. 2 (CC BY 4.0)"

SOURCES = {
    "EBB":  ("Euler-Bernoulli beam theory", "https://en.wikipedia.org/wiki/Euler%E2%80%93Bernoulli_beam_theory", WIKI),
    "BUCK": ("Buckling", "https://en.wikipedia.org/wiki/Buckling", WIKI),
    "SMA":  ("List of second moments of area", "https://en.wikipedia.org/wiki/List_of_second_moments_of_area", WIKI),
    "DEFL": ("Deflection (engineering)", "https://en.wikipedia.org/wiki/Deflection_(engineering)", WIKI),
    "BEAR": ("Bearing capacity", "https://en.wikipedia.org/wiki/Bearing_capacity", WIKI),
    "MC":   ("Mohr-Coulomb theory", "https://en.wikipedia.org/wiki/Mohr%E2%80%93Coulomb_theory", WIKI),
    "TSI":  ("Tsiolkovsky rocket equation", "https://en.wikipedia.org/wiki/Tsiolkovsky_rocket_equation", WIKI),
    "VIS":  ("Vis-viva equation", "https://en.wikipedia.org/wiki/Vis-viva_equation", WIKI),
    "HOH":  ("Hohmann transfer orbit", "https://en.wikipedia.org/wiki/Hohmann_transfer_orbit", WIKI),
    "LID":  ("Lift-induced drag", "https://en.wikipedia.org/wiki/Lift-induced_drag", WIKI),
    "RNG":  ("Range (aeronautics)", "https://en.wikipedia.org/wiki/Range_(aeronautics)", WIKI),
    "ZN":   ("Ziegler-Nichols method", "https://en.wikipedia.org/wiki/Ziegler%E2%80%93Nichols_method", WIKI),
    "PID":  ("PID controller", "https://en.wikipedia.org/wiki/PID_controller", WIKI),
    "DAMP": ("Damping ratio", "https://en.wikipedia.org/wiki/Damping_ratio", WIKI),
    "STEP": ("Step response", "https://en.wikipedia.org/wiki/Step_response", WIKI),
    "OS8":  ("Ch. 8 Key Equations (Capacitance)", "https://openstax.org/books/university-physics-volume-2/pages/8-key-equations", OSX),
    "OS9":  ("Ch. 9 Key Equations (Current and Resistance)", "https://openstax.org/books/university-physics-volume-2/pages/9-key-equations", OSX),
    "OS10": ("Ch. 10 Key Equations (Direct-Current Circuits)", "https://openstax.org/books/university-physics-volume-2/pages/10-key-equations", OSX),
    "OS14": ("Ch. 14 Key Equations (Inductance)", "https://openstax.org/books/university-physics-volume-2/pages/14-key-equations", OSX),
    "OS15": ("Ch. 15 Key Equations (Alternating-Current Circuits)", "https://openstax.org/books/university-physics-volume-2/pages/15-key-equations", OSX),
}

CIV, AER, CTL, ELE = ("Civil & Structural Engineering", "Aerospace Engineering",
                      "Control Engineering", "Electrical Engineering")

ENTRIES = []


def add(id_, eq, syms, disc, domain, src, section, form="literal", note="", hold=""):
    """syms: {symbol: 'unit | meaning'}; unit '1' means dimensionless."""
    ENTRIES.append(dict(id=id_, eq=eq, syms=syms, disc=disc, domain=domain,
                        src=src, section=section, form=form, note=note, hold=hold))


# ------------------------------------------------------------ civil / structural
sc = "civil_structural"
add("euler_critical_load", "F_cr = pi**2*E_mod*I_area/(K_eff*L_col)**2",
    {"F_cr": "newton | critical buckling load", "E_mod": "pascal | Young's modulus",
     "I_area": "meter**4 | smallest second moment of area", "K_eff": "1 | effective length factor",
     "L_col": "meter | unsupported column length"}, CIV, sc, "BUCK", "Columns")
add("euler_critical_stress", "sigma_cr_col = pi**2*E_mod/lam_slender**2",
    {"sigma_cr_col": "pascal | critical buckling stress", "E_mod": "pascal | Young's modulus",
     "lam_slender": "1 | slenderness ratio l/r"}, CIV, sc, "BUCK", "Columns")
add("rankine_gordon_load", "F_max_rg = 1/(1/F_euler + 1/F_crush)",
    {"F_max_rg": "newton | Rankine-Gordon buckling load", "F_euler": "newton | Euler critical load",
     "F_crush": "newton | crushing load"}, CIV, sc, "BUCK", "Columns", form="rearranged",
    note="Page gives 1/Fmax = 1/Fe + 1/Fc; solved for Fmax.")
add("plate_buckling_critical_stress",
    "sigma_cr_plate = k_plate*pi**2*E_mod/(12*(1 - nu_poisson**2)*(b_plate/t_plate)**2)",
    {"sigma_cr_plate": "pascal | plate critical stress", "k_plate": "1 | buckling coefficient",
     "E_mod": "pascal | Young's modulus", "nu_poisson": "1 | Poisson's ratio",
     "b_plate": "meter | plate width", "t_plate": "meter | plate thickness"}, CIV, sc, "BUCK", "Plate buckling")
add("plate_buckling_line_load",
    "N_cr_plate = k_plate*pi**2*E_mod*t_plate**3/(12*(1 - nu_poisson**2)*b_plate**2)",
    {"N_cr_plate": "newton/meter | critical compressive load per unit width",
     "k_plate": "1 | buckling coefficient", "E_mod": "pascal | Young's modulus",
     "t_plate": "meter | plate thickness", "nu_poisson": "1 | Poisson's ratio",
     "b_plate": "meter | plate width"}, CIV, sc, "BUCK", "Plate buckling",
    note="Page labels this 'critical load'; dimensionally it is force per unit width.")
add("plate_buckling_coefficient", "k_plate = (m_half*b_plate/a_plate + a_plate/(m_half*b_plate))**2",
    {"k_plate": "1 | buckling coefficient", "m_half": "1 | number of half sine waves lengthwise",
     "b_plate": "meter | plate width", "a_plate": "meter | plate length"}, CIV, sc, "BUCK", "Plate buckling")
add("plate_effective_width",
    "b_eff = b_plate*sqrt((sigma_cr_plate/sigma_yield)*(1 - 1.022*sqrt(sigma_cr_plate/sigma_yield)))",
    {"b_eff": "meter | effective width", "b_plate": "meter | actual width",
     "sigma_cr_plate": "pascal | critical stress", "sigma_yield": "pascal | yield stress"},
    CIV, sc, "BUCK", "Plate buckling", note="Source marks this as an approximation.",
    hold="Re-read against the page: the equation is printed exactly like this, but it goes imaginary as "
         "sigma_cr/sigma_y approaches 1 and differs from the usual Winter form (coefficient 0.22 outside the root). "
         "Do not approve until checked against a second source.")
add("lateral_torsional_cb",
    "Cb_ltb = 12.5*M_max_ltb/(2.5*M_max_ltb + 3*M_A_ltb + 4*M_B_ltb + 3*M_C_ltb)",
    {"Cb_ltb": "1 | moment gradient modification factor", "M_max_ltb": "newton*meter | max moment in segment",
     "M_A_ltb": "newton*meter | moment at quarter point", "M_B_ltb": "newton*meter | moment at centerline",
     "M_C_ltb": "newton*meter | moment at three-quarter point"}, CIV, sc, "BUCK", "Lateral-torsional buckling")
add("self_buckling_height",
    "h_crit = ((9*B_bessel**2/4)*E_mod*I_area/(rho_mat*g_grav*A_area))**(1/3)",
    {"h_crit": "meter | critical self-buckling height", "B_bessel": "1 | first zero of Bessel function (1.866)",
     "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area",
     "rho_mat": "kilogram/meter**3 | density", "g_grav": "meter/second**2 | gravity",
     "A_area": "meter**2 | cross-section area"}, CIV, sc, "BUCK", "Self-buckling")
add("ring_buckling_pressure_fluid", "q_cr_ring = 3*E_mod*I_ring/R_ring**2",
    {"q_cr_ring": "pascal | critical buckling pressure", "E_mod": "pascal | Young's modulus",
     "I_ring": "meter**4 | second moment of ring section", "R_ring": "meter | mean radius"},
    CIV, sc, "BUCK", "Thin-walled rings",
    note="Extracted as printed by the page summary; dimension check is expected to reject it (needs R^3 or line-load units). Re-read the page before any fix.")
add("flexure_stress", "sigma_bend = M_bend*z_dist/I_area",
    {"sigma_bend": "pascal | bending stress", "M_bend": "newton*meter | bending moment",
     "z_dist": "meter | distance from neutral axis", "I_area": "meter**4 | second moment of area"},
    CIV, sc, "EBB", "Simple or symmetrical bending")
add("section_modulus", "S_sec = I_area/c_fiber",
    {"S_sec": "meter**3 | section modulus", "I_area": "meter**4 | second moment of area",
     "c_fiber": "meter | distance to extreme fibre"}, CIV, sc, "EBB", "Maximum stresses at a cross-section")
add("max_bending_stress_section", "sigma_max_bend = M_bend/S_sec",
    {"sigma_max_bend": "pascal | maximum bending stress", "M_bend": "newton*meter | bending moment",
     "S_sec": "meter**3 | section modulus"}, CIV, sc, "EBB", "Maximum stresses at a cross-section")
add("beam_natural_freq_hinged", "omega_n_beam = n_mode**2*pi**2/L_beam**2*sqrt(E_mod*I_area/mu_lin)",
    {"omega_n_beam": "1/second | nth natural frequency (rad/s)", "n_mode": "1 | mode number",
     "L_beam": "meter | beam length", "E_mod": "pascal | Young's modulus",
     "I_area": "meter**4 | second moment of area", "mu_lin": "kilogram/meter | mass per unit length"},
    CIV, sc, "EBB", "Example: hinged-hinged beam")
add("beam_natural_freq_cantilever_1", "omega_1_cant = 3.5160/L_beam**2*sqrt(E_mod*I_area/mu_lin)",
    {"omega_1_cant": "1/second | first natural frequency (rad/s)", "L_beam": "meter | beam length",
     "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area",
     "mu_lin": "kilogram/meter | mass per unit length"}, CIV, sc, "EBB", "Example: cantilevered beam")
add("cantilever_end_load_deflection", "delta_cant_end = F_load*L_beam**3/(3*E_mod*I_area)",
    {"delta_cant_end": "meter | tip deflection", "F_load": "newton | tip force", "L_beam": "meter | length",
     "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area"},
    CIV, sc, "DEFL", "Cantilever, end loaded")
add("cantilever_end_load_slope", "phi_cant_end = F_load*L_beam**2/(2*E_mod*I_area)",
    {"phi_cant_end": "1 | tip slope (rad)", "F_load": "newton | tip force", "L_beam": "meter | length",
     "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area"},
    CIV, sc, "DEFL", "Cantilever, end loaded")
add("cantilever_end_load_deflection_x",
    "delta_cant_x = F_load*x_pos**2/(6*E_mod*I_area)*(3*L_beam - x_pos)",
    {"delta_cant_x": "meter | deflection at x", "F_load": "newton | tip force", "x_pos": "meter | position",
     "L_beam": "meter | length", "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area"},
    CIV, sc, "DEFL", "Cantilever, end loaded")
add("cantilever_uniform_deflection", "delta_cantu_end = q_load*L_beam**4/(8*E_mod*I_area)",
    {"delta_cantu_end": "meter | tip deflection", "q_load": "newton/meter | uniform load",
     "L_beam": "meter | length", "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area"},
    CIV, sc, "DEFL", "Cantilever, uniformly loaded")
add("simple_center_load_deflection", "delta_simple_mid = F_load*L_beam**3/(48*E_mod*I_area)",
    {"delta_simple_mid": "meter | midspan deflection", "F_load": "newton | centre force",
     "L_beam": "meter | span", "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area"},
    CIV, sc, "DEFL", "Simple beam, centre loaded")
add("simple_center_load_deflection_x",
    "delta_simple_x = F_load*x_pos/(48*E_mod*I_area)*(3*L_beam**2 - 4*x_pos**2)",
    {"delta_simple_x": "meter | deflection at x (0<=x<=L/2)", "F_load": "newton | centre force",
     "x_pos": "meter | position", "L_beam": "meter | span", "E_mod": "pascal | Young's modulus",
     "I_area": "meter**4 | second moment of area"}, CIV, sc, "DEFL", "Simple beam, centre loaded")
add("simple_offcenter_max_deflection",
    "delta_simple_off_max = F_load*a_load*(L_beam**2 - a_load**2)**(3/2)/(9*sqrt(3)*L_beam*E_mod*I_area)",
    {"delta_simple_off_max": "meter | maximum deflection", "F_load": "newton | force",
     "a_load": "meter | load distance from nearest support", "L_beam": "meter | span",
     "E_mod": "pascal | Young's modulus", "I_area": "meter**4 | second moment of area"},
    CIV, sc, "DEFL", "Simple beam, off-centre loaded")
add("simple_offcenter_max_location", "x_max_off = sqrt((L_beam**2 - a_load**2)/3)",
    {"x_max_off": "meter | location of max deflection from nearest support", "L_beam": "meter | span",
     "a_load": "meter | load distance from nearest support"}, CIV, sc, "DEFL", "Simple beam, off-centre loaded")
add("simple_center_load_moment", "M_simple_x = F_load*x_pos/2",
    {"M_simple_x": "newton*meter | bending moment for 0<=x<=L/2", "F_load": "newton | centre force",
     "x_pos": "meter | position"}, CIV, sc, "EBB", "Three-point bending")
add("second_moment_rectangle", "I_rect = b_w*h_d**3/12",
    {"I_rect": "meter**4 | second moment about centroidal x-axis", "b_w": "meter | width", "h_d": "meter | height"},
    CIV, sc, "SMA", "Rectangle")
add("second_moment_circle", "I_circ = pi*r_c**4/4",
    {"I_circ": "meter**4 | second moment", "r_c": "meter | radius"}, CIV, sc, "SMA", "Filled circle")
add("polar_moment_circle", "J_circ = pi*r_c**4/2",
    {"J_circ": "meter**4 | polar second moment", "r_c": "meter | radius"}, CIV, sc, "SMA", "Filled circle")
add("second_moment_annulus", "I_ann = pi*(r_out**4 - r_in**4)/4",
    {"I_ann": "meter**4 | second moment", "r_out": "meter | outer radius", "r_in": "meter | inner radius"},
    CIV, sc, "SMA", "Annulus")
add("parallel_axis_theorem", "I_shift = I_cent + A_area*d_off**2",
    {"I_shift": "meter**4 | second moment about parallel axis", "I_cent": "meter**4 | second moment about centroid",
     "A_area": "meter**2 | area", "d_off": "meter | axis offset"}, CIV, sc, "SMA", "Parallel axis theorem")
add("mohr_coulomb_shear_strength", "tau_soil = sigma_n*tan(phi_fric) + c_coh",
    {"tau_soil": "pascal | shear strength", "sigma_n": "pascal | normal stress",
     "phi_fric": "1 | internal friction angle (rad)", "c_coh": "pascal | cohesion"}, CIV, sc, "MC", "Mohr-Coulomb criterion")
add("mohr_coulomb_principal_form", "tau_m = sigma_m*sin(phi_fric) + c_coh*cos(phi_fric)",
    {"tau_m": "pascal | (s1-s3)/2 max shear stress", "sigma_m": "pascal | (s1+s3)/2 mean normal stress",
     "phi_fric": "1 | internal friction angle (rad)", "c_coh": "pascal | cohesion"}, CIV, sc, "MC", "Principal stress form")
add("terzaghi_strip_footing",
    "q_ult_strip = c_coh*N_c + sigma_zD*N_q + 0.5*gamma_soil*B_found*N_gam",
    {"q_ult_strip": "pascal | ultimate bearing capacity", "c_coh": "pascal | effective cohesion",
     "N_c": "1 | bearing factor", "sigma_zD": "pascal | vertical effective stress at depth",
     "N_q": "1 | bearing factor", "gamma_soil": "newton/meter**3 | effective unit weight",
     "B_found": "meter | footing width", "N_gam": "1 | bearing factor"}, CIV, sc, "BEAR", "Terzaghi general shear")
add("terzaghi_square_footing",
    "q_ult_sq = 1.3*c_coh*N_c + sigma_zD*N_q + 0.4*gamma_soil*B_found*N_gam",
    {"q_ult_sq": "pascal | ultimate bearing capacity", "c_coh": "pascal | effective cohesion",
     "N_c": "1 | bearing factor", "sigma_zD": "pascal | vertical effective stress at depth",
     "N_q": "1 | bearing factor", "gamma_soil": "newton/meter**3 | effective unit weight",
     "B_found": "meter | footing width", "N_gam": "1 | bearing factor"}, CIV, sc, "BEAR", "Terzaghi general shear")
add("terzaghi_circular_footing",
    "q_ult_circ = 1.3*c_coh*N_c + sigma_zD*N_q + 0.3*gamma_soil*B_found*N_gam",
    {"q_ult_circ": "pascal | ultimate bearing capacity", "c_coh": "pascal | effective cohesion",
     "N_c": "1 | bearing factor", "sigma_zD": "pascal | vertical effective stress at depth",
     "N_q": "1 | bearing factor", "gamma_soil": "newton/meter**3 | effective unit weight",
     "B_found": "meter | footing diameter", "N_gam": "1 | bearing factor"}, CIV, sc, "BEAR", "Terzaghi general shear")
add("bearing_nc_from_nq", "N_c = (N_q - 1)/tan(phi_fric)",
    {"N_c": "1 | bearing factor", "N_q": "1 | bearing factor", "phi_fric": "1 | friction angle (rad), phi>0"},
    CIV, sc, "BEAR", "Bearing capacity factors")
add("allowable_bearing_capacity", "q_all = q_ult/FS_safety",
    {"q_all": "pascal | allowable bearing capacity", "q_ult": "pascal | ultimate bearing capacity",
     "FS_safety": "1 | factor of safety"}, CIV, sc, "BEAR", "Factor of safety")
add("bearing_n_gamma_coduto", "N_gam = 2*(N_q + 1)*tan(phi_fric)/(1 + 0.4*sin(4*phi_fric))",
    {"N_gam": "1 | bearing factor", "N_q": "1 | bearing factor", "phi_fric": "1 | friction angle (rad)"},
    CIV, sc, "BEAR", "Bearing capacity factors")

# ------------------------------------------------------------------- aerospace
sa = "aerospace"
add("rocket_equation", "dv_rocket = v_e*log(m_wet/m_dry)",
    {"dv_rocket": "meter/second | delta-v", "v_e": "meter/second | effective exhaust velocity",
     "m_wet": "kilogram | initial mass", "m_dry": "kilogram | final mass"}, AER, sa, "TSI", "Derivation")
add("rocket_wet_mass", "m_wet_req = m_dry*exp(dv_rocket/v_e)",
    {"m_wet_req": "kilogram | required initial mass", "m_dry": "kilogram | final mass",
     "dv_rocket": "meter/second | delta-v", "v_e": "meter/second | effective exhaust velocity"},
    AER, sa, "TSI", "Derivation")
add("rocket_propellant_to_dry_ratio", "prop_ratio = exp(dv_rocket/v_e) - 1",
    {"prop_ratio": "1 | propellant mass / dry mass", "dv_rocket": "meter/second | delta-v",
     "v_e": "meter/second | effective exhaust velocity"}, AER, sa, "TSI", "Derivation")
add("exhaust_velocity_from_isp", "v_e = g0_std*Isp_s",
    {"v_e": "meter/second | effective exhaust velocity", "g0_std": "meter/second**2 | standard gravity 9.80665",
     "Isp_s": "second | specific impulse"}, AER, sa, "TSI", "Specific impulse")
add("vis_viva_speed", "v_orb = sqrt(mu_grav*(2/r_orb - 1/a_sma))",
    {"v_orb": "meter/second | orbital speed", "mu_grav": "meter**3/second**2 | GM",
     "r_orb": "meter | distance from central body", "a_sma": "meter | semi-major axis"},
    AER, sa, "VIS", "Vis-viva", form="rearranged", note="Page gives v^2 = GM(2/r - 1/a); positive root taken.")
add("specific_orbital_energy", "eps_orb = v_orb**2/2 - mu_grav/r_orb",
    {"eps_orb": "meter**2/second**2 | specific orbital energy (J/kg)", "v_orb": "meter/second | orbital speed",
     "mu_grav": "meter**3/second**2 | GM", "r_orb": "meter | orbital radius"}, AER, sa, "VIS", "Energy")
add("escape_speed", "v_esc = sqrt(2*mu_grav/r_orb)",
    {"v_esc": "meter/second | escape speed", "mu_grav": "meter**3/second**2 | GM",
     "r_orb": "meter | distance from centre"}, AER, sa, "VIS", "Escape velocity")
add("specific_angular_momentum", "h_ang = b_sma*sqrt(mu_grav/a_sma)",
    {"h_ang": "meter**2/second | specific angular momentum", "b_sma": "meter | semi-minor axis",
     "mu_grav": "meter**3/second**2 | GM", "a_sma": "meter | semi-major axis"}, AER, sa, "VIS", "Angular momentum")
add("hohmann_dv1", "dv1 = sqrt(mu_grav/r1)*(sqrt(2*r2/(r1 + r2)) - 1)",
    {"dv1": "meter/second | first burn", "mu_grav": "meter**3/second**2 | GM",
     "r1": "meter | departure orbit radius", "r2": "meter | arrival orbit radius"}, AER, sa, "HOH", "Delta-v")
add("hohmann_dv2", "dv2 = sqrt(mu_grav/r2)*(1 - sqrt(2*r1/(r1 + r2)))",
    {"dv2": "meter/second | second burn", "mu_grav": "meter**3/second**2 | GM",
     "r1": "meter | departure orbit radius", "r2": "meter | arrival orbit radius"}, AER, sa, "HOH", "Delta-v")
add("hohmann_transfer_time", "t_hoh = pi*sqrt((r1 + r2)**3/(8*mu_grav))",
    {"t_hoh": "second | transfer time", "r1": "meter | departure orbit radius",
     "r2": "meter | arrival orbit radius", "mu_grav": "meter**3/second**2 | GM"}, AER, sa, "HOH", "Transfer time")
add("induced_drag_coefficient", "CDi = CL_w**2/(pi*AR_wing*e_span)",
    {"CDi": "1 | induced drag coefficient", "CL_w": "1 | lift coefficient", "AR_wing": "1 | aspect ratio",
     "e_span": "1 | span efficiency factor"}, AER, sa, "LID", "Induced drag coefficient")
add("induced_drag_force", "Di_force = L_lift**2/(0.5*rho0_sl*V_eq**2*pi*b_span**2)",
    {"Di_force": "newton | induced drag", "L_lift": "newton | lift", "rho0_sl": "kilogram/meter**3 | sea-level density",
     "V_eq": "meter/second | equivalent airspeed", "b_span": "meter | wingspan"}, AER, sa, "LID", "Induced drag")
add("aspect_ratio", "AR_wing = b_span**2/S_ref",
    {"AR_wing": "1 | aspect ratio", "b_span": "meter | wingspan", "S_ref": "meter**2 | wing area"},
    AER, sa, "LID", "Aspect ratio")
add("lift_coefficient_definition", "CL_w = L_lift/(0.5*rho0_sl*V_eq**2*S_ref)",
    {"CL_w": "1 | lift coefficient", "L_lift": "newton | lift", "rho0_sl": "kilogram/meter**3 | sea-level density",
     "V_eq": "meter/second | equivalent airspeed", "S_ref": "meter**2 | wing area"}, AER, sa, "LID", "Lift coefficient")
add("propeller_range_breguet", "R_prop = eta_prop/(g0_std*c_p_sfc)*LD_ratio*log(W1_mass/W2_mass)",
    {"R_prop": "meter | range", "eta_prop": "1 | propulsive efficiency", "g0_std": "meter/second**2 | gravity",
     "c_p_sfc": "kilogram/joule | power-specific fuel consumption", "LD_ratio": "1 | lift-to-drag ratio",
     "W1_mass": "kilogram | initial mass", "W2_mass": "kilogram | final mass"}, AER, sa, "RNG", "Propeller aircraft")
add("jet_range_fixed_altitude", "R_jet = 2*V1_speed/(g0_std*c_T_sfc)*LD_ratio*(1 - sqrt(W2_mass/W1_mass))",
    {"R_jet": "meter | range", "V1_speed": "meter/second | initial speed", "g0_std": "meter/second**2 | gravity",
     "c_T_sfc": "second/meter | thrust-specific fuel consumption (kg/N/s)", "LD_ratio": "1 | lift-to-drag ratio",
     "W1_mass": "kilogram | initial mass", "W2_mass": "kilogram | final mass"}, AER, sa, "RNG", "Jet aircraft, fixed altitude")
add("electric_aircraft_range", "R_elec = E_spec/g0_std*eta_tot*LD_ratio*(W_batt/W_tot)",
    {"R_elec": "meter | range", "E_spec": "joule/kilogram | battery specific energy", "g0_std": "meter/second**2 | gravity",
     "eta_tot": "1 | total efficiency", "LD_ratio": "1 | lift-to-drag ratio",
     "W_batt": "kilogram | battery mass", "W_tot": "kilogram | total mass"}, AER, sa, "RNG", "Electric aircraft")
add("wind_efficiency", "eta_wind = (TAS - HW_avg)/TAS",
    {"eta_wind": "1 | wind efficiency", "TAS": "meter/second | true airspeed", "HW_avg": "meter/second | average headwind"},
    AER, sa, "RNG", "Operational efficiency")

# --------------------------------------------------------------------- control
sk_ = "control_systems"
add("zn_p_only_kp", "Kp_zn_p = 0.5*Ku_zn",
    {"Kp_zn_p": "1 | P-only proportional gain", "Ku_zn": "1 | ultimate gain"}, CTL, sk_, "ZN", "Tuning table, P")
add("zn_pi_kp", "Kp_zn_pi = 0.45*Ku_zn",
    {"Kp_zn_pi": "1 | PI proportional gain", "Ku_zn": "1 | ultimate gain"}, CTL, sk_, "ZN", "Tuning table, PI")
add("zn_pi_ti", "Ti_zn_pi = 0.833*Pu_zn",
    {"Ti_zn_pi": "second | PI integral time", "Pu_zn": "second | ultimate period"}, CTL, sk_, "ZN", "Tuning table, PI")
add("zn_pd_kp", "Kp_zn_pd = 0.8*Ku_zn",
    {"Kp_zn_pd": "1 | PD proportional gain", "Ku_zn": "1 | ultimate gain"}, CTL, sk_, "ZN", "Tuning table, PD")
add("zn_pessen_kp", "Kp_zn_pessen = 0.7*Ku_zn",
    {"Kp_zn_pessen": "1 | Pessen integral rule proportional gain", "Ku_zn": "1 | ultimate gain"},
    CTL, sk_, "ZN", "Tuning table, Pessen integral rule")
add("zn_some_overshoot_kp", "Kp_zn_so = 0.333*Ku_zn",
    {"Kp_zn_so": "1 | some-overshoot proportional gain", "Ku_zn": "1 | ultimate gain"},
    CTL, sk_, "ZN", "Tuning table, some overshoot")
add("zn_no_overshoot_td", "Td_zn_no = 0.333*Pu_zn",
    {"Td_zn_no": "second | no-overshoot derivative time", "Pu_zn": "second | ultimate period"},
    CTL, sk_, "ZN", "Tuning table, no overshoot")
add("pid_integral_gain_from_ti", "Ki_gain = Kp_gain/Ti_pid",
    {"Ki_gain": "1/second | integral gain", "Kp_gain": "1 | proportional gain", "Ti_pid": "second | integral time"},
    CTL, sk_, "PID", "Standard form")
add("pid_derivative_gain_from_td", "Kd_gain = Kp_gain*Td_pid",
    {"Kd_gain": "second | derivative gain", "Kp_gain": "1 | proportional gain", "Td_pid": "second | derivative time"},
    CTL, sk_, "PID", "Standard form")
add("pid_laplace_transfer_function", "L_pid_s = Kp_gain + Ki_gain/s_laplace + Kd_gain*s_laplace",
    {"L_pid_s": "1 | controller transfer function", "Kp_gain": "1 | proportional gain",
     "Ki_gain": "1/second | integral gain", "s_laplace": "1/second | complex frequency",
     "Kd_gain": "second | derivative gain"}, CTL, sk_, "PID", "Laplace transfer function")
add("q_from_damping_ratio", "Q_factor = 1/(2*zeta_damp)",
    {"Q_factor": "1 | quality factor", "zeta_damp": "1 | damping ratio"}, CTL, sk_, "DAMP", "Q factor and damping ratio")
add("zeta_from_log_decrement", "zeta_from_delta = delta_log/sqrt(delta_log**2 + (2*pi)**2)",
    {"zeta_from_delta": "1 | damping ratio", "delta_log": "1 | logarithmic decrement"},
    CTL, sk_, "DAMP", "Logarithmic decrement")
add("zeta_from_overshoot", "zeta_from_po = -log(PO_frac)/sqrt(pi**2 + log(PO_frac)**2)",
    {"zeta_from_po": "1 | damping ratio", "PO_frac": "1 | fractional overshoot (PO/100)"},
    CTL, sk_, "DAMP", "Percent overshoot", note="Page uses percent PO; written with PO_frac = PO/100.")
add("damping_loss_factor", "eta_loss = 2*zeta_damp*omega_freq/omega_n_sys",
    {"eta_loss": "1 | loss factor", "zeta_damp": "1 | damping ratio", "omega_freq": "1/second | frequency",
     "omega_n_sys": "1/second | natural frequency"}, CTL, sk_, "DAMP", "Loss factor")
add("half_life_decay", "t_half = log(2)/lam_decay",
    {"t_half": "second | half-life", "lam_decay": "1/second | decay rate"}, CTL, sk_, "DAMP", "Decay")
add("one_pole_step_response", "S_ol = A0_gain*(1 - exp(-t_time/tau_1))",
    {"S_ol": "1 | open-loop step response", "A0_gain": "1 | zero-frequency gain", "t_time": "second | time",
     "tau_1": "second | time constant"}, CTL, sk_, "STEP", "One-pole system")
add("one_pole_closed_loop_step_response",
    "S_fb = A0_gain/(1 + beta_fb*A0_gain)*(1 - exp(-t_time*(1 + beta_fb*A0_gain)/tau_1))",
    {"S_fb": "1 | closed-loop step response", "A0_gain": "1 | open-loop gain", "beta_fb": "1 | feedback factor",
     "t_time": "second | time", "tau_1": "second | time constant"}, CTL, sk_, "STEP", "One-pole system")
add("two_pole_settling_time", "t_settle = log(1/Delta_tol)/rho_damp",
    {"t_settle": "second | settling time", "Delta_tol": "1 | acceptable deviation", "rho_damp": "1/second | damping parameter"},
    CTL, sk_, "STEP", "Two-pole system")
add("two_pole_max_overshoot", "S_max_2p = 1 + exp(-pi*rho_damp/mu_osc)",
    {"S_max_2p": "1 | peak of step response", "rho_damp": "1/second | damping parameter",
     "mu_osc": "1/second | oscillation frequency parameter"}, CTL, sk_, "STEP", "Two-pole system")
add("phase_margin_two_pole", "phi_margin = atan(alpha_pole)",
    {"phi_margin": "1 | phase margin (rad)", "alpha_pole": "1 | pole ratio parameter"},
    CTL, sk_, "STEP", "Two-pole system")

# ------------------------------------------------------------------ electrical
se = "electrical"
add("terminal_voltage", "V_term = emf - I_cur*r_int",
    {"V_term": "volt | terminal voltage", "emf": "volt | source emf", "I_cur": "ampere | current",
     "r_int": "ohm | internal resistance"}, ELE, se, "OS10", "Terminal voltage")
add("series_resistance_two", "R_series2 = R1_res + R2_res",
    {"R_series2": "ohm | equivalent", "R1_res": "ohm | resistor 1", "R2_res": "ohm | resistor 2"},
    ELE, se, "OS10", "Resistors in series", form="rearranged", note="Page gives the N-resistor sum; two-resistor case.")
add("parallel_resistance_two", "R_par2 = 1/(1/R1_res + 1/R2_res)",
    {"R_par2": "ohm | equivalent", "R1_res": "ohm | resistor 1", "R2_res": "ohm | resistor 2"},
    ELE, se, "OS10", "Resistors in parallel", form="rearranged", note="Page gives the N-resistor form; two-resistor case.")
add("rc_charging_charge", "q_chg = C_cap*emf*(1 - exp(-t_time/(R_res*C_cap)))",
    {"q_chg": "coulomb | capacitor charge", "C_cap": "farad | capacitance", "emf": "volt | source emf",
     "t_time": "second | time", "R_res": "ohm | resistance"}, ELE, se, "OS10", "RC circuits")
add("rc_charging_current", "I_chg = emf/R_res*exp(-t_time/(R_res*C_cap))",
    {"I_chg": "ampere | charging current", "emf": "volt | source emf", "R_res": "ohm | resistance",
     "t_time": "second | time", "C_cap": "farad | capacitance"}, ELE, se, "OS10", "RC circuits")
add("rc_time_constant", "tau_rc = R_res*C_cap",
    {"tau_rc": "second | time constant", "R_res": "ohm | resistance", "C_cap": "farad | capacitance"},
    ELE, se, "OS10", "RC circuits")
add("parallel_plate_capacitor", "C_pp = eps0*A_plate/d_gap",
    {"C_pp": "farad | capacitance", "eps0": "farad/meter | permittivity of free space",
     "A_plate": "meter**2 | plate area", "d_gap": "meter | plate separation"}, ELE, se, "OS8", "Parallel-plate capacitor")
add("spherical_capacitor", "C_sph = 4*pi*eps0*R_in*R_out/(R_out - R_in)",
    {"C_sph": "farad | capacitance", "eps0": "farad/meter | permittivity of free space",
     "R_in": "meter | inner radius", "R_out": "meter | outer radius"}, ELE, se, "OS8", "Spherical capacitor")
add("cylindrical_capacitor", "C_cyl = 2*pi*eps0*l_cyl/log(R_out/R_in)",
    {"C_cyl": "farad | capacitance", "eps0": "farad/meter | permittivity of free space",
     "l_cyl": "meter | length", "R_out": "meter | outer radius", "R_in": "meter | inner radius"},
    ELE, se, "OS8", "Cylindrical capacitor")
add("series_capacitance_two", "C_series2 = 1/(1/C1_cap + 1/C2_cap)",
    {"C_series2": "farad | equivalent", "C1_cap": "farad | capacitor 1", "C2_cap": "farad | capacitor 2"},
    ELE, se, "OS8", "Series combination", form="rearranged", note="Page gives the N-capacitor form; two-capacitor case.")
add("capacitor_energy", "U_cap = C_cap*V_cap**2/2",
    {"U_cap": "joule | stored energy", "C_cap": "farad | capacitance", "V_cap": "volt | voltage"},
    ELE, se, "OS8", "Energy stored in a capacitor")
add("dielectric_capacitance", "C_diel = kappa_diel*C0_cap",
    {"C_diel": "farad | capacitance with dielectric", "kappa_diel": "1 | dielectric constant",
     "C0_cap": "farad | capacitance without dielectric"}, ELE, se, "OS8", "Capacitor with a dielectric")
add("conductor_resistance", "R_cond = rho_res*L_cond/A_cond",
    {"R_cond": "ohm | resistance", "rho_res": "ohm*meter | resistivity", "L_cond": "meter | length",
     "A_cond": "meter**2 | cross-section area"}, ELE, se, "OS9", "Resistance of a cylinder")
add("resistivity_temperature", "rho_T = rho0_res*(1 + alpha_T*(T_K - T0_K))",
    {"rho_T": "ohm*meter | resistivity at T", "rho0_res": "ohm*meter | reference resistivity",
     "alpha_T": "1/kelvin | temperature coefficient", "T_K": "kelvin | temperature", "T0_K": "kelvin | reference temperature"},
    ELE, se, "OS9", "Resistivity and temperature")
add("power_resistor_voltage_form", "P_res = V_R**2/R_res",
    {"P_res": "watt | power", "V_R": "volt | voltage across resistor", "R_res": "ohm | resistance"},
    ELE, se, "OS9", "Electrical power")
add("solenoid_inductance", "L_sol = mu0*N_turns**2*A_sol/l_sol",
    {"L_sol": "henry | self-inductance", "mu0": "henry/meter | permeability of free space",
     "N_turns": "1 | turns", "A_sol": "meter**2 | cross-section area", "l_sol": "meter | length"},
    ELE, se, "OS14", "Solenoid self-inductance")
add("toroid_inductance", "L_tor = mu0*N_turns**2*h_tor*log(R_out/R_in)/(2*pi)",
    {"L_tor": "henry | self-inductance", "mu0": "henry/meter | permeability of free space",
     "N_turns": "1 | turns", "h_tor": "meter | height", "R_out": "meter | outer radius", "R_in": "meter | inner radius"},
    ELE, se, "OS14", "Toroid self-inductance")
add("inductor_energy", "U_ind = L_ind*I_cur**2/2",
    {"U_ind": "joule | stored energy", "L_ind": "henry | inductance", "I_cur": "ampere | current"},
    ELE, se, "OS14", "Energy stored in an inductor")
add("rl_current_rise", "I_rl = emf/R_res*(1 - exp(-t_time/tau_rl))",
    {"I_rl": "ampere | current", "emf": "volt | source emf", "R_res": "ohm | resistance",
     "t_time": "second | time", "tau_rl": "second | time constant"}, ELE, se, "OS14", "RL circuits")
add("rl_time_constant", "tau_rl = L_ind/R_res",
    {"tau_rl": "second | time constant", "L_ind": "henry | inductance", "R_res": "ohm | resistance"},
    ELE, se, "OS14", "RL circuits")
add("lc_angular_frequency", "omega_lc = 1/sqrt(L_ind*C_cap)",
    {"omega_lc": "1/second | angular frequency", "L_ind": "henry | inductance", "C_cap": "farad | capacitance"},
    ELE, se, "OS14", "LC oscillations")
add("rlc_damped_frequency", "omega_rlc = sqrt(1/(L_ind*C_cap) - (R_res/(2*L_ind))**2)",
    {"omega_rlc": "1/second | damped angular frequency", "L_ind": "henry | inductance", "C_cap": "farad | capacitance",
     "R_res": "ohm | resistance"}, ELE, se, "OS14", "RLC oscillations")
add("capacitive_reactance", "Xc_react = 1/(omega_ac*C_cap)",
    {"Xc_react": "ohm | capacitive reactance", "omega_ac": "1/second | angular frequency",
     "C_cap": "farad | capacitance"}, ELE, se, "OS15", "Capacitor reactance")
add("inductive_reactance", "Xl_react = omega_ac*L_ind",
    {"Xl_react": "ohm | inductive reactance", "omega_ac": "1/second | angular frequency",
     "L_ind": "henry | inductance"}, ELE, se, "OS15", "Inductor reactance")
add("series_rlc_impedance", "Z_rlc = sqrt(R_res**2 + (Xl_react - Xc_react)**2)",
    {"Z_rlc": "ohm | impedance", "R_res": "ohm | resistance", "Xl_react": "ohm | inductive reactance",
     "Xc_react": "ohm | capacitive reactance"}, ELE, se, "OS15", "Series RLC")
add("series_rlc_phase", "phi_rlc = atan((Xl_react - Xc_react)/R_res)",
    {"phi_rlc": "1 | phase angle (rad)", "Xl_react": "ohm | inductive reactance",
     "Xc_react": "ohm | capacitive reactance", "R_res": "ohm | resistance"}, ELE, se, "OS15", "Series RLC")
add("rlc_quality_factor", "Q_rlc = omega0_res*L_ind/R_res",
    {"Q_rlc": "1 | quality factor", "omega0_res": "1/second | resonant angular frequency",
     "L_ind": "henry | inductance", "R_res": "ohm | resistance"}, ELE, se, "OS15", "Resonance")
add("transformer_secondary_voltage", "Vs_tr = Vp_tr*Ns_tr/Np_tr",
    {"Vs_tr": "volt | secondary voltage", "Vp_tr": "volt | primary voltage", "Ns_tr": "1 | secondary turns",
     "Np_tr": "1 | primary turns"}, ELE, se, "OS15", "Transformers", form="rearranged",
    note="Page gives Vs/Vp = Ns/Np.")


# ------------------------------------------------------------------ validation
UNIT_NS = {n: getattr(U, n) for n in
           ("newton", "pascal", "meter", "second", "kilogram", "joule", "watt", "volt", "ampere",
            "ohm", "farad", "henry", "coulomb", "kelvin")}
DS = SI.get_dimension_system()


def unit_of(spec):
    if spec.strip() == "1":
        return sp.Integer(1)
    return eval(spec, {"__builtins__": {}}, UNIT_NS)  # fixed namespace, our own strings


def dims(expr):
    d = SI._collect_factor_and_dimension(expr)[1]
    return DS.get_dimensional_dependencies(d, mark_dimensionless=False)


def check_dimensions(lhs, rhs, unit_map):
    # Each symbol becomes (its own positive scale) x (its unit). The scale keeps
    # sympy from cancelling things like r_out**4 - r_in**4 to zero when both
    # carry the same unit, which would hide real dimension errors.
    sub = {s: sp.Dummy(str(s), positive=True) * unit_map[str(s)]
           for s in (lhs.free_symbols | rhs.free_symbols)}
    for fn in rhs.atoms(sp.Function):  # exp/log/trig arguments must be dimensionless
        for a in fn.args:
            if dims(a.subs(sub)) != {}:
                return False, f"argument of {fn.func.__name__} is not dimensionless"
    try:
        dl, dr = dims(lhs.subs(sub)), dims(rhs.subs(sub))
    except ValueError as e:
        return False, f"cannot add/compare unlike dimensions: {e}"
    if dl != dr:
        return False, f"left side is {dl or 'dimensionless'} but right side is {dr or 'dimensionless'}"
    return True, ""


def skeleton(e):
    if e.is_Symbol:
        return "v"
    if e.is_Number or e is sp.pi:
        return str(e)
    if e.is_Pow:
        return f"({skeleton(e.args[0])})^{e.args[1]}"
    args = sorted(skeleton(a) for a in e.args) if (e.is_Mul or e.is_Add) else [skeleton(a) for a in e.args]
    return f"{type(e).__name__}[{','.join(args)}]"


ENGINE_SKEL = {}
for n, eq in ENGINE.items():
    ENGINE_SKEL.setdefault(skeleton(eq.rhs), []).append(n)
ENGINE_NAMES = set(ENGINE)

good, rejected, duplicates = [], [], []
seen_ids = set()
for e in ENTRIES:
    problems = []
    if e["id"] in seen_ids:
        problems.append("duplicate id inside this batch")
    seen_ids.add(e["id"])
    unit_map, meaning = {}, {}
    for sym, spec in e["syms"].items():
        u_, m_ = [x.strip() for x in spec.split("|", 1)]
        unit_map[sym] = unit_of(u_)
        meaning[sym] = {"unit": u_, "meaning": m_}
    loc = {s: sp.Symbol(s) for s in e["syms"]}
    lhs_txt, rhs_txt = [x.strip() for x in e["eq"].split("=", 1)]
    try:
        lhs, rhs = sp.sympify(lhs_txt, locals=loc), sp.sympify(rhs_txt, locals=loc)
        if not lhs.is_Symbol:
            problems.append("left side is not a single symbol")
        undeclared = {str(s) for s in (lhs.free_symbols | rhs.free_symbols)} - set(e["syms"])
        unused = set(e["syms"]) - {str(s) for s in (lhs.free_symbols | rhs.free_symbols)}
        if undeclared:
            problems.append(f"symbols without units: {sorted(undeclared)}")
        if unused:
            problems.append(f"declared but unused symbols: {sorted(unused)}")
    except Exception as ex:  # noqa: BLE001
        problems.append(f"does not parse: {ex}")
        lhs = rhs = None
    dim_ok, dim_msg = (False, "")
    if lhs is not None and not problems:
        dim_ok, dim_msg = check_dimensions(lhs, rhs, unit_map)
        if not dim_ok:
            problems.append("dimension check: " + dim_msg)
    dup = []
    if rhs is not None:
        if e["id"] in ENGINE_NAMES:
            dup.append(f"same name as engine formula '{e['id']}'")
        if rhs.count_ops() >= 4:
            dup += [f"same shape as engine '{n}'" for n in ENGINE_SKEL.get(skeleton(rhs), [])]
    title, url, lic = SOURCES[e["src"]]
    rec = {
        "id": e["id"], "equation": e["eq"], "discipline": e["disc"], "physics_domain": e["domain"],
        "symbols": meaning,
        "source": {"title": title, "url": url, "section": e["section"], "license": lic, "accessed": ACCESSED},
        "form_vs_source": e["form"], "note": e["note"],
        "checks": {"parses": lhs is not None and not any("parse" in p for p in problems),
                   "dimensions": dim_ok, "possible_duplicates": dup},
        "status": "needs_review" if e["hold"] else "candidate",
    }
    if e["hold"]:
        rec["review_reason"] = e["hold"]
    if problems:
        rec["rejected_because"] = problems
        rejected.append(rec)
    elif dup:
        duplicates.append(rec)
    else:
        good.append(rec)

with open(os.path.join(HERE, "pilot_100.json"), "w") as f:
    json.dump(good, f, indent=2, ensure_ascii=False)
with open(os.path.join(HERE, "rejected.json"), "w") as f:
    json.dump(rejected, f, indent=2, ensure_ascii=False)
with open(os.path.join(HERE, "already_in_engine.json"), "w") as f:
    json.dump(duplicates, f, indent=2, ensure_ascii=False)
with open(os.path.join(HERE, "pilot_100.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "discipline", "physics_domain", "equation", "source_title", "source_url", "section",
                "form_vs_source", "possible_duplicates", "status"])
    for r in good:
        w.writerow([r["id"], r["discipline"], r["physics_domain"], r["equation"], r["source"]["title"],
                    r["source"]["url"], r["source"]["section"], r["form_vs_source"],
                    "; ".join(r["checks"]["possible_duplicates"]), r["status"]])

from collections import Counter  # noqa: E402
print(f"entries {len(ENTRIES)}  accepted {len(good)}  rejected {len(rejected)}  already in engine {len(duplicates)}")
print(Counter(r["discipline"] for r in good))
for r in rejected:
    print("REJECTED", r["id"], "->", r["rejected_because"])
for r in duplicates:
    print("ALREADY IN ENGINE", r["id"], r["checks"]["possible_duplicates"])
