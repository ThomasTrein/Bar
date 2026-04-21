"""Database verbinding helpers voor KSA Bar."""
import sqlite3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DATABASE_PATH


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


def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid


def executemany(sql, params_list):
    conn = get_db()
    conn.executemany(sql, params_list)
    conn.commit()
    conn.close()


def get_setting(sleutel, default=None):
    row = query("SELECT waarde FROM settings WHERE sleutel = ?", (sleutel,), one=True)
    return row['waarde'] if row else default


def set_setting(sleutel, waarde):
    execute(
        "INSERT OR REPLACE INTO settings (sleutel, waarde) VALUES (?, ?)",
        (sleutel, str(waarde))
    )


def add_log(type_, beschrijving, person_id=None, referentie_id=None, referentie_type=None):
    execute(
        """INSERT INTO logs (type, beschrijving, person_id, referentie_id, referentie_type)
           VALUES (?, ?, ?, ?, ?)""",
        (type_, beschrijving, person_id, referentie_id, referentie_type)
    )
