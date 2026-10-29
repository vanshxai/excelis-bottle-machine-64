"""Backward-compatible shim -- the real implementation moved across
gearsystem/twin, gearsystem/calibration, gearsystem/physics, and
gearsystem/signature as part of the Phase-1 architecture refactor (see
/Users/mac/.claude/plans/snug-cuddling-teacup.md). Kept here, re-exporting
the same names, in case anything outside this app still imports
`gearsystem_roulette_metal` directly. Safe to delete once nothing does --
see the migration plan's "parts that must temporarily stay as wrappers".
"""
from gearsystem.calibration.search import (
    N_CARDS,
    NARROW_FRACTION,
    _build_cards,
    _narrow_directional,
    generate_twin_batch,
    guess_for_card,
    pick_closer,
    start_round,
    verify,
)
from gearsystem.calibration.state import STATE_PATH
from gearsystem.calibration.state import load_state
from gearsystem.calibration.state import save_state as _save_state
from gearsystem.physics.current_model import FORCE_REFERENCE_N
from gearsystem.signature.dynamic import TOUCHABLE_GEARS
from gearsystem.signature.dynamic import generate_signature_library as _compute_dynamic_signatures
from gearsystem.twin.store import REGISTRY_PATH, VERIFIED_PATH
from gearsystem.twin.store import load_registry as _load_registry
from gearsystem.twin.store import load_verified
