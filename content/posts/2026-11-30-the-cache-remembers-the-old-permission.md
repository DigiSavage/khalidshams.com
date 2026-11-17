---
title: "The cache remembers the old permission"
date: 2026-11-30
status: approved
tag: security
summary: "Cached content must remain subject to current access rules at the point it is served."
linkedin_url:
visual_required: true
---

The answer is cached. The employee's access changed.

Which fact wins?

I want current permission to decide what may be served, even when yesterday's answer is already waiting in memory.

A useful design record names the caller, tenant, source permissions, cache scope, expiry and the check that runs before delivery. The exact cache strategy depends on the system; a tenant label alone does not prove isolation.

Test with synthetic users. Let one user retrieve a restricted answer, revoke access, then repeat the request. Try another user and another tenant too.

Inspect what is actually returned, including citations and snippets. A blocked full document with a revealing summary is still a failed boundary.

A fast answer should not be an old permission decision in disguise.
