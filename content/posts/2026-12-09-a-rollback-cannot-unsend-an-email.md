---
title: "A rollback cannot unsend an email"
date: 2026-12-09
status: approved
tag: reliability
summary: "Separate reversible state changes from external effects that require a compensating action."
linkedin_url:
visual_required: true
---

The deployment rolled back. The email is still in somebody's inbox.

I separate technical rollback from business recovery before a workflow is allowed to act.

For each operation, mark whether it can be reversed, compensated or only acknowledged. A database transaction and an external message do not share the same undo button.

Define the owner, evidence and next action for each outcome. A correction message may require human review; automatically sending another message could make the situation worse.

In a synthetic test, fail the workflow after an external effect but before local confirmation. Inspect what happened and how the operator establishes the truth.

Keep that recovery path next to the action contract.

"We can redeploy" answers a different question from "we can put this right."
