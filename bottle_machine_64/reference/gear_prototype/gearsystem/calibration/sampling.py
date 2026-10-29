"""Generic constraint-registry sampling helpers -- rig-agnostic, operates
on any {"soft_constraints": {name: {"min":..., "max":...}}} shaped
registry. Originally extracted out of bvs_engine.py (the plastic rig's
calibration engine); relocated here unchanged -- this is Calibration's
"Generate N Candidate Twins" / "Shrink parameter ranges" primitive (see
the migration plan's "key interpretive decisions" #1 for why this lives
in calibration/, not twin/, despite the word "generate" appearing in
both layers' descriptions)."""
import random


def soft_ranges(registry):
    """Only the entries that are genuinely sampleable (have min/max).
    Preserves int vs float typing from the JSON so tooth counts stay
    integers."""
    ranges = {}
    for k, v in registry["soft_constraints"].items():
        if "min" in v and "max" in v:
            ranges[k] = {"min": v["min"], "max": v["max"]}
    return ranges


def is_int_range(lo, hi):
    return isinstance(lo, int) and isinstance(hi, int)


def sample_variant(ranges):
    variant = {}
    for k, r in ranges.items():
        lo, hi = r["min"], r["max"]
        if lo > hi:
            lo, hi = hi, lo
        if is_int_range(lo, hi):
            variant[k] = random.randint(int(round(lo)), int(round(hi))) if hi > lo else lo
        else:
            variant[k] = round(random.uniform(lo, hi), 5)
    return variant
