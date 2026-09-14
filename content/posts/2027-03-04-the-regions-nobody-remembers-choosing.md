---
title: "The regions nobody remembers choosing"
date: 2027-03-04
status: approved
tag: cloud
summary: "During an escalation I asked which regions were real options. Nobody in the room could say. Region choice is a decision, not a default."
linkedin_url:
---

During a database escalation, I asked which regions were real options for the workload.

Nobody in the room could answer. The primary region had been chosen years earlier by whoever created the first subscription. The paired region was whatever the platform assigned. Data residency requirements existed somewhere in a contract. None of it had been decided on purpose.

Region choice is one of those decisions that looks trivial on day one and turns out to be load-bearing.

It sets your latency floor for the users who matter.
It constrains which services and SKUs you can even use.
It determines your DR story, because failover only works to somewhere you've actually set up.
It decides whether you're compliant with the residency clause someone signed.
And it's nearly impossible to change once data has gravity.

What I do now, early in any engagement: write the region decision down as a decision. Primary, secondary, why, what's allowed to leave, and what the migration cost would be if we ever had to move. One page. Reviewed when the contracts change.

It sounds bureaucratic. It's the difference between an escalation that has options and one that doesn't.

Do you know why your workloads run where they run?
