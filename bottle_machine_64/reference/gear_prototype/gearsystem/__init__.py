"""150 RPM Gear System backend, restructured into layers (Phase 1 refactor:
structure only, zero behavior change -- see the migration plan for the
full rationale).

twin/        -- digital twin representation, loading, saving. No simulation.
calibration/ -- the closed-loop search that finds the best-fit twin.
physics/     -- gear-train + current-conversion formulas. Leaf layer.
signature/   -- turns a twin + disturbance into a current signature.
detection/   -- live INA228 acquisition, signal processing, matching.
api/         -- Flask blueprints; the only layer aware of HTTP.
"""
import os

# The project root -- one level above this package -- where every JSON data
# file (constraint_registry_metal.json, gearsystem_metal_verified_twin.json,
# gearsystem_roulette_metal_state.json) lives, unchanged from before this
# refactor. Computed once here rather than independently re-derived via a
# chain of os.path.dirname(__file__) calls in every file that needs it.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
