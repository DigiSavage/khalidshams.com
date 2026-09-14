---
title: "A DR plan you've never run is a rumour"
date: 2027-01-21
status: approved
tag: engineering
summary: "Every organisation has a disaster recovery plan. Very few have run it. Until you run it, it's a document."
linkedin_url:
---

Every organisation has a disaster recovery plan. Far fewer have run it.

One of the 32 gaps in that assessment was a DR plan that had never been exercised against the real dependency map. On paper it was fine. In practice, the first thing it restored depended on the fourth thing it restored, and nobody had noticed because nobody had tried.

Until you've run it, a DR plan is a rumour. A well-formatted rumour with an approval signature on it.

What I push for now is smaller and more frequent than the annual "DR test" that everyone dreads and postpones.

Restore one system from backup every month, into an isolated environment, and time it. If the restore takes longer than the RTO on the slide, the slide is wrong.
Fail over one dependency at a time, not the whole estate, so the exercise is survivable and actually happens.
Keep the dependency map as a living artefact, updated when things change, not rediscovered during a crisis.
Write down what broke each time. That list is the real DR plan.

A plan that's been run badly and fixed is worth ten that have been reviewed and filed.

When did you last restore something on purpose?
