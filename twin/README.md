# Servo Piston Filler / Depositor — Digital Twin

3D wireframe digital twin of the **Volumetric Technologies Servo Piston Filler / Depositor**
(Excelis Packaging Automation → Liquid Filling Machines → Piston Fillers → Servo Series),
driven by the local Yanthros Formula Brain.

## Run

```bash
python3 -m http.server 8777 --directory twin
```

Then open <http://localhost:8777>. No network access needed — three.js is vendored.

## Rebuild the solved data

The page reads `twin_data.json`, which is produced by the Formula Brain, not hand-written.

```bash
TWIN_SCRATCH=/tmp python3 twin/brain_launch.py &
python3 twin/build_twin.py
```

- `brain_launch.py` starts an **isolated** Brain on port **5052**. The user's own Brain
  runs on 5051; this avoids mutating that live service, and redirects
  `brain_extensions.json` out of `faulter-formula-brain/` so the repo is untouched.
- `build_twin.py` runs two phases: **extend** (teach the Brain 50 formulas it was
  missing) then **solve** (forward-chain the machine's inputs to 42 outputs, keeping
  the full derivation trace for each).

To make the 50 new formulas permanent in the real Brain, copy the generated
`brain_extensions.json` into `/Users/mac/Desktop/faulter-formula-brain/`.

## What the Brain already had vs. what was added

The Brain's 333 formulas covered the servo (`torque`, `power_mechanical`,
`efficiency`), the bearings (`bearing_friction_torque`, `bearing_life_l10`), the
structure (`materials` / `polar_moment` / `shaft_torsion`), thermal, and control.
Five things it did **not** have, all added here from published sources:

| Gap | Added | Why it mattered |
|---|---|---|
| Screw drives | `pf_ballscrew_torque`, `pf_reflected_load_inertia` | Library had gears/belts/chains but no screw. `F = 2πηT/p` is the only way to get from piston thrust to motor torque. |
| Non-Newtonian flow | `pf_power_law_wall_stress`, `pf_rabinowitsch_correction`, `pf_generalized_reynolds` | `hydraulics` assumed Newtonian. This machine is sold for shear-thinning product, where Newtonian Δp is materially wrong. |
| Error stacking | `pf_rss_fill_accuracy` | Nothing in the library could combine tolerances, so the OEM's ±0.25% claim could not be checked. |
| Trapezoidal motion | `pf_peak_velocity`, `pf_peak_acceleration` | Needed to turn the OEM's "soft start, fast fill, soft end" into numbers. |
| Volumetric metering | `pf_piston_bore_area`, `pf_stroke_required`, … | Bore/stroke ↔ deposit volume, the core of a volumetric filler. |

## Inverse design — bore and stroke are derived, not chosen

`V = (π/4)·D²·S` has infinite (D, S) solutions, so the deposit volume alone cannot
size the cylinder. The **accuracy spec** breaks the tie, because the two geometric
error terms pull in opposite directions:

- `e_stroke = 100·δS/S`, and `S = 4V/(πD²)` → **grows as D²**
- `e_bore = 200·δD/D` (volume ∝ D², so `dV/V = 2·dD/D`) → **falls as 1/D**

Minimising `e_stroke² + e_bore²` gives a closed form:

```
D_opt = ( 8·δD·V / (√2·π·δS) )^(1/3)
```

Nozzle bore falls out the same way — inverted from the wall-shear ceiling the product
tolerates, at **peak** flow, not mean. Turndown comes from asking how short a stroke
still fits inside the ±0.25% budget.

Verified in-browser: RSS at `D_opt` is lower than at ±10% either side; peak wall shear
lands exactly on the 2000 s⁻¹ ceiling; RSS at minimum stroke lands exactly on 0.25%.

## Confidence

Every input in `twin_data.json` is tagged `oem` / `estimated` / `material`.
Bore, stroke and nozzle are now **derived outputs**. What remains estimated is the
*tolerance* inputs they depend on — `dS_pos_pf` (servo positional repeatability),
`dD_bore_pf` (bore machining tolerance) and the product rheology. Those are the three
numbers worth getting from the OEM: they set the whole geometry.

## Kinematic correctness

The 3D is asserted, not eyeballed. `window.__twin` exposes the scene and motion laws.
Confirmed: the ball screw **rotates** at `60·v/lead` and reverses on the suction
stroke; the servo rotor is rigidly synced to it; the rotary plug valve is **stationary
through both strokes** and swings its full 180° only during the dwells; crosshead,
nut and all four pistons move as one rigid body.

Every rotating part has its geometry baked onto the X axis (`bakeX`) rather than
carrying `object.rotation.z = π/2`. Without that, `rotation.x` is not the part's own
axis and the spin is wrong — this was a real bug in the first version.

## Envelope

The vertical stack is built **upward from the container**, not chosen: conveyor height
(ergonomic standard) + jar height → nozzle tip → valve → cylinder axis → hopper.
Head pitch is jar diameter + clearance. This is the only part of the machine envelope
with a real dimensional anchor.

## Note on the two flow numbers

The right-hand panel reports `Q_pf` and the rheology derived from it as **cycle-mean**
values (`V_net / t_discharge`). The live HUD on the left computes the same equations
from the **instantaneous** piston velocity, so it peaks about 1.5× higher mid-stroke.
Both are correct; they answer different questions.
