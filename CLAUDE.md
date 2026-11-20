# CLAUDE.md — instructions for AI coding assistants

## Project
Prompt Optimizer: a Flask web app that clarifies an unclear request, asks the
user to confirm or correct a paraphrase, and only then generates the answer
from the confirmed prompt. Read `docs/spec.md` (source of truth) and
`docs/architecture.md` before changing code.

## Commands
- Install: `pip install -r requirements-dev.txt`
- Run locally (mock AI): `LLM_PROVIDER=mock flask --app wsgi run --debug`
- Tests: `pytest -q`
- Lint: `ruff check .`

## Rules
- Every behaviour change must map to an acceptance criterion (AC#) in
  `docs/spec.md`. Update the spec in the same commit if behaviour changes.
- Never hardcode secrets. Read `GEMINI_API_KEY` and `APP_SECRET` from the
  environment via `app/config.py`.
- Never call the real Gemini API in tests. Use `LLM_PROVIDER=mock` or
  monkeypatch `requests.post`.
- Keep the server stateless. Conversation state lives in the browser; prompt
  versions are protected by HMAC signatures (`app/signing.py`).
- Validate all request bodies with `app/validation.py` before use.
- Escape model output in the UI; never assign model text to `innerHTML`
  without escaping first.
- Keep user-facing text in the user's language (the model mirrors the
  request language); code, comments and docs in English.
- Small, meaningful commits with conventional prefixes (`feat:`, `fix:`,
  `test:`, `docs:`, `ci:`, `chore:`).
