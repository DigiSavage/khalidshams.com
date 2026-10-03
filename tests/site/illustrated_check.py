"""Focused studio checks and reproducible visual evidence. Serve a fresh dist first.

python tests/site/illustrated_check.py http://localhost:8767 docs/site/evidence/codex
The temporary gallery uses the built site's CSS and the real SVG generators.
"""
import json
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from vignettes import SCENES, vignette

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8767'
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / 'docs/site/evidence/codex')
OUT.mkdir(parents=True, exist_ok=True)
results = []


def check(name, ok, detail=''):
    results.append(dict(check=name, ok=bool(ok), detail=detail))
    print(('PASS ' if ok else 'FAIL ') + name + (' '+str(detail) if detail else ''), flush=True)


def gallery():
    head = (ROOT/'dist/index.html').read_text().split('</head>')[0] + '</head>'
    body = '<main class="studio-review"><h1>Vignette drawing review</h1><p>All 19 library keys, including the shared Decide drawing. Same generated SVG and site styles.</p><div class="studio-grid">'
    for key in SCENES:
        body += '<figure><figcaption>'+key+'</figcaption>'+vignette(key)+'</figure>'
    body += '</div></main>'
    css = '<style>.studio-review{padding:24px}.studio-review h1{font-size:32px}.studio-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:24px}.studio-grid figure{margin:0;max-width:360px}.studio-grid figcaption{font:12px var(--mono);margin:10px 0}.studio-grid .vig{width:100%;height:auto}</style>'
    return head + css + '<body>' + body + '</body></html>'


def screenshot(page, selector, name):
    page.locator(selector).first.screenshot(path=str(OUT/(name+'.jpg')), type='jpeg', quality=82, animations='disabled', style='.site-head,.pagenav{visibility:hidden}')


def main():
    review = ROOT/'dist/__studio_review.html'
    review.write_text(gallery())
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width in (1920, 390):
                for theme in ('light', 'dark'):
                    ctx = browser.new_context(viewport=dict(width=width, height=1080 if width==1920 else 844), color_scheme=theme, reduced_motion='reduce')
                    page = ctx.new_page(); errors=[]
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    suffix=f'{width}-{theme}'
                    for route, parts in [
                        ('/learn/atlas/?step=10', [('atlas-stage','#atl-stage'),('chapters','.chapters'),('approval-trace','#pane-step')]),
                        ('/learn/atlas/how-models-are-made/?step=8', [('model-stage','#atl-stage')]),
                        ('/method/', [('agent-loop','#ag-svg'),('topologies','.ag-cmp'),('estate-map','.mapwrap')]),
                        ('/learn/', [('learn-map','.ln-stage'),('decision-tree','#decide .ln-fig'),('loop-strip','#loop .ln-fig'),('hub-spoke','#multi .ln-fig'),('prompt-hook','#enforce')]),
                        ('/', [('home-situations','#situations')]),
                        ('/architect/', [('architect-situations','.routes')]),
                        ('/__studio_review.html', [('vignettes','.studio-review')]),
                    ]:
                        page.goto(BASE+route); page.evaluate('document.fonts.ready');page.wait_for_timeout(100)
                        check(route+' '+suffix+' layout', page.evaluate('document.documentElement.scrollWidth<=innerWidth'), errors[:2])
                        for name, selector in parts:
                            if not page.locator(selector).count():
                                # Containers differ between pages; use the nearest semantic region.
                                if name=='topologies':selector='.ag-topo-grid'
                                elif name=='architect-situations':selector='#situations'
                            check(name+' '+suffix+' exists',page.locator(selector).count()>0)
                            if page.locator(selector).count():screenshot(page,selector,name+'-'+suffix)
                        if route=='/learn/':
                            drawing=page.locator('#ln-svg').evaluate('(svg)=>svg.outerHTML')
                            isolated=ctx.new_page()
                            isolated.set_content('<html><head>'+page.locator('head').inner_html()+'</head><body style="padding:16px"><div id="studio-overview" style="width:100%">'+drawing+'</div><style>#studio-overview svg{width:100%;height:auto}</style></body></html>')
                            isolated.evaluate('document.fonts.ready')
                            screenshot(isolated,'#studio-overview','learn-map-overview-'+suffix)
                            isolated.close()
                        if route=='/__studio_review.html':
                            clipped=page.locator('.vig').evaluate_all('''svgs=>svgs.flatMap((svg,i)=>[...svg.querySelectorAll('text')].filter(t=>{let b=t.getBBox();return b.x<0||b.y<0||b.x+b.width>320.5||b.y+b.height>180.5}).map(t=>({vignette:i,text:t.textContent})))''')
                            check('vignette label bounds '+suffix,not clipped,clipped)
                    check('no JavaScript errors '+suffix,not errors,errors)
                    ctx.close()
            # Behaviour checks use keyboard where a reader can inspect a new dependency.
            ctx=browser.new_context(viewport=dict(width=1440,height=900),reduced_motion='reduce')
            page=ctx.new_page();page.goto(BASE+'/method/')
            page.locator('.m-node[data-id="data"]').focus();page.keyboard.press('Enter')
            dep=page.locator('#panel [data-dependency]').first
            dep.focus();page.keyboard.press('Enter')
            check('keyboard dependency exposes potential blast radius', 'Potential blast radius' in page.locator('#m-dependency').text_content())
            check('one selected dependency is visible',page.locator('.m-line.selected').count()==1)
            page.locator('#ind button').nth(1).click()
            check('industry weighting retains risk outlines',page.locator('.m-risk.hi,.m-risk.mid').count()>0)
            page.locator('#ag-n').fill('12');page.locator('#ag-n').dispatch_event('input')
            check('topology arithmetic at twelve agents',page.locator('#ag-mesh-n').inner_text()=='66' and page.locator('#ag-hub-n').inner_text()=='11')
            for part in ('mcp','rag','memory','llm','skills'):
                page.locator('#ag-svg .ag-pill[data-part="'+part+'"]').click()
                check('component selection '+part,page.locator('.ag-pane[data-pane="'+part+'"]').is_visible())
            page.goto(BASE+'/learn/');page.locator('#ln-mark').click()
            check('understanding has a non-colour mark',page.locator('.ln-node.lit .ln-understood').is_visible())
            check('understanding retains ks-learn', 'ai' in page.evaluate('JSON.parse(localStorage.getItem("ks-learn"))'))
            page.locator('#ln-circuit').select_option(index=1)
            first=page.locator('#ln-title').inner_text();page.locator('#ln-next').click()
            check('circuit stepping retained',first!=page.locator('#ln-title').inner_text())
            page.get_by_role('button',name='Society',exact=True).click()
            check('seventh cluster is inspectable',page.locator('#ln-clusters button[aria-pressed="true"]').text_content()=='Society')
            page.goto(BASE+'/');page.keyboard.press('Control+k');page.get_by_role('searchbox',name='Search',exact=True).fill('agent');page.wait_for_timeout(250);page.keyboard.press('Enter');page.wait_for_timeout(500)
            check('search arrival has highlights',page.locator('mark.ks-hl').count()>0)
            ctx.close()
            # Both lessons and the changed overview pages at every requested width and 200% equivalent.
            for w,h,scale in [(360,740,1),(390,844,1),(430,932,1),(768,1024,1),(1440,900,1),(1920,1080,1),(720,450,2)]:
                for theme in ('light','dark'):
                    ctx=browser.new_context(viewport=dict(width=w,height=h),device_scale_factor=scale,color_scheme=theme,reduced_motion='reduce')
                    page=ctx.new_page();errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
                    for route in ('/learn/atlas/?step=10','/learn/atlas/how-models-are-made/?step=8','/method/','/learn/'):
                        page.goto(BASE+route)
                        check(f'{route} {w} {theme} scale{scale}',page.evaluate('document.documentElement.scrollWidth<=innerWidth') and not errs,errs)
                        if 'step=10' in route:
                            check(f'chapter rail compact {w} {theme}',page.locator('.chapters').bounding_box()['height']<100)
                    ctx.close()
            browser.close()
    finally:
        review.unlink(missing_ok=True)
        (OUT/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
    failed=[x for x in results if not x['ok']]
    print(f'{len(results)-len(failed)} passed, {len(failed)} failed',flush=True)
    return bool(failed)


if __name__=='__main__':
    sys.exit(main())
