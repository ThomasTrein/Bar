"""
FIFO Stock Engine voor KSA Bar.
Bij aankoop: nieuwe batch toevoegen.
Bij verkoop: oudste batch(es) eerst verminderen.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database.db import get_db


def add_batch(product_id: int, hoeveelheid: int, aankoop_prijs: float, aankoop_id: int = None):
    """Voeg een FIFO batch toe en verhoog de stock."""
    conn = get_db()
    conn.execute(
        """INSERT INTO fifo_batches
           (product_id, aankoop_prijs, hoeveelheid_origineel, hoeveelheid_resterend, aankoop_id)
           VALUES (?, ?, ?, ?, ?)""",
        (product_id, aankoop_prijs, hoeveelheid, hoeveelheid, aankoop_id)
    )
    conn.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (hoeveelheid, product_id)
    )
    conn.commit()
    conn.close()


def consume_stock(product_id: int, hoeveelheid: int) -> float:
    """
    Verminder stock via FIFO.
    Geeft de totale aankoopkost van de geconsumeerde hoeveelheid terug.
    """
    conn = get_db()
    batches = conn.execute(
        """SELECT id, aankoop_prijs, hoeveelheid_resterend
           FROM fifo_batches
           WHERE product_id = ? AND hoeveelheid_resterend > 0
           ORDER BY datum ASC, id ASC""",
        (product_id,)
    ).fetchall()

    resterend = hoeveelheid
    totale_kost = 0.0

    for batch in batches:
        if resterend <= 0:
            break
        te_nemen = min(resterend, batch['hoeveelheid_resterend'])
        totale_kost += te_nemen * batch['aankoop_prijs']
        resterend -= te_nemen
        conn.execute(
            "UPDATE fifo_batches SET hoeveelheid_resterend = hoeveelheid_resterend - ? WHERE id = ?",
            (te_nemen, batch['id'])
        )

    conn.execute(
        "UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?",
        (hoeveelheid, product_id)
    )
    conn.commit()
    conn.close()
    return totale_kost


def restore_stock(product_id: int, hoeveelheid: int, aankoop_kost: float = 0.0):
    """Herstel stock bij annulering of verwijdering van bestelling."""
    conn = get_db()
    conn.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (hoeveelheid, product_id)
    )
    if aankoop_kost > 0 and hoeveelheid > 0:
        prijs_per_stuk = aankoop_kost / hoeveelheid
        conn.execute(
            """INSERT INTO fifo_batches
               (product_id, aankoop_prijs, hoeveelheid_origineel, hoeveelheid_resterend)
               VALUES (?, ?, ?, ?)""",
            (product_id, prijs_per_stuk, hoeveelheid, hoeveelheid)
        )
    conn.commit()
    conn.close()


def get_fifo_cost_per_unit(product_id: int) -> float:
    """Gewogen gemiddelde aankoopprijs op basis van resterend FIFO stock."""
    conn = get_db()
    batches = conn.execute(
        """SELECT aankoop_prijs, hoeveelheid_resterend
           FROM fifo_batches
           WHERE product_id = ? AND hoeveelheid_resterend > 0""",
        (product_id,)
    ).fetchall()
    conn.close()

    totaal = sum(b['hoeveelheid_resterend'] for b in batches)
    kost = sum(b['aankoop_prijs'] * b['hoeveelheid_resterend'] for b in batches)
    return (kost / totaal) if totaal else 0.0


def get_product_profit_stats(product_id: int, start_datum: str, eind_datum: str) -> dict:
    """Winststatistieken voor een product over een periode."""
    from database.db import get_db as _db
    conn = _db()
    row = conn.execute(
        """SELECT
               COALESCE(SUM(oi.hoeveelheid), 0) as totaal_stuks,
               COALESCE(SUM(oi.hoeveelheid * oi.verkoop_prijs_snapshot), 0) as omzet
           FROM order_items oi
           JOIN orders o ON oi.order_id = o.id
           WHERE oi.product_id = ?
             AND o.geannuleerd = 0
             AND o.tijdstip BETWEEN ? AND ?""",
        (product_id, start_datum, eind_datum)
    ).fetchone()
    conn.close()

    totaal_stuks = row['totaal_stuks']
    omzet = row['omzet']
    gem_aankoop = get_fifo_cost_per_unit(product_id)
    kosten = totaal_stuks * gem_aankoop
    return {
        'product_id': product_id,
        'totaal_stuks': totaal_stuks,
        'omzet': round(omzet, 2),
        'kosten': round(kosten, 2),
        'winst': round(omzet - kosten, 2),
        'gem_aankoop_prijs': round(gem_aankoop, 4),
    }
