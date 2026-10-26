"""Rehearse the two authored on-site screen sequences; no cloud/model calls."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8878'
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else '/tmp/video-demo-check')
OUT.mkdir(parents=True, exist_ok=True)
checks = []


def check(label, condition):
    checks.append({'check': label, 'ok': bool(condition)})
    assert condition, label


def advance(page):
    for _ in range(24):
        if page.locator('#es-next').is_disabled():
            return
        page.locator('#es-next').click()
    raise AssertionError('The filmed sequence did not terminate')


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for width in (1380, 390):
        page = browser.new_page(viewport={'width': width, 'height': 960}, reduced_motion='reduce')
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/architect/agent-studio/#design')
        page.locator('#es-example').select_option(label='Internal knowledge assistant')
        page.locator('#es-pattern').select_option(label='Known sequence or retrieval path')
        page.locator('#es-authority').select_option(label='Read and draft only')
        page.locator('#es-condition').select_option(label='Source access denied')
        page.get_by_role('button', name='Reset run', exact=True).click()
        advance(page)
        check(f'{width}: source denial stops without write', page.locator('#es-step-event').inner_text() == 'retrieval.denied' and 'write.receipt_received' not in page.locator('#es-trace').inner_text())
        page.locator('.es-workspace').screenshot(path=str(OUT / f'source-denied-{width}.png'))
        page.get_by_label('Accountable owner or role', exact=True).fill('Teaching example: IT service owner')
        page.get_by_label('First pilot outcome', exact=True).fill('Compare approved-source answers with current search on the same synthetic questions; measure resolution and correct refusal.')
        with page.expect_download() as pending:
            page.get_by_role('button', name='Download the design record', exact=True).click()
        record = Path(pending.value.path()).read_text()
        check(f'{width}: reusable record retains scope and limits', 'Teaching example: IT service owner' in record and 'UNRESOLVED BEFORE PRODUCTION' in record)
        page.locator('#es-authority').select_option(label='Write after explicit review')
        page.locator('#es-risk').select_option(label='Money, access rights or material harm')
        for condition, outcome in [('Evidence and services available', 'outcome.verified'), ('Payload changed after approval', 'payload.changed')]:
            page.locator('#es-condition').select_option(label=condition)
            page.get_by_role('button', name='Reset run', exact=True).click()
            advance(page)
            check(f'{width}: {condition} pauses for explicit approval', page.get_by_role('button', name='Approve proposal', exact=True).is_visible())
            page.get_by_role('button', name='Approve proposal', exact=True).click()
            advance(page)
            check(f'{width}: {condition} reaches expected result', page.locator('#es-step-event').inner_text() == outcome)
            if condition.startswith('Payload'):
                check(f'{width}: changed request never writes', 'write.receipt_received' not in page.locator('#es-trace').inner_text())
                page.locator('.es-workspace').screenshot(path=str(OUT / f'changed-approval-{width}.png'))
        check(f'{width}: screen fits and has no errors', page.evaluate('document.documentElement.scrollWidth<=innerWidth') and not errors)
        page.close()
    browser.close()
(OUT / 'checks.json').write_text(json.dumps(checks, indent=2))
print(f'{len(checks)} shooting-sequence checks passed. Foundry rehearsal is not included.')
