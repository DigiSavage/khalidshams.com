---
title: "The demo is never the hard part"
date: 2026-09-15
status: approved
tag: agentic-ai
summary: "Most agent demos work. Most agent systems don't. The four things nobody demos are the whole difference."
linkedin_url:
---

Most agent demos work. Most agent systems don't.

I've spent the last stretch building a complete agentic system on Anthropic's Claude platform, inception through delivery, and separately building agentic workflows in Azure AI Foundry with RAG grounding over governed data.

The gap between a demo and a system isn't model quality. It's four things nobody demos.

Agent boundaries. What each agent owns, where control passes, and where a human stays in the loop. Vague ownership is how an agent quietly does the wrong thing, confidently.

Grounding. If the data underneath isn't governed, the agent is fluent and wrong. Retrieval without provenance is a liability, not a feature.

Evaluation. Not "it looked good in the demo." A harness, a regression suite, and a written catalogue of failure modes. If you can't measure a regression, you can't safely ship a change.

Blast radius. Typed and validated tool calls. Writes that are idempotent and reversible. Fallback paths. Cost controls per run.

None of that is glamorous. All of it is the difference between a pilot and something people depend on.

If you're evaluating an agentic project right now, ask one question: what happens when it's wrong?

The answer tells you whether it's ready.
