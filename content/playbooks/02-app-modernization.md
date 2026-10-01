---
title: "Application modernization"
kicker: "Retire, rehost, replatform, or rebuild, decided on evidence"
summary: "Assessment, the 6R decision, migration sequencing, and the cutover that is really a change of ownership."
stack: "Azure Migrate · Service Map · Azure Landing Zones · AKS · Container Apps · App Service · Azure SQL Managed Instance · PostgreSQL Flexible Server · Azure Arc · Azure VMware Solution · Azure Backup · Site Recovery · Monitor"
order: 2
---

## What this covers

Modernization is the set of decisions that moves an application estate from where it is to where it can be run, changed, and paid for sensibly. The technology is well understood. The decisions are where programmes go wrong: moving things nobody owns, resizing before diagnosing, finishing at cutover instead of at handover. This playbook is how I run it so the receiving team is bored by the end, which is the goal.

The figures behind it: a Linux modernization pipeline that mapped 6,300 virtual machines, solution assessments across U.S. commercial and education customers, a PostgreSQL escalation that a whole modernization programme depended on, and $4.5M in cost avoidance found in a single assessment without touching a price sheet.

## The questions I ask first

1. **Which applications have a named owner?** Everything else gets a retirement date or an owner before it gets a wave number. In one estate, roughly a third had neither.
2. **What are the real dependencies, not the documented ones?** The last three incidents tell you more than the architecture deck.
3. **What does each application cost today, and who sees the bill?** The invoice is the most honest architecture diagram you have.
4. **What is the resiliency posture, actually?** Not what the slide says. What is configured, and when was the failover last exercised.
5. **What has to keep running during the move?** Which workloads can tolerate a weekend, and which can't tolerate a minute.
6. **Who owns cost, change, and the 3am page on the other side?** With a date for each handover, not "after go-live."
7. **What's the honest range?** Four to nine months depending on three unknowns is a better answer than six months.

## The Azure build, in order

1. **Discover: Azure Migrate with dependency mapping.** Agentless discovery first for the inventory; agent-based dependency mapping on the systems that matter. The output isn't a list of servers. It's the dependency map, the one slide people would rather not see, with every integration and shared database made visible.
2. **Decide: the 6Rs against evidence.** Retire what has no owner. Retain what's fine where it is. Rehost what just needs to move. Replatform what gains from a managed service (Azure SQL Managed Instance, PostgreSQL Flexible Server, App Service). Refactor to containers (AKS or Container Apps) where the application will keep changing. Rebuild only when the business case is explicit. Every decision gets a one-line reason and an owner.
3. **Land: Azure Landing Zones before the first workload.** Management groups, subscriptions, hub and spoke, Azure Policy, naming and tagging enforced from day one. The charter that says who owns the platform, who can say no, and how exceptions expire. Workloads land on a foundation that already knows how to refuse.
4. **Hybrid where it's honest: Azure Arc and Azure VMware Solution.** Some estates stay partly on-premises for years. Arc brings those servers under the same policy, identity, and monitoring. AVS moves VMware estates without rewriting them, which buys time to make the real decisions.
5. **Data: managed services with a tested migration path.** Azure Database Migration Service for the move; performance baselines before and after; a resize only after the root cause is understood. The PostgreSQL escalation taught me that resizing before understanding leaves you with the same problem at a higher bill.
6. **Protect: Azure Backup and Site Recovery, exercised.** RPO and RTO as business decisions written down, then proven by a restore that someone timed. A DR plan that has never been run is a rumour.
7. **Cut over: waves with rollback and a war room, then the part people forget.** Rehearsal, runbooks, named owners on the call. And the handover plan: cost, change, and on-call move to the receiving team on a date.
8. **Operate: Azure Monitor, cost management, and a 90-day review.** Budgets per environment, alarms set at surprising rather than catastrophic, and a review at ninety days that asks whether the receiving team can change it without calling anyone.

## Why each step matters

**Discovery before decisions** because every programme that skipped it moved things it should have retired and discovered the shared database during cutover.

**Retire before you move** because the cheapest migration is the one you don't do. That's where the $4.5M came from: not pricing, noticing.

**Landing zone before workloads** because controls added afterwards are exceptions from day one, and exceptions become the standard.

**Root cause before resize** because capacity bought in a panic is capacity you pay for forever, and it spends the credibility you need for the harder conversation.

**Handover as the finish line** because a system that only works when the migration team is on the call isn't done. It's on loan.

## Real use cases

**6,300 virtual machines.** A Linux modernization pipeline that mapped the estate end to end, classified by owner, dependency, and disposition, and sequenced into waves the business could survive. The map was the deliverable; the migration followed it.

**The PostgreSQL escalation.** An Azure Database for PostgreSQL Flexible Server under real pressure, a customer whose modernization programme depended on it, and a room full of confident theories. We established what was happening before deciding what to do: the actual load sources, the actual queries, the actual resiliency posture versus the assumed one, which regional options were real. The remediation was implementation-ready and the programme's momentum survived, which was the real objective.

**Solution assessments across U.S. commercial and education.** Current-state applications, databases, infrastructure, identity, security, cost, and dependencies mapped into migration, modernization, data, AI, hybrid, and DR strategies. The assessments that changed anything told the customer at least one thing they didn't want to hear.

## How it fails

The wave plan is signed before the ownership pass. Cutover is treated as the finish line. Capacity is bought during the incident. The landing zone is designed beautifully and then exceptioned into a shape nobody recognises. The estimate was a point, not a range, and month seven is spent explaining.

## What I leave behind

The dependency map and the disposition register with an owner per application. The landing zone charter. The migration runbooks with rollback tested. The DR evidence: a timed restore, not a document. The handover schedule with dates. And a cost baseline per workload so the receiving team can tell when something drifts.
