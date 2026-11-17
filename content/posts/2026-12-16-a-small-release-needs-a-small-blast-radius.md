---
title: "A small release needs a small blast radius"
date: 2026-12-16
status: approved
tag: security
summary: "Limit the consequences of a release, not only the size of its code change."
linkedin_url:
visual_required: true
---

A small pull request can change behavior for every customer.

I would size a release by its possible effects: which tenants, records, operations and dependencies can it reach?

Start with a bounded exposure plan. Name the eligible cohort, the signals that stop expansion, who can halt it and what happens to work already in flight.

Exercise the stop path in a non-production environment. A disabled flag should have an explicit meaning for queued jobs and active workers, not just new page loads.

Inspect the resulting business state before widening access. A quiet error dashboard is not enough if the new path never received representative work.

The deployment plan should make the consequence of being wrong smaller.
