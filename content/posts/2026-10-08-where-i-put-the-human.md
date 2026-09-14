---
title: "Where I put the human"
date: 2026-10-08
status: approved
tag: healthcare
summary: "I architected an EMR holding 250+ patient records, and it changed where I put the human."
linkedin_url:
---

I architected an EMR that now holds 250+ active patient records, and it changed how I think about AI.

Not because we put a model in the middle of care. Because we deliberately didn't.

Clinical evidence arrives messy. Documents in several languages. Scans. Labs. Records that refer to the same person three different ways. There's real temptation to let a model reconcile all of it and move on. It can, mostly. And "mostly" means something very different in healthcare than it does in a demo.

So the architecture put the machine where it belongs: intake, OCR, surfacing candidate matches, flagging what needs a look. Fast, tireless, valuable work.

And it put a human at every point where a judgment becomes part of someone's medical record.

Two rules held the whole thing together.

Never destroy the source. The original evidence stays, always, alongside anything derived from it.

Never blur what was observed with what was inferred. Provenance isn't a nice-to-have. It's the difference between a record and a rumour.

Immutable audit underneath. Deterministic validation before and after every deployment.

The best AI systems I've built aren't the ones that decide the most. They're the ones clearest about what they don't decide.

Where have you drawn that line?
