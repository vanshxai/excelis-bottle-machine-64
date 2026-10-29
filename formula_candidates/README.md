# Formula candidates (staging)

Not part of the core engine. Nothing here is merged into `faulter-formula-brain` until a person approves it.

- `pilot_100.json` / `pilot_100.csv` - 100 candidate formulas. Each has the equation, symbol units, discipline, source page (title, URL, section, licence, date fetched) and check results.
- `already_in_engine.json` - 3 formulas that matched something already in the 333.
- `rejected.json` - 1 formula that failed the dimension check.
- `build_pilot.py` - the data and the checks; rerun it to regenerate everything.

How they were sourced: pages fetched on 2026-09-21 (OpenStax University Physics Vol. 2, Wikipedia). The page text was read through a summarising tool, so the automatic dimension check plus a human review are the safety net, not the extraction itself.

Checks catch wrong units and wrong powers. They cannot catch a wrong numeric coefficient, so coefficient-heavy formulas (tuning tables, bearing-capacity factors) need a spot check before approval.
