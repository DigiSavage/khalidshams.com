---
title: "Naming is an architecture decision"
date: 2027-02-02
status: approved
tag: cloud
summary: "A naming and tagging standard looks like housekeeping. It's the thing that makes cost, ownership, and security possible."
linkedin_url:
---

A naming and tagging standard looks like housekeeping. It's actually the foundation for everything that's hard about running a cloud estate.

I've walked into environments where nobody could answer "what does this resource group cost" or "who owns this VM" or "is this production." Not because the tooling was missing. Because the resources were named things like `test-final-2` and tagged with nothing.

Every hard question in cloud operations resolves to a lookup against names and tags.

Cost allocation: which team pays for this?
Ownership: who do I call at 2am?
Security: is this in scope for the control?
Lifecycle: can I delete this?
Compliance: is this in the right region?

If the names and tags don't carry that information, every one of those questions becomes a human investigation, and humans don't investigate at 2am.

The standard doesn't have to be elaborate. Environment, workload, owner, cost centre, and a policy that refuses to create anything without them. Enforced from day one, because retrofitting tags onto three thousand resources is a project nobody funds.

It's the least exciting decision in the landing zone and the one that pays off every single day.

Can you tell what every resource in your estate is for from its name?
