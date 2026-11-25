# Idea Validation Report — Prompt Optimizer

Graded Mini Project 4.2 · Neemias de Carvalho Tavares · 2026-11-23 · Updated 25 November 2026

> **One-line idea.** Prompt Optimizer asks a focused question when a request leaves the
> deliverable or scope unclear, confirms its understanding with the user, and only then
> generates the answer from the confirmed prompt.

## Step 1 — Problem statement

When users describe a topic without stating the deliverable, the AI answers a different
question. The user then has to notice the gap, rewrite the request and ask again.

**Observed case (P01, 2026-11-11).** An occupational safety technician asked an AI about
Brazilian Regulatory Standards (NRs) and American Petroleum Institute (API) standards. She
gave context but left the expected deliverable implicit. Her real intent was a comparison
that starts from API standards, finds comparable NR requirements, and says which one is more
restrictive and why — prioritizing NR-10, NR-12 and NR-13. *(Evidence E1)*

**Consequence.** With her original prompt, Claude explained NRs and API standards with
examples but produced no clause-by-clause comparison, no reference date and no source
editions. *(Evidence E3)*

## Step 2 — Target user

| Attribute | Description |
|---|---|
| Who | Occupational safety technicians in Brazil |
| Context | Use AI chat tools for work research: regulations, standards, comparisons |
| Skill gap | Limited experience writing prompts; write the topic, not the task |
| Stakes | Regulations change over time; an answer without a reference date or source edition can be outdated or wrong |
| Language | Portuguese first |

Why this user first: the cost of an off-target answer is high (compliance decisions), and
the requests have a clear structure (scope, priority standards, reference date, format) that
a clarifying question can recover.

## Step 3 — Problem evidence from a real user

| ID | Evidence | Finding |
|---|---|---|
| E1 | Problem hypothesis and observed prompt (`01_Problem_Hypothesis.txt`) | Context given, deliverable implicit. Intended task, scope and constraints confirmed with P01. |
| E2 | Side-by-side review of original vs rewritten prompt (`02_Prompt_Validation.txt`) | Intent match **partial**: reading the rewrite helped P01 see that her original request was unclear. She approved the table format and asked for an explicit reference date "because the information may change over time". |
| E3 | Manual comparison in Claude, separate conversations (`05_Prompt_Comparison_Findings.txt`, `API_NR_Comparator_EN.pdf`) | Revised prompt → PDF organized by API standard and clause, NR-10/12/13 first, reference date 2026-11-11, source editions, separate sections for "no counterpart" and "not directly comparable". **P01 preferred Response B**, but found it incomplete because not all NRs were listed. |
| E4 | Live test of the deployed app, operated by P01 (`06_Live_User_Test_Record.md`, two session logs, screen recordings) | Both flows completed with the real model. P01 rated the Confirm session 4.5/5 (clear, detailed prompt; satisfactory answer) and raised the higher token count as her concern. In session 2, P01 declined the first confirmation and added "November 2026" as the reference date; the answer came from the corrected v2. Optimized prompts were 7.5–9× longer than the originals. Two defects found and fixed (truncated answer; duplicated checklist instruction). |

**Limits of the evidence.** One participant (n = 1) across three sessions. Technical accuracy
of the comparisons was not independently verified. Follow-up requests saved were not measured.

## Step 4 — Market evidence

**Adoption is high and outpaces training.**
- Brazil: more than 70% of Gen Z and Millennial professionals use GenAI at work, but only 29%
  report any formal training (Deloitte Gen Z and Millennial Survey 2025, as reported by
  Hardware.com.br). A Fundação Dom Cabral survey found 73% of respondents already use GenAI at
  work (Estado de Minas, 2025).
- Global: 62% of 4,135 full-time workers said they lack the skills to use GenAI effectively and
  safely, and 53% don't know how to get the most value from it (Salesforce, via SHRM). Awareness
  of prompt engineering rose only from 22% (2024) to 26% (2025) (Forrester AIQ, via HR Dive).
  More than half of employees given AI tools had to work out how to use them on their own
  (Coda survey, via CIO Dive).

**Relevance to the target user.** The cited surveys provide workplace context. Interviews and Prompt Optimizer sessions involved one Brazilian technician. Her evidence establishes a specific use case. The prevalence of this need among other technicians remains to be measured.

## Step 5 — Why now

P01 requested a reference date because standards can change. Her initial prompt omitted it. During the live revision trial, she added November 2026 only after seeing the proposed prompt. This gives the confirmation step a concrete purpose today. The Gemini API also provides a counting endpoint that makes the input-token trade-off visible before generation.

## Step 6 — Existing alternatives and differentiating angle

| Alternative | What it does | Gap for this user |
|---|---|---|
| Asking the chat assistant directly | Answers immediately | Often assumes one interpretation; no confirmation step |
| Anthropic Console prompt improver | Refines prompt templates for developers | Developer console; rewrites, does not interview the end user |
| OpenAI prompt optimizer | Optimizes prompts in the API dashboard | Developer dashboard; rewrites, does not interview the end user |
| Open-source Prompt-Optimizer | Multi-model rewriting with original vs optimized comparison | Rewrites without asking what the user meant; no domain guards |
| Prompt-writing training | Builds skill over time | Slow; does not help at the moment of the request |

**Differentiating angle — "ask, confirm, then answer" for non-developers.**
1. **Interview before rewrite:** one focused question at a time (max 3), with quick options.
2. **Confirmation contract:** the answer is generated only from the prompt the user confirmed
   (signed prompt versions); "No, change something" loops until it is right.
3. **Domain guards learned from users:** keep the user's reference date and request source
   editions (AC7); request a coverage checklist when the user expects complete coverage (AC8).
4. **Transparency:** original vs optimized prompt side by side with input token counts from the
   same model. Side-by-side comparison exists elsewhere; the combination with clarification and
   confirmation for Portuguese-speaking safety professionals does not, in the tools reviewed.

## Step 7 — Riskiest assumption and validation plan

**Riskiest assumption.** Users will accept one or two extra steps (answer a question, confirm a
paraphrase) because the final answer fits their need better and saves follow-up requests.

| Test | Status | Result / success criterion |
|---|---|---|
| T1 Prompt review with P01 | Done (E2) | Partial intent match; feedback adopted (date, table format) |
| T2 Manual A/B answer comparison | Done (E3) | P01 preferred B (optimized); incomplete NR coverage → AC8 |
| T3 Live app test, Confirm and Revise flows | **Done (E4)** | Met: P01 completed both flows; answers came from v1 and v2, the versions she confirmed; Confirm session rated 4.5/5. Guided Revise had no separate rating. Two defects found and fixed. |
| T4 Live app with ≥ 2 more technicians | Open (v2) | ≥ 2 of 3 rate the answer fit ≥ 4/5; median revisions ≤ 1 |
| T5 Token measurement | **Done (E4)** | Input tokens 33 → 301 and 38 → 285 (Gemini `countTokens`). Input-token saving **not** supported; the claim was narrowed to fewer follow-up requests, to be measured in T4. |

## How user feedback changed the product

| Feedback or finding | Product change | Where |
|---|---|---|
| P01 recognized her request was unclear only after seeing the rewrite | Show the paraphrase as a yes/no question before generating | AC2, confirm card |
| Kept priorities NR-10, 12, 13 + remaining NRs | System prompt must preserve priorities and not add requirements | `ANALYZE_SYSTEM` |
| Wanted a concise table, one row per comparable requirement | Clarification options and format captured in the optimized prompt | AC1 |
| "Add an explicit comparison date" | Deterministic date guard + edition request | AC7, tests |
| Answer B incomplete: not all NRs covered | Coverage checklist with three statuses; v2 follow-up issue | AC8, `docs/v2-issue.md` |
| Confirm intent before generating; revise if declined | Confirm / Revise loop, answer only from latest signed version | AC3, AC4a, AC4b |
| Live test: answer cut off at "NR-38" without warning (likely output limit) | Truncation flag, UI warning, higher output limit | AC11, `fix:` commit |
| Live test: checklist instruction duplicated in the prompt | Guard recognises Portuguese wording | AC8, `fix:` commit |
| Live test: prompts 7.5–9× longer than originals; P01's main concern | UI explains that the goal is fewer follow-ups, not shorter prompts; hypothesis narrowed | README, reflection |

## Sources

- Hardware.com.br — Deloitte Gen Z and Millennial Survey 2025 (Brazil): https://www.hardware.com.br/?p=315592
- Estado de Minas — FDC survey on GenAI at work (06/2025): https://em.com.br/tecnologia/2025/06/7177299-ia-generativa-no-mercado-de-trabalho-no-brasil.html
- SHRM — Salesforce GenAI Snapshot: https://rss.shrm.org/link/22135/16302148/ai-is-changing-the-skills-employers-want-from-workers.aspx
- HR Dive — Forrester AIQ: https://www.hrdive.com/news/ai-tools-productivity-forrester-aiq/816274/
- CIO Dive — Coda survey: https://www.ciodive.com/news/generative-AI-skills-upskilling-training/692196/
- Anthropic — Prompt improver: https://www.anthropic.com/news/prompt-improver
- OpenAI — Prompt optimizer: https://developers.openai.com/api/docs/guides/prompt-optimizer
- Prompt-Optimizer (open source): https://sourceforge.net/mirror/prompt-optimizer
- Google — Gemini API countTokens: https://ai.google.dev/api/tokens
