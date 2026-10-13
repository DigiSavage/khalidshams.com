"""Real browser + real handlers, exclusively against isolated test AWS resources.

No fixture endpoint or data in this file is packaged into the production build.
"""
import json
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from test_backend import Fixture, room
import app

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/decision-room-ui')
OUT.mkdir(parents=True, exist_ok=True)
BASE = 'http://localhost:8775'
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


server = HTTPServer(('localhost', 8775), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE + '/admin/decision-room/')
        page.wait_for_function("() => document.querySelector('#drm-status').textContent.includes('expired')")
        check('signed-out shell hides all case controls', page.locator('#drm-app').is_hidden())
        check('signed-out private method denied', context.request.get(BASE + room.ROOT + '/method').status == 401)
        context.close()
        for width, theme in [(1380, 'light'), (1380, 'dark'), (390, 'light'), (390, 'dark'), (320, 'light')]:
            context = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme=theme)
            context.request.get(BASE + '/__fixture__/login')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE + '/admin/decision-room/')
            page.locator('#drm-app').wait_for(state='visible')
            check(f'empty real starting state {width} {theme}', 'No saved cases yet' in page.locator('#drm-case-list').inner_text())
            check(f'no horizontal overflow {width} {theme}', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(OUT / f'empty-{width}-{theme}.png'), full_page=True)
            page.locator('#drm-new').press('Enter')
            check(f'new case has no prefilled client data {width} {theme}', page.locator('#drm-create-form [name=title]').input_value() == '' and page.locator('#drm-create-form [name=decision]').input_value() == '')
            check(f'creation dialog fits {width} {theme}', page.locator('#drm-create-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'))
            page.locator('#drm-create-close').click()
            check(f'no script errors {width} {theme}', not errors)
            context.close()

        context = browser.new_context(viewport={'width': 1380, 'height': 1000}, accept_downloads=True)
        context.request.get(BASE + '/__fixture__/login')
        page = context.new_page()
        errors, security_errors, traffic = [], [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda msg: security_errors.append(msg.text) if 'violates' in msg.text.lower() or 'content security policy' in msg.text.lower() else None)
        page.on('request', lambda req: traffic.append(req.url))
        page.goto(BASE + '/admin/decision-room/')
        page.locator('#drm-app').wait_for(state='visible')
        page.locator('#drm-new').click()
        form = page.locator('#drm-create-form')
        form.locator('[name=title]').fill('Isolated browser test')
        form.locator('[name=decision]').fill('Compare two approaches using isolated test evidence.')
        form.locator('[name=domain]').select_option('saas')
        page.locator('#drm-retention-ack').check()
        form.get_by_role('button', name='Create private case', exact=True).click()
        page.locator('#drm-case').wait_for(state='visible')
        page.wait_for_function("() => document.querySelector('#drm-status').textContent.includes('created')")
        current = json.loads(f.request()['body'])['items'][0]
        ident = current['id']
        check('creation persists once via real handler', len(json.loads(f.request()['body'])['items']) == 1)
        check('method visible only after owner authorization', 'Synthetic fixture question?' in page.locator('#drm-questions').inner_text())

        def stage(label): page.locator('#drm-stages').get_by_role('button', name=label, exact=True).click()
        def fill(label, value, within=None): (within or page.locator('#drm-editor')).get_by_label(label, exact=True).fill(value)
        stage('02 · Evidence')
        page.get_by_role('button', name='Add evidence', exact=True).click()
        fill('Evidence label', '<img src=x onerror=alert(1)> Evidence')
        fill('What this supports or shows', 'A measured fixture confirms the test-only boundary.')
        fill('Source reference', 'Isolated test runner')
        fill('Scope and environment', 'Local test environment only')
        page.locator('#drm-editor').get_by_label('Evidence type', exact=True).select_option('tested')
        fill('Observation date', '2026-10-13')
        stage('03 · Findings')
        page.get_by_role('button', name='Add finding', exact=True).click()
        fill('Finding title', 'A traceable conclusion')
        fill('Finding and consequence', 'The local fixture supports comparison under a limited scope.')
        page.locator('.drm-evidence-links input').check()
        stage('04 · Options')
        for title in ('Bounded change', 'Keep current approach'):
            page.get_by_role('button', name='Add option', exact=True).click()
            card = page.locator('#drm-editor .drm-card').last
            fill('Option title', title, card)
            fill('Approach and trade-offs', 'Evaluate this option against the same recorded evidence.', card)
            fill('Cost and effort assumptions', 'Unknown until the work is scoped.', card)
        stage('05 · Decision')
        page.locator('#drm-editor').get_by_label('Position', exact=True).select_option('conditional')
        page.locator('#drm-editor').get_by_label('Recommended option', exact=True).select_option(label='Bounded change')
        fill('Recommendation and its conditions', 'Proceed only after the local acceptance checks are reviewed.')
        fill('Strongest counterargument and what could change the decision', 'The current fixture may not represent later requirements.')
        stage('06 · Handoff')
        page.get_by_role('button', name='Add action', exact=True).click()
        fill('Next action', 'Validate the comparison before changing any system.')
        fill('Accountable owner', 'Test-only reviewer')
        fill('Acceptance check', 'Both options are evaluated against the same conditions.')
        stage('07 · Internal')
        fill('Internal working notes', 'INTERNAL-EXPORT-CANARY-9381')
        page.locator('#drm-questions summary').click()
        page.locator('#drm-questions').get_by_label('Internal answer', exact=True).fill('ANSWER-EXPORT-CANARY-8392')
        page.locator('#drm-save').click()
        page.wait_for_function("() => document.querySelector('#drm-status').textContent.includes('Changes saved')")
        check('save persists real field edits', json.loads(f.request(room.ROOT + '/' + ident)['body'])['case']['internal_notes'] == 'INTERNAL-EXPORT-CANARY-9381')
        check('no confidential URL or persistent browser storage', ident not in page.url and page.evaluate("!Object.values(localStorage).join('').includes('CANARY') && !Object.values(sessionStorage).join('').includes('CANARY')"))
        stage('08 · Review')
        check('review requires deliberate acknowledgement', page.get_by_role('button', name='Create reviewed snapshot', exact=True).is_disabled())
        page.locator('#drm-review-ack').check()
        page.evaluate('() => window.scrollTo(0, 0)')
        page.screenshot(path=str(OUT / 'review-desktop.png'), full_page=True)
        page.get_by_role('button', name='Create reviewed snapshot', exact=True).click()
        page.locator('#drm-report-dialog').wait_for(state='visible')
        check('client preview excludes internal content', 'CANARY' not in page.locator('#drm-report-preview').inner_text())
        check('evidence markup stays inert in preview', page.locator('#drm-report-preview img,#drm-report-preview script').count() == 0)
        page.screenshot(path=str(OUT / 'reviewed-preview-desktop.png'))
        with page.expect_download() as download:
            page.locator('#drm-download').click()
        exported = OUT / 'isolated-reviewed-export.html'
        download.value.save_as(exported)
        html = exported.read_text()
        check('export excludes private notes and answers', 'CANARY' not in html)
        check('export encodes submitted markup', '&lt;img' in html and '<img src=x' not in html)
        check('download obtains an authorized export', any('/export?revision=' in url for url in traffic))
        page.locator('#drm-report-close').click()
        page.reload()
        page.locator('#drm-app').wait_for(state='visible')
        page.locator('.drm-case-item').click()
        page.locator('#drm-case').wait_for(state='visible')
        stage('07 · Internal')
        check('saved record survives reload', page.locator('#drm-editor').get_by_label('Internal working notes', exact=True).input_value() == 'INTERNAL-EXPORT-CANARY-9381')
        fill('Internal working notes', 'Unsaved conflict copy')
        latest = json.loads(f.request(room.ROOT + '/' + ident)['body'])['case']
        f.request(room.ROOT + '/' + ident, 'PATCH', {'revision': latest['revision'], 'draft': {'context': 'Concurrent tab update, local fixture only.'}})
        page.locator('#drm-save').click()
        page.locator('#drm-conflict').wait_for(state='visible')
        check('conflict preserves unsaved edits', page.locator('#drm-editor').get_by_label('Internal working notes', exact=True).input_value() == 'Unsaved conflict copy')
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('#drm-reload').click()
        page.wait_for_function("() => document.querySelector('#drm-conflict').hidden")
        for width in (390, 320):
            page.set_viewport_size({'width': width, 'height': 900})
            for label in ('01 · Mandate','02 · Evidence','03 · Findings','04 · Options','05 · Decision','06 · Handoff','07 · Internal','08 · Review'):
                stage(label)
                check(f'populated stage fits {width} {label}', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                if width == 390 and label in ('02 · Evidence', '08 · Review'):
                    page.evaluate('() => window.scrollTo(0, 0)')
                    page.screenshot(path=str(OUT / ('populated-390-' + ('evidence' if label.startswith('02') else 'review') + '.png')), full_page=True)
        stage('08 · Review')
        page.get_by_role('button', name='Preview snapshot', exact=True).click()
        page.locator('#drm-report-dialog').wait_for(state='visible')
        f.auth.idp.admin_get_user.return_value['Enabled'] = False
        page.locator('#drm-download').click()
        page.wait_for_function("() => document.querySelector('#drm-app').hidden")
        check('revoked owner cannot download a cached preview', not page.locator('#drm-report-dialog').is_visible() and page.locator('#drm-report-preview').inner_text() == '')
        check('revocation clears private editors and guidance', page.locator('#drm-editor').inner_text() == '' and page.locator('#drm-questions').inner_text() == '')
        check('no analytics events from private page', not any('/api/events' in url for url in traffic))
        check('no script errors in case lifecycle', not errors)
        check('page CSP permits only intended application behavior', not security_errors)
        context.close()
        browser.close()
finally:
    server.shutdown()
    f.close()
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=2))
print(str(len(checks)) + ' Decision Room browser checks passed.')
