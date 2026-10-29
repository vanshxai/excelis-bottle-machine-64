# Bottle Machine (Unscrambler) — Component Reference

**Source:** Transcribed from 68 of 74 phone photos of the eDrawings Components tree (`bottlemachine64-images/`), captured on-site at a college computer running the real `Bottle Machine_64.exe`. Fasteners (hex bolts, lock washers, nylock nuts, socket-head screws, etc.) are omitted below except where a specific one is functionally notable — there are hundreds of generic fastener line items in the raw tree, all confirmed to be standard hardware (McMaster-Carr part numbers throughout), not engineering-relevant.

**Machine identity:** a rotary-disk **bottle unscrambler** — root assembly is literally named `"Frame; Unscrambler"` / `"Unscrambler, 36" Disk"` throughout the tree, confirming the earlier functional read.

---

## 1. Major assemblies (top-level, under the root)

| ID | Name | Role |
|---|---|---|
| `UF00601` | Frame Assembly, Unscrambler | Structural aluminum-extrusion frame (1-1/2" sq tube, leveling feet) — pure structure, no actuators |
| `UD03601` | Unscrambler Disk Assembly, 36" | The rotary disk itself — motor, slew-ring bearing, disk plates, guides |
| `UY00101` | Bottle Orientor Assembly | Spring-loaded mechanical orienting mechanism (plunger + arm + hook) — **passive, not motor-driven** |
| `UY02201` | Knock Down Wheel Asm | **Passive, no motor** (IMG_4086): slotted bracket `UB01701`, wheel `UT00501`, 1/2" shoulder bolt `90298A720` (the wheel's pivot), L bracket `UB01601`. This is the second "flapper" that hangs in the air in the renders |
| `UX00101` | Paddle Wheel Assembly | Not expanded in captured photos — worth a follow-up look |
| `US00101` | Unscrambler Gripper Belt Sub Frame ASM | A large, separate belt-driven subsystem (see §4) |
| `UE00201` | Electrical Panel Assembly | Motor drivers, controls, enclosure (see §3) |

---

## 2. Unscrambler Disk Assembly (`UD03601`) — the 36" rotary disk

| Part | Name | Notes |
|---|---|---|
| `UD00101` | Disk Base Plate, 36" | |
| `UD00201` | Outer Ring, 36" SM | |
| `UD00301` (×2) | Disk, 36" Lower Main | contains `UD00501` "Rotary Disk, 36"", `UD00601` "Disk Bottom", `UD00701` "Disk Hold-Down Spacer" ×N |
| `UD00401` | Disk Assembly, Large Bottle | contains `UD01001` "Center Disk Upper Plate", `UD01101` "Spacer, 1/4"-20" ×many |
| `UD00801` | Plastic Guide, 36" Ring | |
| `PRT_02_50_AL_1` | **Slew Ring; IGUS** | The large-diameter rotary bearing the whole disk rides on |
| **`INFM0162.B`** | **"33A-GB/H; 90DC; 1/8HP; 120:1; 14RPM"** | **⭐ The disk drive motor.** 90V DC gearmotor, 1/8 HP, 120:1 reduction, 14 RPM output shaft speed |
| `INFM0385.A` | (unlabeled, motor-adjacent part) | Likely a companion component to the drive motor — not yet identified precisely |
| `UB01001` | Motor Mnt Brkt | Mounting bracket for the above motor |
| `UD01301` | Aluminum Plate Adapter, 36" | |
| `UD01401` | Disk to Gripper Transfer Plate | **Confirms a mechanical link** between the disk and the Gripper Belt subsystem |
| **`UB01101`** | **Photoeye Mounting Bracket, Fiber Optic** | **⭐ The one confirmed sensor** — a fiber-optic photoeye, presumably for bottle presence/count |
| `UT00401` | Transition Plow/Side Guide | With hinged leaf mechanism (`1604A51` hinges) — an openable guide/gate |
| `UD03701` | Disk Cover Asm | Cover with hinges, Lexan guard, bumpers |
| `UG01701` | Cover, 2.5" Hole, 4 Bolt | |

## 3. Electrical Panel Assembly (`UE00201`)

| Part | Name | Qty seen | Notes |
|---|---|---|---|
| `BLE2D200-A` | DC Motor Driver | **4** instances (`<1>`–`<4>`) | The speed-control drivers — one per motor, likely including the disk motor above plus 2-3 more not yet spec'd |
| `ble2d60-a` | DC Motor Driver | 1 instance seen (possibly a misread of the above — needs re-confirmation) | |
| `7436K374` | Potentiometer | **4** instances | Manual speed-adjustment dials, one per motor driver |
| `CTT-AN-D24` | Digital Counter/Timer | 1 | Likely bottle/cycle counting |
| `HT8AAX` | Push Button | 2 | Operator controls |
| `SCE-8C12ELJ` | 12×8 Enclosure (Saginaw) | 1 | |
| `SCE-16148ELJSS` | Enclosure (Saginaw) | 2 | A second, larger enclosure type |
| `6094K24` | Plastic Indicating Knob | 4 | |
| `9106K432` | 3/4-NPT Twist-in Male fitting | 2 | Conduit fittings |
| `69915K55` | Plastic Submersible Cord Grip | 1 | |
| `UE00401` | Conduit, Flex 3/4" | 1 | |

**Implication (updated — confirmed via the tree's "motor" text filter):** the machine has **at least 5 driver boards** (4× `BLE2D200-A` + 1× `ble2d60-a`) and **3 confirmed distinct motors so far, all different specs**:

| Motor | Location in tree | Spec | Likely driver |
|---|---|---|---|
| Disk drive | `INFM0162.B`, inside `UD03601` | 90V DC, **1/8 HP**, 120:1 ratio, 14 RPM out | `BLE2D200-A` |
| Gripper Belt drive | `UP00501` "GearMotor, Parallel Shaft", inside `US00101` → `US05601` "Motor Mount" | **1/4 HP**, 10:1 ratio, `BLM6200SHP-GFV` / `GFV6G10AS` | `BLE2D200-A` |
| Paddle Wheel drive | `UP00601` "GearMotor", inside `UD03601` → `UX00101` → `UX01001` "Motor Mounting Bracket" | **1/12 HP** (smallest), 15:1 ratio, `BLM460SHP-GFV` / `GFV4G15AS` | likely `ble2d60-a` (smallest driver ↔ smallest motor) |

**Not all motors are the same** — confirmed, not assumed. `BLM___SHP-GFV` reads as a real Bison Gear & Engineering gearmotor part-numbering pattern; worth a real datasheet pull if exact current draw is needed.

**Still unaccounted for:** 2 of the 4 `BLE2D200-A` drivers don't yet have a confirmed motor — only the disk and gripper-belt motors are matched to `BLE2D200-A` so far. Most likely candidates: another stage within the Gripper Belt system (it's the most complex subsystem, plausibly has more than one drive point) or the Knocker Roller. Use the same "motor" text-filter trick in the Components tree (bottom-left filter box) to check — it surfaces every motor-related part across the whole tree at once, exactly like it just did here.

### Visual cross-check (IMG_4127 exploded view + IMG_4129 thumbnail) — confirms 3, finds no 4th

> **CORRECTION (2026-10-28):** the two "red cylinder + grey gearbox" bodies described below are **not motors**. The component list (IMG_4053) names them `Red SPRAY BOTTLE<1>` and `<2>`: red test bottles drawn on the belts. The table that follows is therefore wrong for Motor #1 and Motor #2. The "3 motors" count still comes from the component tree (disk motor `INFM0162.B`, gripper-belt motor `UP00501`, paddle-wheel motor `UP00601`). Where each of those sits in the render is marked in `motor_location/MOTORS_*.jpg`.

Zoomed into the full exploded-assembly render (`IMG_4127`) at the pixel level, region by region:

| Body seen | Color/shape signature | Location in render | Read as |
|---|---|---|---|
| Motor #1 | Red cylinder + grey rectangular gearbox, on a tall bracket | Main sub-frame cluster, left side | Disk drive motor `INFM0162.B` |
| Motor #2 | Red cylinder + grey rectangular gearbox, smaller, next to the gripper-belt cage frame | Same cluster, right side, beside the vertical-bar conveyor frame | Gripper Belt motor `UP00501` |
| Motor #3 | **Black** cylinder with a shiny end cap — visually distinct color from #1/#2 | Confirmed separately in `IMG_4129`'s 3D thumbnail, mounted on `UX01300` Paddle Wheel Asm | Paddle Wheel motor `UP00601`, "1/12 HP; 15:1; BLM460SHP-GFV" |

No 4th motor-shaped body (cylindrical housing + mounting flange) is visible anywhere else in the render — checked the disk-ring stack, the gripper conveyor frame, the frame/legs, and a small isolated sub-cluster separately. That last one looked promising (shaft + disc + blocks) but resolved to the **manual Gripper Width Adjustment hand-crank** — its handwheel disc matches `UM00201 "Handwheel; 6243K49"`, seen sitting right next to `UX01300 Paddle Wheel Asm` in `IMG_4129`'s list. Not a motor.

> **NOTE (2026-10-28):** the "brake/encoder bolted to the disk motor" read below leaned on the red body, which is a spray bottle. It no longer has any support: `INFM0385.A` is back to **unidentified**, and it could still be a motor with an empty description.

**Read on `INFM0385.A`:** in the exploded view, motor #1 (red) has a grey rectangular block riding directly behind/in-line with it — most likely this *is* `INFM0385.A`: a brake, encoder, or gearbox-adapter bolted to the disk motor, not an independent 4th motor. That would explain why it has no legible name/description (accessory parts often inherit no BOM text) while still being physically attached to a confirmed motor. Lower-confidence than the 3-motor count above — worth a quick Configuration-Properties check if convenient, but no longer the most urgent gap.

**Net read:** 3 distinct motors is the honest ceiling from everything captured so far — text tree, part specs, and now pixel-level visual inspection of the exploded render all converge on the same 3, with 3 different physical appearances (2 red, 1 black) matching 3 different specs. The 2 unmatched `BLE2D200-A` drivers most likely aren't hiding an unseen 4th motor (nothing motor-shaped turned up anywhere in the render) — more likely explanations: a spare/redundant channel, or a driver wired to something other than a rotating gearmotor (e.g. a solenoid/actuator on the Bottle Orientor or Knock Down Wheel that wouldn't show up under a "motor" keyword search). Confirming that needs either the machine running (video) or the vendor's wiring/quotation paperwork — not resolvable from CAD alone.

## 4. Unscrambler Gripper Belt Sub Frame ASM (`US00101`)

A large, separate belt/chain-driven mechanical subsystem — bottle gripping and conveying, running alongside the disk:

- `US00201` Gripper Belt Core Assembly — main plate, drive shafts, retaining rings
- `US00501` Gripper Width Adj. Assembly — sliding blocks, sprockets (`6280K361`), threaded adjustment rods + handwheel (manual width changeover for different bottle sizes)
- `US00701`/`US01701`/`US01901` — fixed & sliding drive shafts for the gripper belts
- `US02901` (×2) Gripper Belt Conv. Asm — includes timing pulleys (`US04301`, 20-tooth) and a **Gates 540H100 timing belt** (`UP00701`)
- `US04601` (×2) Idler Pulley Assembly
- `US05701` (×4) Bearing Housing Asm, Gripper Belt
- `US05901` Knocker Roller Asm Mounted — roller/knocker mechanism with its own weldment, roller wheel, plastic roller housing
- Roller chain (3/8" pitch) + Gates belt (660L050) also present — **mixed chain-and-timing-belt drivetrain**

No motor found directly inside this sub-assembly's captured photos — it's most likely driven from one of the 4 electrical-panel driver boards via a shaft/chain link back to the main drivetrain (needs confirmation).

## 5. Bottle Orientor Assembly (`UY00101`) — passive/spring-driven

- `UY02001` Plunger Asm, Orientor — plunger + housing + compression spring (16lb max) — spring-loaded, not motor-driven
- `UY02101` Orientor Arm Asm — pivot plate, "Scale Key," "Stop," plastic ball bearings
- `UY00301` Pivot Pin, Orientor + `9287K186` Torsion Spring (302 SS)

This confirms the orienting mechanism is **purely mechanical/spring-actuated**, triggered by bottle motion through the machine — not an active fault point in the same way a motor is, but spring fatigue/breakage is a real long-term failure mode.

---

## Open items / not yet confirmed
1. Exact identity of the other 3 DC motors (which physical subsystem each one drives) — the disk motor is the only one with a confirmed nameplate spec so far.
2. `INFM0385.A` and `DFP-AP-1F` — appear in the tree but their exact function wasn't legible/confirmed from photos.
3. Whether more than one photoeye exists (only one `UB01101` bracket confirmed so far).
4. ~~`Paddle Wheel Assembly` (`UX00101`) internals — not expanded~~ — **resolved**, `IMG_4128`–`4133` fully expanded it: contains `UP00601` GearMotor (1/12 HP, 15:1, `BLM460SHP-GFV`) + `UM00201` Handwheel (manual adjustment, not motor-driven).
5. Images 4105–4112 and a few others weren't individually transcribed — pattern strongly suggests more frame/structural tubing, but worth a final pass if a gap shows up later.
