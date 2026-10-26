# 2036, built in the open

Khalid approved five LinkedIn posts a week for four weeks on October 26, 2026. This is a bounded editorial experiment, not a promise of audience growth. The horizon is 2036; the evidence and exercises are available today.

## Editorial standard

Start with a safely completed outcome and work backward through the decisions, evidence, state transitions, permissions, contracts and recovery steps. Build and test the engine before polishing the interface. Early interface sketches can still validate the need. Khalid supplied the personal lesson: building the car's body before thinking through its engine cost him considerable time.

Every added post offers a concrete exercise. Claims about the teaching studio remain explicitly illustrative: it does not execute production cloud operations, certify security or demonstrate customer savings. Use the free public resources; the paid consultation offer was removed from main on October 25. Private Decision Room material is not public proof.

## Calendar

Scheduled time: **08:00 America/Phoenix, 15:00 UTC**. GitHub Actions start times are best-effort and recent runs have been hours late. A successful preview or build is not a publication receipt.

| Week | Monday | Tuesday | Wednesday | Thursday | Friday |
| --- | --- | --- | --- | --- | --- |
| Oct 26–30 | Existing OpenClaw commentary, already posted | Where deals actually die | Build the engine first | Retrieval is not memory | Give context an expiry date |
| Nov 2–6 | Include the refusal in the demo | Write the runbook before the incident | The tool contract must survive the prompt | Fabric changed the question | Approval has a version |
| Nov 9–13 | Price the finished work | Idempotent or it didn't happen | The write you cannot see | A migration is a change of ownership | Recovery needs a clock |
| Nov 16–20 | Change the room and keep the decision | The cost of seeing everything | Change one assumption on purpose | Small models, big boundaries | Hand over the proof |

The existing Tuesday/Thursday files are unchanged. Eleven new native text posts fill the remaining slots; the October 26 manual receipt in `content/linkedin_schedule.json` prevents a duplicate. M/W/F eligibility stops after November 20. Ordinary Tuesday/Thursday scheduling continues; November 26 is a pre-existing queue gap, not a promised publication.

## Publishing contract

- `content/linkedin_schedule.json` owns the base weekdays, campaign dates and manual receipt.
- Campaign posts require matching `series: 2036`, `linkedin_schedule: 2036` and the exact slot date. A missed campaign post is not automatically posted late. Missing or duplicate content fails instead of substituting an ordinary article.
- Tuesday/Thursday selects the oldest due ordinary article. A recorded publication on the Phoenix date prevents a second tracked post.
- Dry runs have no LinkedIn network calls, file writes or GitHub output writes. Only dry runs may use `BUILD_DATE`. Preview selection and text are printed in the log.
- Live execution uses a durable reservation. The workflow commits `content/linkedin_pending.json` before the LinkedIn POST. An unresolved reservation blocks later runs. A confirmed receipt or definite rejection resolves it; timeouts, server errors and missing receipts keep it on hold.
- After a confirmed post, the workflow archives its receipt and commits the publication timestamp and URL. If that Git push fails, the previously committed reservation remains and blocks automatic retry. Git and LinkedIn are separate systems; there is no claim of distributed exactly-once delivery.
- To reconcile a hold, inspect the run log, receipt artifact and actual LinkedIn activity first. If the post exists, record its exact receipt and actual publication timestamp and clear the hold together. If it definitively did not publish, clear the hold with that evidence. Never clear an unknown outcome merely to get the next run green.
- Missing credentials fail visibly. `linkedin-token.yml` remains untouched. The existing November 9 token-renewal reminder remains relevant.

## Verification and measurement

Run `python -m unittest discover -s tests/linkedin -v` for offline behavior and the actual four-week queue. Build using `BUILD_DATE=2026-10-26`, a campaign date, and the first weekday after the campaign. New posts use Markdown autolinks for clickable website references; the publisher removes only the autolink brackets for LinkedIn commentary.

The separate weekday conversation brief runs at 07:30 Phoenix in Codex. It researches up to three substantive comments for Khalid to review and submit. It does not post comments automatically. Monday reviews use matched 7-day and 28-day analytics windows and publisher receipts. Missing metrics stay unknown. Private metrics and drafts remain outside this public repository.

Assess content and operational problems after two weeks and direction after four. Compare useful replies, saves, reach outside the existing audience and per-post performance at matched ages. More impressions alone do not establish qualified interest or causation.
