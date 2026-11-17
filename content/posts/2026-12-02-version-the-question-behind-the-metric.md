---
title: "Version the question behind the metric"
date: 2026-12-02
status: approved
tag: data
summary: "A change to a metric definition needs a visible version and a plan for old and new results."
linkedin_url:
visual_required: true
---

A schema can stay identical while the meaning of its data changes.

Suppose "active customer" changes from someone with an account to someone with recent paid activity. The field name still fits. The trend line does not mean the same thing.

I would version the definition, its effective date and the owner who approved it. Keep downstream consumers visible so they can decide whether to migrate, restate history or display a break in the series.

Run old and new definitions against the same synthetic cases. Include the customers who move between categories and explain why.

Save that comparison with the data contract.

Passing a type check is useful evidence about shape. Meaning needs its own review.
