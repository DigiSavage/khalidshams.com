"""Decision Room integration with moto storage and real signed session JWTs.

Fixtures exist only in tests. Every AWS call is isolated; no live evidence or
private methodology is imported into this module or the public repository.
"""
import contextlib
import copy
import io
import json
import os
import sys
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/admin'))
from test_service import Fixture as AdminFixture
from auth import Auth, digest
import decision_room as room


METHOD = {'schema_version': 1, 'version': 'fixture-v1', 'title': 'Test methodology',
          'reviewed_at': '2026-10-13', 'sections': [{'id': 'base', 'title': 'Test section',
          'questions': [{'id': 'test-question', 'prompt': 'Synthetic fixture question?',
                         'why': 'Tests only.', 'evidence_to_seek': 'Synthetic evidence.'}]}]}


class Fixture(AdminFixture):
    def __init__(self):
        super().__init__()
        os.environ.update(ASSESSMENTS_TABLE='fixture-assessments', METHOD_BUCKET='fixture-methodology',
                          METHOD_KEY='methodology/decision-room.json', RATE_SECRET='fixture-origin')
        db = boto3.resource('dynamodb')
        self.table = db.create_table(TableName='fixture-assessments',
            KeySchema=[{'AttributeName': 'pk', 'KeyType': 'HASH'}, {'AttributeName': 'sk', 'KeyType': 'RANGE'}],
            AttributeDefinitions=[{'AttributeName': 'pk', 'AttributeType': 'S'}, {'AttributeName': 'sk', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST')
        self.s3 = boto3.client('s3')
        self.s3.create_bucket(Bucket=os.environ['METHOD_BUCKET'])
        self.s3.put_bucket_versioning(Bucket=os.environ['METHOD_BUCKET'], VersioningConfiguration={'Status': 'Enabled'})
        self.method_version_id = self.put_method(METHOD)
        os.environ['METHOD_VERSION_ID'] = self.method_version_id
        room.TABLE = self.table
        room.AUTH = Auth(room.SessionReader(db))
        room.AUTH.jwks = self.auth.jwks
        room.AUTH.idp = self.auth.idp
        room.S3 = self.s3
        room.SALT = 'fixture-origin-only'

    def put_method(self, method):
        return self.s3.put_object(Bucket=os.environ['METHOD_BUCKET'], Key=os.environ['METHOD_KEY'],
                                  Body=json.dumps(method).encode())['VersionId']

    def request(self, path=room.ROOT, method='GET', data=None, owner=True, headers=None, q=None):
        h = {'X-Site-Origin': room.SALT, 'Origin': os.environ['PUBLIC_ORIGIN']}
        if owner:
            h.update(Cookie='__Host-ks-session=' + self.sid, **{'X-Csrf-Token': self.csrf})
        h.update(headers or {})
        return room.handler({'path': path, 'httpMethod': method, 'headers': h,
                             'body': json.dumps(data) if data is not None else '', 'queryStringParameters': q})

    def create(self, **changes):
        payload = {'title': 'Fixture decision', 'client': 'Synthetic company', 'decision': 'Compare two synthetic tenant placement options.',
                   'domain': 'saas', 'retention_days': 180, 'request_id': str(uuid.uuid4())}
        payload.update(changes)
        result = self.request(method='POST', data=payload)
        if result['statusCode'] != 201:
            raise AssertionError(result)
        return json.loads(result['body'])['case']

    def switch_owner(self, owner):
        self.auth.idp.admin_get_user.return_value['UserAttributes'] = [{'Name': 'sub', 'Value': owner}]
        self.store.put('sessions', {'pk': 'session#' + digest(self.sid), 'sk': '0',
            'access': self.token(sub=owner), 'csrf': self.csrf, 'sub': owner, 'ttl': int(time.time()) + 800})

    def close(self):
        room.AUTH = room.TABLE = room.S3 = room.SALT = None
        super().close()


def complete_draft():
    return {'context': 'Synthetic baseline collected for this test.', 'boundary': 'One test tenant pool only.',
            'constraints': 'No production changes in this assessment.',
            'evidence': [{'id': 'e1', 'label': 'Synthetic trace', 'detail': 'A fixture trace shows uneven demand.',
                          'source': 'Synthetic input, not a real client.', 'scope': 'Fixture pool', 'observed_at': '2026-10-13', 'kind': 'tested'}],
            'findings': [{'id': 'f1', 'title': 'Uneven demand', 'detail': 'One fixture tenant dominates the synthetic pool.',
                          'evidence_ids': ['e1'], 'severity': 'risk', 'resolved': False, 'contradiction': 'Synthetic trace may omit another peak.'}],
            'options': [{'id': 'o1', 'title': 'Isolate', 'detail': 'Test isolated placement in the fixture system.', 'cost_assumptions': 'Measure before committing.'},
                        {'id': 'o2', 'title': 'Resize', 'detail': 'Compare a larger pool against the same trace.'}],
            'recommendation': {'position': 'conditional', 'option_id': 'o1', 'detail': 'Test isolation only after confirming the synthetic baseline.'},
            'counterargument': 'A missing peak could make shared capacity the better choice.',
            'actions': [{'id': 'a1', 'detail': 'Run the isolated placement comparison.', 'owner': 'Fixture platform owner',
                         'acceptance': 'Compare the same trace and reject a worse result.'}],
            'answers': {'test-question': 'PRIVATE ANSWER FIXTURE'}, 'internal_notes': 'PRIVATE WORKING NOTE FIXTURE'}


class DecisionRoomTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)

    def case_path(self, case):
        return room.ROOT + '/' + case['id']

    def patch(self, case, draft=None):
        result = self.f.request(self.case_path(case), 'PATCH', {'revision': case['revision'], 'draft': draft or complete_draft()})
        self.assertEqual(result['statusCode'], 200, result)
        return json.loads(result['body'])['case']

    def review(self, case):
        result = self.f.request(self.case_path(case) + '/review', 'POST', {'revision': case['revision']})
        self.assertEqual(result['statusCode'], 201, result)
        return json.loads(result['body'])

    def test_empty_list_has_no_seed_records(self):
        result = self.f.request()
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(json.loads(result['body'])['items'], [])
        self.assertEqual(self.f.table.scan()['Items'], [])

    def test_every_route_requires_live_owner_session(self):
        ident = str(uuid.uuid4())
        for path, method in [(room.ROOT, 'GET'), (room.ROOT, 'POST'), (room.ROOT + '/method', 'GET'),
                             (room.ROOT, 'PUT'),
                             (room.ROOT + '/' + ident, 'GET'), (room.ROOT + '/' + ident, 'PATCH'),
                             (room.ROOT + '/' + ident, 'DELETE'), (room.ROOT + '/' + ident + '/review', 'POST'),
                             (room.ROOT + '/' + ident + '/export', 'GET')]:
            with self.subTest(path=path, method=method):
                result = self.f.request(path, method, {}, owner=False)
                self.assertEqual(result['statusCode'], 401)
                self.assertIn('no-store', result['headers']['Cache-Control'])
        self.auth_check = self.f.auth.idp.admin_get_user
        self.auth_check.return_value['Enabled'] = False
        self.assertEqual(self.f.request()['statusCode'], 401)

    def test_origin_csrf_enrollment_and_token_fail_closed(self):
        self.assertEqual(self.f.request(headers={'X-Site-Origin': 'wrong'})['statusCode'], 403)
        for headers in ({'Origin': 'https://other.example'}, {'Origin': ''}):
            self.assertEqual(self.f.request(method='POST', data={}, headers=headers)['statusCode'], 400)
        self.assertEqual(self.f.request(method='POST', data={}, headers={'X-Csrf-Token': 'wrong'})['statusCode'], 401)
        self.assertEqual(self.f.request(headers={'Cookie': '__Host-ks-enrollment=anything'})['statusCode'], 401)
        for changes in ({'exp': int(time.time()) - 20}, {'client_id': 'other'}, {'scope': 'openid'}, {'token_use': 'id'}, {'iss': 'other'}):
            row = self.f.store.get('sessions', 'session#' + digest(self.f.sid))
            row['access'] = self.f.token(**changes)
            self.f.store.put('sessions', row)
            self.assertEqual(self.f.request()['statusCode'], 401)
        self.f.login()
        self.f.auth.idp.admin_list_groups_for_user.return_value = {'Groups': []}
        self.assertEqual(self.f.request()['statusCode'], 401)

    def test_session_reader_cannot_write_and_hides_expired_rows(self):
        reader = room.AUTH.store
        self.assertFalse(hasattr(reader, 'put'))
        row = self.f.store.get('sessions', 'session#' + digest(self.f.sid))
        row['ttl'] = int(time.time()) - 1
        self.f.store.put('sessions', row)
        self.assertEqual(self.f.request()['statusCode'], 401)

    def test_create_retry_and_delete_do_not_resurrect_content(self):
        request_id = str(uuid.uuid4())
        raw = {'title': 'Retry fixture', 'decision': 'A sufficiently detailed fixture decision.', 'request_id': request_id}
        first = self.f.request(method='POST', data=raw)
        self.assertEqual(first['statusCode'], 201, first)
        case = json.loads(first['body'])['case']
        retry = self.f.request(method='POST', data=raw)
        self.assertEqual(retry['statusCode'], 200)
        self.assertEqual(json.loads(retry['body'])['case']['id'], case['id'])
        self.assertEqual(self.f.request(method='POST', data=raw | {'title': 'Changed title'})['statusCode'], 409)
        deleted = self.f.request(self.case_path(case), 'DELETE', {'revision': 0, 'confirm': 'DELETE ' + case['id']})
        self.assertEqual(deleted['statusCode'], 200)
        self.assertEqual(self.f.request(method='POST', data=raw)['statusCode'], 409)
        self.assertEqual(json.loads(self.f.request()['body'])['items'], [])
        tombstone = self.f.table.get_item(Key=room.case_key('owner-id', case['id']))['Item']
        self.assertNotIn('draft', tombstone)
        self.assertNotIn('title', tombstone)

    def test_method_is_private_deployment_pinned_and_case_pinned(self):
        case = self.f.create()
        v2 = copy.deepcopy(METHOD)
        v2['version'] = 'fixture-v2'
        v2['sections'][0]['questions'][0]['prompt'] = 'Changed test question?'
        new_version = self.f.put_method(v2)
        current = json.loads(self.f.request(room.ROOT + '/method')['body'])['method']
        self.assertEqual(current['version'], 'fixture-v1')
        os.environ['METHOD_VERSION_ID'] = new_version
        self.assertEqual(json.loads(self.f.request(room.ROOT + '/method')['body'])['method']['version'], 'fixture-v2')
        pinned = self.f.request(room.ROOT + '/method', q={'case_id': case['id']})
        self.assertEqual(json.loads(pinned['body'])['method']['version'], 'fixture-v1')
        self.assertNotIn('Synthetic fixture question', self.f.request()['body'])
        self.assertEqual(self.f.request(room.ROOT + '/method', q={'key': 'other'})['statusCode'], 400)

    def test_owner_isolation_including_method_and_export(self):
        case = self.patch(self.f.create())
        review = self.review(case)
        self.f.switch_owner('second-owner')
        self.assertEqual(json.loads(self.f.request()['body'])['items'], [])
        for path, q in [(self.case_path(case), None), (room.ROOT + '/method', {'case_id': case['id']}),
                        (self.case_path(case) + '/export', {'revision': str(case['revision'])})]:
            self.assertEqual(self.f.request(path, q=q)['statusCode'], 404)
        self.assertEqual(self.f.request(self.case_path(case), 'PATCH', {'revision': review['case']['revision'], 'draft': {'title': 'Intrusion'}})['statusCode'], 404)

    def test_draft_limits_references_and_unknown_fields(self):
        case = self.f.create()
        for draft in ({'unsupported': 'value'}, {'internal_notes': 'x' * 3001},
                      {'evidence': [{'id': 'same'}, {'id': 'same'}]},
                      {'findings': [{'id': 'f1', 'evidence_ids': ['foreign']}]},
                      {'recommendation': {'position': 'defer', 'option_id': 'foreign'}},
                      {'answers': {'private-foreign-question': 'no'}}, {'actions': [{}]},
                      {'evidence': [{'id': 'e1', 'observed_at': '2026-99-01'}]}):
            with self.subTest(draft=draft):
                result = self.f.request(self.case_path(case), 'PATCH', {'revision': 0, 'draft': draft})
                self.assertEqual(result['statusCode'], 400, result)
        self.assertEqual(self.f.request(self.case_path(case), 'PATCH', {'revision': 0, 'draft': {'context': 'x' * 25000}})['statusCode'], 400)
        saved = self.patch(case, {'evidence': [{'id': 'empty'}], 'actions': [{'id': 'incomplete'}]})
        self.assertEqual(saved['evidence'][0]['detail'], '')
        self.assertEqual(self.f.request(self.case_path(saved) + '/review', 'POST', {'revision': saved['revision']})['statusCode'], 400)

    def test_stale_revision_and_racing_transaction_do_not_add_audit(self):
        case = self.f.create()
        new = self.patch(case, {'context': 'First edit'})
        before = self.f.table.scan()['Count']
        self.assertEqual(self.f.request(self.case_path(case), 'PATCH', {'revision': 0, 'draft': {'context': 'Lost edit'}})['statusCode'], 409)
        original = room.transact
        def race(actions):
            self.f.table.update_item(Key=room.case_key('owner-id', case['id']), UpdateExpression='SET revision=:n', ExpressionAttributeValues={':n': 99})
            return original(actions)
        with patch.object(room, 'transact', side_effect=race):
            result = self.f.request(self.case_path(new), 'PATCH', {'revision': new['revision'], 'draft': {'context': 'Racing edit'}})
        self.assertEqual(result['statusCode'], 409, result)
        self.assertEqual(self.f.table.scan()['Count'], before)
        self.assertEqual(json.loads(self.f.request(self.case_path(case))['body'])['case']['context'], 'First edit')

    def test_review_requires_complete_evidence_and_rejects_unconditional_blocker(self):
        case = self.f.create()
        self.assertEqual(self.f.request(self.case_path(case) + '/review', 'POST', {'revision': 0})['statusCode'], 400)
        draft = complete_draft()
        draft['findings'][0]['severity'] = 'blocker'
        draft['recommendation']['position'] = 'proceed'
        case = self.patch(case, draft)
        result = self.f.request(self.case_path(case) + '/review', 'POST', {'revision': case['revision']})
        self.assertEqual(result['statusCode'], 400)
        case = self.patch(case, {'recommendation': {'position': 'defer', 'detail': 'Defer until the unresolved condition has a measured answer.', 'option_id': ''}})
        self.assertEqual(self.review(case)['case']['state'], 'reviewed')

    def test_immutable_review_and_allowlisted_export(self):
        case = self.patch(self.f.create())
        reviewed = self.review(case)
        self.assertEqual(reviewed['case']['revision'], case['revision'] + 1)
        self.assertEqual(reviewed['review']['source_revision'], case['revision'])
        edited = self.patch(reviewed['case'], {'decision': 'A materially different later draft decision.', 'internal_notes': 'LATER PRIVATE NOTE'})
        exported = self.f.request(self.case_path(case) + '/export', q={'revision': str(case['revision'])})
        self.assertEqual(exported['statusCode'], 200, exported)
        report = json.loads(exported['body'])['report']
        self.assertEqual(report, reviewed['review']['client_report'])
        self.assertNotEqual(report['decision'], edited['decision'])
        for private in ('internal_notes', 'answers', 'PRIVATE', 'question', 'method_object_version', 'fingerprint'):
            self.assertNotIn(private, exported['body'])
        self.assertEqual(self.f.request(self.case_path(case) + '/export', q={'revision': str(edited['revision'])})['statusCode'], 404)
        audit = [r for r in self.f.table.scan()['Items'] if r['kind'] == 'audit']
        self.assertTrue(any(r['action'] == 'exported' for r in audit))
        self.assertTrue(all(set(r) <= {'pk', 'sk', 'kind', 'case_id', 'owner', 'action', 'revision', 'at', 'ttl'} for r in audit))

    def test_delete_removes_case_body_and_all_reviews_atomically(self):
        case = self.patch(self.f.create())
        result = self.review(case)
        case = result['case']
        self.assertEqual(self.f.request(self.case_path(case), 'DELETE', {'revision': case['revision'], 'confirm': 'wrong'})['statusCode'], 400)
        result = self.f.request(self.case_path(case), 'DELETE', {'revision': case['revision'], 'confirm': 'DELETE ' + case['id']})
        self.assertEqual(result['statusCode'], 200, result)
        records = self.f.table.scan()['Items']
        self.assertTrue(all(r['kind'] in {'deleted', 'audit'} for r in records))
        self.assertNotIn('Synthetic company', json.dumps(records, default=str))
        self.assertEqual(self.f.request(self.case_path(case))['statusCode'], 404)
        self.assertEqual(self.f.request(self.case_path(case) + '/export', q={'revision': '1'})['statusCode'], 404)

    def test_export_allowlist_excludes_future_nested_private_fields(self):
        case = self.patch(self.f.create())
        reviewed = self.review(case)
        key = {'pk': room.owner_pk('owner-id'), 'sk': 'review#' + case['id'] + '#' + str(case['revision'])}
        stored = self.f.table.get_item(Key=key)['Item']
        stored['client_report']['evidence'][0]['future_private_note'] = 'CONFIDENTIAL FUTURE FIELD'
        stored['client_report']['recommendation']['private_rationale'] = 'CONFIDENTIAL FUTURE FIELD'
        self.f.table.put_item(Item=stored)
        result = self.f.request(self.case_path(case) + '/export', q={'revision': str(case['revision'])})
        self.assertEqual(result['statusCode'], 200, result)
        self.assertNotIn('CONFIDENTIAL', result['body'])
        self.assertEqual(json.loads(result['body'])['report'], reviewed['review']['client_report'])

    def test_review_cap_and_atomic_delete_at_maximum(self):
        case = self.patch(self.f.create())
        for _ in range(room.MAX_REVIEWS):
            case = self.review(case)['case']
        before = self.f.table.scan()['Count']
        denied = self.f.request(self.case_path(case) + '/review', 'POST', {'revision': case['revision']})
        self.assertEqual(denied['statusCode'], 400)
        self.assertEqual(self.f.table.scan()['Count'], before)
        result = self.f.request(self.case_path(case), 'DELETE', {'revision': case['revision'], 'confirm': 'DELETE ' + case['id']})
        self.assertEqual(result['statusCode'], 200, result)
        self.assertFalse(any(row.get('kind') in {'assessment', 'review'} for row in self.f.table.scan()['Items']))

    def test_delete_wins_against_inflight_edit_review_and_export(self):
        for operation in ('edit', 'review', 'export'):
            with self.subTest(operation=operation):
                case = self.patch(self.f.create())
                if operation == 'export':
                    case = self.review(case)['case']
                original = room.transact
                intercepted = False
                def delete_first(actions):
                    nonlocal intercepted
                    if not intercepted:
                        intercepted = True
                        deleted = self.f.request(self.case_path(case), 'DELETE', {'revision': case['revision'], 'confirm': 'DELETE ' + case['id']})
                        self.assertEqual(deleted['statusCode'], 200, deleted)
                    return original(actions)
                with patch.object(room, 'transact', side_effect=delete_first):
                    if operation == 'edit':
                        result = self.f.request(self.case_path(case), 'PATCH', {'revision': case['revision'], 'draft': {'context': 'Must never resurrect this deleted case.'}})
                    elif operation == 'review':
                        result = self.f.request(self.case_path(case) + '/review', 'POST', {'revision': case['revision']})
                    else:
                        result = self.f.request(self.case_path(case) + '/export', q={'revision': str(case['reviews'][0]['source_revision'])})
                self.assertEqual(result['statusCode'], 409, result)
                self.assertEqual(self.f.request(self.case_path(case))['statusCode'], 404)
                rows = self.f.table.scan()['Items']
                self.assertFalse(any(r.get('case_id') == case['id'] and r.get('kind') == 'review' for r in rows))

    def test_review_deletion_reads_all_query_pages(self):
        case = self.patch(self.f.create())
        case = self.review(case)['case']
        case = self.review(case)['case']
        original_query = self.f.table.query
        def small_pages(**kwargs):
            kwargs['Limit'] = 1
            return original_query(**kwargs)
        with patch.object(self.f.table, 'query', side_effect=small_pages):
            deleted = self.f.request(self.case_path(case), 'DELETE', {'revision': case['revision'], 'confirm': 'DELETE ' + case['id']})
        self.assertEqual(deleted['statusCode'], 200, deleted)
        self.assertFalse(any(r.get('kind') == 'review' for r in self.f.table.scan()['Items']))

    def test_fixed_retention_hides_and_sweeps_content(self):
        case = self.f.create(retention_days=30)
        edited = self.patch(case)
        self.assertEqual(edited['expires_at'], case['expires_at'])
        reviewed = self.review(edited)
        self.assertEqual(reviewed['case']['expires_at'], case['expires_at'])
        for row in self.f.table.scan()['Items']:
            self.assertEqual(row['ttl'], case['expires_at'])
        future = case['expires_at'] + 1
        with patch('decision_room.time.time', return_value=future):
            # Use storage read directly because the genuine short-lived session also expires.
            self.assertIsNone(room.get_case('owner-id', case['id']))
            self.assertGreater(room.maintain()['removed'], 0)
        self.assertTrue(all(r['pk'] == 'system' for r in self.f.table.scan()['Items']))

    def test_sweeper_resumes_bounded_cursor(self):
        now = int(time.time())
        with self.f.table.batch_writer() as batch:
            for n in range(135):
                batch.put_item(Item={'pk': 'expired-owner', 'sk': str(n), 'ttl': now - 1})
        first = room.handler({'source': 'aws.events'})
        self.assertLessEqual(first['removed'], 100)
        self.assertTrue(first['more'])
        second = room.handler({'source': 'aws.events'})
        self.assertEqual(first['removed'] + second['removed'], 135)

    def test_failures_never_log_evidence_or_claim_saved(self):
        case = self.f.create()
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch.object(room.TABLE.meta.client, 'transact_write_items', side_effect=ClientError({'Error': {'Code': 'InternalServerError', 'Message': 'SECRET TEST CONTENT'}}, 'TransactWriteItems')):
            result = self.f.request(self.case_path(case), 'PATCH', {'revision': 0, 'draft': {'context': 'PRIVATE INPUT'}})
        self.assertEqual(result['statusCode'], 503)
        self.assertNotIn('SECRET', output.getvalue() + result['body'])
        self.assertNotIn('PRIVATE INPUT', output.getvalue() + result['body'])
        self.assertEqual(json.loads(self.f.request(self.case_path(case))['body'])['case']['revision'], 0)

    def test_method_corruption_and_missing_version_fail_closed(self):
        broken = copy.deepcopy(METHOD)
        broken['sections'][0]['questions'].append(broken['sections'][0]['questions'][0])
        os.environ['METHOD_VERSION_ID'] = self.f.put_method(broken)
        self.assertEqual(self.f.request(room.ROOT + '/method')['statusCode'], 503)
        os.environ['METHOD_VERSION_ID'] = 'missing-object-version'
        self.assertEqual(self.f.request(room.ROOT + '/method')['statusCode'], 503)


if __name__ == '__main__':
    unittest.main()
