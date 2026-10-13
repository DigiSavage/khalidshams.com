"""Check the paid-review discovery and inquiry flow without contacting the live API.

Build and serve dist, then run: python tests/commercial/ui_check.py BASE OUT
All API requests are intercepted. The submitted fixture is checked against the
existing backend contract and its packaged page registry, never persisted.
"""
import importlib.util
import json
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:8767'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('/tmp/commercial-check')
OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('site_contracts', ROOT / 'services/site-admin/contracts.py')
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)
PAGES = json.loads((ROOT / 'services/site-admin/pages.json').read_text())
OFFER = '/contact/?offer=architecture-review'
results = []


def check(name, ok):
    results.append({'check': name, 'ok': bool(ok)})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)


def api_fixture(context):
    submissions, unexpected = [], []

    def respond(route):
        request = route.request
        path = urlsplit(request.url).path
        if path == '/api/config' and request.method == 'GET':
            route.fulfill(json={'available': False, 'collection': False})
        elif path == '/api/contact/challenge' and request.method == 'GET':
            route.fulfill(json={'challenge': 'commercial-fixture-challenge'})
        elif path == '/api/contact' and request.method == 'POST':
            payload = request.post_data_json
            submissions.append(payload)
            try:
                contracts.inquiry(payload, PAGES)
                route.fulfill(status=201, json={'stored': True, 'id': payload['id']})
            except contracts.Invalid as error:
                route.fulfill(status=400, json={'error': str(error)})
        else:
            unexpected.append((request.method, path))
            route.fulfill(status=503, json={'error': 'Unexpected fixture request'})

    context.route('**/api/**', respond)
    return submissions, unexpected


def submit_fixture(page):
    page.locator('[name=name]').fill('Commercial browser fixture')
    page.locator('[name=email]').fill('commercial@example.test')
    page.locator('[name=company]').fill('Fixture company')
    page.locator('[name=message]').fill(
        '[Architecture Decision Review]\nI need a written comparison of two tenant isolation options.'
    )
    page.locator('#contact-form button[type=submit]').click()
    page.wait_for_function("document.querySelector('#contact-status').textContent.includes('has been stored')")


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for theme in ('light', 'dark'):
        for width in (390, 1380):
            label = f'{theme} {width}'
            context = browser.new_context(
                viewport={'width': width, 'height': 900}, color_scheme=theme,
                reduced_motion='reduce', has_touch=width == 390,
            )
            submissions, unexpected = api_fixture(context)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE + '/#work-with-me')
            section = page.locator('#work-with-me')
            check(f'{label} paid review has a discoverable home',
                  section.is_visible() and 'Architecture Decision Review' in section.inner_text())
            check(f'{label} offer fits viewport',
                  page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            section.screenshot(path=str(OUT / f'offer-{width}-{theme}.png'),
                               style='.site-head,.pagenav{visibility:hidden!important}')
            sample = section.locator('details')
            sample.locator('summary').press('Enter')
            check(f'{label} sample brief opens by keyboard without overflow',
                  sample.locator('article').is_visible()
                  and page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            if width == 1380 and theme == 'light':
                sample.screenshot(path=str(OUT / 'sample-brief-1380-light.png'),
                                  style='.site-head,.pagenav{visibility:hidden!important}')
            sample.locator('summary').press('Enter')
            section.locator(f'a[href="{OFFER}"]').first.press('Enter')
            page.wait_for_url(BASE + OFFER)
            check(f'{label} keyboard CTA opens explanatory contact context',
                  page.locator('#offer-context').is_visible())
            message = page.locator('[name=message]')
            check(f'{label} editable brief is prefilled for architecture',
                  page.locator('[name=topic]').input_value() == 'architecture'
                  and '[Architecture Decision Review]' in message.input_value()
                  and message.is_editable())
            check(f'{label} inquiry requests no payment credentials',
                  page.locator('#contact-form [autocomplete^="cc-"],'
                               '#contact-form input[type=password],#contact-form iframe').count() == 0)
            check(f'{label} contact fits viewport',
                  page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            page.wait_for_function("!document.querySelector('#contact-form button[type=submit]').disabled")
            page.screenshot(path=str(OUT / f'contact-{width}-{theme}.png'), full_page=True)
            submit_fixture(page)
            check(f'{label} existing inquiry contract accepts offer without new fields',
                  len(submissions) == 1 and submissions[0]['source'] == '/'
                  and submissions[0]['topic'] == 'architecture'
                  and submissions[0]['challenge'] == 'commercial-fixture-challenge'
                  and submissions[0].get('test') is False)
            check(f'{label} successful inquiry waits for storage confirmation',
                  page.locator('#contact-form').is_hidden())
            check(f'{label} no unexpected API calls or script errors', not unexpected and not errors)
            context.close()

    # A direct bookmarked offer must still satisfy the deployed page registry
    # when browser storage is denied and click-based attribution is unavailable.
    context = browser.new_context()
    context.add_init_script("""
        Object.defineProperty(window, 'sessionStorage', {
            get() { throw new DOMException('Blocked by browser preference', 'SecurityError'); }
        });
    """)
    submissions, unexpected = api_fixture(context)
    page = context.new_page()
    page.goto(BASE + OFFER)
    submit_fixture(page)
    check('direct offer inquiry succeeds with session storage blocked',
          len(submissions) == 1 and submissions[0]['source'] == '/' and not unexpected)
    context.close()

    context = browser.new_context()
    api_fixture(context)
    page = context.new_page()
    for query in ('', '?offer=unknown', '?offer=' + quote('<img src=x onerror=alert(1)>', safe='')):
        page.goto(BASE + '/contact/' + query)
        check(f'unsupported offer {query or "absent"} leaves general inquiry unchanged',
              page.locator('#offer-context').is_hidden()
              and page.locator('[name=message]').input_value() == '')
    page.goto(BASE + OFFER + '&message=untrusted-prefill&topic=cloud&price=1&source=https://example.test')
    check('arbitrary query fields cannot change the offer or inquiry',
          'untrusted-prefill' not in page.locator('[name=message]').input_value()
          and page.locator('[name=topic]').input_value() == 'architecture')
    context.close()

    # Simulate a browser restoring a draft before the deferred contact script.
    context = browser.new_context()
    api_fixture(context)
    context.add_init_script("""
        document.addEventListener('readystatechange', () => {
            if (document.readyState === 'interactive') {
                const field = document.querySelector('[name=message]');
                if (field) field.value = 'Existing draft about a cloud migration decision.';
            }
        });
    """)
    page = context.new_page()
    page.goto(BASE + OFFER)
    check('offer context preserves an existing browser-restored message',
          page.locator('[name=message]').input_value() == 'Existing draft about a cloud migration decision.')
    context.close()

    for width in (390, 1380):
        context = browser.new_context(viewport={'width': width, 'height': 900})
        api_fixture(context)
        page = context.new_page()
        page.goto(BASE + '/privacy/')
        if width == 390:
            page.locator('.sh-burger').click()
            group = page.locator('.dr-group[data-href="/#work"]')
            group.locator('summary').click()
            group.locator('a[href="/#work-with-me"]').click()
        else:
            work = page.locator('.sh-item:has(> a[href="/#work"])')
            work.hover()
            work.locator('a[href="/#work-with-me"]').click()
        page.wait_for_url(BASE + '/#work-with-me')
        check(f'{width} Work menu reaches the paid review', page.locator('#work-with-me').is_visible())
        page.goto(BASE + '/privacy/')
        page.locator('footer a[href="/#work-with-me"]').first.click()
        page.wait_for_url(BASE + '/#work-with-me')
        check(f'{width} footer reaches the paid review', page.locator('#work-with-me').is_visible())
        context.close()

    context = browser.new_context(java_script_enabled=False)
    api_fixture(context)
    page = context.new_page()
    page.goto(BASE + '/#work-with-me')
    check('offer remains readable with JavaScript disabled',
          page.locator('#work-with-me').is_visible()
          and page.locator(f'#work-with-me a[href="{OFFER}"]').count() > 0)
    page.locator(f'#work-with-me a[href="{OFFER}"]').first.click()
    check('no-script contact keeps a direct email fallback',
          page.locator('main a[href="mailto:khalidshams@gmail.com"]').is_visible())
    context.close()
    browser.close()

(OUT / 'checks.json').write_text(json.dumps(results, indent=2) + '\n')
failed = sum(not result['ok'] for result in results)
print(f'{len(results) - failed}/{len(results)} passed')
sys.exit(bool(failed))
