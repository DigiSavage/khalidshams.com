---
title: "Three signs a platform team is losing"
date: 2027-03-16
status: approved
tag: cloud
summary: "Platform teams don't fail loudly. They fail through exceptions, shadow environments, and everyone waiting."
linkedin_url:
---

Platform teams don't fail loudly. They fail through three quiet signals.

Exceptions become the process. The first exception was reasonable. By the twentieth, the exception path is faster than the standard one, and every new workload asks for it. The platform is now whatever people have been granted, not what was designed.

Shadow environments appear. A business unit gets tired of waiting and stands up its own subscription, its own pipeline, its own copy of the data. Nobody announces it. You find it on the invoice, or in an incident.

Everyone is waiting. Requests queue. The platform team is the bottleneck for every change, and the people waiting have started planning around it rather than through it.

I've seen these signals in landing zones that were technically excellent. The problem was never the Bicep. It was that the platform team was measured on control and the workload teams were measured on delivery, and nobody was measured on both.

The fixes are unexciting. Self-service for the common cases so the team only handles the unusual ones. A published exception process with a time limit on every exception. A funding model where the platform is a shared cost, not a favour. And a monthly number for how long a workload team waits.

Which of the three do you see at work?
