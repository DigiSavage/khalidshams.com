---
title: "A human in the loop is a UI problem"
date: 2027-03-02
status: approved
tag: agentic-ai
summary: "If the review screen is bad, the human stops reviewing and starts approving. The safeguard becomes theatre."
linkedin_url:
---

Everyone agrees there should be a human in the loop. Almost nobody designs the loop.

Here's what happens when the review step is an afterthought. The human gets a queue of items with a big green Approve button and a small grey Reject one. The item shows the agent's conclusion but not the evidence. The queue is long, the deadline is real, and every item looks fine at a glance. Within a month the human is approving at a rate that means they aren't reading. The safeguard has become theatre.

On the EMR and the agentic systems I've built, the review interface got as much design attention as the model.

Show the evidence next to the conclusion, with the specific source region highlighted, so checking is faster than trusting.
Make rejection as easy as approval, with a reason that feeds back into the evaluation set.
Route by confidence, so the human's attention goes to the cases that need it, not to a firehose.
Track review time per item. If it drops below the time it takes to read the evidence, something's wrong.

A human in the loop is only a control if the human can actually exercise judgment. That's a design problem, and it's yours.

How long does your reviewer spend per item?
