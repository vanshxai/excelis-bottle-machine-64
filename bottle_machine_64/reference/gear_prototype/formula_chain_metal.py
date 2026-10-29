"""Backward-compatible shim -- the real implementation moved to
gearsystem/physics/gear_train.py as part of the Phase-1 architecture
refactor (see gearsystem/__init__.py and
/Users/mac/.claude/plans/snug-cuddling-teacup.md). Kept here, re-exporting
the same names, in case anything outside this app still imports
`formula_chain_metal` directly. Safe to delete once nothing does -- see
the migration plan's "parts that must temporarily stay as wrappers"."""
from gearsystem.physics.gear_train import (
    F_TOUCH_N,
    FORCE_TOUCH_MAX_N,
    FORCE_TOUCH_MIN_N,
    InvalidVariantError,
    MOTOR_RPM_OUTPUT_METAL,
    N_STAGES,
    TOUCH_POINTS,
    run_formula_chain,
    run_formula_chain_capless,
)
