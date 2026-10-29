# Formula Database — 150 RPM Metal Internal Gearbox Rig

**System:** 4-stage compound metal gearbox (motor's own internal gearbox, removed from plastic chain, oiled, tested standalone).
**Topology:** Yellow (motor shaft) → Blue → Green → Red → Output (150 RPM, exposed rod).
**Touch points:** Yellow, Blue, Green, Red. Output is sealed inside the cap — not touchable.
**Sensor:** one ACS712-class current sensor at the motor. No sensor exists anywhere else on the rig.
**Source of truth:** `formula_chain_metal.py`, `constraint_registry_metal.json`.

16 unique formulas. 61 evaluations per full twin run (15 × 4 gears + 1 global).

---

## A — RPM Chain (series)

| Formula | Description | Variables | Assumptions/Validity Limits | Use-Case Tag | Source Topic/Section |
|---|---|---|---|---|---|
| `RPM_next = RPM_prev · (T_driving / T_driven)` | Propagates shaft speed one mesh backward, from a known shaft to an unknown one. | `RPM_next` = speed of the shaft being solved (rev/min); `RPM_prev` = speed of the already-known adjacent shaft (rev/min); `T_driving` = tooth count of the gear on the known shaft that drives the mesh; `T_driven` = tooth count of the meshing gear on the unknown shaft | Rigid, non-slipping, fully-engaged tooth contact. Both gears share the same module (mesh geometry compatible). No backlash, no tooth skip, no clutch/freewheel in the path. Ratio is purely kinematic — holds at any load and any efficiency, because efficiency costs torque, not speed. Breaks down under tooth breakage, disengagement, or belt/chain slip (none present in this rig). Requires exactly one known shaft speed to anchor the chain — here `RPM_output = 150`, hard constraint read off the motor label. | Recovering each gear's true spin rate, since only Output's 150 RPM was ever physically measured. Feeds every downstream frequency and signature calculation. | `formula_chain_metal.py` STEP 1; sheet §A (A1–A4) |

**Chain instances (same formula, 4 runs, strictly ordered):**
`RPM_red = 150 · (T_output/T_red,small)` → `RPM_green = RPM_red · (T_red,big/T_green,small)` → `RPM_blue = RPM_green · (T_green,big/T_blue,small)` → `RPM_yellow = RPM_blue · (T_blue,big/T_yellow)`

**Validation gate (not a formula — a filter):** every RPM must be finite, > 0.01, and ≤ 150 × 200. Any twin violating this is discarded before B–F ever run.

---

## B — Mesh Frequency (parallel, per gear)

| Formula | Description | Variables | Assumptions/Validity Limits | Use-Case Tag | Source Topic/Section |
|---|---|---|---|---|---|
| `f = (RPM / 60) · T` | Tooth-passing (gear-mesh) frequency of one gear, in Hz. | `f` = mesh frequency (Hz); `RPM` = that gear's shaft speed (rev/min); `T` = that gear's tooth count on the meshing side; `60` = s/min conversion | Constant angular velocity (no acceleration during the observation window). Uniform tooth spacing. Counts the *fundamental* only — real vibration/current spectra also carry harmonics (2f, 3f…) and sidebands from eccentricity, which this does not model. Assumes the mesh is continuously engaged. Frequency is a property of the mesh, not of the touch — it exists whether or not anyone touches the gear. | Frequency-domain fingerprint for gear identification: each gear meshes at a distinct Hz, so spectral content can discriminate gears independently of signal amplitude. | `formula_chain_metal.py` STEP 2; sheet §B (B1–B4) |

---

## C — Baseline Current (global constant)

| Formula | Description | Variables | Assumptions/Validity Limits | Use-Case Tag | Source Topic/Section |
|---|---|---|---|---|---|
| `I_baseline = I_BASELINE_A` | Steady-state motor current with the rig spinning and nothing touched. | `I_baseline` = idle draw (A); `I_BASELINE_A` = sampled constant, range 0.05–0.5 A | **Set directly, not derived.** Deliberately collapses the unknown electrical model (`V`, `R_a`, `K_t`) into one observable, because no datasheet exists for this motor and current alone can never separate those three. Valid only at thermal and mechanical steady state — assumes warmed-up oil, settled bearings, constant supply voltage. Excludes inrush/startup transient. Drifts with temperature and lubricant viscosity in reality; treated as fixed here. | The zero-reference every touch signature is measured against. `ΔI` is meaningless without it. Also the calibration anchor for the raw sensor trace (`calibrated_A = current_A − zero_ref`). | `formula_chain_metal.py` STEP 3; sheet §C (C1) |

---

## D — Steady-Force Touch Model (per gear, "held press")

| Formula | Description | Variables | Assumptions/Validity Limits | Use-Case Tag | Source Topic/Section |
|---|---|---|---|---|---|
| `r_mm = (T_big · m) / 2` | Pitch radius of the touched gear from its tooth count. | `r_mm` = pitch radius (mm); `T_big` = tooth count of the touched (large) gear; `m` = `MODULE_MM`, 0.4–0.7 mm | Standard involute spur-gear geometry: pitch diameter = module × teeth, by definition. Requires all meshing gears to share one module. Gives the *pitch* radius, not the outer/tip radius — real contact with a tool happens slightly outboard (tip radius ≈ `r + m`), so this mildly under-estimates the true lever arm. Assumes no profile shift/correction. | Establishes the lever arm — the single geometric property that makes a touch on one gear produce a different current than the same touch on another. | `formula_chain_metal.py` STEP 4; sheet §D (D1) |
| `r_m = r_mm / 1000` | Unit conversion to metres. | `r_m` = pitch radius (m) | Pure unit conversion, always valid. Exists only so torque comes out in N·m rather than N·mm. | Keeps the whole chain in SI so `k_I` (A per N·m) applies without a hidden factor of 1000. | sheet §D (D2) |
| `η_chain = η_mesh^n` | Cumulative transmission efficiency across `n` gear meshes. | `η_chain` = end-to-end efficiency (dimensionless, 0–1); `η_mesh` = per-mesh efficiency, 0.85–0.97; `n` = number of meshes between the touched gear and the reference shaft | Assumes every mesh is identical and independent, so losses multiply. Load-independent efficiency — real gear efficiency varies with torque, speed, and oil temperature. Valid only for oiled metal-on-metal contact in the sampled band. **`n` is currently defined as meshes-to-Output** (Yellow=4, Blue=3, Green=2, Red=1) while the sensor physically sits at the motor — flagged as a modelling inconsistency, see Open Items. | Encodes "distance penalty": a touch far from the measurement point arrives weaker. This is the second discriminating axis alongside radius. | `formula_chain_metal.py` STEP 4; sheet §D (D3) |
| `τ_perN = r_m · μ · η_chain` | Torque delivered per newton of applied touch force. | `τ_perN` = torque per unit force (N·m/N); `μ` = `METAL_OILED_FRICTION_COEFF`, 0.05–0.2 | Coulomb dry-friction idealization (`F_tangential = μ·F_normal`) applied to a lubricated contact — an approximation, since oiled contact is genuinely viscous/Stribeck-regime and μ varies with sliding speed. Assumes the touch is normal to the gear surface, at pitch radius, and non-marring. Force-normalized, so independent of how hard you press. | Force-independent sensitivity number — lets predictions be compared against real touches of unknown force. | sheet §D (D4) |
| `ΔI_perN = τ_perN · k_I` | Current draw per newton of touch force. | `ΔI_perN` = current sensitivity (A/N); `k_I` = `CURRENT_PER_NM`, 5.0–12.5 A per N·m | Assumes a **linear** torque→current relationship with no offset, valid only in the motor's linear operating region (away from stall and away from no-load). `k_I` is a lumped stand-in for `1/K_t` including drivetrain effects — it is calibrated, not derived from first principles. Ignores back-EMF shift, magnetic saturation, and controller current limiting. | The headline per-gear sensitivity figure. Used to rank which gears are detectable at all. | sheet §D (D5) |
| `τ_touch = F_touch · r_m · μ` | Torque produced by the specific reference touch. | `τ_touch` = torque at the gear (N·m); `F_touch` = 0.5 N fixed reference force | Same friction idealization as D4. `F_touch = 0.5 N` is an arbitrary but fixed benchmark — the registry permits 0.1–15.0 N. Assumes a sustained, constant-force press with the tool stationary against a spinning surface. **Real recorded touch data did not behave this way** — see §E. | Produces one concrete comparable number per gear at a common force, for the cross-twin comparison table. | sheet §D (D6) |
| `τ_motor = τ_touch · η_chain` | Touch torque after transmission losses. | `τ_motor` = torque seen at the motor (N·m) | Assumes losses are multiplicative and instantaneous — no elastic wind-up, no backlash dead-band, no inertial buffering. Quasi-static: valid only if the touch lasts long enough for the drivetrain to reach a new equilibrium (roughly ≫ the rise time from F1). | Converts a gear-local effect into a motor-observable one. | sheet §D (D7) |
| `ΔI = τ_motor · k_I` | Predicted steady current rise for a 0.5 N touch on this gear. | `ΔI` = current delta (A) | Inherits every limit above. Quasi-static only. Assumes `ΔI` is small enough to stay in the linear region and not trip current limiting. **Fall back to §E (`ΔI_impulse`) when the touch is a strike, scrape, or chatter rather than a sustained press — which is what real testing actually produced.** | Nominal predicted signature magnitude per gear; the number originally intended for gear identification. | sheet §D (D8) |

---

## E — Impact-Response Model (per gear, "screwdriver strike")

Added after real touch data showed <10 ms current spikes with a barely-moving mean — an impact response, not a sustained-force response. This supersedes §D for real-world scrape/strike events.

| Formula | Description | Variables | Assumptions/Validity Limits | Use-Case Tag | Source Topic/Section |
|---|---|---|---|---|---|
| `w_m = GEAR_WIDTH_MM / 1000` | Gear face width in metres. | `w_m` = face width (m); `GEAR_WIDTH_MM` = 3.0–8.0 mm | Unit conversion. Assumes one uniform width applies to all gears in the cluster — a simplification; real compound gears have different widths for the big and small halves. | Feeds the mass calculation. | `formula_chain_metal.py` STEP 4; sheet §E (E1) |
| `mass = ρ · π · r_m² · w_m` | Gear mass from real material density and geometry. | `mass` = gear mass (kg); `ρ` = `MATERIAL_DENSITY_KG_M3`, 7000–8100 (steel/alloy) | **Solid-cylinder idealization.** Ignores the centre bore, spokes/webbing, tooth gaps (real gears are ~5–10% lighter than the solid disc), and any coaxial second gear on the same shaft. Uses pitch radius rather than tip radius. Valid only for solid metal gears — would fail for plastic, hollow, or heavily webbed gears. | Grounds inertia in real physics rather than asserting it — the reason `ρ` and width exist as constants at all. | sheet §E (E2) |
| `I_rot = 0.5 · mass · r_m²` | Rotational inertia of the gear. | `I_rot` = moment of inertia (kg·m²) | Solid-disc formula (`½mr²`) about the central axis. Wrong for a ring/spoked geometry (a ring approaches `mr²`, up to 2× larger). Only accounts for the touched gear itself — **excludes the reflected inertia of the motor armature and the rest of the gear train**, which in a 4-stage reduction can dominate. This is the largest single physical simplification in the model. | Determines how much a given impact perturbs the gear's speed: heavy gear absorbs, light gear transmits. | sheet §E (E3) |
| `ΔI_impulse = η_chain · k_imp / I_rot` | Impulse-normalized current sensitivity. | `ΔI_impulse` = sensitivity (A per N·m·s); `k_imp` = `CURRENT_PER_IMPULSE`, 0.5–5.0 | Inverse-inertia scaling: the same angular impulse produces a speed perturbation ∝ 1/`I_rot`. Assumes the strike is short compared to the drivetrain's mechanical time constant (true: <10 ms observed), and that the drivetrain is rigid so the perturbation propagates undamped except by `η_chain`. `k_imp` is an empirical lump, not derived. Normalized by impulse, so it is independent of both strike force and strike duration — this is what makes it directly comparable to a recorded spike. **Falls back to §D (`ΔI`) if the touch is genuinely sustained.** | The number actually compared against real recorded impact spikes. The current primary discriminator. | sheet §E (E4) |

---

## F — Rise Time (per gear)

| Formula | Description | Variables | Assumptions/Validity Limits | Use-Case Tag | Source Topic/Section |
|---|---|---|---|---|---|
| `t_rise = t₀ · (1 + 0.15·n)` | How long the current signature takes to rise, as a function of drivetrain distance. | `t_rise` = rise time (s); `t₀` = 0.002 s fixed electrical reference; `n` = meshes from the touched gear; `0.15` = per-stage delay coefficient | **Empirical, not derived.** The 0.15 coefficient is asserted, not measured; a real multi-stage drivetrain's delay depends on torsional stiffness, backlash, and reflected inertia per stage, none of which are modelled. `t₀` was originally armature-resistance-derived, but `R_a` cancelled algebraically and is now a fixed 2 ms constant. Linear-in-`n` is a first-order guess; real behaviour is likely nonlinear. Requires sensor bandwidth ≫ 1/`t_rise` — at 2–3 ms this demands a sample rate well above ~1 kHz to resolve. Same `n` inconsistency as D3 applies. | Timing-based discriminator: separates gears that happen to share similar `ΔI` magnitude. Third independent identification axis after amplitude and frequency. | `formula_chain_metal.py` STEP 4; sheet §F (F1) |

---

## G — Dynamic Gear-Train Model (time-domain, per touch simulation)

Everything above (§A–F) is `formula_chain_metal.run_formula_chain()`: a steady-state snapshot for one BVS variant, called thousands of times per card-roulette round. It has no backlash, no mesh compliance, and no reflected inertia -- D7 says so explicitly ("no elastic wind-up, no backlash dead-band, no inertial buffering") and Open Item #2 flags the missing reflected inertia. §G is a second, separate engine -- `dynamic_gear_simulator.py` -- that adds exactly those effects for one already-chosen variant, by numerically integrating (RK4) the six per-gear-stage formulas instead of assuming instantaneous quasi-static transmission. `run_formula_chain()` itself is untouched; the sweep's behavior and scoring are unaffected.

| Formula | Description | Variables | Assumptions/Validity Limits | Use-Case Tag | Source |
|---|---|---|---|---|---|
| `ωout = ωin / N` | Ideal (rigid) speed relation at one mesh. | `N` = stage ratio, from tooth counts | Used only to define `θgap` below -- the integration itself never assumes this holds exactly. | Defines what "no backlash, no wind-up" would look like, as the reference the dynamic model deviates from. | `dynamic_gear_simulator.py` `_mesh_torque()` |
| `Tout = Tin·N·η` | Reflected torque across a mesh. | `η` = `GEAR_MESH_EFFICIENCY` (existing constant, reused) | Same efficiency idealization as §D3. Used inverted (`Tin = Tout/(N·η)`) to find the reaction torque a driving gear feels from whatever it's driving. | Couples each node's equation of motion to its neighbors. | `_derivatives()` |
| `Jreflected = Jgear·N²` | Downstream inertia reflected back to an upstream shaft. | `Jgear` computed from geometry (§E2/E3, reused) | Generalized across multiple hops via the existing cumulative-ratio convention. **Informational only** -- exposed as `reflected_inertia_at_motor_kgm2` for a future motor torque/inertia balance; the integration itself gives each node its own physical inertia rather than working in motor-reflected coordinates. | Quantifies what §E3/Open Item #2 flagged as missing -- the reflected inertia of the rest of the train. | `build_gear_train()` |
| `θgap = θin − θout; Tmesh = 0 if less than θbacklash` | Backlash dead-zone. | `θbacklash` = `GEAR_BACKLASH_RAD` (new constant, 0.001-0.02 rad) | `θin` is `θ_driving/N` (the driving shaft's angle reflected into the driven gear's frame), so `θgap` is the deviation from the rigid-coupling assumption above. Backlash is shared across all four meshes (one constant, not per-stage) -- a simplification, same convention as `GEAR_MESH_EFFICIENCY`. Range is an engineering estimate from typical small-module DIN tolerances, not measured. | Lets the mesh genuinely disengage/re-engage instead of always transmitting torque -- the mechanism behind chatter and lash-related noise. | `_mesh_torque()` |
| `Tmesh = kmesh·(θgap − θbacklash)` | Mesh stiffness once engaged. | `kmesh` = `GEAR_MESH_STIFFNESS_NM_PER_RAD` (new constant, 0.05-5.0 Nm/rad) | Linear torsional spring, sign-corrected for `θgap`'s direction. Range is an unverified placeholder (no measured tooth stiffness for these gears) -- narrow it once a real touch transient is recorded at a sample rate that can resolve the resulting oscillation (kHz-range; see the registry's `dynamic_simulator_note`). | Produces the actual transient shape (rise, overshoot, ringing) instead of an asserted rise-time formula (§F). | `_mesh_torque()` |
| `Tfriction = bshaft·ω` | Viscous shaft/bearing friction. | `bshaft` = `GEAR_SHAFT_FRICTION_NM_S_PER_RAD` (new constant, 1e-6-1e-4 Nm·s/rad) | Applied per node (all five), not per stage. Small value -- with only viscous damping and no separate mesh damping, transients can ring for many ms before settling; a "steady press" signature may not fully settle within a short simulation window. | The load every mesh has to supply just to keep the train spinning, even with nothing touched -- also the reference the equilibrium starting condition (below) is solved against. | `_derivatives()` |

**No motor electrical model.** `motor_1`–`motor_3` (V/R/L/Ke/Kt/Jmotor/b/Tstatic) are not part of this engine -- this rig has no motor datasheet (see `formula_chain_metal.py`'s docstring for why those constants were collapsed into `I_BASELINE_A`/`CURRENT_PER_NM` instead of modeled). Yellow (the motor's own shaft) is driven at a prescribed constant angular velocity -- an idealized, infinitely-stiff speed source -- rather than integrated. A touch applied directly to Yellow still produces a signature (as the extra torque the idealized motor must supply to hold that speed against the disturbance), but the model can never show motor speed sag.

**Equilibrium starting condition.** Starting every mesh at zero twist (`θgap = 0`) would produce an initial gear-train wind-up transient unrelated to the touch. Instead, the simulator solves the `θgap` each mesh needs -- cascaded from Output (free end, only its own friction) back to Yellow -- so that at the nominal rigid-chain speed, with no touch, every node's net torque is already zero. Reported `ΔI` is measured against this equilibrium, not against `I_baseline_A` directly (`I_baseline_A` is a separately-sampled constant, §C -- it isn't derived from this mesh equilibrium, so the two have to be reconciled rather than summed).

**Endpoint:** `POST /api/gearsystem/touch_sim_dynamic` -- same request/response shape as `/api/gearsystem/touch_sim`, selectable via the "Real dynamics" checkbox on the Touch Simulation page.

---

## Per-Gear Formula Load

The current-signature chain (C, D1–D8, E1–E4, F1) is always 14 formulas. The RPM chain length varies with distance from Output.

| Gear | `n` (meshes to Output) | RPM-chain steps | Mesh freq | Signature chain | **Total** |
|---|---|---|---|---|---|
| Red | 1 | 1 | 1 | 14 | **16** |
| Green | 2 | 2 | 1 | 14 | **17** |
| Blue | 3 | 3 | 1 | 14 | **18** |
| Yellow | 4 | 4 | 1 | 14 | **19** |

---

## Open Items

1. **`n` reference-point inconsistency.** `n` is defined as meshes-to-Output, but the current sensor sits at the motor. Yellow — physically *on* the motor shaft, zero meshes from the sensor — currently receives the largest `n` (4), so the model predicts it as the most attenuated and slowest-rising signal when it should arguably be the least attenuated and fastest. Affects D3, D7, E4, F1. Confirm whether this was intentional before trusting absolute magnitudes; relative rankings between the twins are unaffected only if the convention is applied consistently.
2. **Reflected inertia omitted from §D–F (still true there).** `I_rot` in the steady-state model (§E3) counts only the touched gear, and `run_formula_chain()` is unchanged. §G's dynamic model addresses this for the *touch-simulation* path (each node integrates with its own physical inertia, reflected inertia is computed as `reflected_inertia_at_motor_kgm2`), but does not fold it back into `run_formula_chain()`'s `ΔI_impulse` used for gear identification/scoring -- that number still has the compression this item describes.
3. **`ΔI_impulse` units.** Reported in the dashboard as A/(N·ms) at ~10⁶–10⁷ magnitude, which is dimensionally A/(N·m·s). Worth a units audit before comparing against recorded amperes.

---

## Labeling Philosophy

**Assumptions/Validity Limits** are physics-fixed. They describe when the equation is *true*, and they do not move when the project's goals move. `mass = ρπr²w` assumes a solid disc whether you are detecting touches, predicting wear, or estimating startup torque — the idealization is a property of the formula, not of your intent. If a limit is violated, the number is simply wrong and no amount of reinterpretation rescues it; you must fall back to the more general formula (as §D falls back to §E for impact events).

**Use-Case Tags** are contextual. They describe what the number is *for* in this project right now, and they change freely with application. `f = (RPM/60)·T` is tagged here as a gear-identification fingerprint; on a vibration-analysis project the identical formula with identical limits would be tagged as a bearing-fault sideband reference. Same equation, same physics, different job.

**Practical consequence:** when a prediction disagrees with hardware, check Limits first — that tells you whether the model is broken. Check Tags second — that only tells you whether you are using a working model for the wrong question.
