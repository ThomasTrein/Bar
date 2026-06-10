"""Database verbinding helpers voor KSA Bar."""
import sqlite3
import os
import sys
import time
import threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DATABASE_PATH

# ── Simple in-memory TTL cache ───────────────────────
_cache_lock = threading.Lock()
_settings_cache: dict = {}          # sleutel → (waarde, expires_at)
SETTINGS_TTL = 30                   # seconds


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def query(sql, params=(), one=False):
    conn = get_db()
    cur = conn.execute(sql, params)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


_write_counter = 0
_CHECKPOINT_INTERVAL = 100


def execute(sql, params=()):
    global _write_counter
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    lastrowid = cur.lastrowid
    _write_counter += 1
    if _write_counter >= _CHECKPOINT_INTERVAL:
        _write_counter = 0
        try:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except Exception:
            pass
    conn.close()
    return lastrowid


def executemany(sql, params_list):
    conn = get_db()
    conn.executemany(sql, params_list)
    conn.commit()
    conn.close()


def get_setting(sleutel, default=None):
    now = time.monotonic()
    with _cache_lock:
        entry = _settings_cache.get(sleutel)
        if entry and now < entry[1]:
            return entry[0]
    row = query("SELECT waarde FROM settings WHERE sleutel = ?", (sleutel,), one=True)
    value = row['waarde'] if row else default
    with _cache_lock:
        _settings_cache[sleutel] = (value, now + SETTINGS_TTL)
    return value


def set_setting(sleutel, waarde):
    execute(
        "INSERT OR REPLACE INTO settings (sleutel, waarde) VALUES (?, ?)",
        (sleutel, str(waarde))
    )
    # Invalidate cache for this key
    with _cache_lock:
        _settings_cache.pop(sleutel, None)


def add_log(type_, beschrijving, person_id=None, referentie_id=None, referentie_type=None):
    execute(
        """INSERT INTO logs (type, beschrijving, person_id, referentie_id, referentie_type)
           VALUES (?, ?, ?, ?, ?)""",
        (type_, beschrijving, person_id, referentie_id, referentie_type)
    )
