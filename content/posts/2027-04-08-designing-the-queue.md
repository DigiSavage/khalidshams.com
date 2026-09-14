---
title: "Designing the queue"
date: 2027-04-08
status: approved
tag: healthcare
summary: "The intake queue in a clinical system decides what gets seen, by whom, and how fast. It's the most important screen in the product."
linkedin_url:
---

The intake queue in a clinical system decides what gets seen, by whom, and how fast. It's the most important screen in the product, and it's usually the one designed last.

In the EMR I architected, the queue was where every automated step landed its work for a human. Extracted fields waiting for verification. Candidate patient matches waiting for confirmation. Documents the OCR couldn't read well enough to trust. If that queue was slow, confusing, or unfair, the whole system's safety story fell apart.

The design decisions that mattered most were not clinical. They were operational.

Priority by consequence, not by arrival. A possible duplicate patient record outranks a formatting question, every time.
A service level per item type, visible on the item, so the team could see what was about to breach.
Ownership. An item is claimed by one person, and unclaimed items age visibly.
Reason codes on every rejection, feeding straight back into the extraction model's evaluation set.
Nothing leaves the queue without a person's name on it.

The model made the queue possible. The queue made the model safe to use.

If you have a human in the loop, you have a queue. Have you designed it?
