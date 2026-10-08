"""Check delivery guide downloads, independent team controls and page integration."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:8767'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('work/delivery-check')
OUT.mkdir(parents=True, exist_ok=True)
results = []


def check(name, ok):
    results.append({'check': name, 'ok': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for theme in ('light', 'dark'):
        for width in (390, 768, 1440):
            context = browser.new_context(viewport={'width': width, 'height': 900},
                                          color_scheme=theme, reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            label = f'{theme} {width}'
            page.goto(BASE + '/method/?agents=10#building-ai-systems', wait_until='networkidle')
            check(f'{label} five readable components', page.locator('.delivery-components > li').count() == 5)
            for n in (2, 3, 6, 10, 12):
                page.locator('#delivery-people').fill(str(n))
                links = n * (n - 1) // 2
                check(f'{label} {n} people, {links} connections',
                      page.locator('#delivery-team-svg circle').count() == n and
                      page.locator('#delivery-team-svg path').count() == links and
                      f'{links} possible pairwise' in page.locator('#delivery-count').inner_text())
            check(f'{label} human control leaves agent count alone', page.locator('#ag-mesh-n').inner_text() == '45')
            page.locator('#delivery-people').press('Home')
            page.locator('#delivery-people').press('ArrowRight')
            check(f'{label} keyboard updates human count', page.locator('#delivery-count').inner_text().startswith('3 people'))
            page.locator('.delivery-download summary').click()
            image = page.locator('.delivery-download img:visible')
            image.evaluate('(i)=>i.decode()')
            check(f'{label} poster follows theme', image.count() == 1 and image.get_attribute('src').endswith(theme + '.svg'))
            if width in (390, 1440):
                for selector, name in [('#building-ai-systems', 'overview'), ('#human-coordination', 'human')]:
                    page.locator(selector).screenshot(path=str(OUT / f'{name}-{width}-{theme}.jpg'), type='jpeg', quality=85,
                                                     style='.site-head,.pagenav{visibility:hidden!important}')
            with page.expect_download() as download:
                page.locator('.delivery-download a[download]').first.click()
            check(f'{label} download works', download.value.suggested_filename == 'building-ai-systems-light.svg')
            other = 'dark' if theme == 'light' else 'light'
            page.evaluate('(t)=>document.documentElement.dataset.theme=t', other)
            check(f'{label} explicit theme overrides OS', page.locator('.delivery-download img:visible').get_attribute('src').endswith(other + '.svg'))
            check(f'{label} method fits viewport', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.goto(BASE + '/learn/')
            page.locator('a[href="/method/#building-ai-systems"]').click()
            page.wait_for_url(BASE + '/method/#building-ai-systems')
            check(f'{label} Learn link reaches guide', page.locator('#building-ai-systems').is_visible())
            page.goto(BASE + '/illustrated/#field-guides')
            page.locator('.delivery-resource img:visible').evaluate('(i)=>i.decode()')
            check(f'{label} library preview and links', page.locator('.delivery-resource a[download]').count() == 2 and
                  page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            check(f'{label} no script errors', not errors)
            context.close()
        context = browser.new_context(viewport={'width': 1200, 'height': 1720})
        page = context.new_page()
        page.goto(BASE + f'/building-ai-systems-{theme}.svg')
        check(f'{theme} poster labels stay inside page', page.locator('text').evaluate_all(
            '(ns)=>ns.every(n=>{const b=n.getBBox();return b.x>=0&&b.y>=0&&b.x+b.width<=1200&&b.y+b.height<=1720})'))
        check(f'{theme} poster retains selectable text and source link',
              page.locator('text').filter(has_text='Quadratic growth').count() == 1 and
              page.locator('text').filter(has_text='khalidshams.com/method/').count() == 1)
        page.screenshot(path=str(OUT / f'poster-{theme}.png'))
        context.close()
    context = browser.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
    page = context.new_page()
    page.goto(BASE + '/method/#human-coordination')
    check('No-JS example remains meaningful', page.locator('#delivery-team-svg path').count() == 15 and
          '6 people' in page.locator('#delivery-count').inner_text() and page.locator('.delivery-components li').count() == 5)
    search = page.request.get(BASE + '/search.json').json()
    check('Guide and human-team section are searchable',
          any(x['u'] == '/method/#building-ai-systems' for x in search) and
          any(x['u'] == '/method/#human-coordination' for x in search))
    context.close()
    browser.close()

(OUT / 'checks.json').write_text(json.dumps(results, indent=2) + '\n')
failed = sum(not r['ok'] for r in results)
print(f'{len(results) - failed}/{len(results)} passed')
sys.exit(bool(failed))
