"""Check real studio interactions, responsive themes and downloadable design records."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:8773'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('/tmp/enterprise-ui')
OUT.mkdir(parents=True, exist_ok=True)
results = []


def check(name, condition):
    results.append({'check': name, 'ok': bool(condition)})
    print(('PASS ' if condition else 'FAIL ') + name, flush=True)


def end_run(page):
    for _ in range(20):
        if page.locator('#es-next').is_disabled():
            return
        page.locator('#es-next').click()
    raise AssertionError('Unbounded simulation')


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for theme in ('light', 'dark'):
        for width in (360, 390, 768, 1024, 1440, 1920):
            context = browser.new_context(viewport={'width': width, 'height': 1000}, color_scheme=theme, reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(BASE + '/architect/agent-studio/', wait_until='networkidle')
            label = f'{theme} {width}'
            check(label+' page fits', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            check(label+' source and art present', page.locator('.es-intro-art .studio-art img:visible').count() == 1 and page.locator('.es-sources li').count() == 7)
            check(label+' illustrations load', page.locator('.es-intro-art img:visible').evaluate('(i)=>i.complete && i.naturalWidth>0'))
            page.locator('#es-map-detail').click()
            check(label+' step detail zooms the diagram', page.locator('.es-scene').get_attribute('viewBox') != '0 0 1000 620')
            page.locator('#es-map-overview').click()
            check(label+' whole diagram remains available', page.locator('.es-scene').get_attribute('viewBox') == '0 0 1000 620')
            if width < 600:
                page.locator('#es-map-detail').click()
            if width in (390, 1440):
                page.locator('.es-intro').screenshot(path=str(OUT/f'hero-{width}-{theme}.png'))
                page.locator('.es-designer').screenshot(path=str(OUT/f'design-{width}-{theme}.png'))
            end_run(page)
            check(label+' waits for review', page.locator('#es-review-controls').is_visible() and 'WAITING' in page.locator('#es-state').inner_text())
            check(label+' no premature receipt', 'write.receipt_received' not in page.locator('#es-trace').inner_text())
            page.locator('#es-approve').click()
            end_run(page)
            check(label+' approval reaches verified outcome', page.locator('#es-step-event').inner_text() == 'outcome.verified')
            page.locator('#es-condition').select_option('revoked')
            end_run(page)
            page.locator('#es-approve').click()
            end_run(page)
            check(label+' revocation blocks write', page.locator('#es-step-event').inner_text() == 'authorization.revoked' and 'write.receipt_received' not in page.locator('#es-trace').inner_text())
            if width in (390, 1440):
                page.locator('.es-workspace').screenshot(path=str(OUT/f'boundary-{width}-{theme}.png'))
            page.locator('#es-example').select_option('assistant')
            page.locator('#es-authority').select_option('read')
            page.locator('#es-condition').select_option('normal')
            end_run(page)
            check(label+' assistant stays read only', 'No ticket' in page.locator('#es-step-body').inner_text() and not page.locator('#es-review-controls').is_visible())
            page.locator('#es-authority').select_option('bounded')
            page.locator('#es-risk').select_option('consequential')
            check(label+' consequence narrows authority', 'explicit review' in page.locator('#es-authority-result').inner_text())
            page.locator('#es-pattern').select_option('specialists')
            page.locator('#es-budget').fill('1')
            page.locator('#es-budget').press('Tab')
            end_run(page)
            check(label+' specialist budget stops', page.locator('#es-step-event').inner_text() == 'budget.stopped')
            page.locator('#es-platform').select_option('claude-external')
            check(label+' external inference boundary visible', 'outside Azure' in page.locator('#es-platform-note').inner_text())
            page.locator('#es-improvement').select_option('access')
            check(label+' access failure routes to enforcement', 'fix identity' in page.locator('#es-improve-result').inner_text())
            page.locator('#es-owner').fill('<script>review owner</script>')
            with page.expect_download() as pending:
                page.locator('#es-download').click()
            download = pending.value
            text = Path(download.path()).read_text()
            check(label+' record downloaded safely', download.suggested_filename=='shams-assistant-design-record.txt' and 'UNRESOLVED BEFORE PRODUCTION' in text and '<script>review owner</script>' in text)
            check(label+' controls remain keyboard operable', page.locator('#es-reset').evaluate('(e)=>{e.focus();return document.activeElement===e}'))
            page.locator('#es-reset').press('Enter')
            check(label+' keyboard reset', page.locator('#es-step-event').inner_text() == 'identity.verified')
            check(label+' page still fits', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            check(label+' no script errors', not errors)
            context.close()
    context = browser.new_context(java_script_enabled=False, viewport={'width':390,'height':844})
    page = context.new_page()
    page.goto(BASE + '/architect/agent-studio/')
    page.locator('summary', has_text='Read both complete example designs').click()
    check('no JS: both worked examples readable', page.locator('#example-documents').is_visible() and page.locator('#example-assistant').is_visible())
    check('no JS: layout fits', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    context.close()
    context = browser.new_context(viewport={'width':720,'height':450}, device_scale_factor=2)
    page = context.new_page(); page.goto(BASE + '/architect/agent-studio/')
    check('200 percent zoom equivalent fits', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    context.close(); browser.close()

(OUT/'results.json').write_text(json.dumps(results, indent=2))
failed = [r for r in results if not r['ok']]
print(f'{len(results)-len(failed)}/{len(results)} checks pass')
raise SystemExit(bool(failed))
