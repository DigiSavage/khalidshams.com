// Run: node --test tests/atlas/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const E = require("../../static/atlas/engine.js");
const S = require("../../content/atlas/scenarios/damaged-order.json");

const FLAGS = E.FLAGS;
function allConfigs() {
  const out = [];
  for (const design of ["single", "team"]) for (let m = 0; m < 1 << FLAGS.length; m++) {
    const c = { design }; FLAGS.forEach((f, i) => (c[f] = !!(m & (1 << i)))); out.push(c);
  }
  return out;
}

test("every configuration ends in exactly one known outcome, on the last step", () => {
  for (const c of allConfigs()) {
    const r = E.buildRun(S, c);
    assert.ok(r.outcome && S.outcomes[r.outcome], JSON.stringify(c));
    const withOutcome = r.steps.filter((s) => s.outcome);
    assert.equal(withOutcome.length, 1, JSON.stringify(c));
    assert.equal(r.steps.at(-1).outcome, r.outcome);
  }
});

test("all seven outcomes are reachable", () => {
  const seen = new Set(allConfigs().map((c) => E.buildRun(S, c).outcome));
  for (const k of ["completed", "waiting_input", "denied", "blocked", "cancelled", "budget", "failed"]) assert.ok(seen.has(k), k);
});

test("the default run completes only after the application verifies the goal", () => {
  const r = E.buildRun(S, {});
  assert.equal(r.outcome, "completed");
  assert.equal(r.steps.at(-1).id, "verify");
  assert.ok(r.steps.at(-1).events.some((e) => e.type === "goal.verified"));
  // end_turn appears, but success is the verification event, not the stop reason
  const endTurn = r.steps.at(-1).events.find((e) => e.detail.includes("end_turn"));
  assert.ok(endTurn);
});

test("a denied operation never reaches execution", () => {
  for (const c of allConfigs().filter((c) => c.denyRefund && !c.cancel && !c.noEvidence && !c.noNotes && !c.injection)) {
    const r = E.buildRun(S, c);
    if (r.outcome === "budget") continue;
    const ev = r.steps.at(-1).events;
    const denyAt = ev.findIndex((e) => e.type === "authz.denied");
    assert.ok(denyAt >= 0, JSON.stringify(c));
    assert.ok(!ev.some((e) => e.type === "tool.executed" && e.detail.startsWith("issue_refund")), "refund executed after denial");
    assert.ok(!r.steps.some((s) => s.slots.refund), "refund slot filled after denial");
    assert.equal(r.outcome, "denied");
  }
});

test("retries are bounded by maxAttempts and then stop", () => {
  for (const c of allConfigs().filter((c) => c.toolFailure)) {
    const r = E.buildRun(S, c);
    const attempts = r.steps.at(-1).events.filter((e) => e.type === "tool.error").length;
    assert.ok(attempts <= S.limits.maxAttempts, `${attempts} attempts`);
    if (!c.cancel && !c.noEvidence && !c.noNotes && !c.denyRefund && !c.injection && !c.tightBudget) {
      assert.equal(attempts, S.limits.maxAttempts);
      assert.equal(r.outcome, "failed");
    }
  }
});

test("the budget is never exceeded", () => {
  for (const c of allConfigs()) {
    const r = E.buildRun(S, c);
    for (const s of r.steps) assert.ok(s.budget.used <= s.budget.limit, JSON.stringify(c));
  }
  assert.equal(E.buildRun(S, { tightBudget: true }).outcome, "budget");
});

test("no refund without approval when policy requires it", () => {
  for (const c of allConfigs()) {
    const ev = E.buildRun(S, c).steps.at(-1).events;
    const exec = ev.findIndex((e) => e.type === "tool.executed" && e.detail.startsWith("issue_refund"));
    if (exec < 0) continue;
    const appr = ev.findIndex((e) => e.type === "approval.granted");
    assert.ok(appr >= 0 && appr < exec, JSON.stringify(c));
  }
});

test("the specialist gets a bounded work order and never executes the refund", () => {
  const r = E.buildRun(S, { design: "team" });
  const wo = r.steps.find((s) => s.id === "work_order").workOrder;
  for (const x of ["conversation history", "credentials"]) assert.ok(wo.notGiven.includes(x));
  const spec = r.steps.filter((s) => s.actor === "specialist");
  assert.ok(spec.length >= 2);
  for (const s of spec) assert.ok(!s.tool || s.tool.name === "retrieve_policy");
});

test("missing evidence or notes never produce a refund proposal", () => {
  for (const c of [{ noEvidence: true }, { noNotes: true }, { design: "team", noEvidence: true }]) {
    const r = E.buildRun(S, c);
    assert.equal(r.outcome, "waiting_input");
    assert.ok(!r.steps.some((s) => s.tool && s.tool.name === "issue_refund"));
  }
});

test("runs are deterministic", () => {
  for (const c of allConfigs().slice(0, 20)) assert.deepEqual(E.buildRun(S, c), E.buildRun(S, c));
});

test("coordination counts: n(n-1)/2 versus n-1", () => {
  assert.equal(E.meshLinks(5), 10); assert.equal(E.starLinks(5), 4);
  assert.equal(E.meshLinks(2), 1); assert.equal(E.starLinks(2), 1);
  assert.equal(E.meshLinks(1), 0); assert.equal(E.starLinks(10), 9); assert.equal(E.meshLinks(10), 45);
});

test("URL state validates input and round-trips", () => {
  const ids = ["agent", "mcp"];
  const bad = E.parseState("?design=evil&view=x&lens=nope&depth=deep&focus=<script>&x=noEvidence,rm-rf&step=-3", S, ids);
  assert.equal(bad.design, "single"); assert.equal(bad.view, "pic"); assert.equal(bad.lens, null);
  assert.equal(bad.depth, "recognize"); assert.equal(bad.focus, null); assert.equal(bad.step, 0);
  assert.equal(bad.noEvidence, true); assert.equal(bad.denyRefund, false);
  const good = { design: "team", view: "arch", lens: "harden", depth: "architect", focus: "mcp", noEvidence: false, noNotes: true,
                 denyRefund: false, toolFailure: false, injection: true, cancel: false, tightBudget: false, step: 7 };
  assert.deepEqual(E.parseState(E.serializeState(good), S, ids), good);
});

test("planted instructions are blocked by the check before any permission is asked", () => {
  for (const c of allConfigs().filter((c) => c.injection)) {
    const r = E.buildRun(S, c);
    const ev = r.steps.at(-1).events;
    assert.ok(!ev.some((e) => e.type === "tool.executed" && e.detail.startsWith("issue_refund")), "refund executed: " + JSON.stringify(c));
    assert.ok(!ev.some((e) => e.type.startsWith("authz.") && e.detail.includes("op=issue_refund")), "authz asked: " + JSON.stringify(c));
    if (!c.cancel && !c.noEvidence && !c.noNotes && !c.tightBudget) {
      assert.equal(r.outcome, "blocked", JSON.stringify(c));
      const blockAt = ev.findIndex((e) => e.type === "check.blocked");
      const propAt = ev.findIndex((e) => e.type === "tool.proposed" && e.detail.includes("amount=500.00"));
      assert.ok(propAt >= 0 && blockAt > propAt);
    }
  }
});

test("every refund the gate sees has passed the argument check first", () => {
  for (const c of allConfigs()) {
    const ev = E.buildRun(S, c).steps.at(-1).events;
    const gateAt = ev.findIndex((e) => e.type.startsWith("authz.") && e.detail.includes("op=issue_refund"));
    if (gateAt < 0) continue;
    const chkAt = ev.findIndex((e) => e.type === "check.passed");
    assert.ok(chkAt >= 0 && chkAt < gateAt, JSON.stringify(c));
  }
});

/* ---------- the second lesson: How a model is made (declarative plan) ---------- */
const M = require("../../content/atlas/scenarios/model-making.json");
const MF = E.flagsOf(M);
function modelConfigs() {
  const out = [];
  for (let m = 0; m < 1 << MF.length; m++) { const c = {}; MF.forEach((f, i) => (c[f] = !!(m & (1 << i)))); out.push(c); }
  return out;
}

test("model lesson: every condition set ends in one known outcome", () => {
  assert.deepEqual(MF, ["skewData", "overfit", "skipAlign"]);
  for (const c of modelConfigs()) {
    const r = E.buildRun(M, c);
    assert.ok(M.outcomes[r.outcome], JSON.stringify(c));
    assert.equal(r.steps.filter((s) => s.outcome).length, 1);
  }
});

test("model lesson: release happens only when every evaluation criterion passes", () => {
  for (const c of modelConfigs()) {
    const r = E.buildRun(M, c), ev = r.steps.at(-1).events;
    const anyFlag = MF.some((f) => c[f]);
    assert.equal(r.outcome, anyFlag ? "held_back" : "released", JSON.stringify(c));
    if (r.outcome === "released") assert.ok(ev.findIndex((e) => e.type === "eval.passed") < ev.findIndex((e) => e.type === "release.pinned"));
    else assert.ok(!ev.some((e) => e.type === "release.pinned"));
  }
});

test("model lesson: training comes before fine-tuning, which comes before evaluation", () => {
  const ids = E.buildRun(M, {}).steps.map((s) => s.id);
  for (const [a, b] of [["predict", "backprop"], ["backprop", "checkpoint"], ["checkpoint", "finetune"], ["finetune", "align"], ["align", "evaluate"], ["evaluate", "release"]])
    assert.ok(ids.indexOf(a) < ids.indexOf(b), `${a} before ${b}`);
});

test("model lesson: URL state keeps its own conditions and drops the flagship's", () => {
  const st = E.parseState("?x=overfit,denyRefund&step=4", M, ["training"]);
  assert.equal(st.overfit, true); assert.equal(st.denyRefund, undefined);
  assert.equal(E.serializeState(Object.assign({}, st, { step: 4 }), M), "?x=overfit&step=4");
});
