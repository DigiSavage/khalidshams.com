---
title: "Small models, big boundaries"
date: 2026-11-19
status: approved
visual_required: true
tag: agentic-ai
summary: "A model swap belongs inside a tested task boundary, with explicit validation and escalation."
linkedin_url:
---

The model can get smaller. The boundary should not get vague.

For a bounded task such as classification or field extraction, I would compare a deterministic rule, a smaller model and a larger model before choosing one.

Give each candidate the same typed input, expected output, validation checks and escalation cases. Include a malformed document, missing evidence and a request outside the permitted task.

A valid JSON response is only the first check. Inspect whether the answer is correct, whether the source supports it and whether the workflow stops when it should.

Then swap the implementation behind the contract and run those cases again. Record which behavior changes before looking at the savings.

A narrow specialist may be easier to replace and operate. It still needs evidence that it can do its assigned job.

The useful unit of architecture is the task we can test, not the largest model we can afford.
