"""Parameter Sensitivity Analysis -- standalone script, not part of the
Flask app and not wired into any route or page. This phase's spec was
explicit: no new UI, no architecture change, no change to the disturbance
simulation. This script only CALLS signature.dynamic.simulate_touch()
with different constant dicts and reads its existing outputs -- it never
modifies physics/disturbance code, never writes the twin, never runs
automatically as part of the app.

For every constant in the current verified twin, holds every OTHER
constant fixed, perturbs that one constant by +pct% and -pct% in turn,
re-runs the same touch simulation, and compares the result against an
unperturbed baseline on four qualitative axes:

  - peak current   -- %change in delta_I_A (the touch-induced deviation
                       from idle current; NOT peak_A, which also moves
                       trivially whenever I_BASELINE_A itself is the
                       parameter being perturbed)
  - peak timing     -- %change in rise_time_s (simulate_touch's own name
                       for time-to-peak-deviation)
  - rise rate       -- %change in |delta_I_A| / rise_time_s (average
                       slope to peak -- a distinct signal from raw
                       timing: two runs can peak at the same time with
                       different swing sizes, or vice versa)
  - amplitude       -- %change in RMS deviation from baseline across the
                       whole reported waveform (distinct from the single
                       peak value -- captures the overall shape/energy of
                       the transient, not just its extreme point)

This is a one-at-a-time (OAT) LOCAL sensitivity analysis around the
current twin's own constants: it measures how much the SIMULATED output
moves when ONE input moves, entirely self-referential to the model. It
is not a fit/error score against real INA228 data, and it never modifies
or saves the twin -- see this phase's explicit "do not calculate an
optimization score / do not attempt automatic tuning" constraint.

Note on default gear: a touch applied directly to Yellow (the motor's own
gear, 0 mesh stages away) shows rise_time_s == 0.0 exactly, for every
twin -- Yellow's current response is set by an algebraic torque balance
evaluated every step, not by anything that propagates/integrates over
time, so its "peak" is always the very first sample. That's a correct,
physical fact about a direct-touch-on-the-motor-shaft scenario, but it
makes peak-timing and rise-rate meaningless to compare (0 -> anything
looks like an "infinite" shift). Default gear is Red (the far end of the
train, confirmed nonzero rise_time_s) so a first run is informative on
all four metrics; --gear Yellow still works, the script just marks
timing/rate as N/A and explains why in the report header. Confirmed via
direct check: Yellow rise_time_s=0.0, Blue=0.00017s, Green=0.0038s,
Red=0.0020s (this twin, impact/0.5N/5Nms).

Usage:
    python3 sensitivity_analysis.py
    python3 sensitivity_analysis.py --gear Green --touch-type impact --pct 15
"""
import argparse
import sys
import time
from datetime import datetime, timezone

from gearsystem.physics import gear_train
from gearsystem.signature import dynamic as sig_dynamic
from gearsystem.twin import store as twin_store

# Documented, inspectable thresholds -- NOT a fitness/optimization score.
# "Overall influence" is the mean |%change| in simulated output per pct%
# step in one input, averaged across the four metrics above and both
# perturbation directions. Bucketed here purely for readability.
INFLUENCE_BUCKETS = [
    (75.0, "Very High Influence"),
    (30.0, "High Influence"),
    (10.0, "Medium Influence"),
    (2.0, "Low Influence"),
    (0.5, "Very Small Influence"),
    (0.0, "No Measurable Influence"),
]

UNCHANGED_THRESHOLD_PCT = 1.0  # below this, describe a metric as "unchanged" rather than picking a direction


def classify(magnitude_pct):
    for threshold, label in INFLUENCE_BUCKETS:
        if magnitude_pct >= threshold:
            return label
    return INFLUENCE_BUCKETS[-1][1]


def waveform_amplitude_a(result):
    """RMS deviation from I_baseline_A across every reported waveform
    point -- a whole-curve measure, distinct from the single peak value."""
    baseline = result["I_baseline_A"]
    pts = result["waveform"]
    if not pts:
        return 0.0
    devs = [p["current_A"] - baseline for p in pts]
    return (sum(d * d for d in devs) / len(devs)) ** 0.5


def rise_rate_a_per_s(result):
    """Average slope from idle to peak -- |delta_I_A| / rise_time_s."""
    rt = result["rise_time_s"]
    if not rt or rt <= 0:
        return 0.0
    return abs(result["delta_I_A"]) / rt


def pct_change(old, new):
    if abs(old) < 1e-12:
        # Baseline metric is ~zero (e.g. I_BASELINE_A perturbations leave
        # delta_I_A mathematically unchanged -- see module docstring) --
        # percent-of-zero is undefined, so report 0% unless the perturbed
        # value actually moved away from zero too.
        return 100.0 if abs(new) > 1e-12 else 0.0
    return (new - old) / abs(old) * 100.0


def describe_direction(pct, verb_pair, unchanged_word="unchanged"):
    if abs(pct) < UNCHANGED_THRESHOLD_PCT:
        return unchanged_word
    return verb_pair[0] if pct > 0 else verb_pair[1]


def run_one(constants, gear, touch_type, force_n, impulse_ns):
    return sig_dynamic.simulate_touch(
        constants, gear, touch_type=touch_type, force_n=force_n, impulse_ns=impulse_ns,
    )


def perturb_value(value, pct):
    factor_up, factor_down = 1 + pct / 100.0, 1 - pct / 100.0
    if isinstance(value, int) and not isinstance(value, bool):
        return round(value * factor_up), round(value * factor_down)
    return value * factor_up, value * factor_down


def analyze_parameter(key, base_constants, baseline_result, gear, touch_type, force_n, impulse_ns, pct, timing_meaningful):
    original = base_constants[key]
    up_value, down_value = perturb_value(original, pct)

    directions = {}
    for label, value in (("+{:.0f}%".format(pct), up_value), ("-{:.0f}%".format(pct), down_value)):
        c = dict(base_constants)
        c[key] = value
        try:
            result = run_one(c, gear, touch_type, force_n, impulse_ns)
        except (ValueError, gear_train.InvalidVariantError) as e:
            directions[label] = {"error": str(e)}
            continue

        d_peak = pct_change(baseline_result["delta_I_A"], result["delta_I_A"])
        d_amp = pct_change(waveform_amplitude_a(baseline_result), waveform_amplitude_a(result))
        if timing_meaningful:
            d_timing = pct_change(baseline_result["rise_time_s"], result["rise_time_s"])
            d_rate = pct_change(rise_rate_a_per_s(baseline_result), rise_rate_a_per_s(result))
            timing_desc = describe_direction(d_timing, ("shifted later", "shifted earlier"))
            rate_desc = describe_direction(d_rate, ("became faster", "became slower"))
        else:
            d_timing = d_rate = None
            timing_desc = rate_desc = "N/A (baseline peaks at t=0 for this touch point)"

        directions[label] = {
            "value": value,
            "peak_pct": d_peak, "timing_pct": d_timing, "rate_pct": d_rate, "amp_pct": d_amp,
            "peak_desc": describe_direction(d_peak, ("increased", "decreased")),
            "timing_desc": timing_desc,
            "rate_desc": rate_desc,
            "amp_desc": describe_direction(d_amp, ("increased", "decreased")),
        }

    magnitudes = []
    for d in directions.values():
        if "error" in d:
            continue
        magnitudes.append(abs(d["peak_pct"]))
        magnitudes.append(abs(d["amp_pct"]))
        if d["timing_pct"] is not None:
            magnitudes.append(abs(d["timing_pct"]))
        if d["rate_pct"] is not None:
            magnitudes.append(abs(d["rate_pct"]))
    overall_magnitude = sum(magnitudes) / len(magnitudes) if magnitudes else 0.0

    return {
        "key": key, "original": original,
        "directions": directions,
        "overall_magnitude_pct": overall_magnitude,
        "influence": classify(overall_magnitude),
    }


def fmt_pct(v):
    return "N/A" if v is None else "{:+.2f}%".format(v)


def render_report(args, baseline_result, results, elapsed, timing_meaningful):
    lines = []
    lines.append("# Parameter Sensitivity Analysis")
    lines.append("")
    lines.append("Generated {}Z in {:.1f}s.".format(datetime.now(timezone.utc).isoformat(timespec="seconds"), elapsed))
    lines.append("")
    lines.append(
        "One-at-a-time (OAT) local sensitivity analysis around the current verified twin's constants. "
        "Every parameter is perturbed independently by +/-{:.0f}%; all others are held at their twin value. "
        "This measures how much the SIMULATED waveform moves when one input moves -- it is not a fit/error "
        "score against real data, and no twin was modified or saved by running this.".format(args.pct)
    )
    lines.append("")
    lines.append(
        "Disturbance held fixed for every run: gear={}, touch_type={}, force_n={}, impulse_ns={}.".format(
            args.gear, args.touch_type, args.force_n, args.impulse_ns)
    )
    lines.append("")
    lines.append(
        "Baseline: delta_I_A={:.6f} A, peak_A={:.6f} A, rise_time_s={:.6f} s.".format(
            baseline_result["delta_I_A"], baseline_result["peak_A"], baseline_result["rise_time_s"])
    )
    lines.append("")
    if not timing_meaningful:
        lines.append(
            "Note: the baseline peak occurs at t=0 for this touch point (gear={} -- typical for a touch "
            "directly on the motor's own gear, where the current response is set by an algebraic torque "
            "balance rather than anything that propagates over time). Peak-timing and rise-rate are not "
            "meaningful to compare against a zero baseline and are reported as N/A below, excluded from the "
            "overall influence average. Peak current and amplitude are unaffected and still computed "
            "normally.".format(args.gear)
        )
        lines.append("")
    lines.append(
        "Metrics -- peak current: %change in delta_I_A (touch-induced deviation from idle, not the absolute "
        "peak_A, so a shift in I_BASELINE_A itself correctly shows no effect here). peak timing: %change in "
        "time-to-peak. rise rate: %change in |delta_I_A|/time-to-peak (average slope, distinct from raw "
        "timing). amplitude: %change in RMS deviation from baseline across the full reported waveform "
        "(whole-curve, distinct from the single peak value). Overall influence = mean |%change| across all "
        "four metrics, across both perturbation directions."
    )
    lines.append("")
    lines.append(
        "Influence buckets (of that mean |%change| per {:.0f}% input step): "
        ">=75% Very High, >=30% High, >=10% Medium, >=2% Low, >=0.5% Very Small, else No Measurable Influence.".format(args.pct)
    )
    lines.append("")
    lines.append("## Ranked summary")
    lines.append("")
    for i, r in enumerate(results, 1):
        lines.append(
            "{}. **{}** -- {} (avg |change| {:.2f}% per {:.0f}% input step)".format(
                i, r["key"], r["influence"], r["overall_magnitude_pct"], args.pct)
        )
    lines.append("")
    lines.append("## Per-parameter detail")
    lines.append("")
    for r in results:
        lines.append("### {} (twin value: {})".format(r["key"], r["original"]))
        lines.append("")
        for label, d in r["directions"].items():
            if "error" in d:
                lines.append("- {}: invalid configuration -- {}".format(label, d["error"]))
                continue
            lines.append(
                "- {} (-> {}): peak current {} ({}), timing {} ({}), rise {} ({}), "
                "amplitude {} ({})".format(
                    label, d["value"], d["peak_desc"], fmt_pct(d["peak_pct"]), d["timing_desc"], fmt_pct(d["timing_pct"]),
                    d["rate_desc"], fmt_pct(d["rate_pct"]), d["amp_desc"], fmt_pct(d["amp_pct"]))
            )
        lines.append("- Overall: **{}** (avg magnitude {:.2f}%)".format(r["influence"], r["overall_magnitude_pct"]))
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parameter sensitivity analysis for the 150 RPM gear system digital twin.")
    parser.add_argument("--gear", default="Red", choices=["Yellow", "Blue", "Green", "Red"],
                         help="default Red -- Yellow has a degenerate t=0 peak, see module docstring")
    parser.add_argument("--touch-type", default="impact", choices=["steady", "impact", "tooth_strike"])
    parser.add_argument("--force-n", type=float, default=0.5)
    parser.add_argument("--impulse-ns", type=float, default=5.0)
    parser.add_argument("--pct", type=float, default=10.0, help="perturbation size, percent (default 10)")
    parser.add_argument("--out", default="sensitivity_report.md")
    args = parser.parse_args()

    verified = twin_store.load_verified()
    if verified is None:
        print("No verified twin found -- nothing to analyze.", file=sys.stderr)
        sys.exit(1)
    constants = dict(verified["constants"])

    print("Baseline: gear={} touch_type={} force_n={} impulse_ns={}".format(
        args.gear, args.touch_type, args.force_n, args.impulse_ns))
    t0 = time.time()
    baseline_result = run_one(constants, args.gear, args.touch_type, args.force_n, args.impulse_ns)
    timing_meaningful = baseline_result["rise_time_s"] > 1e-9
    if not timing_meaningful:
        print("Note: baseline peak occurs at t=0 for gear={} -- timing/rate metrics will be N/A "
              "(see module docstring). Try --gear Red/Green/Blue for a non-degenerate rise time.".format(args.gear))

    results = []
    for key in sorted(constants.keys()):
        print("  analyzing {} ...".format(key))
        results.append(analyze_parameter(
            key, constants, baseline_result, args.gear, args.touch_type, args.force_n, args.impulse_ns,
            args.pct, timing_meaningful))

    results.sort(key=lambda r: r["overall_magnitude_pct"], reverse=True)
    elapsed = time.time() - t0

    report = render_report(args, baseline_result, results, elapsed, timing_meaningful)
    with open(args.out, "w") as f:
        f.write(report)
    print()
    print(report)
    print("\nWritten to {}".format(args.out))


if __name__ == "__main__":
    main()
