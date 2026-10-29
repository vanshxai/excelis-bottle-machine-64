---
name: project-part-archetype-architecture
description: "User's chosen backend design (Oct 2026): library of part archetypes, each = plain-language UI questions + pre-written parametrized code module; instantiated per machine from BOM/STEP; generated program is proprietary"
metadata:
  node_type: memory
  type: project
  originSessionId: 2b070336-f200-406d-b59b-9fe87feb4d4b
  modified: 2026-10-03T13:17:59.321Z
---

Design direction stated by the user (2026-10-03), replacing the earlier "tabular ranges + fault labels" backend idea:

- Scan BOM + assembly (STEP) files, detect recurring part patterns (conveyor belt, flipper/paddle, gear train, disk + slew bearing, elevator, chain/sprocket, idler, spring orientor...). A few parts per machine are unique.
- Each pattern ("archetype") bundles: (1) a custom plain-language input form for non-technical users (e.g. "what is the max/min range you expect from the flipper; alert critical beyond X, moderate below Y"), (2) a pre-written, parametrized code module (physics formulas + current-signature simulation + alert logic). Modules are linked/called per the formula chain, not rewritten per machine.
- The linked modules form a per-machine program that runs in real time against the live current signatures of all motors in parallel, including cross-sensor fallback rules (e.g. if 2 sensors malfunction).
- The generated per-machine program is proprietary ("secret sauce"); the client only sees the 3D wireframe and visuals. The user does NOT want auto-tests shipped with it.

**Why:** a raw database has no logic; archetype modules give reuse (write each pattern once), versatility, and avoid writing ~50,000 lines per machine.

**How to apply:** keep any validation of archetypes on our side, internal only. User answers in physical units must be translated by the module into thresholds on what the sensors actually measure (current bands per motor branch). Unknown/unique parts need a generic fallback archetype so nothing crashes, and each new machine can add archetypes to the library. This design needs the still-unbuilt per-instance active->passive mapping.

**Later decisions, same day:**
- Uploads are strictly a STEP file (exported from the client's SolidWorks SLDASM, which we cannot read) plus the BOM; on any error the app pops up a notice and asks for re-upload.
- Structure: machine > sections > sub-sections > parts. One folder per part holding its own formulas/code (user accepts a code copy per part, generated from the type templates at setup) with that part's stored simulated results beside it. Series/parallel groups are simulated across CPU cores; outermost part variables take user-entered ranges.
- Live matching: current signatures from the sensors are matched against all stored scenarios; when ambiguous, highlight the smallest enclosing area/section instead of saying "not sure".
- Ideal-operation baseline comes from user-entered values, not a required healthy-run recording (an optional extra only). The BLE2 driver front panel shows "load factor %" (torque as % of rated; verified in manual HM-5189), so the client can read a normal running value per Oriental motor in seconds. Nameplate rating is a ceiling, not the normal value.
- The app needs a sensor section: detect USB/WiFi ports, then click-link each sensor channel to a motor in the 3D wireframe.

Related: [[project-yanthros-product-architecture]], [[feedback-ceo-brief-and-operator-roles]]
