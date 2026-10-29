"""
Extract every formula from formulas.py and export as individual JSON files
organized by domain under faulter-formula-brain/warehouse/.

Each formula gets its own file: warehouse/<domain>/<formula_name>.json

Structure of each JSON file:
{
  "name": "ohms_law",
  "equation": "V = I*R",
  "lhs": "V",
  "rhs_free_symbols": ["I", "R"],
  "domain": "electrical",
  "variables": {
    "V": {"symbol": "V", "description": "voltage"},
    "I": {"symbol": "I", "description": "current"},
    "R": {"symbol": "R", "description": "resistance"}
  }
}
"""
import json
import sys
import sympy as sp
import re
import os

sys_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys_path)
from formulas import FORMULAS, FORMULA_DOMAINS

WAREHOUSE = os.path.join(sys_path, "warehouse")

# Build a mapping from symbol name -> symbol object (inverted lookup)
all_syms = {}
for module in [sp.core.basic, sp.core.numbers]:
    for name, obj in vars(module).items():
        if isinstance(obj, sp.Symbol):
            all_syms[name] = obj

# Also scan FORMULAS dict to collect all symbols
def collect_symbols(equation):
    """Collect all sympy Symbol names from an equation (lhs + rhs)."""
    symbols = set()
    if isinstance(equation, sp.Eq):
        for side in [equation.lhs, equation.rhs]:
            symbols.update(s.name for s in side.free_symbols)
    return symbols


# Map simple names -> descriptions based on common engineering knowledge
SYMBOL_DESCRIPTIONS = {
    "V": "voltage", "I": "current", "R": "resistance", "E": "back emf",
    "Kt": "torque constant", "Ke": "back emf constant", "T": "torque",
    "P": "power", "P_out": "output power", "P_in": "input power",
    "omega": "angular velocity", "Q": "heat/flow", "eta": "efficiency",
    "mu": "friction coefficient", "F": "force", "r": "radius",
    "Tf": "friction torque", "Pf": "friction power",
    "mu0": "permeability of free space", "N": "number/turns",
    "L": "length/inductance", "B": "magnetic field", "A": "area",
    "Rm": "reluctance", "RPM": "revolutions per minute",
    "N_segments": "commutation segments", "f": "frequency",
    "l_cond": "conductor length", "Phi": "magnetic flux",
    "Vol": "volume", "m": "mass", "rho": "density",
    "J": "moment of inertia", "KE": "kinetic energy",
    "d": "diameter", "J_polar": "polar moment of inertia",
    "tau": "shear stress", "C": "bearing load rating",
    "p_life": "bearing life exponent", "L10": "L10 bearing life",
    "n_poles": "number of poles", "Z_cond": "total conductors",
    "a_path": "parallel paths", "sigma_tan": "tangential stress",
    "D_rotor": "rotor diameter", "L_rotor": "rotor active length",
    "D_comm": "commutator diameter", "v_comm": "commutator velocity",
    "J_brush": "brush current density", "A_brush": "brush area",
    "B_max": "max flux density", "t_yoke": "yoke thickness",
    "R0": "initial resistance", "alpha_temp": "thermal coefficient",
    "T_temp": "temperature", "T0_temp": "reference temperature",
    "Phi0": "initial flux", "k_demag": "demagnetization factor",
    "T_max_demag": "max demag temperature",
    "T_amb": "ambient temperature", "t_time": "time",
    "tau_thermal": "thermal time constant", "T_final": "final temp",
    "X0": "initial value", "s_sev": "severity", "k_growth": "growth rate",
    "T_nom": "nominal torque", "k_unbal": "imbalance factor",
    "omega_t": "ripple frequency", "t_ripple": "ripple time",
    "T_ripple": "ripple torque",
    "I_total": "total current", "I_cpu": "CPU current",
    "I_wifi": "WiFi current", "I_gpio": "GPIO current",
    "I_peripherals": "peripheral current",
    "V_out": "output voltage", "V_in": "input voltage",
    "R_regulator": "regulator resistance", "C_battery": "battery capacity",
    "t_batt": "battery life", "T_chip": "chip temperature",
    "R_th": "thermal resistance", "dT_dt": "temperature rise rate",
    "Cp": "specific heat",
    "c_light": "speed of light", "f_rf": "RF frequency",
    "L_ant": "antenna length", "dist_rf": "distance/Range",
    "PL": "path loss", "G_tx": "TX antenna gain",
    "G_rx": "RX antenna gain", "P_tx": "TX power",
    "P_rx": "RX power", "lambda": "wavelength",
    "T_clk": "clock period", "f_crystal": "crystal frequency",
    "f_cpu": "CPU frequency", "cycles": "cycles",
    "cycles_per_inst": "cycles per instruction", "t_inst": "instruction time",
    "V_high": "high logic voltage", "V_low": "low logic voltage",
    "R_load": "load resistance", "I_max": "max drive current",
    "V_dd": "supply voltage", "R_output_impedance": "output impedance",
    "I_pull": "pull resistor current", "R_pull": "pull resistor value",
    "N_s": "synchronous speed", "N_r": "rotor speed",
    "s_slip": "slip", "f_ac": "AC frequency", "f_r": "rotor frequency",
    "E2": "rotor EMF", "E2s": "rotor EMF running",
    "X2": "rotor reactance", "X2s": "rotor reactance running",
    "R2": "rotor resistance", "I2": "rotor current",
    "R1": "stator resistance", "X1": "stator reactance",
    "V1": "stator voltage", "omega_s": "synchronous angular speed",
    "I1": "stator current",
    "T_im": "induction motor torque", "s_maxT": "max torque slip",
    "T_max_im": "breakdown torque", "T_start_im": "starting torque",
    "P_ag": "air gap power", "P_rcl": "rotor copper loss",
    "P_dev": "developed mechanical power", "P_fw_im": "friction windage",
    "P_scl": "stator copper loss",
    "P_in_3ph_im": "3-phase input power", "V_L": "line voltage",
    "I_L": "line current", "pf_im": "power factor",
    "eta_im": "motor efficiency", "P_out_im": "output power",
    "Co_im": "output coefficient", "D_im": "motor diameter",
    "L_im": "motor length", "B_av_im": "avg flux density",
    "Phi_im": "flux per pole", "S_slots_im": "number of slots",
    "g_im": "air gap length", "T_ph_im": "turns per phase",
    "E1": "phase EMF", "k_w_im": "winding factor",
    "lambda_slot_im": "slot pitch", "J_cond_im": "current density",
    "A_cond_im": "conductor area", "I_ph": "phase current",
    "ac_im": "specific electric loading", "m_phases_im": "number of phases",
    "K_trans": "turns ratio", "N1_t": "primary turns", "N2_t": "secondary turns",
    "V1_t": "primary voltage", "V2_t": "secondary voltage",
    "I1_t": "primary current", "I2_t": "secondary current",
    "E_t": "EMF", "Phi_max_t": "max flux",
    "VR_t": "voltage regulation", "R01_t": "equivalent resistance",
    "X01_t": "equivalent reactance", "P_cu_t": "copper loss",
    "P_i_t": "iron loss", "eta_t": "efficiency",
    "P_out_t": "output power", "P_in_t": "input power",
    "E_sync": "synchronous EMF", "Xs_sync": "synchronous reactance",
    "delta_sync": "torque angle", "P_sync": "synch power",
    "V_sync": "synchronous voltage", "Ia_sync": "armature current",
    "Ra_sync": "armature resistance", "Pmax_sync": "max synchronous power",
    "V_ph3": "phase voltage", "V_L3": "line voltage",
    "I_ph3": "phase current", "I_L3": "line current",
    "P_3ph": "3-phase power", "Q_3ph": "reactive power",
    "S_3ph": "apparent power", "pf_3ph": "power factor",
    "Qc_pfc": "power factor correction cap",
    "V_L3": "line voltage 3ph", "I_L3": "line current 3ph",
    "P_3ph": "3-phase power", "Q_3ph": "reactive power", "S_3ph": "apparent power",
    "pf_3ph": "power factor", "Qc_pfc": "PFC capacitor reactive power",
    "P_hyd": "hydraulic pressure", "Q_hyd": "flow rate",
    "A_hyd": "hydraulic area", "v_hyd": "fluid velocity", "F_hyd": "force",
    "rho_hyd": "fluid density", "g_grav": "gravity", "h_hyd": "head/height",
    "Re_hyd": "Reynolds number", "mu_visc": "viscosity",
    "f_darcy": "Darcy friction factor", "L_pipe": "pipe length",
    "D_pipe": "pipe diameter", "hl_major": "major head loss",
    "K_minor": "minor loss coefficient", "hl_minor": "minor head loss",
    "Q_pump": "pump flow rate", "N_pump": "pump speed",
    "D_disp": "displacement", "eta_vol": "volumetric efficiency",
    "eta_mech_hyd": "mechanical efficiency", "eta_overall_hyd": "overall efficiency",
    "P_hyd_power": "hydraulic power", "T_pump": "pump torque",
    "Cv_valve": "flow coefficient", "dP_valve": "valve pressure drop",
    "F_cyl": "cylinder force", "v_cyl": "cylinder speed",
    "Q_cyl": "cylinder flow", "A_cyl": "cylinder area",
    "P_acc": "accumulator pressure", "V_acc": "accumulator volume",
    "P0_acc": "pre-charge pressure", "V0_acc": "pre-charge volume",
    "m_gear": "gear module", "Np_gear": "pinion teeth",
    "Ng_gear": "gear teeth", "Dp_gear": "pinion diameter",
    "Dg_gear": "gear diameter", "CD_gear": "center distance",
    "GR_gear": "gear ratio", "Wt_gear": "tangential load",
    "sigma_lewis": "Lewis bending stress", "Y_lewis": "Lewis factor",
    "Fw_gear": "face width", "v_pitch_gear": "pitch line velocity",
    "Kv_dynamic": "dynamic factor", "Ks_service": "service factor",
    "sigma_agma": "AGMA bending stress", "J_agma": "geometry factor",
    "k_spring": "spring rate", "G_spring": "shear modulus",
    "d_wire": "wire diameter", "D_coil": "coil diameter",
    "Na_spring": "active coils", "Ws_wahl": "Wahl factor",
    "C_spring": "spring index", "tau_spring": "spring shear stress",
    "T_belt": "tight belt tension", "T_slack": "slack belt tension",
    "theta_wrap": "wrap angle", "mu_belt": "belt friction",
    "P_belt": "belt power", "v_belt": "belt velocity",
    "p_chain": "chain pitch", "N1_sprocket": "drive teeth",
    "N2_sprocket": "driven teeth", "v_chain": "chain velocity",
    "CR_chain": "chain ratio",
    "Av_opamp": "opamp gain", "Rf_opamp": "feedback resistor",
    "Rin_opamp": "input resistor", "GBW_opamp": "gain-bandwidth product",
    "SR_opamp": "slew rate", "fc_rc": "cutoff frequency",
    "R_filt": "filter resistor", "C_filt": "filter capacitor",
    "Id_diode": "diode current", "Is_diode": "saturation current",
    "Vd_diode": "diode voltage", "Vt_thermal": "thermal voltage",
    "n_ideality": "ideality factor", "beta_bjt": "BJT gain",
    "Ic_bjt": "collector current", "Ib_bjt": "base current",
    "Ie_bjt": "emitter current", "gm_mosfet": "MOSFET transconductance",
    "Vgs_mosfet": "gate-source voltage", "Vth_mosfet": "threshold voltage",
    "Id_mosfet": "drain current", "k_mosfet": "MOSFET parameter",
    "Vr_ripple": "ripple voltage", "C_filt_cap": "filter capacitor",
    "I_load": "load current", "f_ripple": "ripple frequency",
    "D_duty": "duty cycle", "Vout_buck": "buck output", "Vin_buck": "buck input",
    "Vout_boost": "boost output",
    "F_ar": "armature reaction MMF", "F_cm": "compensating MMF",
    "F_ip": "interpole MMF", "N_eq_cur": "equalizer current",
    "Ia_big": "large motor armature", "Z_big": "large motor conductors",
    "E_series": "series motor EMF", "E_shunt": "shunt motor EMF",
    "SpeedReg_dc": "speed regulation",
    "omega_n": "natural frequency", "k_stiff": "stiffness",
    "m_sys": "system mass", "zeta_damp": "damping ratio", "c_damp": "damping coeff",
    "sigma_a": "alternating stress", "sigma_m": "mean stress",
    "Se_endurance": "endurance limit", "Sut_ultimate": "ultimate strength",
    "n_safety": "safety factor", "h_conv": "convection coefficient",
    "Nu_nusselt": "Nusselt number", "k_thermal_cond": "thermal conductivity",
    "Lc_char": "characteristic length", "Bi_biot": "Biot number",
    "Kp_pid": "PID proportional", "Ki_pid": "PID integral",
    "Kd_pid": "PID derivative", "e_err": "error", "u_pid": "PID output",
    "ess_error": "steady state error", "zeta_2nd": "2nd order damping",
    "omega_n_2nd": "2nd order natural freq", "Mp_overshoot": "overshoot",
    "ts_settling": "settling time",
    "V0_test_im": "no-load test voltage", "I0_test_im": "no-load current",
    "P0_test_im": "no-load power", "pf0_im": "no-load power factor",
    "Vsc_test_im": "short-circuit voltage", "Isc_test_im": "short-circuit current",
    "Psc_test_im": "short-circuit power", "Z01_im": "blocked rotor impedance",
    "s_fl_im": "full-load slip", "N_synch_fl": "synch full-load speed",
    "N_fl_im": "full-load speed", "class_temp_rise_im": "temp rise class",
    "eta_partial_im": "partial load efficiency", "load_frac_im": "load fraction",
    "R2_deep": "deep bar resistance", "R2_ac_im": "AC resistance",
    "k_deepbar_im": "deep bar ratio",
    "sigma_bend": "bending stress", "M_bend": "bending moment",
    "c_dist": "distance from neutral", "I_area": "area moment",
    "Z_section": "section modulus", "delta_beam": "beam deflection",
    "F_beam": "beam force", "Lspan_beam": "beam span",
    "E_mod": "Young's modulus", "P_euler": "Euler buckling load",
    "Le_col": "column effective length", "k_gyr": "radius of gyration",
    "sigma_principal": "principal stress", "sigma_x": "x normal stress",
    "sigma_y": "y normal stress", "tau_xy": "shear stress xy",
    "sigma_vm": "von Mises stress", "Kt_stress": "stress concentration factor",
    "epsilon_strain": "strain", "nu_poisson": "Poisson ratio",
    "alpha_therm": "thermal expansion coeff", "dL_therm": "thermal expansion",
    "T0_therm": "reference temp",
    "delta_shaft": "shaft deflection", "N_crit_shaft": "critical speed",
    "sigma_a_shaft": "alternating shaft stress", "tau_m_shaft": "mean shaft stress",
    "Kf_shaft": "fatigue factor", "tau_key": "key shear stress",
    "F_key": "key force", "A_key": "key area",
    "NPSH_avail": "NPSH available", "h_atm": "atmospheric head",
    "h_vap": "vapor head", "h_suction": "suction head",
    "h_fric_suction": "suction friction loss",
    "Ca_cav": "cavitation number", "P_dp_shock": "pressure wave/drop shock",
    "K_bulk": "bulk modulus", "a_wave": "wave speed",
    "Q_orifice": "orifice flow", "Cd_orifice": "orifice discharge coeff",
    "A_orifice": "orifice area",
    "N_ss_pump": "specific speed", "Q_aff": "affinity flow", "N_aff": "affinity speed",
    "H_aff": "affinity head", "v_torricelli": "Torricelli velocity",
    "h_torricelli": "Torricelli head", "P_manometer": "manometer pressure",
    "rho_manometer": "manometer density", "h_manometer": "manometer height",
    "F_buoy": "buoyancy force", "rho_fluid_b": "fluid density for buoyancy",
    "Vol_disp": "displaced volume", "P_depth": "hydrostatic pressure",
    "Vb_bridge": "bridge voltage", "R1_bridge": "bridge resistor 1",
    "R2_bridge": "bridge resistor 2", "R3_bridge": "bridge resistor 3",
    "R4_bridge": "bridge resistor 4",
    "Vdiv_out": "divider output", "Vdiv_in": "divider input",
    "R1_div": "divider resistor 1", "R2_div": "divider resistor 2",
    "f_555": "555 timer frequency", "R_555a": "555 resistor A",
    "R_555b": "555 resistor B", "C_555": "555 capacitor",
    "Av_instr": "instrumentation amp gain", "Rg_instr": "gain resistor",
    "Vz_zener": "Zener voltage", "Iz_zener": "Zener current",
    "Rz_zener": "Zener resistor",
    "eta_classA": "class A efficiency", "eta_classB": "class B efficiency",
    "t_pd_gate": "gate propagation delay", "C_load_gate": "gate load cap",
    "V_swing_gate": "gate voltage swing", "f_clk_digital": "digital clock freq",
    "T_clk_digital": "digital clock period",
    "P_dyn_cmos": "CMOS dynamic power", "C_load_cmos": "CMOS load",
    "f_sw_cmos": "CMOS switching freq", "V_dd_cmos": "CMOS supply",
    "q_fourier": "heat conduction rate", "k_cond": "conduction conductivity",
    "dT_dx": "temp gradient", "A_cond_area": "conduction area",
    "q_rad": "radiation heat", "eps_rad": "emissivity",
    "sigma_sb": "Stefan-Boltzmann const", "T_hot_rad": "hot radiation temp",
    "T_cold_rad": "cold radiation temp",
    "R_th_series": "series thermal resistance", "R_th_parallel": "parallel thermal resistance",
    "LMTD_hx": "LMTD", "dT1_hx": "temp diff 1", "dT2_hx": "temp diff 2",
    "Gm_margin": "gain margin", "Pm_margin": "phase margin",
    "G_ol": "open loop gain", "H_fb": "feedback transfer",
    "T_cl": "closed loop transfer", "K_dc_gain": "DC gain",
    "K_auto_save": "autotransformer saving factor", "VA_auto": "autotransformer VA",
    "Z_pu": "per-unit impedance", "Z_base": "base impedance",
    "V_base": "base voltage", "S_base": "base power",
    "VR_sync_pct": "voltage reg pct", "SCR_sync": "short circuit ratio",
    "C_peukert": "Peukert capacity", "I_peukert": "Peukert current",
    "k_peukert": "Peukert exponent", "t_peukert": "Peukert time",
    "V_sag": "voltage sag", "R_int_batt": "battery internal resistance",
    "I_batt": "battery current", "C_derated": "derated capacity",
    "T_batt_amb": "battery ambient temp", "alpha_batt": "battery temp coeff",
    "SoC_batt": "state of charge", "Q_used": "charge used", "Q_rated": "rated capacity",
    "C_rate_batt": "C-rate", "I_rate_batt": "rate current",
    "E_batt_wh": "battery energy (Wh)", "V_nom_batt": "nominal voltage",
    "C_ah_batt": "capacity (Ah)", "E_specific_batt": "specific energy", "m_batt": "battery mass",
    "N_cycles_batt": "cycle life", "DoD_batt": "depth of discharge", "k_cycle": "cycle factor",
    "D_miner": "Miner's damage", "n_cycles_i": "cycles at load i", "N_cycles_i": "life at load i",
    "Sf_life": "fatigue strength life", "a_sn": "S-N curve a", "b_sn": "S-N curve b",
    "Nf_life": "fatigue life", "ka_surf": "surface factor", "kb_size": "size factor",
    "Se_corrected": "corrected endurance",
    "X_forced": "forced vibration amplitude", "F0_forced": "forcing amplitude",
    "r_freq_ratio": "frequency ratio", "TR_transmis": "transmissibility",
    "delta_log": "log decrement", "x1_log": "first amplitude", "x2_log": "second amplitude",
    "c_crit_damp": "critical damping coeff",
    "P_1ph": "single-phase real power", "Q_1ph": "single-phase reactive",
    "S_1ph": "single-phase apparent", "V_1ph": "single-phase voltage",
    "I_1ph": "single-phase current", "pf_1ph": "single-phase PF",
    "V_rms_sine": "RMS voltage", "V_peak_sine": "peak voltage",
    "V_pp_sine": "peak-to-peak voltage", "CF_crest": "crest factor",
    "I_oh_fanout": "output high fanout current", "I_ih_fanout": "input high fanout current",
    "N_fanout": "fanout", "V_oh_nm": "output high voltage",
    "V_ol_nm": "output low voltage", "V_ih_nm": "input high voltage",
    "V_il_nm": "input low voltage",
    "NM_high": "noise margin high", "NM_low": "noise margin low",
    "t_setup": "setup time", "t_hold": "hold time", "t_clk_to_q": "clk-to-Q delay",
    "k_rate": "reaction rate", "A_arrhenius": "Arrhenius pre-factor",
    "Ea_arrhenius": "activation energy", "R_gas": "gas constant",
    "T_kelvin": "temperature (K)",
    "sigma_1_transform": "principal stress 1", "sigma_2_transform": "principal stress 2",
    "theta_transform": "principal stress angle",
    "Vout_flyback": "flyback output", "Vin_flyback": "flyback input",
    "N_flyback": "flyback turns", "D_flyback": "flyback duty",
    "VSWR_rf": "VSWR", "Gamma_refl": "reflection coeff",
    "Z0_rf": "characteristic impedance", "ZL_rf": "load impedance",
    "RL_db": "return loss dB", "Z_qw": "quarter-wave impedance",
    "Ku_zn": "ultimate gain", "Pu_zn": "ultimate period",
    "Kp_zn": "Z-N P", "Ti_zn": "Z-N I", "Td_zn": "Z-N D",
    "eps_hx": "heat exchanger effectiveness", "Cmin_hx": "min heat capacity",
    "Cmax_hx": "max heat capacity", "Qmax_hx": "max heat transfer",
    "Qactual_hx": "actual heat transfer", "NTU_hx": "NTU", "UA_hx": "UA product",
    "P_pump_hyd": "pumping power", "gamma_sg": "specific gravity",
    "X_unbalance": "unbalance response", "me_unbalance": "mass-eccentricity prod",
    "M_total_unbalance": "total rotating mass",
    "M_conc": "concrete moment", "As_conc": "steel area", "fy_conc": "steel yield",
    "d_conc": "effective depth", "a_conc": "stress block depth",
    "fc_conc": "concrete compressive", "b_conc": "beam width", "rho_conc": "reinforcement ratio",
    "Pa_rankine": "active earth pressure", "ka_rankine": "active pressure coeff",
    "gamma_soil": "soil unit weight", "H_wall": "wall height", "phi_soil": "soil friction",
    "sigma_allow_col": "allowable column stress", "F_axial_col": "axial column force",
    "A_col": "column area", "w_udl": "UDL load", "L_beam": "beam length",
    "M_max_udl": "max moment UDL", "V_max_udl": "max shear UDL",
    "delta_udl": "deflection UDL",
    "tau_weld": "weld shear stress", "F_weld": "weld force",
    "L_weld": "weld length", "throat_weld": "weld throat", "t_weld": "weld thickness",
    "sigma_butt": "butt weld stress", "F_butt": "butt weld force",
    "t_butt": "butt plate thickness", "L_butt": "butt length",
    "tau_rivet": "rivet shear stress", "F_rivet": "rivet force",
    "d_rivet": "rivet diameter", "n_rivets": "number of rivets",
    "C_bolt": "joint stiffness ratio", "k_bolt": "bolt stiffness",
    "k_member": "member stiffness", "F_ext_bolt": "external bolt load",
    "F_bolt_preload": "bolt preload", "F_bolt_total": "total bolt load",
    "P_equiv_bear": "equivalent bearing load", "X_radial": "radial factor",
    "Y_thrust": "thrust factor", "Fr_bear": "radial bearing load",
    "Fa_bear": "axial bearing load",
    "T_clutch": "clutch torque", "mu_clutch": "clutch friction",
    "F_axial_clutch": "clutch axial force", "R_mean_clutch": "clutch mean radius",
    "n_surfaces": "clutch friction surfaces",
    "T_brake": "brake torque", "mu_brake": "brake friction",
    "F_brake": "brake force", "R_brake": "brake radius",
    "F1_band": "band brake tight side", "F2_band": "band brake slack side",
    "mu_band": "band friction", "theta_band_wrap": "band wrap angle",
    "T_band": "band brake torque",
    "E_fly": "flywheel energy", "J_fly": "flywheel inertia",
    "omega1_fly": "flywheel omega 1", "omega2_fly": "flywheel omega 2",
    "Cs_fly": "fluctuation coeff", "omega_mean_fly": "mean flywheel omega",
    "y_cam": "cam displacement", "h_cam": "cam lift", "theta_cam": "cam angle",
    "beta_cam": "cam action angle", "v_cam": "cam velocity",
    "sigma_hoop": "hoop stress", "P_internal": "internal pressure",
    "D_vessel": "vessel diameter", "t_vessel": "vessel thickness",
    "sigma_long": "longitudinal stress", "sigma_sphere": "sphere stress",
    "G_gibbs": "Gibbs free energy", "H_enthalpy": "enthalpy", "S_entropy": "entropy",
    "dH_rxn": "change enthalpy", "dU_rxn": "change internal energy",
    "P_chem": "pressure chemical", "dV_rxn": "change volume",
    "Ca_conc": "concentration A", "Ca0_conc": "initial A conc", "t_rxn": "reaction time",
    "N_flux": "diffusion flux", "D_diff": "diffusion coeff", "dC_dx": "conc gradient",
    "U_overall_hx": "overall heat transfer", "h1_hx": "film coeff 1",
    "h2_hx": "film coeff 2", "Rf_fouling": "fouling factor",
    "alpha_volatility": "relative volatility", "y_vap": "vapor fraction",
    "x_liq": "liquid fraction",
    "W_compressor": "compressor work", "n_moles_gas": "moles of gas",
    "R_gas_const": "gas constant", "T1_gas": "inlet temp",
    "P1_gas": "inlet pressure", "P2_gas": "outlet pressure", "gamma_gas": "heat capacity ratio",
    "CR_corrosion": "corrosion rate", "mpy_const": "mpy conversion const",
    "W_loss_corr": "weight loss corrosion", "rho_corr": "corrosion density",
    "A_corr": "corrosion area", "t_corr": "time corrosion",
    "P_ideal": "ideal gas pressure", "n_ideal": "moles", "R_ideal": "gas constant",
    "T_ideal": "temp", "V_ideal": "volume",
    "Q_dot_hx": "heat rate", "m_dot_hx": "mass flow rate",
    "cp_hx": "specific heat", "dT_hx": "temp delta",
    "L_lift": "lift force", "Cl_lift": "lift coefficient",
    "S_wing": "wing area", "rho_air": "air density", "V_air": "air velocity",
    "D_drag": "drag force", "Cd_drag": "drag coefficient",
    "T_thrust_jet": "thrust", "m_dot_air": "air mass flow",
    "Ve_exhaust": "exhaust velocity", "V0_inlet": "inlet velocity",
    "R_range_breguet": "Breguet range", "V_cruise": "cruise speed",
    "L_D_ratio": "lift to drag ratio",
    "sfc_engine": "specific fuel consumption",
    "W1_fuel": "initial weight", "W2_fuel": "final weight",
    "V_stall": "stall speed", "W_aircraft": "aircraft weight", "Cl_max": "max lift coeff",
    "COP_refrig": "COP refrigeration", "Qc_refrig": "cooling capacity",
    "Wc_refrig": "compressor work", "COP_heatpump": "heat pump COP",
    "Qh_heatpump": "heat pump output",
    "Q_cooling_load": "cooling load", "m_dot_air_hvac": "air mass flow",
    "cp_air_hvac": "air specific heat", "dT_hvac": "air temp delta",
    "W_humidity_ratio": "humidity ratio", "Pv_vapor": "vapor pressure",
    "P_total_hvac": "total pressure", "COP_carnot": "Carnot COP",
    "Th_carnot": "hot reservoir temp", "Tc_carnot": "cold reservoir temp",
    "P_pv": "PV power", "eta_pv": "PV efficiency",
    "G_irradiance": "irradiance", "A_pv": "PV area",
    "P_wind": "wind power", "Cp_betz": "Bet'z coefficient",
    "rho_air_wind": "air density wind", "A_rotor": "rotor area",
    "V_wind": "wind speed", "Cp_betz_limit": "Bet'z limit",
    "eta_pv_temp": "temp-derated PV efficiency", "T_cell_pv": "cell temp",
    "T_ref_pv": "ref temp", "beta_temp_pv": "temp coeff",
    "E_illum": "illuminance", "F_lumen": "luminous flux",
    "A_illum": "illuminated area", "UF_illum": "use factor",
    "MF_illum": "maintenance factor", "eta_luminous": "luminous efficacy",
    "F_lumen2": "total lumens", "P_lamp": "lamp power",
    "I_ampacity": "cable ampacity", "A_cable": "cable area",
    "J_current_density_cable": "current density",
    "VD_cable": "cable voltage drop", "I_cable": "cable current",
    "R_cable_per_km": "cable resistance per km", "L_cable_km": "cable length km",
    "I_fault": "fault current", "V_fault": "fault voltage",
    "Z_fault": "fault impedance", "MVA_fault": "fault MVA",
    "V_fault_kv": "fault voltage kV", "I_fault_ka": "fault current kA",
    "t_relay": "relay time", "PSM_relay": "plug setting multiplier",
    "TMS_relay": "time multiplier", "k_relay_const": "relay const k",
    "alpha_relay_const": "relay const alpha",
    "Vc_cutting": "cutting speed", "D_workpiece": "workpiece diameter",
    "N_spindle": "spindle speed", "MRR_machining": "MRR",
    "Vc_cutting2": "cutting speed 2", "f_feed": "feed rate", "d_cut": "depth of cut",
    "t_solidify": "solidification", "Cm_chvorinov": "Chvorinov const",
    "Vol_casting": "casting volume", "A_casting_surf": "casting surface area",
    "n_chvorinov": "Chvorinov exponent",
    "sigma_true": "true stress", "sigma_eng": "engineering stress",
    "epsilon_eng": "engineering strain", "epsilon_true": "true strain",
    "T_tool_life": "tool life", "C_taylor": "Taylor constant", "n_taylor": "Taylor exponent",
    "theta_step": "step angle", "N_steps_rev": "steps per revolution",
    "N_rpm_stepper": "stepper RPM", "f_step_rate": "step rate",
    "Kw_window_factor": "window factor", "a_cond_wire": "conductor wire area",
    "Aw_window": "window area",
    "Q_rating_transformer": "transformer rating", "f_trans": "freq transformer",
    "Bm_trans": "max flux density trans", "Ai_core2": "core area",
    "delta_current_density_trans": "current density trans",
    "Kw_trans2": "window factor trans",
    "eta_carnot": "Carnot efficiency", "eta_otto": "Otto efficiency",
    "r_compression": "compression ratio", "eta_diesel": "Diesel efficiency",
    "rc_cutoff_ratio": "cutoff ratio", "eta_brayton": "Brayton efficiency",
    "r_pressure_ratio": "pressure ratio", "eta_rankine_steam": "Rankine efficiency",
    "W_net_rankine": "net Rankine work", "Q_in_rankine": "Rankine heat input",
    "sfc_engine2": "specific fuel cons", "m_dot_fuel": "fuel mass flow",
    "P_engine_out": "engine output",
    "S_sensor": "sensor sensitivity", "dOutput_sensor": "sensor output delta",
    "dInput_sensor": "sensor input delta", "err_pct": "measurement error",
    "Measured_val": "measured value", "True_val": "true value",
    "SNR_db": "SNR dB", "Vsignal_rms": "signal RMS", "Vnoise_rms": "noise RMS",
    "Gain_db": "gain dB", "Vout_instr": "instrument output", "Vin_instr": "instrument input",
    "Ns_pump": "pump specific speed", "N_pump2": "pump speed 2",
    "Q_pump2": "pump flow 2", "H_pump2": "pump head 2",
    "u2_impeller": "impeller tip speed", "D2_impeller": "impeller diameter",
    "H_euler": "Euler head", "Vu2_whirl": "whirl velocity",
}


def export_formulas_as_warehouse():
    """Export all formulas from formulas.py as individual JSON files by domain."""
    domain_formulas = {}

    for name, equation in FORMULAS.items():
        domain = FORMULA_DOMAINS.get(name, "other")
        symbols = collect_symbols(equation)

        # Build variables dict
        variables = {}
        for sym_name in symbols:
            sym = list(symbols)[0]
            all_syms[sym_name] = sym
            variables[sym_name] = {
                "symbol": sym_name,
                "description": SYMBOL_DESCRIPTIONS.get(sym_name, f"{sym_name} (symbol)"),
            }

        formula_entry = {
            "name": name,
            "equation_str": str(equation),
            "lhs": str(equation.lhs),
            "lhs_symbol": str(equation.lhs),
            "rhs_free_symbols": sorted(str(s) for s in equation.rhs.free_symbols),
            "domain": domain,
            "variables": variables,
            "sympy_eq_str": str(equation),
            "is_equation": True,
        }

        domain_formulas.setdefault(domain, [])
        domain_formulas[domain].append((name, formula_entry))

    exported = 0
    for domain, formulas_list in domain_formulas.items():
        safe_domain = domain.replace(" ", "_")
        dir_path = os.path.join(WAREHOUSE, safe_domain)
        os.makedirs(dir_path, exist_ok=True)

        for name, entry in formulas_list:
            safe_name = name.replace(" ", "_")
            file_path = os.path.join(dir_path, f"{safe_name}.json")
            with open(file_path, "w") as f:
                json.dump(entry, f, indent=2)
            exported += 1

    # Also write a warehouse index
    index = {}
    for domain, formulas_list in domain_formulas.items():
        safe_domain = domain.replace(" ", "_")
        index[safe_domain] = [name for name, _ in formulas_list]

    index_path = os.path.join(WAREHOUSE, "index.json")
    with open(index_path, "w") as f:
        json.dump({"total_formulas": exported, "domains": {
            k: {"count": len(v), "formulas": v}
            for k, v in index.items()
        }}, f, indent=2)

    # And a flat list of all formulas (backup snapshot)
    all_flattened = {}
    for name, equation in FORMULAS.items():
        symbol_names = sorted(str(s) for s in equation.rhs.free_symbols)
        symbol_names.append(str(equation.lhs))
        all_flattened[name] = {
            "equation": str(equation),
            "domain": FORMULA_DOMAINS.get(name, "other"),
            "variables": symbol_names,
        }

    flat_path = os.path.join(WAREHOUSE, "all_formulas.json")
    with open(flat_path, "w") as f:
        json.dump(all_flattened, f, indent=2)

    # Count by domain for display
    print(f"\nWarehouse exported to: {WAREHOUSE}\n")
    print(f"Total formulas: {exported}")
    print(f"\nBy domain:")
    for domain in sorted(domain_formulas.keys()):
        print(f"  {domain}: {len(domain_formulas[domain])}")

    print(f"\nFiles created:")
    print(f"  warehouse/index.json          — master index by domain")
    print(f"  warehouse/all_formulas.json   — flat backup of all formulas")
    print(f"  warehouse/<domain>/<name>.json — individual formula files")


if __name__ == "__main__":
    export_formulas_as_warehouse()
