"""Video Studio integration using real owner auth and isolated moto storage.

All scenarios below are synthetic test fixtures. No private research or saved
production videos are fetched, seeded, or copied into the test database.
"""
import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from botocore.exceptions import ClientError

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('video_decision_fixture', REPO / 'tests/decision_room/test_backend.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
Fixture = fixture_module.Fixture
room = fixture_module.room
from auth import digest
import video_studio as studio


def script():
    return {'title': 'Synthetic screen walkthrough', 'premise': 'Demonstrate one synthetic decision.',
            'audience': 'Practitioners using a fixture tool.', 'decision': 'Choose which fixture result to inspect.',
            'stage': 'rehearsal', 'notes': 'PRIVATE FIXTURE NOTES', 'transcript': '',
            'beats': [{'id': 'explain', 'label': 'Show the result', 'seconds': 45,
                       'spoken': 'I compare two synthetic outcomes on this screen. I explain the condition that changes the decision, demonstrate the result, and save the evidence for another review.',
                       'screen': 'Open the fixture result and highlight the measured difference.',
                       'visual': 'Fixture screen only.', 'khalid': 'Explain the decision.',
                       'codex': 'Prepare a fixture comparison.', 'save': 'Save the fixture result.'}],
            'checklist': [{'id': ident, 'label': label, 'done': False} for ident, label in studio.REVIEW_CHECKS.items()],
            'sources': [{'title': 'Fixture source', 'url': 'https://example.com/source', 'note': 'Synthetic source for tests only.'}]}


CATALOG = {'checked_at': '2026-10-26', 'ranking_note': 'Synthetic fixture ranking.',
           'topics': [{'id': 'fixture', 'title': 'Fixture topic'}],
           'templates': [{'id': 'fixture-template', **script()}]}


class VideoStudioTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)
        self.catalog_patch = patch.object(studio, 'catalog', return_value=copy.deepcopy(CATALOG))
        self.catalog_patch.start()
        self.addCleanup(self.catalog_patch.stop)

    def request(self, path=studio.ROOT, method='GET', data=None, **kwargs):
        return self.f.request(path, method, data, **kwargs)

    def create(self, **changes):
        raw = {'request_id': str(uuid.uuid4()), 'title': 'Synthetic video'}
        raw.update(changes)
        result = self.request(method='POST', data=raw)
        self.assertEqual(result['statusCode'], 201, result)
        return json.loads(result['body'])['video']

    def video_path(self, video):
        return studio.ROOT + '/' + video['id']

    def update(self, video, draft):
        result = self.request(self.video_path(video), 'PATCH', {'revision': video['revision'], 'draft': draft})
        self.assertEqual(result['statusCode'], 200, result)
        return json.loads(result['body'])['video']

    def delete(self, video):
        return self.request(self.video_path(video), 'DELETE',
                            {'revision': video['revision'], 'confirm': 'DELETE ' + video['id']})

    def ready(self, video):
        draft = script()
        draft['stage'] = 'ready'
        for check in draft['checklist']:
            check['done'] = True
        return self.update(video, draft)

    def test_empty_list_and_catalog_never_seed_records(self):
        for _ in range(2):
            result = self.request()
            self.assertEqual(json.loads(result['body']), {'items': [], 'next_cursor': None})
            catalog = self.request(studio.ROOT + '/catalog')
            self.assertEqual(catalog['statusCode'], 200)
            self.assertEqual(json.loads(catalog['body'])['catalog'], CATALOG)
            self.assertIn('no-store', catalog['headers']['Cache-Control'])
        self.assertEqual(self.f.table.scan()['Items'], [])

    def test_all_routes_require_owner_auth_even_unsupported_methods(self):
        ident = str(uuid.uuid4())
        for path, method in [(studio.ROOT, 'GET'), (studio.ROOT, 'POST'), (studio.ROOT, 'PUT'),
                             (studio.ROOT + '/catalog', 'GET'), (studio.ROOT + '/' + ident, 'GET'),
                             (studio.ROOT + '/' + ident, 'PATCH'), (studio.ROOT + '/' + ident, 'DELETE')]:
            with self.subTest(path=path, method=method):
                result = self.request(path, method, {}, owner=False)
                self.assertEqual(result['statusCode'], 401)
                self.assertIn('no-store', result['headers']['Cache-Control'])
        self.assertEqual(self.f.table.scan()['Items'], [])

    def test_origin_csrf_mfa_group_session_and_token_fail_closed(self):
        self.assertEqual(self.request(headers={'X-Site-Origin': 'wrong'})['statusCode'], 403)
        for origin in ('https://other.example', ''):
            self.assertEqual(self.request(method='POST', data={}, headers={'Origin': origin})['statusCode'], 400)
        self.assertEqual(self.request(method='POST', data={}, headers={'X-Csrf-Token': 'wrong'})['statusCode'], 401)
        self.assertEqual(self.request(headers={'Cookie': '__Host-ks-enrollment=anything'})['statusCode'], 401)
        user = copy.deepcopy(self.f.auth.idp.admin_get_user.return_value)
        for key, value in [('Enabled', False), ('UserMFASettingList', [])]:
            self.f.auth.idp.admin_get_user.return_value = user | {key: value}
            self.assertEqual(self.request(studio.ROOT + '/catalog')['statusCode'], 401)
        self.f.auth.idp.admin_get_user.return_value = user
        self.f.auth.idp.admin_list_groups_for_user.return_value = {'Groups': []}
        self.assertEqual(self.request()['statusCode'], 401)
        self.f.auth.idp.admin_list_groups_for_user.return_value = {'Groups': [{'GroupName': 'owner'}]}
        for changes in ({'exp': int(time.time()) - 20}, {'client_id': 'other'}, {'scope': 'openid'}, {'token_use': 'id'}, {'iss': 'other'}):
            row = self.f.store.get('sessions', 'session#' + digest(self.f.sid))
            row['access'] = self.f.token(**changes)
            self.f.store.put('sessions', row)
            self.assertEqual(self.request()['statusCode'], 401)
        self.f.login()
        row = self.f.store.get('sessions', 'session#' + digest(self.f.sid))
        row['ttl'] = int(time.time()) - 1
        self.f.store.put('sessions', row)
        self.assertEqual(self.request()['statusCode'], 401)
        self.assertEqual(self.f.table.scan()['Items'], [])

    def test_create_blank_template_and_assessment_namespaces(self):
        blank = self.create()
        self.assertEqual(blank['draft']['stage'], 'research')
        self.assertEqual(blank['draft']['beats'], [])
        self.assertEqual({check['id'] for check in blank['draft']['checklist']}, set(studio.REVIEW_CHECKS))
        templated = self.create(title='Chosen title', template_id='fixture-template')
        self.assertEqual(templated['draft']['title'], 'Chosen title')
        self.assertEqual(templated['draft']['beats'], script()['beats'])
        self.assertNotIn('id', templated['draft'])
        case = self.f.create()
        videos = json.loads(self.request()['body'])['items']
        self.assertEqual({video['id'] for video in videos}, {blank['id'], templated['id']})
        self.assertEqual([item['id'] for item in json.loads(self.f.request()['body'])['items']], [case['id']])
        self.assertNotIn('PRIVATE FIXTURE NOTES', self.request()['body'])
        self.assertEqual(self.request(method='POST', data={'request_id': str(uuid.uuid4()), 'title': 'Unknown', 'template_id': 'unknown'})['statusCode'], 400)

    def test_idempotence_different_payload_and_concurrent_create(self):
        raw = {'request_id': str(uuid.uuid4()), 'title': 'Same request', 'template_id': 'fixture-template'}
        first = self.request(method='POST', data=raw)
        self.assertEqual(first['statusCode'], 201)
        retry = self.request(method='POST', data=raw)
        self.assertEqual(retry['statusCode'], 200)
        self.assertTrue(json.loads(retry['body'])['duplicate'])
        self.assertEqual(json.loads(first['body'])['video'], json.loads(retry['body'])['video'])
        self.assertEqual(self.request(method='POST', data=raw | {'title': 'Different'})['statusCode'], 409)
        self.assertEqual(self.f.table.scan()['Count'], 1)
        raw['request_id'] = str(uuid.uuid4())
        original = room.transact
        raced = False
        def race(actions):
            nonlocal raced
            if not raced:
                raced = True
                self.assertEqual(self.request(method='POST', data=raw)['statusCode'], 201)
            return original(actions)
        with patch.object(room, 'transact', side_effect=race):
            result = self.request(method='POST', data=raw)
        self.assertEqual(result['statusCode'], 200, result)
        self.assertEqual(self.f.table.scan()['Count'], 2)

    def test_owner_isolation_and_revision_cannot_be_spoofed(self):
        video = self.create(template_id='fixture-template')
        self.f.switch_owner('second-owner')
        self.assertEqual(json.loads(self.request()['body'])['items'], [])
        for method, raw in [('GET', None), ('PATCH', {'revision': 0, 'draft': {'title': 'Intrusion'}}),
                            ('DELETE', {'revision': 0, 'confirm': 'DELETE ' + video['id']})]:
            self.assertEqual(self.request(self.video_path(video), method, raw)['statusCode'], 404)
        self.assertEqual(self.request(q={'owner': 'owner-id'})['statusCode'], 400)
        self.assertEqual(self.request(q={'cursor': 'owner#owner-id'})['statusCode'], 400)
        second = self.create(request_id=video['id'])
        self.assertEqual(second['id'], video['id'])
        self.f.switch_owner('owner-id')
        self.assertEqual(json.loads(self.request(self.video_path(video))['body'])['video'], video)

    def test_payload_schema_limits_and_urls(self):
        video = self.create()
        bad_drafts = [{'unknown': 'x'}, {'title': ''}, {'title': 'ab'}, {'title': 'x' * 201}, {'premise': 'x' * 2001},
                      {'notes': 'x' * 3001}, {'transcript': 'x' * 9001}, {'stage': 'published'},
                      {'beats': [{}]}, {'beats': [script()['beats'][0]] * 13},
                      {'beats': [script()['beats'][0], script()['beats'][0]]},
                      {'beats': [script()['beats'][0] | {'seconds': True}]},
                      {'beats': [script()['beats'][0] | {'seconds': 9}]},
                      {'beats': [script()['beats'][0] | {'seconds': 181}]},
                      {'beats': [script()['beats'][0] | {'spoken': 'x' * 1801}]},
                      {'checklist': [{'id': 'evidence', 'label': 'Check', 'done': 1}]},
                      {'checklist': script()['checklist'] * 4}, {'sources': script()['sources'] * 9}]
        bad_drafts += [{'sources': [script()['sources'][0] | {'url': url}]} for url in
                       ('http://example.com', 'javascript:alert(1)', 'https://', 'https://user:pass@example.com',
                        'https://example.com/a b', 'https://example.com:wrong', 'https://example.com/' + 'x' * 600)]
        for draft in bad_drafts:
            with self.subTest(draft=draft):
                result = self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': draft})
                self.assertEqual(result['statusCode'], 400, result)
        self.assertEqual(self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': {'notes': 'x' * 25000}})['statusCode'], 400)
        self.assertEqual(self.request(self.video_path(video), 'PATCH', {'revision': True, 'draft': {}})['statusCode'], 400)
        self.assertEqual(self.request(method='POST', data={'title': 'Missing UUID'})['statusCode'], 400)
        self.assertEqual(json.loads(self.request(self.video_path(video))['body'])['video']['revision'], 0)

    def test_readiness_gates_required_checks_and_meaningful_beats(self):
        video = self.create()
        for stage in ('ready', 'recorded'):
            self.assertEqual(self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': {'stage': stage}})['statusCode'], 400)
        draft = script()
        draft['stage'] = 'ready'
        for check in draft['checklist']:
            check['done'] = True
        for changes in ({'checklist': []}, {'checklist': draft['checklist'][:-1]}, {'beats': []},
                        {'beats': [draft['beats'][0] | {'spoken': 'Too short'}]},
                        {'beats': [draft['beats'][0] | {'screen': ''}]},
                        {'beats': [draft['beats'][0] | {'spoken': 'A short sentence for this beat.'}]}):
            result = self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': draft | changes})
            self.assertEqual(result['statusCode'], 400, result)
        ready = self.update(video, draft)
        recorded = self.update(ready, {'stage': 'recorded'})
        self.assertEqual(recorded['draft']['stage'], 'recorded')

    def test_edits_after_review_reset_checks_and_demote(self):
        video = self.ready(self.create())
        video = self.update(video, {'notes': 'New review context', 'stage': 'ready'})
        self.assertEqual(video['draft']['stage'], 'rehearsal')
        self.assertTrue(all(check['done'] is False for check in video['draft']['checklist']))
        video = self.ready(video)
        video = self.update(video, {'stage': 'recorded'})
        result = self.request(self.video_path(video), 'PATCH', {'revision': video['revision'], 'draft': {'title': 'Changed script title'}})
        self.assertTrue(json.loads(result['body'])['review_required'])
        self.assertEqual(json.loads(result['body'])['video']['draft']['stage'], 'rehearsal')
        video = self.ready(json.loads(result['body'])['video'])
        reopened = self.update(video, {'stage': 'script'})
        self.assertEqual(reopened['draft']['stage'], 'script')
        self.assertTrue(all(check['done'] is False for check in reopened['draft']['checklist']))
        self.assertEqual(self.request(self.video_path(reopened), 'PATCH',
            {'revision': reopened['revision'], 'draft': {'stage': 'ready'}})['statusCode'], 400)

    def test_stale_and_concurrent_revisions_keep_saved_draft(self):
        video = self.create()
        saved = self.update(video, {'notes': 'First edit'})
        self.assertEqual(self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': {'notes': 'Lost edit'}})['statusCode'], 409)
        original = room.transact
        def race(actions):
            self.f.table.update_item(Key=studio.video_key('owner-id', video['id']),
                UpdateExpression='SET revision=:n', ExpressionAttributeValues={':n': 99})
            return original(actions)
        with patch.object(room, 'transact', side_effect=race):
            result = self.request(self.video_path(video), 'PATCH', {'revision': saved['revision'], 'draft': {'notes': 'Racing edit'}})
        self.assertEqual(result['statusCode'], 409)
        self.assertEqual(json.loads(self.request(self.video_path(video))['body'])['video']['draft']['notes'], 'First edit')

    def test_delete_erases_content_blocks_retry_and_wins_against_edit(self):
        ident = str(uuid.uuid4())
        video = self.create(request_id=ident, title='Private deletion fixture', template_id='fixture-template')
        self.assertEqual(self.request(self.video_path(video), 'DELETE', {'revision': 0, 'confirm': 'wrong'})['statusCode'], 400)
        original = room.transact
        intercepted = False
        def delete_first(actions):
            nonlocal intercepted
            if not intercepted:
                intercepted = True
                self.assertEqual(self.delete(video)['statusCode'], 200)
            return original(actions)
        with patch.object(room, 'transact', side_effect=delete_first):
            result = self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': {'notes': 'Must never resurrect this'}})
        self.assertEqual(result['statusCode'], 409)
        self.assertEqual(self.request(self.video_path(video))['statusCode'], 404)
        self.assertEqual(json.loads(self.request()['body'])['items'], [])
        self.assertEqual(self.request(method='POST', data={'request_id': ident, 'title': 'Private deletion fixture', 'template_id': 'fixture-template'})['statusCode'], 409)
        stored = self.f.table.scan()['Items']
        self.assertEqual(stored[0]['kind'], 'video-deleted')
        self.assertNotIn('draft', stored[0])
        self.assertNotIn('Private deletion fixture', json.dumps(stored, default=str))
        self.assertNotIn('PRIVATE FIXTURE NOTES', json.dumps(stored, default=str))

    def test_retention_is_fixed_and_expired_rows_are_hidden_and_swept(self):
        video = self.create()
        self.assertEqual(video['expires_at'] - video['created_at'], 365 * 86400)
        edited = self.update(video, script())
        self.assertEqual(edited['expires_at'], video['expires_at'])
        self.assertEqual(edited['retention_days'], 365)
        row = self.f.table.get_item(Key=studio.video_key('owner-id', video['id']))['Item']
        self.assertEqual(row['ttl'], video['expires_at'])
        with patch.object(studio.time, 'time', return_value=video['expires_at'] + 1):
            self.assertIsNone(studio.get_video('owner-id', video['id']))
            self.assertEqual(room.maintain()['removed'], 1)
        self.assertTrue(all(row['pk'] == 'system' for row in self.f.table.scan()['Items']))
        second = self.create()
        self.f.table.update_item(Key=studio.video_key('owner-id', second['id']),
            UpdateExpression='SET #ttl=:n', ExpressionAttributeNames={'#ttl': 'ttl'},
            ExpressionAttributeValues={':n': int(time.time()) - 1})
        self.assertEqual(self.request(self.video_path(second))['statusCode'], 404)
        self.assertEqual(json.loads(self.request()['body'])['items'], [])

    def test_expiry_between_read_and_write_cannot_save(self):
        video = self.create()
        original = room.transact
        def expire_first(actions):
            self.f.table.update_item(Key=studio.video_key('owner-id', video['id']),
                UpdateExpression='SET expires_at=:n', ExpressionAttributeValues={':n': int(time.time()) - 1})
            return original(actions)
        with patch.object(room, 'transact', side_effect=expire_first):
            result = self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': {'notes': 'Expired edit'}})
        self.assertEqual(result['statusCode'], 409)

    def test_pagination_cursor_stays_owner_scoped(self):
        expected = {self.create()['id'] for _ in range(3)}
        original = self.f.table.query
        def small_pages(**kwargs):
            kwargs['Limit'] = 1
            return original(**kwargs)
        found, cursor = set(), None
        with patch.object(self.f.table, 'query', side_effect=small_pages):
            for _ in range(4):
                result = self.request(q={'cursor': cursor} if cursor else None)
                data = json.loads(result['body'])
                found.update(item['id'] for item in data['items'])
                cursor = data['next_cursor']
                if not cursor:
                    break
        self.assertEqual(found, expected)
        self.assertIsNone(cursor)

    def test_storage_failures_never_log_input_or_claim_saved(self):
        video = self.create()
        output = io.StringIO()
        failure = ClientError({'Error': {'Code': 'InternalServerError', 'Message': 'SECRET TEST CONTENT'}}, 'TransactWriteItems')
        with contextlib.redirect_stdout(output), patch.object(room.TABLE.meta.client, 'transact_write_items', side_effect=failure):
            result = self.request(self.video_path(video), 'PATCH', {'revision': 0, 'draft': {'notes': 'PRIVATE INPUT'}})
        self.assertEqual(result['statusCode'], 503)
        self.assertNotIn('SECRET', output.getvalue() + result['body'])
        self.assertNotIn('PRIVATE INPUT', output.getvalue() + result['body'])
        self.assertIn('not been confirmed', result['body'])
        self.assertEqual(json.loads(self.request(self.video_path(video))['body'])['video']['revision'], 0)

    def test_actual_catalog_templates_fit_request_bounds_and_have_recordable_beats(self):
        self.catalog_patch.stop()
        actual = studio.catalog()
        self.assertRegex(actual['checked_at'], r'^\d{4}-\d{2}-\d{2}$')
        self.assertTrue(actual['ranking_note'])
        self.assertGreaterEqual(len(actual['topics']), 1)
        self.assertGreaterEqual(len(actual['templates']), 3)
        self.assertEqual(len({template['id'] for template in actual['templates']}), len(actual['templates']))
        playbook = actual['playbook']
        self.assertTrue(playbook['promise'])
        for key in ('principles', 'discovery', 'season', 'filming', 'roles', 'continuity'):
            self.assertTrue(playbook[key])
        references = {episode['template_id'] for episode in playbook['season'] if episode.get('template_id')}
        self.assertEqual(references, {template['id'] for template in actual['templates']})
        result = self.request(studio.ROOT + '/catalog')
        self.assertEqual(result['statusCode'], 200, result)
        self.assertEqual(json.loads(result['body'])['catalog'], actual)
        self.assertEqual(self.f.table.scan()['Count'], 0)
        for template in actual['templates']:
            with self.subTest(template=template['id']):
                draft = studio.initial_draft(template['title'], template['id'])
                self.assertEqual(draft['stage'], 'script')
                self.assertEqual(draft['transcript'], '')
                self.assertGreaterEqual(len(draft['sources']), 1)
                self.assertTrue(all(not check['done'] for check in draft['checklist']))
                self.assertGreaterEqual(sum(beat['seconds'] for beat in draft['beats']), 240)
                self.assertLessEqual(sum(beat['seconds'] for beat in draft['beats']), 360)
                for beat in draft['beats']:
                    for field in ('label', 'spoken', 'screen', 'visual', 'khalid', 'codex', 'save'):
                        self.assertTrue(beat[field].strip(), (template['id'], beat['id'], field))
                    # Authored plans leave time to demonstrate the screen. This
                    # guards obviously impossible narration, not delivery style.
                    words_per_minute = len(beat['spoken'].split()) * 60 / beat['seconds']
                    self.assertLessEqual(words_per_minute, 180, (template['id'], beat['id']))
                wire = json.dumps({'revision': 0, 'draft': draft}, ensure_ascii=False).encode()
                self.assertLessEqual(len(wire), 24000)
                with self.assertRaises(fixture_module.room.Invalid):
                    studio.review_ready(draft)
                for check in draft['checklist']:
                    check['done'] = True
                studio.review_ready(draft)

    def test_actual_templates_instantiate_save_review_and_reload_through_authorized_api(self):
        self.catalog_patch.stop()
        for template in studio.catalog()['templates']:
            with self.subTest(template=template['id']):
                video = self.create(title=template['title'], template_id=template['id'])
                self.assertEqual(video['draft']['beats'], template['beats'])
                edited = copy.deepcopy(video['draft'])
                edited['notes'] += '\nAPI-INTEGRATION-PRIVATE-CANARY'
                edited['stage'] = 'rehearsal'
                saved = self.update(video, edited)
                self.assertEqual(saved['revision'], 1)
                self.assertEqual(saved['draft'], edited)
                loaded = self.request(self.video_path(saved))
                self.assertEqual(json.loads(loaded['body'])['video'], saved)
                for check in edited['checklist']:
                    check['done'] = True
                edited['stage'] = 'ready'
                ready = self.update(saved, edited)
                self.assertEqual(ready['draft']['stage'], 'ready')
                self.assertEqual(ready['revision'], 2)
                self.assertEqual(ready['expires_at'], video['expires_at'])
                self.assertEqual(self.delete(ready)['statusCode'], 200)
        self.assertEqual(json.loads(self.request()['body'])['items'], [])

    def test_isolated_static_build_excludes_private_records_catalog_search_and_sitemap(self):
        import build
        import admin_build
        from video_catalog import CATALOG as actual

        private = self.update(self.create(title='PRIVATE-VIDEO-BUILD-CANARY-37a4'),
                              {'notes': 'PRIVATE-VIDEO-NOTES-CANARY-9c63'})
        forbidden = [private['id'], private['draft']['title'], private['draft']['notes']]
        forbidden += [template['id'] for template in actual['templates']]
        forbidden += [template['beats'][0]['spoken'] for template in actual['templates']]
        forbidden += [topic['why'] for topic in actual['topics']]
        forbidden += [actual['playbook']['promise']]
        original_write = Path.write_text
        with tempfile.TemporaryDirectory(prefix='video-studio-build-') as tmp:
            output = Path(tmp) / 'dist'
            # The build normally refreshes the public API page allowlist in
            # source. Capture that generated file inside this isolated test.
            def isolated_write(path, data, *args, **kwargs):
                target = Path(tmp) / 'public-pages.json' if path == REPO / 'services/site-admin/pages.json' else path
                return original_write(target, data, *args, **kwargs)
            with patch.object(build, 'DIST', output), patch.object(Path, 'write_text', isolated_write), contextlib.redirect_stdout(io.StringIO()):
                build.build()
            shell = (output / 'admin/video-studio/index.html').read_text()
            self.assertIn('noindex, nofollow', shell)
            self.assertIn('Content-Security-Policy', shell)
            self.assertIn('name="referrer" content="no-referrer"', shell)
            search = json.loads((output / 'search.json').read_text())
            self.assertFalse(any(item['u'].startswith('/admin/') for item in search))
            sitemap = (output / 'sitemap.xml').read_text()
            self.assertNotIn('/admin/', sitemap)
            public_pages = json.loads((Path(tmp) / 'public-pages.json').read_text())
            self.assertNotIn('/admin/video-studio/', public_pages)
            self.assertNotIn('/admin/video-studio/', admin_build.public_pages(output))
            needles = [value.encode() for value in forbidden]
            for path in output.rglob('*'):
                if not path.is_file():
                    continue
                self.assertNotIn(path.name, {'video_catalog.py', 'video_research.json', 'video_templates.json', 'video_playbook.json', 'video_studio.py'})
                if path.suffix in {'.html', '.json', '.js', '.css', '.txt', '.xml'}:
                    content = path.read_bytes()
                    self.assertFalse(any(needle in content for needle in needles), str(path.relative_to(output)))
        self.assertEqual(json.loads(self.request(self.video_path(private))['body'])['video'], private)


if __name__ == '__main__':
    unittest.main()
