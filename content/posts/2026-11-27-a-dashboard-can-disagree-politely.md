---
title: "A dashboard can disagree politely"
date: 2026-11-27
status: approved
tag: data
summary: "Compare business definitions before treating two different numbers as a data-pipeline failure."
linkedin_url:
visual_required: true
---

Two dashboards show different revenue. Both queries run successfully.

Before blaming the pipeline, I would compare the questions.

Booked or collected? Gross or net of refunds? Which currency? Which time zone? Are late adjustments included?

Write one metric contract with the business owner: definition, time window, included states, conversion rule and treatment of corrections.

Then use the same small synthetic ledger in both views. Include a cancellation, a late payment and a boundary-date transaction. Reconcile the expected result by hand.

Different definitions can be legitimate. Hidden differences create expensive meetings.

Keep the contract beside the chart. A beautifully aligned dashboard is still allowed to answer the wrong question.
