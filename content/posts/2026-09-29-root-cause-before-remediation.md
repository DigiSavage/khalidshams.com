---
title: "Root cause before remediation"
date: 2026-09-29
status: approved
tag: architecture
summary: "A PostgreSQL escalation, a room full of confident theories, and why we refused to resize first."
linkedin_url:
---

A PostgreSQL capacity escalation taught me more about architecture than most design sessions do.

The setup: an Azure Database for PostgreSQL Flexible Server under real pressure, a customer whose whole modernisation programme depended on it, and a room full of confident theories.

The instinct in that room is always to resize. Add capacity, buy time, move on.

We didn't, not first. We did the boring thing and established what was actually happening before deciding what to do about it. Where the load really came from. Which queries. What the resiliency posture actually was, versus what everyone assumed it was. Which regional options were real versus theoretical.

Root cause first. Remediation second.

The reason that ordering matters: if you resize before you understand, you now have the same problem at a higher bill, and you've spent the credibility you were going to need for the harder conversation.

The remediation ended up implementation-ready, and the modernisation momentum survived. That second part was the real goal. An escalation that stalls a programme costs far more than the incident ever did.

Slow down at the diagnosis. Everything downstream gets faster.

When did resizing last actually fix it?
