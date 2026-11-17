---
title: "A deletion has more than one address"
date: 2026-11-26
status: approved
tag: data
summary: "Trace deletion across the copies a system creates, with explicit retention exceptions and verification."
linkedin_url:
visual_required: true
---

Deleting a row can leave a remarkably well-connected ghost.

A source record may also appear in a search index, cache, attachment store, export or backup.

Before I add another retrieval layer, I want a copy map: where the data travels, who owns each copy, how long it lives and how removal is verified.

Use a synthetic marker. Create it, let the normal pipeline copy it, then exercise the removal process. Check the source and every accessible derived copy.

Backups and retention obligations may need a different policy. Record that exception and make sure a restore cannot quietly reintroduce data that should remain unavailable.

This is a lifecycle exercise, not a compliance certificate.

The architecture is incomplete if it explains how information arrives but cannot explain how it leaves.
