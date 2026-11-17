---
title: "Why did it do that"
date: 2026-12-08
status: approved
visual_required: true
tag: agentic-ai
summary: "An agent trace should preserve observable decision evidence without pretending to expose the model's private reasoning."
linkedin_url:
---

"Why did it do that?" needs a better answer than a plausible story after the event.

For an agent workflow, I want a record of observable evidence: the request and its version, approved source references, permission decisions, tool inputs and outcomes, resulting state changes, and cost.

That record can show what the system received and what it did. It does not reveal a model's private reasoning or prove that its explanation caused the action.

Take a synthetic run where a source changes between drafting and execution. Inspect whether the trace connects the final action to the evidence and approval that were actually current.

Capture only what the investigation needs. Sensitive content needs appropriate access, redaction and retention; collecting everything creates another system to protect.

Keep a compact evidence bundle with the evaluation case. Use it to test a change and distinguish a reproduced failure from a convincing explanation.

An audit trail is a witness. It is not a mind reader.
