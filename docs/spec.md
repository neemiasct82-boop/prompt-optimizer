# spec.md — Prompt Optimizer (v1.2)

Status: v1.1 revised after review; v1.2 after the live test with P01 (see `docs/spec-review.md`) ·
Owner: Neemias de Carvalho Tavares · Date: 2026-11-23

## 1. Objective and AI capability

Help occupational safety technicians in Brazil, who have little experience
writing prompts, turn an unclear request into a precise prompt **before** an
AI assistant answers it.

AI capability: **generation with clarification** (LLM-based). The model
(1) decides whether the deliverable and scope are clear, (2) asks one focused
question when they are not, (3) rewrites the request as an optimized prompt
and presents it as a yes/no confirmation, and (4) after confirmation,
generates the answer from the confirmed prompt.

Evidence base: `docs/evidence/01_Problem_Hypothesis.txt`,
`02_Prompt_Validation.txt`, `05_Prompt_Comparison_Findings.txt` (participant P01).

## 2. Inputs

| Input | Endpoint | Type | Rules |
|---|---|---|---|
| `request` | analyze, revise | string | Required. 10–4,000 characters after trimming. Any language. |
| `answers` | analyze, revise | list of {question, answer} | 0–5 items; each field ≤ 1,000 characters. |
| `prompt` | revise, generate | string | ≤ 8,000 characters. Must be a prompt issued by the server. |
| `version` | revise, generate | integer | 1–50. |
| `signature` | revise, generate | hex string | HMAC-SHA256 of `version` + `prompt` with `APP_SECRET`. |
| `feedback` | revise | string | 3–1,000 characters. What should change. |

## 3. Outputs

| Output | When | Content |
|---|---|---|
| Clarification `{status: "clarify"}` | Deliverable, scope or reference date unclear, and fewer than 3 rounds used | One focused question in the user's language, optional 2–4 options, and the gap it resolves. |
| Confirmation `{status: "confirm"}` | Request is clear, or 3 rounds used | Paraphrase as a yes/no question; optimized prompt; `version`; `signature`; token counts for original and optimized prompts (same model) and the counting method; assumptions made. |
| Revised confirmation | User declines and explains | Same as confirmation with `version + 1`, reflecting the correction. |
| Answer | User confirms | Answer text (Markdown), the `version` it was generated from, and `truncated` (true if the model hit its output length limit). |
| Error | Invalid input, bad signature, rate limit, provider failure | HTTP 400 / 403 / 429 / 502 with a readable `error` message. |

## 4. Constraints and edge cases

- The optimized prompt preserves the user's goal, priorities, output format
  and constraints, and must not add requirements the user did not state or imply.
- Same language as the user's request.
- A reference date stated by the user (YYYY-MM-DD or DD/MM/YYYY) must appear
  in the optimized prompt; when the topic is standards or regulations, the
  prompt requests the editions or revisions used and marks unverifiable ones
  as "Unverified".
- When the user asks for complete coverage of a set ("all NRs"), the prompt
  requests a coverage checklist.
- Secrets only in environment variables (`GEMINI_API_KEY`, `APP_SECRET`).
- Rate limit: 30 API requests per IP per 10 minutes (per process).
- Provider timeouts: 60 s for analyze/revise, 180 s for answers.
- Answer output limit: 16,384 tokens (`ANSWER_MAX_TOKENS`).

## 5. Acceptance criteria

- **AC1 Clarify:** Given an ambiguous request (topic without deliverable), the
  app returns one focused question before any prompt. After 3 answered
  rounds it returns a confirmation that lists its assumptions.
- **AC2 Confirm:** Given a clear request, the app shows the paraphrase as a
  yes/no question with the original and optimized prompts side by side.
- **AC3 Revise:** Given the user declines and writes a correction, the next
  confirmation reflects that correction and has `version + 1`.
- **AC4a Generate:** Given the user confirms version *n*, the answer is
  generated from prompt version *n* without asking the user to repeat the
  request, and the response reports `version = n`.
- **AC4b Integrity:** Given a prompt whose text or version does not match its
  signature, `/api/generate` and `/api/revise` return HTTP 403.
- **AC5 Tokens:** Each confirmation shows input token counts for the original
  and optimized prompts from the same reference model; if the provider count
  fails, a character-based estimate is shown and labelled `estimate`.
- **AC6 Validation:** Input outside the limits in section 2 returns HTTP 400
  with a message naming the field.
- **AC7 Reference date (P01):** Given a standards comparison request with a
  user-specified reference date, the optimized prompt retains that date and
  requests the editions or revisions used.
- **AC8 Coverage (P01 test):** Given a request for complete coverage, the
  optimized prompt asks for a coverage checklist with each item marked
  reviewed – match, reviewed – no match identified, or pending review.
- **AC9 Rate limit:** The 31st API request from one IP within 10 minutes
  returns HTTP 429.
- **AC10 Monitoring:** `/healthz` returns status, provider and model;
  `/api/stats` returns request counters including confirm and revise counts.
- **AC11 Truncated answer (live test):** Given the model stops because of its output
  length limit, the response has `truncated = true`, the UI warns the user, and
  `/api/stats` counts `answer_truncated`.
