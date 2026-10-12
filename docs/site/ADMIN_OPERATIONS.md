# Site admin operations

## Provisioning prerequisites

Use an authorized profile or AWS CloudShell session in the account that owns CloudFront distribution `E14OT21V7ATYP1` and the `khalidshams.com` S3 origin. The existing GitHub Actions deployment identity is documented for static storage and invalidation only. Do not broaden it or extract its secrets for this service.

The provisioning principal needs CloudFormation create/update/change-set execution, service provisioning for Cognito, API Gateway, Lambda, EventBridge, the four DynamoDB tables, Secrets Manager, CloudWatch Logs, and the generated Lambda IAM role including PassRole restricted to Lambda. It also needs a private deployment-artifact S3 bucket and CloudFront get/update distribution, create/update cache/origin policies and invalidation. The runtime role is separate: table CRUD/query/scan/batch access only on this stack's four tables, read only on this origin secret, owner lookup/group lookup only on this pool, and Lambda logging. It cannot modify CloudFront, create users or publish the public website.

`infra/site-admin/template.json` is SAM/CloudFormation; `deploy.py` packages Linux ARM64 Python 3.12 dependencies directly and submits a CloudFormation change set. It does not need Docker or local long-lived AWS keys. Use a temporary session where available. Install boto3 in the operator environment if needed.

```bash
python infra/site-admin/deploy.py \
  --profile SITE_PROVISIONING_PROFILE \
  --owner-email khalidshams@gmail.com \
  --domain-prefix khalidshams-owner-UNIQUE_SUFFIX \
  --evidence-dir ~/private-site-admin-evidence
```

The initial command is read-only except a local private config backup. It confirms account, aliases and legacy logging. To execute the reviewed stack and connect the API, use the same command with `--deploy --connect`. In CloudShell omit `--profile`. Keep the domain prefix stable on future updates. The bootstrap email is the existing public owner contact address; use the owner's chosen address if it differs.

The deploy script creates a dedicated private, encrypted, versioned artifact bucket with Block Public Access. Lambda source is never uploaded under the public website bucket. Stack resources are tagged `Project=khalidshams.com-site-admin`. It backs up the current CloudFront configuration with file mode 0600, requires the expected site alias, refuses to take over an API behavior owned by another service, preserves the default S3 behavior, uses a fresh ETag, waits for deployment, and invalidates `/api/*`. Existing distribution config backups may contain origin secrets: never commit them.

Outputs: `ApiHost`, `PoolId`, `ClientId`, `OriginSecretArn`, `NoCachePolicyId`, `OriginRequestPolicyId`. Lambda environment references these resources plus the four table names. The origin secret is retrieved server-side and sent only in the CloudFront origin header. It is not an authentication credential for owner APIs.

## Owner setup and acceptance

1. Open `/login` and `/login/`; both must resolve to the owner sign-in page. The API availability check must enable sign-in only when connected.
2. Cognito sends the secure owner invitation. The owner completes the temporary-password change and authenticator setup themselves. If Cognito returns before MFA is registered, `/login/?setup=mfa` provides an isolated enrollment flow: request a private setup key, add it as a time-based authenticator entry, then verify the current six-digit code. This setup cookie cannot authorize private APIs. Do not paste passwords, temporary credentials, MFA seeds or codes into source, logs or chat. The app denies access until enrolled software MFA and current owner membership are verified.
3. Open `/admin/`; verify an honest empty dashboard. In a separate signed-out browser, call every private endpoint and verify 401/no-store, without any records. Check responses have no `Age` cache hit and do not fall through to S3.
4. Submit one explicitly marked inquiry at `/contact/?ks-test=1` with clearly synthetic, non-sensitive content. Success must mean persisted storage. Sign in as owner, select “Include marked test inquiries,” find the same reference, update status/add a note, reload and verify persistence. It must be absent from public APIs, production inquiry totals, build files and search.
5. In a separate non-owner test browser visit `/?ks-test=1`, allow measurement, interact, hide/reopen the page and navigate into a lesson. Check accepted/deduplicated rows through authorized inspection. Marked traffic must remain absent from production aggregates. Do not introduce fake unmarked production traffic to make the dashboard look populated.
6. Verify logout invalidates the session, expiry clears UI, and disabled or de-grouped owners lose access on the next request. These checks require the real deployed pool and cannot be replaced by fixture results.
7. Repeat the mobile composition and existing Studio/site gates against the released build. Record stack status, public deploy run, exact commit, headers, screenshots and test totals in `ADMIN_RELEASE_REPORT.md`.

## Logs, data care and recovery

The Lambda log group has 14-day retention and logs failure categories and route categories, not raw payloads, tokens, IPs or inquiry fields. API Gateway execution logging and body tracing are off; this stack does not create an access-log destination. AWS services still process network metadata. The existing CloudFront legacy logging configuration must be read from the actual site account; additionally inspect CloudWatch delivery sources for newer CloudFront standard logging, real-time log associations, existing S3 server-access logging and CloudTrail event selectors/lifecycle rules. Do not assert that all logs are off based only on a single legacy logging flag. Record actual destinations/retentions without exposing log contents.

At the initial attempt, Safari account `926952122279` returned `NoSuchDistribution` for `E14OT21V7ATYP1` and no matching `khalidshams.com` distribution. No resources were provisioned there. On 12 October, Chrome account `430110755505` was verified and the stack deployed successfully. The live API is connected; owner password/MFA setup remains required. The stable Cognito domain prefix is `khalidshams-owner-430110755505`.

Analytics default retention is 90 days (1 to 90 configurable); inquiry default is 365 (1 to 730). Session/login/challenge and event dedup TTLs are short-lived. Reads always filter expiry; shortened retention takes effect immediately. The sweeper checks up to 500 rows/table every 15 minutes and saves its cursor. TTL deletion is asynchronous, so physical removal can lag. Dedup markers survive analytics deletion until their two-day TTL to prevent replay resurrecting deleted observations within the one-day acceptance window.

DynamoDB point-in-time recovery is enabled; table deletion and replacement retain data. Restore into new private tables, keep the API closed, reapply current retention and recorded deletion actions, validate owner authorization, then change environment bindings. Never publish a recovered database or export to static storage. Audit rows contain deletion identifiers so restored inquiries can be removed again. Analytics audit subjects contain deleted epoch ranges. Retained backups can contain already deleted records during the provider's recovery window.

Export inquiry and aggregate analytics CSVs separately through the authenticated API. Formula-leading user fields are neutralized, but exports still contain private inquiry data and must be stored privately. A too-large export fails rather than silently omitting records. Inquiries exceeding 2,000 retained rows need an explicit pagination/partition upgrade; do not hide the partial indicator.

## Rollback

For a frontend regression, revert the release through a reviewed PR and verify the normal S3/CloudFront deployment. Do not change the LinkedIn workflows or publisher metadata. To stop telemetry, use the owner collection switch; the public library continues to function. To isolate an API problem, remove only this stack's `/api/*` behavior/origin using a fresh ETag and preserve concurrent CDN changes. The public shells then show unavailable states. Do not blindly restore an old full-distribution backup over newer changes. Roll Lambda back to the previous versioned artifact via CloudFormation. Preserve tables, pool and backups. Re-enabling an API requires the same private-cache and authorization checks as an initial release.

## Cost assumptions, checked 2026-10-12

Illustrative monthly scenario, not an invoice or spending cap: 100,000 API requests, 100,000 Lambda invocations averaging 200 ms at 512 MB, one million DynamoDB write request units and one million read request units, one origin secret, and one owner. The scenario is deliberately stated in billable request units: transactional writes cost additional units, retries/rate counters add work, and actual usage can differ.

- Regional REST API: approximately $0.35 for 100,000 requests at $3.50/million, before transfer. [AWS API Gateway pricing](https://aws.amazon.com/api-gateway/pricing/).
- Lambda ARM compute: approximately $0.13 for 10,000 GB-seconds at $0.0000133334/GB-second, plus $0.02 requests, before free tier. [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/).
- DynamoDB request units: approximately $0.625 writes plus $0.125 reads at the quoted Standard on-demand rates, before storage, PITR, larger items and restores. [AWS DynamoDB pricing](https://aws.amazon.com/dynamodb/pricing/).
- One secret: approximately $0.40/month plus API calls at $0.05/10,000. [AWS Secrets Manager pricing](https://aws.amazon.com/secrets-manager/pricing/).
- Cognito Lite/Essentials has a 10,000 MAU account/organization free tier for eligible direct/social sign-ins. Verify shared usage and tier; do not assume every account has unused allowance. Email delivery can add charges. [AWS Cognito pricing](https://aws.amazon.com/cognito/pricing/).

Those variable components are roughly $1.65/month under the stated assumptions, excluding CloudFront, storage, PITR, logs/metrics, artifact versions, data transfer, taxes and abuse. Actual retained volume and API traffic must be measured after launch. Set a site-specific AWS Budget alert through the owner's approved billing process; a budget alert does not stop spending. This deployment does not silently change account-wide budgets or billing controls.

Queries also cap serialized returned rows at 1.5 MB per partition query and flag partial coverage, protecting Lambda/API response and memory limits even when records have lengthy notes. Total internal note text per inquiry is limited to 20,000 characters, in addition to individual note and history-count bounds.
