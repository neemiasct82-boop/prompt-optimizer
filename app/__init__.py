"""Prompt Optimizer — Flask application factory."""

from __future__ import annotations

import logging

from flask import Flask, jsonify

from .config import load_settings
from .llm import build_client
from .monitoring import RateLimiter, Stats, install_request_logging


def create_app(overrides: dict | None = None) -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = load_settings(overrides)

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64 KB request bodies
    app.config["LLM"] = build_client(settings)
    app.config["STATS"] = Stats()
    app.config["LIMITER"] = RateLimiter(settings.rate_limit_requests, settings.rate_limit_window_s)

    install_request_logging(app, app.config["STATS"])

    from .routes import bp

    app.register_blueprint(bp)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", provider=settings.llm_provider, model=app.config["LLM"].model)

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="Request body is too large."), 413

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Not found."), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify(error="Method not allowed."), 405

    return app
