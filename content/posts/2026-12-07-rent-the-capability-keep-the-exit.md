---
title: "Rent the capability. Keep the exit."
date: 2026-12-07
status: approved
tag: business-value
summary: "Evaluate buy-versus-build choices with a small export and replacement exercise."
linkedin_url:
visual_required: true
---

Buying a capability can be the right architectural decision.

I still want to know what leaving would involve.

Before committing to a service, I would inspect data export, identity integration, API limits, operational visibility and the parts of the workflow that become provider-specific.

Choose one thin slice and rehearse its exit with synthetic data. Export the records, interpret them elsewhere, and replace one dependency behind its contract. Record what breaks and which behavior needs fresh evaluation.

This does not require building a second production system. It requires enough evidence to distinguish a practical exit from a box labelled adapter.

The cheapest option today may remain the best option. At least the decision includes the cost of changing our minds.
