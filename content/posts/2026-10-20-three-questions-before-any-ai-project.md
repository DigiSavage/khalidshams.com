---
title: "Three questions before any AI project"
date: 2026-10-20
status: approved
tag: agentic-ai
summary: "Before the model, before the use case list, three questions decide whether an AI project is real."
linkedin_url:
---

Three questions I ask before I'll take an AI project seriously.

Who is accountable when it's wrong?
Not "who built it." Who owns the outcome when the system gives a confident answer that turns out to be false, and a customer or a patient or an auditor is on the other end of it. If the answer is a committee, the project isn't ready.

What is it allowed to see?
Not what it can technically reach. What it is permitted to reach, per user, enforced by the platform. If the honest answer is "everything the service principal can get to," the project has a governance problem dressed as a capability.

What does a run cost at ten times the volume?
Pilots are cheap. Production is not. Token spend, retrieval calls, tool invocations, retries. If nobody can put a number on cost per run, nobody has thought about what happens when it works.

None of these are about the model. That's deliberate. Model choice is the most discussed and least decisive part of most enterprise AI projects.

Get those three answers in writing and the rest of the architecture almost designs itself. Skip them and you'll be designing it during an incident.

Which one would your current project struggle with?
