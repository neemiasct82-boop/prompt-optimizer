"""Core logic: clarify/confirm (AC1, AC2), revise (AC3), guards from P01 (AC7, AC8), tokens (AC5)."""

import datetime as dt
import json

import pytest

from app import optimizer
from app.llm import LLMError, MockClient, estimate_tokens
from app.signing import sign_prompt, verify_prompt
from tests.conftest import SECRET, ScriptedClient

P01_REQUEST = ("Quero comparar as normas API com as NRs brasileiras, principalmente "
               "NR-10, NR-12 e NR-13, e depois as demais NRs.")
CONFIRM = {"status": "confirm", "paraphrase": "Você quer uma tabela comparativa?",
           "optimized_prompt": "Crie uma tabela comparativa organizada por norma API e cláusula.",
           "assumptions": [], "requires_full_coverage": False}


# ---------- AC7: reference date ----------

def test_extract_reference_dates_iso_and_brazilian_formats():
    dates = optimizer.extract_reference_dates("ref 2026-11-11", "ou 11/11/2026", "nova 01/12/2026")
    assert dates == [dt.date(2026, 11, 11), dt.date(2026, 12, 1)]


def test_extract_reference_dates_ignores_invalid_dates():
    assert optimizer.extract_reference_dates("31/02/2026 e 2026-13-01") == []


def test_reference_date_is_added_with_editions_when_model_drops_it():
    prompt = optimizer.ensure_reference_date("Compare API and NR requirements.", [dt.date(2026, 11, 11)],
                                             portuguese=False)
    assert "2026-11-11" in prompt
    assert "edition or revision" in prompt
    assert "Unverified" in prompt


def test_reference_date_guard_keeps_prompt_that_already_complies():
    prompt = "Use 11/11/2026 as the reference date and identify the edition of each standard."
    assert optimizer.ensure_reference_date(prompt, [dt.date(2026, 11, 11)], portuguese=False) == prompt


def test_no_date_means_no_change():
    assert optimizer.ensure_reference_date("Prompt", [], portuguese=True) == "Prompt"


# ---------- AC8: coverage checklist ----------

def test_full_coverage_detected_from_user_text():
    assert optimizer.wants_full_coverage(False, "revise todas as NRs")
    assert optimizer.wants_full_coverage(False, "depois as demais NRs")
    assert not optimizer.wants_full_coverage(False, "compare NR-10 and API RP 54")


def test_coverage_checklist_added_in_user_language_with_three_statuses():
    prompt = optimizer.ensure_coverage_checklist("Crie uma tabela.", True, portuguese=True)
    for status in ("revisado – com correspondência", "revisado – sem correspondência identificada",
                   "revisão pendente"):
        assert status in prompt


# ---------- model output parsing ----------

def test_parse_model_json_accepts_code_fences():
    data = optimizer.parse_model_json("```json\n" + json.dumps(CONFIRM) + "\n```")
    assert data["status"] == "confirm"


@pytest.mark.parametrize("text", ["not json", '{"status": "confirm"}', '{"status": "other"}'])
def test_parse_model_json_rejects_bad_output(text):
    with pytest.raises(LLMError):
        optimizer.parse_model_json(text)


# ---------- AC1 / AC2 ----------

def test_ambiguous_request_returns_one_question():
    llm = ScriptedClient([{"status": "clarify", "question": "Qual entrega você espera?",
                           "options": ["Tabela", "Resumo", "Checklist", "Lista", "Extra"],
                           "gap": "deliverable"}])
    result = optimizer.analyze(llm, SECRET, P01_REQUEST, [], max_rounds=3, timeout=5)
    assert result["status"] == "clarify"
    assert result["question"] == "Qual entrega você espera?"
    assert len(result["options"]) == 4  # capped
    assert result["round"] == 1


def test_confirmation_is_signed_and_counts_tokens_with_same_model():
    llm = ScriptedClient([CONFIRM])
    answers = [{"question": "Data de referência?", "answer": "11/11/2026"}]
    result = optimizer.analyze(llm, SECRET, P01_REQUEST, answers, max_rounds=3, timeout=5)
    assert result["status"] == "confirm"
    assert result["version"] == 1
    assert verify_prompt(SECRET, 1, result["optimized_prompt"], result["signature"])
    assert "11/11/2026" in result["optimized_prompt"] or "2026-11-11" in result["optimized_prompt"]  # AC7
    assert "checklist" in result["optimized_prompt"].lower()  # AC8 ("demais NRs")
    assert result["tokens"]["model"] == "scripted-model"
    assert result["tokens"]["original"] > 0 and result["tokens"]["optimized"] > 0


def test_after_max_rounds_the_model_is_forced_to_confirm():
    llm = ScriptedClient([{"status": "clarify", "question": "Mais uma?"}, CONFIRM])
    answers = [{"question": f"q{i}", "answer": f"a{i}"} for i in range(3)]
    result = optimizer.analyze(llm, SECRET, P01_REQUEST, answers, max_rounds=3, timeout=5)
    assert result["status"] == "confirm"
    assert json.loads(llm.calls[0]["user"])["force_confirm"] is True
    assert len(llm.calls) == 2


def test_model_that_never_converges_raises():
    llm = ScriptedClient([{"status": "clarify", "question": "?"}, {"status": "clarify", "question": "?"}])
    answers = [{"question": "q", "answer": "a"}] * 3
    with pytest.raises(LLMError):
        optimizer.analyze(llm, SECRET, P01_REQUEST, answers, max_rounds=3, timeout=5)


# ---------- AC3 ----------

def test_revise_sends_correction_and_increments_version():
    revised = dict(CONFIRM, optimized_prompt="Crie uma tabela organizada por norma API, data 2026-11-11.")
    llm = ScriptedClient([revised])
    result = optimizer.revise(llm, SECRET, P01_REQUEST, [], CONFIRM["optimized_prompt"], 1,
                              "Use 2026-11-11 como data de referência", timeout=5)
    sent = json.loads(llm.calls[0]["user"])
    assert sent["user_correction"] == "Use 2026-11-11 como data de referência"
    assert sent["current_prompt"] == CONFIRM["optimized_prompt"]
    assert result["version"] == 2
    assert "2026-11-11" in result["optimized_prompt"]


# ---------- AC5 ----------

def test_estimate_tokens_fallback():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd" * 10) == 10


def test_mock_client_labels_counts_as_estimate():
    assert MockClient().count_tokens("hello world")[1] == "estimate"


# ---------- AC4b ----------

def test_signature_detects_text_or_version_tampering():
    sig = sign_prompt(SECRET, 2, "prompt v2")
    assert verify_prompt(SECRET, 2, "prompt v2", sig)
    assert not verify_prompt(SECRET, 2, "prompt v2 edited", sig)
    assert not verify_prompt(SECRET, 1, "prompt v2", sig)
    assert not verify_prompt("other-secret", 2, "prompt v2", sig)
