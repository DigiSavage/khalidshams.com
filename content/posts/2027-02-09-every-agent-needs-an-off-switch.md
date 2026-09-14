---
title: "Every agent needs an off switch"
date: 2027-02-09
status: approved
tag: agentic-ai
summary: "Not a deploy. Not a rollback. A switch someone can flip in under a minute that stops the agent acting."
linkedin_url:
---

Every agent I ship has an off switch. Not a redeploy, not a rollback. A switch someone can flip in under a minute that stops the agent from taking any action.

The reason is simple. Agents fail in ways that are fast, repetitive, and confident. A bad prompt change, a tool that starts returning garbage, a model update with a new quirk. By the time a human notices, the agent has done the wrong thing forty times and is lining up the forty-first.

A rollback takes ten minutes if everything goes well. An off switch takes ten seconds.

What that looks like on the systems I've built:

A kill flag checked before every action, read from configuration, not baked into the deploy.
A read-only mode, where the agent can still answer but every write becomes a proposal for a human.
Circuit breakers per tool, so a failing integration trips its own breaker without taking down the rest.
Rate ceilings per run and per hour, so "runaway" has a definition and a limit.

None of this is exotic. It's the same discipline we applied to payment systems and trading platforms for years. Agents just make the need for it obvious faster.

Could you stop your agent right now, from your phone?
