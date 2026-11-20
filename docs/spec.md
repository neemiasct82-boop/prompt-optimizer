# spec.md — Prompt Optimizer (v1.0)

Status: draft for review · Owner: Neemias de Carvalho Tavares · Date: 2026-11-20

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

| Input | Type | Rules |
|---|---|---|
| `request` | text, any language | Required. User's original request. |
| `answers` | list of {question, answer} | Answers to clarification questions. |
| `feedback` | text | What the user wants changed after declining a confirmation. |
| `prompt` | text | Optimized prompt the user confirmed. |

## 3. Outputs

| Output | When | Content |
|---|---|---|
| Clarification | Deliverable or scope unclear | One focused question in the user's language. |
| Confirmation | Request is clear | Paraphrase as a yes/no question; optimized prompt; original and optimized prompts side by side with estimated input token counts. |
| Revised confirmation | User declines and explains | New paraphrase and prompt reflecting the correction. |
| Answer | User confirms | Answer generated from the confirmed prompt. |

## 4. Constraints and edge cases

- The optimized prompt preserves the user's goal, priorities, output format
  and constraints. It must not add requirements the user did not state.
- Same language as the user's request.
- API key only in environment variables; never in the client or the repo.
- Empty or very long input is rejected with a clear message.
- If the AI provider fails, the user sees an error and can retry.

## 5. Acceptance criteria

- **AC1 Clarify:** Given an ambiguous request (topic without deliverable),
  the app asks one focused question before showing a prompt.
- **AC2 Confirm:** Given a clear request, the app shows a paraphrase as a
  yes/no question with the original and optimized prompts side by side.
- **AC3 Revise:** Given the user declines and says what to change, the next
  confirmation reflects that correction.
- **AC4 Generate:** Given the user confirms, the answer is generated from the
  confirmed prompt without asking the user to repeat the request.
- **AC5 Tokens:** Each confirmation shows an estimated input token count for
  the original and the optimized prompt for the same reference model.
- **AC6 Validation:** Empty input or input over the limit returns HTTP 400.
