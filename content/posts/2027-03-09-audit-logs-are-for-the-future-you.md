---
title: "Audit logs are for the future you"
date: 2027-03-09
status: approved
tag: healthcare
summary: "Design the audit trail for the question you can't predict yet. In healthcare, that question always arrives."
linkedin_url:
---

Design the audit trail for the question you can't predict yet.

In the EMR I architected, the audit log wasn't a compliance box. It was the answer to a question that would arrive months later from someone with a legitimate reason to ask: who saw this record, what did they change, what did it say before, and what did the system infer versus what a clinician confirmed.

You can't bolt that on afterwards. If the log only records "record updated," you've lost the before state. If it only records the user, you've lost the on-behalf-of. If it's mutable, it's not evidence.

So the design rules were fixed before the first feature.

Append-only. Nothing in the audit store is ever edited or deleted, by anyone, including administrators.
Every write records the actor, the subject, the before and after, and the reason if one was given.
Automated actions are logged as the system, with the human who authorised the automation.
Inferences are logged as inferences, separately from observations, so provenance survives.
Reads of sensitive records are logged too, because access is an event.

It costs storage. It costs a little latency. It's the reason the platform can answer hard questions honestly instead of reconstructing them from memory.

Could your system answer "what did this say six months ago"?
