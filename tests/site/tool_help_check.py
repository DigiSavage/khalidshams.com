"""Every playbook tool opens a readable, dismissible explanation in place."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import build

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:8767'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'work/tool-help'
OUT.mkdir(parents=True, exist_ok=True)
results = []


def check(name, ok):
    results.append({'check': name, 'ok': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)


with sync_playwright() as pw:
    browser = getattr(pw, sys.argv[3] if len(sys.argv) > 3 else 'chromium').launch()
    for width, theme in [(390, 'dark'), (1440, 'light')]:
        context = browser.new_context(viewport={'width': width, 'height': 844}, color_scheme=theme,
                                      has_touch=True, reduced_motion='reduce')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        for pb in build.load_playbooks():
            page.goto(BASE + pb.url)
            check(f'{width} {pb.slug} all tools have controls', page.locator('.pb-tool-trigger').count() == len(pb.stack))
            for trigger in page.locator('.pb-tool-trigger').all():
                term = trigger.inner_text().rstrip('?').strip()
                trigger.click()
                panel = page.locator('#' + trigger.get_attribute('popovertarget'))
                expect(panel).to_be_visible()
                bounds = panel.bounding_box()
                check(f'{width} {pb.slug} {term} explanation opens in place',
                      panel.evaluate('(p)=>p.matches(":popover-open")') and
                      panel.locator('h3').inner_text() == term and
                      len(panel.locator('.pb-tool-memory').inner_text()) > 25 and
                      panel.locator('a').get_attribute('href').startswith('https://') and
                      bounds['x'] >= 0 and bounds['x'] + bounds['width'] <= width + 1 and
                      page.url == BASE + pb.url)
                if term == 'Azure Landing Zones' and pb.slug == 'cloud-foundations-multitenant':
                    page.screenshot(path=str(OUT / f'landing-zones-{width}-{theme}.png'))
                panel.locator('.pb-tool-close').click()
                expect(panel).not_to_be_visible()
            check(f'{width} {pb.slug} no page overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        page.goto(BASE + '/playbooks/cloud-foundations-multitenant/')
        trigger = page.locator('.pb-tool-trigger[popovertarget="pb-tool-aks"]')
        trigger.focus()
        trigger.press('Enter')
        expect(page.locator('#pb-tool-aks')).to_be_visible()
        page.keyboard.press('Escape')
        check(f'{width} keyboard closes and returns focus', page.locator('#pb-tool-aks').is_hidden() and trigger.evaluate('(e)=>e===document.activeElement'))
        trigger.click()
        page.mouse.click(3, 3)
        expect(page.locator('#pb-tool-aks')).not_to_be_visible()
        check(f'{width} outside click dismisses explanation', page.locator('#pb-tool-aks').is_hidden())
        page.goto(BASE + '/playbooks/cloud-foundations-multitenant/#pb-tool-aks-title')
        expect(page.locator('#pb-tool-aks')).to_be_visible()
        check(f'{width} search deep link opens its definition', page.locator('#pb-tool-aks').is_visible())
        check(f'{width} no script errors', not errors)
        context.close()
    context = browser.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
    page = context.new_page()
    page.goto(BASE + '/playbooks/cloud-foundations-multitenant/')
    page.locator('[popovertarget="pb-tool-aks"]').first.click()
    check('Native explanation works without JavaScript', page.locator('#pb-tool-aks').is_visible())
    context.close()
    browser.close()

(OUT / 'checks.json').write_text(json.dumps(results, indent=2) + '\n')
failed = sum(not r['ok'] for r in results)
print(f'{len(results) - failed}/{len(results)} passed')
sys.exit(bool(failed))
