"""Acquisition -- owns the serial port to the ESP32 INA228 sensor: finds
it, connects, reads its plain-text protocol, batches samples into blocks,
and reconnects on failure. Relocated from gearsystem150_app.py
(_ina228_sensor_gateway_loop, _find_gearsystem_sensor_port,
_prefer_macos_cu_device, start_gearsystem_sensor_gateway).

Speaks the ESP32 sender's plain-text wire protocol (esp32_ina228_reader/
src/main.cpp): one signed integer mA reading per line at 460800 baud. All
conversion, smoothing, and gear classification happens in
signal_processing.py / matching.py, not on the chip -- the ESP32 only
samples and forwards.

This is the only sensor gateway in this codebase. The ACS712 raw-ADC
binary-block gateway that used to live alongside it in
gearsystem150_app.py was removed 2026-08-07: it was never started (only
this loop was ever handed to threading.Thread) once the sensor swapped to
the INA228, so it was pure dead weight -- a second, unreachable
current-sensing pipeline sitting next to the real one.
"""
import threading
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

from . import live_state, signal_processing

_INA228_BAUD = 460800
_INA228_BLOCK_SAMPLES = 256  # lines accumulated per processed block -- see the plain-text protocol note in main.cpp
# Observed in practice: the board went silent the instant the motor was switched on and never
# recovered on its own (no exception, no new lines) -- consistent with the I2C bus locking up
# from motor electrical noise, which this firmware has no onboard recovery from. Rather than
# require a manual restart every time that happens, force a reconnect if the board goes quiet
# this long while still marked "connected" -- reopening the port toggles DTR, which resets the
# ESP32 the same way manually restarting this gateway did to recover from that exact failure.
_INA228_STALE_RECONNECT_S = 8

# USB-to-serial bridge chips ESP32 dev boards commonly use, matched against
# each port's pyserial description/manufacturer string.
_ESP32_PORT_KEYWORDS = ("cp210", "ch340", "ch910", "silicon labs", "wchusb", "usb-serial", "usb serial", "usbserial", "esp32", "ftdi")


def _prefer_macos_cu_device(candidates):
    """On macOS, pyserial can list both /dev/cu.X and /dev/tty.X for the
    same physical device -- /dev/tty.X blocks open() until DCD is asserted
    (can hang indefinitely waiting for a signal some USB-serial chips never
    raise), while /dev/cu.X (the "call-up" device) doesn't. No-op on
    Windows/Linux, where no device path starts with /dev/cu."""
    cu_candidates = [p for p in candidates if p.device.startswith("/dev/cu.")]
    return cu_candidates[0] if cu_candidates else candidates[0]


def find_gearsystem_sensor_port():
    """Cross-platform scan via pyserial's list_ports for a port that looks
    like an ESP32 USB-serial bridge. Falls back to the only port present if
    exactly one exists (on a dev machine with nothing else plugged in,
    that's almost always the board).

    Matching is keyword-OR plus a separate "usb"+"serial"-both-present
    check -- macOS's generic USB-serial class driver describes this
    exact board as "USB Single Serial", which contains neither "usb-serial"
    nor "usb serial" as a contiguous substring (the word "Single" splits
    them), so the keyword list alone missed it."""
    if list_ports is None:
        return None, []
    ports = list(list_ports.comports())

    def looks_like_esp32(p):
        desc = f"{p.description} {p.manufacturer or ''}".lower()
        if any(k in desc for k in _ESP32_PORT_KEYWORDS):
            return True
        return "usb" in desc and "serial" in desc

    candidates = [p for p in ports if looks_like_esp32(p)]
    if not candidates and len(ports) == 1:
        candidates = ports
    if not candidates:
        return None, ports
    return _prefer_macos_cu_device(candidates).device, ports


def sensor_gateway_loop():
    while True:
        port, available_ports = find_gearsystem_sensor_port()
        if not port:
            error = (
                "no serial ports detected at all" if not available_ports
                else f"no ESP32-looking port among {len(available_ports)} available: "
                     + ", ".join(f"{p.device} ({p.description})" for p in available_ports)
            )
            with live_state.lock:
                live_state.state["connected"] = False
                live_state.state["status"] = "waiting_for_sensor"
                live_state.state["port"] = None
                live_state.state["error"] = error
            time.sleep(2)
            continue
        ser = None
        try:
            ser = serial.Serial(port, _INA228_BAUD, timeout=2)
            # pyserial asserts both DTR and RTS by default on open() and never
            # releases them again for the life of the connection (SerialBase
            # hardcodes _dtr_state=_rts_state=True; Serial.open() pushes both to
            # the hardware once via ioctl, unconditionally -- see pyserial's
            # serialposix.py). On this board that holds the ESP32's EN/reset
            # line active, so the chip never boots at all -- confirmed via a
            # standalone experiment: left at pyserial's default, zero bytes are
            # ever received, no boot banner, no INA228 init; explicitly
            # released, the boot banner, INA228 init, and the fast current
            # stream all appear within under a second. Must be released before
            # the board can run.
            ser.dtr = False
            ser.rts = False
            time.sleep(2)  # let the board finish booting (banner + INA228 init) before reading
            ser.reset_input_buffer()
            # Both cleared here, not just left to be overwritten by the next auto-calibration --
            # otherwise there's a window (up to ~18s: the 8s delay plus up to a 10s sampling
            # window) right after every reconnect where stale state from a DIFFERENT session
            # (different physical setup, possibly -- a stall-triggered reconnect, or today,
            # an actual teardown/rebuild) is still silently in use. Better to report
            # "not calibrated yet" honestly than classify against a number that may no longer
            # mean anything.
            live_state.recent_means.clear()
            live_state.real_zero_A = None
            live_state.noise_floor_at_cal = None
            live_state.part_interruption_candidate_gear = None
            live_state.part_interruption_candidate_since = None
            live_state.connect_generation += 1
            with live_state.lock:
                live_state.state["connected"] = True
                live_state.state["status"] = "connected"
                live_state.state["port"] = port
                live_state.state["error"] = None
                live_state.state["part_interruption_gear"] = None
            threading.Thread(
                target=signal_processing.auto_calibrate_after_connect,
                args=(live_state.connect_generation,), daemon=True,
            ).start()

            # Plain-text line reader -- one "<int>\n" per sample (see
            # esp32_ina228_reader/src/main.cpp's v4 header note for why this
            # replaced the old binary block framing: at ~893Hz the wire never
            # carried enough traffic to need packing, so the magic-byte scan
            # and checksum were pure overhead). pyserial's readline() does its
            # own internal buffering, so there's no manual byte-slicing here.
            # A line that isn't a bare integer (boot banner, self-test print,
            # a partial line from a mid-write reconnect) just fails int() and
            # gets skipped -- self-resyncing on the next newline.
            last_rx = time.time()
            block_samples = []
            block_t0 = None
            while True:
                line = ser.readline()
                now = time.time()
                if not line:
                    if now - last_rx > _INA228_STALE_RECONNECT_S:
                        raise TimeoutError(
                            f"no data from board for {now - last_rx:.0f}s -- forcing reconnect/reset"
                        )
                    continue
                last_rx = now
                try:
                    sample = int(line.decode(errors="ignore").strip())
                except ValueError:
                    continue
                live_state.raw_buffer.append((now, sample))
                if block_t0 is None:
                    block_t0 = now
                block_samples.append(sample)
                if len(block_samples) < _INA228_BLOCK_SAMPLES:
                    continue
                elapsed = now - block_t0
                rate_hz = int(round(_INA228_BLOCK_SAMPLES / elapsed)) if elapsed > 0 else 0
                # Failure-artifact rejection, unchanged from the binary protocol: a failed
                # I2C transaction on the ESP32 returns 0 instead of erroring, and a block
                # that's flat 0 end-to-end is that failure, not a real reading (every
                # genuine block -- idle or touched -- has shown non-zero ripple).
                if not (min(block_samples) == 0 and max(block_samples) == 0):
                    signal_processing.process_block(block_samples, rate_hz)
                block_samples = []
                block_t0 = None
        except Exception as e:
            with live_state.lock:
                live_state.state["connected"] = False
                live_state.state["status"] = "waiting_for_sensor"
                live_state.state["port"] = None
                live_state.state["error"] = str(e)
            time.sleep(2)
        finally:
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass


def start_gearsystem_sensor_gateway():
    if serial is None:
        print("pyserial not installed -- live current gateway disabled (everything else works fine)")
        return
    threading.Thread(target=sensor_gateway_loop, daemon=True).start()
