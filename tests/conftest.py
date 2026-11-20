import json

import pytest

from app import create_app
from app.llm import LLMResult

SECRET = "test-secret-" + "0" * 40


@pytest.fixture
def app():
    return create_app({"LLM_PROVIDER": "mock", "APP_SECRET": SECRET, "RATE_LIMIT_REQUESTS": "1000"})


@pytest.fixture
def client(app):
    return app.test_client()


class ScriptedClient:
    """Fake LLM that returns queued JSON responses and records what it received."""

    name = "scripted"
    model = "scripted-model"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, system, user, *, json_mode, timeout, max_output_tokens=2048):
        self.calls.append({"system": system, "user": user, "json_mode": json_mode})
        item = self.responses.pop(0)
        text = item if isinstance(item, str) else json.dumps(item)
        return LLMResult(text=text, latency_ms=5)

    def count_tokens(self, text):
        return len(text.split()), "scripted-tokenizer"
