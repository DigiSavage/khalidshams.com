"""Verify recovered art loads, switches theme and remains beside working diagrams."""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
BASE = sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8767'
OUT = Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'docs/site/evidence/codex/art'
OUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'content/art.json').read_text())
scenes={a['scene'] for a in manifest['assets']}
results=[]
def check(name, ok, detail=''):
    results.append(dict(check=name,ok=bool(ok),detail=detail))
    print(('PASS ' if ok else 'FAIL ')+name,flush=True)
def loaded(page, scope, theme):
    pictures=page.locator(scope+' .studio-art')
    good=pictures.count()>0
    for picture in pictures.all():
        image=picture.locator('img:visible')
        image.scroll_into_view_if_needed()
        image.evaluate('(i)=>i.decode()')
        good &= image.count()==1 and theme in image.get_attribute('class') and image.evaluate('(i)=>i.naturalWidth>0 && i.complete && i.alt.length>20')
    return good
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    for theme in ('light','dark'):
        for w,h,scale in [(360,800,1),(390,844,1),(430,900,1),(768,1024,1),(1440,1000,1),(1920,1080,1),(720,450,2)]:
            ctx=browser.new_context(viewport=dict(width=w,height=h),device_scale_factor=scale,color_scheme=theme,reduced_motion='reduce')
            page=ctx.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            label=f'{w} {theme} scale{scale}'
            for route,name,scope in [('/','home','body'),('/method/','method','body'),('/learn/','learn','body'),('/learn/atlas/','atlas','body'),('/illustrated/','library','#architecture')]:
                page.goto(BASE+route,wait_until='networkidle')
                check(f'{name} {label} all placed originals decode in the selected theme',loaded(page,scope,theme))
                check(f'{name} {label} no horizontal overflow or script errors',page.evaluate('document.documentElement.scrollWidth<=innerWidth') and not errors,errors[:])
                if name=='library':
                    check(f'library {label} all eight studies',set(page.locator('#architecture [data-art-scene]').evaluate_all('(ns)=>ns.map(n=>n.dataset.artScene)'))==scenes)
                    if w in (390,1920):
                        for scene in sorted(scenes):
                            page.locator('#study-'+scene).screenshot(path=str(OUT/f'{scene}-{w}-{theme}.jpg'),type='jpeg',quality=82,style='.site-head,.pagenav{visibility:hidden!important}')
                if name=='atlas':
                    check(f'atlas {label} illustration and interactive scene coexist',page.locator('.atlas-art-intro .studio-art').count()==1 and page.locator('#atl-svgwrap svg').count()==1)
                    page.locator('#atl-follow').click()
                    check(f'atlas {label} original lesson still starts',page.locator('#atl-stepno').inner_text()!='Ready')
                    if w in (390,1920):
                        page.locator('.atlas-art-intro').screenshot(path=str(OUT/f'atlas-intro-{w}-{theme}.jpg'),type='jpeg',quality=82,style='.site-head{visibility:hidden!important}')
                        page.locator('#reading-thread').screenshot(path=str(OUT/f'atlas-thread-{w}-{theme}.jpg'),type='jpeg',quality=82,style='.site-head{visibility:hidden!important}')
                if name=='home' and w in (390,1920):
                    page.locator('#situations').screenshot(path=str(OUT/f'home-situations-{w}-{theme}.jpg'),type='jpeg',quality=82,style='.site-head{visibility:hidden!important}')
            # Existing site theme preference must override the operating system, without reload.
            other='dark' if theme=='light' else 'light'
            page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',other)
            check(f'library {label} explicit theme overrides OS',loaded(page,'#architecture',other))
            ctx.close()
    # Images and their text equivalents also render without JavaScript.
    ctx=browser.new_context(viewport=dict(width=390,height=844),java_script_enabled=False,color_scheme='light')
    page=ctx.new_page();page.goto(BASE+'/illustrated/',wait_until='networkidle')
    check('All eight text-free studies render without JavaScript',page.locator('#architecture .art-light:visible').count()==8)
    ctx.close();browser.close()
(OUT/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
failed=sum(not x['ok'] for x in results)
print(f'{len(results)-failed}/{len(results)} passed')
sys.exit(bool(failed))
