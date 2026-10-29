# Motor Parameter Identification — Stage 2.6

**Status:** planning document only. No simulation code, registry numeric values, or twin
files are changed by this document. `MOTOR_Ra_OHM`, `MOTOR_La_H`, `MOTOR_Kt_NM_PER_A`, and
`MOTOR_Ke_V_S_PER_RAD` remain **unknown motor parameters** — see
`constraint_registry_metal.json`'s `unknown_motor_parameter` flags on the Kt/Ke fields.

**Context:** the Stage 2.5 audit found that `MOTOR_Kt_NM_PER_A` (and, through the `Ke=Kt`
identity, `MOTOR_Ke_V_S_PER_RAD`) had been set from `1/CURRENT_PER_NM` — a touch-point-
referenced, gear-train-lumped empirical current gain (`gear_train.py`'s own docstring: "A
per Nm of torque at the touch point, replacing 1/Kt") — with no gear-ratio reflection to
the armature/Yellow shaft `Kt` and `Ke` are actually defined against. That derivation is
retracted (see `constraint_registry_metal.json` changes accompanying this document).
`CURRENT_PER_NM` remains exclusively part of the legacy touch-current model
(`physics/current_model.py::torque_to_current`) and must not be used again, directly or
indirectly, to derive any motor electrical constant.

This document lists every practical way to actually obtain `Ra`, `La`, `Kt`, `Ke` for this
specific motor, and recommends the smallest measurement set that would make
`physics/electrical.py` physically meaningful. **No numeric value in this document is a
proposed replacement for any constant** — nothing here is a measurement, an estimate, or a
guess; it is a plan for how a real measurement would eventually be taken.

---

## What's known and available for these measurements

- `MOTOR_SUPPLY_VOLTAGE_V = 12` — measured, hard constraint, already in
  `constraint_registry_metal.json`.
- An INA228 current sensor is already wired into the rig and already read by
  `detection/acquisition.py`. Its raw sample rate is **~893 Hz** (`acquisition.py:130`) —
  i.e. ~1.12 ms between samples. This bounds what can and can't be resolved directly from
  the existing sensor (see the `La` section below).
- Yellow is the motor's own gear, rigidly on the armature shaft (`gear_train.py`'s module
  docstring) — electrically and mechanically it *is* the motor shaft, so tests that need to
  drive or lock "the motor shaft" can be performed at Yellow without needing to physically
  disassemble the motor out of the gearbox housing.
- No datasheet exists for this motor, and none is expected to surface — every "datasheet
  lookup" row below is included for completeness, not because it's expected to be usable.

---

## Ra — Armature Resistance (Ω)

| Method | Class | Applicable here? |
|---|---|---|
| Multimeter across motor terminals, rotor stationary, ideally 4-wire (Kelvin) to remove lead resistance | Direct measurement | **Yes.** Cheapest, fastest, no rig modification needed. Take readings at a few different rotor positions and average — brush contact resistance varies with commutator position. |
| Manufacturer datasheet value | Datasheet lookup | No — no datasheet exists for this motor. |
| Locked-rotor DC test: lock the shaft, apply a known low DC voltage, record steady-state current, `Ra = V / I` | Experimental identification | **Yes.** More reliable than a passive multimeter reading because it's measured under the same current regime the model will actually use, and it can reuse the rig's own 12 V supply (at a reduced test voltage) and the already-installed INA228. Requires only a way to physically prevent Yellow (or any downstream gear) from turning — a clamp or a jammed gear is sufficient, since the whole train is rigid. |
| Estimate from wire gauge / winding turns / coil geometry | Mathematical estimation | No — winding data for this motor doesn't exist and isn't practical to obtain non-destructively. |

**Applicable methods:** direct multimeter + locked-rotor DC test. These two should agree;
if they don't, brush/contact resistance or lead resistance is the likely explanation.

---

## La — Armature Inductance (H)

| Method | Class | Applicable here? |
|---|---|---|
| LCR meter / impedance analyzer across motor terminals, rotor stationary | Direct measurement | **Yes, and the best option if the equipment is available.** A standard, direct measurement for small brush motors — no modeling, no fitting, no gear-train involvement. This is the method already anticipated in `constraint_registry_metal.json`'s existing `MOTOR_La_H` source note ("pending an LCR-meter measurement"). |
| Manufacturer datasheet value | Datasheet lookup | No — no datasheet exists. |
| Locked-rotor step response: apply a voltage step with the rotor still locked (same physical setup as the `Ra` test), record `i(t)` from turn-on, fit the RL charging curve `i(t) = (V/Ra)(1 - e^(-t·Ra/La))` to extract `τ = La/Ra`, then `La = τ · Ra` using the independently-measured `Ra` | Experimental identification | **Conditionally.** Reuses the `Ra` test rig with no extra setup. But this requires sampling fast enough to resolve `τ`, and the rig's only currently-installed sensor samples at ~893 Hz (~1.12 ms/sample). A small brushed DC motor's electrical time constant is very plausibly sub-millisecond to low-single-digit milliseconds — if so, the existing INA228 acquisition path cannot resolve it, and this method would need a faster data path (an oscilloscope across a shunt, or a faster ADC) rather than the rig's existing detection pipeline. Flagging this explicitly rather than assuming the existing sensor is fast enough. |
| Estimate from coil geometry / core material | Mathematical estimation | No — same reason as `Ra`. |

**Applicable methods:** LCR meter is the primary recommendation. The locked-rotor
step-response fit is a usable fallback only if a current-sampling path faster than the
existing ~893 Hz pipeline is available for the test.

---

## Kt — Torque Constant (Nm/A)

| Method | Class | Applicable here? |
|---|---|---|
| Bench dynamometer / calibrated load cell directly on the bare motor shaft, sweeping load and fitting `ΔT/ΔI` | Direct measurement | **Not practical as stated** — the motor is embedded in the gearbox housing; there is no bare, decoupled shaft to mount a dynamometer on without disassembly. |
| Manufacturer datasheet value | Datasheet lookup | No — no datasheet exists. |
| Locked-rotor stall-torque test: with the rotor locked (same physical setup as the `Ra`/`La` tests), apply a known torque at the point of locking via a calibrated tool (torque wrench, or a known weight on a known-radius lever arm on Yellow or the output shaft) up to the exact breakaway point, and simultaneously record the current at that point; `Kt = T_stall / I_stall` | Experimental identification | **Yes — the practical route for this rig.** Isolates torque/current cleanly because `ω = 0` removes back-EMF entirely from the equation, and it needs no separate access to a bare motor shaft — Yellow (rigidly on the armature) is a valid application point, or the exposed Output rod can be used instead if the gear ratio Yellow↔Output and its `GEAR_MESH_EFFICIENCY` term are treated as a *separate, already-measured* correction (not re-derived from `CURRENT_PER_NM`). Standard textbook DC-motor characterization technique. |
| `Kt = Ke` via the SI identity, once `Ke` is independently known | Mathematical estimation | **Cross-check only, not a source.** Valid *after* one of `Kt`/`Ke` has already been obtained by an independent physical method — using it as the *original* source (as Stage 0 effectively did, transitively through `CURRENT_PER_NM`) is exactly the circularity Stage 2.5 flagged. |

**Applicable methods:** locked-rotor stall-torque test is the practical primary route.
`Kt = Ke` is valid only as a downstream consistency check, never as the initial source for
either constant.

---

## Ke — Back-EMF Constant (V·s/rad)

| Method | Class | Applicable here? |
|---|---|---|
| Drive the motor shaft externally (hand crank, drill, or a second motor) at one or more known, tachometer-measured speeds with the rig's own supply disconnected, and measure the open-circuit terminal voltage; `Ke = V_oc / ω`, fit across several speeds | Direct measurement | **Yes — the cleanest method available.** Generator-mode measurement of the exact defining quantity, with zero current flowing so there's no `Ra` drop to correct for and no gear-train modeling needed beyond knowing the shaft speed at the point of measurement (Yellow, if driven directly, or any other node if the gear ratio to Yellow is applied — using only the *measured* tooth-count ratios, never `CURRENT_PER_NM`). |
| Manufacturer datasheet value | Datasheet lookup | No — no datasheet exists. |
| No-load speed test: apply the known 12 V supply with the shaft as unloaded as practical, measure steady no-load RPM (tachometer or optical/spectral method) and no-load current `I_0`; `Ke ≈ (V - I_0·Ra) / ω_no-load`, using the independently-measured `Ra` and assuming static/friction torque is small at true no-load | Experimental identification | **Yes, as a secondary/cross-check method.** Simpler rig setup than the generator test (no external drive needed — the rig drives itself), but less clean: it assumes friction/static torque is negligible, and needs `Ra` already known from its own test. Best used to corroborate the direct generator-mode measurement, not replace it. |
| `Ke = Kt` via the SI identity | Mathematical estimation | **Cross-check only, not a source** — same caveat as `Kt`'s identity row above. |

**Applicable methods:** the driven/generator-mode test is the primary recommendation; the
no-load speed test is a useful, lower-effort cross-check once `Ra` is known.

---

## Recommended minimal measurement set

Four physical measurements, across **two experimental sessions**, are sufficient to give
all four constants an independent, non-circular physical basis:

**Session 1 — locked rotor** (Yellow, or any convenient point in the rigid gear train,
mechanically clamped so nothing turns):
1. Apply a few known low DC voltages, record steady-state current → **`Ra`** (`Ra = V/I`).
2. If a sampling path faster than the existing ~893 Hz INA228 pipeline is available, record
   the current step-response at turn-on and fit the RL time constant → **`La`**
   (`La = τ·Ra`). If no faster acquisition path is available, defer `La` to an LCR-meter
   measurement instead (still "Session 1" in the sense that it needs the motor at rest, not
   spinning, but doesn't need the electrical supply or the clamp at all).
3. With a calibrated torque wrench or a known weight-on-lever-arm applied at the same
   locked point, find the exact current at breakaway → **`Kt`** (`Kt = T_stall/I_stall`).

**Session 2 — driven, no electrical supply** (shaft turned externally, e.g. by hand-crank
or a second motor, with a tachometer or equivalent speed measurement):
4. Record open-circuit terminal voltage at one or more known speeds → **`Ke`**
   (`Ke = V_oc/ω`, fit as a line across speeds for a consistency check on linearity).

Session 1 alone yields `Ra`, `Kt`, and (equipment-permitting) `La` with no dependency on
`CURRENT_PER_NM` or on any gear-train efficiency assumption. Session 2 yields `Ke`
independently of Session 1. Once both constants are obtained this way, `Kt` vs. `Ke`
(which should coincide, per the standard SI identity, for a lossless ideal motor) becomes a
genuine, non-circular consistency check — unlike Stage 0's use of that identity, which
manufactured agreement rather than testing for it.

No smaller measurement set avoids circularity: any attempt to derive `Kt`/`Ke` purely from
quantities already in the touch-signature model (`CURRENT_PER_NM`, `I_BASELINE_A`, the
measured tooth counts) reproduces exactly the Stage 0 error, because none of those
quantities were ever calibrated against a known torque or a known back-EMF in the first
place.
