"""Flask web application."""

from flask import Flask
from .routes import bp


def create_app(config=None):
    """Application factory."""
    app = Flask(__name__)

    if config:
        app.config.update(config)

    app.register_blueprint(bp)

    return app