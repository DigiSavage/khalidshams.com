---
title: "Full-stack product engineering"
kicker: "Architecture advice ages badly when you stop building"
summary: "How I take a product from a blank repository to something people depend on: data model, API, auth, front end, pipeline, observability and cost, with the questions, the build in order, and three products I ship myself."
stack: "Python · FastAPI · TypeScript · React / Next.js · PostgreSQL · MongoDB · Azure SQL · Entra ID / OAuth 2.0 · Azure Container Apps · App Service · AWS · S3 · GitHub Actions · Application Insights · OpenTelemetry"
order: 6
---

## What this covers

A principal architect who cannot ship is giving advice they have not tested. I build products end to end: the data model, the services, the authorisation, the interface, the release pipeline, and the operations that keep it alive at three in the morning. This playbook is the sequence I follow whether the product is a clinical system for a non-profit, a consumer platform with real traffic, or a multi-tenant platform for an industry. The stack changes. The order does not.

## The questions I ask first

These are the questions I answer for my own products before writing code, and the ones I ask a team whose product I am reviewing.

1. **What is the one record this product exists to keep correct?** A patient. An order. A verse and its audio. Everything else is a view of it.
2. **Who can see and change that record, and how will we prove it later?** Authorisation and audit are part of the data model, not a feature for the second release.
3. **What is the boring stack you can operate alone?** The question is not what is best. It is what you can debug with no one else awake.
4. **What does the API look like to someone who has never spoken to you?** If the answer requires a conversation, the contract is not written yet.
5. **How does a change get from a laptop to production, and how does it get back out?** Branch, test, build, deploy, rollback. In minutes, by one person, without fear.
6. **What will you look at when it breaks?** Logs, traces, and the three numbers that tell you whether users are fine.
7. **What does this cost per user per month, and what alarm fires when it doubles?** Consumer products die quietly of cloud bills.
8. **What are you not building?** The written list of things the product will not do is what keeps the first release shippable.

## The build, in order

This is the order on Azure. The AWS version differs only in the service names, and I run one of each in production.

1. **The record: PostgreSQL, Azure SQL, or MongoDB.** The canonical entity modelled first, with ownership, timestamps, and soft-delete from day one. Relational when the data is relational and the integrity rules matter, which is most business products. A document store when the shape varies by design, as it does for a content platform with many media types. Immutable event or audit tables alongside the mutable ones for anything a person will be asked to explain later.
2. **The contract: a typed API with FastAPI or a Node framework.** Resources named after the domain, versioned from the first release, with schema validation on every request and a generated OpenAPI document that is the documentation. Pagination, filtering, and idempotency designed in, not retrofitted. Errors are structured and never leak internals.
3. **Identity and authorisation: Entra ID, OAuth 2.0, or Cognito.** Authentication delegated to a platform, never hand-rolled. Authorisation as a service inside the product: roles, scopes, and tenant or patient context checked at the API boundary on every call, with the decision logged. Secrets in Key Vault or Secrets Manager, reached by a managed identity.
4. **The interface: React or Next.js in TypeScript.** Server-rendered where search and first paint matter, client-rendered where interaction does. Components that reflect the domain, a design system small enough to keep consistent, and accessibility treated as a requirement because it is one. The front end never holds a secret and never makes an authorisation decision.
5. **Runtime: Container Apps, App Service, or a managed container service.** Containers from the first commit so the laptop, the pipeline, and production run the same image. Scale-to-zero for the things that can, reserved capacity for the things that cannot. Managed services for the database, storage, and queues, because the operations team is me.
6. **Pipeline: GitHub Actions.** Every push builds, tests, and lints. Main deploys to a staging slot, promotes on a check, and can roll back by redeploying the previous image. Infrastructure in Bicep or Terraform in the same repository. Nothing is deployed by hand twice.
7. **Observability: Application Insights and OpenTelemetry.** Structured logs with a correlation id, traces across the API and the database, and a dashboard with three numbers: request success rate, latency at the 95th percentile, and the count of the thing the product exists to do. Alerts on those three, routed to a phone.
8. **Cost and operations.** Budgets with alerts at the resource group, storage lifecycle rules for media, caching in front of anything expensive, and a monthly look at cost per user. A runbook for the five failures that have happened, written the day after each one.

## Why each step matters

**The record first** because every product I have seen fail at scale failed in the data model, and the data model is the one layer you cannot refactor over a weekend. On the EMR, the canonical patient record and its immutable provenance were designed before any screen existed, which is why the system can be trusted with 250+ active patients.

**The contract before the interface** because the API is the product's long-term shape. Interfaces get rebuilt; a contract that other systems depend on is forever.

**Identity before features** because adding authorisation to a product that already works means finding every place a decision should have been made and was not. On a clinical system, that list is the compliance finding.

**The boring stack** because I operate these products myself. Python, TypeScript, a relational database, containers, and a managed platform are the stack I can debug at any hour, and that fact is worth more than any benchmark.

**Containers and a pipeline from the first commit** because "it works on my machine" is the most expensive sentence in software, and a pipeline built after the product is a migration nobody schedules.

**Three numbers on a dashboard** because a wall of metrics is where incidents hide. Success rate, latency, and the count of the core action answer "are users fine" in one glance.

**Cost alarms** because a consumer platform with real traffic can double its storage and egress bill in a week of success, and the first warning should be an alert, not an invoice.

## Real use cases

**FAJR Global EMR.** A HIPAA-aligned electronic medical record built in Python for a non-profit, in production with 250+ active patient records. One canonical patient record across demographics, cases, labs, imaging, documents and clinical updates. Multilingual document intake with OCR and extraction confidence scores, identity reconciliation that proposes but never merges, immutable audit and provenance on every change, and a human at every point where a judgment enters a record. The data model is the security model.

**DivineMarvels.** A consumer knowledge platform I designed, built and operate on AWS with MongoDB and S3. Word-by-word recitation and audio, a personalised dashboard, and AI features governed by explicit provenance rules: recitation follow-along with per-word highlighting and audio-based verse detection that jumps the reader to the matching passage. The interesting engineering is not the AI. It is the provenance rule that decides what the AI is allowed to assert and the media pipeline and caching that keep the bill sane under real traffic.

**HILUM Systems.** A multi-tenant EMR and practice platform, in development, that stands up a clinical practice in minutes: patient portal, admin console, scheduling, notifications. Identity, patient context, authorisation, audit and workflow are shared platform services so specialty applications extend the platform instead of becoming silos. It is the EMR's lessons rebuilt as a platform, with the tenant model from [the foundations playbook](/playbooks/cloud-foundations-multitenant/) underneath.

## How it fails

A schema designed around the first screen. An API that mirrors the database tables. Authorisation checked in the front end. A framework chosen from a conference talk that one person on the team can operate. Deployments by hand from one laptop. Logs without a correlation id. A dashboard with forty charts and no alert. A storage bill that doubled in a month nobody noticed. And a feature list that never had a "not building" column, so the first release never ships. Each of these has a line in [the method](/method/#gates), because products fail the same way estates do, just faster.

## What I leave behind

A data model with ownership, audit, and provenance drawn and explained. An OpenAPI document that is the contract. An authorisation matrix: who, what, on which record, logged where. A repository with the application, the infrastructure, and the pipeline, where a new engineer can deploy on day one. A dashboard with three numbers and three alerts. A cost model per user with the alarm thresholds set. And the "not building" list, so the next release has the same discipline as the first.
