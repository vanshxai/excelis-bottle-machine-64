---
name: project-formula-candidates-staging
description: "Where new cited formulas are staged before the core engine (~/Desktop/excelis/formula_candidates), the sourcing rules the user chose, and the pilot's results"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2b070336-f200-406d-b59b-9fe87feb4d4b
  modified: 2026-09-21T14:23:03.031Z
---

User asked (2026-09-21) to grow the engine toward ~3,000 formulas with sources documented. They chose: **fetch each formula from open sources with a real URL** (not recall from memory), and **pilot 100 first**, then scale in batches, thin disciplines first (Civil 9, Aerospace 5, Control 10 in the engine).

Staging lives in `~/Desktop/excelis/formula_candidates/` (`build_pilot.py` = data + checks, `pilot_100.json/.csv`, `already_in_engine.json`, `rejected.json`, README). Nothing is merged into `faulter-formula-brain`; status stays `candidate`/`needs_review` until the user approves.

Pilot result: 100 formulas (34 civil, 27 electrical, 20 control, 19 aerospace) from OpenStax Univ. Physics Vol. 2 key-equation pages and Wikipedia; 99 candidate + 1 held (plate effective-width formula, printed oddly on Wikipedia); 1 rejected by the dimension check (ring buckling, extractor gave R^2 instead of R^3); 3 already in the engine. Automatic checks: sympy parse, SI dimension check (per-symbol positive Dummy scale so unit-cancellation can't hide errors), engine dedupe by name/shape.

**Why:** WebFetch answers through a small summarising model, so extracted text can be wrong; the dimension check caught a real error. It cannot catch wrong numeric coefficients, so coefficient-heavy formulas need a spot check.

**How to apply:** for the next batches keep the same schema and checks; re-read the source for any formula with fixed coefficients; symbol names in candidates are local and must be reconciled with the engine's canonical names (E_mod, I_area, L_beam...) at merge time, mindful of the shared-symbol trap. NASA's old grc.nasa.gov/www/k-12 pages now redirect to www1.grc.nasa.gov/beginners-guide-to-aeronautics/.

Related: [[project-yanthros-product-architecture]], [[feedback-ceo-brief-and-operator-roles]]
