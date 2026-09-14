---
title: "A landing zone is a political document"
date: 2026-10-13
status: approved
tag: cloud
summary: "The subscriptions and policies are the easy part. A landing zone is really an agreement about who owns what."
linkedin_url:
---

A landing zone is a political document that happens to be implemented in Azure.

The subscriptions, the hub and spoke, the policy assignments, the naming standard. All of that is a week of work if you know what you're doing. It's also the part everyone argues about, because it's the part you can see.

The part that decides whether the landing zone survives is invisible. Who owns the platform team. Who can say no to a workload. What happens when a business unit wants an exception on Friday afternoon. Who pays for the shared services, and how that shows up on someone's budget.

I've watched beautifully designed landing zones rot in eighteen months because those questions were never written down. Every exception became precedent. Every precedent became the new standard. Eventually the "landing zone" was just the first subscription that got created, plus whatever grew around it.

The ones that last have a boring one-page charter. Ownership, funding, exception process, review cadence. The technology sits underneath that page, not the other way around.

If you're about to build one, spend the first week on the charter and the second on the Bicep. It feels backwards. It isn't.

Who can say no in your environment?
