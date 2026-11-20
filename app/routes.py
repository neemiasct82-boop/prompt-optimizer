"""HTTP routes: UI page and JSON API (spec sections 2-3)."""

from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, render_template, request

from . import optimizer
from .llm import LLMError
from .monitoring import client_ip
from .signing import verify_prompt
from .validation import ValidationError, validate_analyze, validate_generate, validate_revise

bp = Blueprint("main", __name__)


def _ctx():
    return (current_app.config["SETTINGS"], current_app.config["LLM"], current_app.config["STATS"])


def _error(message: str, status: int):
    return jsonify(error=message), status


@bp.before_request
def _rate_limit():
    if request.path.startswith("/api/") and request.method == "POST":
        limiter = current_app.config["LIMITER"]
        if not limiter.allow(client_ip()):
            return _error("Too many requests. Please wait a few minutes and try again.", 429)
    return None


@bp.get("/")
def index():
    settings, _, _ = _ctx()
    return render_template("index.html", provider=settings.llm_provider)


@bp.post("/api/analyze")
def api_analyze():
    settings, llm, stats = _ctx()
    try:
        data = validate_analyze(request.get_json(silent=True))
        result = optimizer.analyze(
            llm, settings.app_secret, data["request"], data["answers"],
            max_rounds=settings.max_clarify_rounds, timeout=settings.analyze_timeout_s,
        )
    except ValidationError as exc:
        return _error(str(exc), 400)
    except LLMError as exc:
        stats.incr("llm_errors")
        return _error(str(exc), 502)
    g.llm_ms = result.get("latency_ms")
    stats.incr("analyze")
    stats.incr("clarify_shown" if result["status"] == "clarify" else "confirm_shown")
    return jsonify(result)


@bp.post("/api/revise")
def api_revise():
    settings, llm, stats = _ctx()
    try:
        data = validate_revise(request.get_json(silent=True))
    except ValidationError as exc:
        return _error(str(exc), 400)
    if not verify_prompt(settings.app_secret, data["version"], data["prompt"], data["signature"]):
        stats.incr("signature_rejected")
        return _error("This prompt version was not issued by the server. Please start again.", 403)
    try:
        result = optimizer.revise(
            llm, settings.app_secret, data["request"], data["answers"], data["prompt"],
            data["version"], data["feedback"], timeout=settings.analyze_timeout_s,
        )
    except LLMError as exc:
        stats.incr("llm_errors")
        return _error(str(exc), 502)
    g.llm_ms = result.get("latency_ms")
    stats.incr("revise")
    stats.incr("confirm_shown")
    return jsonify(result)


@bp.post("/api/generate")
def api_generate():
    settings, llm, stats = _ctx()
    try:
        data = validate_generate(request.get_json(silent=True))
    except ValidationError as exc:
        return _error(str(exc), 400)
    if not verify_prompt(settings.app_secret, data["version"], data["prompt"], data["signature"]):
        stats.incr("signature_rejected")
        return _error("This prompt version was not issued by the server. Please start again.", 403)
    try:
        result = optimizer.generate_answer(llm, data["prompt"], data["version"],
                                           timeout=settings.generate_timeout_s)
    except LLMError as exc:
        stats.incr("llm_errors")
        return _error(str(exc), 502)
    g.llm_ms = result.get("latency_ms")
    stats.incr("generate")
    return jsonify(result)


@bp.post("/api/event")
def api_event():
    """Client-side UI events for the funnel (e.g. copy prompt, start over). No content is stored."""
    _, _, stats = _ctx()
    name = (request.get_json(silent=True) or {}).get("name")
    if name not in {"copy_prompt", "copy_answer", "start_over"}:
        return _error("Unknown event.", 400)
    stats.incr(f"ui_{name}")
    return jsonify(ok=True)


@bp.get("/api/stats")
def api_stats():
    _, _, stats = _ctx()
    return jsonify(stats.snapshot())
