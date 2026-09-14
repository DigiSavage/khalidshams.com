#!/usr/bin/env python3
"""
One-time (well, every ~60 days) LinkedIn token helper. Run locally.

  1. python scripts/linkedin_auth.py url      -> prints the URL to open
  2. approve in the browser; copy the `code` from the redirect URL
  3. python scripts/linkedin_auth.py token <code>  -> prints the access token

Set LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, and LINKEDIN_REDIRECT_URI
(the redirect must exactly match one registered on the app's Auth tab —
https://khalidshams.com/ works fine; nothing needs to handle it).

Put the printed token in the repo secret LINKEDIN_ACCESS_TOKEN.
LinkedIn member tokens last 60 days; the publish job will start failing with
401 when it expires — that failure email is the reminder to repeat this.
"""
import os, sys, json, urllib.parse, urllib.request

SCOPES = "openid profile w_member_social"


def need(k: str) -> str:
    v = os.environ.get(k)
    if not v:
        sys.exit(f"set {k}")
    return v


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "url"
    cid, redirect = need("LINKEDIN_CLIENT_ID"), need("LINKEDIN_REDIRECT_URI")
    if cmd == "url":
        q = urllib.parse.urlencode({"response_type": "code", "client_id": cid,
                                    "redirect_uri": redirect, "scope": SCOPES, "state": "khalidshams"})
        print("https://www.linkedin.com/oauth/v2/authorization?" + q)
        return
    if cmd == "token":
        code = sys.argv[2] if len(sys.argv) > 2 else sys.exit("usage: token <code>")
        data = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code,
                                       "client_id": cid, "client_secret": need("LINKEDIN_CLIENT_SECRET"),
                                       "redirect_uri": redirect}).encode()
        req = urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken", data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.loads(r.read())
        print("access_token:", j["access_token"])
        print("expires_in_days:", round(j.get("expires_in", 0) / 86400, 1))
        return
    sys.exit("usage: linkedin_auth.py url | token <code>")


if __name__ == "__main__":
    main()
