---
title: "The agent inherits the user's permissions"
date: 2026-10-06
status: approved
tag: security
summary: "The most important design decision in an enterprise AI system isn't the model."
linkedin_url:
---

The most important design decision in an enterprise AI system isn't the model.

It's this: the agent inherits the user's permissions, and never exceeds them.

Obvious when you say it out loud. Routinely violated in practice — usually by accident, usually by a service principal with broad access that got wired in during a prototype and never revisited. Then someone asks the assistant a question and it cheerfully returns data they were never cleared to see.

The fix isn't a policy document. It's architecture.

Identity boundaries the agent actually runs inside — Entra ID, RBAC, PIM for anything privileged.
Data it can reach that is already governed — a real lakehouse with real ownership, not a folder of extracts someone made for the pilot.
Policy enforced by the platform, not by the prompt.
Monitoring that tells you what was accessed, by whom, and on whose behalf.

Do that, and governance stops being the thing slowing AI down. It becomes the reason you can deploy it at all to people handling sensitive data.

Governance isn't the brake. It's what lets you take your foot off it.

Where does your AI get its permissions from?
