---
title: "Small models, big boundaries"
date: 2026-11-19
status: approved
tag: agentic-ai
summary: "Most steps in an agent don't need the frontier model. The boundary around the step matters more than its size."
linkedin_url:
---

Most of the steps in an agentic system don't need the biggest model.

Classifying a request. Pulling fields out of a document. Formatting an answer. Deciding which tool applies. These are narrow tasks with clear inputs, and a smaller, faster model handles them well at a fraction of the cost and latency.

The expensive model earns its place at the steps that need judgment: reconciling conflicting evidence, planning a multi-step task, deciding that the right answer is "I can't do this safely."

What I've learned is that the boundary around each step matters more than the size of the model inside it. A small model with a typed input, a typed output, a validation check, and a clear failure path is more reliable than a large model with a vague prompt and permission to improvise.

So the architecture ends up looking less like one brilliant agent and more like a pipeline of narrow specialists with a planner on top. Each specialist can be swapped, evaluated, and priced on its own. The planner is where the care goes.

It's also how you stay flexible. Models change every few months. Boundaries don't have to.

Where in your system is a big model doing a small model's job?
