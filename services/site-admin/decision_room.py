"""Owner-only assessment records. No seeded clients, model calls or remote evidence fetches.

The generic engine is public source. The question bank is an exact private S3
object; cases pin its object version and hash. Client exports are constructed
from an explicit field list, never from private working notes.
"""
import copy
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from datetime import date
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from auth import Auth, Unauthorized
from contracts import Invalid, body, exact, text, uid


ROOT = '/api/admin/assessments'
AUTH = TABLE = S3 = SALT = None
DOMAINS = {'general', 'cloud', 'saas', 'data', 'security', 'delivery', 'ai'}
RETENTIONS = {30, 90, 180, 365}
MAX_REVIEWS = 20
EDITABLE = {'title', 'client', 'decision', 'domain', 'context', 'boundary',
            'constraints', 'evidence', 'findings', 'options', 'recommendation',
            'counterargument', 'actions', 'answers', 'internal_notes'}
CLIENT_FIELDS = ('title', 'client', 'decision', 'domain', 'context', 'boundary',
                 'constraints', 'evidence', 'findings', 'options',
                 'recommendation', 'counterargument', 'actions')
CLIENT_ITEMS = {
    'evidence': ('id', 'label', 'detail', 'source', 'scope', 'observed_at', 'kind'),
    'findings': ('id', 'title', 'detail', 'contradiction', 'evidence_ids', 'severity', 'resolved'),
    'options': ('id', 'title', 'detail', 'constraints', 'cost_assumptions'),
    'actions': ('id', 'detail', 'owner', 'acceptance'),
}
REPORT_META = ('report_type', 'review_id', 'source_revision', 'reviewed_at', 'method_version')


class Conflict(Exception):
    pass


class Unavailable(Exception):
    pass


class SessionReader:
    """Auth.session needs only get; this Lambda cannot create or mutate sessions."""
    def __init__(self, db):
        self.table = db.Table(os.environ['SESSIONS_TABLE'])

    def get(self, table, pk, sk='0'):
        if table != 'sessions':
            raise Unauthorized()
        item = self.table.get_item(Key={'pk': pk, 'sk': sk}, ConsistentRead=True).get('Item')
        return item if item and item.get('ttl', 0) > int(time.time()) else None


def initialize():
    global AUTH, TABLE, S3, SALT
    if TABLE is None:
        db = boto3.resource('dynamodb')
        TABLE = db.Table(os.environ['ASSESSMENTS_TABLE'])
        AUTH = Auth(SessionReader(db))
    if S3 is None:
        S3 = boto3.client('s3')
    if SALT is None:
        SALT = boto3.client('secretsmanager').get_secret_value(
            SecretId=os.environ['RATE_SECRET'])['SecretString']


def response(status, data):
    return {'statusCode': status, 'headers': {
        'Content-Type': 'application/json', 'Cache-Control': 'no-store, private, max-age=0',
        'Pragma': 'no-cache', 'Vary': 'Cookie, Origin', 'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer'},
        'body': json.dumps(data, default=lambda n: int(n) if isinstance(n, Decimal) else str(n))}


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', value):
        raise Invalid('Use a valid record identifier')
    return value


def choice(value, options, label):
    if not isinstance(value, str) or value not in options:
        raise Invalid('Choose a valid ' + label)
    return value


def iso_date(value):
    value = text(value, 0, 10)
    if value:
        try:
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError()
        except ValueError:
            raise Invalid('Use YYYY-MM-DD for evidence dates')
    return value


def validate_method(raw):
    exact(raw, {'schema_version', 'version', 'title', 'reviewed_at', 'sections'})
    if type(raw.get('schema_version')) is not int or raw['schema_version'] != 1:
        raise Invalid('Unsupported methodology format')
    method = {'schema_version': 1, 'version': text(raw.get('version'), 1, 80),
              'title': text(raw.get('title'), 1, 200),
              'reviewed_at': iso_date(raw.get('reviewed_at', '')), 'sections': []}
    sections = raw.get('sections')
    if not isinstance(sections, list) or not 1 <= len(sections) <= 12:
        raise Invalid('Invalid methodology sections')
    seen_sections, seen_questions = set(), set()
    for section in sections:
        exact(section, {'id', 'title', 'questions'})
        sid = identifier(section.get('id'))
        if sid in seen_sections:
            raise Invalid('Duplicate methodology section')
        seen_sections.add(sid)
        item = {'id': sid, 'title': text(section.get('title'), 1, 200), 'questions': []}
        questions = section.get('questions')
        if not isinstance(questions, list) or not 1 <= len(questions) <= 30:
            raise Invalid('Invalid methodology questions')
        for question in questions:
            exact(question, {'id', 'prompt', 'why', 'evidence_to_seek', 'hint'})
            qid = identifier(question.get('id'))
            if qid in seen_questions or len(seen_questions) >= 150:
                raise Invalid('Duplicate or excessive methodology questions')
            seen_questions.add(qid)
            item['questions'].append({'id': qid, 'prompt': text(question.get('prompt'), 1, 1200),
                **{k: text(question.get(k, ''), 0, 1600) for k in ('why', 'evidence_to_seek', 'hint')}})
        method['sections'].append(item)
    return method


def load_method(case=None):
    args = {'Bucket': os.environ['METHOD_BUCKET'], 'Key': os.environ['METHOD_KEY']}
    args['VersionId'] = case['method_object_version'] if case else os.environ['METHOD_VERSION_ID']
    result = S3.get_object(**args)
    stream = result['Body']
    try:
        raw = stream.read(131073)
    finally:
        stream.close()
    if len(raw) > 131072:
        raise Unavailable()
    digest = hashlib.sha256(raw).hexdigest()
    if case and not hmac.compare_digest(case['method_hash'], digest):
        raise Unavailable()
    try:
        method = validate_method(json.loads(raw))
    except (Invalid, ValueError, TypeError, UnicodeDecodeError):
        raise Unavailable()
    return method, digest, result.get('VersionId', '')


def rows(value, label):
    if not isinstance(value, list) or len(value) > 16:
        raise Invalid('Use at most 16 ' + label)
    seen = set()
    for item in value:
        if not isinstance(item, dict):
            raise Invalid('Invalid ' + label)
        ident = identifier(item.get('id'))
        if ident in seen:
            raise Invalid('Duplicate ' + label + ' identifier')
        seen.add(ident)
    return value


def validate_draft(raw, method):
    exact(raw, EDITABLE)
    out = {'title': text(raw.get('title'), 3, 200), 'client': text(raw.get('client', ''), 0, 200),
           'domain': choice(raw.get('domain', 'general'), DOMAINS, 'domain')}
    for key in ('decision', 'context', 'boundary', 'constraints', 'counterargument', 'internal_notes'):
        out[key] = text(raw.get(key, ''), 0, 3000)
    out['evidence'] = []
    for item in rows(raw.get('evidence', []), 'evidence records'):
        exact(item, {'id', 'label', 'detail', 'source', 'scope', 'observed_at', 'kind'})
        out['evidence'].append({'id': item['id'], 'label': text(item.get('label', ''), 0, 200),
            'detail': text(item.get('detail', ''), 0, 3000), 'source': text(item.get('source', ''), 0, 500),
            'scope': text(item.get('scope', ''), 0, 500), 'observed_at': iso_date(item.get('observed_at', '')),
            'kind': choice(item.get('kind', 'unknown'), {'reported', 'documented', 'observed', 'tested', 'unknown'}, 'evidence kind')})
    evidence_ids = {item['id'] for item in out['evidence']}
    out['findings'] = []
    for item in rows(raw.get('findings', []), 'findings'):
        exact(item, {'id', 'title', 'detail', 'contradiction', 'evidence_ids', 'severity', 'resolved'})
        links = item.get('evidence_ids', [])
        if not isinstance(links, list) or len(links) > 16 or any(not isinstance(i, str) or i not in evidence_ids for i in links) or len(set(links)) != len(links):
            raise Invalid('Every finding evidence reference must belong to this assessment')
        resolved = item.get('resolved', False)
        if type(resolved) is not bool:
            raise Invalid('Finding resolution must be true or false')
        out['findings'].append({'id': item['id'], 'title': text(item.get('title', ''), 0, 200),
            'detail': text(item.get('detail', ''), 0, 2000), 'contradiction': text(item.get('contradiction', ''), 0, 2000),
            'evidence_ids': links, 'severity': choice(item.get('severity', 'info'), {'info', 'risk', 'blocker'}, 'finding severity'), 'resolved': resolved})
    out['options'] = []
    for item in rows(raw.get('options', []), 'options'):
        exact(item, {'id', 'title', 'detail', 'constraints', 'cost_assumptions'})
        out['options'].append({'id': item['id'], 'title': text(item.get('title', ''), 0, 200),
            **{k: text(item.get(k, ''), 0, 2000) for k in ('detail', 'constraints', 'cost_assumptions')}})
    recommendation = raw.get('recommendation', {})
    exact(recommendation, {'position', 'detail', 'option_id'})
    option_id = text(recommendation.get('option_id', ''), 0, 80)
    if option_id and option_id not in {item['id'] for item in out['options']}:
        raise Invalid('Recommendation must reference an option in this assessment')
    out['recommendation'] = {'position': choice(recommendation.get('position', 'defer'), {'proceed', 'conditional', 'defer'}, 'recommendation'),
                             'detail': text(recommendation.get('detail', ''), 0, 3000), 'option_id': option_id}
    out['actions'] = []
    for item in rows(raw.get('actions', []), 'actions'):
        exact(item, {'id', 'detail', 'owner', 'acceptance'})
        out['actions'].append({'id': item['id'], 'detail': text(item.get('detail', ''), 0, 2000),
            'owner': text(item.get('owner', ''), 0, 200), 'acceptance': text(item.get('acceptance', ''), 0, 1000)})
    answers = raw.get('answers', {})
    if not isinstance(answers, dict) or len(answers) > 100:
        raise Invalid('Invalid answers')
    allowed_questions = {q['id'] for section in method['sections'] for q in section['questions']}
    if set(answers) - allowed_questions:
        raise Invalid('Answers must use questions from the pinned methodology')
    out['answers'] = {k: text(v, 0, 2000) for k, v in answers.items()}
    return out


def review_ready(draft):
    if any(len(draft[k]) < 10 for k in ('decision', 'counterargument')) or len(draft['recommendation']['detail']) < 10:
        raise Invalid('Review needs a decision, recommendation and counterargument with meaningful detail')
    if not draft['evidence'] or any(not e['label'] or len(e['detail']) < 10 or not e['source'] for e in draft['evidence']) or all(e['kind'] == 'unknown' for e in draft['evidence']):
        raise Invalid('Review needs described evidence, its source and an explicit evidence kind')
    if any(not f['title'] or len(f['detail']) < 10 or not f['evidence_ids'] for f in draft['findings']):
        raise Invalid('Every reviewed finding needs detail and supporting evidence references')
    position = draft['recommendation']['position']
    if len(draft['options']) < (1 if position == 'defer' else 2) or any(not o['title'] or len(o['detail']) < 10 for o in draft['options']):
        raise Invalid('Review needs detailed alternatives: two options, or one next step when deferring')
    if position != 'defer' and not draft['recommendation']['option_id']:
        raise Invalid('Choose the recommended option before review')
    if not draft['actions'] or any(len(a['detail']) < 10 or not a['owner'] or len(a['acceptance']) < 10 for a in draft['actions']):
        raise Invalid('Review needs complete actions with an owner and acceptance check')
    if position == 'proceed' and (any(f['severity'] == 'blocker' and not f['resolved'] for f in draft['findings']) or not any(e['kind'] in {'documented', 'observed', 'tested'} for e in draft['evidence'])):
        raise Invalid('Unconditional proceed needs documented, observed or tested evidence and no unresolved blockers. Use conditional or defer when appropriate.')


def client_projection(source, metadata=False):
    """Allowlist every level so later private schema extensions cannot enter reports."""
    report = {key: copy.deepcopy(source[key]) for key in CLIENT_FIELDS
              if key not in CLIENT_ITEMS and key != 'recommendation'}
    for collection, fields in CLIENT_ITEMS.items():
        report[collection] = [{key: copy.deepcopy(item[key]) for key in fields} for item in source[collection]]
    report['recommendation'] = {key: source['recommendation'][key] for key in ('position', 'detail', 'option_id')}
    if metadata:
        report.update({key: source[key] for key in REPORT_META})
    return report


def owner_pk(owner):
    return 'owner#' + owner


def case_key(owner, ident):
    return {'pk': owner_pk(owner), 'sk': 'case#' + uid(ident)}


def get_case(owner, ident):
    row = TABLE.get_item(Key=case_key(owner, ident), ConsistentRead=True).get('Item')
    if not row or row.get('kind') != 'assessment' or row.get('ttl', 0) <= int(time.time()) or row.get('owner') != owner or row.get('id') != ident:
        return None
    return row


def case_view(row):
    return {**copy.deepcopy(row['draft']), **{k: row[k] for k in (
        'id', 'revision', 'created_at', 'updated_at', 'expires_at', 'retention_days',
        'method_version', 'state', 'reviews')}, 'review_count': len(row['reviews'])}


def summary(row):
    return {**{k: row[k] for k in ('id', 'revision', 'created_at', 'updated_at', 'expires_at', 'state')},
            **{k: row['draft'][k] for k in ('title', 'client', 'decision', 'domain')}, 'review_count': len(row['reviews'])}


def audit(owner, row, action, revision):
    now = int(time.time())
    return {'pk': owner_pk(owner), 'sk': 'audit#' + row['id'] + '#' + str(uuid.uuid4()),
            'kind': 'audit', 'case_id': row['id'], 'owner': owner, 'action': action,
            'revision': revision, 'at': now, 'ttl': row['expires_at']}


def put_action(item, condition=None, values=None, names=None):
    if len(json.dumps(item, default=str).encode()) > 70000:
        raise Invalid('Assessment record exceeds the storage limit')
    result = {'TableName': TABLE.name, 'Item': item}
    if condition:
        result['ConditionExpression'] = condition
    if values:
        result['ExpressionAttributeValues'] = values
    if names:
        result['ExpressionAttributeNames'] = names
    return {'Put': result}


def transact(actions):
    try:
        TABLE.meta.client.transact_write_items(TransactItems=actions)
    except ClientError as error:
        if error.response['Error']['Code'] == 'TransactionCanceledException' and any(
                item.get('Code') == 'ConditionalCheckFailed' for item in error.response.get('CancellationReasons', [])):
            raise Conflict()
        raise


def revision(raw, row):
    if type(raw.get('revision')) is not int or raw['revision'] != row['revision']:
        raise Conflict()


def update_action(row, previous):
    return put_action(
        row, 'revision = :revision AND expires_at > :now AND #kind = :kind',
        {':revision': previous, ':now': int(time.time()), ':kind': 'assessment'}, {'#kind': 'kind'})


def review_keys(owner, ident):
    """DynamoDB's byte-size page boundary can occur before its item limit."""
    found, cursor = [], None
    while True:
        result = TABLE.query(KeyConditionExpression=Key('pk').eq(owner_pk(owner)) & Key('sk').begins_with('review#' + ident + '#'),
                             ConsistentRead=True, Limit=MAX_REVIEWS + 1, ProjectionExpression='pk,sk',
                             **({'ExclusiveStartKey': cursor} if cursor else {}))
        found.extend(result['Items'])
        if len(found) > MAX_REVIEWS:
            raise Unavailable()
        cursor = result.get('LastEvaluatedKey')
        if not cursor:
            return found
        if not result['Items']:
            raise Unavailable()


def maintain():
    cursor = TABLE.get_item(Key={'pk': 'system', 'sk': 'expiry-sweep'}, ConsistentRead=True).get('Item', {}).get('cursor')
    page = TABLE.scan(Limit=100, **({'ExclusiveStartKey': cursor} if cursor else {}))
    now = int(time.time())
    expired = [row for row in page['Items'] if row.get('ttl', now + 1) <= now and row.get('pk') != 'system']
    with TABLE.batch_writer() as batch:
        for row in expired:
            batch.delete_item(Key={'pk': row['pk'], 'sk': row['sk']})
    TABLE.put_item(Item={'pk': 'system', 'sk': 'expiry-sweep', 'cursor': page.get('LastEvaluatedKey'), 'ttl': now + 31536000})
    return {'removed': len(expired), 'more': bool(page.get('LastEvaluatedKey'))}


def handler(event, context=None):
    operation = 'unknown'
    try:
        initialize()
        if event.get('source') == 'aws.events' and not event.get('httpMethod'):
            return maintain()
        event['headers'] = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
        headers = event['headers']
        if not hmac.compare_digest(headers.get('x-site-origin', ''), SALT):
            return response(403, {'error': 'Site origin required'})
        method = event.get('httpMethod', 'GET')
        if method != 'GET' and headers.get('origin') != os.environ['PUBLIC_ORIGIN']:
            return response(400, {'error': 'Same-origin request required'})
        session = AUTH.session(event, mutation=method != 'GET')
        if method not in {'GET', 'POST', 'PATCH', 'DELETE'}:
            return response(405, {'error': 'Method not allowed'})
        owner = session['sub']
        path = event.get('path', '')
        query = event.get('queryStringParameters') or {}
        if path == ROOT + '/method' and method == 'GET':
            operation = 'method'
            exact(query, {'case_id'})
            case = get_case(owner, query['case_id']) if query.get('case_id') else None
            if query.get('case_id') and not case:
                return response(404, {'error': 'Assessment not found'})
            bank, _, _ = load_method(case)
            return response(200, {'method': bank})
        if path == ROOT:
            operation = 'collection'
            if method == 'GET':
                exact(query, {'cursor'})
                args = {'KeyConditionExpression': Key('pk').eq(owner_pk(owner)) & Key('sk').begins_with('case#'), 'Limit': 100, 'ConsistentRead': True}
                if query.get('cursor'):
                    args['ExclusiveStartKey'] = case_key(owner, query['cursor'])
                data = TABLE.query(**args)
                items = [summary(row) for row in data['Items'] if row.get('kind') == 'assessment' and row.get('owner') == owner and row.get('ttl', 0) > int(time.time())]
                last = data.get('LastEvaluatedKey')
                return response(200, {'items': sorted(items, key=lambda row: row['updated_at'], reverse=True), 'partial': bool(last), 'next_cursor': last['sk'][5:] if last else None})
            if method == 'POST':
                raw = body(event)
                exact(raw, {'title', 'client', 'decision', 'domain', 'retention_days', 'request_id'})
                days = raw.get('retention_days', 180)
                if type(days) is not int or days not in RETENTIONS:
                    raise Invalid('Choose retention of 30, 90, 180 or 365 days')
                initial = {'title': text(raw.get('title'), 3, 200), 'client': text(raw.get('client', ''), 0, 200),
                           'decision': text(raw.get('decision'), 10, 3000), 'domain': choice(raw.get('domain', 'general'), DOMAINS, 'domain'), 'retention_days': days}
                fingerprint = hashlib.sha256(json.dumps(initial, sort_keys=True).encode()).hexdigest()
                ident = uid(raw['request_id']) if 'request_id' in raw else str(uuid.uuid4())
                existing = TABLE.get_item(Key=case_key(owner, ident), ConsistentRead=True).get('Item')
                if existing:
                    if existing.get('kind') != 'assessment' or existing.get('owner') != owner or existing.get('id') != ident or existing.get('ttl', 0) <= int(time.time()) or not hmac.compare_digest(existing.get('fingerprint', ''), fingerprint):
                        raise Conflict()
                    return response(200, {'case': case_view(existing), 'duplicate': True})
                bank, method_hash, object_version = load_method()
                draft = validate_draft({k: v for k, v in initial.items() if k != 'retention_days'}, bank)
                now = int(time.time())
                row = {**case_key(owner, ident), 'kind': 'assessment', 'id': ident, 'owner': owner,
                    'revision': 0, 'created_at': now, 'updated_at': now, 'retention_days': days,
                    'expires_at': now + days * 86400, 'ttl': now + days * 86400,
                    'method_version': bank['version'], 'method_hash': method_hash,
                    'method_object_version': object_version, 'draft': draft, 'state': 'draft', 'reviews': [], 'fingerprint': fingerprint}
                transact([put_action(row, 'attribute_not_exists(pk)'), put_action(audit(owner, row, 'created', 0))])
                return response(201, {'case': case_view(row)})
            return response(405, {'error': 'Method not allowed'})
        tail = path[len(ROOT) + 1:].split('/') if path.startswith(ROOT + '/') else []
        if not 1 <= len(tail) <= 2:
            return response(404, {'error': 'Not found'})
        ident = uid(tail[0])
        row = get_case(owner, ident)
        if not row:
            return response(404, {'error': 'Assessment not found'})
        operation = tail[1] if len(tail) == 2 and tail[1] in {'review', 'export'} else 'case'
        if len(tail) == 1:
            exact(query, set())
            if method == 'GET':
                return response(200, {'case': case_view(row)})
            raw = body(event)
            if method == 'PATCH':
                exact(raw, {'revision', 'draft'})
                revision(raw, row)
                exact(raw.get('draft'), EDITABLE)
                bank, _, _ = load_method(row)
                changed = copy.deepcopy(row)
                changed['draft'] = validate_draft({**row['draft'], **raw['draft']}, bank)
                changed.update(revision=row['revision'] + 1, updated_at=int(time.time()), state='draft')
                transact([update_action(changed, row['revision']), put_action(audit(owner, changed, 'updated', changed['revision']))])
                return response(200, {'case': case_view(changed)})
            if method == 'DELETE':
                exact(raw, {'revision', 'confirm'})
                revision(raw, row)
                if raw.get('confirm') != 'DELETE ' + ident:
                    raise Invalid('Explicit assessment deletion confirmation required')
                children = review_keys(owner, ident)
                tombstone = {**case_key(owner, ident), 'kind': 'deleted', 'id': ident, 'owner': owner,
                             'revision': row['revision'] + 1, 'expires_at': row['expires_at'], 'ttl': row['ttl']}
                actions = [update_action(tombstone, row['revision'])]
                actions += [{'Delete': {'TableName': TABLE.name, 'Key': {'pk': item['pk'], 'sk': item['sk']}}} for item in children]
                actions.append(put_action(audit(owner, row, 'deleted', row['revision'])))
                transact(actions)
                return response(200, {'deleted': True})
        if len(tail) == 2 and tail[1] == 'review' and method == 'POST':
            exact(query, set())
            raw = body(event)
            exact(raw, {'revision'})
            revision(raw, row)
            if len(row['reviews']) >= MAX_REVIEWS:
                raise Invalid('This assessment has reached its 20 reviewed snapshots limit')
            review_ready(row['draft'])
            now = int(time.time())
            review_id = str(uuid.uuid4())
            report = client_projection(row['draft'])
            report.update(report_type='Architecture Decision Review', review_id=review_id,
                          source_revision=row['revision'], reviewed_at=now, method_version=row['method_version'])
            info = {'id': review_id, 'source_revision': row['revision'], 'created_at': now}
            snapshot = {'pk': owner_pk(owner), 'sk': 'review#' + ident + '#' + str(row['revision']),
                'kind': 'review', 'case_id': ident, 'owner': owner, **info, 'client_report': report, 'ttl': row['expires_at']}
            changed = copy.deepcopy(row)
            changed['reviews'].append(info)
            changed.update(revision=row['revision'] + 1, updated_at=now, state='reviewed')
            transact([update_action(changed, row['revision']), put_action(snapshot, 'attribute_not_exists(pk)'), put_action(audit(owner, row, 'reviewed', row['revision']))])
            return response(201, {'case': case_view(changed), 'review': {**info, 'client_report': report}})
        if len(tail) == 2 and tail[1] == 'export' and method == 'GET':
            exact(query, {'revision'})
            requested = query.get('revision', '')
            if not isinstance(requested, str) or not re.fullmatch(r'0|[1-9][0-9]{0,8}', requested):
                raise Invalid('Choose a reviewed source revision')
            snapkey = {'pk': owner_pk(owner), 'sk': 'review#' + ident + '#' + requested}
            snapshot = TABLE.get_item(Key=snapkey, ConsistentRead=True).get('Item')
            if not snapshot or snapshot.get('ttl', 0) <= int(time.time()) or snapshot.get('owner') != owner or snapshot.get('case_id') != ident:
                return response(404, {'error': 'Reviewed snapshot not found'})
            report = client_projection(snapshot['client_report'], metadata=True)
            # A logged export must still be authorized against a current case revision.
            transact([{'ConditionCheck': {'TableName': TABLE.name, 'Key': case_key(owner, ident),
                'ConditionExpression': 'revision = :revision AND expires_at > :now AND #kind = :kind',
                'ExpressionAttributeNames': {'#kind': 'kind'},
                'ExpressionAttributeValues': {':revision': row['revision'], ':now': int(time.time()), ':kind': 'assessment'}}},
                put_action(audit(owner, row, 'exported', int(requested)))])
            return response(200, {'filename': 'architecture-decision-' + ident + '-r' + requested + '.json', 'report': report})
        return response(405, {'error': 'Method not allowed'})
    except Unauthorized:
        return response(401, {'error': 'Owner sign-in required. Your session may have expired.'})
    except Conflict:
        return response(409, {'error': 'This assessment changed. Reload the saved version before applying your edits.'})
    except Invalid as error:
        return response(400, {'error': str(error)})
    except Exception as error:
        # Operation comes from a fixed vocabulary, never a case ID, title or input.
        print(json.dumps({'failure_type': type(error).__name__, 'operation': 'decision-room.' + operation}))
        return response(503, {'error': 'Decision Room is temporarily unavailable. Your change has not been confirmed.'})
