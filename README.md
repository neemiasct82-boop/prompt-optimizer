# Prompt Optimizer

**Clarify the request, confirm the prompt, then get the answer.**

[![CI](https://github.com/neemiasct82-boop/prompt-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/neemiasct82-boop/prompt-optimizer/actions/workflows/ci.yml)

- **Live app:** https://prompt-optimizer-mw8t.onrender.com (free tier: the first request after idle can take about a minute)
- **Demo video (1:53, English captions):** [`docs/demo/Prompt_Optimizer_Demo_2min.mp4`](docs/demo/Prompt_Optimizer_Demo_2min.mp4)
- **Live test with a real user:** [`docs/evidence/06_Live_User_Test_Record.md`](docs/evidence/06_Live_User_Test_Record.md)
- **Graded Mini Project 4.2 — AI-Powered Web Application** (individual)

## Problem and user

Occupational safety technicians in Brazil increasingly use AI chat tools for work research,
but many have little experience writing prompts. They describe the topic (for example
Brazilian Regulatory Standards, NRs, and API standards) and leave the deliverable implicit.
The AI then answers a different question, and the user has to revise and ask again.

Observed case (participant P01, 2026-11-11): the original prompt produced an explanation of
NRs and API standards; the clarified prompt produced a clause-by-clause comparison table with
a reference date and source editions, which P01 preferred. Evidence: [`docs/evidence/`](docs/evidence).

## What the app does

1. **Clarify.** If the deliverable, scope or reference date is unclear, it asks **one
   focused question** at a time (max 3), with quick options.
2. **Confirm.** It shows its understanding as a yes/no question, with the **original
   request and the optimized prompt side by side** and their **input token counts** for
   the same Gemini model.
3. **Revise.** "No, change something" → the user says what is wrong → a new prompt version
   is shown for confirmation.
4. **Generate.** "Yes" → the answer is generated **from the latest confirmed prompt**,
   without retyping anything. The answer shows which version it came from.

## Live test with a real user (2026-11-23)

Participant P01 used the deployed app in a private window with the real model
(`gemini-3.5-flash`). She ran both flows: **Confirm** (2 questions → v1 → answer from v1) and
**Revise** (2 questions → declined v1 → added "November 2026" as the reference date → v2 →
answer from v2), and rated the Confirm session 4.5/5. The optimized prompts were 7.5–9× longer than her originals (33 → 301 and
38 → 285 tokens). The value is an answer that matches her intent, not a shorter input. The test found two
issues, both fixed with tests: an answer cut off without warning, most likely at the output limit (AC11) and a duplicated checklist
instruction (AC8). Details: [`docs/evidence/06_Live_User_Test_Record.md`](docs/evidence/06_Live_User_Test_Record.md).

Requirements from user validation are enforced in code, not only in the model prompt:
a reference date given by the user is always kept, with a request for the editions or
revisions used (AC7), and a coverage checklist is requested when the user asks for complete
coverage (AC8).

## Architecture

Browser (HTML + vanilla JS) → Flask JSON API (validation, rate limit, HMAC-signed prompt
versions, logging) → Google Gemini REST API (`generateContent`, `countTokens`).
Stateless server, no database. Details: [`docs/architecture.md`](docs/architecture.md).

| Path | Purpose |
|---|---|
| `app/optimizer.py` | Clarify / confirm / revise / generate logic and deterministic guards |
| `app/llm.py` | Gemini REST client and deterministic mock provider |
| `app/validation.py` | Input limits (spec section 2) |
| `app/signing.py` | HMAC signatures for prompt versions |
| `app/monitoring.py` | Request logs, `/api/stats` counters, rate limiter |
| `app/routes.py` | UI page and API endpoints |
| `docs/validation-report.md` | Idea Validation Report (7 steps, evidence, sources) |
| `docs/prd.md` | One-page PRD |
| `docs/spec.md` | Spec v1.2 with acceptance criteria AC1–AC11 ([review notes](docs/spec-review.md)) |
| `docs/reflection.md` | One-page reflection |
| `docs/evidence/` | P01 validation evidence and live-test session logs |
| `CLAUDE.md`, `.cursorrules` | Instructions for AI coding assistants |

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/analyze` | `request`, `answers[]` | `clarify` (question, options) or `confirm` (paraphrase, optimized prompt, version, signature, tokens) |
| POST | `/api/revise` | `request`, `answers[]`, `prompt`, `version`, `signature`, `feedback` | `confirm` with `version + 1` |
| POST | `/api/generate` | `prompt`, `version`, `signature` | `answer`, `version`, `truncated` |
| GET | `/api/stats` | — | usage counters (analyze, clarify, confirm, revise, generate, errors) |
| GET | `/healthz` | — | status, provider, model |

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # add GEMINI_API_KEY (or leave empty for mock mode)
set -a && source .env && set +a
flask --app wsgi run --debug    # http://127.0.0.1:5000
```

Without `GEMINI_API_KEY` the app runs with a deterministic **mock** model and shows a
"Demo mode" badge.

## Tests and CI

```bash
pytest -q          # 46 tests, no network
ruff check .
```

GitHub Actions ([`ci.yml`](.github/workflows/ci.yml)) runs on every push and pull request:
secret scan → lint → unit tests → boot smoke test. CI uses the mock provider, so it needs
no API key.

## Deploy (Render)

1. Push this repository to GitHub (public).
2. Render → **New → Blueprint** → select the repo (uses [`render.yaml`](render.yaml)).
3. Set **`GEMINI_API_KEY`** in the Render dashboard (Environment). `APP_SECRET` is
   generated by Render. Optional: `GEMINI_MODEL` (default `gemini-3.5-flash`) and
   `ANSWER_MAX_TOKENS` (default 16384).
4. Open `https://<service>.onrender.com/healthz` → `"provider": "gemini"`.

## Security

- Secrets only in environment variables; `.env` is git-ignored; CI fails on committed keys.
- The API key is sent in a request header, never in a URL or log line.
- Every request body is validated (types, lengths, control characters); bodies over 64 KB
  are rejected.
- Rate limit: 30 API requests per IP per 10 minutes.
- `/api/generate` accepts only server-signed prompt versions (HMAC-SHA256).
- Model output is HTML-escaped before rendering.

## Monitoring

- One JSON log line per request (path, status, total latency, model latency) in the Render
  log stream. No request content is logged.
- `/api/stats`: funnel counters (clarify shown → confirm shown → revise → generate) and
  error counts since the last restart.
- Render health check on `/healthz`.

## Limitations

- Answers are AI-generated and are not checked against official texts; standards and
  regulations must be verified before use.
- Very long answers can still reach the model's output limit; the app now flags them as
  truncated instead of showing them as complete.
- Counters and rate limits are in memory and reset on restart (free tier sleeps when idle;
  the first request can take ~1 minute).
- Token counts measure the prompt only. In the live test the optimized prompt was 7.5–9× longer;
  the expected saving is in fewer follow-up requests, which v1 does not yet measure.

## Roadmap

v2: coverage follow-up for "pending review" items — see [`docs/v2-issue.md`](docs/v2-issue.md)
and the GitHub issue.

## License

MIT
