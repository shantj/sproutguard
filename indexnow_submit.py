#!/usr/bin/env python3
"""IndexNow submitter for the SproutGuard site.

CRITICAL: the site is served from a SUBPATH (https://shantj.github.io/sproutguard/),
so the key file lives at /sproutguard/<key>.txt, NOT at the domain root.
IndexNow's default lookup is https://<host>/<key>.txt, which 404s here, so every
submission WITHOUT an explicit `keyLocation` is rejected with:

    403 {"errorCode":"UserForbiddedToAccessSite", ...}

Rounds 1-12 of the growth log recorded these submissions as successful because
they read the HTTP status of a *different* endpoint (Yandex, which returns 202
regardless) or trusted a 200 that was never actually verified. Nothing was ever
submitted. Always pass keyLocation.

Usage:  python3 indexnow_submit.py [url ...]
        (no args = every <loc> in the live sitemap)
"""
import json
import re
import sys
import urllib.error
import urllib.request

HOST = "shantj.github.io"
BASE = f"https://{HOST}/sproutguard"
KEY_PATH = "/tmp/indexnow_key.txt"
ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]
UA = {"User-Agent": "Mozilla/5.0 (compatible; IndexNowClient/1.0)"}


def read_key() -> str:
    with open(KEY_PATH) as fh:
        key = fh.read().strip()
    if not key:
        sys.exit("empty key file")
    return key


def key_location(key: str) -> str:
    return f"{BASE}/{key}.txt"


def verify_key_file(key: str) -> None:
    """Fail loudly if the key file is not actually reachable where we claim."""
    loc = key_location(key)
    try:
        resp = urllib.request.urlopen(urllib.request.Request(loc, headers=UA), timeout=20)
        body = resp.read().decode().strip()
    except Exception as exc:
        sys.exit(f"key file unreachable at {loc.replace(key, '<KEY>')}: {exc}")
    if resp.status != 200 or body != key:
        sys.exit(f"key file at {loc.replace(key, '<KEY>')} did not return the key (status {resp.status})")
    print(f"key file OK at {BASE}/<KEY>.txt")


def sitemap_urls() -> list:
    sm = urllib.request.urlopen(f"{BASE}/sitemap.xml", timeout=20).read().decode()
    return re.findall(r"<loc>(.*?)</loc>", sm)


def submit(endpoint: str, key: str, urls: list):
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": key_location(key),
        "urlList": urls,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8", **UA},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status, resp.read().decode()[:200]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:300]
    except Exception as exc:  # network-level failure
        return None, str(exc)[:200]


def main() -> int:
    key = read_key()
    verify_key_file(key)
    urls = sys.argv[1:] or sitemap_urls()
    if not urls:
        sys.exit("no URLs to submit")
    print(f"submitting {len(urls)} URLs")

    ok = 0
    for endpoint in ENDPOINTS:
        status, body = submit(endpoint, key, urls)
        accepted = status in (200, 202)
        ok += accepted
        print(f"  {'OK  ' if accepted else 'FAIL'} {endpoint} -> {status} {body!r}")
    print(f"{ok}/{len(ENDPOINTS)} endpoints accepted")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
