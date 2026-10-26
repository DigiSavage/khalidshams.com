---
title: "The tool contract must survive the prompt"
date: 2026-11-04
status: approved
tag: architecture
summary: "Try the protected operation directly and inspect who really enforces the boundary."
linkedin_url:
series: 2036
linkedin_schedule: 2036
---

“The agent knows not to do that” is an interesting test plan.

Here is the one I would run before building the polished interface.

Take the backend operation that stages an invoice. Send it a missing customer ID, an unknown field, an excessive amount and a request from the wrong tenant. Call it directly, without the conversational interface.

Each rejection should happen at the application boundary, with a useful reason and no business write. Keep the examples as regression tests.

Now the frontend has a working contract to present.

In my 2036 design horizon, an agent can help implement those checks. A named owner accepts the contract and its consequences.

2036, built in the open · 04
