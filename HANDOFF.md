# Handoff: Faulter AI / Yanthros Core, Bottle Machine 64

Written 2026-10-30 to move the work from the old MacBook to a new, faster computer. Everything that matters from the working sessions is either in this repo or listed under "Not in this repo".

## What this project is

"Faulter AI powered by Yanthros Core": a physics-formula engine that builds a per-machine fault-detection twin from the client's STEP assembly and BOM. The first target is **Bottle Machine 64**, a rotary-disk bottle unscrambler. Client is in the USA, we are in India.

Hard rules (decided by the owner, do not relax):
- **Zero guesses.** If any value is missing the software stops and asks. No defaults, no assumed constants.
- **No cloud, no phone-home.** The client forbids it.
- **One offline installable app per machine.** The client's STEP/BOM files are fed into the app on their side; we never see them.
- **Do not suggest any sensor to the client until it is bench-proven in India.** A failed first attempt at the client is unaffordable.
- Licensing: signed contract, perpetual licence, royalty per machine, no hardware lock, no activation-key counting.

## Repo map

| Folder / file | What it is |
|---|---|
| `bottle_machine_64/` | **The product.** `engine/` zero-guess engine (`strict_solver.py`, `step_geometry.py`, `builder.py`, `rulebook.py`, `gear_engine.py`, ...), `app/` Flask builder + formula-flow dashboard, `testdata/mini_sorter/` 10-part fixture, `validation/` gear-physics validation, `docs/mindmap/` 3 software mind maps, `docs/sensor/clamp_placement.svg`, `reference/gear_prototype/` read-only copy of the gear-motor prototype, `spike/` viewer experiments |
| `faulter-formula-brain/` | The core formula engine (333 formulas, `brain.py` + `formulas.py`). Never shipped whole to a client |
| `license_prototype/` | Earlier packet builder, signing and admin dashboard (frozen prototype). Public key only |
| `formula_candidates/` | Cited-formula pilot (100 candidates) staged outside the engine |
| `twin/`, `bottle_twin/` | Earlier 3D twin pages |
| `motor_location/` | This session's motor-location sheets (`MOTORS_1..5`, `FOR_MANUFACTURER_...jpg`, `CHECK_handle_area.jpg`) and the Python that draws them |
| `bottlemachine64-images/` | 82 phone photos (IMG_4052..4135) of the CAD component tree and renders. **The only evidence we have of the machine's structure** |
| `BOTTLE_MACHINE_BOM.md` | Parts list read from the photos, with corrections |
| `CODE_MAP.md`, `code_report/` | Inventory of every code folder on the old Mac |
| `claude_memory/` | Claude's memory notes from the old Mac. Copy into the new machine's Claude memory folder (see below) |
| `.claude/launch.json` | Preview server names and ports (8777, 8779, 8791, 8792, 8795, 8796) with relative paths |

## Setting up on the new PC

1. Clone this repo. Keep `faulter-formula-brain/` as a sibling of `bottle_machine_64/` (paths in the code now resolve relative to the files).
2. Python 3.10+ is required (the old Mac used 3.13.2).
   ```
   cd bottle_machine_64
   python -m venv .venv
   .venv/Scripts/pip install -r requirements.txt      # Windows;  macOS/Linux: .venv/bin/pip
   ```
3. Run the builder app: `bottle_machine_64/.venv/Scripts/python app/server.py` (port 8792).
4. Regenerate the motor sheets: `cd motor_location` then `python annotate_for_manufacturer.py` (needs Pillow). Fonts fall back to Arial on Windows.
5. In `.claude/launch.json`, `python3` is the macOS name; change it to `python` on Windows, and the `.venv/bin/python` entry to `.venv/Scripts/python.exe`.
6. To restore Claude's memory: copy `claude_memory/*` into `~/.claude/projects/<project-folder-name>/memory/` on the new PC after opening the project once in Claude Code.

Known gaps in the code: only 8 part types; real part-level discrimination needs frequency features; radius is read from axis-aligned bounding boxes; qty>1 instances share one folder; branch joins, simultaneous faults and loops are not modelled (a "plan file + join step" is planned). Several older scripts (reference gear prototype, code_report) still contain old Mac paths; they are reference material.

## State of the Bottle Machine 64 work

Built and working on the Mac: STEP reader (cascadio), BOM reader, matching, part-type confirmation, drive links, zero-guess input screen, parallel per-part simulation, result screen with 3D wireframe, formula-flow dashboard (`/flow?name=<project>`), per-motor rulebook with fine / elevated / warning / critical ranges. The gear-physics model was validated against the old gear prototype (`bottle_machine_64/validation/REPORT.md`). Test numbers in the fixture are made-up TEST values.

**The simulated magnitudes have never been compared with real current on a real machine.** The only real data are the old prototype's classification bands and idle current. Proving the absolute scale needs INA228 recordings with a known touch force.

### Facts about the machine (from the CAD tree photos)

- Disc drive motor `INFM0162.B` (CAD text: 33A-GB/H, 90 V DC, 1/8 HP, 120:1, 14 RPM), in `UD03601` with `UB01001` bracket. The real nameplate seen on site is Bison 1/4 HP 20.5:1, which does not match the CAD. Unresolved.
- Belt gearmotor `UP00501` (1/4 HP, 10:1, BLM6200SHP-GFV/GFV6G10AS), mount `US05601` in `US00101`.
- Paddle gearmotor `UP00601` (1/12 HP, 15:1, BLM460SHP-GFV/GFV4G15AS) inside Paddle Wheel Assembly `UX00101` with bracket `UX01001`. The owner considers the black round part a gear system rather than a motor; the CAD parts list still names it GearMotor.
- Knock Down Wheel Assembly `UY02201` is **passive**: slotted bracket, wheel, 1/2" shoulder bolt, L bracket (proven from IMG_4086). It hangs in the air in the renders.
- The belt arms look cantilevered but are tied by a cross rod (owner confirmed). Not a problem.
- The red bodies on the belts are `Red SPRAY BOTTLE` test bottles, not motors.
- Electrical panel in the CAD: 5 driver boards (4x BLE2D200-A, 1x BLE2D60-A), 4 potentiometers, 4 knobs, but only 3 motors drawn. A 4th motor (probably the elevator) is an inference, not proven.
- `INFM0385.A` has no description. Its earlier "brake/encoder" reading was wrong (it leaned on a spray bottle), so it is unidentified.

### Open items (nothing below is proven)

1. **Where are the 3rd and 4th motors?** The question for the company head is drawn in `motor_location/FOR_MANUFACTURER_motors_and_unsupported_parts.jpg`.
2. **The "grey box" at the drum exit.** The owner sees a rectangular grey box that looks like a motor, independent of the drum, at the exit gateway above the first red bottle, below a rotating hand wheel/crank. `CHECK_handle_area.jpg` numbers five candidates (hand crank, grey block with a slot, black round body, tall post, hanging arm) and asks which one it is. **The answer has not come yet.** The blue "grey box" marker on the manufacturer sheet currently sits on the drum end-wall slab, which the owner said is the WRONG object. Move it once the right object is confirmed, and do not regenerate the sheet before then.
3. Nothing was click-verified in the eDrawings viewer. On Windows, select a part in the component tree to highlight it in 3D. Parts to check first: `INFM0162.B`, `UP00501`, `UP00601`, `INFM0385.A`.
4. What drives the disc motor, the BLE2D200-A vs -C driver letter, two BLE2D200 drivers with no confirmed motor, the disc-motor nameplate vs CAD mismatch, and the elevator motor's model and location.

The manufacturer sheet should stay limited to five questions: disc motor right? belt motor right? where are the 3rd and 4th motors? is the grey box a motor? why is the knock-down wheel in the air?

### Sensors

A clamp-placement drawing is in `bottle_machine_64/docs/sensor/clamp_placement.svg`. Decisions so far: the idea of an INA228 on each motor's neutral point was rejected (there is no neutral wire on these motors and it would carry about zero current); clamp sensors (SCT-013) are unproven and must be bench-tested before anything is suggested to the client. A one-page bench-test sheet for the clamp was offered but not made.

## Not in this repo (copy these by USB or another private route)

- `license_prototype/keys/issuer_private.pem` is the licence signing key. **Never put it on GitHub.**
- `bottle_machine_64/spike/ext/V0.2R1 Master Assembly v63.step` (231 MB Voron 0.2 test assembly, over GitHub's file limit) and its wire file.
- The built `.exe` files, the `.venv` folders (rebuild them), the macOS `build/` and `dist/` output of the old packet builder, and the Debian ISO.
- The original `150rpm gear motor prototype/` (82 MB; a read-only copy of the needed part is in `bottle_machine_64/reference/gear_prototype/`). The iPad/BLE apps (GearTwinLive, GearTwinDashboard) are paused.
- Zinaata and ZinaataAndroid (already on GitHub as `yanthros-zinaata` and `zinaata-android`) and `Archive - older projects/`. That archive contains an `openai.key`; if it was ever a live key, rotate it.
- The raw chat transcripts (about 129 MB for this session).

## How the owner likes to work

Short CEO-style replies (1 to 3 sentences). Ask before any major step. The owner runs the pipelines and operations; Claude builds and publishes. Prefer visuals. Say plainly what is verified and what is inference. Do not push into the old repos `vanshxai/faulter_core_new` or `vanshxai/yanthros`. Verify the exact place on a close-up before marking anything on an image, and use a small check image rather than regenerating a whole sheet when the owner's words are ambiguous.

## Offered but not yet approved

Add the disc-motor nameplate-vs-CAD mismatch as a question to the sheet; one-page bench-test sheet for the SCT-013 clamp; plain-language app guide; build plan file + join step; gear/belt ratio coupling.
