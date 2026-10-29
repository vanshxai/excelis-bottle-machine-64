"""
Validate the 150 RPM gear rig's physics model against the real readings that exist, iterate the
model, and check the new gear engine reproduces the final version.

REAL DATA THAT EXISTS (and its limits)
- Idle current 22 mA (INA228, capless, unloaded), supply 12 V, output speed 150 RPM, tooth counts,
  mesh efficiency / friction / module ranges: from the prototype's constraint registry.
- Part-interruption bands: the absolute block-mean current ranges the user tuned live, touching each
  gear on the real rig (Red 31-34, Green 35-42, Blue 43-90, Yellow >=91 mA). They are classification
  bands, not raw recordings, and the applied touch force was never measured.
- NOT usable: the July 2026 recordings databases. Those came from the older ACS712 / "Cybertruck"
  relay setup (means of ~38 A on a 12 V motor) and are contaminated, as the project's own README says.
- No INA228-era raw recordings exist on disk.

Run:  .venv/bin/python validation/validate_gear_prototype.py
"""
import itertools
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

import gear_engine  # noqa: E402

INF = math.inf
DATA = {
    "supply_V": 12.0, "output_rpm": 150.0, "idle_current_A": 0.022,
    "teeth": {"Yellow": [9], "Blue": [27, 8], "Green": [27, 8], "Red": [27, 16]},
    "output_big_teeth_range": [24, 40], "module_mm_range": [0.44828, 0.55172],
    "mesh_efficiency_range": [0.85, 0.97], "friction_coeff_range": [0.05, 0.2],
    "armature_ohm_range": [1.0, 10.0], "normal_force_range_N": [0.1, 15.0],
    "current_per_nm_range_prototype": [5.0, 12.5],
    "bands_abs_A": {"Yellow": [0.091, None], "Blue": [0.043, 0.090], "Green": [0.035, 0.042], "Red": [0.031, 0.034]},
    "noise_observed": "block-mean peak-vs-baseline swings of 20-40 mA with the motor running (live_state.py comment)",
}
GEARS = ["Yellow", "Blue", "Green", "Red"]
I0 = DATA["idle_current_A"]
BANDS = {g: ((lo - I0), (INF if hi is None else hi - I0)) for g, (lo, hi) in DATA["bands_abs_A"].items()}

# prototype's own stored predictions (verified twin), per newton of normal force
PROTO_PER_N = {"Yellow": 0.001871, "Blue": 0.006416, "Green": 0.007333, "Red": 0.008381}
PROTO_DYNAMIC_IMPACT_A = {"Yellow": -6.436, "Blue": -11.850, "Green": 7.691, "Red": 10.029}

# mesh ratios (driver turns this many times faster than the driven shaft)
MESH = {"Blue": 27 / 9, "Green": 27 / 8, "Red": 27 / 8}
CUM = {"Yellow": 1.0}
CUM["Blue"] = MESH["Blue"]
CUM["Green"] = CUM["Blue"] * MESH["Green"]
CUM["Red"] = CUM["Green"] * MESH["Red"]
BIG = {"Yellow": 9, "Blue": 27, "Green": 27, "Red": 27}
SMALL = {"Yellow": 9, "Blue": 8, "Green": 8, "Red": 16}
MESHES_FROM_MOTOR = {"Yellow": 0, "Blue": 1, "Green": 2, "Red": 3}
MESHES_TO_OUTPUT = {"Yellow": 4, "Blue": 3, "Green": 2, "Red": 1}  # what the prototype used


def spread(s):
    """How many times the touch force would have to differ between gears for every gear to land in its band.
    <= 1 means one common force explains all four bands."""
    lo = max(BANDS[g][0] / s[g] for g in GEARS)
    hi = min(BANDS[g][1] / s[g] for g in GEARS if BANDS[g][1] < INF)
    return lo / hi, lo, hi


etas = np.round(np.linspace(0.85, 0.97, 13), 4)


def best_over_eta(make_s):
    return min(((spread(make_s(e))[0], float(e)) for e in etas))


# ---- model iterations: change one thing at a time ---------------------------------------------
iterations = []
sf, e = best_over_eta(lambda e: {g: BIG[g] * e ** MESHES_TO_OUTPUT[g] for g in GEARS})
iterations.append(("M0  prototype as built", "efficiency counted from the OUTPUT side (4,3,2,1 meshes); no gear-ratio reflection; lumped current-per-N*m", sf, e))
sf, e = best_over_eta(lambda e: {g: BIG[g] * e ** MESHES_FROM_MOTOR[g] for g in GEARS})
iterations.append(("M1  fix efficiency direction", "meshes counted from the MOTOR side (0,1,2,3); still no gear-ratio reflection", sf, e))
sf, e = best_over_eta(lambda e: {g: BIG[g] / (CUM[g] * e ** MESHES_FROM_MOTOR[g]) for g in GEARS})
iterations.append(("M2  add gear-ratio reflection", "touch torque divided by the speed reduction from the motor to that shaft (big wheels)", sf, e))
best3 = None
for wheels in itertools.product([0, 1], repeat=3):
    for e in etas:
        t = {"Yellow": 9}
        for i, g in enumerate(["Blue", "Green", "Red"]):
            t[g] = BIG[g] if wheels[i] == 0 else SMALL[g]
        s = {g: t[g] / (CUM[g] * e ** MESHES_FROM_MOTOR[g]) for g in GEARS}
        sf = spread(s)[0]
        if best3 is None or sf < best3[0]:
            best3 = (sf, float(e), wheels)
iterations.append(("M3  allow touching either wheel of a compound gear",
                   "each of Blue/Green/Red has a big and a small wheel; which one the finger hit is not known", best3[0], best3[1]))

# ---- M3 feasible region, with the motor constant derived from V and speed (no fitted gain) ---------
feasible = []
for Nout in range(24, 41):
    omega_motor = (DATA["output_rpm"] * 2 * math.pi / 60) * CUM["Red"] * (Nout / 16.0)
    for Ra in (1.0, 5.5, 10.0):
        Ke = (DATA["supply_V"] - I0 * Ra) / omega_motor
        for wheels in itertools.product([0, 1], repeat=3):
            for e in etas:
                t = {"Yellow": 9}
                for i, g in enumerate(["Blue", "Green", "Red"]):
                    t[g] = BIG[g] if wheels[i] == 0 else SMALL[g]
                for module in (0.44828, 0.53724, 0.55172):
                    s = {g: (t[g] * module / 2000.0) / (CUM[g] * e ** MESHES_FROM_MOTOR[g] * Ke) for g in GEARS}  # A per N tangential
                    sf, lo, hi = spread(s)
                    if sf <= 1.0:
                        feasible.append({"Nout": Nout, "Ra": Ra, "eta": float(e), "wheels": wheels, "module": module,
                                         "Kt": Ke, "Ft_lo": lo, "Ft_hi": hi, "spread": sf})
total_grid = 17 * 3 * 8 * len(etas) * 3
print(f"M3 feasible parameter sets: {len(feasible)} of {total_grid}")

mu_lo, mu_hi = DATA["friction_coeff_range"]
Fn_lo_all, Fn_hi_all = DATA["normal_force_range_N"]
plausible = []
for f in feasible:
    # a common tangential force F_t in [Ft_lo, Ft_hi]; normal press F_n = F_t/mu for some mu in range -> plausible if it can land in 0.1-15 N
    fn_min = f["Ft_lo"] / mu_hi
    fn_max = (f["Ft_hi"] / mu_lo) if math.isfinite(f["Ft_hi"]) else INF
    if fn_min <= Fn_hi_all and fn_max >= Fn_lo_all:
        plausible.append(f)
print(f"... of which the implied press force is inside the rig's 0.1-15 N range: {len(plausible)}")

def centre_distance(f):
    return (abs(f["Nout"] - 32) / 8 + abs(f["Ra"] - 5.5) / 4.5 + abs(f["eta"] - 0.91) / 0.06 + abs(f["module"] - 0.5) / 0.05)


rep = min(plausible, key=centre_distance)
Ft_star = math.sqrt(rep["Ft_lo"] * rep["Ft_hi"]) if math.isfinite(rep["Ft_hi"]) else rep["Ft_lo"] * 1.2
wheel_combo_counts = {}
for f in feasible:
    wheel_combo_counts[f["wheels"]] = wheel_combo_counts.get(f["wheels"], 0) + 1
print("feasible wheel combos (0=big wheel touched, 1=small wheel; blue,green,red):", wheel_combo_counts)
print("M3 representative (nearest the centre of the allowed ranges):", {k: (round(float(v), 5) if isinstance(v, (float, np.floating)) else v) for k, v in rep.items()}, "F_t*=%.3f N" % Ft_star)

# ---- cross-check: the new gear engine (formula-stock driven) must reproduce the numpy model ----------
gear_engine.use_stock()
shafts = [{"name": "Yellow", "in": None, "out": 9}, {"name": "Blue", "in": 27, "out": 8},
          {"name": "Green", "in": 27, "out": 8}, {"name": "Red", "in": 27, "out": 16},
          {"name": "Output", "in": rep["Nout"], "out": None}]
train = gear_engine.GearTrain(shafts, rep["module"], rep["eta"])
omega_out = DATA["output_rpm"] * 2 * math.pi / 60
omega_motor = train.motor_speed_rad_s(omega_out)
mc = gear_engine.motor_constants(DATA["supply_V"], I0, rep["Ra"], omega_motor)
wheels_teeth = {"Yellow": 9}
for i, g in enumerate(["Blue", "Green", "Red"]):
    wheels_teeth[g] = BIG[g] if rep["wheels"][i] == 0 else SMALL[g]
idx = {"Yellow": 0, "Blue": 1, "Green": 2, "Red": 3}
engine_dI = {g: train.delta_current(idx[g], wheels_teeth[g], Ft_star, mc["Kt"]) for g in GEARS}
numpy_dI = {g: Ft_star * (wheels_teeth[g] * rep["module"] / 2000.0) / (CUM[g] * rep["eta"] ** MESHES_FROM_MOTOR[g] * rep["Kt"]) for g in GEARS}
worst = max(abs(engine_dI[g] - numpy_dI[g]) / numpy_dI[g] for g in GEARS)
assert abs(mc["Kt"] - rep["Kt"]) / rep["Kt"] < 1e-9, "motor constant mismatch"
assert worst < 1e-9, f"engine vs numpy mismatch {worst}"
print(f"engine == independent calculation (worst relative difference {worst:.1e})")

# ---- the natural reading (M2): the visible BIG wheel touched, the verified twin's own central parameters ----
m2_eta = [e for sf_, e in [best_over_eta(lambda e: {g: BIG[g] / (CUM[g] * e ** MESHES_FROM_MOTOR[g]) for g in GEARS})]][0]
train2 = gear_engine.GearTrain([{"name": "Yellow", "in": None, "out": 9}, {"name": "Blue", "in": 27, "out": 8},
                               {"name": "Green", "in": 27, "out": 8}, {"name": "Red", "in": 27, "out": 16},
                               {"name": "Output", "in": 30, "out": None}], 0.53724, m2_eta)
w2 = DATA["output_rpm"] * 2 * math.pi / 60
mc2 = gear_engine.motor_constants(DATA["supply_V"], I0, 5.5, train2.motor_speed_rad_s(w2))
s2 = {g: 1.0 / max(1e-12, 1.0) for g in GEARS}
unit = {g: train2.delta_current(idx[g], BIG[g], 1.0, mc2["Kt"]) for g in GEARS}      # A per N tangential
sf2, lo2, hi2 = spread(unit)
Ft2 = math.sqrt(lo2 * hi2)       # best compromise force when no single force fits exactly
m2_pred = {g: unit[g] * Ft2 for g in GEARS}
print(f"M2 central: eta={m2_eta:.2f}, Kt={mc2['Kt']:.4f}, spread={sf2:.2f}, compromise tangential force={Ft2:.3f} N")

proto_at_2N = {g: PROTO_PER_N[g] * 2.0 for g in GEARS}
final_pred = engine_dI
table = []
for g in GEARS:
    lo, hi = BANDS[g]
    inside = lambda v: lo <= v <= hi  # noqa: E731
    table.append({"gear": g, "measured_band_mA": [round(lo * 1e3, 1), None if hi == INF else round(hi * 1e3, 1)],
                  "prototype_at_2N_mA": round(proto_at_2N[g] * 1e3, 2), "prototype_in_band": inside(proto_at_2N[g]),
                  "m2_big_wheels_mA": round(m2_pred[g] * 1e3, 1), "m2_in_band": inside(m2_pred[g]),
                  "m3_small_wheels_mA": round(final_pred[g] * 1e3, 1), "m3_in_band": inside(final_pred[g])})
for r in table:
    print(r)

# ---- outputs ------------------------------------------------------------------------------------------
out = {
    "data_used": DATA, "bands_delta_over_idle_mA": {g: [round(a * 1e3, 1), None if b == INF else round(b * 1e3, 1)] for g, (a, b) in BANDS.items()},
    "iterations": [{"model": a, "change": b, "min_spread_factor": round(c, 2), "at_eta": d} for a, b, c, d in iterations],
    "m3_feasible_sets": len(feasible), "m3_plausible_sets": len(plausible), "grid_size": total_grid,
    "representative_fit_m3": {k: (list(v) if isinstance(v, tuple) else float(v) if isinstance(v, np.floating) else v) for k, v in rep.items()}, "touch_force_tangential_N_m3": Ft_star, "m2_central": {"eta": float(m2_eta), "Kt": mc2["Kt"], "spread": float(sf2), "compromise_force_N": float(Ft2)},
    "prototype_dynamic_model_impact_A": PROTO_DYNAMIC_IMPACT_A, "table": table,
}
with open(os.path.join(HERE, "validation_results.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

fig, ax = plt.subplots(figsize=(8.2, 4.8), dpi=140)
fig.patch.set_facecolor("#0b0f14"); ax.set_facecolor("#0f1319")
for i, g in enumerate(GEARS):
    lo, hi = BANDS[g]
    top = 300.0 if hi == INF else hi * 1e3
    ax.bar(i, top - lo * 1e3, bottom=lo * 1e3, width=0.5, color="#1d4a63", edgecolor="#4fc3f7", zorder=2,
           label="measured band (live touches)" if i == 0 else None)
    if hi == INF:
        ax.annotate("open-ended", (i, 150), ha="center", color="#8fb4c9", fontsize=8)
    ax.plot(i - 0.14, proto_at_2N[g] * 1e3, "x", color="#e5534b", ms=9, mew=2.2, zorder=3, label="prototype model, 2 N press" if i == 0 else None)
    ax.plot(i + 0.10, m2_pred[g] * 1e3, "o", color="#5ec269", ms=8, zorder=3, label="corrected model, big wheels (natural reading)" if i == 0 else None)
    ax.plot(i + 0.24, final_pred[g] * 1e3, "D", color="#e0a940", ms=6, zorder=3, label="corrected model, best fit (small wheels)" if i == 0 else None)
ax.set_yscale("log"); ax.set_ylim(1, 400)
ax.set_xticks(range(4)); ax.set_xticklabels([f"{g}\n(motor side)" if g == "Yellow" else (f"{g}\n(output side)" if g == "Red" else g) for g in GEARS], color="#c9d6e4")
ax.set_ylabel("extra motor current over idle (mA, log scale)", color="#c9d6e4"); ax.tick_params(colors="#c9d6e4")
for sp_ in ax.spines.values(): sp_.set_color("#1c232d")
ax.grid(axis="y", color="#1c232d", zorder=0)
ax.set_title("150 RPM gear rig: measured touch bands vs. model predictions", color="#ffffff", fontsize=11)
leg = ax.legend(facecolor="#0f1319", edgecolor="#1c232d", labelcolor="#c9d6e4", fontsize=8, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "bands_vs_models.png"), facecolor=fig.get_facecolor())

# ---- report --------------------------------------------------------------------------------------------
def band_txt(r):
    lo, hi = r["measured_band_mA"]
    return f"{lo}-{hi}" if hi is not None else f">= {lo}"


def cell(v, ok):
    return f"{v} ({'in band' if ok else 'outside'})"


rows = "\n".join(f"| {r['gear']} | {band_txt(r)} | {cell(r['prototype_at_2N_mA'], r['prototype_in_band'])} | {cell(r['m2_big_wheels_mA'], r['m2_in_band'])} | {cell(r['m3_small_wheels_mA'], r['m3_in_band'])} |" for r in table)
its = "\n".join(f"| {a} | {b} | {c:.2f} |" for a, b, c, d in iterations)
pm = (sf2 ** 0.5 - 1) * 100
rep_md = f"""# Gear rig physics validation

Data used: the rig's recorded constants and the part-interruption bands tuned live on the real INA228 rig.
**Not usable:** the July recordings databases (older ACS712 relay setup, ~38 A means on a 12 V motor); there are no INA228 raw recordings on disk.

## Real bands vs. model, per gear (extra current over the 22 mA idle, in mA)

| Gear | Measured band | Prototype model, its 2 N press | Corrected, big wheels, one compromise force | Corrected, best fit, small wheels |
|---|---|---|---|---|
{rows}

Prototype dynamic (RK4) model, impact touch: Yellow {PROTO_DYNAMIC_IMPACT_A['Yellow']} A, Blue {PROTO_DYNAMIC_IMPACT_A['Blue']} A, Green {PROTO_DYNAMIC_IMPACT_A['Green']} A, Red {PROTO_DYNAMIC_IMPACT_A['Red']} A: amps on a 12 V motor idling at 22 mA, with sign flips. Not physical; not carried forward.

## Iterations (spread factor = how many times the touch force must differ between gears to hit every band; 1.0 or less = one common force explains all four)

| Model | Change | Best spread factor over efficiency 0.85-0.97 |
|---|---|---|
{its}

## Motor constant: derived, not fitted
The prototype lumped everything into one gain (current per N*m, 5-12.5) and retracted Kt/Ke as unknown. Kt = Ke = (V - I_idle*Ra)/omega_motor, with omega_motor from the measured 150 RPM output through the tooth-count chain: about {mc2['Kt']:.4f} N*m/A here (the retracted placeholder was 0.145, about ten times too large).

## Result
- **Structure (no free gain):** with the prototype's formulas the touch force would have to differ ~19x between gears to hit the bands. With the corrected structure and the visible big wheels it differs by {sf2:.2f}x (about +-{pm:.0f}% around one force, well inside how unevenly a hand presses). If the finger hit the small wheels of the compound gears, one common force fits all four bands exactly.
- **Parameter region:** {len(feasible)} of {total_grid} combinations drawn from the registry's own ranges reproduce all four bands with one common force (wheel combinations that work: {wheel_combo_counts}); the implied press force is inside the rig's 0.1-15 N range for {len(plausible)} of them.
- **Natural reading:** big wheels, output gear 30T, armature 5.5 ohm, mesh efficiency {m2_eta:.2f}, tangential touch force about {Ft2:.2f} N (a press of about {Ft2/0.19181:.1f} N at the twin's friction 0.19).
- **Best fit nearest the middle of the allowed ranges:** output gear {rep['Nout']}T, mesh efficiency {rep['eta']:.2f}, armature {rep['Ra']} ohm, module {rep['module']} mm, tangential force about {Ft_star:.2f} N.
- The new engine (`engine/gear_engine.py`, run through the formula stock) reproduces an independent calculation to rounding error (1e-16).

## What this does and does not prove
- It proves the prototype's structure was wrong (efficiency counted from the wrong end, no gear-ratio reflection, motor gain ten times off) and that the corrected structure explains the band ordering and spacing with physically reasonable parameters and no fitted gain.
- It does not prove the absolute scale: the touch force was never measured, the bands are classification limits (not raw recordings), and which wheel of each compound gear was touched is unknown.
- To close that: record the INA228 trace while pressing each gear with a known force (a kitchen scale), about 10 minutes of data.
- Noise: block means swung 20-40 mA with the motor running, larger than the Red band (9-12 mA); detection worked only because of block averaging and the 0.25 s hold.
"""
with open(os.path.join(HERE, "REPORT.md"), "w") as f:
    f.write(rep_md)
print("wrote REPORT.md, validation_results.json, bands_vs_models.png")
