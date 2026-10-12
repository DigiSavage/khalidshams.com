# Private site control room

The public S3 build contains empty, noindex shells at `/login/` and `/admin/`, and the public contact form. Private records are fetched only after API authorization. Neither the static build, the search index, nor the art manifest contains inquiry or analytics records.

## Request boundaries

Browser → existing CloudFront distribution → `/api/*` behavior → regional API Gateway `/prod` → Lambda → four separate DynamoDB tables. The default S3 behavior and its URL rewrite function are preserved. The API behavior has no rewrite function, allows the necessary HTTP methods, forwards cookies, query strings, Origin and CSRF headers, and uses a cache policy with all TTLs zero. Lambda responses have `Cache-Control: no-store, private, max-age=0`. API Gateway stage caching and request-body logging are disabled.

CloudFront injects a generated origin secret. The API rejects direct requests without it; it does not rely on CORS. CloudFront supplies the viewer address for daily keyed abuse counters. Raw addresses are never stored in event or inquiry rows. That origin secret and access tokens remain server-side. Config backups containing origin headers must stay in the deploy script's private evidence directory, outside Git.

Authentication uses Cognito authorization code, S256 PKCE, single-use state, nonce, an HttpOnly correlation cookie and exact HTTPS callback/logout URLs. Self-registration is disabled. The owner invitation is sent by Cognito; password setup and authenticator enrollment belong to the owner. MFA is required. The application requires a signed, unexpired access token from the configured pool and client, the `site-admin/owner` scope, the `owner` group, and a live directory check for enabled status, matching subject, current group membership and enrolled software MFA on every private request. ID tokens are separately validated for audience and nonce during callback. A valid ordinary login is insufficient.

The browser holds only a random `__Host-ks-session` cookie (Secure, HttpOnly, SameSite=Lax, Path=/). Its server-side session expires after at most 15 minutes. No refresh token is retained and no bearer token is placed in localStorage. All mutations additionally require exact Origin and a session CSRF value. Logout deletes the server session and redirects through Cognito logout. Expiry clears the private UI; back/forward restoration reloads authorization.

## Storage and resource limits

- Events: UTC date partition, globally deduplicated event IDs, analytics TTL (default 90 days). Random page-instance records bind visitor, session and registered path. Engagement is bounded by elapsed page time plus five seconds of clock tolerance, a 15-second update maximum and a four-hour page total maximum.
- Inquiries: private inbox partition, validated fields, idempotent client submission UUID plus content fingerprint, revision-checked updates, status history and internal notes. Default retention 365 days, configurable 1 to 730 days.
- Sessions: opaque session hashes, one-time login state, contact challenges, random page-instance state, dedup markers, short-lived rate counters, settings and maintenance cursors. Config and metadata are separate from inquiry content.
- Audit: owner export, settings, update and deletion actions, plus coarse API health counters. Owner actions retain 365 days; health counters retain 90 days. No submitted messages or emails are logged here.

DynamoDB encryption, TTL and point-in-time recovery are enabled. Queries are bounded: 20,000 event rows and 2,000 inquiry rows per request; exports refuse incomplete results. Scan maintenance processes up to 500 rows per table every 15 minutes. Shorter retention filters reads immediately and the sweeper shortens stored TTLs. Physical TTL deletion is asynchronous. Large volumes need a rollup pipeline before raising limits; this release deliberately reports partial coverage instead of inventing full totals. Page detail includes trend, source/device mix, scroll, interactions and observed next pages.

API Gateway throttles at 10 requests/second with burst 20. Lambda reserved concurrency is 5. DynamoDB on-demand maximum read/write units are 40 per table. Application limits are per daily keyed source: six contact attempts/hour, 30 challenges/hour, 20 login starts/hour and 600 telemetry batches/hour. Contact challenges expire after 30 minutes and require at least two seconds; a honeypot and strict length/schema limits supplement rate controls. These reduce casual abuse, not sophisticated distributed attacks. Throttles and caps can reject legitimate bursts; they are not dollar-denominated spending guarantees.

## Public API contract

All mutations require exact same Origin; JSON bodies are at most 24 KB.

| Method and path | Result |
| --- | --- |
| GET `/api/config` | Service availability, collection switch, event version. No credentials or records. |
| GET `/api/auth/start` | Redirect to Cognito with state, nonce and S256 challenge. |
| GET `/api/auth/callback` | Validates code exchange, owner and MFA; sets opaque session, redirects to admin. |
| GET `/api/contact/challenge` | Short-lived challenge bound to a keyed source. |
| POST `/api/contact` | Validated inquiry. `stored:true` only after successful DynamoDB persistence, including identical retries. |
| POST `/api/events` | One to twelve strict version-1 consented events; accepted/duplicate counts. Owner-cookie and bot-UA exclusions. |

## Private API contract

Every endpoint below reauthorizes the session. GETs are private too.

| Method and path | Result |
| --- | --- |
| GET `/api/auth/session` | Owner flag, expiry and CSRF value. |
| POST `/api/auth/logout` | Invalidates server session, clears cookie, returns Cognito logout URL. |
| GET `/api/admin/insights?from=YYYY-MM-DD&to=YYYY-MM-DD` | Phoenix date-range aggregates, comparable prior window, completeness and health. |
| GET/PUT `/api/admin/settings` | Collection and separate retention limits. |
| GET `/api/admin/inquiries?q=&status=&tests=false` | Authorized inbox, excluding marked tests unless requested. |
| PATCH `/api/admin/inquiries/<uuid>` | Revision-checked status and optional internal note. |
| DELETE `/api/admin/inquiries/<uuid>` | Requires exact `DELETE <uuid>` confirmation. |
| GET `/api/admin/export?kind=analytics\|inquiries&from=&to=` | Separate CSV export; user spreadsheet formulas neutralized. |
| DELETE `/api/admin/analytics` | Requires exact date-range confirmation, removes at most 2,000 rows, indicates whether another deliberate batch is needed. |

No mailbox integration exists. Email replies are drafts opened in the owner's email client. A mailto click is not a received inquiry.

## Isolation and failure behavior

The test server under `tests/admin/` uses moto tables and signed fixture JWTs; its fixture login route is never packaged with Lambda or copied to `dist`. It is not a production authentication bypass. The production dashboard has no sample counts. If backend configuration is missing, telemetry stays off, the contact form points to existing email/LinkedIn alternatives, and the owner shell explains that the service is unavailable.
