"""A closed mobile group expands; activating an open group visits its landing page."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:8767'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('work/menu-check')
OUT.mkdir(parents=True, exist_ok=True)
DESTINATIONS = ['/', '/learn/', '/architect/', '/method/', '/playbooks/', '/tools/', '/writing/', '/#work']
results = []


def check(name, ok):
    results.append({'check': name, 'ok': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)


with sync_playwright() as pw:
    browser = getattr(pw, sys.argv[3] if len(sys.argv) > 3 else 'chromium').launch()
    for theme in ('light', 'dark'):
        context = browser.new_context(viewport={'width': 390, 'height': 844},
                                      has_touch=True, color_scheme=theme, reduced_motion='reduce')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        for destination in DESTINATIONS:
            # The current section is pre-expanded. Start elsewhere to exercise both taps.
            start = '/privacy/' if destination == '/learn/' else '/learn/'
            page.goto(BASE + start)
            page.locator('.sh-burger').tap()
            group = page.locator(f'.dr-group[data-href="{destination}"]')
            summary = group.locator('summary')
            summary.tap()
            check(f'{theme} {destination} first tap expands without navigating',
                  group.evaluate('(g) => g.open') and page.url == BASE + start)
            if destination == '/learn/':
                page.screenshot(path=str(OUT / f'learn-menu-{theme}.png'))
            arrow = group.locator('..').locator('.dr-toggle')
            box = arrow.bounding_box()
            check(f'{theme} {destination} arrow is a separate accessible touch target',
                  box['width'] >= 44 and box['height'] >= 44 and
                  arrow.get_attribute('aria-expanded') == 'true' and
                  page.locator('#' + arrow.get_attribute('aria-controls')).count() == 1)
            arrow.tap()
            check(f'{theme} {destination} arrow collapses without navigating or closing drawer',
                  not group.evaluate('(g)=>g.open') and arrow.get_attribute('aria-expanded') == 'false' and
                  page.url == BASE + start and page.locator('#drawer').is_visible())
            arrow.tap()
            check(f'{theme} {destination} arrow reopens without navigating',
                  group.evaluate('(g)=>g.open') and arrow.get_attribute('aria-expanded') == 'true' and page.url == BASE + start)
            summary.tap()
            page.wait_for_url(BASE + destination)
            check(f'{theme} {destination} second tap navigates and closes drawer',
                  page.locator('#drawer').is_hidden())
        for key in ('Enter', 'Space'):
            page.goto(BASE + '/privacy/')
            page.locator('.sh-burger').click()
            summary = page.locator('.dr-group[data-href="/learn/"] summary')
            arrow = summary.locator('../..').locator('.dr-toggle')
            arrow.press(key)
            check(f'{theme} {key} arrow expands without navigating',
                  arrow.get_attribute('aria-expanded') == 'true' and page.url == BASE + '/privacy/')
            arrow.press(key)
            check(f'{theme} {key} arrow collapses without navigating',
                  arrow.get_attribute('aria-expanded') == 'false' and page.url == BASE + '/privacy/')
            summary.focus()
            summary.press(key)
            check(f'{theme} {key} expands Learn', summary.locator('..').evaluate('(g) => g.open'))
            summary.press(key)
            page.wait_for_url(BASE + '/learn/')
            check(f'{theme} {key} navigates to Learn', page.locator('#drawer').is_hidden())
        page.locator('.sh-burger').tap()
        page.locator('.dr-group[data-href="/learn/"] a[href="/learn/#map"]').tap()
        page.wait_for_url(BASE + '/learn/#map')
        check(f'{theme} submenu anchor still navigates and closes drawer', page.locator('#drawer').is_hidden())
        page.locator('.sh-burger').tap()
        page.keyboard.press('Escape')
        check(f'{theme} Escape still closes drawer', page.locator('#drawer').is_hidden())
        check(f'{theme} no script errors or horizontal overflow',
              not errors and page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        context.close()
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.goto(BASE + '/privacy/')
    page.locator('.sh-item > a[href="/learn/"]').click()
    page.wait_for_url(BASE + '/learn/')
    check('Desktop Learn link still navigates on first click', page.url == BASE + '/learn/')
    context.close()
    browser.close()

(OUT / 'checks.json').write_text(json.dumps(results, indent=2) + '\n')
failed = sum(not result['ok'] for result in results)
print(f'{len(results) - failed}/{len(results)} passed')
sys.exit(bool(failed))
