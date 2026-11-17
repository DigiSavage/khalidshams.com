'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../../static/admin/approval-demo.js'), 'utf8');
const {create} = require('../../static/admin/approval-demo.js');

test('changed amount refuses the old approval and performs zero writes', () => {
  const demo = create();
  ['draft', 'approve', 'change', 'attempt'].forEach(a => demo.dispatch(a));
  const s = demo.snapshot();
  assert.equal(s.receipt.status, 'REFUSED');
  assert.equal(s.receipt.reason, 'PAYLOAD_CHANGED');
  assert.equal(s.receipt.approved_payload.amount_cents, 50000);
  assert.equal(s.receipt.current_payload.amount_cents, 500000);
  assert.equal(s.receipt.simulated_writes, 0);
  assert.equal(s.receipt.money_moved, false);
  assert.deepEqual(s.writes, []);
});
test('missing proposal, missing approval and repeat execution fail closed', () => {
  const demo = create();
  assert.equal(demo.dispatch('attempt').receipt.reason, 'NO_PROPOSAL');
  demo.dispatch('draft');
  assert.equal(demo.dispatch('attempt').receipt.reason, 'NO_APPROVAL');
  demo.dispatch('approve');
  assert.equal(demo.dispatch('attempt').receipt.status, 'SIMULATED_ONLY');
  const s = demo.dispatch('attempt');
  assert.equal(s.receipt.reason, 'APPROVAL_USED');
  assert.equal(s.writes.length, 1);
});
test('new proposal version needs a new approval even when its amount is unchanged', () => {
  const demo = create();
  ['draft', 'approve', 'draft'].forEach(a => demo.dispatch(a));
  assert.equal(demo.dispatch('attempt').receipt.reason, 'PAYLOAD_CHANGED');
  demo.dispatch('approve');
  assert.equal(demo.dispatch('attempt').receipt.status, 'SIMULATED_ONLY');
});
test('fresh approval of revised amount is explicit and snapshots cannot change authority', () => {
  const demo = create();
  ['draft', 'approve', 'change'].forEach(a => demo.dispatch(a));
  const forged = demo.snapshot();
  forged.approval.version = forged.version;
  forged.approval.payload.amount_cents = 500000;
  assert.equal(demo.dispatch('attempt').receipt.status, 'REFUSED');
  demo.dispatch('approve');
  assert.equal(demo.dispatch('attempt').receipt.status, 'SIMULATED_ONLY');
  assert.equal(demo.snapshot().writes[0].payload.amount_cents, 500000);
});
test('reset removes every approval, receipt and synthetic write', () => {
  const demo = create();
  ['draft', 'approve', 'attempt'].forEach(a => demo.dispatch(a));
  assert.deepEqual(demo.dispatch('reset'), create().snapshot());
  assert.throws(() => demo.dispatch('approve'), /Draft/);
  assert.throws(() => demo.dispatch('change'), /Draft/);
  assert.throws(() => demo.dispatch('unknown'), /Unknown/);
});
test('browser model runs with network and storage adapters that throw if touched', () => {
  const forbidden = () => { throw Error('External effect attempted'); };
  const context = vm.createContext({fetch: forbidden, XMLHttpRequest: forbidden,
    localStorage: new Proxy({}, {get: forbidden}), sessionStorage: new Proxy({}, {get: forbidden})});
  vm.runInContext(source, context);
  const demo = context.KSApprovalDemo.create();
  ['draft', 'approve', 'change', 'attempt', 'approve', 'attempt', 'reset'].forEach(a => demo.dispatch(a));
  assert.equal(demo.snapshot().writes.length, 0);
});
