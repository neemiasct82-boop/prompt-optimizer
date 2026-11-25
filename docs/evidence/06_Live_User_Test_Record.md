# Live user test record
23 November 2026 · P01, occupational safety technician · Two sessions on the deployed application in a private browser window. Both used Gemini 3.5 Flash. Prompt counts came from the same model’s countTokens endpoint.
## Method
P01 operated the app in both sessions. For the second session, the facilitator asked her to try “No, change something.” She supplied the date correction and confirmed the revised prompt. The exercise was conducted in Portuguese. Participant comments below are paraphrased in English.
Measure | Confirm | Guided Revise
Task | Compare Brazilian NRs with API standards and identify matches. | Build a presentation table with a worked example comparing restrictions.
Clarification | Two questions about scope, format and date. | Two questions about standards and the reference date. Initially chose a fictional example without dates.
Decision | Accepted v1. | Declined v1, requested November 2026 and accepted v2.
Version used for answer | v1 | v2
Input tokens | Original 33. Confirmed v1 301. | Original 38. Proposed v1 247. Confirmed v2 285.
Elapsed time | 2 min 22 s | 3 min 01 s
Observed output | Table and checklist. Output stopped mid-row at NR-38. | Template and worked example generated from v2.
Participant rating | 4.5/5 | No separate rating recorded.
## Participant feedback
P01 found the Confirm prompt clear and detailed and considered the answer satisfactory. She understood why the extra detail was included, although the higher input token count kept her from giving a full score. The rating reflects her experience with that session. Technical correctness and complete regulatory coverage were not independently evaluated.
## Defects and engineering response
The first answer ended mid-row without a warning. The historical session export did not record a finish reason. Commit b1a1228 handles the provider’s MAX_TOKENS signal, warns the user, increments the truncation counter and raises the configured output limit from 8,192 to 16,384. This addresses one identifiable cause of incomplete output.
The first confirmed prompt also included two requests for the coverage checklist. Commit 16f7f83 recognizes common Portuguese wording before appending the instruction. Regression tests cover both changes. P01’s two recorded sessions preceded these fixes.
## Evidence and limits
The English session summaries and event sequences accompany the demo. One participant completed two different tasks. Input counts apply to the prompt strings. Total API usage, end-to-end cost, time saved and follow-ups avoided were not measured.
