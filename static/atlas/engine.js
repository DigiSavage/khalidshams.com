/* SHAMS AI Atlas: deterministic scenario engine.
   Pure functions only: same scenario + same config => same steps. No randomness, no clock, no eval.
   Used by the browser (window.AtlasEngine) and by tests (module.exports). */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.AtlasEngine = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var FLAGS = ["noEvidence", "noNotes", "denyRefund", "toolFailure", "injection", "cancel", "tightBudget"];
  var DESIGNS = ["single", "team"];

  function normalizeConfig(cfg) {
    cfg = cfg || {};
    var out = { design: DESIGNS.indexOf(cfg.design) >= 0 ? cfg.design : "single" };
    FLAGS.forEach(function (f) { out[f] = cfg[f] === true; });
    return out;
  }

  /* The ordered list of step ids for a config. Branching lives here and nowhere else. */
  function plan(cfg) {
    var c = normalizeConfig(cfg);
    var s = ["request", "assemble", "procedure", c.noNotes ? "note_missing" : "note",
             "model_get_order", "authz_read", c.injection ? "exec_get_order_injected" : "exec_get_order"];
    if (c.cancel) return s.concat(["cancel_received"]);
    if (c.design === "team") {
      s.push("work_order", c.noEvidence ? "spec_retrieve_empty" : "spec_retrieve", c.noEvidence ? "spec_return_empty" : "spec_return");
    } else {
      s.push(c.noEvidence ? "retrieve_empty" : "retrieve");
    }
    if (c.noEvidence) return s.concat(["model_escalate", "exec_handoff_owner"]);
    if (c.noNotes) return s.concat(["model_ask_photos", "exec_ask"]);
    if (c.injection) return s.concat(["model_refund_injected", "check_blocked", "exec_handoff_injection"]);
    s.push("model_refund");
    if (c.denyRefund) return s.concat(["authz_refund_deny", "exec_handoff_denied"]);
    s.push("authz_refund_approval", "approval_granted");
    if (c.toolFailure) return s.concat(["exec_refund_error", "exec_refund_retry", "handoff_failure"]);
    return s.concat(["exec_refund", "model_reply", "exec_reply", "verify"]);
  }

  function clone(o) { return JSON.parse(JSON.stringify(o)); }

  /* Expand a plan into full step snapshots, applying the budget. */
  function buildRun(scenario, cfg) {
    var c = normalizeConfig(cfg);
    var limit = c.tightBudget ? scenario.limits.tightSteps : scenario.limits.steps;
    var ids = plan(c), steps = [], used = 0, slots = {}, events = [], attempts = 0;
    for (var i = 0; i < ids.length; i++) {
      var t = scenario.steps[ids[i]];
      if (!t) throw new Error("unknown step " + ids[i]);
      var cost = t.cost || 0;
      if (cost && used + cost > limit) {        // the next unit of work would exceed the budget
        t = scenario.steps.budget_exhausted; ids = ids.slice(0, i).concat(["budget_exhausted"]);
        cost = 0;
      }
      used += cost;
      if (t.tool && t.tool.name === "issue_refund" && t.tool.result) attempts++;
      (t.load || []).forEach(function (k) { slots[k] = true; });
      (t.events || []).forEach(function (e) { events.push({ n: events.length + 1, type: e.type, detail: e.detail, step: steps.length }); });
      var snap = clone(t);
      snap.id = ids[i]; snap.index = steps.length; snap.slots = clone(slots);
      snap.budget = { used: used, limit: limit }; snap.events = events.slice(); snap.refundAttempts = attempts;
      steps.push(snap);
      if (t.outcome) break;
    }
    var last = steps[steps.length - 1];
    return { config: c, steps: steps, outcome: last.outcome || null, limit: limit };
  }

  /* Potential links for n total agents. Topology counts only. */
  function meshLinks(n) { n = Math.floor(n); return n < 2 ? 0 : n * (n - 1) / 2; }
  function starLinks(n) { n = Math.floor(n); return n < 2 ? 0 : n - 1; }

  /* URL state: parse and validate. Unknown values fall back to defaults. */
  function parseState(search, scenario, conceptIds) {
    var p = new URLSearchParams(search || ""), st = {};
    st.design = p.get("design") === "team" ? "team" : "single";
    st.view = p.get("view") === "arch" ? "arch" : "pic";
    var lens = p.get("lens"); st.lens = ["scope", "harden", "anchor", "measure", "sustain"].indexOf(lens) >= 0 ? lens : null;
    var depth = p.get("depth"); st.depth = ["recognize", "understand", "architect"].indexOf(depth) >= 0 ? depth : "recognize";
    var focus = p.get("focus"); st.focus = conceptIds && conceptIds.indexOf(focus) >= 0 ? focus : null;
    var x = (p.get("x") || "").split(",").filter(function (f) { return FLAGS.indexOf(f) >= 0; });
    FLAGS.forEach(function (f) { st[f] = x.indexOf(f) >= 0; });
    var step = parseInt(p.get("step"), 10); st.step = isFinite(step) && step >= 0 && step < 64 ? step : 0;
    return st;
  }
  function serializeState(st) {
    var p = new URLSearchParams();
    if (st.design === "team") p.set("design", "team");
    if (st.view === "arch") p.set("view", "arch");
    if (st.lens) p.set("lens", st.lens);
    if (st.depth && st.depth !== "recognize") p.set("depth", st.depth);
    if (st.focus) p.set("focus", st.focus);
    var x = FLAGS.filter(function (f) { return st[f]; }); if (x.length) p.set("x", x.join(","));
    if (st.step) p.set("step", String(st.step));
    var s = p.toString(); return s ? "?" + s : "";
  }
  return { FLAGS: FLAGS, normalizeConfig: normalizeConfig, plan: plan, buildRun: buildRun,
           meshLinks: meshLinks, starLinks: starLinks, parseState: parseState, serializeState: serializeState };
});
