# Reflection
## What I built
My starting point was a safety technician’s request about Brazilian regulations and API standards. Her first prompt named the topic, but the answer she wanted was a comparison organized by API clause. I built Prompt Optimizer to ask what the user needs, show a rewritten prompt and wait for confirmation before generating the answer.
## What the two live sessions taught me
P01 rated Confirm 4.5/5. She found the prompt clear and detailed and the answer satisfactory. The extra detail came at a cost she noticed: the original request used 33 input tokens and the confirmed prompt used 301. In the guided Revise session, the first rewrite used 247 tokens. After she added November 2026, the confirmed version used 285, compared with 38 for her original request. She did not give that session a separate rating.
My initial expectation of shorter prompts did not hold for either task. The most useful moment came when P01 read the second confirmation and changed the date before generation. The test captured that correction. It did not measure total tokens per task, the number of follow-up requests saved, or the accuracy of the standards comparison.
## Engineering challenges
The browser holds the conversation state. I used a signed prompt version so the server can check that the text submitted for generation matches a version it issued. The logs showed answers generated from v1 and v2 respectively.
The first answer stopped in the middle of the NR-38 row. Its log contained no finish reason. I added handling for the provider’s output-limit signal, a visible warning and a counter. Raising the output limit gives long answers more room. A separate regression test covers a duplicated checklist instruction when the model already wrote it in Portuguese.
## What I would change next
I would test matched tasks with and without the app, counterbalance their order and record answer fit, follow-ups, completion and total token use. The next trial should include at least two additional technicians. I would also let a user review outstanding checklist items and confirm a targeted follow-up before generating more text (issue #1).
