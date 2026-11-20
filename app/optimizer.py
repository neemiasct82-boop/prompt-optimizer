"""Core Prompt Optimizer logic: clarify -> confirm/revise -> generate.

The LLM proposes; deterministic guards enforce requirements that came from
user validation (participant P01): keep the reference date (AC7) and request a
coverage checklist when complete coverage is asked for (AC8).
"""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any
from zoneinfo import ZoneInfo

from .llm import LLMClient, LLMError
from .signing import sign_prompt

ANALYZE_SYSTEM = """You are Prompt Optimizer. You help professionals with little prompt-writing \
experience (first audience: occupational safety technicians in Brazil) turn an unclear request \
into a precise prompt for an AI assistant. You never answer the request yourself.

You receive a JSON object with: task, original_request, clarifications (questions already \
answered), force_confirm, today. A request is clear only when you can tell:
1. the deliverable (what the output is, e.g. comparison table, checklist, summary, letter);
2. the scope and priorities (what is covered first, what is included or excluded);
3. the format (structure, length, columns);
4. constraints (reference date for anything that changes over time, sources, audience).

Rules:
- Write every user-facing field in the SAME LANGUAGE as original_request.
- If the deliverable or scope is unclear and force_confirm is false, ask ONE focused question \
that resolves the most important gap. Offer 2-4 short options when that helps. Never ask again \
about something already answered in clarifications.
- If the request is about standards, regulations, prices or anything that changes over time and \
no reference date was given, treat the missing date as a gap.
- When the request is clear, or force_confirm is true, return a confirmation. If force_confirm \
is true and gaps remain, make reasonable assumptions and list them in "assumptions".
- The optimized prompt states the deliverable first, then scope and priorities, then format, \
then constraints. It preserves the user's goal, priorities, format and constraints and MUST NOT \
add requirements the user did not state or clearly imply.
- If a reference date was given, the optimized prompt must keep that exact date and ask the \
answering AI to identify the edition or revision of each source used, marking any that cannot \
be verified as of that date as "Unverified".
- If the user expects complete coverage of a set (e.g. "all NRs", "every item"), set \
requires_full_coverage to true and make the prompt ask for a coverage checklist where each item \
is marked "reviewed - match", "reviewed - no match identified" or "pending review".
- The paraphrase is a short yes/no question that summarises your understanding in plain words.

Return ONLY a JSON object, one of:
{"status":"clarify","question":"...","options":["..."],"gap":"deliverable|scope|format|reference_date|other"}
{"status":"confirm","paraphrase":"...?","optimized_prompt":"...","assumptions":["..."],"requires_full_coverage":false}
"""

REVISE_SYSTEM = """You are Prompt Optimizer. The user declined your previous understanding and \
explained what should change. You receive a JSON object with: original_request, clarifications, \
current_prompt, user_correction, today.

Apply the correction to the current prompt. Keep everything the user did not ask to change. Do \
not add requirements the user did not state or imply. Write in the same language as \
original_request. Keep any reference date and edition/revision instruction, and any coverage \
checklist instruction, unless the user asked to remove them.

Return ONLY a JSON object:
{"status":"confirm","paraphrase":"...?","optimized_prompt":"...","assumptions":["..."],"requires_full_coverage":false}
"""

GENERATE_SYSTEM = """Answer the user's prompt exactly as specified. Follow the requested format. \
Use Markdown tables when a table is requested. Respond in the language of the prompt. If you \
cannot verify a fact as of the requested reference date, say so explicitly."""

_DATE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DATE_BR = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_EDITION_WORDS = re.compile(r"edi[cç][aã]o|edi[cç][oõ]es|revis[aã]o|revis[oõ]es|edition|revision", re.I)
_FULL_COVERAGE = re.compile(
    r"\b(todas as|todos os|demais|all (the )?(remaining )?|every|complete coverage|cobertura completa)\b",
    re.I,
)
_PT_HINTS = re.compile(r"\b(que|não|para|com|das|dos|uma|normas|quero|preciso|tabela)\b", re.I)


# ---------- deterministic guards ----------

def is_portuguese(text: str) -> bool:
    return len(_PT_HINTS.findall(text)) >= 2


def extract_reference_dates(*texts: str) -> list[dt.date]:
    """Find dates the user wrote (YYYY-MM-DD or DD/MM/YYYY), in order, without duplicates."""
    found: list[dt.date] = []
    for text in texts:
        for y, m, d in _DATE_ISO.findall(text):
            _append_date(found, int(y), int(m), int(d))
        for d, m, y in _DATE_BR.findall(text):
            _append_date(found, int(y), int(m), int(d))
    return found


def _append_date(found: list[dt.date], y: int, m: int, d: int) -> None:
    try:
        date = dt.date(y, m, d)
    except ValueError:
        return
    if date not in found:
        found.append(date)


def _date_present(prompt: str, date: dt.date) -> bool:
    return date.isoformat() in prompt or date.strftime("%d/%m/%Y") in prompt


def ensure_reference_date(prompt: str, dates: list[dt.date], portuguese: bool) -> str:
    """AC7: keep the user's reference date and request the editions or revisions used."""
    if not dates:
        return prompt
    date = dates[-1]  # the most recent statement wins (corrections come later)
    additions = []
    if not _date_present(prompt, date):
        additions.append(
            f"Use {date.isoformat()} como data de referência." if portuguese
            else f"Use {date.isoformat()} as the reference date."
        )
    if not _EDITION_WORDS.search(prompt):
        additions.append(
            "Identifique a edição ou revisão de cada norma ou fonte usada e marque como "
            "\"Não verificada\" a que não puder ser confirmada nessa data." if portuguese
            else "Identify the edition or revision of each standard or source used, and mark as "
            "\"Unverified\" any that cannot be confirmed as of that date."
        )
    return prompt if not additions else prompt.rstrip() + "\n\n" + " ".join(additions)


def wants_full_coverage(model_flag: Any, *texts: str) -> bool:
    return bool(model_flag) or any(_FULL_COVERAGE.search(t) for t in texts)


def ensure_coverage_checklist(prompt: str, needed: bool, portuguese: bool) -> str:
    """AC8: ask for a coverage checklist with three statuses when full coverage is expected."""
    if not needed or "checklist" in prompt.lower():
        return prompt
    line = (
        "Inclua ao final um checklist de cobertura com cada item solicitado marcado como "
        "\"revisado – com correspondência\", \"revisado – sem correspondência identificada\" ou "
        "\"revisão pendente\"." if portuguese
        else "End with a coverage checklist that marks each requested item as \"reviewed - match\", "
        "\"reviewed - no match identified\" or \"pending review\"."
    )
    return prompt.rstrip() + "\n\n" + line


# ---------- model I/O ----------

def parse_model_json(text: str) -> dict[str, Any]:
    """Parse the model's JSON, tolerating code fences or text around the object."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise LLMError("The AI returned an unexpected format. Please try again.")
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError("The AI returned an unexpected format. Please try again.") from exc
    status = data.get("status")
    if status == "clarify" and isinstance(data.get("question"), str) and data["question"].strip():
        return data
    if (
        status == "confirm"
        and isinstance(data.get("optimized_prompt"), str)
        and data["optimized_prompt"].strip()
        and isinstance(data.get("paraphrase"), str)
    ):
        return data
    raise LLMError("The AI response was incomplete. Please try again.")


def _today() -> str:
    return dt.datetime.now(tz=ZoneInfo("America/Sao_Paulo")).date().isoformat()


def _confirmation(client: LLMClient, secret: str, data: dict, *, request: str, texts: list[str],
                  version: int, latency_ms: int) -> dict[str, Any]:
    portuguese = is_portuguese(request)
    prompt = data["optimized_prompt"].strip()
    prompt = ensure_reference_date(prompt, extract_reference_dates(*texts), portuguese)
    prompt = ensure_coverage_checklist(
        prompt, wants_full_coverage(data.get("requires_full_coverage"), *texts), portuguese
    )
    original_tokens, m1 = client.count_tokens(request)
    optimized_tokens, m2 = client.count_tokens(prompt)
    assumptions = [a for a in data.get("assumptions") or [] if isinstance(a, str) and a.strip()]
    return {
        "status": "confirm",
        "paraphrase": data["paraphrase"].strip(),
        "optimized_prompt": prompt,
        "assumptions": assumptions[:5],
        "version": version,
        "signature": sign_prompt(secret, version, prompt),
        "tokens": {
            "original": original_tokens,
            "optimized": optimized_tokens,
            "method": "estimate" if "estimate" in (m1, m2) else m1,
            "model": client.model,
        },
        "latency_ms": latency_ms,
    }


# ---------- public operations ----------

def analyze(client: LLMClient, secret: str, request: str, answers: list[dict], *,
            max_rounds: int, timeout: int) -> dict[str, Any]:
    """AC1/AC2: ask one focused question, or return a signed confirmation (version 1)."""
    force = len(answers) >= max_rounds
    payload = {
        "task": "analyze",
        "original_request": request,
        "clarifications": answers,
        "force_confirm": force,
        "today": _today(),
    }
    result = client.generate(ANALYZE_SYSTEM, json.dumps(payload, ensure_ascii=False),
                             json_mode=True, timeout=timeout)
    data = parse_model_json(result.text)
    latency = result.latency_ms
    if data["status"] == "clarify" and force:
        payload["force_confirm"] = True
        payload["note"] = "Maximum clarification rounds reached: return a confirmation now."
        retry = client.generate(ANALYZE_SYSTEM, json.dumps(payload, ensure_ascii=False),
                                json_mode=True, timeout=timeout)
        data = parse_model_json(retry.text)
        latency += retry.latency_ms
        if data["status"] != "confirm":
            raise LLMError("The AI could not settle on a prompt. Please rephrase your request.")
    if data["status"] == "clarify":
        options = [o for o in data.get("options") or [] if isinstance(o, str) and o.strip()]
        return {
            "status": "clarify",
            "question": data["question"].strip(),
            "options": options[:4],
            "gap": data.get("gap", "other"),
            "round": len(answers) + 1,
            "max_rounds": max_rounds,
            "latency_ms": latency,
        }
    texts = [request] + [a["answer"] for a in answers]
    return _confirmation(client, secret, data, request=request, texts=texts, version=1,
                         latency_ms=latency)


def revise(client: LLMClient, secret: str, request: str, answers: list[dict], current_prompt: str,
           version: int, feedback: str, *, timeout: int) -> dict[str, Any]:
    """AC3: apply the user's correction and return a new signed version (version + 1)."""
    payload = {
        "task": "revise",
        "original_request": request,
        "clarifications": answers,
        "current_prompt": current_prompt,
        "user_correction": feedback,
        "today": _today(),
    }
    result = client.generate(REVISE_SYSTEM, json.dumps(payload, ensure_ascii=False),
                             json_mode=True, timeout=timeout)
    data = parse_model_json(result.text)
    if data["status"] != "confirm":
        raise LLMError("The AI response was incomplete. Please try again.")
    texts = [request] + [a["answer"] for a in answers] + [feedback]
    return _confirmation(client, secret, data, request=request, texts=texts, version=version + 1,
                         latency_ms=result.latency_ms)


def generate_answer(client: LLMClient, prompt: str, version: int, *, timeout: int) -> dict[str, Any]:
    """AC4a: generate the answer from the confirmed prompt version."""
    result = client.generate(GENERATE_SYSTEM, prompt, json_mode=False, timeout=timeout,
                             max_output_tokens=8192)
    return {"answer": result.text, "version": version, "latency_ms": result.latency_ms,
            "usage": result.usage}
