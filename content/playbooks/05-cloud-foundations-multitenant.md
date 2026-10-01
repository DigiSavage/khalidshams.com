---
title: "Cloud foundations & multi-tenant SaaS"
kicker: "A landing zone that can carry a thousand tenants"
summary: "The platform underneath everything else: landing zones, tenant isolation, tiering, resilience and cost, with the questions, the Azure build in order, and what it looked like at 1,000+ tenant databases."
stack: "Azure Landing Zones · Management groups · Azure Policy · Bicep / Terraform · Hub and spoke · Azure SQL elastic pools · AKS · App Service · Container Apps · Azure Monitor · Cost Management · Azure Migrate · Azure Site Recovery"
order: 5
---

## What this covers

Every workload in an estate inherits its foundation: how subscriptions are organised, how networks connect, which rules the platform enforces, how tenants are kept apart, and how cost is attributed. When the foundation is right, teams ship into it without asking permission. When it is wrong, every project rebuilds a worse version of it. This playbook is the foundation I build for enterprises and for ISVs running multi-tenant SaaS, where the same questions arrive with a thousand customers attached.

## The questions I ask first

The answers describe the estate as it is, which is usually different from the diagram on the wall.

1. **How many subscriptions do you have, and can you name the owner of each?** The number is rarely the problem. The unowned ones are.
2. **What is a tenant, in your system?** A database, a schema, a row with a tenant id, a subscription, or some mixture that grew over time. The answer decides what isolation you can promise.
3. **Which tenants pay for the platform, and which ones cost more than they pay?** Most SaaS estates have a top tier that funds everything and a long tail that drives the support queue.
4. **What does "noisy neighbour" mean here, and when did it last happen?** A specific incident, with the tenant, the resource, and what was done about it.
5. **What can you deploy from a clean repository in an afternoon?** The network, the policies, a subscription with its guardrails. If the answer is "the application," the platform is hand-built.
6. **What is your recovery point and recovery time, per tier, and when were they last tested?** Numbers and a date. A backup that has never been restored is a hope.
7. **Can you explain last month's bill to the CFO by product, tenant, and environment?** If cost cannot be attributed, it cannot be reduced, and it will be cut by guesswork instead.
8. **What is the path to Fabric and AI from here?** Not because every estate needs them now, but because the foundation decides whether that path is a quarter or a rewrite.

## The Azure build, in order

The platform is built once, as code, and every workload lands into it. The tenant model is designed before the first tenant is migrated, because it is the one thing that is expensive to change later.

1. **Subscription and management group design.** Platform subscriptions for identity, connectivity, and management, separated from landing zone subscriptions for workloads. Management groups that mirror how the organisation accepts risk, with Azure Policy assigned at each level. Naming and tagging standards enforced by policy from the first subscription: owner, cost centre, environment, data classification, tenant tier.
2. **Connectivity: hub and spoke.** A hub with the firewall, DNS, and the on-premises or partner connection, and a spoke per landing zone. Private DNS zones centralised so private endpoints resolve everywhere. IP address space planned for the next five years, because re-addressing a running estate is a project nobody wants.
3. **Infrastructure as code: Bicep or Terraform in a pipeline.** The platform itself, not just the applications. Policy assignments, network, diagnostic settings, and the subscription vending process, so a new landing zone is a pull request, not a ticket. Environments promoted through the same pipeline with the same code.
4. **Tenant isolation model.** Decide the isolation unit and the tiers before migrating anything. Database per tenant for isolation and simple compliance, with Azure SQL elastic pools to share capacity; schema or row-level isolation for the long tail where economics demand it; dedicated infrastructure for the few tenants whose contracts require it. Every tenant tagged with a tier, and the tier is what drives capacity, SLA, backup, and price.
5. **Compute platform: App Service, Container Apps, or AKS.** Chosen by what the team can operate, not by what is fashionable. App Service and Container Apps for most workloads; AKS when there is a platform team to run it and a reason to. Every workload behind a managed identity, reading configuration from App Configuration and secrets from Key Vault, scaling on signals that reflect tenant load.
6. **Tiering and graduation criteria.** Written rules for when a tenant moves between tiers: the metrics, the thresholds, the price change, and who approves. Business Critical and premium tiers for tenants whose usage or contracts justify them, with explicit criteria so graduation is a measurement, not a negotiation after an outage.
7. **Resilience and recovery.** Per-tier recovery objectives, zone redundancy where the tier promises it, geo-replication for the tenants whose contracts require it, and a tested restore on a calendar. Azure Site Recovery for the virtual machine estate that has not been modernised yet. Runbooks for the failures that have actually happened.
8. **Cost and operations: Azure Monitor and Cost Management.** Diagnostic settings everywhere by policy, a workbook per tier showing capacity and noisy-neighbour signals, cost allocated by tag to product, tenant, and environment, budgets with alerts, and a monthly review with an owner. FinOps is a meeting with a decision at the end, not a dashboard.

## Why each step matters

**Subscriptions and management groups first** because scope is what makes everything else cheap. A policy assigned at the right management group governs a thousand resources with one line. Assigned at the resource group, it governs that resource group.

**Connectivity before code** because the network is the thing most likely to be hand-built and never reproducible. Putting it in code second, after it exists, usually means it never happens.

**Code before tenants** because the tenant migration will be the biggest change the platform ever absorbs, and absorbing it on a hand-built foundation means every tenant inherits a slightly different environment.

**The isolation model before migration** because it is the one decision that cannot be reversed cheaply. Moving from row-level to database-per-tenant later is a data migration for every customer at once.

**Compute by operability** because the most expensive outage I have seen in SaaS was not a capacity problem. It was a platform the team could not debug at two in the morning.

**Graduation criteria in writing** because without them the top tier fills with tenants who complained loudest, and the economics of the long tail quietly stop working. On a 1,000+ database estate, explicit Business Critical criteria were the difference between predictable cost and a performance complaint queue nobody could reproduce.

**Recovery tested on a calendar** because every recovery objective is fiction until the restore has been run, timed, and signed by the person who would have to run it in a real incident.

**Cost attributed by tag** because a bill that cannot be explained gets cut by percentage, and percentages land on the wrong teams. Attribution turns cost from a complaint into a decision.

## Real use cases

**A SaaS estate on 1,000+ Azure SQL tenant databases.** An ISV with unreproducible performance complaints and unpredictable cost. I classified the workloads, defined explicit Business Critical graduation criteria, worked the noisy-neighbour and CPU risk directly, and laid a staged path toward Fabric and AI readiness on a foundation that could carry it. The result was a stabilised estate with a tiering model the business could price.

**A business-value assessment across roughly 3,000 employees.** Applications, data, infrastructure, identity, security, cost and dependencies mapped onto a single view, with 32 gaps documented and each connected to a cloud or services decision. It surfaced $4.5M in cost avoidance, almost none of it from renegotiation and nearly all of it from finding what the organisation was doing twice. That single view is what a foundation assessment should produce.

**HILUM Systems, a multi-tenant platform I am building.** A clinical practice stood up in minutes: patient portal, admin console, scheduling, notifications. Identity, patient context, authorisation, audit and workflow are shared platform services, so specialty applications extend the platform instead of becoming silos. The tenant model was designed before the first screen, for the reasons above.

## How it fails

One subscription for everything with Owner granted to the team that got there first. A network drawn in a diagram and built by hand, so nobody dares change it. Tenants isolated by a column, with a query that forgot the filter once. A top tier defined by who complained. Backups that have never been restored. A bill that arrives as one number. And a Fabric or AI initiative that stalls in month two because the foundation cannot say which data belongs to which tenant. These are the findings that fill a foundation assessment, and each one maps to a gate in [the method](/method/#gates).

## What I leave behind

The subscription and management group design with every owner named. The policy set and the platform code in a repository, deployed by a pipeline, with the subscription vending process documented. The tenant isolation model with the tiers, the graduation criteria, and the price implications written down. Recovery objectives per tier and the date and duration of the last tested restore. A cost model attributed by product, tenant, and environment with budgets and owners. And the staged path to Fabric and AI, with the first step small enough to start next quarter.
