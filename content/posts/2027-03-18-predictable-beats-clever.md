---
title: "Predictable beats clever"
date: 2027-03-18
status: approved
tag: agentic-ai
summary: "In production, an agent that does the same thing every time is worth more than one that occasionally does something brilliant."
linkedin_url:
---

In production, an agent that does the same thing every time is worth more than one that occasionally does something brilliant.

That runs against the grain of how these systems get built. The demo rewards cleverness: the moment the agent figured something out on its own. The operator running it at scale wants the opposite. They want to know what it will do before it does it.

So the systems I ship lean hard toward predictability, even at the cost of some capability.

Deterministic paths wherever the task allows it. If a request matches a known pattern, it takes the known route. The model is for the cases that don't match.
Constrained outputs. The model fills a schema; it doesn't invent a format.
Fixed tool sequences for high-stakes actions. Plan, validate, confirm, execute, in that order, every time.
Temperature set low for anything a human will act on. Creativity is for drafts, not decisions.

The result is less impressive in a demo and much easier to trust, test, and explain. When something goes wrong, you can usually say exactly which step did it.

Clever is for the prototype. Predictable is for the system people rely on.

Would you rather your agent surprised you, or bored you?
