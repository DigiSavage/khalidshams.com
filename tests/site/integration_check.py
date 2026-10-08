"""Verify drawings are discoverable in built pages, not only in an isolated gallery.

Run after build.py while serving dist on 8767. Optional arguments: base URL, evidence directory.
"""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from vignettes import SCENES
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8767'
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT/'docs/site/evidence/codex/integration')
OUT.mkdir(parents=True, exist_ok=True)
results = []


def check(name, ok, detail=''):
    results.append(dict(check=name, ok=bool(ok), detail=detail))
    print(('PASS ' if ok else 'FAIL ') + name + (' '+str(detail) if detail else ''), flush=True)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = set(); self.hrefs = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        if tag == 'a': self.hrefs.append(attrs.get('href', ''))


library = Links()
library.feed((ROOT/'dist/illustrated/index.html').read_text())
broken = []
for href in set(library.hrefs):
    if not href.startswith(('/', '#')): continue
    url = urlsplit(href)
    file = ROOT/'dist'/(url.path or '/illustrated/').lstrip('/')
    if not file.suffix: file /= 'index.html'
    if not file.exists(): broken.append(href); continue
    if url.fragment:
        target = Links(); target.feed(file.read_text())
        if url.fragment not in target.ids: broken.append(href)
check('Every library destination and anchor resolves in the build', not broken, broken)
check('Library is in the sitemap', '/illustrated/</loc>' in (ROOT/'dist/sitemap.xml').read_text())
search = json.loads((ROOT/'dist/search.json').read_text())
check('Drawing titles appear in search', 'Own the recommendation' in json.dumps(search))

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for theme in ('light', 'dark'):
        for width, height, scale in [(360,800,1),(390,844,1),(430,900,1),(768,1024,1),(1440,1000,1),(1920,1080,1),(720,450,2)]:
            context = browser.new_context(viewport=dict(width=width,height=height),device_scale_factor=scale,color_scheme=theme,reduced_motion='reduce')
            page = context.new_page()
            errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
            for route, name in [('/','home'),('/method/','method'),('/learn/','learn'),('/illustrated/','library')]:
                page.goto(BASE+route, wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                label = f'{name} {width} {theme} scale{scale}'
                check(label+' no horizontal overflow', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                if name == 'library':
                    keys = set(page.locator('[data-drawing]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.drawing)'))
                    all_readable = keys == set(SCENES)-{'Decide'}
                    for key in keys:
                        card = page.locator(f'[data-drawing="{key}"]')
                        disclosure = card.locator('.concept-details')
                        if disclosure.count():
                            all_readable &= card.locator('.studio-art img:visible').is_visible()
                            disclosure.locator('summary').focus()
                            page.keyboard.press('Enter')
                        all_readable &= card.locator('svg').is_visible()
                        if disclosure.count(): disclosure.locator('summary').click()
                    check(label+' every concept picture and its live diagram are accessible', all_readable)
                    for scene in page.locator('#studios img:visible').all():
                        scene.scroll_into_view_if_needed()
                        scene.evaluate('(image)=>image.decode()')
                    check(label+' both studio images render in the correct theme', page.locator('#studios img:visible').count()==2 and page.locator(f'#studios img.ap-{theme}:visible, #studios img.art-{theme}:visible').count()==2)
                    if width in (390,1920):
                        for section in ('drawing-vocabulary','studios','systems','foundations','routes'):
                            page.locator('#'+section).screenshot(style=".site-head,.pagenav{visibility:hidden!important}", path=str(OUT/f'library-{section}-{width}-{theme}.jpg'),type='jpeg',quality=82)
                else:
                    check(label+' introduction drawing is visible', page.locator('.hero-drawing .studio-art img:visible').is_visible())
                    if width in (390,1920):
                        page.locator('.visual-hero').screenshot(style=".site-head,.pagenav{visibility:hidden!important}", path=str(OUT/f'{name}-intro-{width}-{theme}.jpg'),type='jpeg',quality=82)
                    if name == 'method':
                        check(label+' illustrations accompany all four references', page.locator('.section-picture .studio-art img:visible').count()==4)
                        if width in (390,1920):
                            for section in ('map','ladder','gates','record'):
                                page.locator('#'+section+' .illustrated-head').screenshot(style=".site-head,.pagenav{visibility:hidden!important}", path=str(OUT/f'method-{section}-{width}-{theme}.jpg'),type='jpeg',quality=82)
                check(label+' no script errors', not errors, errors)
            # Follow a real keyboard-accessible image link from the collection to the working lesson.
            page.locator('#drawing-estate .drawing-image').focus()
            page.keyboard.press('Enter')
            page.wait_for_url('**/method/#map')
            check(f'Library keyboard navigation {width} {theme}', page.locator('#map .section-picture .studio-art img:visible').is_visible())
            context.close()
    browser.close()
(OUT/'checks.json').write_text(json.dumps(results,indent=2))
failed = sum(not result['ok'] for result in results)
print(f'{len(results)-failed}/{len(results)} passed')
sys.exit(bool(failed))
