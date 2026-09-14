---
title: "What the model may not say"
date: 2027-03-11
status: approved
tag: engineering
summary: "On my knowledge platform, the AI features run under written provenance rules. Some things it may never assert."
linkedin_url:
---

On the knowledge platform I run, the AI features operate under a short set of written provenance rules. Some things the model is never allowed to assert on its own.

The platform serves scripture with word-by-word recitation and audio. That's a domain where being fluent and wrong is not acceptable, and where the difference between what the text says and what a model thinks it says has to be visible to the reader.

So the rules are strict, and they shape the architecture.

The canonical text is never generated. It comes from a verified source and the model can only reference it, never paraphrase it as if it were the source.
Audio-based verse detection is deterministic matching against known recitations. No model guesses which verse you're on.
Anything the model produces is labelled as commentary, visually distinct, and carries a link to the passage it's about.
If the model can't ground a response in a passage, it says so, rather than filling the gap.

The features feel less magical than they could. That's the point. Users trust the platform because it never blurs the line between the text and the tool.

The same rules would serve most enterprise systems. Fewer assertions, more citations, and a hard line the model can't cross.

What is your AI never allowed to say?
