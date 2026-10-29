import sympy as sp

V, I, R, E, Kt, Ke, T, P, P_out, P_in, omega, Q, eta = sp.symbols(
    "V I R E Kt Ke T P P_out P_in omega Q eta"
)
mu, F, r, Tf, Pf = sp.symbols("mu F r Tf Pf")
mu0, N, L, B, A, Rm = sp.symbols("mu0 N L B A Rm")
RPM, N_segments, f = sp.symbols("RPM N_segments f")
l_cond, Phi = sp.symbols("l_cond Phi")
Vol, m, rho, J, KE = sp.symbols("Vol m rho J KE")
d, J_polar, tau = sp.symbols("d J_polar tau")
C, p_life, L10 = sp.symbols("C p_life L10")

# --- symbols for the Sawhney-based geometry design equations ---
n_poles, Z_cond, a_path, sigma_tan, D_rotor, L_rotor = sp.symbols(
    "n_poles Z_cond a_path sigma_tan D_rotor L_rotor"
)
D_comm, v_comm, J_brush, A_brush, B_max, t_yoke = sp.symbols(
    "D_comm v_comm J_brush A_brush B_max t_yoke"
)

# --- symbols for fault-simulation formulas (thermal, wear, ripple) ---
R0, alpha_temp, T_temp, T0_temp = sp.symbols("R0 alpha_temp T_temp T0_temp")
Phi0, k_demag, T_max_demag = sp.symbols("Phi0 k_demag T_max_demag")
T_amb, t_time, tau_thermal, T_final = sp.symbols("T_amb t_time tau_thermal T_final")
X0, s_sev, k_growth = sp.symbols("X0 s_sev k_growth")
T_nom, k_unbal, omega_t, t_ripple, T_ripple = sp.symbols("T_nom k_unbal omega_t t_ripple T_ripple")

# --- ESP32 symbols. Distinct names are used wherever the physical quantity
# is NOT the same as an existing DC-motor symbol (e.g. f_rf vs f, L_ant vs L,
# d_rf vs d, T_clk vs T) so the Formula Brain's variable graph doesn't
# accidentally merge two unrelated physical quantities onto one node just
# because they happen to share a letter. Where the quantity genuinely IS the
# same concept (V, I, P, m, T_amb), the existing symbol is reused on purpose.
I_total, I_cpu, I_wifi, I_gpio, I_peripherals = sp.symbols("I_total I_cpu I_wifi I_gpio I_peripherals")
V_out, V_in, R_regulator, C_battery, t_batt = sp.symbols("V_out V_in R_regulator C_battery t_batt")
T_chip, R_th, dT_dt, Cp = sp.symbols("T_chip R_th dT_dt Cp")
c_light, f_rf, L_ant, dist_rf, PL, G_tx, G_rx, P_tx, P_rx, lam = sp.symbols(
    "c_light f_rf L_ant dist_rf PL G_tx G_rx P_tx P_rx lambda"
)
T_clk, f_crystal, f_cpu, cycles, cycles_per_inst, t_inst = sp.symbols(
    "T_clk f_crystal f_cpu cycles cycles_per_inst t_inst"
)
V_high, V_low, R_load, I_max, V_dd, R_output_impedance, I_pull, R_pull = sp.symbols(
    "V_high V_low R_load I_max V_dd R_output_impedance I_pull R_pull"
)

# =====================================================================
# EXPANSION PASS: induction motors, hydraulics, mechanical drives,
# electronics, industrial DC motors, transformers, synchronous machines,
# three-phase power, PID control, and a cross-cutting universal toolkit
# (vibration, fatigue, heat transfer). None of these are wired to a twin
# yet -- this is the formula library first, stitching to real machines
# comes after. Distinct symbol names are used throughout (rather than
# reusing DC-motor/ESP32 symbols) wherever the underlying real machine
# will be a different physical instance, so the Brain's shared-variable
# graph doesn't wrongly conflate two different real quantities just
# because they carry the same textbook letter.
# =====================================================================

# --- induction motor ---
N_s, N_r, s_slip, f_ac, f_r = sp.symbols("N_s N_r s_slip f_ac f_r")
E2, E2s, X2, X2s, R2, I2 = sp.symbols("E2 E2s X2 X2s R2 I2")
R1, X1, V1, omega_s, I1 = sp.symbols("R1 X1 V1 omega_s I1")
T_im, s_maxT, T_max_im, T_start_im = sp.symbols("T_im s_maxT T_max_im T_start_im")
P_ag, P_rcl, P_dev, P_fw_im, P_scl = sp.symbols("P_ag P_rcl P_dev P_fw_im P_scl")
P_in_3ph_im, V_L, I_L, pf_im, eta_im, P_out_im = sp.symbols("P_in_3ph_im V_L I_L pf_im eta_im P_out_im")
I_line_star, I_line_delta, T_start_star, T_start_delta = sp.symbols("I_line_star I_line_delta T_start_star T_start_delta")
Co_im, D_im, L_im, n_poles_im, B_av_im, Phi_im = sp.symbols("Co_im D_im L_im n_poles_im B_av_im Phi_im")
S_slots_im, g_im, T_ph_im, E1, k_w_im = sp.symbols("S_slots_im g_im T_ph_im E1 k_w_im")
lambda_slot_im = sp.Symbol("lambda_slot_im")
J_cond_im, A_cond_im, I_ph, ac_im, m_phases_im = sp.symbols("J_cond_im A_cond_im I_ph ac_im m_phases_im")

# --- transformers ---
K_trans, N1_t, N2_t, V1_t, V2_t, I1_t, I2_t = sp.symbols("K_trans N1_t N2_t V1_t V2_t I1_t I2_t")
E_t, Phi_max_t, VR_t, R01_t, X01_t = sp.symbols("E_t Phi_max_t VR_t R01_t X01_t")
P_cu_t, P_i_t, P_out_t, P_in_t, eta_t = sp.symbols("P_cu_t P_i_t P_out_t P_in_t eta_t")

# --- synchronous machines ---
E_sync, Xs_sync, delta_sync, P_sync, V_sync = sp.symbols("E_sync Xs_sync delta_sync P_sync V_sync")
Ia_sync, Ra_sync, Pmax_sync = sp.symbols("Ia_sync Ra_sync Pmax_sync")

# --- three-phase power systems ---
V_ph3, V_L3, I_ph3, I_L3, P_3ph, Q_3ph, S_3ph, pf_3ph, Qc_pfc = sp.symbols(
    "V_ph3 V_L3 I_ph3 I_L3 P_3ph Q_3ph S_3ph pf_3ph Qc_pfc"
)

# --- hydraulics ---
P_hyd, Q_hyd, A_hyd, v_hyd, F_hyd = sp.symbols("P_hyd Q_hyd A_hyd v_hyd F_hyd")
rho_hyd, g_grav, h_hyd, Re_hyd, mu_visc = sp.symbols("rho_hyd g_grav h_hyd Re_hyd mu_visc")
f_darcy, L_pipe, D_pipe, hl_major, K_minor, hl_minor = sp.symbols("f_darcy L_pipe D_pipe hl_major K_minor hl_minor")
Q_pump, N_pump, D_disp, eta_vol, eta_mech_hyd, eta_overall_hyd = sp.symbols(
    "Q_pump N_pump D_disp eta_vol eta_mech_hyd eta_overall_hyd"
)
P_hyd_power, T_pump, Cv_valve, dP_valve = sp.symbols("P_hyd_power T_pump Cv_valve dP_valve")
F_cyl, v_cyl, Q_cyl, A_cyl = sp.symbols("F_cyl v_cyl Q_cyl A_cyl")
P_acc, V_acc, P0_acc, V0_acc = sp.symbols("P_acc V_acc P0_acc V0_acc")

# --- mechanical: gears, springs, belts, chains ---
m_gear, Np_gear, Ng_gear, Dp_gear, Dg_gear, CD_gear, GR_gear = sp.symbols(
    "m_gear Np_gear Ng_gear Dp_gear Dg_gear CD_gear GR_gear"
)
Wt_gear, sigma_lewis, Y_lewis, Fw_gear = sp.symbols("Wt_gear sigma_lewis Y_lewis Fw_gear")
v_pitch_gear = sp.Symbol("v_pitch_gear")
Kv_dynamic, Ks_service, sigma_agma, J_agma = sp.symbols("Kv_dynamic Ks_service sigma_agma J_agma")
k_spring, G_spring, d_wire, D_coil, Na_spring, Ws_wahl, C_spring, tau_spring = sp.symbols(
    "k_spring G_spring d_wire D_coil Na_spring Ws_wahl C_spring tau_spring"
)
T_belt, T_slack, theta_wrap, mu_belt, P_belt, v_belt = sp.symbols("T_belt T_slack theta_wrap mu_belt P_belt v_belt")
p_chain, N1_sprocket, N2_sprocket, v_chain, CR_chain = sp.symbols("p_chain N1_sprocket N2_sprocket v_chain CR_chain")

# --- electronics (beyond ESP32) ---
Av_opamp, Rf_opamp, Rin_opamp, GBW_opamp, SR_opamp = sp.symbols("Av_opamp Rf_opamp Rin_opamp GBW_opamp SR_opamp")
fc_rc, R_filt, C_filt = sp.symbols("fc_rc R_filt C_filt")
Id_diode, Is_diode, Vd_diode, Vt_thermal, n_ideality = sp.symbols("Id_diode Is_diode Vd_diode Vt_thermal n_ideality")
beta_bjt, Ic_bjt, Ib_bjt, Ie_bjt = sp.symbols("beta_bjt Ic_bjt Ib_bjt Ie_bjt")
gm_mosfet, Vgs_mosfet, Vth_mosfet, Id_mosfet, k_mosfet = sp.symbols("gm_mosfet Vgs_mosfet Vth_mosfet Id_mosfet k_mosfet")
Vr_ripple, C_filt_cap, I_load, f_ripple = sp.symbols("Vr_ripple C_filt_cap I_load f_ripple")
D_duty, Vout_buck, Vin_buck, Vout_boost = sp.symbols("D_duty Vout_buck Vin_buck Vout_boost")

# --- bigger / industrial DC motor ---
F_ar, F_cm, F_ip, N_eq_cur, Ia_big, Z_big = sp.symbols("F_ar F_cm F_ip N_eq_cur Ia_big Z_big")
E_series, E_shunt, SpeedReg_dc = sp.symbols("E_series E_shunt SpeedReg_dc")

# --- universal cross-cutting toolkit ---
omega_n, k_stiff, m_sys, zeta_damp, c_damp = sp.symbols("omega_n k_stiff m_sys zeta_damp c_damp")
sigma_a, sigma_m, Se_endurance, Sut_ultimate, n_safety = sp.symbols("sigma_a sigma_m Se_endurance Sut_ultimate n_safety")
h_conv, Nu_nusselt, k_thermal_cond, Lc_char, Bi_biot = sp.symbols("h_conv Nu_nusselt k_thermal_cond Lc_char Bi_biot")

# --- PID control ---
Kp_pid, Ki_pid, Kd_pid, e_err, u_pid = sp.symbols("Kp_pid Ki_pid Kd_pid e_err u_pid")
ess_error, zeta_2nd, omega_n_2nd, Mp_overshoot, ts_settling = sp.symbols(
    "ess_error zeta_2nd omega_n_2nd Mp_overshoot ts_settling"
)

# =====================================================================
# EXPANSION PASS 2: pushing past the 250-formula mark -- induction motor
# test/nameplate depth, strength of materials, shaft dynamics, hydraulic
# depth, electronics depth, thermal depth, control systems, transformer/
# synchronous depth, battery electrochemistry, fatigue, digital/logic,
# extra fluid statics, vibration, and single-phase AC power.
# =====================================================================

# --- induction motor: test/nameplate depth ---
V0_test_im, I0_test_im, P0_test_im, pf0_im = sp.symbols("V0_test_im I0_test_im P0_test_im pf0_im")
Vsc_test_im, Isc_test_im, Psc_test_im, Z01_im = sp.symbols("Vsc_test_im Isc_test_im Psc_test_im Z01_im")
s_fl_im, N_synch_fl, N_fl_im, class_temp_rise_im = sp.symbols("s_fl_im N_synch_fl N_fl_im class_temp_rise_im")
eta_partial_im, load_frac_im, R2_deep, R2_ac_im, k_deepbar_im = sp.symbols(
    "eta_partial_im load_frac_im R2_deep R2_ac_im k_deepbar_im"
)

# --- strength of materials / beam bending ---
sigma_bend, M_bend, c_dist, I_area, Z_section = sp.symbols("sigma_bend M_bend c_dist I_area Z_section")
delta_beam, F_beam, Lspan_beam, E_mod, P_euler, Le_col, k_gyr = sp.symbols(
    "delta_beam F_beam Lspan_beam E_mod P_euler Le_col k_gyr"
)
sigma_principal, sigma_x, sigma_y, tau_xy, sigma_vm, Kt_stress = sp.symbols(
    "sigma_principal sigma_x sigma_y tau_xy sigma_vm Kt_stress"
)
epsilon_strain, nu_poisson, alpha_therm, dL_therm, T0_therm = sp.symbols(
    "epsilon_strain nu_poisson alpha_therm dL_therm T0_therm"
)

# --- shaft dynamics (extends existing shaft domain) ---
delta_shaft, N_crit_shaft, sigma_a_shaft, tau_m_shaft, Kf_shaft, tau_key, F_key, A_key = sp.symbols(
    "delta_shaft N_crit_shaft sigma_a_shaft tau_m_shaft Kf_shaft tau_key F_key A_key"
)

# --- hydraulic depth ---
NPSH_avail, h_atm, h_vap, h_suction, h_fric_suction = sp.symbols("NPSH_avail h_atm h_vap h_suction h_fric_suction")
Ca_cav, P_dp_shock, K_bulk, a_wave = sp.symbols("Ca_cav P_dp_shock K_bulk a_wave")
Q_orifice, Cd_orifice, A_orifice = sp.symbols("Q_orifice Cd_orifice A_orifice")
N_ss_pump, Q_aff, N_aff, H_aff = sp.symbols("N_ss_pump Q_aff N_aff H_aff")
v_torricelli, h_torricelli, P_manometer, rho_manometer, h_manometer = sp.symbols(
    "v_torricelli h_torricelli P_manometer rho_manometer h_manometer"
)
F_buoy, rho_fluid_b, Vol_disp, P_depth = sp.symbols("F_buoy rho_fluid_b Vol_disp P_depth")

# --- electronics depth ---
Vb_bridge, R1_bridge, R2_bridge, R3_bridge, R4_bridge = sp.symbols("Vb_bridge R1_bridge R2_bridge R3_bridge R4_bridge")
Vdiv_out, Vdiv_in, R1_div, R2_div = sp.symbols("Vdiv_out Vdiv_in R1_div R2_div")
f_555, R_555a, R_555b, C_555 = sp.symbols("f_555 R_555a R_555b C_555")
Av_instr, Rg_instr = sp.symbols("Av_instr Rg_instr")
Vz_zener, Iz_zener, Rz_zener = sp.symbols("Vz_zener Iz_zener Rz_zener")
eta_classA, eta_classB = sp.symbols("eta_classA eta_classB")
t_pd_gate, C_load_gate, V_swing_gate, f_clk_digital, T_clk_digital = sp.symbols(
    "t_pd_gate C_load_gate V_swing_gate f_clk_digital T_clk_digital"
)
P_dyn_cmos, C_load_cmos, f_sw_cmos, V_dd_cmos = sp.symbols("P_dyn_cmos C_load_cmos f_sw_cmos V_dd_cmos")

# --- thermal depth ---
q_fourier, k_cond, dT_dx, A_cond_area = sp.symbols("q_fourier k_cond dT_dx A_cond_area")
q_rad, eps_rad, sigma_sb, T_hot_rad, T_cold_rad = sp.symbols("q_rad eps_rad sigma_sb T_hot_rad T_cold_rad")
R_th_series, R_th_parallel = sp.symbols("R_th_series R_th_parallel")
LMTD_hx, dT1_hx, dT2_hx = sp.symbols("LMTD_hx dT1_hx dT2_hx")

# --- control systems ---
Gm_margin, Pm_margin, G_ol, H_fb, T_cl = sp.symbols("Gm_margin Pm_margin G_ol H_fb T_cl")
K_dc_gain = sp.Symbol("K_dc_gain")

# --- transformer / synchronous depth ---
K_auto_save, VA_auto = sp.symbols("K_auto_save VA_auto")
Z_pu, Z_base, V_base, S_base = sp.symbols("Z_pu Z_base V_base S_base")
VR_sync_pct, SCR_sync = sp.symbols("VR_sync_pct SCR_sync")

# --- battery electrochemistry (extends ESP32's battery_life) ---
C_peukert, I_peukert, k_peukert, t_peukert = sp.symbols("C_peukert I_peukert k_peukert t_peukert")
V_sag, R_int_batt, I_batt = sp.symbols("V_sag R_int_batt I_batt")
C_derated, T_batt_amb, alpha_batt = sp.symbols("C_derated T_batt_amb alpha_batt")
SoC_batt, Q_used, Q_rated = sp.symbols("SoC_batt Q_used Q_rated")
C_rate_batt, I_rate_batt = sp.symbols("C_rate_batt I_rate_batt")
E_batt_wh, V_nom_batt, C_ah_batt = sp.symbols("E_batt_wh V_nom_batt C_ah_batt")
E_specific_batt, m_batt = sp.symbols("E_specific_batt m_batt")
N_cycles_batt, DoD_batt, k_cycle = sp.symbols("N_cycles_batt DoD_batt k_cycle")

# --- fatigue / materials depth ---
D_miner, n_cycles_i, N_cycles_i = sp.symbols("D_miner n_cycles_i N_cycles_i")
Sf_life, a_sn, b_sn, Nf_life = sp.symbols("Sf_life a_sn b_sn Nf_life")
ka_surf, kb_size, Se_corrected = sp.symbols("ka_surf kb_size Se_corrected")

# --- vibration depth ---
X_forced, F0_forced, r_freq_ratio = sp.symbols("X_forced F0_forced r_freq_ratio")
TR_transmis = sp.Symbol("TR_transmis")
delta_log, x1_log, x2_log = sp.symbols("delta_log x1_log x2_log")
c_crit_damp = sp.Symbol("c_crit_damp")

# --- single-phase AC power ---
P_1ph, Q_1ph, S_1ph, V_1ph, I_1ph, pf_1ph = sp.symbols("P_1ph Q_1ph S_1ph V_1ph I_1ph pf_1ph")
V_rms_sine, V_peak_sine, V_pp_sine, CF_crest = sp.symbols("V_rms_sine V_peak_sine V_pp_sine CF_crest")

# =====================================================================
# EXPANSION PASS 3: final push past 250 -- digital logic depth, chemical
# kinetics (Arrhenius), stress transformation, more power electronics,
# RF matching/VSWR, control-loop tuning, heat exchanger effectiveness,
# rotating unbalance vibration, pipe pumping power.
# =====================================================================
I_oh_fanout, I_ih_fanout, N_fanout = sp.symbols("I_oh_fanout I_ih_fanout N_fanout")
V_oh_nm, V_ol_nm, V_ih_nm, V_il_nm, NM_high, NM_low = sp.symbols("V_oh_nm V_ol_nm V_ih_nm V_il_nm NM_high NM_low")
t_setup, t_hold, t_clk_to_q = sp.symbols("t_setup t_hold t_clk_to_q")

k_rate, A_arrhenius, Ea_arrhenius, R_gas, T_kelvin = sp.symbols("k_rate A_arrhenius Ea_arrhenius R_gas T_kelvin")

sigma_1_transform, sigma_2_transform, theta_transform = sp.symbols("sigma_1_transform sigma_2_transform theta_transform")

Vout_flyback, Vin_flyback, N_flyback, D_flyback = sp.symbols("Vout_flyback Vin_flyback N_flyback D_flyback")

VSWR_rf, Gamma_refl, Z0_rf, ZL_rf, RL_db = sp.symbols("VSWR_rf Gamma_refl Z0_rf ZL_rf RL_db")
Z_qw = sp.Symbol("Z_qw")

Ku_zn, Pu_zn, Kp_zn, Ti_zn, Td_zn = sp.symbols("Ku_zn Pu_zn Kp_zn Ti_zn Td_zn")

eps_hx, Cmin_hx, Cmax_hx, Qmax_hx, Qactual_hx, NTU_hx, UA_hx = sp.symbols(
    "eps_hx Cmin_hx Cmax_hx Qmax_hx Qactual_hx NTU_hx UA_hx"
)

P_pump_hyd, gamma_sg = sp.symbols("P_pump_hyd gamma_sg")

X_unbalance, me_unbalance, M_total_unbalance = sp.symbols("X_unbalance me_unbalance M_total_unbalance")

# =====================================================================
# EXPANSION PASS 4: broad industry coverage -- civil/structural, welding
# and joints, bearings/clutches/brakes/flywheels/cams, pressure vessels,
# chemical engineering, aerospace, HVAC/refrigeration, renewable energy,
# illumination, cable sizing/protection, manufacturing processes,
# thermodynamic cycles, instrumentation, fluid machinery, plus more
# electrical-machine design depth (Sawhney-style transformer/stepper).
# =====================================================================

# --- civil / structural ---
M_conc, As_conc, fy_conc, d_conc, a_conc, fc_conc, b_conc, rho_conc = sp.symbols(
    "M_conc As_conc fy_conc d_conc a_conc fc_conc b_conc rho_conc"
)
Pa_rankine, ka_rankine, gamma_soil, H_wall, phi_soil = sp.symbols("Pa_rankine ka_rankine gamma_soil H_wall phi_soil")
sigma_allow_col, F_axial_col, A_col = sp.symbols("sigma_allow_col F_axial_col A_col")
w_udl, L_beam, M_max_udl, V_max_udl, delta_udl = sp.symbols("w_udl L_beam M_max_udl V_max_udl delta_udl")

# --- welding / joints ---
tau_weld, F_weld, L_weld, throat_weld, t_weld = sp.symbols("tau_weld F_weld L_weld throat_weld t_weld")
sigma_butt, F_butt, t_butt, L_butt = sp.symbols("sigma_butt F_butt t_butt L_butt")
tau_rivet, F_rivet, d_rivet, n_rivets = sp.symbols("tau_rivet F_rivet d_rivet n_rivets")
C_bolt, k_bolt, k_member, F_ext_bolt, F_bolt_preload, F_bolt_total = sp.symbols(
    "C_bolt k_bolt k_member F_ext_bolt F_bolt_preload F_bolt_total"
)

# --- bearings depth / clutches / brakes / flywheels / cams ---
P_equiv_bear, X_radial, Y_thrust, Fr_bear, Fa_bear = sp.symbols("P_equiv_bear X_radial Y_thrust Fr_bear Fa_bear")
T_clutch, mu_clutch, F_axial_clutch, R_mean_clutch, n_surfaces = sp.symbols(
    "T_clutch mu_clutch F_axial_clutch R_mean_clutch n_surfaces"
)
T_brake, mu_brake, F_brake, R_brake = sp.symbols("T_brake mu_brake F_brake R_brake")
F1_band, F2_band, mu_band, theta_band_wrap, T_band = sp.symbols("F1_band F2_band mu_band theta_band_wrap T_band")
E_fly, J_fly, omega1_fly, omega2_fly, Cs_fly, omega_mean_fly = sp.symbols(
    "E_fly J_fly omega1_fly omega2_fly Cs_fly omega_mean_fly"
)
y_cam, h_cam, theta_cam, beta_cam, v_cam = sp.symbols("y_cam h_cam theta_cam beta_cam v_cam")

# --- pressure vessels ---
sigma_hoop, P_internal, D_vessel, t_vessel, sigma_long, sigma_sphere = sp.symbols(
    "sigma_hoop P_internal D_vessel t_vessel sigma_long sigma_sphere"
)

# --- chemical engineering ---
G_gibbs, H_enthalpy, S_entropy = sp.symbols("G_gibbs H_enthalpy S_entropy")
dH_rxn, dU_rxn, P_chem, dV_rxn = sp.symbols("dH_rxn dU_rxn P_chem dV_rxn")
Ca_conc, Ca0_conc, t_rxn = sp.symbols("Ca_conc Ca0_conc t_rxn")
N_flux, D_diff, dC_dx = sp.symbols("N_flux D_diff dC_dx")
U_overall_hx, h1_hx, h2_hx, Rf_fouling = sp.symbols("U_overall_hx h1_hx h2_hx Rf_fouling")
alpha_volatility, y_vap, x_liq = sp.symbols("alpha_volatility y_vap x_liq")
W_compressor, n_moles_gas, R_gas_const, T1_gas, P1_gas, P2_gas, gamma_gas = sp.symbols(
    "W_compressor n_moles_gas R_gas_const T1_gas P1_gas P2_gas gamma_gas"
)
CR_corrosion, mpy_const, W_loss_corr, rho_corr, A_corr, t_corr = sp.symbols(
    "CR_corrosion mpy_const W_loss_corr rho_corr A_corr t_corr"
)
P_ideal, n_ideal, R_ideal, T_ideal, V_ideal = sp.symbols("P_ideal n_ideal R_ideal T_ideal V_ideal")
Q_dot_hx, m_dot_hx, cp_hx, dT_hx = sp.symbols("Q_dot_hx m_dot_hx cp_hx dT_hx")

# --- aerospace / aerodynamics ---
L_lift, Cl_lift, S_wing, rho_air, V_air = sp.symbols("L_lift Cl_lift S_wing rho_air V_air")
D_drag, Cd_drag = sp.symbols("D_drag Cd_drag")
T_thrust_jet, m_dot_air, Ve_exhaust, V0_inlet = sp.symbols("T_thrust_jet m_dot_air Ve_exhaust V0_inlet")
R_range_breguet, V_cruise, L_D_ratio, sfc_engine, W1_fuel, W2_fuel = sp.symbols(
    "R_range_breguet V_cruise L_D_ratio sfc_engine W1_fuel W2_fuel"
)
V_stall, W_aircraft, Cl_max = sp.symbols("V_stall W_aircraft Cl_max")

# --- HVAC / refrigeration ---
COP_refrig, Qc_refrig, Wc_refrig = sp.symbols("COP_refrig Qc_refrig Wc_refrig")
COP_heatpump, Qh_heatpump = sp.symbols("COP_heatpump Qh_heatpump")
Q_cooling_load, m_dot_air_hvac, cp_air_hvac, dT_hvac = sp.symbols("Q_cooling_load m_dot_air_hvac cp_air_hvac dT_hvac")
W_humidity_ratio, Pv_vapor, P_total_hvac = sp.symbols("W_humidity_ratio Pv_vapor P_total_hvac")
COP_carnot, Th_carnot, Tc_carnot = sp.symbols("COP_carnot Th_carnot Tc_carnot")

# --- renewable energy ---
P_pv, eta_pv, G_irradiance, A_pv = sp.symbols("P_pv eta_pv G_irradiance A_pv")
P_wind, Cp_betz, rho_air_wind, A_rotor, V_wind = sp.symbols("P_wind Cp_betz rho_air_wind A_rotor V_wind")
Cp_betz_limit = sp.Symbol("Cp_betz_limit")
eta_pv_temp, T_cell_pv, T_ref_pv, beta_temp_pv = sp.symbols("eta_pv_temp T_cell_pv T_ref_pv beta_temp_pv")

# --- illumination engineering ---
E_illum, F_lumen, A_illum, UF_illum, MF_illum = sp.symbols("E_illum F_lumen A_illum UF_illum MF_illum")
eta_luminous, F_lumen2, P_lamp = sp.symbols("eta_luminous F_lumen2 P_lamp")

# --- cable sizing / power system protection ---
I_ampacity, A_cable, J_current_density_cable = sp.symbols("I_ampacity A_cable J_current_density_cable")
VD_cable, I_cable, R_cable_per_km, L_cable_km = sp.symbols("VD_cable I_cable R_cable_per_km L_cable_km")
I_fault, V_fault, Z_fault = sp.symbols("I_fault V_fault Z_fault")
MVA_fault, V_fault_kv, I_fault_ka = sp.symbols("MVA_fault V_fault_kv I_fault_ka")
t_relay, PSM_relay, TMS_relay, k_relay_const, alpha_relay_const = sp.symbols(
    "t_relay PSM_relay TMS_relay k_relay_const alpha_relay_const"
)

# --- manufacturing processes ---
Vc_cutting, D_workpiece, N_spindle = sp.symbols("Vc_cutting D_workpiece N_spindle")
MRR_machining, Vc_cutting2, f_feed, d_cut = sp.symbols("MRR_machining Vc_cutting2 f_feed d_cut")
t_solidify, Cm_chvorinov, Vol_casting, A_casting_surf, n_chvorinov = sp.symbols(
    "t_solidify Cm_chvorinov Vol_casting A_casting_surf n_chvorinov"
)
sigma_true, sigma_eng, epsilon_eng, epsilon_true = sp.symbols("sigma_true sigma_eng epsilon_eng epsilon_true")
T_tool_life, C_taylor, n_taylor = sp.symbols("T_tool_life C_taylor n_taylor")

# --- stepper motors ---
theta_step, N_steps_rev, N_rpm_stepper, f_step_rate = sp.symbols("theta_step N_steps_rev N_rpm_stepper f_step_rate")

# --- transformer design depth (Sawhney) ---
Kw_window_factor, a_cond_wire, Aw_window = sp.symbols("Kw_window_factor a_cond_wire Aw_window")
Q_rating_transformer, f_trans, Bm_trans, Ai_core2, delta_current_density_trans, Kw_trans2 = sp.symbols(
    "Q_rating_transformer f_trans Bm_trans Ai_core2 delta_current_density_trans Kw_trans2"
)

# --- thermodynamic cycles ---
eta_carnot = sp.Symbol("eta_carnot")
eta_otto, r_compression = sp.symbols("eta_otto r_compression")
eta_diesel, rc_cutoff_ratio = sp.symbols("eta_diesel rc_cutoff_ratio")
eta_brayton, r_pressure_ratio = sp.symbols("eta_brayton r_pressure_ratio")
eta_rankine_steam, W_net_rankine, Q_in_rankine = sp.symbols("eta_rankine_steam W_net_rankine Q_in_rankine")
sfc_engine2, m_dot_fuel, P_engine_out = sp.symbols("sfc_engine2 m_dot_fuel P_engine_out")

# --- instrumentation ---
S_sensor, dOutput_sensor, dInput_sensor = sp.symbols("S_sensor dOutput_sensor dInput_sensor")
err_pct, Measured_val, True_val = sp.symbols("err_pct Measured_val True_val")
SNR_db, Vsignal_rms, Vnoise_rms = sp.symbols("SNR_db Vsignal_rms Vnoise_rms")
Gain_db, Vout_instr, Vin_instr = sp.symbols("Gain_db Vout_instr Vin_instr")

# --- fluid machinery depth ---
Ns_pump, N_pump2, Q_pump2, H_pump2 = sp.symbols("Ns_pump N_pump2 Q_pump2 H_pump2")
u2_impeller, D2_impeller = sp.symbols("u2_impeller D2_impeller")
H_euler, Vu2_whirl = sp.symbols("H_euler Vu2_whirl")

FORMULAS = {
    # --- required minimum set ---
    "ohms_law": sp.Eq(V, I * R),
    "back_emf": sp.Eq(E, V - I * R),
    "torque": sp.Eq(T, Kt * I),
    "power_electrical": sp.Eq(P, V * I),
    "power_mechanical": sp.Eq(P, T * omega),
    "heat_generated": sp.Eq(Q, I ** 2 * R),
    "efficiency": sp.Eq(eta, P_out / P_in),
    "angular_velocity": sp.Eq(omega, (V - I * R) / Ke),
    "bearing_friction_torque": sp.Eq(Tf, mu * F * r),
    "flux_density": sp.Eq(B, mu0 * N * I / L),
    # --- supporting formulas needed to cover every component ---
    "rpm_conversion": sp.Eq(RPM, omega * 60 / (2 * sp.pi)),
    "commutation_frequency": sp.Eq(f, N_segments * RPM / 60),
    "lorentz_force": sp.Eq(F, B * I * l_cond),
    "magnetic_flux": sp.Eq(Phi, B * A),
    "reluctance": sp.Eq(Rm, L / (mu * A)),
    "cylinder_volume": sp.Eq(Vol, sp.pi * r ** 2 * L),
    "mass_from_volume": sp.Eq(m, rho * Vol),
    "moment_of_inertia_cylinder": sp.Eq(J, m * r ** 2 / 2),
    "kinetic_energy": sp.Eq(KE, J * omega ** 2 / 2),
    "polar_moment": sp.Eq(J_polar, sp.pi * d ** 4 / 32),
    "shear_stress": sp.Eq(tau, T * r / J_polar),
    "bearing_power_loss": sp.Eq(Pf, Tf * omega),
    "bearing_life_l10": sp.Eq(L10, (C / P) ** p_life * 10 ** 6),
    # --- Sawhney DC-machine geometry design equations (motor_design_derivation.md) ---
    "winding_torque_constant": sp.Eq(Kt, (n_poles * Z_cond * Phi) / (2 * sp.pi * a_path)),
    "rotor_shear_sizing": sp.Eq(T, 2 * sigma_tan * (sp.pi / 4) * D_rotor ** 2 * L_rotor),
    "shaft_torsion": sp.Eq(T, sp.pi * tau * d ** 3 / 16),
    "commutator_peripheral_velocity": sp.Eq(v_comm, sp.pi * D_comm * RPM / 60),
    "brush_current_density": sp.Eq(J_brush, I / A_brush),
    "stator_yoke_thickness": sp.Eq(t_yoke, Phi / (2 * B_max * L_rotor)),
    # --- fault-simulation formulas (thermal, wear/severity growth, ripple) ---
    "resistance_temperature": sp.Eq(R, R0 * (1 + alpha_temp * (T_temp - T0_temp))),
    "flux_thermal_derating": sp.Eq(Phi, Phi0 * (1 - k_demag * (T_temp - T0_temp) / (T_max_demag - T0_temp))),
    "thermal_rise_rc": sp.Eq(T_temp, T_amb + (T_final - T_amb) * (1 - sp.exp(-t_time / tau_thermal))),
    "severity_growth_asymptotic": sp.Eq(R, R0 / (1 - s_sev)),  # generalized open/wear-toward-infinity pattern (used by E01 and reusable for any "progressively worse" resistance/friction fault)
    "severity_growth_linear": sp.Eq(R, R0 * (1 + k_growth * s_sev)),  # generalized gradual wear pattern (bounded growth, e.g. bearing wear, contact roughening)
    "torque_ripple": sp.Eq(T_ripple, T_nom * (1 + k_unbal * sp.sin(omega_t * t_ripple))),  # periodic ripple for imbalance/eccentricity/bent-shaft faults

    # --- ESP32: power domain ---
    "supply_current": sp.Eq(I_total, I_cpu + I_wifi + I_gpio + I_peripherals),
    "voltage_drop": sp.Eq(V_out, V_in - I_total * R_regulator),
    "power_consumption": sp.Eq(P, V * I_total),
    "battery_life": sp.Eq(t_batt, C_battery / I_total),
    # --- ESP32: thermal domain ---
    "chip_temperature": sp.Eq(T_chip, T_amb + P * R_th),
    "thermal_resistance": sp.Eq(R_th, (T_chip - T_amb) / P),
    "temperature_rise_rate": sp.Eq(dT_dt, P / (m * Cp)),
    # --- ESP32: RF domain ---
    "wavelength": sp.Eq(lam, c_light / f_rf),
    "antenna_length_quarter_wave": sp.Eq(L_ant, lam / 4),
    "path_loss": sp.Eq(PL, 20 * sp.log(4 * sp.pi * dist_rf * f_rf / c_light, 10)),
    "received_signal": sp.Eq(P_rx, P_tx - PL + G_tx + G_rx),
    # --- ESP32: timing domain ---
    "clock_period": sp.Eq(T_clk, 1 / f_crystal),
    "cpu_cycles_per_second": sp.Eq(cycles, f_cpu),
    "instruction_time": sp.Eq(t_inst, cycles_per_inst / f_cpu),
    # --- ESP32: GPIO domain ---
    "gpio_current": sp.Eq(I_gpio, (V_high - V_low) / R_load),
    "drive_strength": sp.Eq(I_max, V_dd / R_output_impedance),
    "pull_resistor_current": sp.Eq(I_pull, V_dd / R_pull),

    # =================================================================
    # INDUCTION MOTOR
    # =================================================================
    "synchronous_speed": sp.Eq(N_s, 120 * f_ac / n_poles_im),
    "slip": sp.Eq(s_slip, (N_s - N_r) / N_s),
    "rotor_speed_from_slip": sp.Eq(N_r, N_s * (1 - s_slip)),
    "rotor_frequency": sp.Eq(f_r, s_slip * f_ac),
    "rotor_emf_running": sp.Eq(E2s, s_slip * E2),
    "rotor_reactance_running": sp.Eq(X2s, s_slip * X2),
    "rotor_current_im": sp.Eq(I2, (s_slip * E2) / sp.sqrt(R2 ** 2 + (s_slip * X2) ** 2)),
    "synchronous_angular_speed": sp.Eq(omega_s, 2 * sp.pi * N_s / 60),
    "torque_equation_im": sp.Eq(T_im, (3 * V1 ** 2 * (R2 / s_slip)) / (omega_s * ((R1 + R2 / s_slip) ** 2 + (X1 + X2) ** 2))),
    "max_torque_slip": sp.Eq(s_maxT, R2 / sp.sqrt(R1 ** 2 + (X1 + X2) ** 2)),
    "breakdown_torque_im": sp.Eq(T_max_im, (3 * V1 ** 2) / (2 * omega_s * (R1 + sp.sqrt(R1 ** 2 + (X1 + X2) ** 2)))),
    "starting_torque_im": sp.Eq(T_start_im, (3 * V1 ** 2 * R2) / (omega_s * ((R1 + R2) ** 2 + (X1 + X2) ** 2))),
    "air_gap_power": sp.Eq(P_ag, 3 * I2 ** 2 * (R2 / s_slip)),
    "rotor_copper_loss_im": sp.Eq(P_rcl, s_slip * P_ag),
    "mech_power_developed": sp.Eq(P_dev, (1 - s_slip) * P_ag),
    "output_power_im": sp.Eq(P_out_im, P_dev - P_fw_im),
    "stator_copper_loss_im": sp.Eq(P_scl, 3 * I1 ** 2 * R1),
    "input_power_3phase_im": sp.Eq(P_in_3ph_im, sp.sqrt(3) * V_L * I_L * pf_im),
    "power_factor_im": sp.Eq(pf_im, P_in_3ph_im / (sp.sqrt(3) * V_L * I_L)),
    "efficiency_im": sp.Eq(eta_im, P_out_im / P_in_3ph_im),
    "star_delta_current_ratio": sp.Eq(I_line_star, I_line_delta / 3),
    "star_delta_torque_ratio": sp.Eq(T_start_star, T_start_delta / 3),
    "output_equation_im": sp.Eq(P_out_im, Co_im * D_im ** 2 * L_im * N_s),
    "specific_magnetic_loading_im": sp.Eq(B_av_im, Phi_im / ((sp.pi * D_im / n_poles_im) * L_im)),
    "slot_pitch_im": sp.Eq(lambda_slot_im, sp.pi * D_im / S_slots_im),
    "air_gap_length_im": sp.Eq(g_im, sp.Rational(2, 10) + 2 * sp.sqrt(D_im * L_im)),
    "turns_per_phase_im": sp.Eq(T_ph_im, E1 / (sp.Rational(444, 100) * f_ac * Phi_im * k_w_im)),
    "current_density_conductor_im": sp.Eq(J_cond_im, I_ph / A_cond_im),
    "specific_electric_loading_im": sp.Eq(ac_im, (sp.sqrt(2) * m_phases_im * T_ph_im * I_ph) / (sp.pi * D_im)),

    # =================================================================
    # TRANSFORMERS
    # =================================================================
    "transformer_turns_ratio": sp.Eq(K_trans, N2_t / N1_t),
    "transformer_voltage_ratio": sp.Eq(K_trans, V2_t / V1_t),
    "transformer_current_ratio": sp.Eq(K_trans, I1_t / I2_t),
    "transformer_emf_equation": sp.Eq(E_t, sp.Rational(444, 100) * f_ac * Phi_max_t * N1_t),
    "transformer_voltage_regulation": sp.Eq(VR_t, (I2_t * (R01_t * sp.cos(delta_sync) + X01_t * sp.sin(delta_sync))) / V2_t),
    "transformer_copper_loss": sp.Eq(P_cu_t, I1_t ** 2 * R01_t),
    "transformer_efficiency": sp.Eq(eta_t, P_out_t / (P_out_t + P_cu_t + P_i_t)),
    "transformer_input_power": sp.Eq(P_in_t, P_out_t + P_cu_t + P_i_t),

    # =================================================================
    # SYNCHRONOUS MACHINES
    # =================================================================
    "synchronous_emf_equation": sp.Eq(E_sync, sp.Rational(444, 100) * f_ac * Phi_im * N1_t * k_w_im),
    "synchronous_power_developed": sp.Eq(P_sync, (V_sync * E_sync * sp.sin(delta_sync)) / Xs_sync),
    "synchronous_max_power": sp.Eq(Pmax_sync, (V_sync * E_sync) / Xs_sync),
    "synchronous_armature_current": sp.Eq(Ia_sync, (E_sync - V_sync) / sp.sqrt(Ra_sync ** 2 + Xs_sync ** 2)),

    # =================================================================
    # THREE-PHASE POWER SYSTEMS
    # =================================================================
    "three_phase_power": sp.Eq(P_3ph, sp.sqrt(3) * V_L3 * I_L3 * pf_3ph),
    "three_phase_reactive_power": sp.Eq(Q_3ph, sp.sqrt(3) * V_L3 * I_L3 * sp.sin(sp.acos(pf_3ph))),
    "three_phase_apparent_power": sp.Eq(S_3ph, sp.sqrt(3) * V_L3 * I_L3),
    "star_line_phase_voltage": sp.Eq(V_L3, sp.sqrt(3) * V_ph3),
    "delta_line_phase_current": sp.Eq(I_L3, sp.sqrt(3) * I_ph3),
    "power_factor_correction_capacitor": sp.Eq(Qc_pfc, P_3ph * (sp.tan(sp.acos(pf_3ph)) - sp.tan(delta_sync))),

    # =================================================================
    # HYDRAULICS
    # =================================================================
    "pascals_law": sp.Eq(P_hyd, F_hyd / A_hyd),
    "continuity_equation": sp.Eq(Q_hyd, A_hyd * v_hyd),
    "bernoulli_head": sp.Eq(h_hyd, P_hyd / (rho_hyd * g_grav) + v_hyd ** 2 / (2 * g_grav)),
    "reynolds_number": sp.Eq(Re_hyd, (rho_hyd * v_hyd * D_pipe) / mu_visc),
    "darcy_weisbach_head_loss": sp.Eq(hl_major, f_darcy * (L_pipe / D_pipe) * (v_hyd ** 2 / (2 * g_grav))),
    "minor_head_loss": sp.Eq(hl_minor, K_minor * (v_hyd ** 2 / (2 * g_grav))),
    "pump_flow_rate": sp.Eq(Q_pump, D_disp * N_pump),
    "pump_volumetric_efficiency": sp.Eq(eta_vol, Q_pump / (D_disp * N_pump)),
    "pump_overall_efficiency": sp.Eq(eta_overall_hyd, eta_vol * eta_mech_hyd),
    "hydraulic_power": sp.Eq(P_hyd_power, P_hyd * Q_hyd),
    "pump_torque": sp.Eq(T_pump, (P_hyd * D_disp) / (2 * sp.pi * eta_mech_hyd)),
    "valve_flow_coefficient": sp.Eq(Q_hyd, Cv_valve * sp.sqrt(dP_valve)),
    "cylinder_force": sp.Eq(F_cyl, P_hyd * A_cyl),
    "cylinder_speed": sp.Eq(v_cyl, Q_cyl / A_cyl),
    "accumulator_gas_law": sp.Eq(P_acc, (P0_acc * V0_acc) / V_acc),

    # =================================================================
    # MECHANICAL: GEARS, SPRINGS, BELTS, CHAINS
    # =================================================================
    "gear_module": sp.Eq(m_gear, Dp_gear / Np_gear),
    "gear_ratio": sp.Eq(GR_gear, Ng_gear / Np_gear),
    "gear_center_distance": sp.Eq(CD_gear, (Dp_gear + Dg_gear) / 2),
    "gear_pitch_line_velocity": sp.Eq(v_pitch_gear, sp.pi * Dp_gear * N_pump / 60),
    "lewis_bending_stress": sp.Eq(sigma_lewis, Wt_gear / (Fw_gear * m_gear * Y_lewis)),
    "agma_bending_stress": sp.Eq(sigma_agma, (Wt_gear * Kv_dynamic * Ks_service) / (Fw_gear * m_gear * J_agma)),
    "spring_rate": sp.Eq(k_spring, (G_spring * d_wire ** 4) / (8 * D_coil ** 3 * Na_spring)),
    "spring_index": sp.Eq(C_spring, D_coil / d_wire),
    "wahl_stress_factor": sp.Eq(Ws_wahl, (4 * C_spring - 1) / (4 * C_spring - 4) + sp.Rational(615, 1000) / C_spring),
    "spring_shear_stress": sp.Eq(tau_spring, (Ws_wahl * 8 * F_hyd * D_coil) / (sp.pi * d_wire ** 3)),
    "belt_tension_ratio": sp.Eq(T_belt, T_slack * sp.exp(mu_belt * theta_wrap)),
    "belt_power_transmitted": sp.Eq(P_belt, (T_belt - T_slack) * v_belt),
    "chain_velocity": sp.Eq(v_chain, p_chain * N1_sprocket / 60),
    "chain_sprocket_ratio": sp.Eq(CR_chain, N2_sprocket / N1_sprocket),

    # =================================================================
    # ELECTRONICS (beyond ESP32)
    # =================================================================
    "opamp_inverting_gain": sp.Eq(Av_opamp, -Rf_opamp / Rin_opamp),
    "opamp_noninverting_gain": sp.Eq(Av_opamp, 1 + Rf_opamp / Rin_opamp),
    "opamp_bandwidth": sp.Eq(GBW_opamp, Av_opamp * fc_rc),
    "rc_cutoff_frequency": sp.Eq(fc_rc, 1 / (2 * sp.pi * R_filt * C_filt)),
    "diode_shockley_equation": sp.Eq(Id_diode, Is_diode * (sp.exp(Vd_diode / (n_ideality * Vt_thermal)) - 1)),
    "bjt_current_gain": sp.Eq(beta_bjt, Ic_bjt / Ib_bjt),
    "bjt_emitter_current": sp.Eq(Ie_bjt, Ib_bjt + Ic_bjt),
    "mosfet_drain_current_saturation": sp.Eq(Id_mosfet, k_mosfet * (Vgs_mosfet - Vth_mosfet) ** 2),
    "mosfet_transconductance": sp.Eq(gm_mosfet, 2 * sp.sqrt(k_mosfet * Id_mosfet)),
    "capacitor_ripple_voltage": sp.Eq(Vr_ripple, I_load / (C_filt_cap * f_ripple)),
    "buck_converter_ratio": sp.Eq(Vout_buck, D_duty * Vin_buck),
    "boost_converter_ratio": sp.Eq(Vout_boost, Vin_buck / (1 - D_duty)),

    # =================================================================
    # BIGGER / INDUSTRIAL DC MOTOR
    # =================================================================
    "armature_reaction_demag_mmf": sp.Eq(F_ar, (Z_big * Ia_big * (1)) / (2 * n_poles * a_path)),
    "compensating_winding_mmf": sp.Eq(F_cm, F_ar),
    "interpole_mmf": sp.Eq(F_ip, F_ar + (Z_big * Ia_big) / (2 * n_poles * a_path)),
    "equalizer_ring_current": sp.Eq(N_eq_cur, Ia_big / n_poles),
    "series_motor_emf": sp.Eq(E_series, V - Ia_big * (R + R_regulator)),
    "shunt_motor_speed_regulation": sp.Eq(SpeedReg_dc, (omega - omega_s) / omega_s),

    # =================================================================
    # UNIVERSAL CROSS-CUTTING TOOLKIT
    # =================================================================
    "natural_frequency": sp.Eq(omega_n, sp.sqrt(k_stiff / m_sys)),
    "damping_ratio": sp.Eq(zeta_damp, c_damp / (2 * sp.sqrt(k_stiff * m_sys))),
    "goodman_fatigue_criterion": sp.Eq(n_safety, 1 / (sigma_a / Se_endurance + sigma_m / Sut_ultimate)),
    "convection_heat_transfer": sp.Eq(Q, h_conv * A * (T_temp - T_amb)),
    "nusselt_number": sp.Eq(Nu_nusselt, (h_conv * Lc_char) / k_thermal_cond),
    "biot_number": sp.Eq(Bi_biot, (h_conv * Lc_char) / k_thermal_cond),

    # =================================================================
    # PID CONTROL
    # =================================================================
    "pid_control_output": sp.Eq(u_pid, Kp_pid * e_err + Ki_pid * e_err * t_time + Kd_pid * e_err / t_time),
    "second_order_overshoot": sp.Eq(Mp_overshoot, sp.exp((-zeta_2nd * sp.pi) / sp.sqrt(1 - zeta_2nd ** 2))),
    "second_order_settling_time": sp.Eq(ts_settling, 4 / (zeta_2nd * omega_n_2nd)),
    "steady_state_error_ramp": sp.Eq(ess_error, 1 / Kp_pid),

    # =================================================================
    # INDUCTION MOTOR: test / nameplate depth
    # =================================================================
    "no_load_power_factor_im": sp.Eq(pf0_im, P0_test_im / (sp.sqrt(3) * V0_test_im * I0_test_im)),
    "blocked_rotor_impedance_im": sp.Eq(Z01_im, Vsc_test_im / (sp.sqrt(3) * Isc_test_im)),
    "full_load_slip_im": sp.Eq(s_fl_im, (N_synch_fl - N_fl_im) / N_synch_fl),
    "efficiency_partial_load_im": sp.Eq(eta_partial_im, (load_frac_im * P_out_im) / (load_frac_im * P_out_im + P_scl * load_frac_im ** 2 + P_i_t)),
    "deep_bar_resistance_ratio_im": sp.Eq(k_deepbar_im, R2_deep / R2_ac_im),

    # =================================================================
    # STRENGTH OF MATERIALS / BEAM BENDING
    # =================================================================
    "bending_stress": sp.Eq(sigma_bend, (M_bend * c_dist) / I_area),
    "section_modulus": sp.Eq(Z_section, I_area / c_dist),
    "beam_deflection_center_load": sp.Eq(delta_beam, (F_beam * Lspan_beam ** 3) / (48 * E_mod * I_area)),
    "euler_buckling_load": sp.Eq(P_euler, (sp.pi ** 2 * E_mod * I_area) / Le_col ** 2),
    "radius_of_gyration": sp.Eq(k_gyr, sp.sqrt(I_area / A)),
    "von_mises_stress": sp.Eq(sigma_vm, sp.sqrt(sigma_x ** 2 - sigma_x * sigma_y + sigma_y ** 2 + 3 * tau_xy ** 2)),
    "stress_concentration": sp.Eq(sigma_principal, Kt_stress * sigma_bend),
    "hookes_law": sp.Eq(sigma_bend, E_mod * epsilon_strain),
    "poissons_ratio": sp.Eq(nu_poisson, -epsilon_strain / (sigma_bend / E_mod)),
    "thermal_expansion": sp.Eq(dL_therm, alpha_therm * Lspan_beam * (T_temp - T0_therm)),

    # =================================================================
    # SHAFT DYNAMICS (extends existing shaft domain)
    # =================================================================
    "shaft_deflection_bending": sp.Eq(delta_shaft, (F_beam * Lspan_beam ** 3) / (48 * E_mod * J_polar)),
    "shaft_critical_speed": sp.Eq(N_crit_shaft, (30 / sp.pi) * sp.sqrt(k_stiff / m_sys)),
    "asme_shaft_combined_stress": sp.Eq(tau_m_shaft, (16 / (sp.pi * d ** 3)) * sp.sqrt((Kf_shaft * M_bend) ** 2 + (T * 1) ** 2)),
    "key_shear_stress": sp.Eq(tau_key, F_key / A_key),

    # =================================================================
    # HYDRAULIC DEPTH
    # =================================================================
    "npsh_available": sp.Eq(NPSH_avail, h_atm - h_vap - h_suction - h_fric_suction),
    "cavitation_number": sp.Eq(Ca_cav, (P_hyd - h_vap) / (sp.Rational(1, 2) * rho_hyd * v_hyd ** 2)),
    "water_hammer_pressure": sp.Eq(P_dp_shock, rho_hyd * a_wave * v_hyd),
    "wave_speed_bulk_modulus": sp.Eq(a_wave, sp.sqrt(K_bulk / rho_hyd)),
    "orifice_flow": sp.Eq(Q_orifice, Cd_orifice * A_orifice * sp.sqrt(2 * g_grav * h_hyd)),
    "pump_specific_speed": sp.Eq(N_ss_pump, (N_pump * sp.sqrt(Q_pump)) / h_hyd ** sp.Rational(3, 4)),
    "affinity_law_flow": sp.Eq(Q_aff, Q_pump * (N_aff / N_pump)),
    "affinity_law_head": sp.Eq(H_aff, h_hyd * (N_aff / N_pump) ** 2),
    "torricellis_law": sp.Eq(v_torricelli, sp.sqrt(2 * g_grav * h_torricelli)),
    "manometer_pressure": sp.Eq(P_manometer, rho_manometer * g_grav * h_manometer),
    "buoyancy_force": sp.Eq(F_buoy, rho_fluid_b * g_grav * Vol_disp),
    "hydrostatic_pressure": sp.Eq(P_depth, rho_hyd * g_grav * h_hyd),

    # =================================================================
    # ELECTRONICS DEPTH
    # =================================================================
    "wheatstone_bridge_balance": sp.Eq(R1_bridge, (R2_bridge * R3_bridge) / R4_bridge),
    "voltage_divider": sp.Eq(Vdiv_out, Vdiv_in * (R2_div / (R1_div + R2_div))),
    "555_timer_astable_frequency": sp.Eq(f_555, sp.Rational(144, 100) / ((R_555a + 2 * R_555b) * C_555)),
    "instrumentation_amp_gain": sp.Eq(Av_instr, 1 + (2 * Rf_opamp) / Rg_instr),
    "zener_regulator_current": sp.Eq(Iz_zener, (Vdiv_in - Vz_zener) / Rz_zener),
    "class_a_amplifier_efficiency": sp.Eq(eta_classA, sp.Rational(25, 100)),
    "class_b_amplifier_efficiency": sp.Eq(eta_classB, sp.pi / 4),
    "gate_propagation_delay": sp.Eq(t_pd_gate, C_load_gate * V_swing_gate / I_max),
    "digital_clock_period": sp.Eq(T_clk_digital, 1 / f_clk_digital),
    "cmos_dynamic_power": sp.Eq(P_dyn_cmos, C_load_cmos * V_dd_cmos ** 2 * f_sw_cmos),

    # =================================================================
    # THERMAL DEPTH
    # =================================================================
    "fouriers_law_conduction": sp.Eq(q_fourier, -k_cond * A_cond_area * dT_dx),
    "stefan_boltzmann_radiation": sp.Eq(q_rad, eps_rad * sigma_sb * A * (T_hot_rad ** 4 - T_cold_rad ** 4)),
    "thermal_resistance_series": sp.Eq(R_th_series, R_th + R_regulator),
    "thermal_resistance_parallel": sp.Eq(R_th_parallel, (R_th * R_regulator) / (R_th + R_regulator)),
    "log_mean_temp_difference": sp.Eq(LMTD_hx, (dT1_hx - dT2_hx) / sp.log(dT1_hx / dT2_hx)),

    # =================================================================
    # CONTROL SYSTEMS
    # =================================================================
    "closed_loop_transfer_function": sp.Eq(T_cl, G_ol / (1 + G_ol * H_fb)),
    "gain_margin_db": sp.Eq(Gm_margin, -20 * sp.log(G_ol, 10)),
    "dc_gain": sp.Eq(K_dc_gain, G_ol / (1 + G_ol * H_fb)),

    # =================================================================
    # TRANSFORMER / SYNCHRONOUS DEPTH
    # =================================================================
    "autotransformer_saving": sp.Eq(VA_auto, K_auto_save * (P_in_t)),
    "per_unit_impedance": sp.Eq(Z_pu, Z_base / (V_base ** 2 / S_base)),
    "synchronous_voltage_regulation_pct": sp.Eq(VR_sync_pct, ((E_sync - V_sync) / V_sync) * 100),
    "short_circuit_ratio": sp.Eq(SCR_sync, 1 / Xs_sync),

    # =================================================================
    # BATTERY ELECTROCHEMISTRY (extends ESP32's battery_life)
    # =================================================================
    "peukerts_law": sp.Eq(t_peukert, C_peukert / I_peukert ** k_peukert),
    "battery_voltage_sag": sp.Eq(V_sag, I_batt * R_int_batt),
    "battery_thermal_derating": sp.Eq(C_derated, C_battery * (1 - alpha_batt * (T_batt_amb - 25))),
    "state_of_charge": sp.Eq(SoC_batt, 1 - Q_used / Q_rated),
    "c_rate": sp.Eq(C_rate_batt, I_rate_batt / C_ah_batt),
    "battery_energy_wh": sp.Eq(E_batt_wh, V_nom_batt * C_ah_batt),
    "battery_specific_energy": sp.Eq(E_specific_batt, E_batt_wh / m_batt),
    "battery_cycle_life": sp.Eq(N_cycles_batt, k_cycle / DoD_batt),

    # =================================================================
    # FATIGUE / MATERIALS DEPTH
    # =================================================================
    "miners_rule": sp.Eq(D_miner, n_cycles_i / N_cycles_i),
    "sn_curve_life": sp.Eq(Nf_life, (Sf_life / a_sn) ** (1 / b_sn)),
    "marin_corrected_endurance": sp.Eq(Se_corrected, ka_surf * kb_size * Se_endurance),

    # =================================================================
    # VIBRATION DEPTH
    # =================================================================
    "forced_vibration_amplitude": sp.Eq(X_forced, F0_forced / (k_stiff * sp.sqrt((1 - r_freq_ratio ** 2) ** 2 + (2 * zeta_damp * r_freq_ratio) ** 2))),
    "transmissibility_ratio": sp.Eq(TR_transmis, sp.sqrt((1 + (2 * zeta_damp * r_freq_ratio) ** 2) / ((1 - r_freq_ratio ** 2) ** 2 + (2 * zeta_damp * r_freq_ratio) ** 2))),
    "logarithmic_decrement": sp.Eq(delta_log, sp.log(x1_log / x2_log)),
    "critical_damping_coefficient": sp.Eq(c_crit_damp, 2 * sp.sqrt(k_stiff * m_sys)),

    # =================================================================
    # SINGLE-PHASE AC POWER
    # =================================================================
    "single_phase_real_power": sp.Eq(P_1ph, V_1ph * I_1ph * pf_1ph),
    "single_phase_reactive_power": sp.Eq(Q_1ph, V_1ph * I_1ph * sp.sin(sp.acos(pf_1ph))),
    "single_phase_apparent_power": sp.Eq(S_1ph, V_1ph * I_1ph),
    "sine_rms_value": sp.Eq(V_rms_sine, V_peak_sine / sp.sqrt(2)),
    "sine_peak_to_peak": sp.Eq(V_pp_sine, 2 * V_peak_sine),
    "crest_factor": sp.Eq(CF_crest, V_peak_sine / V_rms_sine),

    # =================================================================
    # DIGITAL LOGIC DEPTH
    # =================================================================
    "digital_fanout": sp.Eq(N_fanout, I_oh_fanout / I_ih_fanout),
    "noise_margin_high": sp.Eq(NM_high, V_oh_nm - V_ih_nm),
    "noise_margin_low": sp.Eq(NM_low, V_il_nm - V_ol_nm),
    "flip_flop_min_period": sp.Eq(T_clk_digital, t_clk_to_q + t_setup),

    # =================================================================
    # CHEMICAL KINETICS (Arrhenius -- general, extends battery thermal derating)
    # =================================================================
    "arrhenius_rate_constant": sp.Eq(k_rate, A_arrhenius * sp.exp(-Ea_arrhenius / (R_gas * T_kelvin))),

    # =================================================================
    # STRESS TRANSFORMATION
    # =================================================================
    "principal_stress_transform": sp.Eq(sigma_1_transform, (sigma_x + sigma_y) / 2 + sp.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy ** 2)),
    "principal_stress_transform_min": sp.Eq(sigma_2_transform, (sigma_x + sigma_y) / 2 - sp.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy ** 2)),
    "principal_stress_angle": sp.Eq(theta_transform, sp.atan((2 * tau_xy) / (sigma_x - sigma_y)) / 2),

    # =================================================================
    # MORE POWER ELECTRONICS
    # =================================================================
    "flyback_converter_ratio": sp.Eq(Vout_flyback, Vin_flyback * N_flyback * (D_flyback / (1 - D_flyback))),

    # =================================================================
    # RF MATCHING / VSWR
    # =================================================================
    "reflection_coefficient": sp.Eq(Gamma_refl, (ZL_rf - Z0_rf) / (ZL_rf + Z0_rf)),
    "vswr": sp.Eq(VSWR_rf, (1 + Gamma_refl) / (1 - Gamma_refl)),
    "return_loss_db": sp.Eq(RL_db, -20 * sp.log(Gamma_refl, 10)),
    "quarter_wave_transformer": sp.Eq(Z_qw, sp.sqrt(Z0_rf * ZL_rf)),

    # =================================================================
    # CONTROL-LOOP TUNING (Ziegler-Nichols)
    # =================================================================
    "ziegler_nichols_kp": sp.Eq(Kp_zn, sp.Rational(6, 10) * Ku_zn),
    "ziegler_nichols_ti": sp.Eq(Ti_zn, Pu_zn / 2),
    "ziegler_nichols_td": sp.Eq(Td_zn, Pu_zn / 8),

    # =================================================================
    # HEAT EXCHANGER EFFECTIVENESS-NTU
    # =================================================================
    "heat_exchanger_effectiveness": sp.Eq(eps_hx, Qactual_hx / Qmax_hx),
    "heat_exchanger_qmax": sp.Eq(Qmax_hx, Cmin_hx * (T_hot_rad - T_cold_rad)),
    "heat_exchanger_ntu": sp.Eq(NTU_hx, UA_hx / Cmin_hx),

    # =================================================================
    # PIPE PUMPING POWER / ROTATING UNBALANCE
    # =================================================================
    "pumping_power_required": sp.Eq(P_pump_hyd, (rho_hyd * g_grav * Q_hyd * h_hyd) / eta_overall_hyd),
    "specific_gravity": sp.Eq(gamma_sg, rho_hyd / 1000),
    "rotating_unbalance_response": sp.Eq(X_unbalance, (me_unbalance * r_freq_ratio ** 2) / (M_total_unbalance * sp.sqrt((1 - r_freq_ratio ** 2) ** 2 + (2 * zeta_damp * r_freq_ratio) ** 2))),

    # =================================================================
    # CIVIL / STRUCTURAL
    # =================================================================
    "concrete_moment_capacity": sp.Eq(M_conc, As_conc * fy_conc * (d_conc - a_conc / 2)),
    "concrete_stress_block_depth": sp.Eq(a_conc, (As_conc * fy_conc) / (sp.Rational(85, 100) * fc_conc * b_conc)),
    "reinforcement_ratio": sp.Eq(rho_conc, As_conc / (b_conc * d_conc)),
    "rankine_active_pressure_coeff": sp.Eq(ka_rankine, (1 - sp.sin(phi_soil)) / (1 + sp.sin(phi_soil))),
    "rankine_active_force": sp.Eq(Pa_rankine, sp.Rational(1, 2) * ka_rankine * gamma_soil * H_wall ** 2),
    "column_axial_stress": sp.Eq(sigma_allow_col, F_axial_col / A_col),
    "udl_max_moment": sp.Eq(M_max_udl, w_udl * L_beam ** 2 / 8),
    "udl_max_shear": sp.Eq(V_max_udl, w_udl * L_beam / 2),
    "udl_max_deflection": sp.Eq(delta_udl, (5 * w_udl * L_beam ** 4) / (384 * E_mod * I_area)),

    # =================================================================
    # WELDING / JOINTS
    # =================================================================
    "fillet_weld_stress": sp.Eq(tau_weld, F_weld / (throat_weld * L_weld)),
    "weld_throat_thickness": sp.Eq(throat_weld, sp.Rational(707, 1000) * t_weld),
    "butt_weld_stress": sp.Eq(sigma_butt, F_butt / (t_butt * L_butt)),
    "rivet_shear_stress": sp.Eq(tau_rivet, F_rivet / (n_rivets * sp.pi / 4 * d_rivet ** 2)),
    "bolt_joint_stiffness_ratio": sp.Eq(C_bolt, k_bolt / (k_bolt + k_member)),
    "bolt_total_load": sp.Eq(F_bolt_total, F_bolt_preload + C_bolt * F_ext_bolt),

    # =================================================================
    # BEARINGS DEPTH / CLUTCHES / BRAKES / FLYWHEELS / CAMS
    # =================================================================
    "bearing_equivalent_load": sp.Eq(P_equiv_bear, X_radial * Fr_bear + Y_thrust * Fa_bear),
    "clutch_torque_capacity": sp.Eq(T_clutch, n_surfaces * mu_clutch * F_axial_clutch * R_mean_clutch),
    "disc_brake_torque": sp.Eq(T_brake, mu_brake * F_brake * R_brake),
    "band_brake_tension": sp.Eq(F1_band, F2_band * sp.exp(mu_band * theta_band_wrap)),
    "band_brake_torque": sp.Eq(T_band, (F1_band - F2_band) * R_brake),
    "flywheel_energy_fluctuation": sp.Eq(E_fly, sp.Rational(1, 2) * J_fly * (omega1_fly ** 2 - omega2_fly ** 2)),
    "coefficient_of_fluctuation": sp.Eq(Cs_fly, (omega1_fly - omega2_fly) / omega_mean_fly),
    "cam_shm_displacement": sp.Eq(y_cam, (h_cam / 2) * (1 - sp.cos(sp.pi * theta_cam / beta_cam))),
    "cam_shm_velocity": sp.Eq(v_cam, (sp.pi * h_cam / (2 * beta_cam)) * sp.sin(sp.pi * theta_cam / beta_cam)),

    # =================================================================
    # PRESSURE VESSELS
    # =================================================================
    "thin_cylinder_hoop_stress": sp.Eq(sigma_hoop, (P_internal * D_vessel) / (2 * t_vessel)),
    "thin_cylinder_longitudinal_stress": sp.Eq(sigma_long, (P_internal * D_vessel) / (4 * t_vessel)),
    "thin_sphere_stress": sp.Eq(sigma_sphere, (P_internal * D_vessel) / (4 * t_vessel)),

    # =================================================================
    # CHEMICAL ENGINEERING
    # =================================================================
    "gibbs_free_energy": sp.Eq(G_gibbs, H_enthalpy - T_kelvin * S_entropy),
    "enthalpy_from_internal_energy": sp.Eq(dH_rxn, dU_rxn + P_chem * dV_rxn),
    "first_order_reaction": sp.Eq(Ca_conc, Ca0_conc * sp.exp(-k_rate * t_rxn)),
    "ficks_law_diffusion": sp.Eq(N_flux, -D_diff * dC_dx),
    "overall_heat_transfer_coeff": sp.Eq(U_overall_hx, 1 / (1 / h1_hx + 1 / h2_hx + Rf_fouling)),
    "relative_volatility": sp.Eq(alpha_volatility, (y_vap / (1 - y_vap)) / (x_liq / (1 - x_liq))),
    "isentropic_compressor_work": sp.Eq(W_compressor, (n_moles_gas * R_gas_const * T1_gas * gamma_gas / (gamma_gas - 1)) * ((P2_gas / P1_gas) ** ((gamma_gas - 1) / gamma_gas) - 1)),
    "corrosion_rate_mpy": sp.Eq(CR_corrosion, (mpy_const * W_loss_corr) / (rho_corr * A_corr * t_corr)),
    "ideal_gas_law": sp.Eq(P_ideal, n_ideal * R_ideal * T_ideal / V_ideal),
    "sensible_heat_rate": sp.Eq(Q_dot_hx, m_dot_hx * cp_hx * dT_hx),

    # =================================================================
    # AEROSPACE / AERODYNAMICS
    # =================================================================
    "lift_equation": sp.Eq(L_lift, sp.Rational(1, 2) * Cl_lift * rho_air * V_air ** 2 * S_wing),
    "drag_equation": sp.Eq(D_drag, sp.Rational(1, 2) * Cd_drag * rho_air * V_air ** 2 * S_wing),
    "thrust_equation": sp.Eq(T_thrust_jet, m_dot_air * (Ve_exhaust - V0_inlet)),
    "breguet_range_equation": sp.Eq(R_range_breguet, (V_cruise * L_D_ratio / sfc_engine) * sp.log(W1_fuel / W2_fuel)),
    "stall_speed": sp.Eq(V_stall, sp.sqrt((2 * W_aircraft) / (rho_air * S_wing * Cl_max))),

    # =================================================================
    # HVAC / REFRIGERATION
    # =================================================================
    "coefficient_of_performance": sp.Eq(COP_refrig, Qc_refrig / Wc_refrig),
    "heat_pump_cop": sp.Eq(COP_heatpump, Qh_heatpump / Wc_refrig),
    "sensible_cooling_load": sp.Eq(Q_cooling_load, m_dot_air_hvac * cp_air_hvac * dT_hvac),
    "humidity_ratio": sp.Eq(W_humidity_ratio, sp.Rational(622, 1000) * Pv_vapor / (P_total_hvac - Pv_vapor)),
    "carnot_cop_refrigeration": sp.Eq(COP_carnot, Tc_carnot / (Th_carnot - Tc_carnot)),

    # =================================================================
    # RENEWABLE ENERGY
    # =================================================================
    "solar_pv_power": sp.Eq(P_pv, eta_pv * G_irradiance * A_pv),
    "wind_turbine_power": sp.Eq(P_wind, sp.Rational(1, 2) * Cp_betz * rho_air_wind * A_rotor * V_wind ** 3),
    "betz_limit": sp.Eq(Cp_betz_limit, sp.Rational(16, 27)),
    "pv_temperature_derating": sp.Eq(eta_pv_temp, 1 - beta_temp_pv * (T_cell_pv - T_ref_pv)),

    # =================================================================
    # ILLUMINATION ENGINEERING
    # =================================================================
    "lumen_method_illuminance": sp.Eq(E_illum, (F_lumen * UF_illum * MF_illum) / A_illum),
    "luminous_efficacy": sp.Eq(eta_luminous, F_lumen2 / P_lamp),

    # =================================================================
    # CABLE SIZING / POWER SYSTEM PROTECTION
    # =================================================================
    "cable_ampacity": sp.Eq(I_ampacity, J_current_density_cable * A_cable),
    "cable_voltage_drop": sp.Eq(VD_cable, I_cable * R_cable_per_km * L_cable_km),
    "fault_current": sp.Eq(I_fault, V_fault / Z_fault),
    "fault_mva": sp.Eq(MVA_fault, sp.sqrt(3) * V_fault_kv * I_fault_ka),
    "idmt_relay_time": sp.Eq(t_relay, (TMS_relay * k_relay_const) / (PSM_relay ** alpha_relay_const - 1)),

    # =================================================================
    # MANUFACTURING PROCESSES
    # =================================================================
    "cutting_speed": sp.Eq(Vc_cutting, sp.pi * D_workpiece * N_spindle / 1000),
    "material_removal_rate": sp.Eq(MRR_machining, Vc_cutting2 * f_feed * d_cut),
    "chvorinov_rule": sp.Eq(t_solidify, Cm_chvorinov * (Vol_casting / A_casting_surf) ** n_chvorinov),
    "true_stress": sp.Eq(sigma_true, sigma_eng * (1 + epsilon_eng)),
    "true_strain": sp.Eq(epsilon_true, sp.log(1 + epsilon_eng)),
    "taylor_tool_life": sp.Eq(T_tool_life, (C_taylor / Vc_cutting) ** (1 / n_taylor)),

    # =================================================================
    # STEPPER MOTORS
    # =================================================================
    "stepper_step_angle": sp.Eq(theta_step, 360 / N_steps_rev),
    "stepper_speed": sp.Eq(N_rpm_stepper, (f_step_rate * 60) / N_steps_rev),

    # =================================================================
    # TRANSFORMER DESIGN DEPTH (Sawhney)
    # =================================================================
    "window_space_factor": sp.Eq(Kw_window_factor, (N1_t * a_cond_wire) / Aw_window),
    "transformer_output_equation": sp.Eq(Q_rating_transformer, sp.Rational(222, 100) * f_trans * Bm_trans * delta_current_density_trans * Aw_window * Ai_core2 * Kw_trans2 * sp.Rational(1, 1000)),

    # =================================================================
    # THERMODYNAMIC CYCLES
    # =================================================================
    "carnot_efficiency": sp.Eq(eta_carnot, 1 - Tc_carnot / Th_carnot),
    "otto_cycle_efficiency": sp.Eq(eta_otto, 1 - (1 / r_compression) ** (gamma_gas - 1)),
    "diesel_cycle_efficiency": sp.Eq(eta_diesel, 1 - (1 / r_compression) ** (gamma_gas - 1) * (rc_cutoff_ratio ** gamma_gas - 1) / (gamma_gas * (rc_cutoff_ratio - 1))),
    "brayton_cycle_efficiency": sp.Eq(eta_brayton, 1 - (1 / r_pressure_ratio) ** ((gamma_gas - 1) / gamma_gas)),
    "rankine_steam_cycle_efficiency": sp.Eq(eta_rankine_steam, W_net_rankine / Q_in_rankine),
    "specific_fuel_consumption": sp.Eq(sfc_engine2, m_dot_fuel / P_engine_out),

    # =================================================================
    # INSTRUMENTATION
    # =================================================================
    "sensor_sensitivity": sp.Eq(S_sensor, dOutput_sensor / dInput_sensor),
    "measurement_error_pct": sp.Eq(err_pct, ((Measured_val - True_val) / True_val) * 100),
    "signal_to_noise_ratio_db": sp.Eq(SNR_db, 20 * sp.log(Vsignal_rms / Vnoise_rms, 10)),
    "instrument_gain_db": sp.Eq(Gain_db, 20 * sp.log(Vout_instr / Vin_instr, 10)),

    # =================================================================
    # FLUID MACHINERY DEPTH
    # =================================================================
    "specific_speed_pump": sp.Eq(Ns_pump, (N_pump2 * sp.sqrt(Q_pump2)) / H_pump2 ** sp.Rational(3, 4)),
    "impeller_tip_speed": sp.Eq(u2_impeller, sp.pi * D2_impeller * N_pump2 / 60),
    "euler_head_pump": sp.Eq(H_euler, (u2_impeller * Vu2_whirl) / g_grav),
}

# Domain tag for every formula -- lets the Brain report "Domains detected: ..."
# and lets /brain/understand narrow a natural-language query to the right
# neighborhood of the graph instead of searching all 52 formulas blindly.
FORMULA_DOMAINS = {
    "ohms_law": "electrical", "back_emf": "electrical", "torque": "mechanical",
    "power_electrical": "electrical", "power_mechanical": "mechanical", "heat_generated": "thermal",
    "efficiency": "electrical", "angular_velocity": "mechanical", "bearing_friction_torque": "mechanical",
    "flux_density": "magnetic", "rpm_conversion": "mechanical", "commutation_frequency": "electrical",
    "lorentz_force": "magnetic", "magnetic_flux": "magnetic", "reluctance": "magnetic",
    "cylinder_volume": "design", "mass_from_volume": "mechanical", "moment_of_inertia_cylinder": "mechanical",
    "kinetic_energy": "mechanical", "polar_moment": "mechanical", "shear_stress": "mechanical",
    "bearing_power_loss": "mechanical", "bearing_life_l10": "mechanical",
    "winding_torque_constant": "design", "rotor_shear_sizing": "design", "shaft_torsion": "mechanical",
    "commutator_peripheral_velocity": "mechanical", "brush_current_density": "electrical",
    "stator_yoke_thickness": "design", "resistance_temperature": "thermal",
    "flux_thermal_derating": "thermal", "thermal_rise_rc": "thermal",
    "severity_growth_asymptotic": "fault_pattern", "severity_growth_linear": "fault_pattern",
    "torque_ripple": "fault_pattern",
    "supply_current": "power", "voltage_drop": "power", "power_consumption": "power", "battery_life": "power",
    "chip_temperature": "thermal", "thermal_resistance": "thermal", "temperature_rise_rate": "thermal",
    "wavelength": "rf", "antenna_length_quarter_wave": "rf", "path_loss": "rf", "received_signal": "rf",
    "clock_period": "timing", "cpu_cycles_per_second": "timing", "instruction_time": "timing",
    "gpio_current": "gpio", "drive_strength": "gpio", "pull_resistor_current": "gpio",

    # --- induction motor ---
    "synchronous_speed": "induction_motor", "slip": "induction_motor", "rotor_speed_from_slip": "induction_motor",
    "rotor_frequency": "induction_motor", "rotor_emf_running": "induction_motor", "rotor_reactance_running": "induction_motor",
    "rotor_current_im": "induction_motor", "synchronous_angular_speed": "induction_motor", "torque_equation_im": "induction_motor",
    "max_torque_slip": "induction_motor", "breakdown_torque_im": "induction_motor", "starting_torque_im": "induction_motor",
    "air_gap_power": "induction_motor", "rotor_copper_loss_im": "induction_motor", "mech_power_developed": "induction_motor",
    "output_power_im": "induction_motor", "stator_copper_loss_im": "induction_motor", "input_power_3phase_im": "induction_motor",
    "power_factor_im": "induction_motor", "efficiency_im": "induction_motor", "star_delta_current_ratio": "induction_motor",
    "star_delta_torque_ratio": "induction_motor", "output_equation_im": "induction_motor", "specific_magnetic_loading_im": "induction_motor",
    "slot_pitch_im": "induction_motor", "air_gap_length_im": "induction_motor", "turns_per_phase_im": "induction_motor",
    "current_density_conductor_im": "induction_motor", "specific_electric_loading_im": "induction_motor",
    "no_load_power_factor_im": "induction_motor", "blocked_rotor_impedance_im": "induction_motor", "full_load_slip_im": "induction_motor",
    "efficiency_partial_load_im": "induction_motor", "deep_bar_resistance_ratio_im": "induction_motor",

    # --- transformers ---
    "transformer_turns_ratio": "transformer", "transformer_voltage_ratio": "transformer",
    "transformer_current_ratio": "transformer", "transformer_emf_equation": "transformer",
    "transformer_voltage_regulation": "transformer", "transformer_copper_loss": "transformer",
    "transformer_efficiency": "transformer", "transformer_input_power": "transformer",
    "autotransformer_saving": "transformer", "per_unit_impedance": "transformer",

    # --- synchronous machines ---
    "synchronous_emf_equation": "synchronous_machine", "synchronous_power_developed": "synchronous_machine",
    "synchronous_max_power": "synchronous_machine", "synchronous_armature_current": "synchronous_machine",
    "synchronous_voltage_regulation_pct": "synchronous_machine", "short_circuit_ratio": "synchronous_machine",

    # --- three-phase / single-phase power ---
    "three_phase_power": "power_systems", "three_phase_reactive_power": "power_systems",
    "three_phase_apparent_power": "power_systems", "star_line_phase_voltage": "power_systems",
    "delta_line_phase_current": "power_systems", "power_factor_correction_capacitor": "power_systems",
    "single_phase_real_power": "power_systems", "single_phase_reactive_power": "power_systems",
    "single_phase_apparent_power": "power_systems", "sine_rms_value": "power_systems",
    "sine_peak_to_peak": "power_systems", "crest_factor": "power_systems",

    # --- hydraulics ---
    "pascals_law": "hydraulics", "continuity_equation": "hydraulics", "bernoulli_head": "hydraulics",
    "reynolds_number": "hydraulics", "darcy_weisbach_head_loss": "hydraulics", "minor_head_loss": "hydraulics",
    "pump_flow_rate": "hydraulics", "pump_volumetric_efficiency": "hydraulics", "pump_overall_efficiency": "hydraulics",
    "hydraulic_power": "hydraulics", "pump_torque": "hydraulics", "valve_flow_coefficient": "hydraulics",
    "cylinder_force": "hydraulics", "cylinder_speed": "hydraulics", "accumulator_gas_law": "hydraulics",
    "npsh_available": "hydraulics", "cavitation_number": "hydraulics", "water_hammer_pressure": "hydraulics",
    "wave_speed_bulk_modulus": "hydraulics", "orifice_flow": "hydraulics", "pump_specific_speed": "hydraulics",
    "affinity_law_flow": "hydraulics", "affinity_law_head": "hydraulics", "torricellis_law": "hydraulics",
    "manometer_pressure": "hydraulics", "buoyancy_force": "hydraulics", "hydrostatic_pressure": "hydraulics",

    # --- mechanical: gears, springs, belts, chains ---
    "gear_module": "mechanical_drives", "gear_ratio": "mechanical_drives", "gear_center_distance": "mechanical_drives",
    "gear_pitch_line_velocity": "mechanical_drives", "lewis_bending_stress": "mechanical_drives",
    "agma_bending_stress": "mechanical_drives", "spring_rate": "mechanical_drives", "spring_index": "mechanical_drives",
    "wahl_stress_factor": "mechanical_drives", "spring_shear_stress": "mechanical_drives",
    "belt_tension_ratio": "mechanical_drives", "belt_power_transmitted": "mechanical_drives",
    "chain_velocity": "mechanical_drives", "chain_sprocket_ratio": "mechanical_drives",

    # --- strength of materials / shaft dynamics ---
    "bending_stress": "materials", "section_modulus": "materials", "beam_deflection_center_load": "materials",
    "euler_buckling_load": "materials", "radius_of_gyration": "materials", "von_mises_stress": "materials",
    "stress_concentration": "materials", "hookes_law": "materials", "poissons_ratio": "materials",
    "thermal_expansion": "materials", "shaft_deflection_bending": "materials", "shaft_critical_speed": "materials",
    "asme_shaft_combined_stress": "materials", "key_shear_stress": "materials",
    "miners_rule": "materials", "sn_curve_life": "materials", "marin_corrected_endurance": "materials",

    # --- electronics ---
    "opamp_inverting_gain": "electronics", "opamp_noninverting_gain": "electronics", "opamp_bandwidth": "electronics",
    "rc_cutoff_frequency": "electronics", "diode_shockley_equation": "electronics", "bjt_current_gain": "electronics",
    "bjt_emitter_current": "electronics", "mosfet_drain_current_saturation": "electronics",
    "mosfet_transconductance": "electronics", "capacitor_ripple_voltage": "electronics",
    "buck_converter_ratio": "electronics", "boost_converter_ratio": "electronics",
    "wheatstone_bridge_balance": "electronics", "voltage_divider": "electronics", "555_timer_astable_frequency": "electronics",
    "instrumentation_amp_gain": "electronics", "zener_regulator_current": "electronics",
    "class_a_amplifier_efficiency": "electronics", "class_b_amplifier_efficiency": "electronics",
    "gate_propagation_delay": "electronics", "digital_clock_period": "electronics", "cmos_dynamic_power": "electronics",

    # --- bigger / industrial DC motor ---
    "armature_reaction_demag_mmf": "dc_motor_industrial", "compensating_winding_mmf": "dc_motor_industrial",
    "interpole_mmf": "dc_motor_industrial", "equalizer_ring_current": "dc_motor_industrial",
    "series_motor_emf": "dc_motor_industrial", "shunt_motor_speed_regulation": "dc_motor_industrial",

    # --- universal cross-cutting toolkit ---
    "natural_frequency": "universal", "damping_ratio": "universal", "goodman_fatigue_criterion": "universal",
    "convection_heat_transfer": "universal", "nusselt_number": "universal", "biot_number": "universal",
    "fouriers_law_conduction": "universal", "stefan_boltzmann_radiation": "universal",
    "thermal_resistance_series": "universal", "thermal_resistance_parallel": "universal", "log_mean_temp_difference": "universal",
    "forced_vibration_amplitude": "universal", "transmissibility_ratio": "universal",
    "logarithmic_decrement": "universal", "critical_damping_coefficient": "universal",

    # --- control systems ---
    "pid_control_output": "control_systems", "second_order_overshoot": "control_systems",
    "second_order_settling_time": "control_systems", "steady_state_error_ramp": "control_systems",
    "closed_loop_transfer_function": "control_systems", "gain_margin_db": "control_systems", "dc_gain": "control_systems",

    # --- battery electrochemistry ---
    "peukerts_law": "battery_chemistry", "battery_voltage_sag": "battery_chemistry",
    "battery_thermal_derating": "battery_chemistry", "state_of_charge": "battery_chemistry",
    "c_rate": "battery_chemistry", "battery_energy_wh": "battery_chemistry",
    "battery_specific_energy": "battery_chemistry", "battery_cycle_life": "battery_chemistry",

    "digital_fanout": "electronics", "noise_margin_high": "electronics", "noise_margin_low": "electronics",
    "flip_flop_min_period": "electronics",
    "arrhenius_rate_constant": "chemistry",
    "principal_stress_transform": "materials", "principal_stress_transform_min": "materials", "principal_stress_angle": "materials",
    "flyback_converter_ratio": "electronics",
    "reflection_coefficient": "rf", "vswr": "rf", "return_loss_db": "rf", "quarter_wave_transformer": "rf",
    "ziegler_nichols_kp": "control_systems", "ziegler_nichols_ti": "control_systems", "ziegler_nichols_td": "control_systems",
    "heat_exchanger_effectiveness": "universal", "heat_exchanger_qmax": "universal", "heat_exchanger_ntu": "universal",
    "pumping_power_required": "hydraulics", "specific_gravity": "hydraulics", "rotating_unbalance_response": "universal",

    "concrete_moment_capacity": "civil_structural", "concrete_stress_block_depth": "civil_structural",
    "reinforcement_ratio": "civil_structural", "rankine_active_pressure_coeff": "civil_structural",
    "rankine_active_force": "civil_structural", "column_axial_stress": "civil_structural",
    "udl_max_moment": "civil_structural", "udl_max_shear": "civil_structural", "udl_max_deflection": "civil_structural",

    "fillet_weld_stress": "welding_joints", "weld_throat_thickness": "welding_joints",
    "butt_weld_stress": "welding_joints", "rivet_shear_stress": "welding_joints",
    "bolt_joint_stiffness_ratio": "welding_joints", "bolt_total_load": "welding_joints",

    "bearing_equivalent_load": "mechanical_drives", "clutch_torque_capacity": "mechanical_drives",
    "disc_brake_torque": "mechanical_drives", "band_brake_tension": "mechanical_drives",
    "band_brake_torque": "mechanical_drives", "flywheel_energy_fluctuation": "mechanical_drives",
    "coefficient_of_fluctuation": "mechanical_drives", "cam_shm_displacement": "mechanical_drives",
    "cam_shm_velocity": "mechanical_drives",

    "thin_cylinder_hoop_stress": "pressure_vessels", "thin_cylinder_longitudinal_stress": "pressure_vessels",
    "thin_sphere_stress": "pressure_vessels",

    "gibbs_free_energy": "chemistry", "enthalpy_from_internal_energy": "chemistry",
    "first_order_reaction": "chemistry", "ficks_law_diffusion": "chemistry",
    "overall_heat_transfer_coeff": "chemistry", "relative_volatility": "chemistry",
    "isentropic_compressor_work": "chemistry", "corrosion_rate_mpy": "chemistry",
    "ideal_gas_law": "chemistry", "sensible_heat_rate": "chemistry",

    "lift_equation": "aerospace", "drag_equation": "aerospace", "thrust_equation": "aerospace",
    "breguet_range_equation": "aerospace", "stall_speed": "aerospace",

    "coefficient_of_performance": "hvac_refrigeration", "heat_pump_cop": "hvac_refrigeration",
    "sensible_cooling_load": "hvac_refrigeration", "humidity_ratio": "hvac_refrigeration",
    "carnot_cop_refrigeration": "hvac_refrigeration",

    "solar_pv_power": "renewable_energy", "wind_turbine_power": "renewable_energy",
    "betz_limit": "renewable_energy", "pv_temperature_derating": "renewable_energy",

    "lumen_method_illuminance": "illumination", "luminous_efficacy": "illumination",

    "cable_ampacity": "power_systems", "cable_voltage_drop": "power_systems",
    "fault_current": "power_systems", "fault_mva": "power_systems", "idmt_relay_time": "power_systems",

    "cutting_speed": "manufacturing", "material_removal_rate": "manufacturing",
    "chvorinov_rule": "manufacturing", "true_stress": "manufacturing",
    "true_strain": "manufacturing", "taylor_tool_life": "manufacturing",

    "stepper_step_angle": "electrical", "stepper_speed": "electrical",

    "window_space_factor": "transformer", "transformer_output_equation": "transformer",

    "carnot_efficiency": "thermodynamic_cycles", "otto_cycle_efficiency": "thermodynamic_cycles",
    "diesel_cycle_efficiency": "thermodynamic_cycles", "brayton_cycle_efficiency": "thermodynamic_cycles",
    "rankine_steam_cycle_efficiency": "thermodynamic_cycles", "specific_fuel_consumption": "thermodynamic_cycles",

    "sensor_sensitivity": "instrumentation", "measurement_error_pct": "instrumentation",
    "signal_to_noise_ratio_db": "instrumentation", "instrument_gain_db": "instrumentation",

    "specific_speed_pump": "hydraulics", "impeller_tip_speed": "hydraulics", "euler_head_pump": "hydraulics",
}


def mynja(formula_name, known_values, solve_for):
    """
    Look up `formula_name` in FORMULAS, substitute `known_values`
    (dict of symbol-name -> number), and solve for `solve_for`.
    Returns a float rounded to 6 decimal places, or None on failure.
    """
    try:
        formula = FORMULAS[formula_name]
        subs_dict = {sp.Symbol(k): v for k, v in known_values.items()}
        equation = formula.subs(subs_dict)
        target = sp.Symbol(solve_for)
        solutions = sp.solve(equation, target)
        if not solutions:
            print(f"mynja: no solution found for '{solve_for}' in '{formula_name}'")
            return None
        result = complex(solutions[0])
        if abs(result.imag) > 1e-9:
            print(f"mynja: complex result for '{solve_for}' in '{formula_name}': {result}")
            return None
        return round(float(result.real), 6)
    except Exception as e:
        print(f"mynja error in '{formula_name}' solving for '{solve_for}': {e}")
        return None
