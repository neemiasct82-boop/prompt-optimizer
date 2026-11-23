# Reflection — Prompt Optimizer

Neemias de Carvalho Tavares · Graded Mini Project 4.2 · 2026-11-23

## What I built

Prompt Optimizer is a web app for people with little prompt-writing experience. When a
request leaves the deliverable unclear, it asks one focused question at a time. It then
confirms its understanding as a yes/no question and generates the answer only from the
prompt the user confirmed. It is live at https://prompt-optimizer-mw8t.onrender.com, runs on
Flask with the Gemini API, and has GitHub Actions CI with 46 tests.

## Key learnings

1. **The problem was intent, not wording.** P01, an occupational safety technician, did not
   need nicer phrasing. The AI needed to know the deliverable, the direction of the comparison,
   the priority NRs and the reference date. She realised her original request was unclear only
   when she read the rewrite. That moved the product from "rewrite the prompt" to "ask,
   confirm, then answer".
2. **My first hypothesis about tokens was wrong.** I started from the idea that better prompts
   use fewer tokens. In the live test, the optimized prompts were 7.5–9 times longer than the
   originals (33 → 301 and 38 → 285 tokens). P01 rated the Confirm session 4.5/5 and found
   the prompt clear, but the higher token count was her main concern. The app is worth using
   only if the first answer matches the user's intent so she needs fewer follow-up requests,
   and that is still unmeasured. The UI states this next to the token counts.
3. **Users' requirements belong in code, not only in the system prompt.** The reference date and
   the coverage checklist came from P01's feedback. Enforcing them with deterministic guards
   made them testable. Testing caught two weaknesses in those guards. One was a wording
   collision ("revisão pendente" hid a missing edition request). The other, from the live
   test, was a duplicated checklist instruction.

## Challenges

- **Proving "the answer comes from the confirmed prompt".** The server is stateless and cannot
  trust the browser, so each prompt version is signed with HMAC and edited prompts are
  rejected. In the live test, both answers came from the version P01 confirmed (v1 and v2).
- **Silent incompleteness.** P01's first answer stopped mid-row at "NR-38", most likely at the
  model's output limit (the log did not record the finish reason), and nothing warned her. Long, complete-coverage requests are exactly what this user
  asks for, so I added truncation detection and a warning, and raised the limit.
- **Small evidence base.** One participant and two tasks. The validation framework steps in the
  brief were not enumerated, so I mapped my evidence to a common seven-step structure.

## What I would improve in v2

- **Coverage follow-up** (GitHub issue #1): read the checklist and offer a confirmed follow-up
  prompt for "pending review" items, which also recovers truncated answers.
- **Measure what matters:** follow-up requests per task with and without the app, with at
  least three technicians, to test the "fewer retries" claim directly.
- **Persist anonymous usage metrics** instead of in-memory counters that reset on restart.
