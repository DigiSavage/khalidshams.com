---
title: "How a tenant earns the next tier"
date: 2027-02-04
status: approved
tag: architecture
summary: "Tenants get upgraded when someone complains loudly enough. Or they get upgraded when they meet written criteria. Only one of those scales."
linkedin_url:
---

There are two ways a tenant gets upgraded to a higher service tier.

Someone complains loudly enough. Or the tenant meets written criteria.

Only one of those scales. Across 1,000+ tenant databases, the loudest customer method produced an estate where cost had no relationship to need, support couldn't explain why anything was where it was, and every escalation reopened the same argument.

The criteria we wrote down were not sophisticated. Sustained utilisation over a threshold for a defined window. A contractual commitment that required a specific SLA. A workload pattern that matched the enterprise profile rather than the trial profile. Meet two of three and you graduate. Miss them for a defined window and you're reviewed for the tier below.

What changed wasn't the tiering. It was that a support engineer could apply the rule on a Tuesday afternoon without a meeting, and the answer would be the same one an architect would have given.

That's the real test of a rule: can the person closest to the problem apply it without you?

Multi-tenant platforms don't fail because the rules are wrong. They fail because the rules are in someone's head.

Who can apply your tiering rules without a meeting?
