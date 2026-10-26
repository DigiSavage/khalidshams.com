---
title: "Recovery needs a clock"
date: 2026-11-13
status: approved
tag: cloud
summary: "Measure the steps required to restore service and reconcile completed actions."
linkedin_url:
series: 2036
linkedin_schedule: 2036
---

My 2036 design horizon includes a fairly old-fashioned instrument: a clock.

Pick one failure. In an isolated environment, time detection, the decision to act, restoration, verification and reconciliation of any completed business actions.

Keep estimated steps visibly separate from measured ones. Include the wait for the person who has permission to restore. Their calendar is part of the recovery path.

Then compare the total with the recovery target you promised. Write down the longest untested step and schedule that exercise next.

The recovery calculator lets you inspect the arithmetic. You still have to run the drill:
<https://khalidshams.com/tools/availability/#restore>

2036, built in the open · 08

A faster model cannot recover a backup nobody tested.
