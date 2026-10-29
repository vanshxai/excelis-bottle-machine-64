# 150 RPM Gear System — Digital Twin

Standalone Flask web app for a 150 RPM metal internal gearbox: a 3D digital twin, a real physics formula chain, a fault-detection "roulette" game, and (in progress) a live current-sensor gateway.

Run it:
```
pip install -r requirements.txt
python3 gearsystem150_app.py
```
Opens on `http://localhost:5053/twin/gearsystem150`.

## What's real vs assumed

Gearbox topology: Yellow (motor shaft) → Blue → Green → Red → Output (150 RPM, exposed rod, sealed inside the cap).

**Measured (locked, not sampled):**
- Tooth counts — Yellow: 9, Blue: 27/8, Green: 27/8, Red: 27/16 (physically counted, confirmed 2026-07-31)
- Module ≈ 0.448–0.552mm, back-solved from a ~14mm outer-diameter measurement on the 27-tooth gears
- Motor supply voltage: 12V

**Still unmeasured / searched via roulette:**
- Output gear tooth count (sealed inside the cap, 24–40T range)

**Assumed placeholders (not measured for this specific unit):** material density/Young's modulus (generic steel), gear width, motor rotor dimensions. See `constraint_registry_metal.json`'s `soft_constraints` for exact ranges and `source` notes on each.

All of this feeds `formula_chain_metal.py` (steady-state RPM/torque/current formulas, documented in `FORMULA_DATABASE.md`) and `dynamic_gear_simulator.py` (real time-domain RK4 physics sim of touch events per gear). Both are live-wired into the app, not dead code — exercised via the roulette game and the verified-twin flow.

The 3D wireframe (THREE.js) now derives each gear's radius and rendered tooth-box count from these real tooth counts instead of a flat placeholder — see `gearTeeth()`/`makeShaft()` in `gearsystem150_app.py`.

## Live current-sensor gateway — status and history

This is the part still in progress. Short version: **there is currently no real sensor data reaching this app.**

**What happened, in order:**
1. Originally this app read current over USB serial from an ESP32 that turned out to be running a totally unrelated project's dual-channel firmware (an old "Cybertruck" rig — rear motor + front steering motor sensors). Its `REAR`/`FRONT` tags got tangled into this app's live feed, producing meaningless ~3A/~38A alternation with no relation to this gearbox.
2. All of that legacy current-capturing code was deleted (per explicit request) — no serial reader, no calibration, no recordings routes. The HUD's "Live" mode was removed too; only a decorative "Simulated" random-number display was left.
3. A **fresh gateway was rebuilt from scratch**: a background thread in `gearsystem150_app.py` (`_gearsystem_sensor_gateway_loop`) that defaults to `waiting_for_sensor`, rescans local serial ports every 2s for an ESP32-class USB bridge, and the moment one connects and sends `CUR,<TAG>,<current_A>,<raw_mV>` lines, publishes the value straight to the HUD via `/api/gearsystem/live/state`. No tag filtering, no calibration — deliberately minimal "for now."
4. Testing that gateway surfaced the *same* Cybertruck board again (still physically plugged in) — confirmed definitively by dumping its flash with `esptool` and finding the compiled boot string `"Yanthros ESP32 (Mac side) booted -- ESP-NOW receiver"` / `"Scanning WiFi channels for the Cybertruck sender"`. **This board is a pure wireless relay** — it has no local sensor of its own; it just hunts for a second ESP32 ("the Cybertruck sender") broadcasting over ESP-NOW and forwards whatever it hears to USB. The other board, when connected and flash-dumped the same way, confirmed itself as that sender half: `"Yanthros ESP32 (Cybertruck side) booted -- ESP-NOW broadcast sender"`, also carrying `rear`/`front` tags. Neither board has anything to do with this gearbox.
5. Neither board's firmware source exists anywhere on this machine as an editable project file (searched `.ino` and PlatformIO projects broadly) — only the compiled binaries are on the chips.

**What's new (this session's last step):** wrote and flashed fresh sender firmware for this gearbox specifically — `esp32_gearbox_sender/` (PlatformIO project, `src/main.cpp`). It reads an ADC pin and broadcasts `CUR,GEARBOX,<current_A>,<raw_mV>` over ESP-NOW (broadcast address, no pairing).

**Not yet done / open items:**
- The ACS712 sensor is **not yet physically wired** to the sender board (`GPIO34` assumed in code — confirm or change). Right now it's reading a floating pin.
- **Not yet verified that the existing (old Cybertruck) receiver board will actually pick up this new `GEARBOX` broadcast** — its packet-parsing internals aren't known (no source access, only a compiled binary), so compatibility is unconfirmed. If it doesn't work, the fix is writing fresh matching receiver firmware too, rather than reverse-engineering the old one.
- Supply voltage assumption (3.3V) for the ACS712 sensitivity/zero-point math in `esp32_gearbox_sender/src/main.cpp` needs confirming against actual wiring.
- Once real data flows, the gateway's current math is uncalibrated on purpose ("publish it straight through") — a real zero-calibration step is a deliberate next step, not yet built into this version.

## Repo layout
```
gearsystem150_app.py          Flask app: 3D twin, formula routes, roulette, AI fault-check, live-sensor gateway
dynamic_gear_simulator.py     Time-domain RK4 physics sim of touch events
formula_chain_metal.py        Steady-state formula chain (RPM/torque/current)
gearsystem_roulette_metal.py  Roulette game state + card sampling/verification
constraint_sampling.py        Constraint-sampling helpers used by the roulette
constraint_registry_metal.json Source of truth for all constants (hard + soft/searched)
FORMULA_DATABASE.md           Full formula reference/documentation
esp32_gearbox_sender/         New PlatformIO firmware for the gearbox's own ESP32 sender (in progress, see above)
```
