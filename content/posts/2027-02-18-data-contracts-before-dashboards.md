---
title: "Data contracts before dashboards"
date: 2027-02-18
status: approved
tag: data
summary: "A dashboard built on an undocumented table is a promise nobody agreed to keep."
linkedin_url:
---

A dashboard built on an undocumented table is a promise nobody agreed to keep.

The team that owns the table doesn't know the dashboard exists. They rename a column, change a grain, or fix a bug in the source, and somewhere an executive's number changes with no explanation. Then the investigation starts, and it always ends with "we didn't know anyone was using that."

Data contracts fix this at the source. Before a consumer builds on a table, the producer publishes what they're committing to: the schema, the grain, the refresh cadence, the quality checks, and what happens when they need to change it. The consumer signs up to that contract. Changes go through it, not around it.

On the Fabric estates I've worked on, this is what medallion layering actually means in practice. Gold isn't just "the clean tables." It's the tables someone has agreed to keep clean, on a schedule, with a process for change.

The dashboard that gets applause on Monday is cheap. The dashboard that still shows the right number in a year is the one with a contract underneath it.

Which of your dashboards has a producer who knows it exists?
