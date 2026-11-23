# Live User Test Record — Prompt Optimizer

Test T3 of the Idea Validation Report · Date: 2026-11-23 (local time 00:59–01:52, UTC−3)

| Field | Value |
|---|---|
| Participant | P01, occupational safety technician (same participant as E1–E3) |
| Operated by | P01 (she typed every request, answer and correction; the facilitator did not suggest wording) |
| Environment | Deployed app https://prompt-optimizer-mw8t.onrender.com in a private (InPrivate) browser window |
| Model | `gemini-3.5-flash`; token counts from the Gemini `countTokens` endpoint |
| Raw evidence | `live-test/session-1-confirm.json`, `live-test/session-2-revise.json` (session logs exported from the app), screen recordings (edited into the demo video `docs/demo/Prompt_Optimizer_Demo_2min.mp4`) |

## Results

| Measure | Session 1 — Confirm flow | Session 2 — Revise flow |
|---|---|---|
| Original request (Portuguese, summarised) | What is similar between Brazilian NRs and API standards; which NRs compare to API | How to build a table of NR vs API restrictive points for a work presentation |
| Clarifying questions asked | 2 (format and scope; reference date) | 2 (which standards; reference date) |
| Revise used | No | Yes, once: "use data comparativa referente ao mês de novembro 2026" |
| Confirmed version → answer version | v1 → v1 | v2 → v2 (**AC4a met**) |
| Input tokens, original → optimized | 33 → 301 | 38 → 247 (v1) → 285 (v2) |
| Reference date in confirmed prompt (AC7) | Yes — November 2026, with editions requested | Yes — added by the correction |
| Coverage checklist (AC8) | Yes (requested "all NRs") — but duplicated, see L2 | Not applicable |
| Time from request to answer | 2 min 22 s | 3 min 01 s |
| Answer | 13,635 characters, table + checklist; **cut off at "NR-38"**, see L1 | 5,297 characters, template + worked example |
| Participant rating | **4.5 / 5** | Not recorded |

## Observations

- Both flows worked end to end on the deployed app with the real model. Each answer was
  generated from the version P01 had just confirmed.
- In session 2, P01 first chose a fictional example "without dates". When she read the
  confirmation, she declined it and added November 2026 as the reference date. The
  confirmation step caught the gap before an answer was generated.
- The optimized prompts were 7.5–9.1 times longer than the originals. The input-token saving
  in the first hypothesis did not happen. What the app gains is an answer that matches
  the user's intent without extra follow-up requests.

## Participant feedback

P01 operated the application in both sessions. She rated the Confirm session **4.5/5**. She
found the optimized prompt clear and detailed and considered the answer satisfactory. Her
concern was the higher input token count, although she understood why the extra detail was
included. No separate rating was recorded for the Revise session. In both sessions the
optimized prompt used more input tokens than the original request; total token use per task
was not measured.

## Issues found and fixes

| # | Issue observed | Severity | Fix (commit) | Retested |
|---|---|---|---|---|
| L1 | Session 1 answer stopped mid-row at "NR-38", and the app did not tell P01 it was incomplete. The v1 session log does not record the model's finish reason, so the cause is inferred, not proven: a 13,635-character answer is consistent with the 8,192-token output limit | High — silent incompleteness | `fix: flag answers cut off by the model's length limit (AC11)` — records the finish reason, truncation flag, UI warning, counter, answer limit 8,192 → 16,384 tokens | Unit/API tests (`test_answer_cut_by_length_limit_is_flagged`, `test_gemini_client_reports_finish_reason`) |
| L2 | The optimized prompt asked for the coverage checklist twice (model's Portuguese wording + guard) | Low — redundant tokens | `fix: stop duplicating the coverage checklist instruction (AC8)` | Unit test (`test_checklist_not_duplicated_when_model_wrote_it_in_portuguese`) |
