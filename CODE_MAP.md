# Faulter / Yanthros / Excelis - where every piece of code lives

Written 2026-10-10 from a scan of this Mac. Paths are absolute. "Backed up?" says whether the code also exists on GitHub (account `vanshxai`).

## How this list was made (and its limits)

- Searched `Desktop`, `Documents`, `Downloads` and the home-folder folders (`pi`, `Apps`, `bin`, `tatvalabz-agent`) for any folder or file named faulter / yanthros / zinaata / dorus / excelis / geartwin / bottle machine / unscrambler.
- Opened every code, text and data file in those places and kept the ones that mention faulter, yanthros, zinaata or dorus (309 files).
- Spotlight search returned nothing on this Mac, so everything was checked by walking the folders directly.
- NOT covered: external drives (none connected), iCloud, other computers, phones/iPads, and any cloud account other than GitHub.
- The older projects in `Archive - older projects` and `Downloads/Yanthros_fresh` were located and measured, not read.

## 1. The product being built now (Bottle Machine 64)

| Path | What it is | Size / code | Backed up? |
|---|---|---|---|
| `/Users/mac/Desktop/excelis/bottle_machine_64/` | The new per-machine app: STEP + BOM in, wireframe and fault-current rulebook out | 138 files, 76 Python/HTML files, about 9,800 lines (without the virtual environments) | NO. Only on this Mac |
| `.../bottle_machine_64/engine/` | The brain of the app (14 Python files): `step_geometry`, `bom_reader`, `matching`, `part_types`, `linking`, `formula_pack`, `strict_solver`, `runtime`, `builder`, `live_match`, `flow_trace`, `rulebook`, `gear_engine`, `fault_sweep_strict` | 1,543 lines | NO |
| `.../bottle_machine_64/app/` | The screens: `server.py` (port 8792), `static/index.html` (6-step flow), `static/flow.html` (Formula Flow dashboard) | 597 lines | NO |
| `.../bottle_machine_64/testdata/` | 10-part Mini Sorter test machine (STEP + BOM + test answers) and the script that generated it | small | NO |
| `.../bottle_machine_64/projects/mini_sorter/` | A finished build: one folder per part, `signatures.json`, `rulebook.json` | small | NO |
| `.../bottle_machine_64/validation/` | Physics check against the gear prototype's real readings (`REPORT.md`) | | NO |
| `.../bottle_machine_64/reference/gear_prototype/` | Read-only copy of the gear-motor prototype code | 42 Python files | copy |
| `.../bottle_machine_64/docs/mindmap/` | The three Excalidraw boards and the scripts that draw them | | NO |
| `.../bottle_machine_64/docs/sensor/` | Clamp placement diagram | | NO |
| `.../bottle_machine_64/dev_checks/` | Zero-guess checks and the mini trial runner (internal) | | NO |
| `.../bottle_machine_64/spike/` | STEP viewer experiments and the 179 MB Voron test file | large | NO |
| `/Users/mac/Desktop/excelis/formula_candidates/` | The 100 cited formulas staged outside the engine | 6 files | NO |
| `/Users/mac/Desktop/excelis/BOTTLE_MACHINE_BOM.md` | Notes on the machine's parts list | | NO |
| `/Users/mac/Desktop/excelis/bottlemachine64-images/` | 84 photos of the machine | | NO |

## 2. The core formula engine (333 formulas) - two copies

| Path | Notes |
|---|---|
| `/Users/mac/Desktop/faulter-formula-brain/` | The working copy: `brain.py`, `formulas.py`, `brain_graph.json`, `esp32_specs.json`, `export_warehouse.py`, and a `warehouse/` folder of 33 empty domain folders. 3 Python files, 2,195 lines. No git. |
| `/Users/mac/Desktop/YANTHROS CORE/` | A second copy from Sep 18. `brain.py` and `formulas.py` are the same size as the working copy, but its `brain_graph.json` is a different, larger (older) file. No git. |
| `/Users/mac/Desktop/excelis/PROTOTYPE_BACKUP_2026-10-03/` | Frozen copy of the engine and the demo prototype taken on 2026-10-03 (see its `README.txt`). Same disk, so it protects against mistakes, not against losing the Mac. |

## 3. The earlier prototype (software packet builder and dashboard)

| Path | What it is |
|---|---|
| `/Users/mac/Desktop/excelis/license_prototype/` | `packet_builder_app.py`, `step_parser.py`, `formula_selector.py`, `fault_sweep_generator.py`, `crypto_core.py`, `issue_key.py`, `unlock.py`, `demo.py`, the signed-license keys, `subsets/`, `twin_viewer_build/`, and `dist/` with the packaged Mac app. 20 Python/HTML files, 13,811 lines, 107 MB. |
| `/Users/mac/Desktop/excelis/license_prototype/dashboard/` | The local admin dashboard (port 5090): `app.py`, `templates/index.html`, `releases/` |
| `/Users/mac/Desktop/excelis/twin/` and `bottle_twin/` | Earlier 3D twin pages (`build_twin.py`, `twin_data.json`, `index.html`) |
| `/Users/mac/Desktop/excelis/Bottle Machine_64.exe`, `20260911041840.exe/.zip`, `_backups/Bottle-Machine-Software/`, `_testing/` | Packaged Windows demo builds from September (71.6 MB each) and test copies |
| `/Users/mac/Desktop/twin-forge/` | The first twin builder from Aug 2: `engine/`, `pipeline-ui/`, `research/`, `brain_launch.py` (27 code files) |

## 4. The 150 RPM gear-motor prototype (the one that worked live)

| Path | What it is |
|---|---|
| `/Users/mac/Desktop/150rpm gear motor prototype/Vansh/150rpm gear system/` | Python app (port 5053), the 150 RPM fault detection, formulas database, ESP32 firmware (`esp32_gearbox_sender`, `esp32_ina228_reader`) |
| `.../Vansh/GearTwinLive-iPad/` | iPad live app (Swift). Paused. Git remote: `vanshxai/faulter-ipad-app` |
| `.../Vansh/GearTwinDashboard-iPad/` | iPad dashboard app (Swift). Paused |
| Whole folder | 84 code files, 65,846 lines, 91 MB. Newest file Aug 12 |

## 5. Zinaata (phone diagnosis, same method) and Dorus

| Path | What it is |
|---|---|
| `/Users/mac/Desktop/ZinaataAndroid/` | Android app (Kotlin), backend with `dorus_engine.py`, `rl_diagnosis/` (DORUSSS report), web app, component database. 1,126 files. Git remote: `vanshxai/zinaata-android` (private) |
| `/Users/mac/Desktop/Zinaata/` | macOS app (Swift, 39 files) |
| `/Users/mac/Desktop/ZAdmin/` | Empty skeleton (two empty folders: `static`, `templates`) |

## 6. Older versions (not opened in this scan)

All inside `/Users/mac/Desktop/Archive - older projects/`:
`YANTHROS/`, `YANTHROS v2/` (includes "Faulter DC 12v motor demo"), `FAULTER-EI/`, `faulter/`, `DIVINE INDUSTRIES/` (faulter, faulter-software, faulter-wireless ESP32 sketch), `dumpyard/` (faulter, faulter-software; 3,152 files, 405 MB), `untitled folder/150rpm motor prototype/` (Yanthros folder and `Yanthros.zip`).

## 7. Copies and data in Downloads

| Path | Notes |
|---|---|
| `/Users/mac/Downloads/Yanthros_fresh/` and `Yanthros.zip` | A July 31 copy of Yanthros (21 Python files, about 22,000 lines) |
| `/Users/mac/Downloads/faulter-software data/` | 304 MB of images and documents, incl. `Faulter_Project_Circuit_Design_Report.pdf` |
| `/Users/mac/Downloads/excelis-images-bottle-machine64/`, `Bottle Machine_64.exe` | Machine photos (317 MB) and another copy of the demo build |
| `/Users/mac/Documents/BMS-faulter/` | Business-management site for Faulter (JS), Apr 30. GitHub: `BMS-faulter` (private) |

## 8. GitHub (account `vanshxai`)

`faulter_core_new`, `faulter_front_new`, `fauter_core` (private), `FAULTER-EI`, `faulter-ipad-app`, `faulter-nassenger8`, `yanthros`, `yanthros-zinaata` (core + Zinaata, last push Sep 18), `zinaata-android` (private), `zinaata-windows`, `BMS-faulter` (private).

**Nothing from after Sep 18 is on GitHub.** That includes everything in section 1 (the whole Bottle Machine 64 build) and the formula candidates.

## 9. Claude's memory and chat history for this work

- Memory notes: `/Users/mac/.claude/projects/-Users-mac-Desktop-excelis/memory/`
- Full chat transcripts: `/Users/mac/.claude/projects/-Users-mac-Desktop-excelis/*.jsonl` (also `-Users-mac-Desktop-YANTHROS`, `-Users-mac-Desktop-FAULTER-EI`, `-Users-mac-Desktop-150rpm-gear-motor-prototype`)

## 10. Tools that are on this Mac but are not Faulter code

- `/Users/mac/Desktop/excalidraw-local/` - a local Excalidraw copy (probably what `~/Applications/Excalidraw.app` opens; not checked)
- `/Users/mac/Desktop/esp32-ap/` - a PlatformIO ESP32 test from Oct 8 (19-line `main.cpp`); not read for relevance
- `/Users/mac/Documents/esp32-control/` - a 12-line LED blink sketch
