---
title: "Retrieval is not memory"
date: 2026-10-29
status: approved
tag: agentic-ai
summary: "Teams say their agent has memory when it has retrieval. The difference decides what you can trust."
linkedin_url:
---

Teams often say their agent "has memory" when what it has is retrieval.

The difference matters more than it sounds.

Retrieval is looking something up at the moment it's needed. The source stays where it lives, governed, versioned, and owned by whoever owns it. If the source changes, the next answer changes with it.

Memory is the agent keeping its own copy of something it saw earlier. The moment that copy exists, you have a second source of truth. Nobody governs it. Nobody knows when it goes stale. And the agent will happily prefer it because it's faster and closer.

On the systems I've built, the rule is simple. Facts about the world are retrieved, never remembered. What the agent may remember is narrow: the state of the current task, user preferences that were explicitly given, and decisions already made in this session. Everything else is a lookup with provenance attached.

That rule costs a little latency. It buys you the ability to say, for any answer, where it came from and whether it's current.

In regulated environments, that's the whole ballgame. An answer you can't trace is an answer you can't defend.

What does your agent remember that it should be looking up?
