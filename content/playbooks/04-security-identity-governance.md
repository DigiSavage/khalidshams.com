---
title: "Security, identity & governance"
kicker: "Controls that land before the workloads do"
summary: "Identity as the perimeter, policy as code, and detection you can afford: the questions, the Azure build in order, and what it looked like in a regulated programme."
stack: "Microsoft Entra ID · Conditional Access · PIM · Azure Policy · Management groups · Defender for Cloud · Key Vault · Private Link · Microsoft Sentinel · Azure Monitor · Purview"
order: 4
---

## What this covers

Security in an enterprise estate is not a product you buy at the end. It is the order in which you build. Identity decides who can act, policy decides what the platform will allow regardless of who asks, and detection tells you what happened anyway. This playbook is how I sequence those three so that compliance is something the estate inherits, not something each project relitigates. It is written for the moment a leader asks "are we safe to put this workload, this data, or this AI system here" and wants an answer with evidence behind it.

## The questions I ask first

Most of these have a one-word answer in a healthy estate. When the answer is a paragraph, that paragraph is the finding.

1. **Who has standing admin rights right now, and why?** The list, not the policy. Global Administrator, Owner at the subscription root, and anything with a wildcard.
2. **What stops a stolen password from becoming a stolen estate?** MFA for everyone is table stakes. The real question is Conditional Access: device, location, risk, and what happens to legacy authentication.
3. **Where is the identity perimeter for machines?** Service principals with secrets in config files, versus managed identities and workload identity federation. The first category is where the breach usually starts.
4. **Which rules does the platform enforce by itself?** If "no public storage" and "encrypt at rest" live in a document rather than in Azure Policy, they are suggestions.
5. **Can you show me a network path from the internet to your most sensitive data?** Drawn, not described. If it goes through a public endpoint with an IP allow list, we have work to do.
6. **What is in Sentinel, and how much of it has a detection written against it?** Logs you ingest and never query are the most expensive way to feel secure.
7. **Who is told when a control fails, and how fast?** Alert routing, severity, and the on-call human. A dashboard nobody opens is not an alert.
8. **Which regulation shapes this, and which control maps to which clause?** HIPAA, PCI DSS, SOC 2, FedRAMP, or an internal standard. If nobody can map a control to a clause, the audit will do it for you.

## The Azure build, in order

The sequence matters more than the tooling. Each layer makes the next one enforceable.

1. **Tenant and identity foundation: Microsoft Entra ID.** One tenant, a clean break-glass procedure tested on a calendar, and every human in a group that means something. Hybrid identity through Entra Connect where there is still on-premises AD, with password hash sync so Identity Protection has signal. Guest access governed through entitlement management, not ad hoc invitations.
2. **Access control: Conditional Access and Identity Protection.** Policies in report-only mode first, then enforced: MFA everywhere, block legacy authentication, require compliant or hybrid-joined devices for anything sensitive, step up on sign-in risk. Named locations for the places work actually happens. Every policy has an owner and an exception process that expires.
3. **Privilege: Privileged Identity Management.** No standing admin. Eligible roles with approval, justification, time limits, and an access review that actually runs. Owner at the subscription level becomes a PIM-activated role with an alert when it is used. This is usually the single highest-leverage change in the estate.
4. **Platform guardrails: management groups and Azure Policy.** A management group hierarchy that mirrors how the organisation accepts risk: platform, landing zones, sandbox, decommissioned. Policy assignments at the right scope: deny public network access on PaaS, require private endpoints, enforce encryption and TLS versions, require tags that drive cost and ownership, restrict regions for data residency. Deny for the non-negotiables, audit for the rest, and a weekly compliance number someone owns.
5. **Secrets and encryption: Key Vault and managed identities.** Secrets, keys, and certificates in Key Vault with RBAC rather than access policies, soft delete and purge protection on, private endpoint only. Applications reach it with a managed identity. Customer-managed keys where the regulation or the customer requires them, and nowhere else, because every CMK is an operational commitment.
6. **Network boundary: Private Link, firewall, and segmentation.** Hub and spoke with Azure Firewall or a partner appliance in the hub, private endpoints for every PaaS service that holds data, DNS set up so private resolution just works, and NSGs that default to deny. Public endpoints disabled at the resource, not just filtered.
7. **Posture: Defender for Cloud.** The Defender plans turned on where they earn their cost: servers, storage, SQL, containers, Key Vault. Secure Score tracked as a trend with the recommendations triaged into a backlog with owners, not a report that gets forwarded. Regulatory compliance dashboards mapped to the frameworks the organisation actually answers to.
8. **Detection and response: Microsoft Sentinel.** Detection first, ingestion second. Decide which attacks matter, write the analytics rules for them, then ingest exactly the logs those rules need at the retention those rules need. Entra sign-in and audit logs, Activity logs, Defender alerts, firewall logs, and the application logs that carry authorisation decisions. Automation rules and playbooks for the responses that are safe to automate: disable the account, isolate the host, open the ticket. Everything else routes to a person with context attached.

## Why each step matters

**Identity before everything** because every other control assumes you know who is asking. A perfect network and a shared admin account is a perfect network with a side door.

**Conditional Access before PIM** because PIM protects the roles and Conditional Access protects the sign-in that activates them. Doing it the other way round puts an approval workflow in front of an unverified session.

**PIM before policy** because the people who write policy need to do it with elevated rights they do not keep. The first thing a standing Owner does with Azure Policy is exempt themselves.

**Policy before workloads** because retrofitting deny rules onto a running estate is a change-management project. Landing the rules first means every new workload inherits them for free and the exceptions are visible from day one. This is the sequencing that let a financial services programme build data and AI capability without reopening compliance at every step.

**Key Vault and managed identities before networking** because the moment the network closes, the first thing teams do to keep working is paste secrets into pipelines. Give them the right path before you take away the wrong one.

**Networking before Defender** because posture tools report on what exists, and reporting on an estate full of public endpoints produces a backlog nobody can work through.

**Defender before Sentinel** because Defender generates the highest-quality alerts you will have, and Sentinel is where they get correlated with everything else. Sentinel without Defender is a query engine looking for signal.

**Detection-first ingestion** because the alternative is the most common Sentinel failure I see: every log source turned on in month one, a bill that triples by month three, and a dashboard of raw events with nothing watching them. The log bill should be a consequence of the detections you chose, not a surprise.

## Real use cases

**A multi-million-dollar financial services programme.** Banking and capital markets stakeholders, regulatory obligations shaping every architectural option. I contributed the data, security, governance and Fabric and Sentinel strategy: access boundaries, policy enforcement, monitoring, and the sequencing that let controls land before workloads did. The outcome was a governed foundation the programme could build on without relitigating compliance at every step. The sequence above is that sequence.

**A HIPAA-aligned EMR I built myself.** The same model at product scale: identity, authorisation, immutable audit, and provenance built as platform services before the first clinical screen existed. Every judgment that enters a record is attributable to a person, and the source document that informed it cannot be changed. The audit trail is not a feature added for compliance. It is the data model.

**An agentic AI system in a regulated environment.** The agent runs as the signed-in user through an on-behalf-of flow, with Conditional Access and PIM for anything privileged and a kill switch read before every action. Agent activity lands in Sentinel alongside everything else, because an agent is an identity doing things and should be watched like one. The details are in [the agentic AI playbook](/playbooks/agentic-ai/).

## How it fails

Standing Global Administrators from the migration that never got removed. Conditional Access policies that have been in report-only mode for a year. A service principal with Contributor on the root management group because a pipeline needed it once. Azure Policy in audit mode everywhere, so the compliance number is a weather report. Private endpoints on the database and a public endpoint on the storage account next to it. Every log source in Sentinel and three analytics rules. A Secure Score that gets screenshotted for the steering committee and never worked. Each of these is a finding I have written more than once, and each maps to a gate in [the method](/method/#gates).

## What I leave behind

The privileged role inventory with every standing assignment converted or justified. The Conditional Access policy set with owners and expiry on every exception. The management group hierarchy and the policy assignments as code, in a repository, deployed by a pipeline. A network diagram with the path to sensitive data drawn and every public endpoint accounted for. The detection catalogue: which attacks, which rules, which logs, which retention, and the monthly cost that follows from it. The control-to-clause map for the regulation that applies. And the break-glass procedure, tested, with the date of the last test written on it.
