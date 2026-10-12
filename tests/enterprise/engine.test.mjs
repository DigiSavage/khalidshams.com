import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
const require = createRequire(import.meta.url);
const {normalize, design, buildRun, record} = require('../../static/enterprise/engine.js');
const {examples} = JSON.parse(readFileSync(new URL('../../content/enterprise/studio.json', import.meta.url)));
const conditions = ['normal','access','evidence','injection','revoked','changed','timeout','budget'];
const hasWrite = run => run.some(x => ['write.receipt_received','write.unknown'].includes(x.event));

test('reviewed writes cannot execute before an explicit approval, for both examples and every pattern', () => {
  for (const e of examples) for (const pattern of ['fixed','adaptive','specialists']) {
    const config = {example:e.id, pattern, authority:'review'};
    assert.equal(buildRun(config,e).at(-1).state, 'waiting');
    assert.equal(hasWrite(buildRun(config,e)),false);
    assert.equal(hasWrite(buildRun(config,e,'reject')),false);
    const approved = buildRun(config,e,'approve');
    assert.equal(approved.at(-1).event,'outcome.verified');
    assert.ok(approved.findIndex(x=>x.event==='approval.recorded') < approved.findIndex(x=>x.event==='write.receipt_received'));
  }
});
test('read-only designs never write, even with an approval or attempted escalation', () => {
  for (const e of examples) for (const condition of conditions) for (const pattern of ['fixed','adaptive','specialists']) {
    assert.equal(hasWrite(buildRun({authority:'read',condition,pattern},e,'approve')),false);
  }
});
test('revoked authority and changed payload invalidate even an approved operation', () => {
  for (const e of examples) for (const condition of ['revoked','changed']) {
    const run = buildRun({authority:'review',condition},e,'approve');
    assert.ok(run.some(x=>x.event==='approval.recorded'));
    assert.equal(hasWrite(run),false);
    assert.equal(run.at(-1).event, condition==='revoked'?'authorization.revoked':'payload.changed');
  }
});
test('access, evidence and injected-action failures stop before any business write', () => {
  for (const e of examples) for (const condition of ['access','evidence','injection']) for(const authority of ['read','review','bounded']) {
    const run=buildRun({condition,authority},e,'approve');
    assert.equal(hasWrite(run),false);
    if(condition==='access') assert.equal(run.some(x=>x.node==='model'),false);
  }
});
test('a timeout remains unknown rather than reporting success or retrying blindly', () => {
  for (const e of examples) {
    const run=buildRun({condition:'timeout'},e,'approve');
    assert.equal(run.at(-1).state,'unknown');
    assert.equal(run.filter(x=>x.event.startsWith('write.')).length,1);
    assert.equal(run.some(x=>x.event==='outcome.verified'),false);
  }
});
test('consequential writes narrow requested bounded authority to reviewed execution', () => {
  for(const e of examples) {
    const c={authority:'bounded',risk:'consequential'};
    assert.equal(design(c,e).authority,'review');
    assert.equal(buildRun(c,e).at(-1).state,'waiting');
    assert.equal(hasWrite(buildRun(c,e)),false);
  }
});
test('all paths terminate once, stay within the call limit and are deterministic', () => {
  for(const e of examples) for(const condition of conditions) for(const authority of ['read','review','bounded'])
  for(const pattern of ['fixed','adaptive','specialists']) for(const budget of [1,2,3,6,8]) for(const decision of ['pending','approve','reject']) {
    const c={example:e.id,condition,authority,pattern,budget}, run=buildRun(c,e,decision);
    assert.deepEqual(run,buildRun(c,e,decision));
    assert.equal(run.filter(x=>x.terminal).length,1);
    assert.equal(run.at(-1).terminal,true);
    assert.ok(run.every(x=>x.used<=budget));
  }
});
test('architecture patterns produce distinct handoffs, without expanding authority',()=>{
  const e=examples[0];
  const fixed=buildRun({pattern:'fixed'},e), agent=buildRun({pattern:'adaptive'},e), team=buildRun({pattern:'specialists'},e);
  assert.equal(fixed.some(x=>x.event==='specialists.dispatched'),false);
  assert.equal(agent.some(x=>x.event==='agent.observation_received'),true);
  assert.equal(team.filter(x=>x.event.startsWith('specialist.')).length,2);
  assert.equal(hasWrite(team),false);
});
test('invalid values cannot introduce authority or unbounded loops',()=>{
  const c=normalize({authority:'admin',condition:'bypass',budget:Infinity,example:'unknown',risk:'anything'});
  assert.equal(c.authority,'review');assert.equal(c.budget,6);assert.equal(c.example,'documents');
  for(const budget of [-1,0,1.5,'',NaN,9,1e10]) assert.equal(normalize({budget}).budget,6);
});
test('design record preserves unresolved ownership, effective authority and production limits',()=>{
  const text=record({authority:'bounded',risk:'consequential'},examples[0],'','');
  assert.match(text,/UNASSIGNED/);assert.match(text,/Effective authority: ⏸ Write after explicit review/);
  assert.match(text,/UNRESOLVED BEFORE PRODUCTION/);assert.match(text,/No cloud system was deployed/);
});
