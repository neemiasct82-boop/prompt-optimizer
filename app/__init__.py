"""Prompt Optimizer — Flask application factory."""

from __future__ import annotations

import logging

from flask import Flask, jsonify

from .config import load_settings


def create_app(overrides: dict | None = None) -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = load_settings(overrides)

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # 64 KB request bodies

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", provider=settings.llm_provider, model=settings.gemini_model)

    return app
