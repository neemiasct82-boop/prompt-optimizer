"""AI layer: Google Gemini over REST, plus a deterministic mock for tests and demos."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from typing import Protocol

import requests


class LLMError(RuntimeError):
    """Provider failure that should reach the user as HTTP 502."""


@dataclass
class LLMResult:
    text: str
    latency_ms: int
    usage: dict = field(default_factory=dict)
    finish_reason: str = "STOP"


class LLMClient(Protocol):
    name: str
    model: str

    def generate(self, system: str, user: str, *, json_mode: bool, timeout: int,
                 max_output_tokens: int = 2048) -> LLMResult: ...

    def count_tokens(self, text: str) -> tuple[int, str]: ...


def estimate_tokens(text: str) -> int:
    """Character-based fallback: about 4 characters per token (labelled 'estimate')."""
    return max(1, math.ceil(len(text) / 4)) if text else 0


class GeminiClient:
    name = "gemini"

    def __init__(self, api_key: str, model: str, base_url: str):
        self._api_key = api_key
        self.model = model
        self._base_url = base_url

    def _post(self, method: str, body: dict, timeout: int) -> dict:
        url = f"{self._base_url}/models/{self.model}:{method}"
        try:
            resp = requests.post(
                url,
                json=body,
                headers={"x-goog-api-key": self._api_key, "Content-Type": "application/json"},
                timeout=timeout,
            )
        except requests.RequestException as exc:  # network error or timeout
            raise LLMError(f"AI provider unreachable: {exc.__class__.__name__}") from exc
        if resp.status_code != 200:
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", "")[:200]
            except ValueError:
                pass
            raise LLMError(f"AI provider returned HTTP {resp.status_code}. {detail}".strip())
        return resp.json()

    def generate(self, system: str, user: str, *, json_mode: bool, timeout: int,
                 max_output_tokens: int = 2048) -> LLMResult:
        config: dict = {"temperature": 0.2, "maxOutputTokens": max_output_tokens}
        if json_mode:
            config["responseMimeType"] = "application/json"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": config,
        }
        start = time.monotonic()
        data = self._post("generateContent", body, timeout)
        latency = int((time.monotonic() - start) * 1000)
        candidates = data.get("candidates") or []
        if not candidates:
            reason = data.get("promptFeedback", {}).get("blockReason", "no candidates")
            raise LLMError(f"AI provider returned no answer ({reason}).")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text.strip():
            raise LLMError("AI provider returned an empty answer.")
        return LLMResult(text=text, latency_ms=latency, usage=data.get("usageMetadata", {}),
                         finish_reason=candidates[0].get("finishReason", "STOP"))

    def count_tokens(self, text: str) -> tuple[int, str]:
        body = {"contents": [{"role": "user", "parts": [{"text": text}]}]}
        try:
            data = self._post("countTokens", body, timeout=15)
            return int(data["totalTokens"]), "gemini-countTokens"
        except (LLMError, KeyError, TypeError, ValueError):
            return estimate_tokens(text), "estimate"


class MockClient:
    """Deterministic provider for CI, tests and local demos without a key."""

    name = "mock"
    model = "mock-model"

    def generate(self, system: str, user: str, *, json_mode: bool, timeout: int,
                 max_output_tokens: int = 2048) -> LLMResult:
        if not json_mode:
            first_line = user.strip().splitlines()[0][:120] if user.strip() else ""
            return LLMResult(text=f"**Mock answer** generated from the confirmed prompt.\n\n> {first_line}",
                             latency_ms=1)
        payload = json.loads(user)
        task = payload.get("task")
        request = payload.get("original_request", "")
        answers = payload.get("clarifications", [])
        if task == "analyze" and not answers and not payload.get("force_confirm"):
            result = {
                "status": "clarify",
                "question": "What deliverable do you expect "
                "(for example a comparison table, a checklist or a summary)?",
                "options": ["Comparison table", "Checklist", "Summary"],
                "gap": "deliverable",
            }
        else:
            details = "; ".join(a["answer"] for a in answers)
            prompt = f"Task: {request}\nDetails confirmed by the user: {details or 'none'}"
            if task == "revise":
                current = payload.get("current_prompt", "")
                prompt = f"{current}\nCorrection from the user: {payload.get('user_correction', '')}"
            result = {
                "status": "confirm",
                "paraphrase": "Did I understand correctly? You want: " + request[:200],
                "optimized_prompt": prompt,
                "assumptions": [],
                "requires_full_coverage": False,
            }
        return LLMResult(text=json.dumps(result), latency_ms=1)

    def count_tokens(self, text: str) -> tuple[int, str]:
        return estimate_tokens(text), "estimate"


def build_client(settings) -> LLMClient:
    if settings.llm_provider == "gemini":
        return GeminiClient(settings.gemini_api_key, settings.gemini_model, settings.gemini_base_url)
    return MockClient()
