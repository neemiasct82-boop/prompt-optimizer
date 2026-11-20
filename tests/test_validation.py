"""AC6: input outside the limits returns a clear error naming the field."""

import pytest

from app.validation import ValidationError, validate_analyze, validate_generate, validate_revise


def test_valid_request_is_trimmed_and_cleaned():
    data = validate_analyze({"request": "  Compare API standards\x00 with NRs  "})
    assert data == {"request": "Compare API standards with NRs", "answers": []}


@pytest.mark.parametrize("body, field", [
    ({"request": "short"}, "request"),
    ({"request": "x" * 4001}, "request"),
    ({"request": 123}, "request"),
    ({"request": "valid request text", "answers": "nope"}, "answers"),
    ({"request": "valid request text", "answers": [{"question": "q"}]}, "answers[0].answer"),
])
def test_invalid_analyze_bodies_name_the_field(body, field):
    with pytest.raises(ValidationError, match=field.replace("[", r"\[").replace("]", r"\]")):
        validate_analyze(body)


def test_body_must_be_object():
    with pytest.raises(ValidationError, match="JSON object"):
        validate_analyze(["not", "an", "object"])


@pytest.mark.parametrize("version", [0, 51, "1", True, None])
def test_version_must_be_int_in_range(version):
    with pytest.raises(ValidationError, match="version"):
        validate_generate({"prompt": "p", "version": version, "signature": "a" * 64})


def test_signature_must_be_hex_sha256():
    with pytest.raises(ValidationError, match="signature"):
        validate_generate({"prompt": "p", "version": 1, "signature": "not-hex"})


def test_revise_requires_feedback():
    body = {"request": "valid request text", "prompt": "p", "version": 1, "signature": "a" * 64,
            "feedback": "x"}
    with pytest.raises(ValidationError, match="feedback"):
        validate_revise(body)
