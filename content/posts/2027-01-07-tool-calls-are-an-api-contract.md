---
title: "Tool calls are an API contract"
date: 2027-01-07
status: approved
tag: agentic-ai
summary: "When an agent calls a tool, that's an API. It deserves the same discipline as any other integration."
linkedin_url:
---

When an agent calls a tool, that's an API call. It deserves the same discipline as any other integration, and it usually doesn't get it.

The pattern I see in prototypes: a function with a loose description, an untyped dictionary going in, whatever comes back going straight into the model's context. It works in the demo because the demo only sends nice inputs.

The systems I've shipped treat every tool like a versioned API contract.

A typed input schema, validated before anything executes. If the model produces a malformed call, it gets a structured error back, not a stack trace and not silence.
A typed output, so the next step knows exactly what it's reading.
A description written for the caller, which in this case is a model. Specific about what the tool does, what it must not be used for, and what a failure looks like.
Versioning, because tools change and old prompts keep calling them.
A permission scope per tool, inherited from the user, not from the service.

Once tools are contracts, three things get easier: testing them without a model in the loop, swapping the model without rewriting the tools, and explaining to an auditor what the agent was and wasn't able to do.

How many of your agent's tools have a schema?
