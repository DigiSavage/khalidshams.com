"""Concept art remains in the existing learning flow, with every live diagram available."""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from art_assets import CONCEPT_STUDIES
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8767'
OUT=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'docs/site/evidence/codex/concepts'
OUT.mkdir(parents=True,exist_ok=True)
G=json.loads((ROOT/'content/learn/graph.json').read_text())['ideas']
results=[]
def check(name,ok):
    results.append(dict(check=name,ok=bool(ok)));print(('PASS ' if ok else 'FAIL ')+name,flush=True)
# Every one of the 44 pages still has its original progress action and diagram.
for idea in G:
    html=(ROOT/'dist/learn/ideas'/idea['id']/'index.html').read_text()
    check(idea['id']+' retains its diagram and progress control', 'class="vig hero-art"' in html and 'id="idea-got"' in html)
    check(idea['id']+' uses the registered concept illustration when ready', ('data-concept-visual=' in html)==(idea['cluster'] in CONCEPT_STUDIES))
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    for theme in ('light','dark'):
        for width in (390,1920):
            ctx=browser.new_context(viewport=dict(width=width,height=844 if width==390 else 1080),color_scheme=theme,reduced_motion='reduce')
            page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            for route,name,selector in [('/','home-doors','.doors'),('/learn/','learn-doors','.doors'),('/architect/','architect','#situations'),('/learn/ideas/agent/','agent-idea','.hero'),('/learn/paths/what-makes-an-agent/','agent-path','.hero'),('/illustrated/#studios','studios','#studios')]:
                page.goto(BASE+route,wait_until='networkidle');page.evaluate('document.fonts.ready')
                for image in page.locator(selector+' .studio-art img:visible').all():
                    image.scroll_into_view_if_needed();image.evaluate('(i)=>i.decode()')
                for summary in page.locator(selector+' .concept-details summary').all():
                    summary.focus();page.keyboard.press('Enter')
                    check(f'{name} {width} {theme} diagram opens by keyboard',summary.locator('..').locator('svg').is_visible())
                    page.keyboard.press('Enter')
                check(f'{name} {width} {theme} layout and scripts', page.evaluate('document.documentElement.scrollWidth<=innerWidth') and not errors)
                page.locator(selector).screenshot(path=str(OUT/f'{name}-{width}-{theme}.jpg'),type='jpeg',quality=82,style='.site-head,.pagenav{visibility:hidden!important}')
                if name=='home-doors':
                    targets=page.locator('.door .door-cta a').evaluate_all('(links)=>links.map(a=>a.getAttribute("href"))')
                    check(f'Home door destinations {width} {theme}',targets==['/learn/paths/what-is-ai/','/architect/','/learn/#map'])
            ctx.close()
    browser.close()
(OUT/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
failed=sum(not x['ok'] for x in results)
print(f'{len(results)-failed}/{len(results)} passed')
sys.exit(bool(failed))
