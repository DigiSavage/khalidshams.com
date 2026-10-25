"""Exercise the public workflow without submitting or creating any client records.

Run: python tests/site/run_cached.py tests/engagement/ui_check.py BASE OUT
An optional final argument selects Chromium or WebKit. Only local downloads and
screenshots are saved. The shared analytics API is disabled in this test context.
"""
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://127.0.0.1:8767'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'work/engagement-check'
ENGINE = sys.argv[3] if len(sys.argv) > 3 else 'chromium'
ROUTE = '/method/engagement/'
DATA = json.loads((ROOT / 'content/engagement.json').read_text())
OUT.mkdir(parents=True, exist_ok=True)
RESULTS = []
EXPECTED = {
    'baseline': ('Pilot proposal', '160 to 252 person-hours', '$27,600 to $43,470 USD', 5),
    'autonomy': ('Re-scope required', '208 to 332 person-hours', '$35,880 to $57,270 USD', 6),
    'unowned': ('Hold', 'Delivery effort: not yet estimable', 'Delivery price: not established', 1),
    'deadline': ('Reduce scope', '96 to 144 person-hours', '$16,560 to $24,840 USD', 5),
}
TEXT_SPACING = '* {line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important} p {margin-bottom:2em!important}'


def check(name, ok, **evidence):
    RESULTS.append({'check': name, 'ok': bool(ok), **evidence})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)


def fits(page):
    return page.evaluate('document.documentElement.scrollWidth <= innerWidth')


def disabled_api(context):
    context.route('**/api/**', lambda route: route.fulfill(
        status=200, json={'available': False, 'collection': False}))


def wait_ready(page):
    page.locator('#eg-interactive').wait_for(state='visible')
    page.evaluate('document.fonts.ready')


def snapshot(page):
    return page.evaluate('''() => Object.fromEntries(
        ['decision','scope','test','operation','owner','hours','cost'].map(
            key => [key, document.getElementById('eg-' + key).textContent]))''')


def button_contrast(page):
    return page.locator('.eg button.btn').evaluate_all('''buttons => {
        const channels = value => (value.match(/[\\d.]+/g) || []).map(Number);
        const luminance = rgb => rgb.slice(0, 3).map(value => {
            value /= 255;
            return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
        }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
        return buttons.map(button => {
            const style = getComputedStyle(button);
            const foreground = channels(style.color), background = channels(style.backgroundColor);
            const light = luminance(foreground), dark = luminance(background);
            return {id:button.id, foreground:style.color, background:style.backgroundColor,
                opaque:background.length === 3 || background[3] === 1,
                contrast:(Math.max(light, dark) + 0.05) / (Math.min(light, dark) + 0.05),
                cursor:style.cursor};
        });
    }''')


with sync_playwright() as pw:
    browser = getattr(pw, ENGINE).launch()
    try:
        for width, theme in ((390, 'light'), (1380, 'light'), (390, 'dark'), (1380, 'dark')):
            label = f'{ENGINE} {width} {theme}'
            context = browser.new_context(viewport={'width': width, 'height': 900},
                                          color_scheme=theme, reduced_motion='reduce', has_touch=width == 390,
                                          accept_downloads=True)
            disabled_api(context)
            page = context.new_page()
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append((request.method, request.url)))
            try:
                page.goto(BASE + ROUTE, wait_until='networkidle')
                wait_ready(page)
                check(f'{label} readable page and disclosure', page.locator('h1').count() == 1
                      and 'not a historical client engagement' in page.locator('main').inner_text()
                      and fits(page))
                buttons = button_contrast(page)
                check(f'{label} action buttons have explicit readable backgrounds',
                      len(buttons) == 4 and all(button['opaque'] and button['contrast'] >= 4.5
                                               and button['cursor'] == 'pointer' for button in buttons),
                      buttons=buttons)
                page.screenshot(path=str(OUT / f'hero-{ENGINE}-{width}-{theme}.png'))
                initial_requests = len(requests)
                initial_storage = page.evaluate('({local:{...localStorage},session:{...sessionStorage}})')
                baseline_records = {}
                for audience, audience_data in DATA['audiences'].items():
                    page.locator('#eg-audience').select_option(audience)
                    for change, expected in EXPECTED.items():
                        page.locator('#eg-change').select_option(change)
                        status, hours, cost, row_count = expected
                        values = snapshot(page)
                        prefix = f'{label} {audience}/{change}'
                        check(prefix + ' audience and planning values',
                              page.locator('#eg-opening').inner_text() == audience_data['opening']
                              and page.locator('#eg-question').inner_text() == audience_data['question']
                              and page.locator('#eg-change-status').inner_text() == status
                              and values['hours'] == hours and values['cost'] == cost
                              and page.locator('#eg-rows tr').count() == row_count)
                        if audience == 'executive':
                            baseline_records[change] = values
                        check(prefix + ' decision remains consistent across audiences',
                              values == baseline_records[change] and 'D-01' in values['decision']
                              and all(values[field].strip() for field in ('scope', 'test', 'operation', 'owner')))
                        check(prefix + ' shareable state and layout',
                              parse_qs(urlsplit(page.url).query) == {'audience': [audience], 'change': [change]}
                              and fits(page))
                check(f'{label} changed requirement propagates through every record', all(
                    len({record[field] for record in baseline_records.values()}) == 4
                    for field in ('decision', 'scope', 'test', 'operation', 'owner')))
                check(f'{label} exercise creates no network requests or stored records',
                      len(requests) == initial_requests
                      and initial_storage == page.evaluate('({local:{...localStorage},session:{...sessionStorage}})'))
                page.locator('#eg-change').select_option('unowned')
                check(f'{label} unknown delivery is separated from discovery',
                      'Discovery' in page.locator('#eg-rows').inner_text()
                      and 'discovery only' in page.locator('#eg-estimate-note').inner_text().lower()
                      and '$0' not in page.locator('#eg-cost').inner_text())
                with page.expect_download() as download_event:
                    page.locator('#eg-download').click()
                download = download_event.value
                download_path = OUT / f'brief-{ENGINE}-{width}-{theme}.txt'
                download.save_as(download_path)
                brief = download_path.read_text()
                check(f'{label} downloaded brief includes current hold and honest boundaries',
                      download.suggested_filename == 'shams-engagement-unowned.txt'
                      and 'D-01 CHANGE ASSESSMENT: Hold' in brief
                      and 'Delivery hours and price are not established' in brief
                      and 'Observed business results: not measured.' in brief
                      and 'Teaching example, not a quote for services. I do not offer paid consultations through this site.' in brief
                      and 'BASELINE WORKFLOW REFERENCE' in brief
                      and all(stage['title'].upper() in brief for stage in DATA['stages']))
                page.goto(BASE + ROUTE + '?audience=risk&change=unowned&token=private&approval=approved#decision')
                wait_ready(page)
                page.locator('#eg-reset').press('Enter')
                check(f'{label} keyboard reset removes arbitrary URL state',
                      page.locator('#eg-audience').input_value() == 'executive'
                      and page.locator('#eg-change').input_value() == 'baseline'
                      and parse_qs(urlsplit(page.url).query) == {'audience': ['executive'], 'change': ['baseline']}
                      and 'private' not in page.locator('main').inner_text())
                page.locator('#eg-audience').focus()
                # Native select menus differ across desktop engines. Typeahead
                # cycles from Executive to Engineering without popup automation.
                page.keyboard.press('e')
                page.keyboard.press('Tab')
                check(f'{label} audience control is usable by keyboard',
                      page.locator('#eg-audience').input_value() == 'engineering'
                      and page.locator('#eg-change').evaluate('(element) => element === document.activeElement'),
                      value=page.locator('#eg-audience').input_value(), focus=page.evaluate('document.activeElement.id'))
                artifact = page.locator('#stage-prepare .eg-artifact')
                artifact.locator('summary').press('Enter')
                check(f'{label} artifact opens using keyboard', artifact.get_attribute('open') is not None
                      and artifact.locator('ul').is_visible())
                artifact.locator('summary').press('Enter')
                page.locator('#eg-change').select_option('baseline')
                page.locator('#decision').screenshot(path=str(OUT / f'decision-{ENGINE}-{width}-{theme}.png'),
                    style='.site-head,.pagenav{visibility:hidden!important}')
                page.locator('#stage-prepare').screenshot(path=str(OUT / f'prepare-{ENGINE}-{width}-{theme}.png'),
                    style='.site-head,.pagenav{visibility:hidden!important}')
                sources = page.locator('details').filter(has=page.locator('.eg-sources'))
                sources.locator('summary').click()
                page.locator('a[href="#source-copilot"]').click()
                page.wait_for_function('document.querySelector("#source-copilot").closest("details").open')
                check(f'{label} source reference opens a collapsed panel',
                      page.locator('#source-copilot').is_visible() and urlsplit(page.url).fragment == 'source-copilot')
                sources.locator('summary').click()
                page.locator('a[href="#source-copilot"]').click()
                check(f'{label} repeated source reference remains usable',
                      page.locator('#source-copilot').is_visible())
                if width == 1380:
                    page.set_viewport_size({'width': 1380, 'height': 720})
                    nav = page.locator('.eg-journey nav')
                    nav.scroll_into_view_if_needed()
                    nav_box = nav.bounding_box()
                    nav.locator('a[href="#stage-partner"]').click()
                    heading = page.locator('#stage-partner h3').bounding_box()
                    check(f'{label} stage navigation fits a short desktop and reaches the final stage',
                          nav_box['height'] <= 574 and heading['y'] >= 0 and heading['y'] < 720,
                          navigation=nav_box, finalHeading=heading)
                    page.set_viewport_size({'width': 1380, 'height': 900})
                before_print = page.locator('.eg details').evaluate_all('(items) => items.map(item => item.open)')
                page.evaluate('window.dispatchEvent(new Event("beforeprint"))')
                page.emulate_media(media='print')
                check(f'{label} print includes evidence, sources and every artifact',
                      page.locator('#proof').is_visible()
                      and page.locator('.eg-artifact[open]').count() == 11
                      and page.locator('.eg-controls').is_hidden())
                page.evaluate('window.dispatchEvent(new Event("afterprint"))')
                page.emulate_media(media='screen')
                check(f'{label} printing restores the reader disclosure state',
                      before_print == page.locator('.eg details').evaluate_all('(items) => items.map(item => item.open)'))
                page.add_style_tag(content=TEXT_SPACING)
                check(f'{label} increased text spacing preserves page width', fits(page))
                check(f'{label} no script errors', not errors, pageErrors=errors)
            except Exception as error:
                check(f'{label} browser scenario completed', False, error=str(error))
            finally:
                context.close()

        context = browser.new_context(viewport={'width': 320, 'height': 844}, color_scheme='dark',
                                      reduced_motion='reduce', has_touch=True)
        disabled_api(context)
        page = context.new_page()
        try:
            page.goto(BASE + ROUTE)
            wait_ready(page)
            page.locator('.eg details').evaluate_all('(items) => items.forEach(item => { item.open = true; })')
            page.add_style_tag(content=TEXT_SPACING)
            check(f'{ENGINE} 320 dark with increased text spacing and all artifacts open fits',
                  fits(page) and page.locator('.eg-artifact[open]').count() == 11)
            clipping = page.locator('.eg :is(p,li,dd,button,select)').evaluate_all('''items => items
                .filter(item => item.getClientRects().length && item.scrollWidth > item.clientWidth + 1)
                .map(item => ({tag:item.tagName,id:item.id,text:item.textContent.slice(0,80),
                    width:item.clientWidth,scrollWidth:item.scrollWidth}))''')
            check(f'{ENGINE} 320 expanded content and controls do not clip horizontally', not clipping, clipping=clipping)
            page.locator('#stage-prepare').screenshot(path=str(OUT / f'prepare-{ENGINE}-320-dark-text-spacing.png'),
                style='.site-head,.pagenav{visibility:hidden!important}')
        except Exception as error:
            check(f'{ENGINE} 320 expanded-content scenario completed', False, error=str(error))
        finally:
            context.close()

        context = browser.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
        disabled_api(context)
        page = context.new_page()
        page.goto(BASE + ROUTE)
        check(f'{ENGINE} no-script workflow remains readable',
              page.locator('.eg-stage').count() == 11
              and page.locator('#eg-interactive').is_hidden()
              and 'needs JavaScript' in page.locator('noscript').inner_text()
              and fits(page))
        page.locator('#stage-prepare summary').click()
        check(f'{ENGINE} no-script artifact stays accessible', page.locator('#stage-prepare .eg-artifact ul').is_visible())
        audience_details = page.locator('details').filter(has=page.locator('summary', has_text='Read all four audience briefs'))
        audience_details.locator('summary').click()
        check(f'{ENGINE} all audience explanations exist without JavaScript',
              audience_details.locator('article').count() == 4
              and audience_details.locator('article').last.is_visible())
        context.close()

        context = browser.new_context(viewport={'width': 1380, 'height': 900}, reduced_motion='reduce')
        disabled_api(context)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        try:
            for query in ('?audience=%3Cscript%3E&change=approved', '?audience=risk&audience=engineering&change=unowned&change=autonomy'):
                page.goto(BASE + ROUTE + query)
                wait_ready(page)
                check(f'{ENGINE} malformed query {query} cannot inject or expand authority',
                      page.locator('#eg-audience').input_value() == 'executive'
                      and page.locator('#eg-change').input_value() == 'baseline'
                      and page.locator('#eg-hours').inner_text() == EXPECTED['baseline'][1]
                      and page.locator('main script').count() == 0)
            page.goto(BASE + '/privacy/')
            page.locator('body').press(('Meta' if sys.platform == 'darwin' else 'Control') + '+k')
            search = page.locator('.ks-search input[type=search]')
            search.wait_for(state='visible')
            search.fill('Prepare before the first conversation')
            page.locator('.ks-item').first.wait_for(state='visible')
            destination = page.locator('.ks-item').first.get_attribute('href')
            check(f'{ENGINE} site search discovers engagement preparation', destination.startswith(ROUTE))
            search.press('Enter')
            page.wait_for_url(BASE + destination)
            page.locator('mark.ks-hl').first.wait_for(state='attached')
            check(f'{ENGINE} keyboard search navigates and highlights the workflow',
                  page.locator('mark.ks-hl').count() > 0 and urlsplit(page.url).path == ROUTE and not errors)
        except Exception as error:
            check(f'{ENGINE} query and search checks completed', False, error=str(error))
        finally:
            context.close()
    finally:
        browser.close()
        (OUT / f'checks-{ENGINE}.json').write_text(json.dumps(RESULTS, indent=2) + '\n')

failed = sum(not result['ok'] for result in RESULTS)
print(f'{len(RESULTS) - failed}/{len(RESULTS)} passed')
sys.exit(bool(failed))
