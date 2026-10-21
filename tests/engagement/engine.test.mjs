import test from 'node:test';
import assert from 'node:assert/strict';
import {AUDIENCES, CHANGES, parseState, serializeState, analyze} from '../../static/engagement/engine.js';

test('all supported audience and change combinations round trip without changing a decision', () => {
  assert.deepEqual(AUDIENCES, ['executive', 'engineering', 'risk', 'operations']);
  assert.deepEqual(CHANGES, ['baseline', 'autonomy', 'unowned', 'deadline']);
  for (const change of CHANGES) for (const audience of AUDIENCES) {
    const state = {audience, change};
    assert.deepEqual(parseState(serializeState(state)), state);
    assert.deepEqual(analyze(parseState(serializeState(state)).change), analyze(change));
  }
  assert.ok(Object.isFrozen(AUDIENCES));
  assert.ok(Object.isFrozen(CHANGES));
});

test('query parsing accepts only exact allowlisted enum values and excludes unrelated input', () => {
  const defaults = {audience: 'executive', change: 'baseline'};
  for (const query of ['', '?', null, undefined, 9, {}, [], '?audience=EXECUTIVE&change=AUTONOMY',
    '?audience=%3Cscript%3E&change=approve', '?audience=engineering%00&change=deadline%20',
    '?audience=%E0%A4%A&change=%ZZ', '?audience=__proto__&change=constructor',
    '?audience[]=risk&change[]=autonomy']) assert.deepEqual(parseState(query), defaults);
  assert.deepEqual(parseState('?audience=risk&change=not-a-change&token=private'), {audience: 'risk', change: 'baseline'});
  assert.deepEqual(parseState(new URLSearchParams('audience=operations&change=deadline')), {audience: 'operations', change: 'deadline'});
  assert.deepEqual(parseState('?change=autonomy&audience=engine%65ring'), {audience: 'engineering', change: 'autonomy'});
});

test('ambiguous duplicate parameters are not allowed to choose authority or communication state', () => {
  for (const query of [
    '?change=autonomy&change=baseline', '?change=baseline&change=autonomy',
    '?change=autonomy&change=autonomy'
  ]) assert.equal(parseState(query).change, 'baseline');
  assert.deepEqual(parseState('?audience=risk&audience=engineering&change=unowned'), {audience: 'executive', change: 'unowned'});
});

test('serialization drops unknown fields and normalizes invalid states without leaking values', () => {
  assert.equal(serializeState({audience: 'risk', change: 'deadline', owner: 'private', token: 'secret'}), 'audience=risk&change=deadline');
  for (const value of [null, undefined, '', 4, [], {audience: '<svg>', change: 'send-now'}]) {
    assert.equal(serializeState(value), 'audience=executive&change=baseline');
  }
});

test('baseline effort and contingency match the declared planning ranges', () => {
  const plan = analyze('baseline');
  assert.deepEqual(plan.rows, [
    {role: 'Architecture', low: 24, high: 36},
    {role: 'Data', low: 40, high: 64},
    {role: 'Application', low: 48, high: 80},
    {role: 'Quality', low: 32, high: 48},
    {role: 'Release', low: 16, high: 24}
  ]);
  assert.equal(plan.lowHours, 160);
  assert.equal(plan.highHours, 252);
  assert.equal(plan.rate, 150);
  assert.equal(plan.contingency, 0.15);
  assert.equal(plan.lowCost, 27600);
  assert.equal(plan.highCost, 43470);
  assert.match(plan.decision, /named human approves the exact draft/);
});

test('autonomy request adds assurance effort but cannot promote permission', () => {
  const plan = analyze('autonomy');
  assert.equal(plan.status, 'Re-scope required');
  assert.deepEqual(plan.rows.at(-1), {role: 'Assurance and change verification', low: 48, high: 80});
  assert.equal(plan.lowHours, 208);
  assert.equal(plan.highHours, 332);
  assert.equal(plan.lowCost, 35880);
  assert.equal(plan.highCost, 57270);
  assert.match(plan.decision, /does not approve automatic writes/);
  assert.match(plan.scope, /stay excluded until new controls, evidence and owner approval/);
  for (const word of ['approval', 'revocation', 'idempotent', 'timeout']) assert.ok(plan.test.includes(word));
  assert.match(plan.operation, /Stop/);
  assert.match(plan.operation, /Reconcile external effects/);
});

test('missing source ownership holds delivery with unknown totals, not a normal or zero estimate', () => {
  const plan = analyze('unowned');
  assert.equal(plan.status, 'Hold');
  for (const key of ['lowHours', 'highHours', 'lowCost', 'highCost']) assert.equal(plan[key], null);
  assert.deepEqual(plan.rows, [{role: 'Discovery investigation only', low: 24, high: 36}]);
  assert.match(plan.scope, /Investigation only/);
  assert.match(plan.decision, /source owner.*access rights/);
  assert.match(plan.owner, /missing/);
  assert.ok(plan.assumptions.some(item => /not a delivery estimate/.test(item)));
});

test('deadline pressure narrows the scope without promising elapsed time or skipping approval', () => {
  const plan = analyze('deadline');
  assert.equal(plan.status, 'Reduce scope');
  assert.equal(plan.lowHours, 96);
  assert.equal(plan.highHours, 144);
  assert.equal(plan.lowCost, 16560);
  assert.equal(plan.highCost, 24840);
  assert.match(plan.scope, /One team, one approved source and a read-only/);
  assert.match(plan.scope, /No ERP write/);
  assert.match(plan.decision, /not a two-week delivery promise/);
  assert.match(plan.owner, /availability/);
  assert.ok(plan.assumptions.some(item => /reviewer availability and team capacity/.test(item)));
});

test('each change propagates distinct scope, test, operation, ownership and decision records', () => {
  const plans = CHANGES.map(analyze);
  for (const field of ['id', 'label', 'summary', 'decision', 'scope', 'test', 'operation', 'owner']) {
    assert.equal(new Set(plans.map(plan => plan[field])).size, CHANGES.length, field);
    assert.ok(plans.every(plan => typeof plan[field] === 'string' && plan[field].length > 0));
  }
  for (const plan of plans) {
    for (const row of plan.rows) {
      assert.ok(Number.isInteger(row.low) && row.low > 0);
      assert.ok(Number.isInteger(row.high) && row.high >= row.low);
    }
    if (plan.lowHours === null) continue;
    assert.equal(plan.lowHours, plan.rows.reduce((sum, row) => sum + row.low, 0));
    assert.equal(plan.highHours, plan.rows.reduce((sum, row) => sum + row.high, 0));
    assert.equal(plan.lowCost, Math.ceil(plan.lowHours * plan.rate * 115 / 100));
    assert.equal(plan.highCost, Math.ceil(plan.highHours * plan.rate * 115 / 100));
  }
});

test('changes revise the same D-01 decision instead of creating an unrelated approval', () => {
  for (const change of CHANGES) {
    const plan = analyze(change);
    assert.equal(plan.id, change);
    assert.match(plan.decision, /D-01/);
    assert.doesNotMatch(plan.decision, /D-0[2-9]/);
  }
});

test('all records preserve planning limits, human approval and excluded automatic dispatch', () => {
  for (const change of CHANGES) {
    const plan = analyze(change);
    const assumptions = plan.assumptions.join(' ');
    assert.match(assumptions, /not a delivered result, binding quote, funding commitment or release approval/);
    assert.match(assumptions, /named human must approve the exact draft/);
    assert.match(assumptions, /no sending or dispatch capability/);
    assert.match(assumptions, /Cloud usage, software licences, tax and ongoing support are excluded/);
    assert.ok(!['Approved', 'Funded', 'Delivered', 'Complete'].includes(plan.status));
    assert.doesNotMatch(JSON.stringify(plan), /[\u2013\u2014]/);
  }
});

test('analysis is deterministic, rejects unknown branches and does not share mutable results', () => {
  for (const invalid of [null, {}, [], 1, '__proto__', 'approve', 'AUTONOMY']) assert.deepEqual(analyze(invalid), analyze('baseline'));
  const changed = analyze('baseline');
  changed.rows[0].low = 0;
  changed.assumptions.push('Modified by a consumer');
  assert.equal(analyze('baseline').rows[0].low, 24);
  assert.ok(!analyze('baseline').assumptions.includes('Modified by a consumer'));
  for (const change of CHANGES) assert.deepEqual(analyze(change), analyze(change));
});
