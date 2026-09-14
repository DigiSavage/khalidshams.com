---
title: "Least privilege for machines"
date: 2027-02-23
status: approved
tag: security
summary: "People get least privilege reviews. Service principals get created once and never looked at again."
linkedin_url:
---

People get least privilege reviews. Service principals get created once and never looked at again.

That's the pattern in most estates I've assessed. Human identities have joiners, movers, leavers, access reviews, PIM. Machine identities have a creation date and, frequently, Contributor on the subscription because that's what made the pipeline work on day one.

Now put an AI agent on top of that service principal. The agent inherits everything the identity can do, and the identity can do almost anything.

The fix is the same discipline applied to non-human identities.

Managed identities over secrets wherever the platform supports it. No credential to leak.
One identity per workload, scoped to what that workload touches. Not one identity per team.
Privileged actions behind just-in-time elevation, for machines as well as people.
An access review cadence for service principals with a named owner for each. Unowned identities get disabled.
For agents specifically: the agent acts as the user, with the user's permissions, and the service identity only does what no user could.

This isn't a security nicety. It's the difference between an agent that can be deployed to people handling sensitive data and one that can't.

When did you last review what your service principals can do?
