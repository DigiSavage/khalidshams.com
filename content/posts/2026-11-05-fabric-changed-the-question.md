---
title: "Fabric changed the question"
date: 2026-11-05
status: approved
tag: data
summary: "Before a governed lakehouse the question was where is the data. After, it became who owns this layer."
linkedin_url:
---

Before a governed lakehouse, the question I heard most was "where is the data?"

After moving an estate onto Microsoft Fabric with proper medallion layering, the question changed. It became "who owns this layer?"

That's progress, even though it doesn't feel like it at first.

"Where is the data" is a discovery problem. You solve it with catalogues and tribal knowledge and a lot of Teams messages. It never really ends, because every new extract someone makes creates a new place the data might be.

"Who owns this layer" is a governance problem. Bronze is raw and owned by whoever ingests it. Silver is cleaned and conformed and owned by a data team that signs off on the contracts. Gold is shaped for consumption and owned by the people who consume it. The ownership is part of the design, not a spreadsheet maintained on the side.

Once that structure exists, AI stops being scary. An agent grounded on gold has a known owner, a known refresh, and a known set of rules. An agent grounded on "the folder someone made for the pilot" has none of that.

The lakehouse didn't make the data better. It made the ownership explicit. That's what made everything above it possible.

Which layer of your data has no owner?
