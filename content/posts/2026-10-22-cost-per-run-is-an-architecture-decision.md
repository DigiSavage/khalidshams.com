---
title: "Cost per run is an architecture decision"
date: 2026-10-22
status: approved
tag: agentic-ai
summary: "A license costs the same whether people use it or not. An agent costs more the better it works."
linkedin_url:
---

A license costs the same whether people use it or not. An agent costs more the better it works.

That single difference changes how you have to design.

With traditional software, adoption is the goal and cost is fixed. With agentic systems, adoption is the goal and cost scales with it, sometimes faster than linearly, because successful agents get asked harder questions and take more steps to answer them.

So cost per run has to be an architecture decision, not a finance surprise.

What that looks like in practice on the systems I've built:

A token budget per run, enforced, with a graceful stop rather than a runaway loop.
Model routing. Most steps don't need the frontier model. Classification, extraction, and formatting can run on something smaller and faster, with the expensive model reserved for the steps that need judgment.
Caching where the inputs are stable. Repeated retrievals over the same documents are pure waste.
A hard ceiling on tool calls, retries, and recursion depth.
A cost line on the same dashboard as the quality line, so nobody optimises one without seeing the other.

The teams that skip this ship a pilot that everyone loves and a bill that nobody approved.

Do you know what your most expensive single run last week cost?
