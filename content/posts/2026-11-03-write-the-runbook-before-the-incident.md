---
title: "Write the runbook before the incident"
date: 2026-11-03
status: approved
tag: engineering
summary: "The resiliency posture everyone described in the room was not the one the system actually had."
linkedin_url:
---

During a database escalation, I asked what the resiliency posture was.

Three people answered. All three were confident. None of them agreed with each other, and none of them matched what was actually configured.

That's not a knock on the team. It's what happens when the runbook lives in people's heads. Each person carries the version from the last time they touched the system, and the system kept changing after that.

The fix was not more capacity. It was writing down, in one place, what was actually true. Which failover was configured and tested, which was configured and never tested, and which was a slide from the original design that never got built. Then what to do, in order, when each of the likely failures happened.

It took a day. It was the most valuable day of the engagement.

The uncomfortable part of runbooks is that writing one forces you to admit what you don't have. Teams avoid that. Then an incident forces the same admission, at 2am, with a customer on the call.

Assumed posture and actual posture drift apart quietly. The only way to know the gap is to write it down and test it.

When was your failover last exercised, not just configured?
