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

```
Browser                         Flask API                         Gemini
  │ 1. request text  ───────────▶ POST /api/analyze ─────────────▶ generateContent (JSON mode)
  │                               validate → rate-limit            ◀── {status: clarify | confirm}
  │ ◀── clarify: one question ─── (if clarify)
  │ 2. answer        ───────────▶ POST /api/analyze (with answers)
  │ ◀── confirm: paraphrase,  ─── deterministic guards ──────────▶ countTokens (original, optimized)
  │     optimized prompt v1,      sign(version, prompt)
  │     token counts, signature
  │ 3a. "No, change X" ─────────▶ POST /api/revise  (verify signature) ─▶ generateContent
  │ ◀── confirm v2 + signature ──
  │ 3b. "Yes" ──────────────────▶ POST /api/generate (verify signature) ─▶ generateContent (answer)
  │ ◀── answer + version used ───
```

## Key design decisions

1. **Stateless server, signed prompt versions.** The server returns each
   optimized prompt with a version number and an HMAC signature
   (`APP_SECRET`). `/api/revise` and `/api/generate` accept only prompts the
   server itself produced, so the answer is always generated from a prompt the
   user saw and confirmed, never from an edited or injected one.
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
