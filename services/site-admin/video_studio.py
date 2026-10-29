"""Private, owner-scoped video drafts behind the Decision Room authentication gate.

Catalog examples are copied only by an explicit create request. No model calls,
remote source fetching, publishing, or access to other owners' records occurs.
"""
import copy
import hashlib
import hmac
import json
import re
import time
from urllib.parse import urlsplit

from boto3.dynamodb.conditions import Key

from contracts import Invalid, body, exact, text, uid
import decision_room as room


ROOT = room.ROOT + '/videos'
RETENTION_DAYS = 365
STAGES = {'research', 'script', 'rehearsal', 'ready', 'recorded'}
EDITABLE = {'title', 'premise', 'audience', 'decision', 'stage', 'notes',
            'transcript', 'beats', 'checklist', 'sources'}
REVIEW_CHECKS = {
    'evidence': 'I checked the sources, examples, and factual claims.',
    'clarity': 'The screen and narration explain the same decision clearly.',
    'rehearsal': 'I rehearsed the timing and can demonstrate each screen step.',
    'privacy': 'The recording contains no secrets, private records, or client details.',
    'save': 'I checked the saved artifact and the closing viewer action.',
}
META = ('id', 'revision', 'created_at', 'updated_at', 'expires_at', 'retention_days')


def video_key(owner, ident):
    return {'pk': room.owner_pk(owner), 'sk': 'video#' + uid(ident)}


def get_video(owner, ident):
    row = room.TABLE.get_item(Key=video_key(owner, ident), ConsistentRead=True).get('Item')
    if (not row or row.get('kind') != 'video' or row.get('owner') != owner
            or row.get('id') != ident or row.get('ttl', 0) <= int(time.time())):
        return None
    return row


def video_view(row):
    return {**{key: row[key] for key in META}, 'draft': copy.deepcopy(row['draft'])}


def summary(row):
    return {**{key: row[key] for key in META},
            'title': row['draft']['title'], 'stage': row['draft']['stage']}


def collection(value, maximum, label, identified=True):
    if not isinstance(value, list) or len(value) > maximum:
        raise Invalid('Use at most ' + str(maximum) + ' ' + label)
    seen = set()
    for item in value:
        if not isinstance(item, dict):
            raise Invalid('Invalid ' + label)
        if identified:
            ident = room.identifier(item.get('id'))
            if ident in seen:
                raise Invalid('Duplicate ' + label + ' identifier')
            seen.add(ident)
    return value


def source_url(value):
    value = text(value, 1, 600)
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == 'https' and parsed.hostname and parsed.netloc
                 and parsed.username is None and parsed.password is None
                 and not re.search(r'\s', value))
        # Accessing port also rejects malformed and out-of-range ports.
        parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise Invalid('Sources need a valid HTTPS URL without credentials')
    return value


def validate_draft(raw):
    exact(raw, EDITABLE)
    out = {'title': text(raw.get('title'), 3, 200),
           'stage': room.choice(raw.get('stage', 'research'), STAGES, 'video stage')}
    for key in ('premise', 'audience', 'decision'):
        out[key] = text(raw.get(key, ''), 0, 2000)
    out['notes'] = text(raw.get('notes', ''), 0, 3000)
    out['transcript'] = text(raw.get('transcript', ''), 0, 9000)
    out['beats'] = []
    beat_limits = {'label': 200, 'spoken': 1800, 'screen': 1200, 'visual': 1200,
                   'khalid': 1200, 'codex': 1200, 'save': 800}
    for item in collection(raw.get('beats', []), 12, 'script beats'):
        exact(item, {'id', 'seconds', *beat_limits})
        seconds = item.get('seconds')
        if type(seconds) is not int or not 10 <= seconds <= 180:
            raise Invalid('Each beat needs a duration from 10 to 180 whole seconds')
        out['beats'].append({'id': item['id'], 'seconds': seconds,
            **{key: text(item.get(key, ''), 0, limit) for key, limit in beat_limits.items()}})
    out['checklist'] = []
    for item in collection(raw.get('checklist', []), 16, 'review checks'):
        exact(item, {'id', 'label', 'done'})
        if type(item.get('done')) is not bool:
            raise Invalid('Each review check must be true or false')
        out['checklist'].append({'id': item['id'], 'label': text(item.get('label'), 1, 300),
                                 'done': item['done']})
    out['sources'] = []
    for item in collection(raw.get('sources', []), 8, 'sources', identified=False):
        exact(item, {'title', 'url', 'note'})
        out['sources'].append({'title': text(item.get('title'), 1, 200),
                               'url': source_url(item.get('url')),
                               'note': text(item.get('note', ''), 0, 1500)})
    return out


def review_ready(draft):
    checks = draft['checklist']
    if not set(REVIEW_CHECKS) <= {check['id'] for check in checks} or not all(check['done'] for check in checks):
        raise Invalid('Complete every review check, including evidence, clarity, rehearsal, privacy, and save, before marking this video ready or recorded')
    beats = draft['beats']
    if (not beats or any(len(beat['spoken']) < 20 or len(beat['screen']) < 10 for beat in beats)
            or sum(len(beat['spoken']) for beat in beats) < 120):
        raise Invalid('Ready videos need a meaningful script: at least 120 spoken characters in total, with at least 20 spoken characters and 10 screen instruction characters in every beat')


def check_revision(raw, row):
    if type(raw.get('revision')) is not int or raw['revision'] < 0:
        raise Invalid('A nonnegative whole revision number is required')
    if raw['revision'] != row['revision']:
        raise room.Conflict()


def update_action(row, previous):
    return room.put_action(row,
        'revision = :revision AND expires_at > :now AND #kind = :kind',
        {':revision': previous, ':now': int(time.time()), ':kind': 'video'}, {'#kind': 'kind'})


def catalog():
    from video_catalog import CATALOG
    return CATALOG


def initial_draft(title, template_id):
    if template_id:
        template = next((item for item in catalog()['templates'] if item['id'] == template_id), None)
        if template is None:
            raise Invalid('Choose a video template from the catalog')
        raw = {key: copy.deepcopy(value) for key, value in template.items() if key != 'id'}
        raw['title'] = title
    else:
        raw = {'title': title, 'stage': 'research', 'checklist': [
            {'id': key, 'label': label, 'done': False} for key, label in REVIEW_CHECKS.items()]}
    draft = validate_draft(raw)
    # Starting from a template always requires this video's own review.
    if draft['stage'] in {'ready', 'recorded'}:
        draft['stage'] = 'script'
    for check in draft['checklist']:
        check['done'] = False
    return draft


def duplicate(owner, ident, fingerprint):
    existing = room.TABLE.get_item(Key=video_key(owner, ident), ConsistentRead=True).get('Item')
    if existing:
        if (existing.get('kind') != 'video' or existing.get('owner') != owner
                or existing.get('id') != ident or existing.get('ttl', 0) <= int(time.time())
                or not hmac.compare_digest(existing.get('fingerprint', ''), fingerprint)):
            raise room.Conflict()
        return room.response(200, {'video': video_view(existing), 'duplicate': True})
    return None


def handle(event, owner):
    """Called only after the parent handler's origin, session, role and CSRF checks."""
    method, path = event.get('httpMethod', 'GET'), event.get('path', '')
    query = event.get('queryStringParameters') or {}
    if path == ROOT + '/catalog':
        if method != 'GET':
            return room.response(405, {'error': 'Method not allowed'})
        exact(query, set())
        return room.response(200, {'catalog': catalog()})
    if path == ROOT:
        if method == 'GET':
            exact(query, {'cursor'})
            args = {'KeyConditionExpression': Key('pk').eq(room.owner_pk(owner)) & Key('sk').begins_with('video#'),
                    'Limit': 100, 'ConsistentRead': True}
            if query.get('cursor'):
                args['ExclusiveStartKey'] = video_key(owner, query['cursor'])
            data = room.TABLE.query(**args)
            items = [summary(row) for row in data['Items'] if row.get('kind') == 'video'
                     and row.get('owner') == owner and row.get('ttl', 0) > int(time.time())]
            last = data.get('LastEvaluatedKey')
            return room.response(200, {'items': sorted(items, key=lambda item: item['updated_at'], reverse=True),
                                       'next_cursor': last['sk'][6:] if last else None})
        if method == 'POST':
            exact(query, set())
            raw = body(event)
            exact(raw, {'request_id', 'title', 'template_id'})
            ident, title = uid(raw.get('request_id')), text(raw.get('title'), 3, 200)
            template_id = room.identifier(raw['template_id']) if 'template_id' in raw else ''
            fingerprint = hashlib.sha256(json.dumps({'title': title, 'template_id': template_id}, sort_keys=True).encode()).hexdigest()
            existing = duplicate(owner, ident, fingerprint)
            if existing:
                return existing
            draft = initial_draft(title, template_id)
            now = int(time.time())
            expires = now + RETENTION_DAYS * 86400
            row = {**video_key(owner, ident), 'kind': 'video', 'owner': owner, 'id': ident,
                   'revision': 0, 'created_at': now, 'updated_at': now, 'expires_at': expires,
                   'ttl': expires, 'retention_days': RETENTION_DAYS, 'fingerprint': fingerprint, 'draft': draft}
            try:
                room.transact([room.put_action(row, 'attribute_not_exists(pk)')])
            except room.Conflict:
                existing = duplicate(owner, ident, fingerprint)
                if existing:
                    return existing
                raise
            return room.response(201, {'video': video_view(row)})
        return room.response(405, {'error': 'Method not allowed'})
    tail = path[len(ROOT) + 1:] if path.startswith(ROOT + '/') else ''
    if not tail or '/' in tail:
        return room.response(404, {'error': 'Not found'})
    ident = uid(tail)
    exact(query, set())
    row = get_video(owner, ident)
    if not row:
        return room.response(404, {'error': 'Video not found'})
    if method == 'GET':
        return room.response(200, {'video': video_view(row)})
    if method == 'PATCH':
        raw = body(event)
        exact(raw, {'revision', 'draft'})
        check_revision(raw, row)
        exact(raw.get('draft'), EDITABLE)
        # DynamoDB returns integers as Decimal; validate their exact JSON type
        # only when submitted, while normalizing trusted stored durations.
        previous = copy.deepcopy(row['draft'])
        for beat in previous['beats']:
            beat['seconds'] = int(beat['seconds'])
        draft = validate_draft({**previous, **raw['draft']})
        changed_content = any(draft[key] != previous[key] for key in EDITABLE - {'stage'})
        rereview = previous['stage'] in {'ready', 'recorded'} and (
            changed_content or draft['stage'] not in {'ready', 'recorded'})
        if rereview:
            if draft['stage'] in {'ready', 'recorded'}:
                draft['stage'] = 'rehearsal'
            for check in draft['checklist']:
                check['done'] = False
        if draft['stage'] in {'ready', 'recorded'}:
            review_ready(draft)
        changed = copy.deepcopy(row)
        changed.update(draft=draft, revision=row['revision'] + 1, updated_at=int(time.time()))
        room.transact([update_action(changed, row['revision'])])
        return room.response(200, {'video': video_view(changed), 'review_required': rereview})
    if method == 'DELETE':
        raw = body(event)
        exact(raw, {'revision', 'confirm'})
        check_revision(raw, row)
        if raw.get('confirm') != 'DELETE ' + ident:
            raise Invalid('Explicit video deletion confirmation required')
        tombstone = {**video_key(owner, ident), 'kind': 'video-deleted', 'id': ident, 'owner': owner,
                     'revision': row['revision'] + 1, 'expires_at': row['expires_at'], 'ttl': row['ttl']}
        room.transact([update_action(tombstone, row['revision'])])
        return room.response(200, {'deleted': True})
    return room.response(405, {'error': 'Method not allowed'})
