"""API routes voor AJAX/fetch calls vanuit de kiosk."""
from flask import Blueprint, jsonify, request, session
from database.db import query, execute, get_setting
from hardware.gpio_controller import get_fridge_controller
from hardware.camera import stop_recording

api_bp = Blueprint('api', __name__)


@api_bp.route('/deur-status')
def deur_status():
    """Polling endpoint: status alle deuren + of bestelling klaar is."""
    fridge = get_fridge_controller()
    status = fridge.get_status()

    order = session.get('active_order', {})
    deuren_nodig = set(order.get('deuren_nodig', []))

    # Klaar = alle benodigde deuren zijn terug vergrendeld
    alle_klaar = bool(deuren_nodig) and all(
        not status.get(d, {}).get('unlocked', False)
        for d in deuren_nodig
    )

    if alle_klaar:
        stop_recording()
        session.pop('active_order', None)

    return jsonify({'deuren': {str(k): v for k, v in status.items()},
                    'alle_klaar': alle_klaar})


@api_bp.route('/hardware-test/deur/<int:deur>/unlock', methods=['POST'])
def hw_unlock(deur):
    fridge = get_fridge_controller()
    if deur in fridge.doors:
        fridge.doors[deur].unlock()
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400


@api_bp.route('/hardware-test/deur/<int:deur>/lock', methods=['POST'])
def hw_lock(deur):
    fridge = get_fridge_controller()
    if deur in fridge.doors:
        fridge.doors[deur].lock()
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400


@api_bp.route('/hardware-test/deur/<int:deur>/simulate-open', methods=['POST'])
def hw_sim_open(deur):
    fridge = get_fridge_controller()
    if deur in fridge.doors:
        fridge.doors[deur].simulate_open()
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400


@api_bp.route('/hardware-test/deur/<int:deur>/simulate-close', methods=['POST'])
def hw_sim_close(deur):
    fridge = get_fridge_controller()
    if deur in fridge.doors:
        fridge.doors[deur].simulate_close()
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400


@api_bp.route('/personen/zoeken')
def personen_zoeken():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    rows = query(
        """SELECT id, voornaam, achternaam, bijnaam, foto_path
           FROM persons WHERE actief=1 AND is_bond=0
           AND (voornaam LIKE ? OR achternaam LIKE ? OR bijnaam LIKE ?)
           ORDER BY voornaam LIMIT 10""",
        (f'%{q}%', f'%{q}%', f'%{q}%')
    )
    return jsonify([dict(r) for r in rows])


@api_bp.route('/bestelling/item-verwijderen', methods=['POST'])
def item_verwijderen():
    idx = (request.get_json(silent=True) or {}).get('index', -1)
    order = session.get('active_order', {})
    items = order.get('regels', [])
    if 0 <= idx < len(items):
        items.pop(idx)
        order['regels'] = items
        session['active_order'] = order
        session.modified = True
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400
