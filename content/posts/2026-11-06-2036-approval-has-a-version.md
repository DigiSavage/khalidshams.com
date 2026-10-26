---
title: "Approval has a version"
date: 2026-11-06
status: approved
tag: security
summary: "An approval belongs to an exact proposal and must survive a fresh permission check."
linkedin_url:
series: 2036
linkedin_schedule: 2036
---

Suppose I approve a draft. Someone changes the amount before execution.

What, exactly, did I approve?

For my 2036 design horizon, approval needs a precise object: this action, these arguments, this version, this authorized reviewer, within this time window.

Try two tests. Change the payload after approval. Then run the original payload after permission to execute is revoked.

Neither should quietly inherit the old green light. Inspect the execution record, including whether anything changed in the business system.

The synthetic studio lets you try both conditions. It makes no live cloud calls:
<https://khalidshams.com/architect/agent-studio/#runtime>

2036, built in the open · 05

“Approved” deserves a little more grammar.
