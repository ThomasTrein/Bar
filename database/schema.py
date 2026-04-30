"""Database schema en initialisatie voor KSA Bar systeem."""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DATABASE_PATH, DEFAULT_SETTINGS

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voornaam TEXT NOT NULL,
    achternaam TEXT DEFAULT '',
    bijnaam TEXT DEFAULT '',
    foto_path TEXT DEFAULT '',
    is_bond INTEGER DEFAULT 0,
    actief INTEGER DEFAULT 1,
    aangemaakt_op DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL UNIQUE,
    volgorde INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    categorie_id INTEGER REFERENCES categories(id),
    verkoop_prijs REAL NOT NULL DEFAULT 0,
    aankoop_prijs REAL DEFAULT 0,
    actief INTEGER DEFAULT 1,
    foto_path TEXT DEFAULT '',
    stock INTEGER DEFAULT 0,
    aangemaakt_op DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_doors (
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    deur INTEGER NOT NULL CHECK(deur IN (1,2,3)),
    PRIMARY KEY (product_id, deur)
);

CREATE TABLE IF NOT EXISTS fifo_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    aankoop_prijs REAL NOT NULL,
    hoeveelheid_origineel INTEGER NOT NULL,
    hoeveelheid_resterend INTEGER NOT NULL,
    datum DATETIME DEFAULT CURRENT_TIMESTAMP,
    aankoop_id INTEGER
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tijdstip DATETIME DEFAULT CURRENT_TIMESTAMP,
    type TEXT DEFAULT 'normaal' CHECK(type IN ('normaal','bond')),
    geannuleerd INTEGER DEFAULT 0,
    video_path TEXT DEFAULT '',
    gestart_door_id INTEGER REFERENCES persons(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    person_id INTEGER REFERENCES persons(id),
    product_id INTEGER REFERENCES products(id),
    hoeveelheid INTEGER NOT NULL DEFAULT 1,
    verkoop_prijs_snapshot REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS door_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    deur INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('unlock','open','close','lock','timeout')),
    tijdstip DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bar_evenings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activator_id INTEGER REFERENCES persons(id),
    deactivator_id INTEGER REFERENCES persons(id),
    start_tijd DATETIME DEFAULT CURRENT_TIMESTAMP,
    eind_tijd DATETIME,
    start_inventaris TEXT DEFAULT '{}',
    eind_inventaris TEXT DEFAULT '{}',
    verbruik TEXT DEFAULT '{}',
    video_path TEXT DEFAULT '',
    actief INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS refill_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER REFERENCES persons(id),
    start_tijd DATETIME DEFAULT CURRENT_TIMESTAMP,
    eind_tijd DATETIME,
    video_path TEXT DEFAULT '',
    deur_wijzigingen TEXT DEFAULT '{}',
    actief INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS shop_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER REFERENCES persons(id),
    tijdstip DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shop_purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aankoop_id INTEGER REFERENCES shop_purchases(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    hoeveelheid INTEGER NOT NULL,
    aankoop_prijs_per_stuk REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tijdstip DATETIME DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    beschrijving TEXT NOT NULL,
    person_id INTEGER REFERENCES persons(id),
    referentie_id INTEGER,
    referentie_type TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    sleutel TEXT PRIMARY KEY,
    waarde TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_sessions (
    token TEXT PRIMARY KEY,
    aangemaakt_op DATETIME DEFAULT CURRENT_TIMESTAMP,
    verlopen_op DATETIME
);
"""


def init_db():
    """Initialiseer de database met schema en standaard data."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.executescript(SCHEMA_SQL)

    for sleutel, waarde in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (sleutel, waarde) VALUES (?, ?)",
            (sleutel, waarde)
        )

    # De Bond als vast systeemprofiel (id=1)
    conn.execute("""
        INSERT OR IGNORE INTO persons (id, voornaam, is_bond, actief)
        VALUES (1, 'De Bond', 1, 1)
    """)

    # Standaard categorieën
    for i, cat in enumerate(['Frisdranken', 'Bier'], 1):
        conn.execute(
            "INSERT OR IGNORE INTO categories (naam, volgorde) VALUES (?, ?)",
            (cat, i)
        )

    conn.commit()

    # Migraties voor bestaande databases
    migrations = [
        "ALTER TABLE bar_evenings ADD COLUMN naam TEXT DEFAULT ''",
        "ALTER TABLE products ADD COLUMN bak_grootte INTEGER DEFAULT NULL",
        """CREATE TABLE IF NOT EXISTS betalingen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER REFERENCES persons(id),
            bedrag REAL NOT NULL,
            beschrijving TEXT DEFAULT '',
            tijdstip DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        "ALTER TABLE products ADD COLUMN aankoop_prijs REAL DEFAULT 0",
        """CREATE TABLE IF NOT EXISTS person_blocked_products (
            person_id  INTEGER REFERENCES persons(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            PRIMARY KEY (person_id, product_id)
        )""",
        """CREATE TABLE IF NOT EXISTS person_blocked_categories (
            person_id   INTEGER REFERENCES persons(id) ON DELETE CASCADE,
            category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
            PRIMARY KEY (person_id, category_id)
        )""",
        "ALTER TABLE products ADD COLUMN globally_locked INTEGER DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN deur_niet_geopend INTEGER DEFAULT 0",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass  # Kolom/tabel bestaat al

    conn.close()
    print("[OK] Database geinitialiseerd.")


if __name__ == '__main__':
    init_db()
