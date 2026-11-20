"""Input validation for API request bodies (spec section 2, AC6)."""

from __future__ import annotations

import re
from typing import Any

REQUEST_MIN, REQUEST_MAX = 10, 4000
FEEDBACK_MIN, FEEDBACK_MAX = 3, 1000
ANSWER_MAX, ANSWERS_MAX_ITEMS = 1000, 5
PROMPT_MAX = 8000
VERSION_MIN, VERSION_MAX = 1, 50

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HEX = re.compile(r"^[0-9a-f]{64}$")


class ValidationError(ValueError):
    """Raised when a request body is invalid; message names the field."""


def clean_text(value: Any, field: str, min_len: int, max_len: int) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be text.")
    text = _CONTROL_CHARS.sub("", value).replace("\r\n", "\n").strip()
    if len(text) < min_len:
        raise ValidationError(f"'{field}' must have at least {min_len} characters.")
    if len(text) > max_len:
        raise ValidationError(f"'{field}' must have at most {max_len} characters.")
    return text


def _body(data: Any) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return data


def _answers(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError("'answers' must be a list.")
    if len(value) > ANSWERS_MAX_ITEMS:
        raise ValidationError(f"'answers' must have at most {ANSWERS_MAX_ITEMS} items.")
    out = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValidationError(f"'answers[{i}]' must be an object.")
        out.append(
            {
                "question": clean_text(item.get("question"), f"answers[{i}].question", 1, ANSWER_MAX),
                "answer": clean_text(item.get("answer"), f"answers[{i}].answer", 1, ANSWER_MAX),
            }
        )
    return out


def _signed_prompt(data: dict) -> dict[str, Any]:
    version = data.get("version")
    is_int = isinstance(version, int) and not isinstance(version, bool)
    if not is_int or not (VERSION_MIN <= version <= VERSION_MAX):
        raise ValidationError(f"'version' must be an integer between {VERSION_MIN} and {VERSION_MAX}.")
    signature = data.get("signature")
    if not isinstance(signature, str) or not _HEX.match(signature):
        raise ValidationError("'signature' is missing or malformed.")
    return {
        "prompt": clean_text(data.get("prompt"), "prompt", 1, PROMPT_MAX),
        "version": version,
        "signature": signature,
    }


def validate_analyze(data: Any) -> dict[str, Any]:
    data = _body(data)
    return {
        "request": clean_text(data.get("request"), "request", REQUEST_MIN, REQUEST_MAX),
        "answers": _answers(data.get("answers")),
    }


def validate_revise(data: Any) -> dict[str, Any]:
    data = _body(data)
    out = validate_analyze(data)
    out.update(_signed_prompt(data))
    out["feedback"] = clean_text(data.get("feedback"), "feedback", FEEDBACK_MIN, FEEDBACK_MAX)
    return out


def validate_generate(data: Any) -> dict[str, Any]:
    return _signed_prompt(_body(data))
