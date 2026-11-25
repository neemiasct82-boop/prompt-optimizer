# Architecture notes — Prompt Optimizer

## Components

| Layer | Technology | Responsibility |
|---|---|---|
| UI | Single HTML page + vanilla JS (`app/templates/index.html`, `app/static/`) | Request form, clarification card, confirmation card (side-by-side prompts + token counts), Confirm / Revise buttons, answer view. Holds the conversation state in the browser. |
| Backend | Python 3.12 + Flask (`app/`), served by Gunicorn | JSON API, input validation, rate limiting, prompt-version signing, request logging and usage counters. Stateless: no database. |
| AI layer | Google Gemini API over REST (`app/llm.py`) | `generateContent` for clarify / confirm / revise / answer; `countTokens` for input token counts. A deterministic mock provider is used in tests and when no key is configured. |
| Hosting | Render web service (`render.yaml`) | HTTPS URL, environment variables for secrets, health check. |
| CI | GitHub Actions (`.github/workflows/ci.yml`) | Lint, unit tests with the mock provider, secret scan on every push and pull request. |

## Data flow

1. The browser submits the original request to /api/analyze. Flask validates the request and asks Gemini to identify any missing detail.
2. The browser displays a focused question. The user’s answer returns to /api/analyze. The server applies the date and coverage rules, counts both prompts and returns the confirmation question and signed prompt version.
3. Revise sends the correction to /api/revise. A successful revision returns a new prompt version and signature for review.
4. Confirm sends the accepted text, version and signature to /api/generate. After verification, the server uses that prompt to generate the answer and returns its version.

## Key design decisions

1. **Stateless server, signed prompt versions.** The server returns each
   optimized prompt with a version number and an HMAC signature
   (`APP_SECRET`). `/api/revise` and `/api/generate` accept only prompts the
   server itself produced, so changing the prompt text or version without a matching signature fails verification. The browser presents the confirmation action to the user.
2. **Deterministic guards after the LLM.** Requirements that came from user
   validation (P01) are enforced in code, not only in the system prompt:
   a reference date stated by the user is kept in the optimized prompt, and a
   coverage checklist is requested when the user asks for complete coverage.
3. **Mock provider.** CI and local development run without a key and without
   network. Production uses Gemini; `/healthz` reports which provider is active.
4. **Token counts from the provider.** `countTokens` on the reference model;
   if it fails, a labelled character-based estimate (≈ 4 characters/token) is shown.

## Security

- Secrets (`GEMINI_API_KEY`, `APP_SECRET`) only in environment variables;
  `.env` is git-ignored; CI fails if a Google API key pattern is committed.
- Input validation on every endpoint (type, length, control characters).
- Per-IP rate limit on API routes to protect the API quota.
- Model output is rendered with HTML escaping in the browser.

## Monitoring

- One JSON log line per request (path, status, latency, provider latency),
  visible in the Render log stream.
- `GET /api/stats`: in-memory counters (analyze, clarify, confirm, revise,
  generate, errors) — a basic funnel of Confirm vs Revise.
- `GET /healthz`: liveness plus active provider and model.
