"""Cosmetic waveform generator -- relocated from gearsystem150_app.py's
_simulate_touch_waveform(). NOT a physics source of truth (own original
docstring said so); predates signature/dynamic.py's real RK4 waveform and
was kept alongside it, not replaced by it, because /api/gearsystem/touch_sim
(cosmetic, fast) and /api/gearsystem/touch_sim_dynamic (real, slower) are
both still live, separate UI features -- see the migration plan's
"APIs that remain unchanged" section.
"""
import math


def simulate_touch_waveform(I_baseline, delta_I, rise_time_s, touch_type, n_points=60):
    """Synthetic current-vs-time trace for a simulated touch, shaped per
    signature_shape ("spike_then_partial_recovery" for impact, a held step
    for steady press) -- for visualization, not a physics source of truth."""
    rise_ms = max(rise_time_s * 1000, 0.5)
    points = []
    if touch_type == "impact":
        pre_ms = rise_ms * 2
        decay_ms = rise_ms * 8
        residual_frac = 0.15
        total_ms = pre_ms + rise_ms + decay_ms
        for i in range(n_points):
            t = total_ms * i / (n_points - 1)
            if t < pre_ms:
                current = I_baseline
            elif t < pre_ms + rise_ms:
                frac = (t - pre_ms) / rise_ms
                current = I_baseline + delta_I * frac
            else:
                frac = min((t - pre_ms - rise_ms) / decay_ms, 1.0)
                decay = math.exp(-3 * frac)
                current = I_baseline + delta_I * (residual_frac + (1 - residual_frac) * decay)
            points.append({"t_ms": round(t, 3), "current_A": current})
    else:
        pre_ms = rise_ms * 2
        hold_ms = rise_ms * 5
        fall_ms = rise_ms
        total_ms = pre_ms + rise_ms + hold_ms + fall_ms
        for i in range(n_points):
            t = total_ms * i / (n_points - 1)
            if t < pre_ms:
                current = I_baseline
            elif t < pre_ms + rise_ms:
                frac = (t - pre_ms) / rise_ms
                current = I_baseline + delta_I * frac
            elif t < pre_ms + rise_ms + hold_ms:
                current = I_baseline + delta_I
            else:
                frac = min((t - pre_ms - rise_ms - hold_ms) / fall_ms, 1.0)
                current = I_baseline + delta_I * (1 - frac)
            points.append({"t_ms": round(t, 3), "current_A": current})
    return points
