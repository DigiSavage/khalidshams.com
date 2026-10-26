#!/usr/bin/env python3
"""
Publish one approved note, following content/linkedin_schedule.json.

Scheduled runs retain the ordinary Tue/Thu oldest-overdue queue. During a
bounded campaign, extra weekdays select only that day's explicitly marked note.
Manual runs may publish an ordinary overdue note on other days; campaign notes
never catch up outside their own dates. Receipts prevent a second tracked post
on the same Phoenix date. The workflow commits each confirmed publication.

Env:
  LINKEDIN_ACCESS_TOKEN   required to post (openid profile w_member_social)
  LINKEDIN_VERSION        optional, YYYYMM; defaults to last month
  DRY_RUN=1               select + print, no network or file/output changes
  SCHEDULED=1             apply configured weekdays; fail an exhausted base queue
  BUILD_DATE=YYYY-MM-DD   override "today" only with DRY_RUN=1
  RESERVE_ONLY=1          create an exclusive local publication hold, no API calls
  PUBLICATION_ATTEMPT    unique run/attempt ID, shared by reserve and live steps
  REQUIRE_RESERVATION=1  mandatory for live publication, after the hold is pushed

Outputs: published, reserved, reservation_released, status, selected_path, title,
receipt_url. Dry runs print the result but do not write GITHUB_OUTPUT.

The workflow commits content/linkedin_pending.json before any publication API
call. An unresolved hold blocks all subsequent runs. Confirmed publication writes
its receipt and removes the hold; definite pre-publish/client rejection also
releases it. The workflow commits that resolution. API ambiguity, process failure
or a failed resolution commit leaves the remote hold for manual reconciliation.
"""
from __future__ import annotations
import http.client
import json, os, re, sys, tempfile, urllib.request, urllib.error
from datetime import date, datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "content" / "posts"
SCHEDULE = ROOT / "content" / "linkedin_schedule.json"
PENDING = ROOT / "content" / "linkedin_pending.json"
TZ = timezone(timedelta(hours=-7))
API = "https://api.linkedin.com"


def out(k: str, v: str) -> None:
    if os.environ.get("DRY_RUN") == "1":
        return
    v = str(v).replace("\r", " ").replace("\n", " ")
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


@dataclass
class Selection:
    status: str
    post: tuple | None = None
    receipt_url: str = ""
    message: str = ""


def valid_receipt(url: str) -> bool:
    return bool(re.fullmatch(r"https://www\.linkedin\.com/feed/update/urn:li:(?:share|ugcPost):[0-9]+/", url))


def load_schedule(path: Path = None) -> dict:
    config = json.loads((path or SCHEDULE).read_text(encoding="utf-8"))

    def weekdays(values):
        if not isinstance(values, list) or not values or any(type(x) is not int or x not in range(7) for x in values):
            raise ValueError("Schedule weekdays must be nonempty lists of integers 0 through 6.")

    weekdays(config["base_weekdays"])
    names = set()
    for campaign in config.get("campaigns", []):
        name = campaign["name"]
        if not name or name in names:
            raise ValueError("Campaign names must be nonempty and unique.")
        names.add(name)
        start, end = date.fromisoformat(campaign["start"]), date.fromisoformat(campaign["end"])
        if start > end:
            raise ValueError(f"Campaign {name} ends before it starts.")
        weekdays(campaign["weekdays"])
        if set(campaign["weekdays"]) & set(config["base_weekdays"]):
            raise ValueError(f"Campaign {name} overlaps ordinary publishing weekdays.")
        for manual in campaign.get("manual_dates", []):
            d = date.fromisoformat(manual)
            receipt = campaign.get("manual_receipts", {}).get(manual, "")
            if not (start <= d <= end and d.weekday() in campaign["weekdays"] and valid_receipt(receipt)):
                raise ValueError(f"Campaign {name} has an invalid manual date or missing receipt: {manual}.")
    return config


def publication_day(meta: dict) -> date:
    # Legacy receipts lack an actual timestamp. New backlog posts record the
    # real publication date rather than relying on their original due date.
    raw = meta.get("linkedin_published_at") or meta["date"]
    if len(raw) == 10:
        return date.fromisoformat(raw)
    stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("linkedin_published_at must include a timezone.")
    return stamp.astimezone(TZ).date()


def select_post(posts: list, config: dict, t: date, scheduled: bool) -> Selection:
    campaigns = config.get("campaigns", [])
    for campaign in campaigns:
        if t.isoformat() in campaign.get("manual_dates", []):
            return Selection("already_published", receipt_url=campaign["manual_receipts"][t.isoformat()],
                             message="This date already has a manually verified publication.")
    for post in posts:
        meta = post[1]
        if (meta.get("linkedin_url", "").strip() or meta.get("status", "").lower() == "published") and publication_day(meta) == t:
            receipt = meta.get("linkedin_url", "").strip()
            if not valid_receipt(receipt):
                raise ValueError(f"{post[0].name} records a publication today without a verifiable receipt. Reconcile it before posting.")
            return Selection("already_published", post, receipt, "A publication is already recorded for today.")

    active = [c for c in campaigns if date.fromisoformat(c["start"]) <= t <= date.fromisoformat(c["end"])
              and t.weekday() in c["weekdays"]]
    if len(active) > 1:
        raise ValueError("Multiple campaigns claim today's publishing slot.")
    if active:
        campaign = active[0]
        matches = [p for p in posts if p[1].get("linkedin_schedule") == campaign["name"] and p[1].get("date") == str(t)]
        if len(matches) != 1:
            raise ValueError(f"Campaign {campaign['name']} requires exactly one marked post for {t}; found {len(matches)}. Ordinary backlog will not be substituted.")
        post = matches[0]
        meta = post[1]
        if meta.get("series") != campaign["name"] or meta.get("status", "").lower() != "approved" or meta.get("linkedin_url", "").strip():
            raise ValueError(f"Campaign post {post[0].name} must have matching series, approved status and no existing receipt.")
        return Selection("due", post)

    if scheduled and t.weekday() not in config["base_weekdays"]:
        return Selection("outside_schedule", message="No publishing slot today. The campaign is bounded; ordinary backlog stays on base weekdays.")
    campaign_names = {c["name"] for c in campaigns}
    ordinary = [p for p in posts if not p[1].get("linkedin_schedule") and p[1].get("series") not in campaign_names]
    approved = [p for p in ordinary if p[1].get("status", "").lower() == "approved" and not p[1].get("linkedin_url", "").strip()]
    due = sorted((p for p in approved if date.fromisoformat(p[1]["date"]) <= t), key=lambda p: (p[1]["date"], p[0].name))
    if due:
        return Selection("due", due[0])
    if not approved and scheduled:
        raise ValueError("The ordinary approved queue is empty. Add an approved note before the next base publishing slot.")
    return Selection("nothing_due", message="No ordinary approved note is due today.")


def report(selection: Selection, status: str = None, receipt: str = "", published: bool = False,
           reserved: bool = False, reservation_released: bool = False) -> None:
    selected = selection.post
    result = {
        "published": "true" if published else "false",
        "reserved": "true" if reserved else "false",
        "reservation_released": "true" if reservation_released else "false",
        "status": status or selection.status,
        "selected_path": str(selected[0].relative_to(ROOT)) if selected and selected[0].is_relative_to(ROOT) else (str(selected[0]) if selected else ""),
        "title": selected[1].get("title", selected[0].stem) if selected else "",
        "receipt_url": receipt or selection.receipt_url,
    }
    print("result=" + json.dumps(result))
    for key, value in result.items():
        out(key, value)


def record_publication(path: Path, receipt: str, t: date) -> None:
    text = path.read_text(encoding="utf-8")
    # Restrict edits to frontmatter, never a line in the post body.
    match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)$", text, re.S)
    if not match:
        raise ValueError("Post frontmatter disappeared before recording publication.")
    front = match[2]
    stamp = datetime.now(TZ)
    stamp = stamp.replace(year=t.year, month=t.month, day=t.day)
    for key, value in (("status", "published"), ("linkedin_url", receipt), ("linkedin_published_at", stamp.isoformat(timespec="seconds"))):
        if re.search(rf"^{key}:.*$", front, re.M):
            front = re.sub(rf"^{key}:.*$", lambda _: f"{key}: {value}", front, count=1, flags=re.M)
        else:
            front += f"\n{key}: {value}"
    # Write beside the source and replace atomically so a partial disk write
    # cannot truncate an existing approved post.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(match[1] + front + match[3] + match[4])
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def public_text(body: str) -> str:
    """Website Markdown autolinks become ordinary URLs in LinkedIn commentary."""
    return re.sub(r"<(https?://[^<>\s]+)>", r"\1", body)


def selected_path(post: tuple) -> str:
    return str(post[0].relative_to(ROOT))


def read_reservation() -> dict | None:
    if not PENDING.exists():
        return None
    hold = json.loads(PENDING.read_text(encoding="utf-8"))
    if not isinstance(hold, dict) or not all(isinstance(hold.get(key), str) and hold[key] for key in ("path", "date", "attempt")):
        raise ValueError("Publication hold is malformed; reconcile it before publishing.")
    date.fromisoformat(hold["date"])
    target = Path(hold["path"])
    if target.is_absolute() or ".." in target.parts or not (ROOT / target).is_relative_to(POSTS):
        raise ValueError("Publication hold references an invalid post path.")
    return hold


def reserve(selection: Selection, t: date, attempt: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", attempt):
        raise ValueError("PUBLICATION_ATTEMPT must be a nonempty run-specific identifier.")
    hold = {"path": selected_path(selection.post), "date": str(t), "attempt": attempt}
    # Exclusive creation also prevents two local processes from reserving the
    # same queue. Git commit/push is the workflow's durable reservation boundary.
    with PENDING.open("x", encoding="utf-8") as handle:
        json.dump(hold, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def release_reservation() -> bool:
    try:
        PENDING.unlink()
        return True
    except OSError as error:
        print(f"::error::Could not release the publication hold: {error}. Reconcile it before another run.")
        return False


def main() -> int:
    dry = os.environ.get("DRY_RUN") == "1"
    reserve_only = os.environ.get("RESERVE_ONLY") == "1"
    require_reservation = os.environ.get("REQUIRE_RESERVATION") == "1"
    attempt = os.environ.get("PUBLICATION_ATTEMPT", "")
    selection = Selection("error")
    if os.environ.get("BUILD_DATE") and not dry:
        print("::error::BUILD_DATE is allowed only with DRY_RUN=1. Live publishing always uses today's Phoenix date.")
        report(selection, "invalid_date_override")
        return 1
    try:
        t = today()
        hold = read_reservation()
    except (ValueError, OSError) as error:
        print(f"::error::Publication hold could not be checked: {error}")
        report(selection, "reservation_error")
        return 1
    if hold and (dry or reserve_only or not require_reservation or hold["attempt"] != attempt or hold["date"] != str(t)):
        print("::error::An unresolved publication hold blocks new publishing: " + json.dumps(hold))
        print("Inspect LinkedIn and the prior run, then reconcile its receipt or confirm no publication before clearing this hold. Do not blindly retry.")
        report(selection, "reservation_held")
        return 1
    try:
        posts = []
        for path in sorted(POSTS.glob("*.md")):
            meta, body = parse(path.read_text(encoding="utf-8"))
            if meta:
                posts.append((path, meta, body))
        selection = select_post(posts, load_schedule(), t, os.environ.get("SCHEDULED") == "1")
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"::error::Publication selection failed: {error}")
        report(selection, "selection_error")
        return 1

    print(f"today={t} selection={selection.status}")
    if selection.status != "due":
        if hold:
            print("::error::A publication hold exists but its post is no longer due. Reconcile the hold and receipt before continuing.")
            report(selection, "reservation_held")
            return 1
        print(selection.message)
        report(selection)
        return 0
    path, meta, body = selection.post
    title = meta.get("title", path.stem)
    body = public_text(body)
    print(f"selected: {path.name} ({title})")
    img = image_for(path)
    if dry:
        print(f"DRY_RUN: image={'none' if img is None else img.name}")
        print("DRY_RUN: would post the following commentary:\n" + "-" * 60 + f"\n{body}\n" + "-" * 60)
        report(selection, "dry_run")
        return 0
    if reserve_only:
        try:
            reserve(selection, t, attempt)
        except (ValueError, OSError) as error:
            print(f"::error::Could not reserve publication: {error}")
            report(selection, "reservation_error")
            return 1
        print("Publication reserved locally. Commit and push this hold before invoking the live publisher.")
        report(selection, "reserved", reserved=True)
        return 0
    if not require_reservation or not hold or hold["path"] != selected_path(selection.post):
        print("::error::Live publication requires a committed reservation for this exact post, date and attempt. Run the reservation workflow first.")
        report(selection, "reservation_required")
        return 1
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not token:
        print("::error::A post is due but LINKEDIN_ACCESS_TOKEN is missing. Nothing was published.")
        released = release_reservation()
        report(selection, "missing_token", reservation_released=released)
        return 1
    version = os.environ.get("LINKEDIN_VERSION", "").strip() or default_version()
    try:
        status, _, raw = api("GET", "/v2/userinfo", token)
        if status != 200:
            raise ValueError(f"userinfo failed ({status}): {raw[:300]}")
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
    except (ValueError, KeyError, OSError, http.client.HTTPException) as error:
        print(f"::error::Preparation failed before publishing: {error}")
        released = release_reservation()
        report(selection, "preparation_error", reservation_released=released)
        return 1

    # The previously committed hold survives API uncertainty or process failure.
    # It blocks later dates and later workflow attempts until reconciled.
    try:
        status, headers, raw = api("POST", "/rest/posts", token, payload, version)
    except (OSError, http.client.HTTPException) as error:
        print(f"::error::Ambiguous publish outcome: {type(error).__name__}. The hold remains. Inspect LinkedIn and reconcile the receipt before retrying.")
        report(selection, "ambiguous")
        return 1
    if status != 201:
        # Explicit client rejection is safe to resolve. Any other unexpected
        # status remains held, including 5xx responses after a possible write.
        rejected = 400 <= status < 500
        print(f"::error::LinkedIn publish returned {status} (version {version}): {raw[:500]}")
        released = release_reservation() if rejected else False
        if not rejected:
            print("::error::The outcome may be ambiguous. The hold remains. Inspect LinkedIn and reconcile the receipt before retrying.")
        report(selection, "publish_failed" if rejected else "ambiguous", reservation_released=released)
        return 1
    share = next((str(v).strip() for k, v in headers.items() if k.lower() == "x-restli-id"), "")
    url = f"https://www.linkedin.com/feed/update/{share}/"
    if not valid_receipt(url):
        print("::error::LinkedIn accepted the request but returned no valid share ID. The post may be live. Do not blindly retry. The hold remains until its receipt is reconciled.")
        report(selection, "ambiguous")
        return 1
    print(f"posted: {url}")
    try:
        record_publication(path, url, t)
    except (ValueError, OSError) as error:
        print(f"::error::Post is live at {url}, but the local receipt could not be saved: {error}. The hold remains. Reconcile this receipt before continuing.")
        report(selection, "receipt_write_failed", receipt=url)
        return 1
    released = release_reservation()
    if not released:
        report(selection, "reservation_release_failed", receipt=url)
        return 1
    report(selection, "published", receipt=url, published=True, reservation_released=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
