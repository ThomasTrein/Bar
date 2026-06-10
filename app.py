"""
KSA Bar Systeem — Flask hoofdapplicatie.
Start met: python app.py
"""
import os
import secrets
from datetime import datetime, timezone
from flask import Flask, send_from_directory

try:
    from zoneinfo import ZoneInfo
    _BRUSSELS = ZoneInfo('Europe/Brussels')
except (ImportError, KeyError):
    _BRUSSELS = None

from config import BASE_DIR, VIDEOS_DIR, BACKUPS_DIR, UPLOADS_DIR, UPLOADS_PERSONS_DIR, UPLOADS_PRODUCTS_DIR, UPLOADS_SCREENSAVER_DIR
from database.schema import init_db
from database.db import add_log


def create_app():
    app = Flask(__name__)

    # Gebruik een vaste secret_key die bewaard wordt in de database,
    # zodat sessies geldig blijven na een herstart van de app.
    from database.db import get_setting, set_setting
    sk = get_setting('_flask_secret_key')
    if not sk:
        sk = secrets.token_hex(32)
        set_setting('_flask_secret_key', sk)
    app.secret_key = sk
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

    # Mappen
    for d in [VIDEOS_DIR, BACKUPS_DIR, UPLOADS_DIR, UPLOADS_PERSONS_DIR, UPLOADS_PRODUCTS_DIR, UPLOADS_SCREENSAVER_DIR]:
        os.makedirs(d, exist_ok=True)

    # Database
    init_db()

    # Context processor: inject screensaver_foto into every template
    @app.context_processor
    def inject_globals():
        from database.db import get_setting
        return {'screensaver_foto': get_setting('screensaver_foto', '')}

    # Jinja2 template global: geef volledige naam (voornaam + achternaam) terug
    @app.template_global()
    def volnaam(obj, fallback='—'):
        if obj is None:
            return fallback
        try:
            v = obj['voornaam'] or ''
        except (KeyError, IndexError, TypeError):
            v = ''
        try:
            a = obj['achternaam'] or ''
        except (KeyError, IndexError, TypeError):
            a = ''
        return (f"{v} {a}".strip()) or fallback

    # Jinja2 filter: converteer UTC datetime string naar Belgische lokale tijd
    @app.template_filter('localtime')
    def localtime_filter(value):
        if not value:
            return ''
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value)
            else:
                dt = value
            if _BRUSSELS:
                dt_utc = dt.replace(tzinfo=timezone.utc)
                dt_local = dt_utc.astimezone(_BRUSSELS)
            else:
                # Fallback: voeg 2 uur toe (geen DST-bewustzijn)
                from datetime import timedelta
                dt_local = dt + timedelta(hours=2)
            return dt_local.strftime('%d/%m/%Y %H:%M')
        except (ValueError, TypeError):
            return str(value)[:16] if value else ''

    # Blueprints
    from routes.kiosk import kiosk_bp
    from routes.admin import admin_bp
    from routes.api   import api_bp

    app.register_blueprint(kiosk_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp,   url_prefix='/api')

    @app.route('/videos/<path:pad>')
    def serve_video(pad):
        return send_from_directory(VIDEOS_DIR, pad)

    @app.route('/uploads/<path:pad>')
    def serve_upload(pad):
        return send_from_directory(UPLOADS_DIR, pad)

    add_log('systeem', 'KSA Bar gestart')

    from config import IS_RASPBERRY_PI
    if IS_RASPBERRY_PI:
        try:
            import subprocess as _sp
            _sp.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            add_log('systeem', 'ffmpeg beschikbaar')
        except Exception:
            add_log('systeem', 'ffmpeg niet gevonden — camera niet beschikbaar')
        try:
            from gpiozero import OutputDevice  # noqa
            add_log('systeem', 'GPIO beschikbaar')
        except Exception:
            add_log('systeem', 'GPIO niet beschikbaar — stub modus')

    return app


# WSGI-entry point voor gunicorn: gunicorn "app:create_app()"
# Direct opstarten (python app.py) blijft ook werken
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
