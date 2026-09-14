---
title: "Where RAG quietly fails"
date: 2027-01-28
status: approved
tag: agentic-ai
summary: "Retrieval systems rarely fail loudly. They drift. Stale indexes, permission gaps, citations to documents that no longer exist."
linkedin_url:
---

Retrieval systems rarely fail loudly. They drift.

The demo answers perfectly because the index was built that morning from the documents in the demo folder. Six months later the same system is answering from an index that has quietly gone wrong in four ways.

The index is stale. Documents changed, the index didn't, and the agent is citing last quarter's policy with complete confidence.
The permissions drifted. A document was restricted after it was indexed, and the index doesn't know. Now the agent can surface content the user isn't cleared for.
The chunks lost their context. A table split across two chunks, a "not" separated from its sentence, a heading that made the paragraph mean something else.
The citations point at nothing. The source was deleted or moved, and the link in the answer goes to a 404.

None of these show up in an accuracy score on a fixed test set. They show up in the wild, one embarrassing answer at a time.

What works: index refresh tied to the source system's change events, permission checks at query time rather than index time, chunking that respects document structure, and a citation validator that runs before the answer goes out.

When did your index last get rebuilt, and who decided?
