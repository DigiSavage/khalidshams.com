---
title: "Build the engine first"
date: 2026-10-28
status: published
tag: architecture
summary: "Work backward from the finished job, then prove the backend before polishing its interface."
linkedin_url: https://www.linkedin.com/feed/update/urn:li:share:7521301407157829633/
series: 2036
linkedin_schedule: 2036
linkedin_published_at: 2026-10-28T13:06:35-07:00
---

I built the car’s body before thinking through its engine. In software, that mistake cost me far more time than I expected.

Now I plan like reverse chess. Start with the final position: what must be true for someone to finish the job safely? Work backward through the evidence, state changes, permissions and failure paths.

Then build the engine first. Prove one complete path through the backend, including a failed attempt, before polishing the interface.

Early UI sketches still help test whether we are solving the right problem.

“2036, built in the open” is my design horizon, not a forecast. Start here: change one requirement and inspect what else must change.
<https://khalidshams.com/method/engagement/#decision>
