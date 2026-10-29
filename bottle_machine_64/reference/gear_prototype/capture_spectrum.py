"""
Capture raw ADC blocks from the ESP32 streamer and report the current
spectrum -- the diagnostic tool for figuring out what is actually in the
motor-current signal.

Run it while the motor is doing something known (idle / a specific gear
being pressed), and compare the peak list between runs. Gear identity
lives in the tooth-pass frequencies, so this is the instrument that
decides whether gear identification is possible at all.

The gearbox's output gear was removed with the cap, so the "150 RPM at the
output" anchor that used to fix absolute shaft speeds is gone -- the motor
now runs unloaded at an unknown speed. Absolute tooth-pass frequencies
therefore CANNOT be predicted right now, only measured. What survives is
their ratios, which depend purely on tooth counts (all measured):

    Yellow : Green : Red  =  9 : 8/3 : 64/81   =   11.39 : 3.375 : 1

i.e. each gear's tooth-pass frequency is exactly 3.375x the next one down.
That fixed ladder is the fingerprint to hunt for -- find one peak and the
others are pinned, whatever the motor speed happens to be.

Usage:
    python3 capture_spectrum.py [seconds] [label]
"""
import struct
import sys
import time

import numpy as np
import serial

PORT = "/dev/cu.usbserial-5A580468301"
BAUD = 460800
BLOCK_SAMPLES = 256
FRAME_LEN = 8 + BLOCK_SAMPLES * 2 + 2

SENSITIVITY_MV_PER_A = 66.0 * (3.3 / 5.0)  # ACS712-30A, ratiometric to a 3.3V supply

# The firmware streams raw 12-bit ADC counts (not calibrated millivolts --
# doing the calibration per-sample on-chip capped the sample rate at
# 5781 Hz, short of the 8 kHz target).
#
# The nominal 3100/4095 factor is WRONG on this chip: it put the idle level
# at 1367mV where the eFuse-calibrated firmware read 1683mV on the very
# same signal, a 23% scale error. The factor below is back-solved from that
# comparison instead (1683/1806 counts). It is a SINGLE-POINT calibration
# assuming a zero intercept, so absolute amps carry a few percent of
# residual error -- fine for "is the current ~0.3A or ~1A", not good enough
# to trust the third decimal. Gear identification does not depend on it at
# all, since frequencies are invariant to any linear scaling.
COUNTS_TO_MV = 0.9316

# Tooth-pass frequency ratios, normalized to Red = 1. Tooth counts are all
# measured/locked (Yellow 9, Blue 27/8, Green 27/8, Red 27/16), so these
# ratios are exact even though the absolute frequencies are not known.
GEAR_RATIOS = {"Yellow": 9.0, "Green": 8.0 / 3.0, "Red": 64.0 / 81.0}


def capture(seconds):
    """Returns (samples_mV, achieved_rate_hz). Frames failing checksum are
    dropped rather than silently accepted -- a corrupted block would inject
    a fake broadband transient straight into the FFT."""
    # Read into a bytearray and advance an index instead of re-slicing the
    # buffer per frame. The naive `buf = buf[i+FRAME_LEN:]` version copies
    # the entire remaining buffer on every single frame, which made the
    # reader fall behind the 16 kB/s stream; the resulting back-pressure
    # stalled the ESP32's write() and dragged its sampling rate from
    # 8009 Hz down to 5779 Hz. Uneven sampling smears spectral peaks, so
    # keeping the host ahead of the stream is a correctness issue here,
    # not just a performance one.
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2.0)  # let the board settle after the port opens (can reset it)
    ser.reset_input_buffer()

    buf = bytearray()
    pos = 0
    samples = []
    rates = []
    bad = 0
    t0 = time.time()
    while time.time() - t0 < seconds:
        chunk = ser.read(16384)
        if chunk:
            buf += chunk
        while True:
            i = buf.find(b"\xAA\x55", pos)
            if i < 0 or len(buf) - i < FRAME_LEN:
                break
            _seq, n, rate = struct.unpack("<HHH", buf[i + 2:i + 8])
            if n != BLOCK_SAMPLES:
                pos = i + 2
                continue
            block = struct.unpack(f"<{BLOCK_SAMPLES}H", buf[i + 8:i + 8 + BLOCK_SAMPLES * 2])
            cks = struct.unpack("<H", buf[i + 8 + BLOCK_SAMPLES * 2:i + FRAME_LEN])[0]
            if (sum(block) & 0xFFFF) == cks:
                samples.extend(block)
                rates.append(rate)
            else:
                bad += 1
            pos = i + FRAME_LEN
        # Compact only occasionally, so the copy cost is amortized instead
        # of being paid once per frame.
        if pos > 1 << 20:
            del buf[:pos]
            pos = 0
    ser.close()
    if bad:
        print(f"(dropped {bad} corrupted blocks)")
    rate_arr = np.array(rates) if rates else np.array([8000.0])
    print(f"ESP32 sampling rate: median {np.median(rate_arr):.0f} Hz, "
          f"min {rate_arr.min():.0f}, max {rate_arr.max():.0f}  "
          f"({100*(rate_arr < 7900).mean():.1f}% of blocks below 7900 Hz)")
    return np.array(samples, dtype=float) * COUNTS_TO_MV, float(np.median(rate_arr))


def analyze(mV, fs, label):
    print(f"\n=== {label} ===")
    print(f"samples {len(mV)}  ({len(mV)/fs:.1f}s at {fs:.0f} Hz)")
    print(f"raw mV: mean {mV.mean():.1f}  sd {mV.std():.1f}  min {mV.min():.0f}  max {mV.max():.0f}")

    # Rare commutation/EMI spikes hit the ADC rails and would dominate the
    # FFT as broadband splatter, masking the narrowband tooth-pass peaks we
    # are actually looking for. Clip them to a robust range first.
    med = np.median(mV)
    mad = np.median(np.abs(mV - med)) * 1.4826  # ~sigma for gaussian noise
    lo, hi = med - 8 * mad, med + 8 * mad
    n_clipped = int(((mV < lo) | (mV > hi)).sum())
    x = np.clip(mV, lo, hi)
    print(f"outlier clip at +/-8 MAD ({lo:.0f}..{hi:.0f} mV): {n_clipped} samples "
          f"({100*n_clipped/len(mV):.3f}%)")

    ac = x - x.mean()
    print(f"AC RMS: {ac.std():.2f} mV  ({ac.std()/SENSITIVITY_MV_PER_A:.4f} A)")

    # Welch PSD: average many overlapping windows so random noise averages
    # down while any genuinely periodic component stays put.
    nperseg = 4096
    win = np.hanning(nperseg)
    step = nperseg // 2
    segs = [ac[i:i + nperseg] * win for i in range(0, len(ac) - nperseg + 1, step)]
    if not segs:
        print("not enough samples for a spectrum")
        return None
    psd = np.mean([np.abs(np.fft.rfft(s)) ** 2 for s in segs], axis=0)
    freqs = np.fft.rfftfreq(nperseg, 1 / fs)
    print(f"Welch PSD: {len(segs)} segments, resolution {fs/nperseg:.2f} Hz")

    # Ignore the lowest bins -- DC drift and thermal wander live there and
    # are not tooth-pass content.
    lo_bin = np.searchsorted(freqs, 20.0)
    band = psd[lo_bin:]
    bfreq = freqs[lo_bin:]
    order = np.argsort(band)[::-1]

    print("\ntop spectral peaks (20 Hz - Nyquist):")
    shown = []
    for idx in order:
        f = bfreq[idx]
        if any(abs(f - s) < 8 for s in shown):
            continue  # skip neighbours of an already-listed peak
        shown.append(f)
        rel = band[idx] / np.median(band)
        print(f"   {f:8.1f} Hz   power {band[idx]:12.1f}   {rel:8.1f}x median")
        if len(shown) >= 12:
            break
    return shown


if __name__ == "__main__":
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    label = sys.argv[2] if len(sys.argv) > 2 else "capture"
    mV, fs = capture(secs)
    if len(mV) == 0:
        print("NO DATA -- is the streamer firmware running?")
        sys.exit(1)
    analyze(mV, fs, label)
