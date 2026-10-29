---
name: feedback-ceo-brief-and-operator-roles
description: "User wants CEO-brief replies (1-3 sentences, no paragraph walls), wants to be the operator of pipelines while Claude builds/publishes tools, and wants a check-in before major steps"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b7d42af2-26d9-4e9f-8fc7-05876685436e
  modified: 2026-09-21T13:24:53.279Z
---

Keep replies to a few statements — the user repeatedly said "I'm the CEO, I don't have time for paragraphs" (Sep 2026). Tables are fine when they asked for one; long explanations are not.

**Why:** they reprimanded multi-paragraph answers several times in a row, even when the content was correct.

**How to apply:** lead with the result in one or two sentences; put detail in files/UI, not chat. Brainstorm requests still get a short recommendation + the main tradeoff, not a survey.

Roles: Claude builds and *publishes* tools (e.g. releases them on the local Yanthros dashboard); the **user runs the pipeline steps themselves** (uploads the CAD file, clicks Build, downloads the exe). Do not run their pipeline for them and report results as if that were the product test.

**Why:** they corrected Claude for running the fault-sweep generator itself instead of building the tool for them to operate.

**How to apply:** "ask before any major step" was an explicit instruction — propose the plan and the one real decision, then build. Never pre-build a deliverable by hand outside the tool that's supposed to generate it (they had a hand-made Adafruit app removed for exactly this).

Related: [[excelis-digital-twin-project]]
