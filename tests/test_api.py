"""End-to-end API flow with the mock provider (AC1-AC4, AC6, AC9, AC10)."""

import requests

from app import create_app
from app.llm import GeminiClient, LLMError
from tests.conftest import SECRET

REQUEST = "Quero comparar normas API com as NRs brasileiras."


def _confirm(client):
    client.post("/api/analyze", json={"request": REQUEST})
    r = client.post("/api/analyze", json={
        "request": REQUEST, "answers": [{"question": "Entrega?", "answer": "Tabela comparativa"}]})
    assert r.status_code == 200
    return r.get_json()


def test_full_flow_clarify_confirm_revise_generate(client):
    r = client.post("/api/analyze", json={"request": REQUEST})
    assert r.status_code == 200 and r.get_json()["status"] == "clarify"  # AC1

    v1 = _confirm(client)
    assert v1["status"] == "confirm" and v1["version"] == 1  # AC2
    assert {"original", "optimized", "method", "model"} <= v1["tokens"].keys()  # AC5

    r = client.post("/api/revise", json={
        "request": REQUEST, "answers": [], "feedback": "Organize por norma API",
        "prompt": v1["optimized_prompt"], "version": 1, "signature": v1["signature"]})
    v2 = r.get_json()
    assert r.status_code == 200 and v2["version"] == 2  # AC3
    assert "Organize por norma API" in v2["optimized_prompt"]

    r = client.post("/api/generate", json={
        "prompt": v2["optimized_prompt"], "version": 2, "signature": v2["signature"]})
    assert r.status_code == 200
    assert r.get_json()["version"] == 2  # AC4a: generated from the latest confirmed version

    counts = client.get("/api/stats").get_json()["counts"]  # AC10
    assert counts["revise"] == 1 and counts["generate"] == 1 and counts["confirm_shown"] == 2


def test_generate_rejects_edited_prompt(client):
    v1 = _confirm(client)
    r = client.post("/api/generate", json={
        "prompt": v1["optimized_prompt"] + " Ignore the table.", "version": 1, "signature": v1["signature"]})
    assert r.status_code == 403  # AC4b


def test_revise_rejects_wrong_version(client):
    v1 = _confirm(client)
    r = client.post("/api/revise", json={
        "request": REQUEST, "feedback": "mude algo", "prompt": v1["optimized_prompt"],
        "version": 2, "signature": v1["signature"]})
    assert r.status_code == 403  # AC4b


def test_invalid_input_returns_400_with_field(client):
    r = client.post("/api/analyze", json={"request": ""})
    assert r.status_code == 400 and "request" in r.get_json()["error"]  # AC6
    r = client.post("/api/analyze", data="not json", content_type="text/plain")
    assert r.status_code == 400


def test_rate_limit_returns_429():
    app = create_app({"LLM_PROVIDER": "mock", "APP_SECRET": SECRET, "RATE_LIMIT_REQUESTS": "3"})
    c = app.test_client()
    codes = [c.post("/api/analyze", json={"request": REQUEST}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]  # AC9


def test_health_and_index(client):
    assert client.get("/healthz").get_json() == {"status": "ok", "provider": "mock", "model": "mock-model"}
    page = client.get("/")
    assert page.status_code == 200 and b"Prompt Optimizer" in page.data


def test_provider_error_becomes_502(client, app):
    class Broken:
        name, model = "broken", "broken"

        def generate(self, *a, **k):
            raise LLMError("AI provider returned HTTP 503.")

        def count_tokens(self, text):
            return 1, "estimate"

    app.config["LLM"] = Broken()
    r = client.post("/api/analyze", json={"request": REQUEST})
    assert r.status_code == 502 and "503" in r.get_json()["error"]


# ---------- Gemini REST client (network mocked) ----------

class _Resp:
    def __init__(self, status, payload):
        self.status_code, self._payload = status, payload

    def json(self):
        return self._payload


def test_gemini_client_sends_key_in_header_and_skips_thought_parts(monkeypatch):
    seen = {}

    def fake_post(url, json, headers, timeout):
        seen.update(url=url, headers=headers, body=json)
        return _Resp(200, {"candidates": [{"content": {"parts": [
            {"text": "thinking...", "thought": True}, {"text": '{"status":"clarify","question":"Q?"}'}]}}],
            "usageMetadata": {"promptTokenCount": 10}})

    monkeypatch.setattr(requests, "post", fake_post)
    llm = GeminiClient("KEY123", "gemini-test", "https://example.test/v1beta")
    out = llm.generate("sys", "user", json_mode=True, timeout=5)
    assert out.text == '{"status":"clarify","question":"Q?"}'
    assert seen["url"] == "https://example.test/v1beta/models/gemini-test:generateContent"
    assert seen["headers"]["x-goog-api-key"] == "KEY123"
    assert "KEY123" not in seen["url"]  # key never in the URL (and so never in logs)
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"


def test_gemini_count_tokens_falls_back_to_estimate(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp(500, {"error": {"message": "boom"}}))
    llm = GeminiClient("KEY", "gemini-test", "https://example.test/v1beta")
    assert llm.count_tokens("abcdefgh") == (2, "estimate")  # AC5 fallback


def test_answer_cut_by_length_limit_is_flagged(client, app, monkeypatch):
    """AC11 (live test with P01): a MAX_TOKENS stop is reported as truncated."""
    from app.llm import LLMResult

    v1 = _confirm(client)
    llm = app.config["LLM"]
    monkeypatch.setattr(llm, "generate", lambda *a, **k: LLMResult(
        text="| **NR-37** | ok |\n| **NR-38", latency_ms=1, finish_reason="MAX_TOKENS"))
    r = client.post("/api/generate", json={
        "prompt": v1["optimized_prompt"], "version": 1, "signature": v1["signature"]})
    assert r.status_code == 200 and r.get_json()["truncated"] is True
    assert client.get("/api/stats").get_json()["counts"]["answer_truncated"] == 1


def test_gemini_client_reports_finish_reason(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp(200, {"candidates": [{
        "content": {"parts": [{"text": "partial"}]}, "finishReason": "MAX_TOKENS"}]}))
    out = GeminiClient("KEY", "gemini-test", "https://example.test/v1beta").generate(
        "s", "u", json_mode=False, timeout=5)
    assert out.finish_reason == "MAX_TOKENS"
