---
title: "Someone else's bug is your outage"
date: 2027-01-12
status: approved
tag: architecture
summary: "Multi-tenant means a customer you've never met can take down the customer who pays you most. Isolation is the design."
linkedin_url:
---

Multi-tenant means a customer you've never met can take down the customer who pays you the most.

That's the deal you sign when you share infrastructure. One tenant runs a report that scans everything. One tenant's integration goes into a retry loop. One tenant is simply bigger than you planned for. Everyone else experiences it as "the platform is slow today."

Across the estates I've worked on, from 1,000+ Azure SQL tenant databases to platforms I've built myself, the answer has never been more capacity. It's been isolation, decided on purpose.

Which tenants share a pool and which get their own. Written down.
What a single tenant is allowed to consume before it gets throttled, not paused, throttled. Enforced by the platform.
How a tenant moves between tiers, with criteria a support engineer can apply without a meeting.
What the blast radius of a bad deploy is, and whether you can roll it out tenant by tenant.

The uncomfortable part is that isolation costs money before it saves any. You're paying for boundaries that only matter on a bad day. But bad days are when your biggest customer decides whether to renew.

Which tenant could take your platform down today?
