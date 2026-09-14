---
title: "Prompts are config, not code"
date: 2027-01-19
status: approved
tag: agentic-ai
summary: "Treat prompts like configuration: versioned, reviewed, tested, and rolled back when they break something."
linkedin_url:
---

Prompts are configuration, and most teams manage them like sticky notes.

A change to a system prompt can change what an agent refuses to do, how it handles an edge case, what it cites, and how much it costs per run. That's a production change. In a lot of teams it gets made by editing a string in a file, or worse, in a console, with no record of what it used to say.

On the systems I've delivered, prompts get the same treatment as any other configuration that can break production.

They live in version control, separate from the code that loads them, so a prompt change is its own reviewable diff.
Every change runs against the evaluation harness before it merges. If the fixed case set gets worse, it doesn't ship.
They carry a version identifier that gets written into every trace, so when a run misbehaves you know which prompt it ran under.
Rollback is one commit, not an archaeology exercise.

None of this slows the team down. It speeds them up, because they can change prompts confidently instead of nervously. Fear is the slowest thing in any delivery.

Who reviewed your last prompt change?
