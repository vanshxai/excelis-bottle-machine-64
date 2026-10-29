import os
import sqlite3
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gearsystem_recordings.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            started_at REAL NOT NULL,
            duration_s REAL NOT NULL,
            sample_count INTEGER NOT NULL,
            mean_A REAL, std_A REAL, min_A REAL, max_A REAL,
            effective_hz REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recording_samples (
            recording_id INTEGER NOT NULL,
            t REAL NOT NULL,
            current_A REAL NOT NULL
        )
    """)
    return conn


def record_gearsystem_current(label, duration_s, live_channels, live_lock, raw_tag):
    """Tight-poll capture straight off the raw live-channel dict (not the
    already rate-limited 20Hz bridge buffer) so the recorded sample rate
    reflects what the sensor/serial link can actually deliver, not an
    artificial ceiling. Dedupes on last_update timestamp so it only
    records genuinely new samples, however fast or slow those arrive."""
    samples = []
    last_seen = None
    t0 = time.time()
    while time.time() - t0 < duration_s:
        with live_lock:
            ch = live_channels.get(raw_tag, {})
            val = ch.get("current_A")
            ts = ch.get("last_update")
        if val is not None and ts != last_seen:
            samples.append((ts, val))
            last_seen = ts
        time.sleep(0.001)

    n = len(samples)
    if n == 0:
        return {"error": "no samples captured -- ESP32 not connected or not sending data"}

    vals = [v for _, v in samples]
    mean_A = sum(vals) / n
    var = sum((v - mean_A) ** 2 for v in vals) / n
    std_A = var ** 0.5
    min_A = min(vals)
    max_A = max(vals)
    span = samples[-1][0] - samples[0][0]
    effective_hz = (n - 1) / span if span > 0 else 0.0

    conn = _connect()
    cur = conn.execute(
        "INSERT INTO recordings (label, started_at, duration_s, sample_count, mean_A, std_A, min_A, max_A, effective_hz) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (label, t0, duration_s, n, mean_A, std_A, min_A, max_A, effective_hz),
    )
    recording_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO recording_samples (recording_id, t, current_A) VALUES (?, ?, ?)",
        [(recording_id, t, v) for t, v in samples],
    )
    conn.commit()
    conn.close()

    return {
        "id": recording_id, "label": label, "started_at": t0, "duration_s": duration_s,
        "sample_count": n, "mean_A": round(mean_A, 6), "std_A": round(std_A, 6),
        "min_A": round(min_A, 6), "max_A": round(max_A, 6), "effective_hz": round(effective_hz, 2),
        "samples": [{"t": t, "current_A": v} for t, v in samples],
    }


def list_recordings():
    conn = _connect()
    rows = conn.execute(
        "SELECT id, label, started_at, duration_s, sample_count, mean_A, std_A, min_A, max_A, effective_hz "
        "FROM recordings ORDER BY started_at DESC"
    ).fetchall()
    conn.close()
    keys = ["id", "label", "started_at", "duration_s", "sample_count", "mean_A", "std_A", "min_A", "max_A", "effective_hz"]
    return [dict(zip(keys, row)) for row in rows]


def get_recording_samples(recording_id):
    conn = _connect()
    rows = conn.execute(
        "SELECT t, current_A FROM recording_samples WHERE recording_id = ? ORDER BY t", (recording_id,)
    ).fetchall()
    conn.close()
    return [{"t": t, "current_A": v} for t, v in rows]
