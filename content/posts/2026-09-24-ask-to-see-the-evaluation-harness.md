---
title: "Ask to see the evaluation harness"
date: 2026-09-24
status: approved
tag: agentic-ai
summary: "The one question that separates real AI projects from expensive demos."
linkedin_url:
---

One question separates real AI projects from expensive demos:

"Can you show me your evaluation harness?"

Not the demo. Not the architecture diagram. The harness — the thing that runs a fixed set of cases and tells you whether today's version is better or worse than last week's.

If the answer is a pause, you're looking at a prototype wearing production clothes.

Here's why it matters. Every change to an agentic system — a prompt, a tool, a model version, a retrieval tweak — has an unknown blast radius. Without a regression suite you aren't iterating. You're gambling and calling it iteration.

What I look for:

A fixed case set that includes the ugly inputs, not just the happy path.
A written catalogue of known failure modes.
Groundedness and citation checks, so "confident" and "correct" don't get confused.
At least one number that moves when quality moves.

None of this needs exotic tooling. It needs deciding that quality is measurable before you're under pressure to ship.

The teams that build this early ship faster later. Consistently.

What do you actually measure on your AI systems?
