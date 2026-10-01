---
title: "Data & AI platform"
kicker: "A lakehouse people trust, because someone owns each layer"
summary: "Microsoft Fabric, medallion layering, data contracts, semantic models, and the governance that makes AI safe to ground on it."
stack: "Microsoft Fabric · OneLake · Data Factory · Lakehouse & Warehouse · Semantic models · Power BI · Purview · Azure SQL · PostgreSQL Flexible Server · Event Hubs · Azure AI Search"
order: 3
---

## What this covers

Every AI answer is only as trustworthy as the data it was grounded on. Every dashboard that gets applause on Monday is a promise someone has to keep in a year. This playbook is how I build the data layer so that both of those become ordinary: ownership per layer, contracts between producers and consumers, one definition of each metric, and governance that is part of the design rather than a spreadsheet maintained on the side.

It draws on moving an estate onto Microsoft Fabric with real medallion layering, advising on a 1,000+ tenant Azure SQL estate, and the data and governance strategy work behind a security and AI programme.

## The questions I ask first

1. **Who owns each layer?** Bronze, silver, gold. A name per layer, not a team.
2. **How do you know when a source changes, and does anything downstream find out?** If the answer is "someone notices," the index is stale.
3. **How many definitions of your most important metric exist right now?** Three definitions of revenue is three opinions with charts.
4. **Can a user's permission be enforced at query time?** Or only at the application, which means an AI agent can route around it.
5. **Which dashboards have a producer who knows they exist?** A dashboard on an undocumented table is a promise nobody agreed to keep.
6. **What is classified, and where does classification live?** PII, PHI, financial data, export-controlled technical data. Before anything gets indexed.
7. **What's the cost per layer, and who sees it?** Compute and storage per workspace, with an owner.

## The Azure build, in order

1. **Foundations: OneLake, workspaces, and Purview.** One logical lake, workspaces aligned to ownership rather than org charts, and Purview wired in from the start so classification and lineage are facts about the data rather than a later project.
2. **Bronze: ingestion as it arrives.** Data Factory and mirroring for batch and near-real-time sources; Event Hubs where events matter. Raw, immutable, owned by whoever ingests. Nothing downstream reads bronze directly.
3. **Silver: cleaned, conformed, and under contract.** The data team owns this layer and publishes a contract per table: schema, grain, refresh cadence, quality checks, and the process for change. Consumers sign up to the contract. Changes go through it, not around it.
4. **Gold and the semantic model: one definition per metric.** Shaped for consumption and owned by the people who consume it. The semantic model is where "revenue" gets defined once, with an owner who can say no to a report that wants a slightly different one. Power BI reads the model; nobody redefines a measure on a Friday afternoon.
5. **Operational stores: Azure SQL and PostgreSQL Flexible Server.** Systems of record stay transactional. At multi-tenant scale, written tiering criteria decide which tenants share a pool and which earn Business Critical, so that cost stops being a negotiation and support stops guessing.
6. **Retrieval for AI: Azure AI Search over gold, with permissions at query time.** Only governed, classified data gets indexed. Each chunk carries its source and its permission set. Index refresh is tied to the change events from step two, so an agent never cites last quarter's policy with confidence.
7. **Observability and cost: Monitor, capacity metrics, budgets per workspace.** Refresh failures, contract violations, and capacity spikes visible to the owner of the layer, not just the platform team.

## Why each step matters

**Ownership before pipelines** because "where is the data" is a discovery problem that never ends, and "who owns this layer" is a governance problem you can actually solve.

**Contracts before dashboards** because the team that owns the table doesn't know the dashboard exists until it breaks, and the investigation always ends with "we didn't know anyone was using that."

**One semantic model** because arguments about what the number is should become arguments about what to do about it.

**Classification before indexing** because the first embarrassing AI answer is usually a document someone shouldn't have seen.

**Query-time permissions** because an agent with a service identity will happily route around application-level security unless the platform enforces it where the data lives.

## Real use cases

**Fabric changed the question.** Before a governed lakehouse, the question I heard most was "where is the data?" After moving the estate onto Fabric with medallion layering and owners, it became "who owns this layer?" That shift is what made grounding AI on it safe: an agent reading gold has a known owner, refresh, and rule set.

**1,000+ tenant databases.** A performance complaint nobody could reproduce turned out to be a handful of tenants consuming shared capacity in bursts. The fix wasn't a bigger tier. It was classification and written graduation criteria a support engineer could apply on a Tuesday without a meeting. Cost stopped being a negotiation, and the path toward Fabric and AI readiness stopped being blocked by a foundation nobody trusted.

**Data, security, and governance for an AI programme.** Access boundaries, policy enforcement, and monitoring sequenced so controls landed before workloads. The AI features that arrived later inherited governance instead of fighting it.

## How it fails

The lakehouse is built and the ownership is informal. Extracts proliferate because the governed layer is slower to get into than a spreadsheet. The semantic model exists but reports bypass it. Sensitive fields get indexed because classification was a later project. The index refreshes nightly while the source changes hourly.

## What I leave behind

An ownership map per layer. Published contracts for silver and gold. A semantic model with named metric owners. Purview classification and lineage in place before the first AI index. Tiering criteria for operational stores. And the cost view per workspace, with an owner looking at it.
