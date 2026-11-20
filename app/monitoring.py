"""Basic monitoring (AC10) and per-IP rate limiting (AC9). In-memory, per process."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import Counter, defaultdict, deque

from flask import Flask, g, request

log = logging.getLogger("prompt_optimizer")


class Stats:
    """Thread-safe counters exposed at /api/stats (usage funnel, errors, latency)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: Counter[str] = Counter()
        self._latency_total_ms = 0
        self._latency_n = 0
        self.started_at = time.time()

    def incr(self, key: str, n: int = 1) -> None:
        with self._lock:
            self._counts[key] += n

    def observe_latency(self, ms: int) -> None:
        with self._lock:
            self._latency_total_ms += ms
            self._latency_n += 1

    def snapshot(self) -> dict:
        with self._lock:
            avg = round(self._latency_total_ms / self._latency_n) if self._latency_n else 0
            return {
                "uptime_s": int(time.time() - self.started_at),
                "counts": dict(self._counts),
                "avg_api_latency_ms": avg,
                "note": "In-memory counters for this process since the last restart.",
            }


class RateLimiter:
    """Sliding-window limit: at most `limit` requests per `window_s` per key."""

    def __init__(self, limit: int, window_s: int) -> None:
        self.limit = limit
        self.window_s = window_s
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window_s:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True


def client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "unknown")


def install_request_logging(app: Flask, stats: Stats) -> None:
    """One JSON log line per request; never logs request bodies or secrets."""

    @app.before_request
    def _start_timer():
        g.start = time.monotonic()

    @app.after_request
    def _log(response):
        ms = int((time.monotonic() - g.get("start", time.monotonic())) * 1000)
        if request.path.startswith("/api/") and request.path != "/api/stats":
            stats.observe_latency(ms)
            if response.status_code >= 400:
                stats.incr(f"http_{response.status_code}")
        log.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "ms": ms,
            "llm_ms": g.get("llm_ms"),
        }))
        return response
