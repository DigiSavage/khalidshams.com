---
title: "Feature flags for models"
date: 2027-04-15
status: approved
tag: agentic-ai
summary: "A model version change is a production deploy. Put it behind a flag, run it against the harness, roll it out to a slice first."
linkedin_url:
---

A model version change is a production deploy. Most teams treat it as a configuration tweak.

The provider announces a new version. It's better on the benchmarks. Someone updates the model name in a config file, and by lunchtime every user is on it. Then the reports start: it's more verbose, it refuses a case it used to handle, the cost per run went up 30 percent, the tone changed.

None of that is the model's fault. It's a deploy without a deploy process.

What I do instead, and it's nothing new:

The model identifier sits behind a feature flag, per workflow, not globally.
The new version runs against the full evaluation harness first. Accuracy, groundedness, cost, latency, and the failure-mode catalogue. If any number moves the wrong way, it doesn't roll out.
It goes to a slice of traffic, with traces tagged by model version, so the comparison is real.
Rollback is flipping the flag, not a code change.

This matters more every quarter, because model versions change faster than any other dependency in the stack. The team that can evaluate and switch in a day has an advantage. The team that switches blind has an incident.

How did your last model upgrade go out?
