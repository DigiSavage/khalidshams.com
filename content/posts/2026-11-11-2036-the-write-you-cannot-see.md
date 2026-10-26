---
title: "The write you cannot see"
date: 2026-11-11
status: approved
tag: architecture
summary: "A timed-out write needs reconciliation before another attempt."
linkedin_url:
series: 2036
linkedin_schedule: 2036
---

The most interesting moment in an agent demo might be the one after the screen stops responding.

Did the write fail, or did the receipt fail to arrive?

For my 2036 design horizon, I want that uncertainty represented explicitly.

In a test environment, let a business operation commit, then interrupt its response. Retry the same logical request using the same idempotency key. Inspect the authoritative business record and the reconciliation path.

A working design should avoid a second business effect and give an operator a way to resolve the unknown result. Where the destination cannot guarantee that, pause for reconciliation.

2036, built in the open · 07

An impatient retry can be a very confident duplicate.
