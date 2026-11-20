# PRD — Prompt Optimizer v1

Owner: Neemias de Carvalho Tavares · 2026-11-20 · Status: built, live test pending

**1. Problem.** Occupational safety technicians describe a topic but leave the deliverable
implicit, so the AI answers a different question and they must revise and ask again. In the
observed case (P01), the original prompt produced an explanation instead of a clause-by-clause
comparison with a reference date; the clarified prompt produced the comparison she preferred.

**2. Target user.** Occupational safety technicians in Brazil with limited prompt-writing
experience who use AI chat tools for regulation and standards research (Portuguese first).

**3. Goals and success metrics.**

| Goal | Metric (from `/api/stats` and user tests) | v1 target |
|---|---|---|
| Answers match intent | User rating of answer fit (1–5) | ≥ 4 for 2 of 3 testers |
| Few correction loops | Revisions per generated answer | median ≤ 1 |
| Flow is completed | generate ÷ confirm_shown | ≥ 60% |
| Transparency | Confirmations showing token counts | 100% |

**4. Core features and acceptance criteria** (full list: `docs/spec.md`, AC1–AC10)

| Feature | Testable acceptance criterion |
|---|---|
| F1 Clarify | Ambiguous request → one focused question before any prompt; after 3 rounds → confirmation with stated assumptions (AC1) |
| F2 Confirm | Clear request → paraphrase as yes/no question + original and optimized prompts side by side (AC2) |
| F3 Revise | "No, change something" + correction → next confirmation reflects it, version + 1 (AC3) |
| F4 Generate | "Yes" on version *n* → answer from version *n*, no retyping; edited or unsigned prompt → HTTP 403 (AC4a/b) |
| F5 Token counts | Input tokens for original and optimized prompt, same model; labelled estimate on fallback (AC5) |
| F6 Domain guards | User's reference date kept + editions requested (AC7); coverage checklist when full coverage requested (AC8) |

**5. Out of scope (v1).** User accounts and saved history; verifying the technical accuracy of
answers; uploading regulation files; measuring follow-up requests saved; payments.

**6. Constraints, risks and dependencies.** Stack: Flask + vanilla JS, Google Gemini API,
Render, GitHub Actions. Secrets only in environment variables; 30 requests/IP/10 min. Risks:
model may ask unnecessary questions (mitigated by the 3-round cap); answers may be outdated
(disclaimer, reference date, editions); free tier sleeps when idle; evidence so far from one
participant.
