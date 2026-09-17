---
title: "1,000 tenants and a problem you can't reproduce"
date: 2026-09-17
status: published
tag: architecture
summary: "A performance problem nobody could reproduce across 1,000+ tenant databases, and why the fix was written rules, not a bigger tier."
linkedin_url: https://www.linkedin.com/feed/update/urn:li:share:7506424556291735552/
---

A customer had 1,000+ Azure SQL tenant databases and a performance problem nobody could reproduce.

The complaint was "the platform is slow." The reality was noisier. A handful of tenants consuming shared capacity in bursts, and everyone else feeling it as random latency. Classic noisy neighbour, at a scale where you can't just go look at it.

What moved the needle wasn't a bigger tier.

It was classification. Which tenants behave like enterprise workloads, which behave like trials, and which are quietly pathological. Then explicit graduation criteria: the written conditions under which a tenant earns Business Critical, rather than getting upgraded because someone complained loudly enough.

Once those criteria existed, three things changed.

Cost stopped being a negotiation.
Support stopped guessing.
And the path toward Fabric and AI readiness stopped being blocked by a foundation nobody trusted.

Multi-tenant SaaS punishes ambiguity. Every "we'll figure it out per customer" decision compounds into an estate no one can reason about.

Write the rules down. Imperfect written rules beat per-incident judgment at 1,000 tenants, every time.

How does your team decide when a tenant graduates?
