---
title: "Backups are not disaster recovery"
date: 2027-03-25
status: approved
tag: engineering
summary: "Having backups tells you your data exists somewhere. It tells you nothing about how long it takes to be a system again."
linkedin_url:
---

Having backups tells you your data exists somewhere. It tells you nothing about how long it takes to be a system again.

I've seen teams answer "do you have DR" with "yes, we have backups" and mean it sincerely. Then a real failure happens and the timeline looks like this: find the backup, find someone with permission to restore it, discover the restore takes eleven hours, discover the application also needs a config store that wasn't backed up, discover the DNS still points at the dead region.

Backups are one ingredient. Disaster recovery is the whole recipe, with times attached.

RPO: how much data are you willing to lose? That's a business decision, and it drives backup frequency.
RTO: how long can you be down? That drives everything else, and it's almost always shorter than the restore actually takes.
Dependencies: what else has to come back, in what order, for the system to work?
Access: who can execute the restore at 2am, and do they still have permission?
Proof: when did you last restore for real and measure it?

On the AWS platform I run alone, the monthly restore test is the least enjoyable thing I do. It's also the only reason I'm confident the RTO on my own runbook is true.

What's your actual restore time, not the one on the slide?
