---
title: "What building on AWS taught me about boring"
date: 2026-12-01
status: approved
tag: engineering
summary: "I built and run a knowledge platform on AWS, solo. The choices that held up were the boring ones."
linkedin_url:
---

I design, build, and operate a knowledge platform on AWS, solo. MongoDB for the documents, S3 for the audio and media, a small set of services in front.

It does some interesting things. Word-by-word recitation with per-word highlighting. Audio-based verse detection that takes what someone is reciting and jumps the reader to the matching passage. AI features with explicit provenance rules about what the model may and may not assert.

None of that is what keeps it running.

What keeps it running is a stack of deliberately boring choices. Managed services wherever one exists. One way to deploy, scripted, and used every time. Backups tested by restoring them, not by checking that the job ran. A cost alarm set lower than I think I need. Logs I actually read.

When you're the whole team, every clever decision is a future page at midnight. Boring infrastructure is what lets the product be interesting.

I think this applies at enterprise scale too, it's just easier to see when there's nobody else to blame. The platform should be dull. The product on top of it should be the thing people talk about.

What's the most interesting part of your infrastructure, and does it need to be?
