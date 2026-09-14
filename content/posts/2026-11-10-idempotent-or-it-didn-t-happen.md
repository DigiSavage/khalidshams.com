---
title: "Idempotent or it didn't happen"
date: 2026-11-10
status: approved
tag: agentic-ai
summary: "An agent will retry. If a write isn't safe to retry, the agent will eventually do it twice."
linkedin_url:
---

An agent will retry. That's not a bug. It's how they work.

Networks fail, tools time out, a model decides the first attempt didn't take. So the agent calls the tool again. If that tool sends an email, creates a ticket, or moves money, and the first call actually succeeded, you now have two.

On every agentic system I've built, the rule for writes is short: idempotent, or it doesn't get a tool.

Idempotent means calling it twice with the same input produces the same result as calling it once. In practice that looks like a client-supplied request id that the receiving system dedupes on, or a write that sets state rather than adds to it, or a check before the action that makes the second attempt a no-op.

It also means reversible where possible. Soft deletes. Drafts before sends. Holds before transfers. Anything that gives a human a window to catch a wrong call before it becomes permanent.

This is unglamorous work, and it's the work that decides whether you can let the system run without someone watching it.

The demo never shows the retry. Production always does.

What's the one tool in your system you'd least want called twice?
