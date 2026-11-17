# 2036, built in the open

Khalid approved the original four-week series on October 26, 2026, then authorized continuing five weekday posts on November 17. The original `2036` campaign remains a bounded historical record. From November 23, an effective base-schedule change keeps Monday through Friday active without an artificial end date. The horizon is a design direction, not a promise of audience growth or a prediction of technology.

## Editorial standard

Start with a safely completed outcome and work backward through the decisions, evidence, state transitions, permissions, contracts and recovery steps. Build and test the engine before polishing the interface. Early interface sketches can still validate the need. Khalid supplied the personal lesson: building the car's body before thinking through its engine cost him considerable time.

Every added post offers a concrete exercise. Claims about the teaching studio remain explicitly illustrative: it does not execute production cloud operations, certify security or demonstrate customer savings. Use the free public resources; the paid consultation offer was removed from main on October 25. Private Decision Room material is not public proof.

## Calendar

Scheduled time: **08:00 America/Phoenix, 15:00 UTC**. GitHub Actions start times are best-effort and recent runs have been hours late. A successful preview or build is not a publication receipt.

| Week | Monday | Tuesday | Wednesday | Thursday | Friday |
| --- | --- | --- | --- | --- | --- |
| Oct 26 to 30 | Existing OpenClaw commentary, already posted | Where deals actually die | Build the engine first | Retrieval is not memory | Give context an expiry date |
| Nov 2 to 6 | Include the refusal in the demo | Write the runbook before the incident | The tool contract must survive the prompt | Fabric changed the question | Approval has a version |
| Nov 9 to 13 | Price the finished work | Idempotent or it didn't happen | The write you cannot see | A migration is a change of ownership | Recovery needs a clock |
| Nov 16 to 20 | Change the room and keep the decision | The cost of seeing everything | Change one assumption on purpose | Small models, big boundaries | Hand over the proof |

The original Tuesday/Thursday dates, slugs and all publication receipts are preserved. Upcoming article wording has been reviewed for factual support and distinct teaching value. Eleven series posts fill the original campaign slots; the October 26 manual receipt in `content/linkedin_schedule.json` prevents a duplicate. The original campaign ends November 20. A separate effective base-schedule change starts November 23 and makes all five weekdays eligible for ordinary posts. The prepared continuation covers every weekday through December 18, including the former November 26 gap. See [the ongoing editorial plan](LINKEDIN_EDITORIAL_PLAN.md).

## Publishing contract

- `content/linkedin_schedule.json` owns the historical base weekdays, dated base-schedule changes, campaign dates and manual receipt. A dated base change applies from its start date until a later change replaces it; it does not rewrite earlier eligibility.
- Campaign posts require matching `series: 2036`, `linkedin_schedule: 2036` and the exact slot date. A missed campaign post is not automatically posted late. Missing or duplicate content fails instead of substituting an ordinary article.
- Ordinary publishing selects the oldest due approved article on the effective base weekdays. Through November 22 these are Tuesday/Thursday; from November 23 they are Monday through Friday. A recorded publication on the Phoenix date prevents a second tracked post. Weekends remain inactive.
- Dry runs have no LinkedIn network calls, file writes or GitHub output writes. Only dry runs may use `BUILD_DATE`. Preview selection and text are printed in the log.
- Live execution uses a durable reservation. The workflow commits `content/linkedin_pending.json` before the LinkedIn POST. An unresolved reservation blocks later runs. A confirmed receipt or definite rejection resolves it; timeouts, server errors and missing receipts keep it on hold.
- After a confirmed post, the workflow archives its receipt and commits the publication timestamp and URL. If that Git push fails, the previously committed reservation remains and blocks automatic retry. Git and LinkedIn are separate systems; there is no claim of distributed exactly-once delivery.
- To reconcile a hold, inspect the run log, receipt artifact and actual LinkedIn activity first. If the post exists, record its exact receipt and actual publication timestamp and clear the hold together. If it definitively did not publish, clear the hold with that evidence. Never clear an unknown outcome merely to get the next run green.
- Missing credentials fail visibly. `linkedin-token.yml` remains untouched. Token renewal and exact expiry must be verified from their own receipt; an old reminder is not evidence of credential state.

## Verification and measurement

Run `python -m unittest discover -s tests/linkedin -v` for offline behavior, the preserved original campaign and the next four complete publishing weeks. Build using `BUILD_DATE=2026-10-26`, a campaign date, and the first weekday of the continuing cadence. New posts use Markdown autolinks for clickable website references; the publisher removes only the autolink brackets for LinkedIn commentary.

The separate weekday conversation brief runs at 07:30 Phoenix in Codex. It researches up to three substantive comments for Khalid to review and submit. It does not post comments automatically. Monday reviews use matched 7-day and 28-day analytics windows and publisher receipts. Missing metrics stay unknown. Private metrics and drafts remain outside this public repository.

Assess content and operational problems after two weeks and direction after four. Compare useful replies, saves, reach outside the existing audience and per-post performance at matched ages. More impressions alone do not establish qualified interest or causation.
