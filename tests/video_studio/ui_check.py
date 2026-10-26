"""Browser acceptance against real handlers and isolated moto AWS resources.

All mutations below occur only in the local fixture database. No production
session, client record, recording, or model service is used.
"""
import json
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/decision_room'))
from test_backend import Fixture, room
import app
import video_studio as studio

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/video-studio-ui')
OUT.mkdir(parents=True, exist_ok=True)
BASE = 'http://localhost:8778'
API = studio.ROOT
f = Fixture()
os.environ['PUBLIC_ORIGIN'] = BASE
f.auth.origin = room.AUTH.origin = BASE
checks = []


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'dist'), **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/__fixture__/login':
            f.login()
            self.send_response(204)
            self.send_header('Set-Cookie', '__Host-ks-session=' + f.sid + '; Path=/; HttpOnly; SameSite=Lax; Secure')
            self.end_headers()
        elif self.path.startswith('/api/'):
            self.api()
        else:
            super().do_GET()

    def do_POST(self): self.api()
    def do_PATCH(self): self.api()
    def do_DELETE(self): self.api()

    def api(self):
        url = urlsplit(self.path)
        headers = dict(self.headers)
        headers['X-Site-Origin'] = app.SALT
        headers['CloudFront-Viewer-Address'] = '192.0.2.1:1'
        event = dict(path=url.path, httpMethod=self.command, headers=headers,
                     body=self.rfile.read(int(self.headers.get('Content-Length', '0'))).decode(),
                     queryStringParameters={k: v[0] for k, v in parse_qs(url.query).items()})
        result = (room.handler if url.path.startswith(room.ROOT) else app.handler)(event)
        self.send_response(result['statusCode'])
        for key, value in result['headers'].items(): self.send_header(key, value)
        for key, values in result.get('multiValueHeaders', {}).items():
            for value in values: self.send_header(key, value)
        self.end_headers()
        self.wfile.write(result['body'].encode())


def check(label, condition):
    checks.append({'check': label, 'ok': bool(condition)})
    print(('PASS ' if condition else 'FAIL ') + label, flush=True)
    assert condition, label


def clear_fixture_records():
    for row in f.table.scan()['Items']:
        f.table.delete_item(Key={'pk': row['pk'], 'sk': row['sk']})


def videos():
    return json.loads(f.request(API)['body'])['items']


def saved(ident):
    return json.loads(f.request(API + '/' + ident)['body'])['video']


def tab(page, name):
    page.locator('[data-tab=' + name + ']').click()


def save(page):
    page.locator('#vs-save').click()
    page.wait_for_function("() => document.querySelector('#vs-save-state').textContent === 'Saved'")


def create_template(page):
    page.locator('#vs-templates button').first.click()
    page.locator('#vs-create-form button[type=submit]').click()
    page.locator('#vs-workbench').wait_for(state='visible')
    page.wait_for_function("() => document.querySelector('#vs-status').textContent.includes('created')")
    return videos()[0]['id']


def visibility(page, hidden):
    page.evaluate("hidden => {Object.defineProperty(document,'hidden',{configurable:true,value:hidden});document.dispatchEvent(new Event('visibilitychange'));}", hidden)


server = HTTPServer(('localhost', 8778), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE + '/admin/video-studio/')
        page.wait_for_function("() => document.querySelector('#vs-status').textContent.includes('expired')")
        check('signed-out shell masks the private studio', page.locator('#vs-app').is_hidden())
        check('signed-out catalog is denied', context.request.get(BASE + API + '/catalog').status == 401)
        context.close()

        for width, theme in [(1380, 'light'), (1380, 'dark'), (390, 'light'), (390, 'dark'), (320, 'light')]:
            context = browser.new_context(viewport={'width': width, 'height': 1000}, color_scheme=theme)
            context.request.get(BASE + '/__fixture__/login')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE + '/admin/video-studio/')
            page.locator('#vs-app').wait_for(state='visible')
            check(f'research fits {width} {theme}', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            expected_date = datetime.strptime(studio.catalog()['checked_at'], '%Y-%m-%d').strftime('%b %d, %Y')
            check(f'calendar research date is preserved {width} {theme}', expected_date in page.locator('#vs-catalog-date').inner_text())
            check(f'catalog does not seed records {width} {theme}', f.table.scan()['Count'] == 0)
            page.screenshot(path=str(OUT / f'research-{width}-{theme}.png'), full_page=True)
            page.locator('#vs-playbook-nav').click()
            check(f'shared approach available {width} {theme}', page.locator('#vs-playbook').is_visible() and studio.catalog()['playbook']['promise'] in page.locator('#vs-playbook-content').inner_text())
            check(f'approach does not seed episodes {width} {theme}', f.table.scan()['Count'] == 0)
            page.screenshot(path=str(OUT / f'approach-{width}-{theme}.png'), full_page=True)
            groups = page.locator('.vs-method-group')
            fits = True
            for i in range(groups.count()):
                groups.nth(i).locator('summary').click()
                fits = fits and page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            check(f'expanded approach and roadmap fit {width} {theme}', fits)
            check(f'roadmap links only to authored drafts {width} {theme}', page.locator('#vs-playbook-content button').count() == len(studio.catalog()['templates']))
            page.locator('#vs-research-nav').click()
            create_template(page)
            for name in ['brief', 'beats', 'sources', 'readiness', 'transcript']:
                tab(page, name)
                check(f'editor {name} fits {width} {theme}', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            tab(page, 'beats')
            page.screenshot(path=str(OUT / f'beats-{width}-{theme}.png'), full_page=True)
            page.locator('#vs-rehearse').click()
            check(f'rehearsal fits {width} {theme}', page.locator('#vs-rehearsal-dialog').evaluate('(e) => e.scrollWidth <= e.clientWidth + 1'))
            check(f'rehearsal navigation visible {width} {theme}', page.locator('#vs-rehearsal-next').evaluate('(e) => e.getBoundingClientRect().bottom <= innerHeight'))
            page.screenshot(path=str(OUT / f'rehearsal-{width}-{theme}.png'))
            page.locator('#vs-rehearsal-next').click()
            check(f'rehearsal next beat {width} {theme}', 'Beat 2 of' in page.locator('#vs-rehearsal-position').inner_text())
            page.locator('#vs-timer-toggle').click()
            check(f'rehearsal timer starts {width} {theme}', page.locator('#vs-timer-toggle').inner_text() == 'Pause timer')
            page.locator('#vs-timer-toggle').click()
            page.locator('#vs-rehearsal-close').click()
            check(f'no script errors {width} {theme}', not errors)
            clear_fixture_records()
            context.close()

        context = browser.new_context(viewport={'width': 1380, 'height': 1000}, accept_downloads=True)
        context.request.get(BASE + '/__fixture__/login')
        page = context.new_page()
        errors, security_errors, traffic = [], [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda msg: security_errors.append(msg.text) if 'violates' in msg.text.lower() or 'content security policy' in msg.text.lower() else None)
        page.on('request', lambda request: traffic.append(request.url))
        page.goto(BASE + '/admin/video-studio/')
        page.locator('#vs-app').wait_for(state='visible')
        ident = create_template(page)
        check('explicit creation persists one episode', len(videos()) == 1)
        page.locator('#vs-title').fill('<img src=x onerror=alert(1)> Browser fixture')
        page.locator('#vs-notes').fill('PRIVATE-VIDEO-CANARY-9381')
        page.locator('#vs-playbook-nav').click()
        page.locator('#vs-library-nav').click()
        check('approach navigation retains unsaved episode', page.locator('#vs-notes').input_value() == 'PRIVATE-VIDEO-CANARY-9381' and page.locator('#vs-save-state').inner_text() == 'Unsaved changes')
        tab(page, 'sources')
        page.locator('#vs-editor').get_by_label('Source title', exact=True).first.fill('<svg onload=alert(1)> Fixture source')
        page.locator('#vs-editor').get_by_label('Source URL · HTTPS', exact=True).first.fill('javascript:alert(1)')
        page.locator('#vs-save').click()
        page.wait_for_function("() => document.querySelector('#vs-status').textContent.includes('HTTPS')")
        check('unsafe source URL is rejected before save', saved(ident)['revision'] == 0)
        page.locator('#vs-editor').get_by_label('Source URL · HTTPS', exact=True).first.fill('https://example.com/fixture-source')
        page.locator('#vs-editor').get_by_label('Claim supported, date and limits', exact=True).first.fill('<img src=x onerror=alert(1)> Synthetic evidence for browser tests only.')
        tab(page, 'transcript')
        page.locator('#vs-transcript').fill('<img src=x onerror=alert(1)> This is a synthetic recorded transcript, not a real video.')
        save(page)
        check('private title markup remains inert', page.locator('#vs-video-title img,#vs-video-title script').count() == 0)
        tab(page, 'sources')
        check('source markup remains inert', page.locator('#vs-editor svg,#vs-editor img,#vs-editor script').count() == 0)
        check('source links use HTTPS and noreferrer', page.locator('#vs-editor .vs-sources a').evaluate_all("nodes => nodes.every(n => n.href.startsWith('https:') && n.rel.includes('noreferrer'))"))
        check('real save persists edited notes', saved(ident)['draft']['notes'] == 'PRIVATE-VIDEO-CANARY-9381')
        check('private data absent from URL and browser storage', ident not in page.url and page.evaluate("!Object.values(localStorage).join('').includes('CANARY') && !Object.values(sessionStorage).join('').includes('CANARY')"))
        for kind, filename in [('pack', 'shooting-pack.md'), ('script', 'draft-script.txt'), ('transcript', 'recorded-transcript.txt')]:
            before = len(traffic)
            with page.expect_download() as got:
                page.locator('#vs-export-' + kind).click()
            got.value.save_as(OUT / filename)
            check(kind + ' export freshly authorizes and reads saved revision', BASE + '/api/auth/session' in traffic[before:] and BASE + API + '/' + ident in traffic[before:])
        check('shooting pack includes responsibilities and encoded markup', all(value in (OUT / 'shooting-pack.md').read_text() for value in ['What Khalid does', 'What Codex prepares', '&lt;img', 'Readiness']))
        check('script export cannot be mistaken for a recorded transcript', 'not a recorded transcript' in (OUT / 'draft-script.txt').read_text())
        check('recorded transcript is separate plain text', 'synthetic recorded transcript' in (OUT / 'recorded-transcript.txt').read_text())

        page.reload()
        page.locator('#vs-app').wait_for(state='visible')
        page.locator('#vs-library-nav').click()
        page.locator('.vs-video-item').click()
        page.locator('#vs-workbench').wait_for(state='visible')
        check('saved notes survive a page reload', page.locator('#vs-notes').input_value() == 'PRIVATE-VIDEO-CANARY-9381')
        tab(page, 'readiness')
        for name in ['evidence', 'clarity', 'rehearsal', 'privacy', 'save']:
            page.locator('#vs-check-' + name).check()
        page.locator('#vs-stage').select_option('ready')
        save(page)
        check('reviewed preparation saves ready stage', saved(ident)['draft']['stage'] == 'ready')
        tab(page, 'brief')
        page.locator('#vs-notes').fill('Changed content for readiness regression.')
        tab(page, 'readiness')
        check('content edits reset readiness in the editor', page.locator('#vs-stage').input_value() == 'rehearsal' and not page.locator('#vs-check-evidence').is_checked())
        save(page)
        check('readiness reset persists', saved(ident)['draft']['stage'] == 'rehearsal' and not any(c['done'] for c in saved(ident)['draft']['checklist']))

        tab(page, 'brief')
        page.locator('#vs-notes').fill('Unsaved conflict copy')
        current = saved(ident)
        f.request(API + '/' + ident, 'PATCH', {'revision': current['revision'], 'draft': {'notes': 'Concurrent fixture edit'}})
        page.locator('#vs-save').click()
        page.locator('#vs-conflict').wait_for(state='visible')
        check('conflict preserves unsaved edits', page.locator('#vs-notes').input_value() == 'Unsaved conflict copy')
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('#vs-reload').click()
        page.wait_for_function("() => document.querySelector('#vs-conflict').hidden")
        check('explicit reload obtains concurrent revision', page.locator('#vs-notes').input_value() == 'Concurrent fixture edit')

        page.locator('#vs-notes').fill('Saved despite failed library refresh')
        def fail_list(route):
            if route.request.method == 'GET':
                route.fulfill(status=503, content_type='application/json', body=json.dumps({'error': 'Isolated list refresh failure'}))
            else:
                route.continue_()
        page.route(BASE + API, fail_list)
        save(page)
        page.wait_for_function("() => document.querySelector('#vs-status').textContent.includes('could not refresh')")
        check('successful save is retained when list refresh fails', saved(ident)['draft']['notes'] == 'Saved despite failed library refresh' and page.locator('#vs-save').is_disabled())
        page.unroute(BASE + API, fail_list)

        tab(page, 'beats')
        original_count = len(saved(ident)['draft']['beats'])
        page.locator('#vs-add-beat').click()
        last = page.locator('#vs-editor .vs-card').last
        last.get_by_label('Beat label', exact=True).fill('New fixture beat')
        last.get_by_label('What I say · Draft spoken script', exact=True).fill('I describe a synthetic browser check and its limits.')
        last.get_by_label('What I click · Screen actions', exact=True).fill('Open the local fixture screen.')
        last.get_by_label('What Khalid does', exact=True).fill('Describe the test.')
        last.get_by_label('What Codex prepares', exact=True).fill('Prepare the local fixture.')
        last.get_by_role('button', name='↑ Move up', exact=True).click()
        save(page)
        check('beat creation and reorder persist', len(saved(ident)['draft']['beats']) == original_count + 1 and saved(ident)['draft']['beats'][-2]['label'] == 'New fixture beat')
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('#vs-editor .vs-card').nth(original_count - 1).get_by_role('button', name='Remove', exact=True).click()
        save(page)
        check('beat removal persists', len(saved(ident)['draft']['beats']) == original_count)

        tab(page, 'readiness')
        page.locator('.vs-danger summary').click()
        page.locator('#vs-delete-confirm').fill('wrong phrase')
        page.locator('#vs-delete').click()
        page.wait_for_function("() => document.querySelector('#vs-status').textContent.includes('exact deletion')")
        check('deletion requires exact confirmation', len(videos()) == 1)
        page.locator('#vs-delete-confirm').fill('DELETE ' + ident)
        page.locator('#vs-delete').click()
        page.locator('#vs-workbench').wait_for(state='hidden')
        check('confirmed deletion removes the active episode', not videos())
        check('deleted record cannot be fetched', f.request(API + '/' + ident)['statusCode'] == 404)

        page.locator('#vs-research-nav').click()
        ident = create_template(page)
        page.locator('#vs-notes').fill('UNSAVED-OLD-OWNER-CANARY')
        visibility(page, True)
        check('hidden tab masks private content', page.locator('#vs-app').is_hidden())
        f.csrf = 'different-session-csrf'
        f.switch_owner('different-owner')
        visibility(page, False)
        page.locator('#vs-app').wait_for(state='visible')
        check('changed owner session clears old draft and list', page.locator('#vs-workbench').is_hidden() and page.locator('#vs-editor').inner_text() == '' and page.locator('.vs-video-item').count() == 0)
        f.auth.idp.admin_get_user.return_value['UserAttributes'] = [{'Name': 'sub', 'Value': 'owner-id'}]
        f.csrf = 'fixture-csrf'
        f.login()
        page.reload()
        page.locator('#vs-app').wait_for(state='visible')
        page.locator('#vs-library-nav').click()
        page.locator('.vs-video-item').click()
        page.locator('#vs-workbench').wait_for(state='visible')
        f.auth.idp.admin_get_user.return_value['Enabled'] = False
        page.locator('#vs-export-pack').click()
        page.wait_for_function("() => document.querySelector('#vs-app').hidden")
        check('revoked owner cannot export and private content clears', page.locator('#vs-editor').inner_text() == '' and page.locator('#vs-topic-list').inner_text() == '' and page.locator('#vs-playbook-content').inner_text() == '')
        check('private studio sends no analytics events', not any('/api/events' in url for url in traffic))
        check('lifecycle has no script errors', not errors)
        check('CSP permits only intended behavior', not security_errors)
        context.close()
        browser.close()
finally:
    server.shutdown()
    f.close()
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=2))
print(str(len(checks)) + ' Video Studio browser checks passed.')
