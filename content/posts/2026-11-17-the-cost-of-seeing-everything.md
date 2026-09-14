---
title: "The cost of seeing everything"
date: 2026-11-17
status: approved
tag: security
summary: "Logging everything into Sentinel is a bill, not a strategy. Decide what you need to detect first."
linkedin_url:
---

"Send everything to Sentinel" is a bill, not a security strategy.

I've seen the invoice that comes from that sentence. Ingestion priced per gigabyte, every verbose diagnostic log from every subscription flowing in, and a SOC drowning in data it never wrote a single detection for.

Seeing everything feels safe. It isn't. It's expensive noise with a false sense of coverage.

The approach that worked, on the security strategy work I contributed to, went the other way round. Start from what you need to detect. Privileged role activation. Impossible travel. Data leaving a boundary it shouldn't. New service principals with broad rights. Then trace backwards: which sources actually feed those detections, at what verbosity, and with what retention.

Everything else goes to cheap storage, or doesn't get collected until there's a detection that needs it.

The result was a smaller pipe, a sharper set of alerts, and analysts who could explain why each source existed. It also meant the AI-assisted investigation tooling had a signal-rich dataset to work with rather than a landfill.

Visibility is a design decision with a price. Treat it like one.

What percentage of your log ingestion feeds a detection someone actually maintains?
