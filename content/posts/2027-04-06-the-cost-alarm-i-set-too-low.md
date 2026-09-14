---
title: "The cost alarm I set too low"
date: 2027-04-06
status: approved
tag: engineering
summary: "I set the cost alarm on my own platform lower than I thought I needed. It has paid for itself three times."
linkedin_url:
---

I set the cost alarm on my own AWS platform lower than I thought I needed. It has paid for itself three times.

Once for a media processing job that retried in a loop over a weekend. Once for a storage class that turned out to charge for retrievals in a way I hadn't read carefully. Once for a test environment I forgot existed.

None of those were dramatic. Each would have been a few hundred dollars by the time a monthly invoice surfaced them. The alarm surfaced them in hours.

What I've learned running things alone is that cost is the fastest signal you have. Errors need a log to be read. Latency needs a user to complain. Cost just accumulates, quietly, and it's measured for you for free.

So the rules I follow, and recommend to teams far larger than me:

Budgets per environment, not per account. Production and test should never share an alarm.
Thresholds set at "surprising," not "catastrophic." You want to hear about the anomaly, not the disaster.
Daily granularity, because monthly is a post-mortem.
Someone who actually receives the alert and has permission to act on it.

An alarm you set too high is a decoration. Set it low enough to be occasionally annoying.

When did your cost alarm last fire, and was it useful?
