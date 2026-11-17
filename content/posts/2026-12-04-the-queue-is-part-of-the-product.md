---
title: "The queue is part of the product"
date: 2026-12-04
status: approved
tag: reliability
summary: "A task deadline includes waiting, execution and review, so queued work needs age and expiry controls."
linkedin_url:
visual_required: true
---

The model responds quickly. The task spends most of its life waiting.

A queue is part of the customer's experience, even when it is absent from the demo.

For a time-sensitive workflow, I would budget the whole path: intake, queue wait, execution, review and confirmation. Show the oldest pending request alongside throughput.

Define when work becomes stale, who may cancel it, and whether retrying is still appropriate. More workers cannot rescue a request whose authority or usefulness has expired.

Exercise a burst in an isolated environment. Hold a dependency unavailable, then restore it. Inspect which tasks resume, expire or require a new decision.

Keep estimated capacity separate from measured results.

A queue is a plan for later. Later needs a definition.
