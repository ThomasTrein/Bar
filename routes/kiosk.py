"""Kiosk routes voor KSA Bar."""
import os, json, uuid
from flask import Blueprint, render_template, request, redirect, url_for, session
from database.db import get_db, query, execute, add_log, get_setting
from hardware.gpio_controller import get_fridge_controller
from hardware.camera import start_recording, stop_recording
from services.fifo import consume_stock, restore_stock
from config import UPLOADS_PERSONS_DIR

kiosk_bp = Blueprint('kiosk', __name__)


# ─── Helpers ────────────────────────────────────────────────────────────────

def get_order():
    return session.get('active_order', {'regels': [], 'started': False,
                                        'recording_path': '', 'current_person_id': None,
                                        'current_person_naam': None, 'deuren_nodig': []})

def save_order(o):
    session['active_order'] = o
    session.modified = True

def alle_personen():
    return query(
        """SELECT id, voornaam, achternaam, bijnaam, foto_path
           FROM persons WHERE actief = 1 AND is_bond = 0
           ORDER BY LOWER(COALESCE(NULLIF(bijnaam,''), voornaam))"""
    )

def alle_producten_per_categorie():
    cats = query("SELECT * FROM categories ORDER BY volgorde")
    prods = query(
        """SELECT p.*, c.naam as cat_naam, c.volgorde as cat_volgorde,
               GROUP_CONCAT(pd.deur) as deuren
           FROM products p
           LEFT JOIN categories c ON p.categorie_id = c.id
           LEFT JOIN product_doors pd ON p.id = pd.product_id
           WHERE p.actief = 1
           GROUP BY p.id ORDER BY c.volgorde, p.naam"""
    )
    return cats, prods


# ─── Home ────────────────────────────────────────────────────────────────────

@kiosk_bp.route('/')
def home():
    # Controleer of er actieve baravond / aanvulmodus is
    bar_actief  = bool(session.get('active_bar_evening'))
    refill_actief = bool(session.get('active_refill'))
    return render_template('kiosk/home.html',
                           bar_actief=bar_actief, refill_actief=refill_actief)


# ─── Bestelling: naam selecteren ─────────────────────────────────────────────

@kiosk_bp.route('/bestelling/naam')
def bestelling_naam():
    save_order({'regels': [], 'started': True, 'recording_path': '',
                'current_person_id': None, 'current_person_naam': None, 'deuren_nodig': []})
    return render_template('kiosk/order_name.html', personen=alle_personen(), extra=False)


@kiosk_bp.route('/bestelling/naam', methods=['POST'])
def bestelling_naam_post():
    pid = request.form.get('person_id', type=int)
    if not pid:
        return redirect(url_for('kiosk.bestelling_naam'))
    p = query("SELECT * FROM persons WHERE id=? AND actief=1", (pid,), one=True)
    if not p:
        return redirect(url_for('kiosk.bestelling_naam'))

    order = get_order()
    naam = p['bijnaam'] or p['voornaam']

    if not order.get('recording_path'):
        rec = start_recording(f"bestelling_{naam}")
        order['recording_path'] = rec.get_relatief_pad()

    order['current_person_id']   = pid
    order['current_person_naam'] = naam
    save_order(order)
    return redirect(url_for('kiosk.bestelling_producten'))


# ─── Bestelling: extra persoon ────────────────────────────────────────────────

@kiosk_bp.route('/bestelling/extra-persoon')
def bestelling_extra_persoon():
    order = get_order()
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    return render_template('kiosk/order_name.html', personen=alle_personen(), extra=True)


@kiosk_bp.route('/bestelling/extra-persoon', methods=['POST'])
def bestelling_extra_persoon_post():
    pid = request.form.get('person_id', type=int)
    if not pid:
        return redirect(url_for('kiosk.bestelling_producten'))
    p = query("SELECT * FROM persons WHERE id=? AND actief=1", (pid,), one=True)
    if not p:
        return redirect(url_for('kiosk.bestelling_producten'))

    order = get_order()
    order['current_person_id']   = pid
    order['current_person_naam'] = p['bijnaam'] or p['voornaam']
    save_order(order)
    return redirect(url_for('kiosk.bestelling_producten'))


# ─── Bestelling: wissel actieve persoon ──────────────────────────────────────

@kiosk_bp.route('/bestelling/wissel-persoon', methods=['POST'])
def bestelling_wissel_persoon():
    naam = request.form.get('person_naam', '')
    order = get_order()
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    # Zoek persoon_id op via de regels
    for item in order.get('regels', []):
        if item['person_naam'] == naam:
            order['current_person_id']   = item['person_id']
            order['current_person_naam'] = naam
            break
    save_order(order)
    return redirect(url_for('kiosk.bestelling_producten'))


# ─── Bestelling: producten ────────────────────────────────────────────────────

@kiosk_bp.route('/bestelling/producten')
def bestelling_producten():
    order = get_order()
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    cats, prods = alle_producten_per_categorie()
    toon_prijs  = get_setting('prijs_tonen', 'false') == 'true'
    return render_template('kiosk/order_products.html',
                           order=order, categorieen=cats, producten=prods,
                           toon_prijs=toon_prijs)


@kiosk_bp.route('/bestelling/producten', methods=['POST'])
def bestelling_producten_post():
    order = get_order()
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))

    actie = request.form.get('actie')

    if actie == 'toevoegen':
        pid_prod = request.form.get('product_id', type=int)
        hoeveelheid = request.form.get('hoeveelheid', 1, type=int)
        if pid_prod and hoeveelheid > 0:
            prod = query("SELECT * FROM products WHERE id=? AND actief=1", (pid_prod,), one=True)
            if prod:
                order['regels'].append({
                    'person_id':    order['current_person_id'],
                    'person_naam':  order['current_person_naam'],
                    'product_id':   pid_prod,
                    'product_naam': prod['naam'],
                    'hoeveelheid':  hoeveelheid,
                    'prijs':        prod['verkoop_prijs'],
                    'stock':        prod['stock'],
                })
                save_order(order)

    elif actie == 'persoon_toevoegen':
        return redirect(url_for('kiosk.bestelling_extra_persoon'))

    elif actie == 'overzicht':
        return redirect(url_for('kiosk.bestelling_overzicht'))

    return redirect(url_for('kiosk.bestelling_producten'))


# ─── Bestelling: overzicht & bevestigen ──────────────────────────────────────

@kiosk_bp.route('/bestelling/overzicht')
def bestelling_overzicht():
    order = get_order()
    if not order.get('started') or not order.get('regels'):
        return redirect(url_for('kiosk.bestelling_producten'))
    toon_prijs = get_setting('prijs_tonen', 'false') == 'true'
    return render_template('kiosk/order_overview.html', order=order, toon_prijs=toon_prijs)


@kiosk_bp.route('/bestelling/bevestigen', methods=['POST'])
def bestelling_bevestigen():
    order = get_order()
    if not order.get('started') or not order.get('regels'):
        return redirect(url_for('kiosk.home'))

    conn = get_db()
    first_pid = order['regels'][0]['person_id']
    cursor = conn.execute(
        "INSERT INTO orders (type, gestart_door_id, video_path) VALUES ('normaal',?,?)",
        (first_pid, order.get('recording_path', ''))
    )
    order_id = cursor.lastrowid

    deuren = set()
    for item in order['regels']:
        conn.execute(
            """INSERT INTO order_items
               (order_id, person_id, product_id, hoeveelheid, verkoop_prijs_snapshot)
               VALUES (?,?,?,?,?)""",
            (order_id, item['person_id'], item['product_id'],
             item['hoeveelheid'], item['prijs'])
        )
        for row in conn.execute("SELECT deur FROM product_doors WHERE product_id=?", (item['product_id'],)):
            deuren.add(row['deur'])

    conn.commit()
    conn.close()

    for item in order['regels']:
        consume_stock(item['product_id'], item['hoeveelheid'])

    add_log('bestelling', f"Bestelling #{order_id} ({len(order['regels'])} items)", first_pid, order_id, 'bestelling')

    order['order_id']    = order_id
    order['deuren_nodig'] = list(deuren)
    save_order(order)

    timeout = int(get_setting('deur_timeout_sec', '120'))
    fridge  = get_fridge_controller()

    def on_done(deur, opened):
        add_log('deur', f"Deur {deur} {'OK' if opened else 'timeout'}", referentie_id=order_id, referentie_type='order')

    fridge.unlock_doors(list(deuren), timeout_sec=timeout, on_complete=on_done)
    return redirect(url_for('kiosk.bestelling_wachten'))


@kiosk_bp.route('/bestelling/wachten')
def bestelling_wachten():
    order = get_order()
    return render_template('kiosk/order_waiting.html', order=order)


@kiosk_bp.route('/bestelling/annuleren', methods=['POST'])
def bestelling_annuleren():
    stop_recording()
    add_log('bestelling', 'Bestelling geannuleerd')
    session.pop('active_order', None)
    return redirect(url_for('kiosk.home'))


# ─── Stock weergave ───────────────────────────────────────────────────────────

@kiosk_bp.route('/stock')
def stock_view():
    cats, prods = alle_producten_per_categorie()
    return render_template('kiosk/stock_view.html', categorieen=cats, producten=prods)


# ─── Baravond modus ───────────────────────────────────────────────────────────

@kiosk_bp.route('/baravond', methods=['GET', 'POST'])
def baravond():
    personen = alle_personen()
    producten = query("SELECT * FROM products ORDER BY naam")
    actief_id = session.get('active_bar_evening')

    if request.method == 'POST' and request.form.get('actie') == 'kies_naam':
        session['baravond_person_id'] = request.form.get('person_id', type=int)

    session_person_id = session.get('baravond_person_id')
    return render_template('kiosk/bar_evening.html',
                           personen=personen, producten=producten,
                           actief_id=actief_id, session_person_id=session_person_id)


@kiosk_bp.route('/baravond/reset-naam', methods=['POST'])
def baravond_reset_naam():
    session.pop('baravond_person_id', None)
    return redirect(url_for('kiosk.baravond'))


@kiosk_bp.route('/baravond/start', methods=['POST'])
def baravond_start():
    pid = request.form.get('person_id', type=int)
    inv = {k.replace('product_', ''): int(v or 0)
           for k, v in request.form.items() if k.startswith('product_')}

    rec = start_recording('baravond')
    bar_id = execute(
        "INSERT INTO bar_evenings (activator_id, start_inventaris, video_path) VALUES (?,?,?)",
        (pid, json.dumps(inv), rec.get_relatief_pad())
    )
    get_fridge_controller().unlock_all()
    p = query("SELECT voornaam, bijnaam FROM persons WHERE id=?", (pid,), one=True)
    naam = (p['bijnaam'] or p['voornaam']) if p else '?'
    add_log('baravond', f"Baravond gestart door {naam}", pid, bar_id, 'bar_evening')
    session['active_bar_evening'] = bar_id
    return redirect(url_for('kiosk.home'))


@kiosk_bp.route('/baravond/stop', methods=['POST'])
def baravond_stop():
    bar_id = session.get('active_bar_evening') or request.form.get('bar_id', type=int)
    pid    = request.form.get('person_id', type=int)
    eind   = {k.replace('product_', ''): int(v or 0)
              for k, v in request.form.items() if k.startswith('product_')}

    bar = query("SELECT * FROM bar_evenings WHERE id=?", (bar_id,), one=True)
    if bar:
        start_inv = json.loads(bar['start_inventaris'] or '{}')
        verbruik  = {pid_: max(0, start_inv.get(pid_, 0) - eind.get(pid_, 0))
                     for pid_ in start_inv}
        execute(
            """UPDATE bar_evenings SET eind_tijd=CURRENT_TIMESTAMP, eind_inventaris=?,
               verbruik=?, actief=0, deactivator_id=? WHERE id=?""",
            (json.dumps(eind), json.dumps(verbruik), pid, bar_id)
        )

    get_fridge_controller().lock_all()
    stop_recording()
    add_log('baravond', 'Baravond gestopt', pid, bar_id, 'bar_evening')
    session.pop('active_bar_evening', None)
    session.pop('baravond_person_id', None)
    return redirect(url_for('kiosk.home'))


# ─── Aanvul modus ─────────────────────────────────────────────────────────────

@kiosk_bp.route('/aanvullen')
def aanvullen():
    personen = alle_personen()
    producten = query(
        """SELECT p.*, GROUP_CONCAT(pd.deur) as deuren
           FROM products p LEFT JOIN product_doors pd ON p.id=pd.product_id
           WHERE p.actief=1 GROUP BY p.id ORDER BY p.naam"""
    )
    actief_id = session.get('active_refill')
    return render_template('kiosk/refill.html',
                           personen=personen, producten=producten, actief_id=actief_id)


@kiosk_bp.route('/aanvullen/start', methods=['POST'])
def aanvullen_start():
    pid = request.form.get('person_id', type=int)
    rec = start_recording('aanvullen')
    refill_id = execute(
        "INSERT INTO refill_sessions (person_id, video_path) VALUES (?,?)",
        (pid, rec.get_relatief_pad())
    )
    get_fridge_controller().unlock_all()
    add_log('aanvulling', 'Aanvulmodus gestart', pid, refill_id, 'refill')
    session['active_refill'] = refill_id
    return redirect(url_for('kiosk.aanvullen'))


@kiosk_bp.route('/aanvullen/stop', methods=['POST'])
def aanvullen_stop():
    refill_id = session.get('active_refill')
    # Verwerk deur-wijzigingen (JSON body van drag-and-drop)
    wijzigingen = request.get_json(silent=True) or {}

    conn = get_db()
    for prod_id_str, deuren in wijzigingen.items():
        try:
            prod_id = int(prod_id_str)
            conn.execute("DELETE FROM product_doors WHERE product_id=?", (prod_id,))
            for d in deuren:
                conn.execute("INSERT OR IGNORE INTO product_doors (product_id,deur) VALUES (?,?)",
                             (prod_id, int(d)))
        except (ValueError, Exception):
            pass
    conn.commit()
    conn.close()

    if refill_id:
        execute(
            "UPDATE refill_sessions SET eind_tijd=CURRENT_TIMESTAMP, actief=0, deur_wijzigingen=? WHERE id=?",
            (json.dumps(wijzigingen), refill_id)
        )

    get_fridge_controller().lock_all()
    stop_recording()
    add_log('aanvulling', 'Aanvulmodus gestopt', referentie_id=refill_id, referentie_type='refill')
    session.pop('active_refill', None)
    return redirect(url_for('kiosk.home'))


# ─── De Bond ─────────────────────────────────────────────────────────────────

@kiosk_bp.route('/de-bond')
def de_bond():
    bond = query("SELECT * FROM persons WHERE is_bond=1", one=True)
    cats, prods = alle_producten_per_categorie()
    toon_prijs  = get_setting('prijs_tonen', 'false') == 'true'
    return render_template('kiosk/bond.html', bond=bond,
                           categorieen=cats, producten=prods, toon_prijs=toon_prijs)


@kiosk_bp.route('/de-bond/bevestigen', methods=['POST'])
def de_bond_bevestigen():
    bond = query("SELECT * FROM persons WHERE is_bond=1", one=True)
    if not bond:
        return redirect(url_for('kiosk.home'))

    items = []
    for key, val in request.form.items():
        if key.startswith('qty_') and val and int(val) > 0:
            prod_id = int(key.replace('qty_', ''))
            prod = query("SELECT * FROM products WHERE id=? AND actief=1", (prod_id,), one=True)
            if prod:
                items.append({'product_id': prod_id, 'hoeveelheid': int(val),
                              'prijs': prod['verkoop_prijs']})
    if not items:
        return redirect(url_for('kiosk.de_bond'))

    rec = start_recording('de_bond')
    conn = get_db()
    cur  = conn.execute(
        "INSERT INTO orders (type, gestart_door_id, video_path) VALUES ('bond',?,?)",
        (bond['id'], rec.get_relatief_pad())
    )
    order_id = cur.lastrowid
    deuren = set()
    for item in items:
        conn.execute(
            "INSERT INTO order_items (order_id,person_id,product_id,hoeveelheid,verkoop_prijs_snapshot) VALUES (?,?,?,?,?)",
            (order_id, bond['id'], item['product_id'], item['hoeveelheid'], item['prijs'])
        )
        for row in conn.execute("SELECT deur FROM product_doors WHERE product_id=?", (item['product_id'],)):
            deuren.add(row['deur'])
    conn.commit()
    conn.close()

    for item in items:
        consume_stock(item['product_id'], item['hoeveelheid'])

    add_log('bestelling', f"De Bond bestelling #{order_id}", bond['id'], order_id, 'order')
    session['active_order'] = {'order_id': order_id, 'deuren_nodig': list(deuren),
                                'recording_path': rec.get_relatief_pad(), 'is_bond': True, 'items': items}

    timeout = int(get_setting('deur_timeout_sec', '120'))
    get_fridge_controller().unlock_doors(list(deuren), timeout_sec=timeout)
    return redirect(url_for('kiosk.bestelling_wachten'))


# ─── Winkelaankoop ────────────────────────────────────────────────────────────

@kiosk_bp.route('/winkelaankoop')
def winkelaankoop():
    return render_template('kiosk/shop_purchase.html',
                           personen=alle_personen(),
                           producten=query("SELECT * FROM products WHERE actief=1 ORDER BY naam"))


@kiosk_bp.route('/winkelaankoop/bevestigen', methods=['POST'])
def winkelaankoop_bevestigen():
    from services.fifo import add_batch
    pid = request.form.get('person_id', type=int)
    aankoop_id = execute("INSERT INTO shop_purchases (person_id) VALUES (?)", (pid,))

    n = 0
    for key, val in request.form.items():
        if key.startswith('qty_') and val and int(val) > 0:
            prod_id = int(key.replace('qty_', ''))
            qty   = int(val)
            prijs = float(request.form.get(f'prijs_{prod_id}', 0) or 0)
            execute(
                "INSERT INTO shop_purchase_items (aankoop_id,product_id,hoeveelheid,aankoop_prijs_per_stuk) VALUES (?,?,?,?)",
                (aankoop_id, prod_id, qty, prijs)
            )
            add_batch(prod_id, qty, prijs, aankoop_id)
            n += 1

    add_log('stock', f"Winkelaankoop: {n} producten", pid, aankoop_id, 'shop_purchase')
    return redirect(url_for('kiosk.home'))


# ─── Nieuw persoon ────────────────────────────────────────────────────────────

@kiosk_bp.route('/persoon/nieuw', methods=['GET', 'POST'])
def persoon_nieuw():
    if request.method == 'POST':
        voornaam = request.form.get('voornaam', '').strip()
        if not voornaam:
            return render_template('kiosk/new_person.html', fout="Voornaam is verplicht")

        foto_path = ''
        foto = request.files.get('foto')
        if foto and foto.filename:
            ext = foto.filename.rsplit('.', 1)[-1].lower()
            if ext in ('jpg', 'jpeg', 'png', 'webp'):
                naam = f"{uuid.uuid4().hex}.{ext}"
                foto.save(os.path.join(UPLOADS_PERSONS_DIR, naam))
                foto_path = f"persons/{naam}"

        pid = execute(
            "INSERT INTO persons (voornaam, achternaam, bijnaam, foto_path) VALUES (?,?,?,?)",
            (voornaam, request.form.get('achternaam', '').strip(),
             request.form.get('bijnaam', '').strip(), foto_path)
        )
        add_log('systeem', f"Nieuw persoon: {voornaam}", pid)
        return redirect(url_for('kiosk.bestelling_naam'))

    return render_template('kiosk/new_person.html')
