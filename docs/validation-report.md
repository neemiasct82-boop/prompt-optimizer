# Idea Validation Report — Prompt Optimizer

Graded Mini Project 4.2 · Neemias de Carvalho Tavares · 2026-11-20 · Version 1.0

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
| E3 | Manual comparison in Claude, separate conversations (`05_Prompt_Comparison_Findings.txt`, `Comparativo_API_x_NR.pdf`) | Revised prompt → PDF organized by API standard and clause, NR-10/12/13 first, reference date 2026-11-11, source editions, separate sections for "no counterpart" and "not directly comparable". **P01 preferred Response B**, but found it incomplete because not all NRs were listed. |

**Limits of the evidence.** One participant (n = 1) and one task. Technical accuracy of the
comparison was not independently verified. Token savings were not measured in the manual test.

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

**Models do not reliably ask before answering.** Research reports that state-of-the-art LLMs
often answer ambiguous requests by assuming one interpretation instead of asking (Zhang et al.,
arXiv 2410.13788), and that adding clarifying questions improves performance across tasks
(Kuhn et al., arXiv 2311.09469). A user study found clear benefits when an AI asked follow-up
questions before writing a one-page document (Tix, arXiv 2407.12017).

## Step 5 — Why now

1. **Regulatory change makes the reference date critical in 2026–2027.** The new text of NR-10
   (Portaria MTE nº 737/2026) was published on 01/06/2026 and enters into force on 01/06/2027;
   until then, the 2004 text applies (CBIC; uai.com.br). A technician comparing requirements
   today must say which text she means — exactly the gap P01 raised.
2. **Usage is now daily, training is not.** Workers have moved from trying AI to using it
   routinely, but most skills stopped at basic prompting (Section AI survey, via Insurance
   Business). The gap is in everyday requests, not in developer tooling.
3. **The building blocks are cheap and available.** LLM APIs return structured JSON and expose
   token counting (Gemini `countTokens`), so a clarify-confirm-generate loop with transparent
   token counts can ship as a small web app in a week.

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
| T3 Live app test, Confirm and Revise flows | **To run** | P01 completes both flows; answer generated from the latest confirmed version |
| T4 Live app with ≥ 2 more technicians | **To run** | ≥ 2 of 3 rate the answer fit ≥ 4/5; median revisions ≤ 1 |
| T5 Token and usage measurement | **To run** | Record original vs optimized tokens and total requests per session in `/api/stats` |

## How user feedback changed the product

| Feedback or finding | Product change | Where |
|---|---|---|
| P01 recognized her request was unclear only after seeing the rewrite | Show the paraphrase as a yes/no question before generating | AC2, confirm card |
| Kept priorities NR-10, 12, 13 + remaining NRs | System prompt must preserve priorities and not add requirements | `ANALYZE_SYSTEM` |
| Wanted a concise table, one row per comparable requirement | Clarification options and format captured in the optimized prompt | AC1 |
| "Add an explicit comparison date" | Deterministic date guard + edition request | AC7, tests |
| Answer B incomplete: not all NRs covered | Coverage checklist with three statuses; v2 follow-up issue | AC8, `docs/v2-issue.md` |
| Confirm intent before generating; revise if declined | Confirm / Revise loop, answer only from latest signed version | AC3, AC4a, AC4b |

## Sources

- CBIC — "Nova NR-10 … entra em vigor em 2027" (08/07/2026): https://cbic.org.br/nova-nr-10-atualiza-regras-para-gestao-dos-riscos-eletricos-e-entra-em-vigor-em-2027/
- uai.com.br — "Nova NR-10 2027: o que muda na prática" (21/10/2026): https://www.uai.com.br/networking-e-negocios/2026/10/21/nova-nr-10-2027-o-que-muda-na-pratica-como-as-empresas-devem-se-preparar-desde-agora/
- Hardware.com.br — Deloitte Gen Z and Millennial Survey 2025 (Brazil): https://www.hardware.com.br/?p=315592
- Estado de Minas — FDC survey on GenAI at work (06/2025): https://em.com.br/tecnologia/2025/06/7177299-ia-generativa-no-mercado-de-trabalho-no-brasil.html
- SHRM — Salesforce GenAI Snapshot: https://rss.shrm.org/link/22135/16302148/ai-is-changing-the-skills-employers-want-from-workers.aspx
- HR Dive — Forrester AIQ: https://www.hrdive.com/news/ai-tools-productivity-forrester-aiq/816274/
- CIO Dive — Coda survey: https://www.ciodive.com/news/generative-AI-skills-upskilling-training/692196/
- Insurance Business — Section AI proficiency survey: https://www.insurancebusinessmag.com/us/news/technology/are-your-staff-any-good-at-ai-562775.aspx
- Zhang et al., "Modeling Future Conversation Turns to Teach LLMs to Ask Clarifying Questions": https://arxiv.org/abs/2410.13788
- Kuhn et al., "Clarify When Necessary": https://arxiv.org/abs/2311.09469
- Tix, "Follow-Up Questions Improve Documents Generated by Large Language Models": https://arxiv.org/abs/2407.12017
- Anthropic — Prompt improver: https://www.anthropic.com/news/prompt-improver
- OpenAI — Prompt optimizer: https://developers.openai.com/api/docs/guides/prompt-optimizer
- Prompt-Optimizer (open source): https://sourceforge.net/mirror/prompt-optimizer
- Google — Gemini API countTokens: https://ai.google.dev/api/tokens
