---
title: "The fallback needs a smaller promise"
date: 2026-11-25
status: approved
tag: reliability
summary: "A degraded mode should state which outcomes remain possible and which actions must stop."
linkedin_url:
visual_required: true
---

"We have a fallback" leaves a surprisingly large amount of architecture unspecified.

If the approved source is unavailable, can the assistant still answer? If the execution service is down, can it still accept a request?

I would write a smaller promise for each degraded mode: what remains available, what becomes read-only, what queues, and what stops.

Put the owner and recovery condition beside each promise. A queue also needs an expiry rule so yesterday's request does not execute unexpectedly tomorrow.

Test the dependency failure, then its return. Inspect both the response to the person and any deferred business action.

The fallback may legitimately do less. Its interface should make that reduction obvious.

Availability is more useful when everyone agrees on what is available.
