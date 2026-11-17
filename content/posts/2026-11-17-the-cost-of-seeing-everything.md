---
title: "The cost of seeing everything"
date: 2026-11-17
status: published
visual_required: true
tag: security
summary: "A log budget starts with the decisions the data must support. Keep detection, investigation and retention needs visible."
linkedin_url: https://www.linkedin.com/feed/update/urn:li:share:7528474382395088897/
linkedin_published_at: 2026-11-17T08:09:25-07:00
---

"Send everything to Sentinel" is a budget decision disguised as a security strategy.

Before adding another log source, I want a short record of what it earns its place by doing:

1. The question. Which event or investigation must we be able to explain?
2. The evidence. Which source, fields and time window make that possible?
3. The test. Can a controlled event be detected, investigated and traced back to its evidence?
4. The owner. Who maintains that check and reviews the cost and retention?

Take a privileged role activation. Collecting the event is one step. Joining it to the right identity, retaining the evidence and having someone responsible for the resulting alert are separate decisions.

The graphic is a review card for that conversation. Try it on one source before changing collection. If removing a field breaks an investigation, that is evidence against the saving.

A source can also earn its place through audit, incident response or a retention obligation. "No detection uses it" is not permission to delete it.

An expensive log lake can still have blind spots. I want the coverage test beside the cost estimate.
