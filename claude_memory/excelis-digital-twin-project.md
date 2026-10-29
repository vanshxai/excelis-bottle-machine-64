---
name: excelis-digital-twin-project
description: "Digital-twin work driving the local Yanthros Formula Brain -- the one-off Excelis piston filler twin, and its generalized successor pipeline \"twin-forge\""
metadata: 
  node_type: memory
  type: project
  originSessionId: b133925d-dc62-443f-960f-388cf8f95b81
  modified: 2026-08-02T08:14:59.943Z
---

Two related things now exist:

1. `~/Desktop/excelis/twin/` -- the **first** digital twin, hand-built for the
   Volumetric Technologies Servo Piston Filler/Depositor (Excelis Packaging
   Automation subsidiary). Proved the method: scrape OEM specs, drive the
   Formula Brain (`~/Desktop/faulter-formula-brain`) instead of
   hand-calculating, derive underdetermined geometry (bore/stroke) by
   inverting a published performance spec (±0.25% accuracy) rather than
   guessing, render as a Three.js wireframe.

2. `~/Desktop/twin-forge/` (built 2026-08-02) -- that method turned into a
   **repeatable pipeline** for any machine: two parallel research Agents
   (spec agent + formula agent, prompts in `twin-forge/README.md`) produce
   cited JSON, a human checkpoint reviews it, a generic `engine/build_twin.py`
   extends+solves through the Brain, a generic Three.js shell
   (`engine/template/`) renders whatever `research/<slug>/scene.js` builds,
   and `engine/verify.py` + `verify_kinematics.js` check the numbers and the
   3D actually agree with the physics. Full design rationale in
   `/Users/mac/.claude/plans/misty-conjuring-flask.md`. Validated end-to-end
   on a second, unrelated machine (a Goulds/Xylem NPE centrifugal pump) --
   the research agents found real citable sources, and cross-checking their
   two outputs against each other caught a genuine symbol-naming bug
   (`h_hyd` vs `H_pump2`) before it reached the Brain.

**Why:** the user's goal was never a one-off model -- it's proving the Brain's
Pathfinder can chain across unfamiliar machine domains, finding where its
formula library is thin, and eventually not needing a human to hand-drive the
whole process every time.

**How to apply:**
- For a NEW machine, use twin-forge's pipeline (README has the exact agent
  prompts and JSON schemas), not a fresh hand-built script like excelis/twin.
- The user's real Brain serves on **port 5051**. Never POST `/brain/extend`
  to it directly -- that persists into `faulter-formula-brain/brain_extensions.json`
  permanently. Always launch an isolated copy on another port first
  (`brain_launch.py`, `TWIN_SCRATCH` env var redirects the extensions file).
- `/brain/extend` now **requires** a `source` citation field (added to
  `faulter-formula-brain/brain.py` 2026-08-02) -- a formula without a
  textbook/standard/paper/datasheet citation is rejected outright, and
  citations now surface in every `/brain/solve` trace step.
- OEMs publish almost no real engineering numbers (no bore, stroke, motor
  rating, impeller width, etc.). Estimate from industry-typical/textbook
  values but tag every input `oem` / `estimated` / `material` so the guesses
  stay visible and swappable -- this convention traces back to a predecessor
  project, `~/Desktop/YANTHROS v2/` (see its RS775 motor twin), which is
  worth checking for prior art before modeling a new machine type.
- Namespace every new formula's symbols with a per-machine suffix (`_pf` for
  the piston filler, `_cp` for the centrifugal pump). The Brain merges graph
  nodes by bare variable name across ALL machines sharing one instance, so an
  un-namespaced `T` or `P` silently fuses unrelated machines' physics
  together. Conversely, DO reuse the Brain's existing bare symbols (e.g.
  `D2_impeller`, `H_pump2`, `N_pump2`) when a new machine genuinely needs the
  same physical quantity an existing formula already models -- that's the
  whole point of one shared Brain instead of per-machine silos.
- When two independent research agents (spec + formula) produce outputs that
  reference the same machine, have them cross-check each other's symbol
  names before the human checkpoint -- this caught a real bug for free in
  the centrifugal pump run.
