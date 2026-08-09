"""
Flask application factory. main.py calls create_app() and runs it — nothing
in this file starts a server itself, so the same app object is importable
for tests (flask.testing) without side effects.
"""
from __future__ import annotations

from flask import Flask

from config import settings


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False

    from dashboard.api_routes import api_bp
    from dashboard.page_routes import pages_bp
    from dashboard.download_routes import downloads_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(downloads_bp)

    return app
