---
title: "Don't let the pilot pick the platform"
date: 2027-04-13
status: approved
tag: business-value
summary: "Pilots make platform decisions by accident. Whatever was convenient in week two becomes the standard for years."
linkedin_url:
---

Pilots make platform decisions by accident.

Someone needs a database quickly, so they use whatever the pilot environment had. Someone needs a model, so they use the one with the easiest API key. Someone needs to deploy, so they script it by hand. Six months later the pilot is a production system, and every one of those convenient choices is now load-bearing.

Nobody decided any of it. It was just what was there in week two.

I've come to treat the pilot phase as the most dangerous time for architecture, precisely because nobody thinks architecture matters yet. So a few rules I hold to, even when the pilot is small:

The pilot runs on the platform the production system would run on. If that's slower to set up, that's the real cost of the pilot, and it should be visible.
The pilot's data lives where governed data lives. No "temporary" copies.
Every convenience shortcut gets written down as a decision with an expiry date.
The exit criteria include "what would we have to rebuild," and that list gets reviewed before the go decision.

A pilot should test the idea, not quietly choose the infrastructure for the next five years.

What in your production estate was chosen by a pilot?
