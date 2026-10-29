"""Signal Processing -- turns raw current blocks into a smoothed,
classified live state, and owns the runtime zero-reference calibration.
Relocated from gearsystem150_app.py (_ina228_process_block,
_run_zero_calibrate, _ina228_auto_calibrate_after_connect).

NOTE on naming: this runtime "zero calibration" (a live sensor
zero-reference capture) is UNRELATED to the Calibration Layer
(calibration/, the offline twin-parameter search). They share the word
"calibrate" by coincidence -- see the migration plan's "key interpretive
decisions" for this exact callout. This module lives in detection/ (live
signal conditioning), not calibration/.
"""
import statistics
import time

from . import live_state, matching

_MEAN_SHIFT_FLOOR_MA = 5.0  # see run_zero_calibrate -- overridden per-session by real measured noise once calibrated


def process_block(samples, rate_hz):
    """One validated 256-sample current block (mA, signed) -> updated
    published state. Classification is still stateless in the sense that
    matters (no baseline tracking, no freeze-while-touched, can't get
    stuck) -- but the raw per-block mean is noisy enough that a touch
    hovering near the boundary between the Yellow zone and the
    Blue/Green/Red zone made the displayed gear flicker between totally
    different answers mid-touch. Fixed with smoothing over the last few
    RAW readings before classifying -- always updates, every block,
    unconditionally, so it carries none of the old EMA baseline's
    "freeze while touched" behavior that caused the stuck-state bug.

    That smoothing then caused a second, real bug found live: releasing
    a touch lingered as "still touched" for several seconds, because the
    old elevated readings took a few blocks to age out of the average --
    and blocks can arrive seconds apart when the connection is unstable,
    so "a few blocks" became "several real seconds" of a stale-looking
    touch. Fixed with an asymmetric response: a single fresh reading back
    at baseline clears "touched" immediately (no lag on release), but
    climbing into / staying in a touch still uses the smoothed value to
    decide WHICH gear (so mid-touch flicker stays fixed). Release fast,
    decide slow -- not lag in both directions.

    When live_state.CLASSIFY_ENABLED is False (temporarily, for raw-
    waveform inspection -- see live_state.py), this still publishes
    current_A/rate_hz/last_update (basic "what does the sensor read right
    now" telemetry, unrelated to detection) but skips the smoothing and
    matching.gear_matches() call entirely -- touched/delta_mA/
    detected_gears are reported as untouched/None/empty. Flipping
    CLASSIFY_ENABLED back to True restores the block below exactly as it
    was, unchanged.

    Also drives update_part_interruption() with this exact same
    current_A -- the identical number the Current Feed card displays, not
    a separately-sampled or separately-smoothed value -- once per block,
    independent of CLASSIFY_ENABLED. Called AFTER live_state.lock is
    released below: live_state.lock is a plain (non-reentrant) Lock, and
    update_part_interruption() takes it too for its own tiny write, so
    calling it from inside this function's own `with` block would
    deadlock."""
    mean_mA = sum(samples) / len(samples)
    now = time.time()
    current_A = mean_mA / 1000.0

    with live_state.lock:
        gs = live_state.state
        gs["current_A"] = current_A
        gs["rate_hz"] = rate_hz
        gs["last_update"] = now

        if not live_state.CLASSIFY_ENABLED:
            gs["touched"] = False
            gs["delta_mA"] = None
            gs["detected_gears"] = []
            gs["detected_gear"] = None
            hist = gs["history"]
            hist.append({"t": now, "current_A": gs["current_A"], "touched": False, "detected_gears": []})
            if len(hist) > live_state.HISTORY_MAX:
                del hist[: len(hist) - live_state.HISTORY_MAX]
        else:
            zero_A = live_state.real_zero_A
            floor_mA = (live_state.noise_floor_at_cal * 1000.0) if live_state.noise_floor_at_cal else _MEAN_SHIFT_FLOOR_MA

            recent = live_state.recent_means
            recent.append(mean_mA)
            smoothed_mA = sum(recent) / len(recent)

            if zero_A is None:
                delta_mA, touched_now, matches = None, False, []
            else:
                raw_delta_mA = mean_mA - zero_A * 1000.0
                if abs(raw_delta_mA) <= floor_mA:
                    delta_mA, touched_now, matches = raw_delta_mA, False, []
                else:
                    delta_mA = smoothed_mA - zero_A * 1000.0
                    touched_now = abs(delta_mA) > floor_mA
                    matches = matching.gear_matches(delta_mA / 1000.0) if touched_now else []

            gs["touched"] = touched_now
            gs["delta_mA"] = round(delta_mA, 3) if delta_mA is not None else None
            gs["detected_gears"] = matches
            gs["detected_gear"] = matches[0] if matches else None  # back-compat, first/strongest match
            hist = gs["history"]
            hist.append({
                "t": now, "current_A": gs["current_A"], "touched": touched_now,
                "detected_gears": [m["component"] for m in matches],
            })
            if len(hist) > live_state.HISTORY_MAX:
                del hist[: len(hist) - live_state.HISTORY_MAX]

    update_part_interruption(current_A, now)


def update_part_interruption(current_a, now=None):
    """Proof-of-concept "Part Interruption" detector -- see live_state.py's
    PART_INTERRUPTION_* config block for the actual numbers. Deliberately
    separate from process_block()'s baseline-delta pipeline above: no
    zero-reference, no smoothing beyond the block-mean current_A it's
    handed, no history -- just "is the live reading inside one gear's
    fixed experimental range, continuously, for PART_INTERRUPTION_HOLD_S."
    Called once per processed block (see process_block() above), against
    the exact same current_A value the Current Feed card displays.

    Below PART_INTERRUPTION_IDLE_MAX_A: idle, clears any pending/declared
    gear immediately (no lag on release).

    STICKY once declared: once a gear is published as interrupted, it
    stays published -- even if the current later climbs high enough to
    fall inside a DIFFERENT gear's range -- until the reading drops back
    to idle. A harder push against an already-touched gear reads as a
    bigger current on the SAME gear, not as switching to whichever gear
    that bigger number happens to fall in; only a genuine release back to
    idle clears the lock so the next touch gets classified fresh.

    Before anything is locked: tracks which range (if any) the reading
    falls in, resets the hold timer the moment the matched range changes,
    and only publishes a declaration once the same range has held
    continuously for PART_INTERRUPTION_HOLD_S."""
    now = now if now is not None else time.time()
    currently_locked = live_state.state["part_interruption_gear"]

    if current_a < live_state.PART_INTERRUPTION_IDLE_MAX_A:
        live_state.part_interruption_candidate_gear = None
        live_state.part_interruption_candidate_since = None
        declared = None
    elif currently_locked is not None:
        declared = currently_locked
    else:
        gear = None
        for name, (lo, hi) in live_state.PART_INTERRUPTION_RANGES_A.items():
            if lo <= current_a <= hi:
                gear = name
                break
        if gear != live_state.part_interruption_candidate_gear:
            live_state.part_interruption_candidate_gear = gear
            live_state.part_interruption_candidate_since = now
        declared = None
        since = live_state.part_interruption_candidate_since
        if gear is not None and since is not None and (now - since) >= live_state.PART_INTERRUPTION_HOLD_S:
            declared = gear

    with live_state.lock:
        live_state.state["part_interruption_gear"] = declared


def run_zero_calibrate(window_s=10.0, min_samples=5, generation=None):
    """Captures the CURRENT live baseline (motor running or not, whatever
    state it's actually in right now -- untouched) as the fixed zero-
    reference the fault-o-meter reads every block against. This is the
    "pre-built calibration" step -- deliberately a one-time act, not a
    continuously-adapting background process, matching the speedometer
    design: calibrate once, then every reading is just compared against
    that fixed scale. Returns (ok: bool, info: dict).

    generation, when passed (only the auto-calibrate-after-connect caller
    does), is checked against the live live_state.connect_generation right
    before committing results -- sampling takes up to window_s seconds, and
    if a newer reconnect happened during that window the result reflects a
    session that may no longer be physically valid, so it's discarded
    instead of silently becoming the new zero point."""
    with live_state.lock:
        if not live_state.state["connected"]:
            return False, {"error": "sensor not connected"}
        start_mean = live_state.state["current_A"]
    if start_mean is None:
        return False, {"error": "no live reading yet"}

    # Window is long and the freshness check is "did a genuinely new block
    # arrive" rather than "arrived within the last second" -- blocks are
    # currently landing anywhere from ~0.1s to ~3s apart (motor-noise-related
    # I2C stalling, see conversation), so a tight per-poll freshness cutoff
    # was discarding real data and starving this of samples.
    samples = []
    seen_updates = set()
    t0 = time.time()
    while time.time() - t0 < window_s and len(samples) < 20:
        with live_state.lock:
            v = live_state.state["current_A"]
            last_update = live_state.state["last_update"]
        if v is not None and last_update and last_update not in seen_updates:
            seen_updates.add(last_update)
            samples.append(v)
        time.sleep(0.05)

    if len(samples) < min_samples:
        return False, {"error": "not enough fresh samples arrived during calibration window"}

    if generation is not None and generation != live_state.connect_generation:
        return False, {"error": "stale calibration -- sensor reconnected during sampling, discarded"}

    mean_A = statistics.mean(samples)
    stdev_A = statistics.stdev(samples) if len(samples) > 1 else 0.0
    live_state.real_zero_A = mean_A
    # 4 sigma, floored at _MEAN_SHIFT_FLOOR_MA -- the idle mean held within
    # about +-2mA across every untouched test run, so 4 sigma over real measured noise
    # should sit safely below the smallest real touch delta observed (+7mA on Red).
    live_state.noise_floor_at_cal = max(4 * stdev_A, _MEAN_SHIFT_FLOOR_MA / 1000.0)

    return True, {
        "zero_A": round(mean_A, 6), "noise_floor_A": round(live_state.noise_floor_at_cal, 6),
        "stdev_A": round(stdev_A, 6), "n_samples": len(samples),
    }


def auto_calibrate_after_connect(generation, delay_s=8.0):
    """Fires once, shortly after the gateway connects, so the fault-o-meter
    has a real calibrated zero without anyone having to press a button --
    matches "just start detecting" rather than requiring a manual step
    first. Runs in its own thread so it doesn't block the read loop.
    Carries the connect generation it was spawned for -- if a newer
    reconnect happens while this is sleeping/sampling, run_zero_calibrate's
    generation check discards the result instead of applying a stale zero."""
    time.sleep(delay_s)
    ok, info = run_zero_calibrate(generation=generation)
    if ok:
        print(f"[gearsystem] auto-calibrated: zero={info['zero_A']*1000:.2f}mA "
              f"noise_floor={info['noise_floor_A']*1000:.2f}mA n={info['n_samples']}")
    else:
        print(f"[gearsystem] auto-calibrate failed: {info.get('error')} -- use the calibrate button manually")
