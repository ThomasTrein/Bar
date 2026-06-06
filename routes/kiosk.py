"""Kiosk routes voor KSA Bar."""
import os, json, uuid, threading
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.db import get_db, query, execute, executemany, add_log, get_setting
from hardware.gpio_controller import get_fridge_controller
from hardware.camera import start_recording, stop_recording
from services.fifo import consume_stock, restore_stock, reconcile_stock
from config import UPLOADS_PERSONS_DIR

kiosk_bp = Blueprint('kiosk', __name__)


# ─── Helpers ────────────────────────────────────────────────────────────────

def get_order(token=''):
    return session.get('orders', {}).get(token, {'regels': [], 'started': False,
                                                   'recording_path': '', 'current_person_id': None,
                                                   'current_person_naam': None, 'deuren_nodig': []})

def save_order(o, token=''):
    if 'orders' not in session:
        session['orders'] = {}
    session['orders'][token] = o
    session.modified = True

def alle_personen():
    return query(
        """SELECT id, voornaam, achternaam, bijnaam, foto_path
           FROM persons WHERE actief = 1 AND is_bond = 0
           ORDER BY LOWER(COALESCE(NULLIF(bijnaam,''), voornaam))"""
    )

def persoon_foto_tonen():
    return get_setting('persoon_foto_tonen', 'false') == 'true'

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
    ot = request.args.get('ot', '')
    order = get_order(ot)
    if not ot or not order.get('started'):
        ot = uuid.uuid4().hex
        save_order({'regels': [], 'started': True, 'recording_path': '',
                    'current_person_id': None, 'current_person_naam': None, 'deuren_nodig': []}, ot)
    persoon_kolommen = int(get_setting('persoon_kolommen', '4'))
    return render_template('kiosk/order_name.html', personen=alle_personen(), extra=False,
                           ot=ot, persoon_kolommen=persoon_kolommen, toon_foto=persoon_foto_tonen())


@kiosk_bp.route('/bestelling/naam', methods=['POST'])
def bestelling_naam_post():
    ot = request.form.get('ot', '')
    pid = request.form.get('person_id', type=int)
    if not pid:
        return redirect(url_for('kiosk.bestelling_naam'))
    p = query("SELECT * FROM persons WHERE id=? AND actief=1", (pid,), one=True)
    if not p:
        return redirect(url_for('kiosk.bestelling_naam', ot=ot))

    order = get_order(ot)
    naam = p['bijnaam'] or p['voornaam']

    if not order.get('recording_path'):
        rec = start_recording(f"bestelling_{naam}")
        order['recording_path'] = rec.get_relatief_pad()

    order['current_person_id']   = pid
    order['current_person_naam'] = naam
    save_order(order, ot)
    return redirect(url_for('kiosk.bestelling_producten', ot=ot))


# ─── Bestelling: extra persoon ────────────────────────────────────────────────

@kiosk_bp.route('/bestelling/extra-persoon')
def bestelling_extra_persoon():
    ot = request.args.get('ot', '')
    order = get_order(ot)
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    persoon_kolommen = int(get_setting('persoon_kolommen', '4'))
    return render_template('kiosk/order_name.html', personen=alle_personen(), extra=True,
                           ot=ot, persoon_kolommen=persoon_kolommen, toon_foto=persoon_foto_tonen())


@kiosk_bp.route('/bestelling/extra-persoon', methods=['POST'])
def bestelling_extra_persoon_post():
    ot = request.form.get('ot', '')
    pid = request.form.get('person_id', type=int)
    if not pid:
        return redirect(url_for('kiosk.bestelling_producten', ot=ot))
    p = query("SELECT * FROM persons WHERE id=? AND actief=1", (pid,), one=True)
    if not p:
        return redirect(url_for('kiosk.bestelling_producten', ot=ot))

    order = get_order(ot)
    order['current_person_id']   = pid
    order['current_person_naam'] = p['bijnaam'] or p['voornaam']
    save_order(order, ot)
    return redirect(url_for('kiosk.bestelling_producten', ot=ot))



# ─── Bestelling: wissel actieve persoon ──────────────────────────────────────

@kiosk_bp.route('/bestelling/wissel-persoon', methods=['POST'])
def bestelling_wissel_persoon():
    ot = request.form.get('ot', '')
    naam = request.form.get('person_naam', '')
    order = get_order(ot)
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    # Zoek persoon_id op via de regels
    for item in order.get('regels', []):
        if item['person_naam'] == naam:
            order['current_person_id']   = item['person_id']
            order['current_person_naam'] = naam
            break
    save_order(order, ot)
    return redirect(url_for('kiosk.bestelling_producten', ot=ot))


# ─── Bestelling: producten ────────────────────────────────────────────────────

@kiosk_bp.route('/bestelling/producten')
def bestelling_producten():
    ot = request.args.get('ot', '')
    order = get_order(ot)
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    cats, prods = alle_producten_per_categorie()
    toon_prijs  = get_setting('prijs_tonen', 'false') == 'true'

    # Beperkingen voor huidige persoon ophalen
    pid = order.get('current_person_id')
    blocked_prod_ids = set()
    blocked_cat_ids  = set()
    if pid:
        blocked_prod_ids = {r['product_id'] for r in
            query("SELECT product_id FROM person_blocked_products WHERE person_id=?", (pid,))}
        blocked_cat_ids = {r['category_id'] for r in
            query("SELECT category_id FROM person_blocked_categories WHERE person_id=?", (pid,))}

    # Producten zonder deur-koppeling zijn niet bestelbaar
    unlinked_prod_ids = {r['id'] for r in
        query("""SELECT p.id FROM products p
                 WHERE p.actief=1
                 AND NOT EXISTS (SELECT 1 FROM product_doors pd WHERE pd.product_id=p.id)""")}
    blocked_prod_ids |= unlinked_prod_ids

    product_kolommen = int(get_setting('product_kolommen', '2'))
    return render_template('kiosk/order_products.html',
                           order=order, categorieen=cats, producten=prods,
                           toon_prijs=toon_prijs,
                           blocked_prod_ids=blocked_prod_ids,
                           blocked_cat_ids=blocked_cat_ids,
                           product_kolommen=product_kolommen,
                           ot=ot)


@kiosk_bp.route('/bestelling/producten', methods=['POST'])
def bestelling_producten_post():
    ot = request.form.get('ot', '')
    order = get_order(ot)
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
                save_order(order, ot)

    elif actie == 'persoon_toevoegen':
        return redirect(url_for('kiosk.bestelling_extra_persoon', ot=ot))

    elif actie == 'overzicht':
        return redirect(url_for('kiosk.bestelling_overzicht', ot=ot))

    return redirect(url_for('kiosk.bestelling_producten', ot=ot))


@kiosk_bp.route('/bestelling/bak-toevoegen', methods=['POST'])
def bestelling_bak_toevoegen():
    ot = request.form.get('ot', '')
    order = get_order(ot)
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    prod_id = request.form.get('product_id', type=int)
    if prod_id:
        prod = query("SELECT * FROM products WHERE id=? AND actief=1", (prod_id,), one=True)
        if prod and prod['bak_grootte']:
            order['regels'].append({
                'person_id':    order['current_person_id'],
                'person_naam':  order['current_person_naam'],
                'product_id':   prod_id,
                'product_naam': prod['naam'],
                'hoeveelheid':  prod['bak_grootte'],
                'prijs':        prod['verkoop_prijs'],
                'stock':        prod['stock'],
            })
            save_order(order, ot)
    return redirect(url_for('kiosk.bestelling_producten', ot=ot))


# ─── Bestelling: overzicht & bevestigen ──────────────────────────────────────

@kiosk_bp.route('/bestelling/overzicht')
def bestelling_overzicht():
    ot = request.args.get('ot', '')
    order = get_order(ot)
    if not order.get('started') or not order.get('regels'):
        return redirect(url_for('kiosk.bestelling_producten', ot=ot))
    toon_prijs = get_setting('prijs_tonen', 'false') == 'true'

    # Groepeer regels per persoon (volgorde eerste verschijning) en per product
    personen_volgorde = []
    persoon_items = {}
    for item in order['regels']:
        pid = item['person_id']
        if pid not in persoon_items:
            personen_volgorde.append(pid)
            persoon_items[pid] = {'naam': item['person_naam'], 'producten': {}}
        prod_key = (item['product_id'], item['prijs'])
        if prod_key not in persoon_items[pid]['producten']:
            persoon_items[pid]['producten'][prod_key] = dict(item)
        else:
            persoon_items[pid]['producten'][prod_key]['hoeveelheid'] += item['hoeveelheid']

    gegroepeerde_regels = []
    for pid in personen_volgorde:
        for regel in persoon_items[pid]['producten'].values():
            gegroepeerde_regels.append(regel)

    gegroepeerde_order = dict(order)
    gegroepeerde_order['regels'] = gegroepeerde_regels

    return render_template('kiosk/order_overview.html',
                           order=gegroepeerde_order, toon_prijs=toon_prijs, ot=ot)


@kiosk_bp.route('/bestelling/bevestigen', methods=['POST'])
def bestelling_bevestigen():
    ot = request.form.get('ot', '')
    order = get_order(ot)
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
    product_door_map = {}   # product_id → set van deuren
    for item in order['regels']:
        conn.execute(
            """INSERT INTO order_items
               (order_id, person_id, product_id, hoeveelheid, verkoop_prijs_snapshot)
               VALUES (?,?,?,?,?)""",
            (order_id, item['person_id'], item['product_id'],
             item['hoeveelheid'], item['prijs'])
        )
        pid = item['product_id']
        if pid not in product_door_map:
            product_door_map[pid] = set()
        for row in conn.execute("SELECT deur FROM product_doors WHERE product_id=?", (pid,)):
            deuren.add(row['deur'])
            product_door_map[pid].add(row['deur'])

    conn.commit()
    conn.close()

    for item in order['regels']:
        consume_stock(item['product_id'], item['hoeveelheid'])

    add_log('bestelling', f"Bestelling geplaatst: #{order_id} ({len(order['regels'])} items)", first_pid, order_id, 'bestelling')

    order['order_id']    = order_id
    order['deuren_nodig'] = list(deuren)
    save_order(order, ot)

    timeout = int(get_setting('deur_timeout_sec', '120'))
    fridge  = get_fridge_controller()

    groups = [s for s in product_door_map.values() if s]
    total_groups = len(groups)
    done_results = []   # True = deur geopend, False = timeout
    done_lock = threading.Lock()
    order_items_snapshot = [(item['product_id'], item['hoeveelheid']) for item in order['regels']]

    def on_done(deur, opened):
        with done_lock:
            done_results.append(opened)
            if opened:
                add_log('deur', f"Deur {deur} geopend", referentie_id=order_id, referentie_type='order')
                add_log('deur', f"Deur {deur} gesloten", referentie_id=order_id, referentie_type='order')
            else:
                add_log('deur', f"Deur {deur} timeout — nooit geopend", referentie_id=order_id, referentie_type='order')

            if len(done_results) == total_groups and not any(done_results):
                # Alle deuren hebben timeout gehad: bestelling annuleren
                execute("UPDATE orders SET geannuleerd=1, deur_niet_geopend=1 WHERE id=?", (order_id,))
                for prod_id, hoeveelheid in order_items_snapshot:
                    restore_stock(prod_id, hoeveelheid)
                add_log('bestelling',
                        f"Bestelling #{order_id} geannuleerd: deuren nooit geopend — bedrag NIET aangerekend",
                        referentie_id=order_id, referentie_type='bestelling')

    fridge.unlock_door_groups(groups, timeout_sec=timeout, on_complete=on_done)
    return redirect(url_for('kiosk.bestelling_wachten', ot=ot))


@kiosk_bp.route('/bestelling/wachten')
def bestelling_wachten():
    ot = request.args.get('ot', '')
    order = get_order(ot)
    if not order.get('started'):
        return redirect(url_for('kiosk.home'))
    return render_template('kiosk/order_waiting.html', order=order, ot=ot)


@kiosk_bp.route('/bestelling/annuleren', methods=['POST'])
def bestelling_annuleren():
    ot = request.form.get('ot', '')
    stop_recording()
    order = get_order(ot)
    oid = order.get('order_id')
    beschrijving = f"Bestelling geannuleerd: #{oid}" if oid else "Bestelling geannuleerd"
    add_log('bestelling', beschrijving, referentie_id=oid, referentie_type='bestelling' if oid else None)
    orders = session.get('orders', {})
    orders.pop(ot, None)
    session['orders'] = orders
    session.modified = True
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

    if request.method == 'GET':
        # Always reset naam selection on fresh page visit
        session.pop('baravond_person_id', None)
        session.pop('baravond_stop_person_id', None)
    elif request.method == 'POST' and request.form.get('actie') == 'kies_naam':
        # Check if another mode is active before saving naam
        if session.get('active_refill'):
            flash('Aanvulmodus is actief. Stop eerst de aanvulmodus voor je baravond start.', 'error')
            return redirect(url_for('kiosk.home'))
        pid = request.form.get('person_id', type=int)
        session['baravond_person_id'] = pid
        # Start opname zodra naam geselecteerd is
        if not session.get('baravond_recording_path'):
            p = query("SELECT voornaam, bijnaam FROM persons WHERE id=?", (pid,), one=True)
            naam = (p['bijnaam'] or p['voornaam']) if p else 'baravond'
            rec = start_recording(f"baravond_{naam}")
            session['baravond_recording_path'] = rec.get_relatief_pad()
            session.modified = True
    elif request.method == 'POST' and request.form.get('actie') == 'kies_stop_naam':
        session['baravond_stop_person_id'] = request.form.get('person_id', type=int)

    session_person_id = session.get('baravond_person_id')
    stop_person_id = session.get('baravond_stop_person_id')
    persoon_kolommen = int(get_setting('persoon_kolommen', '4'))
    inv_kolommen = int(get_setting('inv_kolommen', '3'))
    cats = query("SELECT * FROM categories ORDER BY volgorde")
    return render_template('kiosk/bar_evening.html',
                           personen=personen, producten=producten,
                           categorieen=cats,
                           actief_id=actief_id, session_person_id=session_person_id,
                           stop_person_id=stop_person_id,
                           persoon_kolommen=persoon_kolommen,
                           toon_foto=persoon_foto_tonen(),
                           inv_kolommen=inv_kolommen)


@kiosk_bp.route('/baravond/reset-naam', methods=['POST'])
def baravond_reset_naam():
    # Stop opname als die al gestart was
    if session.get('baravond_recording_path'):
        stop_recording()
        session.pop('baravond_recording_path', None)
    session.pop('baravond_person_id', None)
    return redirect(url_for('kiosk.baravond'))


@kiosk_bp.route('/baravond/reset-stop-naam', methods=['POST'])
def baravond_reset_stop_naam():
    session.pop('baravond_stop_person_id', None)
    return redirect(url_for('kiosk.baravond'))


@kiosk_bp.route('/baravond/start', methods=['POST'])
def baravond_start():
    if session.get('active_refill'):
        flash('Aanvulmodus is actief. Stop eerst de aanvulmodus voor je baravond start.', 'error')
        return redirect(url_for('kiosk.baravond'))
    pid = request.form.get('person_id', type=int)
    naam = request.form.get('naam', '').strip()
    inv = {k.replace('product_', ''): int(v or 0)
           for k, v in request.form.items() if k.startswith('product_')}

    # Reconcilieer FIFO voor elk product op basis van de getelde inventaris
    for prod_id_str, counted in inv.items():
        try:
            reconcile_stock(int(prod_id_str), counted)
        except Exception:
            pass

    # Gebruik bestaande opname als die al bij naam selectie gestart was, anders start nieuw
    bestaand_pad = session.pop('baravond_recording_path', None)
    if bestaand_pad:
        rec_pad = bestaand_pad
    else:
        rec = start_recording('baravond')
        rec_pad = rec.get_relatief_pad()
    bar_id = execute(
        "INSERT INTO bar_evenings (activator_id, start_inventaris, video_path, naam) VALUES (?,?,?,?)",
        (pid, json.dumps(inv), rec_pad, naam)
    )

    # Sla prijzen op als snapshot zodat latere prijswijzigingen niet de baravond beïnvloeden
    from services.fifo import get_fifo_cost_per_unit
    for prod_id_str in inv:
        try:
            prod_id = int(prod_id_str)
            prod = query("SELECT verkoop_prijs FROM products WHERE id=?", (prod_id,), one=True)
            if prod:
                aankoop = get_fifo_cost_per_unit(prod_id)
                execute(
                    """INSERT OR REPLACE INTO bar_evening_prices
                       (bar_evening_id, product_id, verkoop_prijs, aankoop_prijs)
                       VALUES (?,?,?,?)""",
                    (bar_id, prod_id, prod['verkoop_prijs'] or 0, aankoop)
                )
        except Exception:
            pass

    get_fridge_controller().unlock_all()
    add_log('baravond', "Baravond gestart", pid, bar_id, 'bar_evening')
    session['active_bar_evening'] = bar_id
    return redirect(url_for('kiosk.home'))


@kiosk_bp.route('/baravond/stop', methods=['POST'])
def baravond_stop():
    bar_id = session.get('active_bar_evening') or request.form.get('bar_id', type=int)
    pid    = session.get('baravond_stop_person_id') or request.form.get('person_id', type=int)
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

    # Reconcilieer FIFO voor elk product op basis van de eind-inventaris
    for prod_id_str, counted in eind.items():
        try:
            reconcile_stock(int(prod_id_str), counted)
        except Exception:
            pass

    get_fridge_controller().lock_all()
    stop_recording()
    add_log('baravond', "Baravond gestopt", pid, bar_id, 'bar_evening')
    session.pop('active_bar_evening', None)
    session.pop('baravond_person_id', None)
    session.pop('baravond_stop_person_id', None)
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
    persoon_kolommen = int(get_setting('persoon_kolommen', '4'))

    # Load current fridge layout (multi-product per slot)
    layout = {}  # {"d-v": [product_id, ...]}
    if actief_id:
        layout_rows = query("SELECT deur, vak, product_id, product_ids FROM fridge_layout")
        for r in layout_rows:
            key = f"{r['deur']}-{r['vak']}"
            if r['product_ids']:
                try:
                    ids = json.loads(r['product_ids'])
                    layout[key] = ids if isinstance(ids, list) else [ids]
                except (ValueError, TypeError):
                    layout[key] = [r['product_id']] if r['product_id'] else []
            elif r['product_id']:
                layout[key] = [r['product_id']]
    product_names = {p['id']: p['naam'] for p in producten}

    return render_template('kiosk/refill.html',
                           personen=personen, producten=producten, actief_id=actief_id,
                           persoon_kolommen=persoon_kolommen, toon_foto=persoon_foto_tonen(),
                           layout=layout, product_names=product_names)


@kiosk_bp.route('/aanvullen/start', methods=['POST'])
def aanvullen_start():
    if session.get('active_bar_evening'):
        flash('Baravond is actief. Stop eerst de baravond voor je aanvulmodus start.', 'error')
        return redirect(url_for('kiosk.home'))
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


@kiosk_bp.route('/aanvullen/stop-naam', methods=['POST'])
def aanvullen_stop_naam():
    door_data = request.form.get('door_data', '{}')
    layout_data = request.form.get('layout_data', '{}')
    personen = alle_personen()
    persoon_kolommen = int(get_setting('persoon_kolommen', '4'))
    return render_template('kiosk/refill_stop_naam.html',
                           personen=personen, door_data=door_data,
                           layout_data=layout_data,
                           persoon_kolommen=persoon_kolommen,
                           toon_foto=persoon_foto_tonen())


@kiosk_bp.route('/aanvullen/stop', methods=['POST'])
def aanvullen_stop():
    refill_id = session.get('active_refill')

    # Parse door_data and layout_data from form
    door_data_str = request.form.get('door_data', '{}')
    layout_data_str = request.form.get('layout_data', '{}')
    try:
        wijzigingen = json.loads(door_data_str)
    except (ValueError, TypeError):
        wijzigingen = {}
    try:
        layout_data = json.loads(layout_data_str)
    except (ValueError, TypeError):
        layout_data = {}
    stopper_id = request.form.get('person_id', type=int)

    conn = get_db()

    # Update fridge_layout from layout_data ("d-v": [product_id, ...])
    if layout_data:
        conn.execute("DELETE FROM fridge_layout")
        for slot_key, prod_ids in layout_data.items():
            try:
                parts = slot_key.split('-')
                d, v = int(parts[0]), int(parts[1])
                if isinstance(prod_ids, list):
                    ids = [int(x) for x in prod_ids if x]
                else:
                    ids = [int(prod_ids)] if prod_ids else []
                if ids:
                    conn.execute(
                        "INSERT OR REPLACE INTO fridge_layout (deur, vak, product_id, product_ids) VALUES (?,?,?,?)",
                        (d, v, ids[0], json.dumps(ids))
                    )
            except (ValueError, IndexError, Exception):
                pass

    # Rebuild product_doors directly from fridge_layout (more reliable than door_data via HTML)
    conn.execute("DELETE FROM product_doors")
    for row in conn.execute("SELECT deur, product_ids, product_id FROM fridge_layout"):
        try:
            pids = json.loads(row['product_ids']) if row['product_ids'] else [row['product_id']]
        except Exception:
            pids = [row['product_id']] if row['product_id'] else []
        for pid in pids:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO product_doors (product_id, deur) VALUES (?,?)",
                    (int(pid), int(row['deur']))
                )
            except Exception:
                pass

    conn.commit()
    conn.close()

    if refill_id:
        execute(
            "UPDATE refill_sessions SET eind_tijd=CURRENT_TIMESTAMP, actief=0, deur_wijzigingen=? WHERE id=?",
            (json.dumps(wijzigingen), refill_id)
        )

    # Bepaal wie gestopt heeft
    if not stopper_id and refill_id:
        rs = query("SELECT person_id FROM refill_sessions WHERE id=?", (refill_id,), one=True)
        if rs and rs['person_id']:
            stopper_id = rs['person_id']

    get_fridge_controller().lock_all()
    stop_recording()
    add_log('aanvulling', "Aanvulmodus gestopt", stopper_id, refill_id, 'refill')
    session.pop('active_refill', None)
    return redirect(url_for('kiosk.home'))


# ─── De Bond ─────────────────────────────────────────────────────────────────

@kiosk_bp.route('/de-bond')
def de_bond():
    # Reset bond sessie zodat opname pas bij naam selectie start
    session.pop('bond_session', None)
    session.modified = True
    return redirect(url_for('kiosk.de_bond_naam'))


@kiosk_bp.route('/de-bond/naam')
def de_bond_naam():
    personen = alle_personen()
    persoon_kolommen = int(get_setting('persoon_kolommen', '4'))
    return render_template('kiosk/bond_naam.html', personen=personen,
                           persoon_kolommen=persoon_kolommen, toon_foto=persoon_foto_tonen())


@kiosk_bp.route('/de-bond/naam', methods=['POST'])
def de_bond_naam_post():
    pid = request.form.get('person_id', type=int)
    if not pid:
        return redirect(url_for('kiosk.de_bond_naam'))
    p = query("SELECT * FROM persons WHERE id=? AND actief=1", (pid,), one=True)
    if not p:
        return redirect(url_for('kiosk.de_bond_naam'))
    naam = p['bijnaam'] or p['voornaam']
    rec = start_recording(f"de_bond_{naam}")
    session['bond_session'] = {
        'recording_path': rec.get_relatief_pad(),
        'person_id':   pid,
        'person_naam': naam,
    }
    session.modified = True
    return redirect(url_for('kiosk.de_bond_producten'))


@kiosk_bp.route('/de-bond/producten')
def de_bond_producten():
    bond_sess = session.get('bond_session', {})
    if not bond_sess.get('person_id'):
        return redirect(url_for('kiosk.de_bond_naam'))
    cats, prods = alle_producten_per_categorie()
    inv_kolommen = int(get_setting('inv_kolommen', '3'))
    return render_template('kiosk/bond.html', categorieen=cats, producten=prods,
                           person_naam=bond_sess['person_naam'],
                           inv_kolommen=inv_kolommen)


@kiosk_bp.route('/de-bond/bevestigen', methods=['POST'])
def de_bond_bevestigen():
    bond = query("SELECT * FROM persons WHERE is_bond=1", one=True)
    if not bond:
        return redirect(url_for('kiosk.home'))

    bond_sess = session.get('bond_session', {})
    actor_id   = bond_sess.get('person_id')
    actor_naam = bond_sess.get('person_naam', '?')
    rec_pad    = bond_sess.get('recording_path', '')

    items = []
    for key, val in request.form.items():
        if key.startswith('qty_') and val and int(val) > 0:
            prod_id = int(key.replace('qty_', ''))
            prod = query("SELECT * FROM products WHERE id=? AND actief=1", (prod_id,), one=True)
            if prod:
                items.append({'product_id': prod_id, 'hoeveelheid': int(val),
                              'prijs': prod['verkoop_prijs']})
    if not items:
        return redirect(url_for('kiosk.de_bond_producten'))

    conn = get_db()
    cur  = conn.execute(
        "INSERT INTO orders (type, gestart_door_id, video_path) VALUES ('bond',?,?)",
        (actor_id or bond['id'], rec_pad)
    )
    order_id = cur.lastrowid
    deuren = set()
    product_door_map = {}   # product_id → set van deuren
    for item in items:
        conn.execute(
            "INSERT INTO order_items (order_id,person_id,product_id,hoeveelheid,verkoop_prijs_snapshot) VALUES (?,?,?,?,?)",
            (order_id, bond['id'], item['product_id'], item['hoeveelheid'], item['prijs'])
        )
        pid = item['product_id']
        if pid not in product_door_map:
            product_door_map[pid] = set()
        for row in conn.execute("SELECT deur FROM product_doors WHERE product_id=?", (pid,)):
            deuren.add(row['deur'])
            product_door_map[pid].add(row['deur'])
    conn.commit()
    conn.close()

    for item in items:
        consume_stock(item['product_id'], item['hoeveelheid'])

    add_log('bestelling', f"De Bond bestelling #{order_id}",
            actor_id or bond['id'], order_id, 'order')
    session['bond_session'] = {}

    # Use token system so bestelling_wachten works correctly
    ot = uuid.uuid4().hex
    save_order({'started': True, 'order_id': order_id, 'deuren_nodig': list(deuren),
                'recording_path': rec_pad, 'is_bond': True, 'regels': items,
                'current_person_id': actor_id, 'current_person_naam': actor_naam}, ot)

    timeout = int(get_setting('deur_timeout_sec', '120'))
    groups = [s for s in product_door_map.values() if s]
    get_fridge_controller().unlock_door_groups(groups, timeout_sec=timeout)
    return redirect(url_for('kiosk.bestelling_wachten', ot=ot))




# ─── De Bond - terugzetten ────────────────────────────────────────────────────

@kiosk_bp.route('/de-bond/terugzetten', methods=['GET'])
def de_bond_terugzetten():
    producten = query("SELECT * FROM products WHERE actief=1 ORDER BY naam")
    categorieen = query("SELECT * FROM categories ORDER BY naam")
    inv_kolommen = int(get_setting('inv_kolommen', '3'))
    return render_template('kiosk/bond_return.html', producten=producten,
                           categorieen=categorieen, inv_kolommen=inv_kolommen)


@kiosk_bp.route('/de-bond/terugzetten', methods=['POST'])
def de_bond_terugzetten_post():
    from services.fifo import return_to_oldest_fifo
    teruggezet = 0
    for key, val in request.form.items():
        if key.startswith('qty_') and val and int(val) > 0:
            prod_id = int(key.replace('qty_', ''))
            qty = int(val)
            return_to_oldest_fifo(prod_id, qty)
            teruggezet += qty
    if teruggezet:
        add_log('stock', f"De Bond: {teruggezet} items teruggezet naar stock", 1)
    return redirect(url_for('kiosk.home'))


# ─── Bak bier bestellen (verouderd - enkel via bestelling/bak-toevoegen) ──────

@kiosk_bp.route('/bak-bestellen')
def bak_bestellen():
    return redirect(url_for('kiosk.home'))


@kiosk_bp.route('/bak-bestellen/bevestigen', methods=['POST'])
def bak_bestellen_bevestigen():
    return redirect(url_for('kiosk.home'))


# ─── Winkelaankoop ────────────────────────────────────────────────────────────

@kiosk_bp.route('/winkelaankoop')
def winkelaankoop():
    """Stap 1: persoon selecteren."""
    persoon_kolommen = int(get_setting('persoon_kolommen', '4'))
    return render_template('kiosk/shop_purchase_person.html', personen=alle_personen(),
                           persoon_kolommen=persoon_kolommen, toon_foto=persoon_foto_tonen())


@kiosk_bp.route('/winkelaankoop/<int:pid>')
def winkelaankoop_producten(pid):
    """Stap 2: producten invullen voor geselecteerde persoon."""
    persoon = query("SELECT * FROM persons WHERE id=? AND actief=1", (pid,), one=True)
    if not persoon:
        return redirect(url_for('kiosk.winkelaankoop'))
    producten = query("SELECT * FROM products ORDER BY actief DESC, naam")
    cats = query("SELECT * FROM categories ORDER BY volgorde")
    inv_kolommen = int(get_setting('inv_kolommen', '3'))
    return render_template('kiosk/shop_purchase.html', persoon=persoon, producten=producten,
                           categorieen=cats, inv_kolommen=inv_kolommen)


@kiosk_bp.route('/winkelaankoop/bevestigen', methods=['POST'])
def winkelaankoop_bevestigen():
    from services.fifo import add_batch
    pid = request.form.get('person_id', type=int)
    if not pid:
        return redirect(url_for('kiosk.winkelaankoop'))
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
    next_url = request.args.get('next', 'bestelling_naam')
    ot = request.args.get('ot', '')
    if request.method == 'POST':
        voornaam = request.form.get('voornaam', '').strip()
        next_url = request.form.get('next', 'bestelling_naam')
        ot = request.form.get('ot', '')
        if not voornaam:
            return render_template('kiosk/new_person.html',
                                   fout="Voornaam is verplicht", next=next_url, ot=ot)

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
        # Auto-block globally locked products for new person
        locked_prods = query("SELECT id FROM products WHERE globally_locked=1")
        if locked_prods:
            executemany(
                "INSERT OR IGNORE INTO person_blocked_products (person_id, product_id) VALUES (?,?)",
                [(pid, p['id']) for p in locked_prods]
            )
        add_log('systeem', f"Nieuw persoon: {voornaam}", pid)
        if next_url == 'home':
            return redirect(url_for('kiosk.home'))
        if ot:
            return redirect(url_for('kiosk.bestelling_naam', ot=ot))
        return redirect(url_for('kiosk.bestelling_naam'))

    return render_template('kiosk/new_person.html', next=next_url, ot=ot)
