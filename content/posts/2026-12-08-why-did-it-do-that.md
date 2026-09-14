---
title: "Why did it do that"
date: 2026-12-08
status: approved
tag: agentic-ai
summary: "Logs tell you what an agent did. They don't tell you why. Observability for agents is a different thing."
linkedin_url:
---

"Why did it do that?" is the question every agentic system eventually gets asked, and logs can't answer it.

Logs tell you what happened. The tool was called, the response came back, the answer was returned. What they don't tell you is why the agent chose that tool, what it believed at the time, what it retrieved, and what it ignored.

For a conventional service that's fine. The code is the reasoning, and you can read the code. For an agent, the reasoning happened at runtime and evaporated.

So observability for agents means capturing the reasoning trail, not just the events. On the systems I've built, every run produces a trace: the plan the agent formed, each retrieval and what it returned, each tool call with its input and output, each decision point and the alternative it rejected, and the cost of every step.

That trace is what lets you answer "why" after the fact. It's also what feeds the evaluation harness, what surfaces new failure modes, and what an auditor will ask for in a regulated environment.

It isn't free. Traces have to be stored, secured, and redacted where they hold sensitive data. But a system that can't explain itself is a system you can't safely change.

Could your system answer "why" for a run from last Tuesday?
