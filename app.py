"""
KSA Bar Systeem — Flask hoofdapplicatie.
Start met: python app.py
"""
import os
import secrets
from flask import Flask, send_from_directory

from config import BASE_DIR, VIDEOS_DIR, BACKUPS_DIR, UPLOADS_DIR, UPLOADS_PERSONS_DIR, UPLOADS_PRODUCTS_DIR
from database.schema import init_db
from database.db import add_log


def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

    # Mappen
    for d in [VIDEOS_DIR, BACKUPS_DIR, UPLOADS_DIR, UPLOADS_PERSONS_DIR, UPLOADS_PRODUCTS_DIR]:
        os.makedirs(d, exist_ok=True)

    # Database
    init_db()

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
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
