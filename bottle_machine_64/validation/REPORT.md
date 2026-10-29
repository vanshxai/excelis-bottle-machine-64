# Gear rig physics validation

Data used: the rig's recorded constants and the part-interruption bands tuned live on the real INA228 rig.
**Not usable:** the July recordings databases (older ACS712 relay setup, ~38 A means on a 12 V motor); there are no INA228 raw recordings on disk.

## Real bands vs. model, per gear (extra current over the 22 mA idle, in mA)

| Gear | Measured band | Prototype model, its 2 N press | Corrected, big wheels, one compromise force | Corrected, best fit, small wheels |
|---|---|---|---|---|
| Yellow | >= 69.0 | 3.74 (outside) | 60.4 (outside) | 150.5 (in band) |
| Blue | 21.0-68.0 | 12.83 (outside) | 68.7 (outside) | 49.0 (in band) |
| Green | 13.0-20.0 | 14.67 (in band) | 23.1 (outside) | 16.0 (in band) |
| Red | 9.0-12.0 | 16.76 (outside) | 7.8 (outside) | 10.4 (in band) |

Prototype dynamic (RK4) model, impact touch: Yellow -6.436 A, Blue -11.85 A, Green 7.691 A, Red 10.029 A: amps on a 12 V motor idling at 22 mA, with sign flips. Not physical; not carried forward.

## Iterations (spread factor = how many times the touch force must differ between gears to hit every band; 1.0 or less = one common force explains all four)

| Model | Change | Best spread factor over efficiency 0.85-0.97 |
|---|---|---|
| M0  prototype as built | efficiency counted from the OUTPUT side (4,3,2,1 meshes); no gear-ratio reflection; lumped current-per-N*m | 18.90 |
| M1  fix efficiency direction | meshes counted from the MOTOR side (0,1,2,3); still no gear-ratio reflection | 10.59 |
| M2  add gear-ratio reflection | touch torque divided by the speed reduction from the motor to that shaft (big wheels) | 1.34 |
| M3  allow touching either wheel of a compound gear | each of Blue/Green/Red has a big and a small wheel; which one the finger hit is not known | 0.75 |

## Motor constant: derived, not fitted
The prototype lumped everything into one gain (current per N*m, 5-12.5) and retracted Kt/Ke as unknown. Kt = Ke = (V - I_idle*Ra)/omega_motor, with omega_motor from the measured 150 RPM output through the tooth-count chain: about 0.0118 N*m/A here (the retracted placeholder was 0.145, about ten times too large).

## Result
- **Structure (no free gain):** with the prototype's formulas the touch force would have to differ ~19x between gears to hit the bands. With the corrected structure and the visible big wheels it differs by 1.34x (about +-16% around one force, well inside how unevenly a hand presses). If the finger hit the small wheels of the compound gears, one common force fits all four bands exactly.
- **Parameter region:** 1989 of 15912 combinations drawn from the registry's own ranges reproduce all four bands with one common force (wheel combinations that work: {(1, 1, 1): 1989}); the implied press force is inside the rig's 0.1-15 N range for 1989 of them.
- **Natural reading:** big wheels, output gear 30T, armature 5.5 ohm, mesh efficiency 0.88, tangential touch force about 0.30 N (a press of about 1.5 N at the twin's friction 0.19).
- **Best fit nearest the middle of the allowed ranges:** output gear 32T, mesh efficiency 0.91, armature 5.5 ohm, module 0.53724 mm, tangential force about 0.69 N.
- The new engine (`engine/gear_engine.py`, run through the formula stock) reproduces an independent calculation to rounding error (1e-16).

## What this does and does not prove
- It proves the prototype's structure was wrong (efficiency counted from the wrong end, no gear-ratio reflection, motor gain ten times off) and that the corrected structure explains the band ordering and spacing with physically reasonable parameters and no fitted gain.
- It does not prove the absolute scale: the touch force was never measured, the bands are classification limits (not raw recordings), and which wheel of each compound gear was touched is unknown.
- To close that: record the INA228 trace while pressing each gear with a known force (a kitchen scale), about 10 minutes of data.
- Noise: block means swung 20-40 mA with the motor running, larger than the Red band (9-12 mA); detection worked only because of block averaging and the 0.25 s hold.
