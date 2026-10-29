"""Backward-compatible shim -- the real implementation moved to
gearsystem/calibration/sampling.py as part of the Phase-1 architecture
refactor (this logic is Calibration's "generate N candidate twins"
primitive, not Twin Layer's -- see the migration plan's "key
interpretive decisions" #1, at
/Users/mac/.claude/plans/snug-cuddling-teacup.md). Kept here,
re-exporting the same names, in case anything outside this app still
imports `constraint_sampling` directly. Safe to delete once nothing does.
"""
from gearsystem.calibration.sampling import is_int_range as _is_int_range
from gearsystem.calibration.sampling import sample_variant as _sample_variant
from gearsystem.calibration.sampling import soft_ranges as _soft_ranges
