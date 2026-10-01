---
title: "Agentic AI"
kicker: "From a demo that works to a system people depend on"
summary: "Agents, grounding, evaluation, and governance: the questions I ask, the Azure build in order, and what it looked like when it was real."
stack: "Entra ID · Azure AI Foundry · Azure AI Search · Microsoft Fabric · Azure Functions · Container Apps · API Management · Key Vault · Application Insights · Purview · Sentinel"
order: 1
---

## What this covers

An agentic system is software that plans, retrieves, decides, and acts, with a model somewhere in the loop. The model is the least reliable component in that chain, which is why the architecture around it matters more than the model inside it. This playbook is the sequence I use to take a system from a working demo to something a regulated organisation can run: the questions first, then the build, then the proof.

I've shipped this twice in the last stretch: a complete agentic system on Anthropic's Claude platform, inception through delivery, and multi-agent workflows in Azure AI Foundry grounded over governed Azure data. The patterns below are what survived both.

## The questions I ask first

These get answered in writing before any orchestration code exists. If a team can't answer them, we aren't ready to build, and that's useful to know on day one rather than day sixty.

1. **What decision does this system make, and who owns it when it's wrong?** Not "it helps with X." The specific decision, and a name.
2. **What is it allowed to see and do, per user?** Enforced by the platform, not the prompt. If the answer is "whatever the service principal can reach," stop here.
3. **Where does every fact come from, and is that source governed?** A folder someone made for the pilot is not a source.
4. **What happens when it's wrong?** The cost in dollars or harm, and the path a wrong answer takes before a person sees it.
5. **Can you show me the evaluation harness?** A fixed case set, a failure-mode catalogue, a number that moves.
6. **What does a run cost at ten times the volume?** Agents cost more the better they work.
7. **Can you stop it in under a minute?** Not a rollback. A switch.
8. **What does "done" look like for the pilot?** The numbers that trigger a production build, the numbers that trigger shutting it down, and a date.

## The Azure build, in order

The order is the method. Each step assumes the ones before it are in place, and most failed agent projects I've reviewed skipped straight to step six.

1. **Identity boundary: Microsoft Entra ID.** The agent runs as the signed-in user through an on-behalf-of flow, with Conditional Access and PIM for anything privileged. A workload identity for the agent itself, scoped to traces and configuration, nothing more. This is the step that makes everything else deployable to people handling sensitive data.
2. **Governed data: Microsoft Fabric, Azure SQL, Cosmos DB.** The agent grounds on a gold layer with named owners and a semantic model, not on extracts. Purview carries lineage and classification so sensitive fields are known before they're indexed.
3. **Retrieval: Azure AI Search.** Hybrid retrieval (vector plus keyword) over chunks that respect document structure, with the source and the permission set stored alongside each chunk. Permissions are checked at query time, not index time. Index refresh is tied to source change events, not a nightly job someone forgets.
4. **Models and orchestration: Azure AI Foundry.** A planner that decomposes the task and narrow specialists that retrieve, analyse, and act, each with a typed input, a typed output, and an explicit handoff condition. Small models for classification, extraction, and formatting; the frontier model only for steps that need judgment. Prompts live in the repo as versioned configuration, not in a console.
5. **Tools: Azure Functions and Container Apps behind API Management.** Every tool is a versioned API contract: schema validated before execution, idempotency keys on every write, reversibility where the action has consequences (drafts before sends, holds before transfers). API Management gives you one place for authentication, rate limits, and audit on every tool call. Secrets in Key Vault, never in prompts or code.
6. **Evaluation in the pipeline: GitHub Actions or Azure DevOps.** The harness runs on every prompt, tool, or model change. Groundedness and citation checks, the failure-mode catalogue, one quality number and one cost number. If either moves the wrong way, the change doesn't merge.
7. **Observability: Application Insights and Azure Monitor.** A trace per run: the plan, each retrieval and what it ignored, each tool call with input and output, each rejected alternative, the cost of every step. This is what answers "why did it do that" on a Tuesday six months from now.
8. **Operations: feature flags, kill switch, Sentinel.** Model versions behind App Configuration flags, rolled to a slice first. A kill flag read before every action. Circuit breakers per tool. Agent activity visible in Sentinel alongside everything else, because an agent is an identity doing things.

The same sequence holds on other platforms. On the Claude platform build, steps four and five were Anthropic's APIs and my own tool layer; everything else was identical, because everything else is architecture, not vendor.

## Why each step matters

**Identity first** because the most common enterprise AI failure I've seen isn't a hallucination. It's an assistant returning data a user was never cleared for, through a service principal that was given Contributor during the pilot and never revisited.

**Governed data before retrieval** because an index over ungoverned data produces fluent, confident, wrong answers, and nobody can trace them. Retrieval with provenance is the difference between an answer and a rumour.

**Typed tools and idempotency** because agents retry. That is how they work. If a tool sends an email and the first call succeeded, you now have two emails.

**The harness in CI** because every change to an agentic system has an unknown blast radius. Without a regression suite you aren't iterating; you're gambling and calling it iteration.

**Traces, not logs** because logs tell you what the agent did. Only a trace tells you why. The reasoning happened at runtime and evaporated unless you captured it.

**A kill switch** because agents fail fast, repetitive, and confident. By the time a person notices, the agent has done the wrong thing forty times. A rollback takes ten minutes if everything goes well. A switch takes ten seconds.

## Real use cases

**Clinical intake on a HIPAA-aligned EMR.** Documents arrive in five languages: referrals, labs, handwritten notes, scans. The machine does the reading: OCR, extraction with confidence scores, candidate patient matches. People do the deciding: anything below threshold goes to a reviewer with the source region highlighted, name matching proposes but never merges, and the source document stays immutable forever. The system holds 250+ active patient records. The architecture's job was to make sure a guess could never be mistaken for a fact.

**Multi-agent workflows in Azure AI Foundry.** Enterprise scenarios advanced from design to working proof of concept with RAG grounding over governed Azure data, multi-agent orchestration, and tool integration against real systems of record. The hard part was never the agents. It was the governed data layer underneath them and the identity model that let them run as the user.

**A complete agentic system on Anthropic's Claude platform.** Owned every milestone from inception to delivery: agent boundary design, orchestration, tool and function integration, an evaluation harness with a written failure-mode catalogue, and production hardening (guardrails, fallback paths, observability, cost controls). Shipped, not demoed.

## How it fails

The pilot picks the platform by accident. The service principal has standing admin rights. The index was built once from a demo folder. One model does everything and nobody can quote the most expensive run last week. The human in the loop is an Approve button nobody designed, so the human stops reviewing and starts approving. The prompt was last edited in a console on a Friday afternoon. Every one of these maps to a gate in [the method](/method/#gates), which is why the gates exist.

## What I leave behind

A signed gate record per gate. The agent map. The tool contracts. The evaluation harness and failure-mode catalogue in the repo, running in CI. A cost model per run with the ceilings set. The runbook with the off switch tested in front of the owner. And exit criteria for the pilot, with a date, written before the architecture.
