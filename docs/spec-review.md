# Spec review — v1.0 → v1.1

Date: 2026-11-20 · Method: line-by-line review of `spec.md` v1.0 against the
evidence files, the architecture notes and the Graded Assignment 4.2 brief.
Each finding was resolved in spec v1.1.

| # | Finding in v1.0 | Source | Change in v1.1 |
|---|---|---|---|
| R1 | The acceptance criterion from P01's follow-up (keep a user-specified reference date and request the editions used) was not in the spec. | `02_Prompt_Validation.txt` | New **AC7**, enforced in code by a deterministic guard, not only by the system prompt. |
| R2 | The design implication from the manual test (coverage checklist when complete coverage is requested) was missing. | `05_Prompt_Comparison_Findings.txt` | New **AC8** with the three statuses: reviewed – match; reviewed – no match identified; pending review. |
| R3 | AC4 ("generated from the confirmed prompt") could not be tested: nothing stopped a client from sending an edited prompt. | Architecture decision 1 | Inputs now include `version` and `signature`; **AC4** split into AC4a (answer reports the version used and equals the latest confirmed version) and AC4b (unsigned or edited prompt → HTTP 403). |
| R4 | The clarification loop had no bound; a model that keeps asking questions would block the user. | Edge-case review | Max **3** clarification rounds, then the model must confirm and state its assumptions (**AC1**). |
| R5 | AC5 did not say what happens when the token-count API fails. | Edge-case review | Fallback to a character-based estimate, labelled as an estimate (**AC5**). |
| R6 | AC6 said "over the limit" without numbers, so it was not testable. | Testability | Limits defined in section 4 and referenced by **AC6**. |
| R7 | Rate limiting and monitoring appeared in the architecture notes but not in the spec. | Brief, Phase 3–4 | Added to constraints; new **AC9** (rate limit) and **AC10** (stats and health endpoints). |
