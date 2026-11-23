---
title: "Draw the finish line before the flow"
date: 2026-11-23
status: published
tag: architecture
summary: "Work backward from an accepted business outcome to the records, authority and contracts that make it possible."
linkedin_url: https://www.linkedin.com/feed/update/urn:li:share:7530648636045684736/
visual_required: true
linkedin_published_at: 2026-11-23T08:09:08-07:00
---

The easiest box to draw is often the least useful place to start.

I would start with the last observable fact: what has to be true for someone to accept the work?

For a synthetic service request, "the agent replied" is a different finish line from "the right team owns an accepted request."

Work backward. What record proves acceptance? Who can create it? What evidence must they see? Which state change and component contract make that possible?

Keep those answers on one page before polishing the interface. An early screen sketch can still reveal that people need a different outcome.

Then break one dependency. Remove the destination's acknowledgement and inspect whether the system admits it cannot yet prove completion.

The useful diagram ends with evidence, not a confident adjective.
