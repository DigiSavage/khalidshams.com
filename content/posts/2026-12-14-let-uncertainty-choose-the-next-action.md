---
title: "Let uncertainty choose the next action"
date: 2026-12-14
status: approved
tag: architecture
summary: "Map missing evidence and missing authority to distinct next steps instead of a generic confidence score."
linkedin_url:
visual_required: true
---

"Low confidence" is not a complete instruction.

Should the system ask a question, retrieve another source, hand over to a person or stop?

I would map uncertainty to an observable next action. Missing information calls for a specific question. Conflicting approved sources need an accountable owner. Missing permission means the system must not proceed.

Use a small synthetic case set with one example of each condition. Specify the expected action before running it, then inspect the returned evidence and any changed business state.

A model's confidence estimate can be one signal. It cannot grant authority or establish that a source is current.

Keep the decision table with the workflow. A useful admission of uncertainty tells someone what can happen next.
