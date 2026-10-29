# 150 RPM Gear System — Digital Twin
## Full Project Documentation (Technical + Non-Technical)

**Document scope:** describes the system as it exists in the codebase today. Written by reading every source file directly (not from memory of past conversations), so it reflects real, current behavior — including places where other project documents (`README.md`) are known to be out of date. Those spots are called out explicitly below.

**Last verified against source:** 2026-08-11.

---

## Table of Contents

**Part 1 — Non-Technical Overview**
1. [What this project is](#1-what-this-project-is)
2. [The physical machine](#2-the-physical-machine)
3. [What "digital twin" means here](#3-what-digital-twin-means-here)
4. [What the system can do today](#4-what-the-system-can-do-today)
5. [What doesn't work yet / open problems](#5-what-doesnt-work-yet--open-problems)
6. [Where the project stands right now](#6-where-the-project-stands-right-now)
7. [Plain-language glossary](#7-plain-language-glossary)

**Part 2 — Technical Documentation**
8. [Architecture at a glance](#8-architecture-at-a-glance)
9. [Repository layout](#9-repository-layout)
10. [Running the app](#10-running-the-app)
11. [The constraint registry (source of truth for constants)](#11-the-constraint-registry-source-of-truth-for-constants)
12. [Physics model](#12-physics-model)
13. [Calibration layer (card-roulette)](#13-calibration-layer-card-roulette)
14. [Live sensor hardware and firmware](#14-live-sensor-hardware-and-firmware)
15. [Detection pipeline](#15-detection-pipeline)
16. [Web UI — page inventory](#16-web-ui--page-inventory)
17. [API reference](#17-api-reference)
18. [Known issues, inconsistencies, and open items](#18-known-issues-inconsistencies-and-open-items)
19. [Technical glossary](#19-technical-glossary)

---

# Part 1 — Non-Technical Overview

## 1. What this project is

This project is a **digital twin of a small 12V gear motor**. In plain terms: there is one real, physical gearbox on a workbench — a motor driving four metal gears (nicknamed Red, Green, Blue, Yellow) in a chain — and there is a piece of software that mathematically predicts, from first-principles physics, exactly how much electrical current that motor should draw at any moment, including what happens to that current when someone touches or interferes with one of the spinning gears.

The end goal is **touch/interference detection using nothing but the motor's current draw** — no cameras, no vibration sensors, no extra hardware on the gears themselves. The idea is: if you know precisely how a healthy machine behaves electrically, you can tell something touched a specific gear just from a blip in the current, the same way an experienced technician can tell an engine is misfiring just by the sound. This is a common real-world technique in industrial equipment monitoring, and this project is a hands-on testbed for building that capability from scratch, gear by gear, with real measurements at every step.

## 2. The physical machine

- **One 12-volt DC motor**, salvaged from its original plastic gear housing, with its internal 4-stage **metal** gearbox kept and run standalone (oiled, tested outside the original casing).
- **Four touchable gears**, arranged Yellow → Blue → Green → Red → (Output). Yellow sits directly on the motor's own shaft; each subsequent gear is driven by the one before it.
- A fifth gear, **Output**, exists but is sealed inside a plastic cap once the rig is fully assembled — it can never actually be touched, so it's excluded from detection, though its tooth count still matters for the math.
- **One real current sensor** (an INA228 precision current-monitor chip) is wired at the motor, reading its supply current hundreds of times per second, streamed over USB through an ESP32 microcontroller into the web app.
- Physical facts that have actually been measured by hand: the tooth count on every gear, the motor's supply voltage (12V), and the gearbox's approximate module (tooth size). Facts that have **not** been measured, and are either assumed (generic steel) or still being searched for computationally, are documented transparently rather than quietly guessed at.

## 3. What "digital twin" means here

A "twin" in this project is not a 3D model for looks — it's a specific **set of numbers** (gear tooth counts, friction coefficients, material properties, an electrical baseline) that, when run through the physics formulas, produce a prediction of what the real motor's current should look like. Because several of those numbers were never physically measured (nobody has taken this exact gearbox apart with a micrometer and a torque wrench), the software generates many *candidate* twins with different guesses for the unknowns, and narrows them down by comparing each candidate's predictions against real touches performed on the actual machine — a process nicknamed "card-roulette" in this codebase (see [§13](#13-calibration-layer-card-roulette)). Whichever candidate best explains real measured data becomes the "verified twin" — the one the live detection system actually trusts.

## 4. What the system can do today

- **View a 3D model** of the gearbox in the browser, with gears sized and toothed according to the real measured tooth counts.
- **Run touch simulations** — pick a gear, pick a touch type (a steady press, a single strike, or a repeated "buzz" from a stationary tool resting against the spinning teeth), and see a predicted current waveform, both from a fast approximate model and from a slower, more realistic physics simulation that accounts for backlash (gear slop) and mesh stiffness.
- **Stream live current** from the real sensor and display it on the same 3D view in real time.
- **Detect which gear is currently being interfered with**, live, using a simple proof-of-concept feature called **Part Interruption** (see [§15](#15-detection-pipeline)): it watches the live current, and if it sits inside one of four experimentally-measured ranges for long enough, it declares "this gear is interrupted" and highlights that gear in the 3D view. It's deliberately simple — no AI, no adaptive learning, no signal processing beyond what's already computed.
- **Run the calibration game** ("roulette") that narrows down the unknown physical constants by comparing simulated candidates against real touches.
- **Ask an AI assistant** (optional, needs an OpenAI API key) to interpret the machine's current state in plain language.

## 5. What doesn't work yet / open problems

- **The motor's own electrical personality is still unknown.** Two key constants that describe how the motor converts electricity into torque (called Kt and Ke) were never properly measured — an earlier shortcut that assumed a value for them was found to be based on faulty reasoning and has been formally retracted (see [§12](#12-physics-model)). A practical measurement plan exists ([MOTOR_PARAMETER_IDENTIFICATION.md](MOTOR_PARAMETER_IDENTIFICATION.md)), but the actual bench measurements haven't been performed yet.
- **The sensor intermittently "disconnects" during real touches.** This has been root-caused: the touching/motor noise electrically disturbs the sensor's data bus, and the sensor chip locks up until the software forces a reset. This is a real hardware/firmware limitation, not a bug introduced by this project's software — it's been diagnosed, but not yet fixed. Three possible fixes have been identified (shorten the automatic recovery time, add bus-recovery logic to the sensor's firmware, or improve the physical wiring/shielding), but none have been implemented yet — this is a decision still waiting on you.
- **One gear's tooth count is still unknown.** The Output gear is sealed inside a cap and has never been counted; the software is still narrowing down its value through the calibration game rather than a direct measurement.
- **A live open question:** you're considering adding a second small motor (a different model, "12V DC 65RPM") to the rig, wired electrically in series with the existing one. As explained in the prior turn, this wouldn't overload anything, but it would make the two motors' electrical behavior interdependent in a way that breaks the current touch-detection ranges — nothing has been changed in the code for this yet, pending your decision on how (or whether) to proceed.

## 6. Where the project stands right now

The **core measurement pipeline works end-to-end**: real sensor → web app → live current display → gear highlighting, verified working via direct testing. The **physics model is built and internally consistent everywhere except the motor's electrical constants**, which are openly flagged as unknown rather than silently guessed. The **Part Interruption detection feature works** for the single-motor rig as currently wired, tuned through several rounds of live testing against your actual touches. The next real decisions on the table are (a) how to physically measure the motor's Kt/Ke constants, (b) what to do about the sensor's I2C noise sensitivity, and (c) whether/how to add a second motor to the rig.

## 7. Plain-language glossary

| Term | Plain-language meaning |
|---|---|
| **Digital twin** | A set of numbers plus formulas that predicts how the real machine behaves electrically. |
| **Touch signature** | The distinctive pattern (size, speed, shape) of the current blip produced when a specific gear is touched. |
| **Baseline current** | How much current the motor draws when it's just running, with nothing touched. |
| **Calibration / roulette** | The process of narrowing down unmeasured physical constants by comparing simulated predictions to real touches. |
| **Verified twin** | The one specific set of constants that has been confirmed (via the roulette process) to best match real behavior. |
| **Part Interruption** | The live feature that watches current in real time and declares which gear is currently being touched. |
| **INA228** | The specific chip used to measure the motor's current very precisely and very fast. |
| **ESP32** | The small microcontroller board that reads the sensor chip and forwards the numbers to the laptop over USB. |
| **I2C** | The two-wire digital connection between the ESP32 and the sensor chip — the thing that gets disrupted by motor electrical noise. |

---

# Part 2 — Technical Documentation

## 8. Architecture at a glance

```
┌─────────────────────────┐        USB serial, plain-text        ┌──────────────────────────────┐
│   ESP32 (esp32_ina228_   │  "<signed int mA>\n" @ ~893 Hz  --> │  Flask app (gearsystem150_    │
│   reader firmware)       │ <---------------------------------  │  app.py + gearsystem/ package)│
│   + INA228 current chip  │                                     │                                │
└─────────────────────────┘                                     └──────────────┬─────────────────┘
                                                                                │
                                                        ┌───────────────────────┼───────────────────────┐
                                                        │                       │                       │
                                                 detection/               physics/ + signature/     calibration/ + twin/
                                              (live acquisition,        (formulas: RPM chain,       (card-roulette search,
                                               block averaging,          torque/current, RK4          verified-twin storage)
                                               gear classification,      dynamics, motor model)
                                               Part Interruption)
                                                        │                       │                       │
                                                        └───────────────────────┼───────────────────────┘
                                                                                │
                                                                          api/ (Flask blueprints)
                                                                                │
                                                                      templates.py (3D view, HUD,
                                                                    roulette UI, touch-sim UI, etc.)
```

The app is a **single Flask process** (`gearsystem150_app.py`, port **5053**), organized as one Python package, `gearsystem/`, split into six layers:

| Layer | Responsibility |
|---|---|
| `twin/` | Pure data I/O — loading the constraint registry, loading/saving the verified twin. No physics. |
| `calibration/` | The card-roulette search loop: sample candidate constants, score them against real touches, narrow ranges, verify a winner. |
| `physics/` | The actual formulas — gear kinematics, torque↔current conversion, the (currently unwired) motor electrical model, disturbance injection. |
| `signature/` | Turns a twin's constants into a predicted current signature — both the fast steady-state version and the slow real-dynamics (RK4) version. |
| `detection/` | Everything to do with the *real*, *live* sensor: serial acquisition, block averaging, gear classification, the Part Interruption feature. |
| `api/` | Flask blueprints (thin HTTP wrappers over the layers above) plus all page templates (the actual HTML/JS/CSS shipped to the browser). |

This is a **Phase-1 architecture refactor** — the original monolithic `gearsystem150_app.py`, `dynamic_gear_simulator.py`, `formula_chain_metal.py`, and `constraint_sampling.py` files still exist at the project root as thin re-export shims (per their own docstrings) in case anything external imports them directly, but all real logic now lives inside `gearsystem/`.

## 9. Repository layout

```
150 rpm gear system/
├── gearsystem150_app.py              Flask app factory: registers all blueprints, starts the sensor gateway thread
├── gearsystem/                       All real application logic
│   ├── twin/
│   │   ├── model.py                  Twin — a thin structural wrapper around a constants dict
│   │   └── store.py                  load_registry() / load_verified() / save_verified() — JSON file I/O
│   ├── calibration/
│   │   ├── sampling.py               Generic min/max-range sampling helpers
│   │   ├── search.py                 The full roulette workflow: build cards, score, narrow, verify
│   │   └── state.py                  Persists one in-progress roulette round to disk between HTTP calls
│   ├── physics/
│   │   ├── gear_train.py             RPM chain, mesh frequencies, RK4 mechanical dynamics (the core formula engine)
│   │   ├── current_model.py          The one torque→current conversion function, and its algebraic inverse
│   │   ├── motor.py                  Motor rotor inertia (the only motor-body quantity actually computed)
│   │   ├── electrical.py             V=iR+Ldi/dt+Keω armature model — built, verified standalone, NOT wired into the simulator
│   │   └── disturbance.py            Documented-but-unimplemented pressure-based touch model (stub)
│   ├── signature/
│   │   ├── steady_state.py           Thin wrapper over gear_train's fast (non-integrated) signature calculation
│   │   ├── dynamic.py                simulate_touch() — the real RK4 time-domain touch transient
│   │   ├── electrical_comparison.py  Side-by-side comparison of the existing model vs. the electrical model (Stage 2)
│   │   └── waveform_display.py       Hand-shaped exponential waveform for the fast/cosmetic touch-sim page
│   ├── detection/
│   │   ├── acquisition.py            Owns the serial port: finds the ESP32, reads its protocol, reconnects on failure
│   │   ├── live_state.py             The one shared mutable-state module (current reading, calibration, Part Interruption config)
│   │   ├── signal_processing.py      Turns raw sample blocks into smoothed/classified state; owns zero-calibration
│   │   └── matching.py               Two classifiers: gear_matches() (verified-twin force-fit) and compare_to_dynamic_model()
│   └── api/
│       ├── pages.py                  Page routes (render_template_string wrappers)
│       ├── templates.py              All HTML/CSS/JS for every page (2,600+ lines)
│       ├── twin_routes.py            Placeholder blueprint (no dedicated routes yet)
│       ├── calibration_routes.py     /api/gearsystem/roulette_metal/* and /twin_batch
│       ├── signature_routes.py       /api/gearsystem/motor_chain, /touch_sim, /touch_sim_dynamic, /touch_sim_electrical_comparison
│       ├── detection_routes.py       /api/gearsystem/live/*
│       └── admin_routes.py           /api/admin/* (company info, AI chat/fault-check)
├── constraint_registry_metal.json    Source of truth for every physical constant (hard facts + searchable ranges)
├── gearsystem_metal_verified_twin.json   The currently "verified" twin (constants + cached signatures), written by calibration.search.verify()
├── gearsystem_roulette_metal_state.json  The in-progress roulette round, if any
├── FORMULA_DATABASE.md               Full human-readable formula reference (16 formulas, A–G)
├── MOTOR_PARAMETER_IDENTIFICATION.md Measurement plan for the still-unknown motor constants (Ra/La/Kt/Ke)
├── README.md                         ⚠️ Stale — describes an earlier ACS712 + ESP-NOW wireless architecture that has since
│                                        been fully replaced by the direct-USB INA228 setup described in this document (§14).
├── esp32_ina228_reader/src/main.cpp  Current, in-use ESP32 firmware (INA228 over I2C, plain-text serial output)
├── esp32_gearbox_sender/src/main.cpp Dead code — an earlier ACS712/ESP-NOW firmware attempt, superseded, not used
└── requirements.txt                  flask, openai, pyserial
```

## 10. Running the app

```bash
pip install -r requirements.txt
python3 gearsystem150_app.py
```

Opens at **`http://localhost:5053/twin/gearsystem150`**.

**Must be launched this exact way** — `start_gearsystem_sensor_gateway()` (the background thread that reads the real sensor) is only called inside `gearsystem150_app.py`'s `if __name__ == "__main__":` guard. Launching via `python3 -c "from gearsystem150_app import app; app.run(...)"` or any other import-based method silently skips starting the sensor gateway, and the live current features will appear stuck at "waiting for sensor" with no visible error.

## 11. The constraint registry (source of truth for constants)

**File:** [constraint_registry_metal.json](constraint_registry_metal.json)

Every physical constant used anywhere in the physics/signature layers is declared here, split into two sections:

- **`hard_constraints`** — settled facts, not sampled or searched. Includes the measured tooth counts (Yellow 9T; Blue, Green, Red each a compound gear — 27T/8T, 27T/8T, 27T/16T respectively), the measured motor supply voltage (12V), the measured Output shaft speed (150 RPM), and material/geometry placeholders.
- **`soft_constraints`** — each has a `min`/`max` range. Where a value has actually been measured, `min == max` (pinning it) so every sampled twin gets the true value with no code changes needed. Genuinely unknown values (currently only `TEETH_OUTPUT_BIG`, 24–40T) keep a real range and are still searched via calibration.

Every constant's `source` field documents **how it was obtained** — `measured`, `assumed` (a stand-in, e.g. generic steel density), or `estimated`/`unknown_motor_parameter` (an explicit placeholder with no physical basis, most notably `MOTOR_Kt_NM_PER_A` and `MOTOR_Ke_V_S_PER_RAD` — see [§12.5](#125-the-motor-electrical-model-and-its-known-inconsistency)). The file's own `dependency_links` array documents which downstream calculations each constant feeds, and `validation_rule` documents the one sanity gate (RPM chain must be finite/positive/bounded) that discards physically impossible sampled variants before they're ever scored.

**Note:** `hard_constraints` still contains `ACS712_30A_NOISE_FLOOR_FILTERED_A` / `ACS712_30A_NOISE_FLOOR_UNFILTERED_A`, leftover from an earlier sensor (see [§18](#18-known-issues-inconsistencies-and-open-items)) — confirmed via direct search to be **read by no current Python code**. The live pipeline's actual noise floor is `live_state.NOISE_FLOOR_MIN = 0.06` A, set from real measured noise with the current INA228 sensor, not from these stale registry values.

## 12. Physics model

Full formula-by-formula reference lives in [FORMULA_DATABASE.md](FORMULA_DATABASE.md) (16 unique formulas, sections A–G). This section summarizes it and maps it to code.

### 12.1 Gear train topology

```
Yellow (motor shaft, 9T) → Blue (27T/8T) → Green (27T/8T) → Red (27T/16T) → Output (sealed, unmeasured, 24–40T)
```

Only Yellow, Blue, Green, Red are touch points (`physics/gear_train.py::TOUCH_POINTS`). Output cannot physically be touched once assembled but its tooth count still anchors the RPM chain.

### 12.2 Steady-state chain (`physics/gear_train.py::run_formula_chain`)

The fast, non-integrated model, run thousands of times per calibration round:

1. **RPM chain** — worked backward from the known Output speed (150 RPM) through Red→Green→Blue→Yellow via tooth-count ratios. Validated: every stage's RPM must be finite, > 0.01, and ≤ 150×200, or the whole variant is discarded.
2. **Mesh frequency** per gear — `f = (RPM/60) · teeth`, the tooth-passing frequency, used as a frequency-domain fingerprint independent of amplitude.
3. **Baseline current** (`I_BASELINE_A`) — set directly from a real live measurement (0.022 A, idle, motor running, capless), **not derived** from voltage/resistance/torque-constant, because those three are still unknown and current alone can never separate them.
4. **Steady-force ("held press") model** — pitch radius from tooth count and module → torque per newton of touch force (via a Coulomb-friction idealization) → current via the single lumped gain `CURRENT_PER_NM` (a stand-in for `1/Kt` that is *touch-point-referenced*, not armature-referenced — this distinction is the root of the Kt/Ke inconsistency, see §12.5).
5. **Impact-response ("screwdriver strike") model** — added after real touch data showed <10ms current spikes with a barely-moving mean, i.e. an impulse response, not a sustained-force response. Uses each gear's computed rotational inertia (solid-disc idealization from measured density/geometry) so a heavier gear absorbs more of a given impact.
6. **Rise time** — an empirical `t₀·(1 + 0.15n)` formula, `n` = mesh-count from the touch point to Output.

A second entry point, `run_formula_chain_capless()`, exists for when the cap/Output gear is physically removed from the rig — it re-anchors the whole chain on a directly supplied `rpm_yellow` instead of the (now-invalid) 150 RPM Output assumption, and runs the cascade *forward* (motor outward) instead of backward.

### 12.3 Dynamic (RK4) model (`physics/gear_train.py`, `signature/dynamic.py`)

A separate, slower engine that adds what the steady-state chain explicitly does not model: **backlash** (gear slop — a dead-zone before mesh torque engages), **mesh stiffness** (a torsional spring, derived from a tooth-as-cantilever-beam bending model rather than swept as an independent unknown), and **reflected inertia** of the rest of the drivetrain. Numerically integrates each node's `(θ, ω)` state via fixed-timestep RK4, starting from a solved equilibrium (not zero-twist, to avoid a spurious wind-up transient at t=0) and injecting the touch as a torque/impulse directly at the touched node.

Three physically distinct touch types are modeled (`signature/dynamic.py::simulate_touch`):
- **`steady`** — a held press, constant torque for the whole window.
- **`impact`** — one single strike, a brief pulse then free ringing.
- **`tooth_strike`** — a stationary tool tip repeatedly rapped by every passing tooth, at that gear's own mesh frequency, for the whole window.

Yellow's own angular velocity is **prescribed constant** (an idealized, infinitely-stiff motor speed source), not integrated — this is a deliberate simplification (no motor electrical model backs it yet) with a direct consequence documented in §12.5 and §18.

This is the **slow path**, deliberately run only once per twin, at calibration-verify time (`calibration/search.py::verify()` → `signature/dynamic.py::generate_signature_library()`), and cached into the verified-twin JSON so the live comparison endpoint doesn't have to re-simulate on every poll.

### 12.4 Torque↔current conversion (`physics/current_model.py`)

The single conversion point used everywhere: `delta_I = delta_torque_nm * CURRENT_PER_NM (+ baseline)`. Its algebraic inverse, `implied_force_n()`, is what lets a live current delta be converted back into "how much force would explain this," which both the calibration scorer and the live gear-matcher use to rank candidate gears.

### 12.5 The motor electrical model, and its known inconsistency

`physics/electrical.py` implements the standard DC motor equation `V = R·i + L·(di/dt) + Ke·ω` as a **standalone, verified, but completely unwired** module — nothing in the live simulator calls it. It exists for **Stage 2 comparison only** (`signature/electrical_comparison.py`, reachable via `POST /api/gearsystem/touch_sim_electrical_comparison`), run side-by-side against the existing model, never replacing it.

**The inconsistency, precisely:** `MOTOR_Kt_NM_PER_A` and `MOTOR_Ke_V_S_PER_RAD` were originally set (Stage 0) from `1/CURRENT_PER_NM`, using the identity `Ke = Kt` for an ideal motor. This was a category error: `CURRENT_PER_NM` is a *touch-point-referenced, gear-train-lumped* empirical gain (it already has gear-ratio and touch-radius effects baked in), while `Kt`/`Ke` are properties of the bare *armature/Yellow shaft* — no gear-ratio reflection was ever applied between the two reference frames. Running the numbers, `Ke·ω` at the verified twin's Yellow speed comes out to roughly **146V**, far exceeding the 12V supply — a physical impossibility that is direct evidence the stored value is wrong, not evidence of an unusual motor.

**Current status (post Stage 2.6):** both fields are marked `"unknown_motor_parameter": true` in the registry, with their `source` text formally retracting the derivation. The numeric `min`/`max` values were deliberately left unchanged (so nothing downstream silently shifts) but are explicitly documented as **stale and physically meaningless** — not a measurement, not a default. [MOTOR_PARAMETER_IDENTIFICATION.md](MOTOR_PARAMETER_IDENTIFICATION.md) lays out the actual measurement plan: a locked-rotor test (Ra, Kt, and La if a fast-enough sampling path is available) plus a driven/no-supply generator-mode test (Ke) — two sessions, four measurements, no dependency on `CURRENT_PER_NM`. **No measurement has been performed yet; this remains open.**

### 12.6 Known modeling simplifications, stated plainly

These are documented in-code and in `FORMULA_DATABASE.md`'s "Open Items," not hidden:
- **`n` (mesh-count) reference inconsistency**: `n` is defined as meshes-to-*Output*, but the sensor physically sits at the *motor*. Yellow — zero meshes from the sensor — currently receives the *largest* `n`, meaning the steady-state model predicts it as the most attenuated/slowest-rising signal, which is questionable given where the sensor actually is. Not yet resolved; relative gear rankings are unaffected only if the convention is applied consistently everywhere (which it currently is).
- **Reflected inertia** is included in the RK4 dynamic model but not folded back into the steady-state chain's impact-response sensitivity (`ΔI_impulse`) used for live gear identification.
- **`ΔI_impulse` units** are reported at ~10⁶–10⁷ magnitude (A per N·m·s) — flagged as needing a units audit before direct comparison against recorded amperes.

## 13. Calibration layer (card-roulette)

**File:** [gearsystem/calibration/search.py](gearsystem/calibration/search.py)

Workflow (unchanged since before the Phase-1 refactor):

1. **Load registry** → **identify unknown parameters** (`calibration/sampling.py::soft_ranges()`, only entries with real min/max spread).
2. **Generate N candidate twins** (default 20, `_build_cards()`) — each with independently sampled constants, run through the fast steady-state chain, discarding physically invalid variants.
3. Present all candidates ("cards") to the user; each is scored live against the real sensor's current delta (`guess_for_card()` → `physics/current_model.py::rank_candidates_by_force_fit()` → implied touch force per gear, filtered to a plausible 0.1–15N range, closest-to-2N-reference wins).
4. **Pick a winner** (`pick_closer()`) → ranges are narrowed directionally around the winner (each parameter's search window shrinks by 20% and re-centers, tracking whether the winner moved up or down from the previous round) → a new generation of cards is built.
5. Repeat until convergence.
6. **Verify** (`verify()`) — locks in a specific card as the "verified twin," additionally running the *slow* RK4 dynamic simulation once for all four gears (`signature/dynamic.py::generate_signature_library()`) and caching the result. Saved to [gearsystem_metal_verified_twin.json](gearsystem_metal_verified_twin.json).

The verified twin is what both `detection/matching.py::gear_matches()` (the live fault-o-meter) and `compare_to_dynamic_model()` (the live-vs-model comparison page) read at runtime — calibration and live detection are decoupled by this one JSON file.

## 14. Live sensor hardware and firmware

**⚠️ Note:** `README.md` describes an earlier, now-fully-replaced architecture (ACS712 analog sensor + a pair of ESP32 boards talking wirelessly over ESP-NOW, one of which turned out to be someone else's unrelated "Cybertruck" project board). That entire approach was abandoned. **What is actually running today** is described below, verified directly from `detection/acquisition.py` and `esp32_ina228_reader/src/main.cpp`.

### 14.1 Hardware

- **Sensor:** Adafruit INA228 breakout (current/power monitor), onboard shunt = 0.015Ω, configured for a **±5.0A** range (`MAX_CURRENT_A` in firmware).
- **Bridge:** an ESP32 dev board, connected to the sensor via I2C (SDA=GPIO21, SCL=GPIO22, 400kHz Fast Mode) and to the laptop via **USB serial** (not wireless).
- **Wire protocol:** one signed integer, in whole milliamps, per line of plain text (e.g. `"23\n"`, `"-4\n"`) at **460800 baud**. Deliberately switched away from an earlier binary block-framing protocol (magic bytes, checksums) once the actual data rate turned out low enough (~1.8 KB/s) that packing was pure overhead.
- **Sample rate:** INA228 configured for `CONT_SHUNT` mode (current-only, no bus-voltage conversion), 4x hardware averaging, 280µs conversion time → a theoretical ceiling of **~893 Hz**. Confirmed rock-solid at that rate with the motor off; **degrades to 74–450Hz, unevenly, with the motor running** — see §14.3.

### 14.2 The DTR/RTS boot bug (found and fixed this project)

**Symptom:** the webapp never received any sensor data — not corrupted, not slow, literally zero bytes.

**Root cause:** `pyserial` asserts both DTR and RTS high by default on `serial.Serial(...)` and never releases them. On this ESP32 board's auto-reset circuit, that holds the chip's EN/reset line active continuously, so it **never boots at all**. Confirmed via a standalone experiment (opening the port, printing DTR/RTS state, then explicitly releasing both) — released, the boot banner and INA228 init appeared within under a second; left at pyserial's default, nothing ever arrived.

**Fix** ([acquisition.py:116-119](gearsystem/detection/acquisition.py)):
```python
ser.dtr = False
ser.rts = False
time.sleep(2)  # let the board finish booting (banner + INA228 init) before reading
ser.reset_input_buffer()
```
Verified end-to-end afterward: boot banner → I2C scan → INA228 init → self-test samples → the live text stream, all confirmed reaching the webapp and its `/raw_waveform` / validation-page endpoints without regression.

### 14.3 The I2C noise / disconnect issue (diagnosed, NOT yet fixed)

**Symptom, reported during live testing:** the sensor appears to "disconnect" mid-test; the UI shows `waiting_for_sensor`.

**Root cause:** motor electrical noise (worse under touch/load) corrupts I2C bus transactions. A confused I2C slave can hold the SDA line low, blocking *all* future transactions until something resets the bus — this is a hardware/protocol-level failure mode, below the layer where a "value" would even exist, which is why it presents as total silence rather than garbled numbers or a value stuck at zero.

**Existing mitigation (recovery, not prevention):** `acquisition.py`'s `_INA228_STALE_RECONNECT_S = 8` — if no bytes arrive for 8 seconds while still marked connected, the code raises and forces a full reconnect, which happens to reset the ESP32 via the DTR toggle on port reopen (the same mechanism that caused §14.2, now working in the app's favor for recovery). The firmware itself also shortens its I2C bus timeout from pyserial's default 50ms to **5ms** (`Wire.setTimeOut(5)`) specifically because measured stall gaps matched `(gap_ms / 50ms)` stalled transactions almost exactly — i.e., a large fraction of I2C reads were already stalling against noise, each eating the full 50ms before giving up.

**Not yet done:** no fix for the underlying noise susceptibility itself. Three options have been identified but none implemented: (1) shrink `_INA228_STALE_RECONNECT_S` for faster recovery, (2) add I2C bus-recovery logic (a clock-pulse unstick routine) to the ESP32 firmware, (3) improve physical wiring/shielding between the motor and the sensor leads. **This is an open decision, not a pending task in progress.**

### 14.4 Firmware file status

- [esp32_ina228_reader/src/main.cpp](esp32_ina228_reader/src/main.cpp) — **current, in use.** Well-commented with its own v2→v4 protocol history.
- [esp32_gearbox_sender/src/main.cpp](esp32_gearbox_sender/src/main.cpp) — **dead code.** An earlier ACS712 + ESP-NOW attempt (see `README.md`'s history section), superseded before it was ever fully wired up. Not started by any code path today.

## 15. Detection pipeline

**Files:** [acquisition.py](gearsystem/detection/acquisition.py), [live_state.py](gearsystem/detection/live_state.py), [signal_processing.py](gearsystem/detection/signal_processing.py), [matching.py](gearsystem/detection/matching.py)

### 15.1 Data flow

```
ESP32 (one int mA per line)
  → acquisition.sensor_gateway_loop()      reads lines, batches 256 samples/block (~287ms/block)
      → live_state.raw_buffer               unconditional raw ring buffer (waveform inspection, bypasses everything below)
      → signal_processing.process_block()   computes mean_mA, current_A = mean_mA/1000
          → live_state.state["current_A"]   published — this is what the "Current Feed" HUD card shows
          → (if CLASSIFY_ENABLED) matching.gear_matches()   verified-twin force-fit classifier → live_state.state["detected_gears"]
          → update_part_interruption(current_A)   the Part Interruption detector (independent, always runs)
              → live_state.state["part_interruption_gear"]
```

Two genuinely separate, independent classifiers exist side by side and are **not** unified (an explicit design decision — the user's constraint was "preserve current behavior," not "improve classification"):

### 15.2 `gear_matches()` — the verified-twin force-fit detector

Drives the older "fault-o-meter" style feature. Pure function of the current live delta: computes each gear's implied touch force (using the verified twin's own `delta_I_per_N_A` sensitivities), keeps only gears whose implied force clusters within 25% of the single best-fit gear's force. Stateless — every reading is judged fresh, which fixed an earlier bug where a slow-adapting baseline could get permanently "stuck" reading as touched after a motor power-cycle. Requires a verified twin and a completed zero-calibration to produce any output. **Currently `CLASSIFY_ENABLED = False`** in `live_state.py` (temporarily disabled while raw waveforms are being inspected directly) — flipping it back to `True` restores this path with no other code change needed.

### 15.3 Part Interruption — the fixed-range experimental detector

A deliberately simple, temporary proof-of-concept, independent of the twin/calibration system entirely — it uses fixed, experimentally-measured current ranges for *this specific* gearbox, tuned through several rounds of live testing directly against your touches. Config lives entirely in [live_state.py](gearsystem/detection/live_state.py):

```python
PART_INTERRUPTION_IDLE_MAX_A = 0.025
PART_INTERRUPTION_RANGES_A = {
    "Red":    (0.031, 0.034),
    "Green":  (0.035, 0.042),
    "Blue":   (0.043, 0.090),
    "Yellow": (0.091, float("inf")),
}
PART_INTERRUPTION_HOLD_S = 0.25
```

State machine (`signal_processing.py::update_part_interruption()`), fed the exact same block-mean `current_A` the Current Feed HUD card displays (explicitly *not* a separately-sampled or separately-smoothed value, per direct user instruction after an earlier version was wired to noisy raw per-sample current instead):

- **Below idle threshold** → clears any pending or declared gear immediately (no lag on release).
- **Above idle, nothing declared yet** → tracks which range the reading currently falls in; if it changes, the hold timer resets; only declares a gear once the *same* range has held continuously for `PART_INTERRUPTION_HOLD_S` (~250ms).
- **Once declared → sticky.** The declared gear stays published even if current later climbs into a *different* gear's range — a harder push reads as a bigger current on the same gear, not a switch to a new one. Only a genuine drop back to idle clears the lock.

Reset on every sensor reconnect (`acquisition.py`), so a stale declaration never survives a reconnect.

Explicitly out of scope by design: adaptive thresholds, FFT/frequency analysis, machine learning, automatic calibration. Ranges are edited directly in `live_state.py`; nothing else needs to change to retune them.

### 15.4 Live zero-calibration (separate from both classifiers above)

`signal_processing.py::run_zero_calibrate()` — a one-time, on-demand capture of the current live baseline as a fixed zero-reference (the "speedometer" design: calibrate once, then every reading compares against that fixed scale, rather than continuously adapting). Fires automatically ~8s after every reconnect (`auto_calibrate_after_connect()`), and is also exposed manually via `POST /api/gearsystem/live/zero_calibrate`. Tracks a `connect_generation` counter so a slow calibration in progress during a reconnect discards its own stale result instead of overwriting a newer session's zero point. This is **unrelated** to the Calibration *layer* (§13) despite sharing the word "calibrate" — one is a live sensor zero-reference, the other is the offline twin-parameter search.

## 16. Web UI — page inventory

All routes registered in [gearsystem/api/pages.py](gearsystem/api/pages.py); all markup lives in [gearsystem/api/templates.py](gearsystem/api/templates.py).

| Route | Page | Purpose |
|---|---|---|
| `/twin/gearsystem150` | Main 3D twin | Live 3D view, HUD (Current Feed / Part Interruption / Feed Mode), gear highlighting, motor-click physics popup, admin panel (AI chat) |
| `/twin/gearsystem150/roulette` | Calibration roulette | The card-roulette UI — generate candidates, view live guesses per card, pick a winner, verify |
| `/twin/gearsystem150/twins` | Twin batch inspector | Independent batch of sampled twins for inspection, not tied to an active roulette round |
| `/twin/gearsystem150/touch-sim` | Touch simulation | Pick a gear + touch type + force/impulse, view predicted waveform (fast steady-state or real RK4 dynamics via a checkbox) |
| `/twin/gearsystem150/live-model` | Live vs. model | Real sensor delta shown side-by-side with the verified twin's cached RK4 predictions per gear |
| `/twin/gearsystem150/motor` | Motor physics detail | Full RPM/frequency/current chain for the verified twin, plus motor nameplate facts |
| `/twin/gearsystem150/raw` | Raw waveform | Direct dump of the unprocessed per-sample ring buffer — bypasses all smoothing/classification |
| `/twin/gearsystem150/validate` | Validation | Generic constants-form + live comparison, used during development to sanity-check a twin against live readings |

**Known stale UI text:** the Motor page template hardcodes the sensor label as `"ACS712-30A"` ([templates.py:1884](gearsystem/api/templates.py)) — left over from the pre-INA228 architecture; the actual sensor is the INA228 (see §14, §18).

## 17. API reference

All routes are Flask blueprints registered in `gearsystem150_app.py`.

**Calibration** (`gearsystem/api/calibration_routes.py`)
| Route | Method | Purpose |
|---|---|---|
| `/api/gearsystem/twin_batch` | GET | Generate an independent batch of 20 sampled twins |
| `/api/gearsystem/roulette_metal/start` | POST | Start a new roulette round |
| `/api/gearsystem/roulette_metal/state` | GET | Current round's cards/ranges |
| `/api/gearsystem/roulette_metal/guesses` | GET | Live per-card guesses against the real sensor delta |
| `/api/gearsystem/roulette_metal/pick_closer` | POST | Pick a winning card, narrow ranges, generate next round |
| `/api/gearsystem/roulette_metal/verify` | POST | Lock in a card as the verified twin (also runs the RK4 signature library) |
| `/api/gearsystem/roulette_metal/verified` | GET | The current verified twin, if any |

**Signature / simulation** (`gearsystem/api/signature_routes.py`)
| Route | Method | Purpose |
|---|---|---|
| `/api/gearsystem/motor_chain` | GET | Full physics chain for the verified twin (motor popup + motor page) |
| `/api/gearsystem/touch_sim` | POST | Fast, cosmetic touch waveform (hand-shaped exponential) |
| `/api/gearsystem/touch_sim_dynamic` | POST | Real RK4 time-domain touch waveform |
| `/api/gearsystem/touch_sim_electrical_comparison` | POST | Stage-2 side-by-side: existing model vs. experimental electrical model |

**Live detection** (`gearsystem/api/detection_routes.py`)
| Route | Method | Purpose |
|---|---|---|
| `/api/gearsystem/live/zero_calibrate` | POST | Manually trigger zero-reference calibration |
| `/api/gearsystem/live/state` | GET | Full live state (current, history, connection status, Part Interruption gear, etc.) — polled by the HUD |
| `/api/gearsystem/live/detect` | GET | Overall calibrated delta/noise-floor status |
| `/api/gearsystem/live/raw_waveform` | GET | Raw unprocessed per-sample buffer dump |
| `/api/gearsystem/live/model_compare` | GET | Live sensor vs. verified twin's cached RK4 predictions |

**Admin** (`gearsystem/api/admin_routes.py`)
| Route | Method | Purpose |
|---|---|---|
| `/api/admin/company_info` | GET/POST | Free-text context blob fed to the AI assistant |
| `/api/admin/ask_ai` | POST | OpenAI-backed chat / fault-check mode (requires `OPENAI_API_KEY` env var or an `openai.key` file — not configured by default) |

## 18. Known issues, inconsistencies, and open items

| # | Item | Status |
|---|---|---|
| 1 | `MOTOR_Kt_NM_PER_A` / `MOTOR_Ke_V_S_PER_RAD` are unknown motor parameters; the physical measurement plan exists but hasn't been executed | **Open** — see §12.5, [MOTOR_PARAMETER_IDENTIFICATION.md](MOTOR_PARAMETER_IDENTIFICATION.md) |
| 2 | Sensor disconnects during real touches, due to I2C bus lockup from motor electrical noise | **Diagnosed, not fixed** — see §14.3 |
| 3 | `TEETH_OUTPUT_BIG` (Output gear tooth count) still unmeasured, only bounded 24–40T | **Open** — still searched via calibration |
| 4 | `n` (mesh-count) convention inconsistency: Yellow is physically closest to the sensor but modeled as furthest | **Open** — see §12.6 |
| 5 | `README.md` describes a superseded ACS712 + ESP-NOW architecture, not the current INA228-over-USB one | **Documentation debt** — this document (§14) reflects current reality |
| 6 | Motor page UI hardcodes `"ACS712-30A"` as the sensor label | **Documentation/UI debt** — cosmetic only, doesn't affect data |
| 7 | `ACS712_30A_NOISE_FLOOR_*` constants remain in the registry, unread by any current code | **Dead data**, harmless |
| 8 | `gear_matches()` (verified-twin classifier) currently disabled (`CLASSIFY_ENABLED = False`) while raw waveforms are inspected directly | **Intentional, temporary** — flip the flag to restore |
| 9 | Reflected inertia not folded into the steady-state impact-response sensitivity used for live classification (only in the RK4 dynamic model) | **Open**, documented simplification |
| 10 | `ΔI_impulse` units need an audit (reported at ~10⁶–10⁷ magnitude) | **Open**, documented simplification |
| 11 | Whether/how to add a second motor (electrical series vs. parallel) to the rig | **Open decision**, pending — see conversation context; would require re-measuring all Part Interruption ranges regardless of which wiring is chosen |

## 19. Technical glossary

| Term | Meaning in this codebase |
|---|---|
| **Twin / constants** | A dict of concrete values for every soft constraint — one sampled candidate, or the verified winner |
| **Soft constraint** | A registry entry with a min/max range — sampled during calibration |
| **Hard constraint** | A settled, non-sampled fact in the registry |
| **`I_BASELINE_A`** | The motor's measured idle current (0.022A), used as the zero-reference for the steady-state formula chain (distinct from the live zero-calibration in §15.4) |
| **`CURRENT_PER_NM`** | The lumped, touch-point-referenced torque→current gain; stands in for `1/Kt` but is NOT equal to it (see §12.5) |
| **Capless** | Rig configuration with the Output gear/cap physically removed; re-anchors the RPM chain on a measured `rpm_yellow` instead of the 150 RPM Output assumption |
| **Steady-state chain** | The fast, non-integrated formula path (`gear_train.run_formula_chain`) |
| **Dynamic / RK4 model** | The slow, numerically-integrated mechanical model with backlash/mesh-stiffness/reflected inertia |
| **`CLASSIFY_ENABLED`** | Flag in `live_state.py` gating the verified-twin force-fit classifier on/off |
| **Part Interruption** | The independent, fixed-range, sticky-lock live detector (§15.3) |
| **Zero-calibration** | A one-time capture of the live baseline as a fixed comparison reference |
| **Verified twin** | The twin locked in via `calibration.search.verify()`, stored in `gearsystem_metal_verified_twin.json` |
| **Block** | 256 consecutive raw samples (~287ms at ~893Hz), the unit `signal_processing.process_block()` operates on |
