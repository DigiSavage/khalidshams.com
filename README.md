# khalidshams.com

The source for [khalidshams.com](https://khalidshams.com) — my portfolio and a running record of what I'm writing about agentic AI, cloud architecture, and the work of turning demos into systems that survive production.

I built this the way I build anything I expect to keep running without me hovering over it: content in plain files, a build that's deterministic, and a pipeline that does the boring parts on a schedule.

## How it works

```
content/posts/*.md  ──►  build.py  ──►  dist/  ──►  S3  ──►  CloudFront  ──►  khalidshams.com
        │
        └──►  scripts/publish_linkedin.py  ──►  LinkedIn (Tue/Thu 8am Phoenix)
```

- **Content is Markdown with frontmatter.** Every post in `content/posts/` carries a `date`, a `status` (`draft` → `approved` → `published`), a `tag`, and a `summary`. Nothing else is required.
- **Every post has a card.** `content/images/<slug>.png` is a 1200×1200 typographic card rendered by `tools/make_cards.py` from the specs in `tools/cards.py`. It goes to LinkedIn with the post and becomes the post page's share image.
- **The site builds itself.** `build.py` renders the home page, a `/writing/` index, one page per post, an RSS feed, a sitemap, and `robots.txt`. A post appears on the site the day its `date` arrives (America/Phoenix) if it's `approved` or `published`. Drafts never leave the repo.
- **Deploys are automatic.** `deploy.yml` runs on every push to `main` and once a day. It builds, syncs `dist/` to S3, and invalidates CloudFront. The daily run is what lets a date-gated post go live on the right morning even if nobody touches the repo.
- **LinkedIn is distribution, not the source of truth.** `publish.yml` runs Tuesday and Thursday mornings, picks the oldest `approved` post whose date has arrived, uploads its card and posts both through the LinkedIn API, then writes the resulting post URL back into the Markdown file and commits it as `published`. The site redeploys with a "Read on LinkedIn" link.
- **Approve-then-publish.** I review everything before it gets a `status: approved`. If the approved queue runs dry on a scheduled morning, the workflow fails loudly so I get an email instead of silence.

## Running it locally

```bash
pip install -r requirements.txt
python build.py                      # builds today's view into dist/
BUILD_DATE=2026-12-01 python build.py  # preview a future date
python -m http.server -d dist 8000
```

## Secrets and permissions

The deploy identity is an IAM user scoped to `s3:PutObject`/`GetObject`/`ListBucket` on one bucket and `cloudfront:CreateInvalidation` on one distribution. It deliberately cannot delete anything. Credentials live only in GitHub Actions secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `LINKEDIN_ACCESS_TOKEN`).

LinkedIn member tokens expire after roughly 60 days; `scripts/linkedin_auth.py` walks the OAuth flow to mint a new one.

## Stack

Python 3.12 · `markdown` · GitHub Actions · S3 · CloudFront · ACM · Route 53. No framework, no JavaScript build step, no database. The whole site is a few hundred kilobytes and renders in one paint.
