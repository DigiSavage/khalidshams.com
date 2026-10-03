"""Run a browser check with an on-disk cache of unmodified Google Fonts responses.

Usage: python tests/site/run_cached.py tests/atlas/ui_check.py <base> <shots>
Only font resources are cached. Site HTML, scripts, styles and assertions run normally.
This avoids loading the same external fonts in every fresh browser context.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path
from playwright.async_api import Browser as AsyncBrowser
from playwright.sync_api import Browser as SyncBrowser

CACHE = Path(__file__).resolve().parents[2] / 'work/font-cache'
CACHE.mkdir(parents=True, exist_ok=True)
PATTERN = 'https://fonts.*.com/**'


def paths(url):
    name = hashlib.sha256(url.encode()).hexdigest()
    return CACHE / (name+'.json'), CACHE / (name+'.body')


def read(url):
    meta, body = paths(url)
    if meta.exists() and body.exists():
        return json.loads(meta.read_text()), body.read_bytes()
    return None


def save(url, response, body):
    headers = {'content-type': response.headers.get('content-type', 'application/octet-stream'),
               'access-control-allow-origin': '*'}
    if response.status == 200:
        meta, file = paths(url)
        file.write_bytes(body)
        meta.write_text(json.dumps(dict(status=response.status, headers=headers)))
    return dict(status=response.status, headers=headers), body


async def async_font(route):
    cached = read(route.request.url)
    if cached is None:
        response = await route.fetch(timeout=90000)
        cached = save(route.request.url, response, await response.body())
    meta, body = cached
    await route.fulfill(**meta, body=body)


def sync_font(route):
    cached = read(route.request.url)
    if cached is None:
        response = route.fetch(timeout=90000)
        cached = save(route.request.url, response, response.body())
    meta, body = cached
    route.fulfill(**meta, body=body)


async_original = AsyncBrowser.new_context
sync_original = SyncBrowser.new_context


async def async_context(self, *args, **kwargs):
    context = await async_original(self, *args, **kwargs)
    await context.route(PATTERN, async_font)
    return context


def sync_context(self, *args, **kwargs):
    context = sync_original(self, *args, **kwargs)
    context.route(PATTERN, sync_font)
    return context


if __name__ == '__main__':
    AsyncBrowser.new_context = async_context
    SyncBrowser.new_context = sync_context
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    script = sys.argv[1]
    sys.argv = sys.argv[1:]
    runpy.run_path(script, run_name='__main__')
