"""Backward-compatible shim -- the real implementation moved to
gearsystem/physics/gear_train.py (mechanical model) and
gearsystem/signature/dynamic.py (simulate_touch, the touch-scenario
orchestration) as part of the Phase-1 architecture refactor (see
/Users/mac/.claude/plans/snug-cuddling-teacup.md). Kept here, re-exporting
the same names, in case anything outside this app still imports
`dynamic_gear_simulator` directly. Safe to delete once nothing does --
see the migration plan's "parts that must temporarily stay as wrappers".
"""
from gearsystem.physics.gear_train import (
    NODE_TEETH_KEY,
    NODES,
    NODES_CAPLESS,
    STAGE_RATIO_KEYS,
    STAGES_TOPOLOGY,
    STAGES_TOPOLOGY_CAPLESS,
    _derivatives,
    _gear_inertia_kgm2,
    _tooth_linear_stiffness_n_per_m,
    build_gear_train,
)
from gearsystem.physics.gear_train import equilibrium_state as _equilibrium_state
from gearsystem.physics.gear_train import gear_radius_m as _gear_radius_m
from gearsystem.physics.gear_train import mesh_torque as _mesh_torque
from gearsystem.physics.gear_train import rk4_step as _rk4_step
from gearsystem.physics.gear_train import stable_dt as _stable_dt
from gearsystem.physics.motor import motor_rotor_inertia_kgm2 as _motor_rotor_inertia_kgm2
from gearsystem.signature.dynamic import simulate_touch
