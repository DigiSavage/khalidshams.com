# Measurement dictionary, version 1

Collection is off until the API is available, its collection switch is on, and a visitor explicitly allows measurements. Global Privacy Control, an explicit owner browser opt-out, and authenticated owner cookies exclude collection. Local development and previews are excluded unless explicitly marked `?ks-test=1`; marked rows remain excluded from production aggregates. Only controlled acceptance tests should use that marker. Public events are untrusted even after validation.

Consent expires after 90 days. Random first-party visitor/session identifiers are created only after consent and removed on revocation; no fingerprinting. Expired consent clears old identifiers before another choice. Existing lesson progress storage remains independent. Reloads create new page instances. Back/forward cache restoration creates a new page instance without counting time hidden in cache. Sessions restart after 30 minutes without observed activity; crossing that boundary also creates a new page instance.

| Measure | Meaning and denominator |
| --- | --- |
| Observed visitors | Union of consenting random browser IDs over the selected range. Never a sum of daily uniques and never exact people. |
| Sessions | Distinct session IDs with observed pageviews. Multiple tabs share a browser's session; concurrent updates can race, so this is an observation. |
| Pageviews | Distinct registered page instances; retries reuse event IDs and are deduplicated server-side. |
| Total page engagement | Sum of accepted visible active-time updates. Simultaneous tabs can overlap. This is not deduplicated human attention. |
| Average active time | Total accepted engagement divided by page instances with an engagement measurement. Pages without measurements are unavailable, not assumed zero. |
| Active in last 5 minutes | Sessions with a positive engagement event timestamp in the last five minutes, independently queried from the selected report range. |
| Entrances / exits | First / last observed page per session within the selected window; clipped windows and blockers can conceal navigation. |
| Scroll | Page instances reaching 25%, 50%, 75% or 100% of the scrollable page. |
| Sources | Referring domain only, including `direct`; this is per-page observed referrer, not guaranteed acquisition attribution. |
| Campaign | Only `linkedin`, `newsletter`, `community`, or `direct`. Other query values are discarded. |
| Journeys | Sessions observed in each named section; contact-click numerator is those sessions with a contact-link click in the selected period. Association, not causation. |
| Stored inquiries | Validated website submissions retained in DynamoDB, excluding marked tests; unrelated to email/LinkedIn click totals. |
| LCP | Mean observed browser Largest Contentful Paint, in milliseconds. No server uptime inference. |
| Client errors | Generic script-error events with no messages, stack traces, URLs or form contents. Missing observations display unavailable. |

Timing ticks every 15 seconds, counts only while visible and within 30 seconds of pointer, key, touch or scroll activity, and flushes on visibility changes/pagehide using beacon or keepalive. A delayed timer accrues at most 15 seconds, conservatively losing unmeasured time. Queues retain up to 120 events, batches contain at most 12. Network failures retain IDs for retry; malformed 400 batches are discarded. Beacon deliveries may be resent, but server deduplication prevents double counting. Server-side page ownership, timestamp window (one day behind to 60 seconds ahead), plausible elapsed duration and a four-hour page total bound reject fabricated time accumulation. These are bounds, not proof a person paid attention.

The event allowlist is `pageview`, `engagement`, `scroll`, `lesson_start`, `lesson_complete`, `workflow_control`, `design_download`, `tool_use`, `contact_open`, `outbound_email`, `outbound_linkedin`, `performance`, `client_error`. Fields: `v,id,visitor,session,page,path,at,name,value,target,referrer,campaign,device,browser,consent,test`. UUIDs must be canonical. Paths come from the public build allowlist; targets and broad device/browser categories are enums. No arbitrary metadata, query strings, fragments, searches, form values, email, message contents or full referrer URLs are accepted.

Dates use America/Phoenix. A report's prior period has the same calendar span; an ongoing current day compares only the equivalent elapsed portion in the prior window. Comparisons are unavailable if collection start, retention or query bounds make either window incomplete, or when a positive prior denominator is absent. Current-period and previous-period inquiry totals use their corresponding windows. Page trend counts are daily; unique visitors are calculated independently across the entire chosen range.

Consent choices, blocked scripts, cleared storage, multiple devices, strict rate limits and incomplete bot filtering all affect coverage. API health counts include tests and rejected attempts; production traffic aggregates exclude marked test events. Rejected malformed batches may lack a trustworthy event count, so the dashboard also shows rejected batch counts. An API or browser error is not an uptime monitor.
