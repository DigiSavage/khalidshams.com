---
title: "Structured outputs are the new API"
date: 2027-04-01
status: approved
tag: agentic-ai
summary: "Free text from a model is a demo. A validated JSON object is a system. The gap is where most production failures live."
linkedin_url:
---

Free text from a model is a demo. A validated object with a schema is a system.

Almost every production failure I've traced in an agentic system came down to the same shape: the model produced something that looked right, a downstream step assumed it was right, and nobody checked. A date in the wrong format. A field that was supposed to be one of four values and was a fifth. A number with a currency symbol in it.

The fix is to stop treating model output as text and start treating it as an API response.

Define a schema for every output the model produces, as strictly as you'd define an API contract.
Validate against it before anything downstream reads it. A schema failure is a handled error, with a retry that includes the validation message, then a fallback.
Keep the schemas in version control next to the prompts, because they change together.
Test the schemas without a model in the loop, with the ugly cases you've already seen in production.

Once outputs are structured, the rest of the system gets ordinary. It's just services passing typed data around, which is a problem we solved a long time ago.

The model is the least reliable component in the pipeline. Treat its output that way.

How much of your agent's output is validated before it's used?
