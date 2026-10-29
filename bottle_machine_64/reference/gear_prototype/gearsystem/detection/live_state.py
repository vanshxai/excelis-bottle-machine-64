"""Single owning module for all live (INA228 gateway) mutable state.

acquisition.py and signal_processing.py both REBIND some of these values
(not just mutate in place -- e.g. resetting real_zero_A to None on
reconnect, or setting it to a freshly-computed mean after calibration).
They must share one physical module for that to work correctly: Python's
`global X` binds to the enclosing module's OWN namespace, so if these
values lived as independent module-level globals split across two
different files, each file's rebind would silently create a disconnected
copy instead of updating a shared value -- calibration would appear to
succeed while live detection kept reading a stale (or never-set) zero.
Every other file imports this module and uses qualified attribute access
(`live_state.real_zero_A = ...`) instead of `global` -- the one place in
this refactor where code is not simply relocated verbatim, but adapted to
stay correct across the module split. See the migration plan's
"non-pure-move exception" for the full reasoning.

Relocated from gearsystem150_app.py's module-level globals, unchanged in
value/meaning."""
import collections
import threading

lock = threading.Lock()

state = {
    "current_A": None, "history": [], "last_update": None,
    "connected": False, "port": None, "status": "waiting_for_sensor", "error": None,
    "touched": False, "rate_hz": None,
    "detected_gear": None, "detected_gears": [], "delta_mA": None,
    "part_interruption_gear": None,
}
HISTORY_MAX = 200

# ---------------------------------------------------------------------------
# Proof-of-concept "Part Interruption" detection -- a simple, temporary
# threshold/range classifier against the live INA228 current, deliberately
# independent of the baseline-delta gear-matching pipeline above
# (CLASSIFY_ENABLED / matching.gear_matches()). Experimentally measured
# current ranges for THIS SPECIFIC gearbox -- not adaptive, no automatic
# calibration, no FFT, no ML. Edit the numbers below directly to retune;
# nothing else needs to change. See signal_processing.update_part_interruption()
# for the state machine that applies them.
PART_INTERRUPTION_IDLE_MAX_A = 0.025
# Contiguous, no unassigned dead zones between Red/Green/Blue/Yellow -- each
# range's floor picks up right where the previous one's ceiling ends (at
# this sensor's native 1mA integer resolution -- see esp32_ina228_reader's
# wire protocol -- adjacent thousandths-of-an-amp bounds like .034/.035
# leave no representable reading in between, so they're contiguous, not
# gapped). Yellow's ceiling is intentionally open-ended (no upper bound
# supplied). Below PART_INTERRUPTION_IDLE_MAX_A is idle; between idle and
# Red's floor (0.025-0.030A) is deliberately left unassigned -- readings
# there are simply "no part interrupted," not a fifth zone.
PART_INTERRUPTION_RANGES_A = {
    "Red": (0.031, 0.034),
    "Green": (0.035, 0.042),
    "Blue": (0.043, 0.090),
    "Yellow": (0.091, float("inf")),
}
PART_INTERRUPTION_HOLD_S = 0.25  # ~200-300ms continuous match required before declaring

# The detector's own working memory: which gear's range the current reading
# is presently inside, and since when -- so a declaration only fires once
# it's held continuously for PART_INTERRUPTION_HOLD_S. Reset on reconnect
# (acquisition.py) alongside the other per-session state below.
part_interruption_candidate_gear = None
part_interruption_candidate_since = None

# Calibration state, settable via /api/gearsystem/live/zero_calibrate. None
# until a user runs that step (or the automatic post-connect calibration
# in signal_processing.py completes).
real_zero_A = None
noise_floor_at_cal = None
# Bumped on every reconnect (acquisition.py) so a slow auto-calibration
# started before a reconnect can tell its result is stale and discard
# itself instead of overwriting a newer session's zero point -- see
# signal_processing.run_zero_calibrate's generation check.
connect_generation = 0
# Measured live (motor running, untouched): per-block peak-vs-baseline
# swings from noise alone were 20-40+mA -- far above the 3mA starting
# guess, and above the 1.6-4.5mA the physics model predicts for a light
# reference touch. Raised past the observed noise ceiling so it stops
# permanently false-tripping; this means only touches bigger than a light
# reference press are guaranteed to register right now.
NOISE_FLOOR_MIN = 0.06

SMOOTH_WINDOW = 3  # blocks -- see signal_processing.process_block's note on why this exists
recent_means = collections.deque(maxlen=SMOOTH_WINDOW)

# Raw per-sample ring buffer -- bypasses the block-mean pipeline entirely,
# for direct waveform inspection. Appended to unconditionally, once per
# raw sample, in acquisition.py's read loop (~893Hz idle), regardless of
# CLASSIFY_ENABLED below. maxlen covers ~5s at the fastest observed rate
# (893Hz * 5s ~= 4465); holds (timestamp, raw_mA) tuples.
RAW_BUFFER_MAXLEN = 4500
raw_buffer = collections.deque(maxlen=RAW_BUFFER_MAXLEN)

# Temporarily disabled to inspect raw current waveforms directly, before
# any block-mean smoothing/classification -- see
# signal_processing.py::process_block(). Flip back to True to restore
# gear classification; no other code change is needed to revert.
CLASSIFY_ENABLED = False
