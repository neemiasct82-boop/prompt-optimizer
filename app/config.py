"""Runtime configuration read from environment variables (never hardcoded)."""

from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass

log = logging.getLogger("prompt_optimizer")


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    gemini_api_key: str
    gemini_model: str
    gemini_base_url: str
    app_secret: str
    rate_limit_requests: int
    rate_limit_window_s: int
    analyze_timeout_s: int
    generate_timeout_s: int
    max_clarify_rounds: int


def load_settings(overrides: dict | None = None) -> Settings:
    """Build Settings from the environment, with optional overrides for tests."""
    env = dict(os.environ)
    if overrides:
        env.update({k: str(v) for k, v in overrides.items()})

    api_key = env.get("GEMINI_API_KEY", "").strip()
    provider = env.get("LLM_PROVIDER", "").strip().lower() or ("gemini" if api_key else "mock")
    if provider == "gemini" and not api_key:
        log.warning("LLM_PROVIDER=gemini but GEMINI_API_KEY is empty; falling back to mock provider")
        provider = "mock"

    app_secret = env.get("APP_SECRET", "").strip()
    if not app_secret:
        # With `gunicorn --preload` all workers share this value. Set APP_SECRET in production.
        log.warning("APP_SECRET not set; using a random per-process secret")
        app_secret = secrets.token_hex(32)

    return Settings(
        llm_provider=provider,
        gemini_api_key=api_key,
        gemini_model=env.get("GEMINI_MODEL", "gemini-3.5-flash").strip(),
        gemini_base_url=env.get(
            "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
        ).rstrip("/"),
        app_secret=app_secret,
        rate_limit_requests=int(env.get("RATE_LIMIT_REQUESTS", "30")),
        rate_limit_window_s=int(env.get("RATE_LIMIT_WINDOW_S", "600")),
        analyze_timeout_s=int(env.get("ANALYZE_TIMEOUT_S", "60")),
        generate_timeout_s=int(env.get("GENERATE_TIMEOUT_S", "180")),
        max_clarify_rounds=int(env.get("MAX_CLARIFY_ROUNDS", "3")),
    )
