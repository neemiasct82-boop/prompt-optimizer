# GitHub issue (v2) — paste into "New issue"

**Title:** v2: Coverage follow-up — detect "pending review" items and offer a completion prompt

**Labels:** enhancement, v2

**Problem (evidence).** In the manual test (`docs/evidence/05_Prompt_Comparison_Findings.txt`),
participant P01 preferred the optimized-prompt answer but found it incomplete because it
did not cover all Brazilian NRs. v1 already asks the answering AI for a coverage checklist
(AC8), but the user still has to read the checklist and write a follow-up request herself.

**Proposal.** After an answer is generated:
1. Parse the coverage checklist in the answer and count items marked
   "reviewed – match", "reviewed – no match identified" and "pending review".
2. Show a coverage bar (e.g. "NRs reviewed: 14 / 38").
3. If items are pending, offer **"Continue with pending items"**, which builds a signed
   follow-up prompt (version n+1) that lists only the pending items, keeps the reference
   date and format, and asks the user to confirm before generating.

**Acceptance criteria.**
- Given an answer whose checklist has pending items, the UI shows the counts and the
  continue button.
- The follow-up prompt contains only the pending items and the original reference date.
- Given an answer with no checklist, no coverage bar is shown.

**Out of scope.** Verifying the technical accuracy of each comparison.
