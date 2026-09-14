#!/usr/bin/env python3
"""
Post the next approved note to LinkedIn as the authenticated member.

Selection: the OLDEST post with status `approved`, date <= today (Phoenix),
and no linkedin_url yet. On success the post file is updated in place
(status: published, linkedin_url: ...). The workflow commits that change.

Env:
  LINKEDIN_ACCESS_TOKEN   required to post (openid profile w_member_social)
  LINKEDIN_VERSION        optional, YYYYMM; defaults to last month
  DRY_RUN=1               select + print, no network write, no file change
  SCHEDULED=1             set by the scheduled workflow; if the queue is
                          completely empty on a scheduled run we exit 1 so
                          GitHub emails a reminder to write more.
  BUILD_DATE=YYYY-MM-DD   override "today" (testing)

Outputs (GITHUB_OUTPUT): published=true|false, title=<post title>
"""
from __future__ import annotations
import json, os, re, sys, urllib.request, urllib.error
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "content" / "posts"
TZ = timezone(timedelta(hours=-7))
API = "https://api.linkedin.com"


def out(k: str, v: str) -> None:
    p = os.environ.get("GITHUB_OUTPUT")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"{k}={v}\n")


def today() -> date:
    if os.environ.get("BUILD_DATE"):
        return date.fromisoformat(os.environ["BUILD_DATE"])
    return datetime.now(TZ).date()


def default_version() -> str:
    d = datetime.now(timezone.utc).replace(day=1) - timedelta(days=1)
    return d.strftime("%Y%m")


def parse(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] == '"':
                v = v[1:-1].replace('\\"', '"')
            meta[k.strip()] = v
    return meta, m.group(2).strip()


def little_text(s: str) -> str:
    """LinkedIn 'little text' requires these characters escaped in commentary."""
    return re.sub(r"([\\\|\{\}\@\[\]\(\)\<\>\#\*\_\~])", r"\\\1", s)


def api(method: str, path: str, token: str, body=None, version=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Restli-Protocol-Version", "2.0.0")
    if version:
        req.add_header("LinkedIn-Version", version)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data, timeout=30) as r:
            return r.status, dict(r.headers), r.read().decode() or "{}"
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()


IMAGES = POSTS.parent / "images"


def image_for(path) -> "Path | None":
    """content/images/<slug>.png, where slug is the filename without the date prefix."""
    m = re.match(r"\d{4}-\d{2}-\d{2}-(.+)$", path.stem)
    if not m:
        return None
    img = IMAGES / f"{m.group(1)}.png"
    return img if img.exists() else None


def upload_image(token: str, version: str, author: str, img_path) -> "str | None":
    """LinkedIn Images API: initializeUpload -> PUT bytes -> return urn:li:image:..."""
    status, _, raw = api("POST", "/rest/images?action=initializeUpload", token,
                         {"initializeUploadRequest": {"owner": author}}, version)
    if status != 200:
        print(f"::warning::image initializeUpload failed ({status}): {raw[:300]} — posting without image")
        return None
    v = json.loads(raw)["value"]
    upload_url, urn = v["uploadUrl"], v["image"]
    req = urllib.request.Request(upload_url, data=img_path.read_bytes(), method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/octet-stream")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status not in (200, 201):
                print(f"::warning::image upload returned {r.status} — posting without image")
                return None
    except urllib.error.HTTPError as e:
        print(f"::warning::image upload failed ({e.code}): {e.read().decode()[:300]} — posting without image")
        return None
    print(f"image uploaded: {urn}")
    return urn


def main() -> int:
    t = today()
    dry = bool(os.environ.get("DRY_RUN"))
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()

    posts = []
    for p in sorted(POSTS.glob("*.md")):
        meta, body = parse(p.read_text(encoding="utf-8"))
        if not meta:
            continue
        posts.append((p, meta, body))

    approved = [x for x in posts if x[1].get("status", "").lower() == "approved"]
    due = [x for x in approved if date.fromisoformat(x[1]["date"]) <= t and not x[1].get("linkedin_url", "").strip()]
    due.sort(key=lambda x: x[1]["date"])

    remaining = [x for x in approved if date.fromisoformat(x[1]["date"]) > t]
    print(f"today={t}  approved={len(approved)}  due_now={len(due)}  scheduled_after_today={len(remaining)}")

    if not due:
        out("published", "false")
        if not approved and os.environ.get("SCHEDULED"):
            print("::error::The approved queue is empty. Nothing will post until a new note is approved.")
            return 1
        if len(remaining) <= 1:
            print(f"::warning::Only {len(remaining)} approved post(s) left in the queue. Time to write.")
        print("Nothing due today.")
        return 0

    path, meta, body = due[0]
    title = meta.get("title", path.stem)
    print(f"selected: {path.name}  ({title})")
    out("title", title.replace("\n", " "))

    if not token:
        print("::notice::LINKEDIN_ACCESS_TOKEN not set. Skipping LinkedIn. Site will still update on its daily deploy.")
        out("published", "false")
        return 0
    img = image_for(path)
    if dry:
        print(f"DRY_RUN: image={'none' if img is None else img.name}")
        print("DRY_RUN: would post the following commentary:\n" + "-" * 60 + f"\n{body}\n" + "-" * 60)
        out("published", "false")
        return 0

    version = os.environ.get("LINKEDIN_VERSION", "").strip() or default_version()

    status, _, raw = api("GET", "/v2/userinfo", token)
    if status != 200:
        print(f"::error::userinfo failed ({status}): {raw[:300]}")
        return 1
    person = json.loads(raw)["sub"]
    author = f"urn:li:person:{person}"

    payload = {
        "author": author,
        "commentary": little_text(body),
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if img is not None:
        urn = upload_image(token, version, author, img)
        if urn:
            payload["content"] = {"media": {"id": urn, "title": title, "altText": title}}
    status, headers, raw = api("POST", "/rest/posts", token, payload, version)
    if status != 201:
        print(f"::error::LinkedIn post failed ({status}, version {version}): {raw[:500]}")
        return 1
    share = headers.get("x-restli-id") or headers.get("X-RestLi-Id") or ""
    url = f"https://www.linkedin.com/feed/update/{share}/" if share else "https://www.linkedin.com/in/kalshams/recent-activity/all/"
    print(f"posted: {url}")

    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^status:.*$", "status: published", text, count=1, flags=re.M)
    if re.search(r"^linkedin_url:.*$", text, re.M):
        text = re.sub(r"^linkedin_url:.*$", f"linkedin_url: {url}", text, count=1, flags=re.M)
    else:
        text = text.replace("\n---\n", f"\nlinkedin_url: {url}\n---\n", 1)
    path.write_text(text, encoding="utf-8")
    out("published", "true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
