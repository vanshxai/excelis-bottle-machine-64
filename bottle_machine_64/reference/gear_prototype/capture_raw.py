"""
Capture raw ADC samples from the ESP32 streamer to a .npy file, with a
per-sample timebase, so a single continuous recording can be segmented
afterwards (motor off vs motor on, untouched vs gear pressed).

Recording the transition inside ONE trace is deliberate: comparing two
separate captures confounds the thing being tested with thermal drift of
the ACS712 zero-point, which has been observed moving tens of millivolts
(~1A worth) over a session. Within a single trace that drift is slow and
continuous, so a step change is attributable to the event, not the clock.

Usage:
    python3 capture_raw.py <seconds> <output.npy>
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


def main(seconds, path):
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2.0)  # board settles after the port opens (opening can reset it)
    ser.reset_input_buffer()

    buf = bytearray()
    pos = 0
    samples = []
    block_times = []   # host arrival time per block, for a wall-clock timebase
    rates = []
    bad = 0

    t0 = time.time()
    while time.time() - t0 < seconds:
        chunk = ser.read(16384)
        now = time.time() - t0
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
                block_times.append(now)
                rates.append(rate)
            else:
                bad += 1
            pos = i + FRAME_LEN
        if pos > 1 << 20:
            del buf[:pos]
            pos = 0
    ser.close()

    arr = np.array(samples, dtype=np.uint16)
    fs = float(np.median(rates)) if rates else 8000.0
    np.save(path, arr)
    np.save(path.replace(".npy", "_meta.npy"),
            np.array([fs, len(arr), bad], dtype=float))
    print(f"saved {len(arr)} samples to {path}")
    print(f"sample rate: median {fs:.0f} Hz (min {min(rates)}, max {max(rates)}), "
          f"{bad} corrupted blocks dropped")
    print(f"duration: {len(arr)/fs:.1f}s")


if __name__ == "__main__":
    main(float(sys.argv[1]), sys.argv[2])
