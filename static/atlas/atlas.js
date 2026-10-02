/* SHAMS AI Atlas: interaction layer for /learn/atlas/.
   Progressive enhancement: the page is readable without this file (picture + text version).
   All scenario logic is in engine.js (pure, tested). This file only renders state.
   No eval, no innerHTML with untrusted input: registry text is escaped before insertion. */
(function () {
  "use strict";
  var root = document.getElementById("atlas"), dataEl = document.getElementById("atlas-data");
  if (!root || !dataEl || !window.AtlasEngine) return;
  var E = window.AtlasEngine, DATA = JSON.parse(dataEl.textContent);
  var SC = DATA.scenario, CON = DATA.concepts, SRC = {}, CBY = {};
  DATA.sources.sources.forEach(function (s) { SRC[s.id] = s; });
  CON.concepts.forEach(function (c) { CBY[c.id] = c; });
  var LAYER = {}; CON.layers.forEach(function (l) { LAYER[l.id] = l; });
  var LENS = {}; CON.shams.forEach(function (m) { LENS[m.id] = m; });
  var svg = document.getElementById("atlas-scene"), wrap = document.getElementById("atl-svgwrap");
  var $ = function (id) { return document.getElementById(id); };
  var qa = function (sel, el) { return [].slice.call((el || root).querySelectorAll(sel)); };
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var mobile = function () { return window.matchMedia("(max-width:760px)").matches; };
  root.classList.add("js");

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  /* ---------------- state ---------------- */
  var conceptIds = CON.concepts.map(function (c) { return c.id; });
  var st = E.parseState(location.search, SC, conceptIds);
  var run = null, idx = -1, playing = null, tab = "step", whole = false;
  var VB0 = { x: 0, y: 22, w: 1280, h: 772 }, vb = Object.assign({}, VB0);

  function cfg() { var c = { design: st.design }; E.FLAGS.forEach(function (f) { c[f] = st[f]; }); return c; }
  function rebuild() { run = E.buildRun(SC, cfg()); }

  /* ---------------- progress (local only, never in URLs) ---------------- */
  var PKEY = "ks-atlas-v1";
  var prog = { visited: [], understood: [], passed: [] };
  try {
    var raw = JSON.parse(localStorage.getItem(PKEY) || "null");
    if (raw && Array.isArray(raw.visited) && Array.isArray(raw.understood) && Array.isArray(raw.passed)) prog = raw;
  } catch (e) { prog = { visited: [], understood: [], passed: [] }; }
  var learned = [];   // the Learn map's existing self-report key, read only
  try { learned = JSON.parse(localStorage.getItem("ks-learn") || "[]"); if (!Array.isArray(learned)) learned = []; } catch (e) { learned = []; }
  function saveProg() { try { localStorage.setItem(PKEY, JSON.stringify(prog)); } catch (e) {} }
  function mark(list, id) { if (prog[list].indexOf(id) < 0) { prog[list].push(id); saveProg(); } }
  function understood(c) { return prog.understood.indexOf(c.id) >= 0 || (c.mapId && learned.indexOf(c.mapId) >= 0); }

  /* ---------------- URL state ---------------- */
  function urlState(push) {
    var s = Object.assign({}, st, { step: idx < 0 ? 0 : idx + 1 });
    var url = location.pathname + E.serializeState(s) + location.hash;
    try { (push ? history.pushState : history.replaceState).call(history, null, "", url); } catch (e) {}
  }
  window.addEventListener("popstate", function () {
    st = E.parseState(location.search, SC, conceptIds); rebuild();
    idx = Math.min(st.step, run.steps.length) - 1; syncControls(); render(false);
  });

  /* ---------------- scene helpers ---------------- */
  function obj(id) { return svg.querySelector('.obj[data-o="' + id + '"]'); }
  function objsFor(concept) { return qa('.obj[data-c="' + concept + '"]', svg); }
  function bbox(els) {
    var b = null;
    els.forEach(function (el) { if (!el) return; try { var r = el.getBBox(); if (!r.width) return;
      b = b ? { x: Math.min(b.x, r.x), y: Math.min(b.y, r.y), x2: Math.max(b.x2, r.x + r.width), y2: Math.max(b.y2, r.y + r.height) }
            : { x: r.x, y: r.y, x2: r.x + r.width, y2: r.y + r.height }; } catch (e) {} });
    return b;
  }
  function setVB(v) { vb = v; svg.setAttribute("viewBox", [v.x, v.y, v.w, v.h].map(Math.round).join(" ")); }
  function camera() {
    if (!mobile() || whole) { if (!zoomed) setVB(VB0); return; }
    var step = idx >= 0 ? run.steps[idx] : null;
    var els = step ? step.focus.map(obj) : [obj("agent"), obj("context"), obj("model")];
    if (st.focus && !step) els = objsFor(st.focus);
    var b = bbox(els); if (!b) { setVB(VB0); return; }
    var pad = 40, w = Math.max(b.x2 - b.x + pad * 2, 520), h = Math.max(b.y2 - b.y + pad * 2, 420);
    var ar = wrap.clientWidth / Math.max(wrap.clientHeight, 1) || 0.9;
    if (w / h < ar) w = h * ar; else h = w / ar;
    var cx = (b.x + b.x2) / 2, cy = (b.y + b.y2) / 2;
    setVB({ x: Math.max(-40, Math.min(cx - w / 2, 1320 - w)), y: Math.max(-20, Math.min(cy - h / 2, 820 - h)), w: w, h: h });
  }
  var zoomed = false;
  function zoom(f) {
    zoomed = true; var w = vb.w * f, h = vb.h * f, cx = vb.x + vb.w / 2, cy = vb.y + vb.h / 2;
    w = Math.max(300, Math.min(w, 1600)); h = w * (vb.h / vb.w);
    setVB({ x: cx - w / 2, y: cy - h / 2, w: w, h: h });
  }
  function fit() { zoomed = false; whole = false; $("atl-whole").setAttribute("aria-pressed", "false"); setVB(VB0); camera(); }

  function selBox() {
    var old = svg.querySelector(".sel-box"); if (old) old.remove();
    if (!st.focus) return;
    var b = bbox(objsFor(st.focus)); if (!b) return;
    var r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    r.setAttribute("class", "sel-box"); r.setAttribute("x", b.x - 8); r.setAttribute("y", b.y - 8);
    r.setAttribute("width", b.x2 - b.x + 16); r.setAttribute("height", b.y2 - b.y + 16); r.setAttribute("rx", 8);
    svg.appendChild(r);
  }
  function lensBadges() {
    qa(".lens-badge", svg).forEach(function (n) { n.remove(); });
    if (!st.lens) return;
    var letter = LENS[st.lens].letter;
    qa(".obj.lens-hit", svg).forEach(function (o) {
      var b = bbox([o]); if (!b) return;
      var g = document.createElementNS("http://www.w3.org/2000/svg", "g"); g.setAttribute("class", "lens-badge");
      g.innerHTML = '<circle cx="' + (b.x + 2) + '" cy="' + (b.y + 2) + '" r="12"></circle><text x="' + (b.x + 2) + '" y="' + (b.y + 8.5) + '" text-anchor="middle">' + letter + "</text>";
      svg.appendChild(g);
    });
  }

  /* courier: a small document travels along the step's first information edge (decorative; the slot state carries the meaning) */
  var courierTimer = null;
  function courier(step) {
    var c = svg.querySelector(".courier"); if (!c) return;
    c.classList.remove("go"); if (courierTimer) cancelAnimationFrame(courierTimer);
    if (reduced || !step) return;
    var eid = null;
    step.edges.forEach(function (e) { var g = svg.querySelector('.edge[data-e="' + e + '"]'); if (!eid && g && (g.classList.contains("e-data") || step.edges.length === 1)) eid = e; });
    if (!eid) return;
    var p = svg.querySelector('.edge[data-e="' + eid + '"] .ep'); if (!p) return;
    var L = p.getTotalLength(), t0 = null; c.classList.add("go");
    function f(ts) { if (!t0) t0 = ts; var k = Math.min(1, (ts - t0) / 1100), pt = p.getPointAtLength(L * (1 - Math.pow(1 - k, 2)));
      c.setAttribute("transform", "translate(" + pt.x + " " + pt.y + ")"); if (k < 1) courierTimer = requestAnimationFrame(f); else setTimeout(function () { c.classList.remove("go"); }, 400); }
    courierTimer = requestAnimationFrame(f);
  }

  /* ---------------- render ---------------- */
  var lastIdx = -1;
  function render(animate) {
    var step = idx >= 0 ? run.steps[idx] : null;
    root.classList.toggle("has-step", !!step);
    root.classList.toggle("is-arch", st.view === "arch");
    root.classList.toggle("is-team", st.design === "team");
    root.classList.toggle("lens-on", !!st.lens);
    // objects
    qa(".obj", svg).forEach(function (o) {
      var id = o.getAttribute("data-o");
      o.classList.toggle("focus", !!step && step.focus.indexOf(id) >= 0);
      o.classList.toggle("actor", !!step && step.actor === id);
      o.classList.toggle("keep", ["requester", "owner", "approver"].indexOf(id) >= 0 && !step);
      o.classList.toggle("muted", st.design !== "team" && (id === "specialist" || id === "coordinator"));
      o.classList.toggle("lens-hit", !!st.lens && (o.getAttribute("data-lens") || "").split(" ").indexOf(st.lens) >= 0);
    });
    // edges
    var deniedNow = step && step.deny;
    qa(".edge", svg).forEach(function (g) {
      var on = !!step && step.edges.indexOf(g.getAttribute("data-e")) >= 0;
      g.classList.toggle("on", on); g.classList.toggle("denied", !!(on && deniedNow && g.classList.contains("e-ctrl")));
    });
    // slots
    var slots = step ? step.slots : {}, fresh = step ? step.load : [];
    qa(".slot", svg).forEach(function (s) { var k = s.getAttribute("data-slot"); s.classList.toggle("filled", !!slots[k]); s.classList.toggle("fresh", fresh.indexOf(k) >= 0); });
    // gates and approval from the event log
    var evs = step ? step.events : [];
    function gate(id, op) {
      var m = svg.querySelector('.obj[data-o="' + id + '"] .g-mark'); if (!m) return;
      var txt = "", cls = "";
      evs.forEach(function (e) { if (e.detail.indexOf("op=" + op) === 0 || e.detail.indexOf("op=" + op + " ") >= 0) {
        if (e.type === "authz.allowed") { txt = "✓"; cls = "allowed"; }
        if (e.type === "authz.denied") { txt = "✕"; cls = "denied"; }
        if (e.type === "authz.approval_required") { txt = "⏸"; cls = "approval"; } } });
      if (cls === "approval" && evs.some(function (e) { return e.type === "approval.granted"; })) { txt = "✓"; cls = "allowed"; }
      m.textContent = txt; m.setAttribute("class", "g-mark " + cls);
    }
    gate("gate_orders", "get_order"); gate("gate_refunds", "issue_refund"); gate("gate_msg", "send_message");
    var stamp = svg.querySelector(".stamp-t");
    if (stamp) { var granted = evs.some(function (e) { return e.type === "approval.granted"; }), req = evs.some(function (e) { return e.type === "authz.approval_required"; });
      stamp.textContent = granted ? "approved" : req ? "reviewing" : "awaiting"; stamp.setAttribute("class", "stamp-t" + (granted ? " ok" : "")); }
    // model proposal + tokens
    var prop = svg.querySelector(".proposal");
    var mstep = step && step.actor === "model" && step.tool ? step.tool : null;
    if (prop) prop.textContent = mstep ? "→ " + mstep.name + "(…)" : (step && step.id === "verify" ? "end_turn" : "");
    qa(".tokens rect", svg).forEach(function (r, i) { r.classList.toggle("lit", !!(step && (step.actor === "model" || step.id === "verify"))); });
    // specialist work order / result
    var wo = svg.querySelector(".wo-lines"), rs = svg.querySelector(".res-lines");
    var ids = step ? run.steps.slice(0, idx + 1).map(function (s) { return s.id; }) : [];
    if (wo) wo.classList.toggle("lit", ids.indexOf("work_order") >= 0);
    if (rs) rs.classList.toggle("lit", ids.indexOf("spec_return") >= 0 || ids.indexOf("spec_return_empty") >= 0);
    // goal criteria
    var done = step && step.outcome === "completed";
    qa(".crit rect", svg).forEach(function (r) { r.classList.toggle("done", !!done); });
    // budget
    var bt = svg.querySelector(".bud-t"), nd = svg.querySelector(".needle");
    var used = step ? step.budget.used : 0, lim = run.limit;
    if (bt) bt.textContent = used + "/" + lim;
    if (nd) { var a = Math.PI * (1 - Math.min(1, used / lim)); nd.setAttribute("d", "M826 552 L" + (826 + 22 * Math.cos(a)).toFixed(1) + " " + (552 - 22 * Math.sin(a)).toFixed(1)); }
    // event trail ticks
    var tk = svg.querySelector(".ticks"), last = svg.querySelector(".trail-last");
    if (tk) {
      var html = "", n = evs.length;
      evs.forEach(function (e, i) { var x = 222 + i * Math.min(38, 1020 / Math.max(n, 1)); var cls = /denied|error|exhausted|cancel/.test(e.type) ? "tick deny" : /verified|allowed|granted/.test(e.type) ? "tick ok" : "tick";
        html += '<rect class="' + cls + '" x="' + x.toFixed(1) + '" y="755" width="4" height="14" rx="1"></rect>'; });
      tk.innerHTML = html;
    }
    if (last) last.textContent = evs.length ? evs[evs.length - 1].type + "  " + evs[evs.length - 1].detail : "";
    // narration
    var o = step && step.outcome ? SC.outcomes[step.outcome] : null;
    $("atl-phase").textContent = step ? step.phase + (st.design === "team" ? " · coordinator design" : " · one-agent design") : "Ready";
    $("atl-title").textContent = step ? step.title : 'Press "Follow the request" to start.';
    $("atl-text").textContent = step ? step.narration : "One customer request, followed through an example AI system: who owns it, what goes on the desk, what the model proposes, what is checked before anything happens, and how the run ends.";
    var out = $("atl-outcome");
    if (o) { out.hidden = false; out.setAttribute("data-kind", o.kind); out.innerHTML = "<b>Run ended: " + esc(o.label) + ".</b> " + esc(o.text); }
    else out.hidden = true;
    $("atl-stepno").textContent = step ? "Step " + (idx + 1) + " of " + run.steps.length : "Ready";
    $("atl-prev").disabled = idx < 0; $("atl-next").disabled = idx >= run.steps.length - 1;
    $("atl-follow").textContent = idx < 0 ? "Follow the request" : idx >= run.steps.length - 1 ? "Replay" : "Next step";
    // rail
    qa(".rl-c").forEach(function (b) { var c = b.getAttribute("data-c"); b.classList.toggle("in-step", !!step && step.concepts.indexOf(c) >= 0); b.setAttribute("aria-current", st.focus === c ? "true" : "false"); });
    selBox(); lensBadges(); camera();
    if (animate && idx !== lastIdx) courier(step);
    lastIdx = idx;
    renderInspector(step);
    if (step) step.concepts.forEach(function (c) { mark("visited", c); });
  }

  /* ---------------- inspector ---------------- */
  function kv(obj) { return '<dl class="in-kv">' + Object.keys(obj).map(function (k) { var v = obj[k]; return "<dt>" + esc(k) + "</dt><dd>" + esc(Array.isArray(v) ? v.join(", ") : v) + "</dd>"; }).join("") + "</dl>"; }
  function renderStep(step) {
    var p = $("pane-step");
    if (!step) { p.innerHTML = '<p class="in-empty">Start the walkthrough to inspect each step: what is on the desk, the tool call and its arguments, what came back, where the evidence came from, and the events recorded.</p>' + coordHtml(); bindCoord(); return; }
    var h = '<p class="in-h">' + esc(step.phase) + " · step " + (idx + 1) + " of " + run.steps.length + "</p>" +
            '<p class="in-title">' + esc(step.title) + "</p><p class=\"in-p\">" + esc(step.narration) + "</p>";
    var onDesk = SC.slots.filter(function (s) { return step.slots[s.id]; }).map(function (s) { return '<span class="in-chip">' + esc(s.label) + "</span>"; });
    h += '<p class="in-h">On the desk for the next model call</p><div class="in-chips">' + (onDesk.join("") || '<span class="in-chip">nothing yet</span>') + "</div>";
    if (step.tool) {
      h += '<p class="in-h">' + (step.tool.result ? "Tool call executed" : "Proposed tool call (not executed by the model)") + "</p>";
      h += '<pre class="in-code">' + esc(step.tool.name + "(" + JSON.stringify(step.tool.args, null, 1).replace(/\n\s*/g, " ") + ")") + "</pre>";
      if (step.tool.result) h += '<p class="in-h">Returned</p><pre class="in-code">' + esc(JSON.stringify(step.tool.result, null, 1)) + "</pre>";
    }
    if (step.workOrder) {
      var w = step.workOrder;
      h += '<p class="in-h">Work order</p><div class="in-wo"><div><b>Task:</b> ' + esc(w.task) + "</div><div><b>Given:</b> " + esc(w.given.join("; ")) + '</div><div class="no"><b>Not given:</b> ' + esc(w.notGiven.join("; ")) + "</div><div><b>Returns:</b> " + esc(w.returns) + "</div></div>";
    }
    if (step.result) h += '<p class="in-h">Structured result</p><pre class="in-code">' + esc(JSON.stringify(step.result, null, 1)) + "</pre>";
    if (step.evidence) h += '<p class="in-h">Evidence and provenance</p><blockquote class="in-quote">' + esc(step.evidence.text) + '</blockquote><p class="in-prov">' + esc(step.evidence.source) + " · owner: " + esc(step.evidence.owner) + " · reviewed " + esc(step.evidence.reviewed) + " · synthetic</p>";
    h += '<p class="in-h">Run budget</p><p class="in-p">' + step.budget.used + " of " + step.budget.limit + " model calls and tool executions used.</p>";
    var n0 = idx > 0 ? run.steps[idx - 1].events.length : 0;
    h += '<p class="in-h">Event trail (synthetic, newest last)</p><ol class="in-ev">' + step.events.slice(-8).map(function (e) {
      var c = /denied|error|exhausted|cancel/.test(e.type) ? "t-deny" : /verified|allowed|granted/.test(e.type) ? "t-ok" : "";
      return '<li class="' + (e.n > n0 ? "new" : "") + '"><span class="n">' + e.n + '</span><span class="' + c + '">' + esc(e.type) + " " + esc(e.detail) + "</span></li>"; }).join("") + "</ol>";
    h += '<p class="in-h">Concepts in this step</p><div class="in-btns">' + step.concepts.map(function (c) { return '<button type="button" class="tb-b" data-go="' + c + '">' + esc(CBY[c].title) + "</button>"; }).join("") + "</div>";
    if (step.outcome) h += '<p class="in-h">Outcome</p><p class="in-p"><b>' + esc(SC.outcomes[step.outcome].label) + ".</b> " + esc(SC.outcomes[step.outcome].text) + "</p>";
    if (st.design === "team") h += coordHtml();
    p.innerHTML = h; bindGo(p); bindCoord();
  }
  function coordHtml() {
    return '<div class="coord" id="atl-coord"><p class="in-h">Coordination arithmetic</p>' +
      '<label class="in-p" for="atl-n">Total agents: <b id="atl-nv">5</b></label><input type="range" id="atl-n" min="2" max="10" value="5">' +
      '<div class="nums"><div><b id="atl-mesh">10</b><span>potential links, full mesh n(n−1)/2</span></div><div><b id="atl-star">4</b><span>potential links, coordinator star n−1</span></div></div>' +
      "<p>Potential links describe topology only. They are not message counts, prices, speed or quality. This lesson has 2 agents: 1 link either way, and 2 handoffs (work order out, result back).</p></div>";
  }
  function bindCoord() {
    var r = $("atl-n"); if (!r) return;
    var upd = function () { var n = +r.value; $("atl-nv").textContent = n; $("atl-mesh").textContent = E.meshLinks(n); $("atl-star").textContent = E.starLinks(n); };
    r.addEventListener("input", upd); upd();
  }
  function bindGo(el) { qa("[data-go]", el).forEach(function (b) { b.addEventListener("click", function () { select(b.getAttribute("data-go"), true); }); }); }

  function renderConcept() {
    var p = $("pane-concept"), c = st.focus ? CBY[st.focus] : null;
    var opts = '<label class="in-h" for="atl-csel">Choose a concept</label><div class="in-sel"><select id="atl-csel"><option value="">Select…</option>' +
      CON.concepts.map(function (x) { return '<option value="' + x.id + '"' + (c && c.id === x.id ? " selected" : "") + ">" + esc(x.title) + "</option>"; }).join("") + "</select></div>";
    if (!c) { p.innerHTML = opts + '<p class="in-empty">Select anything in the scene, or a concept in the list, to see what it does at three depths and where the analogy stops.</p>'; bindSel(); return; }
    var d = st.depth, txt = c[d];
    var layers = '<span class="in-chip">Taught under: ' + esc(LAYER[c.primaryLayer].title) + "</span>" + c.relatedLayers.map(function (l) { return '<span class="in-chip">Connects to: ' + esc(LAYER[l].title) + "</span>"; }).join("");
    var lens = c.shams.map(function (m) { return '<span class="in-chip lens">' + esc(LENS[m].letter + " · " + LENS[m].title) + "</span>"; }).join("");
    var pre = c.prerequisites.length ? '<p class="in-h">◇ Learn first (a learning link, not a runtime call)</p><div class="in-btns">' + c.prerequisites.map(function (x) { return '<button type="button" class="tb-b" data-go="' + x + '">' + esc(CBY[x].title) + "</button>"; }).join("") + "</div>" : "";
    var srcs = c.sources.map(function (s) { var x = SRC[s]; return '<li><a href="' + esc(x.url) + '" rel="noopener">' + esc(x.title) + "</a>, " + esc(x.publisher) + ". Checked " + esc(x.checked) + ".</li>"; }).join("");
    var status = { "source-checked": "Checked against the sources below", "editorial": "Teaching judgment, not a sourced claim", "needs-review": "Needs further review" }[c.status];
    var h = opts + '<p class="in-title">' + esc(c.title) + '</p><div class="in-chips">' + layers + "</div>" +
      '<div class="seg depth" role="group" aria-label="Explanation depth">' + ["recognize", "understand", "architect"].map(function (k) {
        return '<button type="button" class="seg-b" data-depth="' + k + '" aria-pressed="' + (d === k) + '">' + { recognize: "Recognize it", understand: "Understand it", architect: "Architect it" }[k] + "</button>"; }).join("") + "</div>" +
      '<p class="in-p">' + esc(txt) + "</p>" +
      '<p class="in-h">In the picture</p><p class="in-p">' + esc(c.picture) + "</p>" +
      '<div class="in-limit"><b>Where the analogy stops.</b> ' + esc(c.metaphorLimit) + "</div>" +
      '<p class="in-h">In this scenario</p><p class="in-p">' + esc(c.example) + "</p>" +
      '<p class="in-h">Typical failure</p><p class="in-p">' + esc(c.failureMode) + "</p>" +
      '<p class="in-h">Boundary</p><p class="in-p">' + esc(c.boundaryNotes) + "</p>" +
      '<p class="in-h">SHAMS moves</p><div class="in-chips">' + lens + "</div>" + pre +
      '<p class="in-h">Sources</p><p class="in-status ' + c.status + '">' + esc(status) + "</p>" + (srcs ? '<ul class="in-src">' + srcs + "</ul>" : "") +
      (c.mapId ? '<p class="in-p"><a href="/learn/?idea=' + esc(c.mapId) + '#map">Find it on the Learn map</a></p>' : "") +
      '<div class="in-btns"><button type="button" class="tb-b" id="atl-got" aria-pressed="' + understood(c) + '">' + (understood(c) ? "Marked as understood" : "I understand this") + "</button></div>" +
      '<p class="prog">Self-reported understanding is not a passed check. ' + (prog.passed.indexOf(c.id) >= 0 ? "You have passed a check that covers this concept." : "Try the check tab to test the distinction.") + "</p>";
    p.innerHTML = h; bindSel(); bindGo(p);
    qa("[data-depth]", p).forEach(function (b) { b.addEventListener("click", function () { st.depth = b.getAttribute("data-depth"); urlState(false); renderConcept(); }); });
    $("atl-got").addEventListener("click", function () { mark("understood", c.id); renderConcept(); });
  }
  function bindSel() { var s = $("atl-csel"); if (s) s.addEventListener("change", function () { if (s.value) select(s.value, true); }); }

  function renderChecks() {
    var p = $("pane-check");
    p.innerHTML = '<p class="in-p">Three short checks on the distinctions that matter most. Passing one is recorded on this device only.</p>' +
      DATA.checks.checks.map(function (ch) {
        var passed = ch.concepts.every(function (c) { return prog.passed.indexOf(c) >= 0; });
        return '<div class="chk" data-ch="' + ch.id + '"><p class="q">' + esc(ch.q) + "</p>" + ch.options.map(function (o, i) {
          return '<button type="button" data-i="' + i + '">' + esc(o.t) + "</button>"; }).join("") + '<p class="why" aria-live="polite">' + (passed ? "Passed before on this device." : "") + "</p></div>"; }).join("") +
      '<p class="prog">Visited ' + prog.visited.length + " · marked understood " + prog.understood.length + " · passed checks cover " + prog.passed.length + " concepts.</p>";
    qa(".chk", p).forEach(function (box) {
      var ch = DATA.checks.checks.filter(function (x) { return x.id === box.getAttribute("data-ch"); })[0];
      qa("button", box).forEach(function (b) { b.addEventListener("click", function () {
        var o = ch.options[+b.getAttribute("data-i")];
        qa("button", box).forEach(function (x) { x.classList.remove("right", "wrong"); });
        b.classList.add(o.ok ? "right" : "wrong"); box.querySelector(".why").textContent = o.why;
        if (o.ok) ch.concepts.forEach(function (c) { mark("passed", c); });
      }); });
    });
  }

  function renderLens() {
    var lp = $("atl-lenspanel");
    if (!st.lens) { lp.hidden = true; return; }
    var m = LENS[st.lens], hits = qa(".obj.lens-hit", svg).map(function (o) { return CBY[o.getAttribute("data-c")].title; });
    hits = hits.filter(function (x, i) { return hits.indexOf(x) === i; });
    lp.hidden = false;
    lp.innerHTML = "<p><b>" + esc(m.letter + " · " + m.title) + ".</b> " + esc(m.reveals) + " A design lens, not a runtime service.</p><ul>" + hits.map(function (h) { return "<li>" + esc(h) + "</li>"; }).join("") + "</ul>";
  }

  function renderInspector(step) {
    renderStep(step); renderConcept(); renderChecks(); renderLens(); showTab(tab);
  }
  function showTab(t) {
    tab = t;
    ["step", "concept", "check"].forEach(function (k) { $("tab-" + k).setAttribute("aria-selected", k === t ? "true" : "false"); $("pane-" + k).hidden = k !== t; });
  }
  qa(".in-t").forEach(function (b) { b.addEventListener("click", function () { showTab(b.id.replace("tab-", "")); }); });
  $("atl-insp").querySelector(".in-tabs").addEventListener("keydown", function (e) {
    var order = ["step", "concept", "check"], i = order.indexOf(tab);
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); showTab(order[(i + (e.key === "ArrowRight" ? 1 : 2)) % 3]); $("tab-" + tab).focus(); }
  });

  /* ---------------- actions ---------------- */
  function select(c, push) {
    if (!CBY[c]) return;
    st.focus = c; mark("visited", c); urlState(push); showTab("concept"); render(false); tab = "concept"; showTab("concept");
  }
  function go(i, animate) { stop(); idx = Math.max(-1, Math.min(i, run.steps.length - 1)); urlState(false); render(animate !== false); }
  function stop() { if (playing) { clearInterval(playing); playing = null; $("atl-play").setAttribute("aria-pressed", "false"); $("atl-play").textContent = "Play"; } }
  function play() {
    if (playing) { stop(); return; }
    if (idx >= run.steps.length - 1) idx = -1;
    $("atl-play").setAttribute("aria-pressed", "true"); $("atl-play").textContent = "Pause";
    var tick = function () { if (idx >= run.steps.length - 1) { stop(); return; } idx++; urlState(false); render(true); };
    tick(); playing = setInterval(tick, reduced ? 3800 : 2800);
  }
  $("atl-follow").addEventListener("click", function () { if (idx >= run.steps.length - 1) go(0); else go(idx + 1); if (tab !== "step") showTab("step"); });
  $("atl-next").addEventListener("click", function () { go(idx + 1); });
  $("atl-prev").addEventListener("click", function () { go(idx - 1); });
  $("atl-play").addEventListener("click", play);
  $("atl-reset").addEventListener("click", function () { stop(); idx = -1; urlState(false); fit(); render(false); });
  root.addEventListener("keydown", function (e) {
    if (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName) || e.target.closest(".in-tabs")) return;
    if (e.key === "ArrowRight" && e.target.closest(".atl-toolbar, .atl-stage")) { e.preventDefault(); go(idx + 1); }
    if (e.key === "ArrowLeft" && e.target.closest(".atl-toolbar, .atl-stage")) { e.preventDefault(); go(idx - 1); }
  });

  function syncControls() {
    qa("[data-design]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-design") === st.design ? "true" : "false"); });
    qa("[data-view]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-view") === st.view ? "true" : "false"); });
    qa(".ls-b").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-lens") === st.lens ? "true" : "false"); });
    qa("[data-iv]").forEach(function (cb) { cb.checked = !!st[cb.getAttribute("data-iv")]; });
  }
  qa("[data-design]").forEach(function (b) { b.addEventListener("click", function () { st.design = b.getAttribute("data-design"); rebuild(); idx = Math.min(idx, run.steps.length - 1); syncControls(); urlState(true); render(false); }); });
  qa("[data-view]").forEach(function (b) { b.addEventListener("click", function () { st.view = b.getAttribute("data-view"); syncControls(); urlState(true); render(false); }); });
  qa(".ls-b").forEach(function (b) { b.addEventListener("click", function () { var l = b.getAttribute("data-lens"); st.lens = st.lens === l ? null : l; syncControls(); urlState(true); render(false); }); });
  qa("[data-iv]").forEach(function (cb) { cb.addEventListener("change", function () { st[cb.getAttribute("data-iv")] = cb.checked; stop(); rebuild(); idx = -1; urlState(true); render(false); }); });
  qa(".rl-c").forEach(function (b) { b.addEventListener("click", function () { select(b.getAttribute("data-c"), true); }); });
  svg.addEventListener("click", function (e) { var o = e.target.closest(".obj"); if (o) select(o.getAttribute("data-c"), true); });
  $("atl-rail-t").addEventListener("click", function () {
    var narrow = window.matchMedia("(max-width:1699px)").matches;
    if (narrow) root.classList.toggle("rail-open"); else root.classList.toggle("rail-closed");
    var open = narrow ? root.classList.contains("rail-open") : !root.classList.contains("rail-closed");
    $("atl-rail-t").setAttribute("aria-expanded", open ? "true" : "false");
  });

  $("atl-opts").addEventListener("click", function () { var o = root.classList.toggle("opts-open"); $("atl-opts").setAttribute("aria-expanded", o ? "true" : "false"); });

  /* zoom, fit, whole scene */
  $("atl-zoomin").addEventListener("click", function () { zoom(0.8); });
  $("atl-zoomout").addEventListener("click", function () { zoom(1.25); });
  $("atl-fit").addEventListener("click", fit);
  $("atl-whole").addEventListener("click", function () { whole = !whole; zoomed = false; $("atl-whole").setAttribute("aria-pressed", whole ? "true" : "false"); $("atl-whole").textContent = whole ? "Focus on step" : "Whole scene"; setVB(VB0); camera(); });
  /* size the workspace to the first screen on desktop: the drawing gets the height, not the prose */
  var body = root.querySelector(".atl-body");
  function fitHeight() {
    if (root.classList.contains("is-expanded") || window.innerWidth < 1100) { body.style.height = ""; return; }
    var top = body.getBoundingClientRect().top + window.scrollY;
    body.style.height = Math.max(560, Math.min(1180, window.innerHeight - top - 10)) + "px";
  }
  fitHeight();
  window.addEventListener("resize", function () { fitHeight(); if (!zoomed) camera(); });

  /* expand: viewport-filling workspace, state preserved, focus and scroll restored */
  var expandFrom = null, scrollY0 = 0;
  function expand(on) {
    if (on) { expandFrom = document.activeElement; scrollY0 = window.scrollY; root.classList.add("is-expanded"); document.documentElement.classList.add("atlas-lock"); }
    else { root.classList.remove("is-expanded"); document.documentElement.classList.remove("atlas-lock"); window.scrollTo(0, scrollY0); if (expandFrom && expandFrom.focus) expandFrom.focus(); }
    $("atl-expand").setAttribute("aria-pressed", on ? "true" : "false"); $("atl-expand").textContent = on ? "Exit expanded view" : "Expand";
    setTimeout(function () { if (!zoomed) camera(); }, 30);
  }
  $("atl-expand").addEventListener("click", function () { expand(!root.classList.contains("is-expanded")); });
  $("atl-exit").addEventListener("click", function () { expand(false); });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var d = $("atl-change"); if (d.open) { d.open = false; d.querySelector("summary").focus(); return; }
    if (root.classList.contains("is-expanded")) expand(false);
  });

  /* exports: the current view as SVG, and a print one-pager */
  function cssVar(n) { return getComputedStyle(root).getPropertyValue(n).trim(); }
  $("atl-svg").addEventListener("click", function () {
    var clone = svg.cloneNode(true), step = idx >= 0 ? run.steps[idx] : null;
    clone.removeAttribute("id"); clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("viewBox", "0 0 1280 900"); clone.setAttribute("width", "1280"); clone.setAttribute("height", "900");
    var v = {}; ["--paper", "--card", "--sunk", "--ink", "--body", "--mute", "--faint", "--rule", "--rule2", "--blue", "--blue-soft", "--gold", "--gold-ink", "--gold-soft", "--top", "--warn", "--warn-soft", "--sans", "--mono", "--display"].forEach(function (k) { v[k] = cssVar(k); });
    var rules = qa("link[href$='atlas.css']", document).length ? [].slice.call(document.styleSheets).filter(function (s) { return (s.href || "").indexOf("atlas.css") >= 0; }) : [];
    var css = ":root{" + Object.keys(v).map(function (k) { return k + ":" + v[k]; }).join(";") + "}";
    try { rules.forEach(function (s) { [].slice.call(s.cssRules).forEach(function (r) { if (r.selectorText && r.selectorText.indexOf(".atlas-scene") >= 0) css += r.cssText.replace(/\.atlas(\.[\w-]+)*\s+\.atlas-scene/g, "svg"); }); }); } catch (e) {}
    css += "svg{background:" + v["--paper"] + "}" + (st.view === "arch" ? ".pic{display:none}.arch{display:inline}" : ".arch{display:none}");
    css += ".obj{opacity:" + (step ? ".42" : "1") + "}.obj.focus{opacity:1}.edge{opacity:0}.edge.on{opacity:1}.courier{display:none}";
    var style = document.createElementNS("http://www.w3.org/2000/svg", "style"); style.textContent = css; clone.insertBefore(style, clone.firstChild);
    var cap = document.createElementNS("http://www.w3.org/2000/svg", "g");
    var line2 = step ? ("Step " + (idx + 1) + " of " + run.steps.length + ": " + step.title + (step.outcome ? ". Outcome: " + SC.outcomes[step.outcome].label : "")) : "Overview";
    cap.innerHTML = '<rect x="0" y="806" width="1280" height="94" fill="' + v["--card"] + '"></rect>' +
      '<text x="20" y="836" font-family="Georgia, serif" font-size="22" fill="' + v["--ink"] + '">' + esc(SC.title) + "</text>" +
      '<text x="20" y="862" font-family="sans-serif" font-size="14" fill="' + v["--body"] + '">' + esc(line2) + " · " + (st.design === "team" ? "coordinator design" : "one-agent design") + " · " + (st.view === "arch" ? "architecture view" : "picture view") + "</text>" +
      '<text x="20" y="886" font-family="monospace" font-size="12" fill="' + v["--mute"] + '">khalidshams.com/learn/atlas · content ' + esc(CON.version) + " · teaching simulation, synthetic data · solid figures are people, outline figures are software</text>";
    clone.appendChild(cap);
    var blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(clone)], { type: "image/svg+xml" });
    var a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = "shams-atlas-" + (st.design) + "-" + (step ? "step-" + (idx + 1) : "overview") + ".svg";
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  });
  $("atl-print").addEventListener("click", function () { var lg = root.querySelector(".legend"); var was = lg.open; lg.open = true; window.print(); lg.open = was; });

  /* ---------------- boot ---------------- */
  rebuild();
  idx = Math.min(st.step, run.steps.length) - 1;
  syncControls();
  if (window.matchMedia("(max-width:1699px)").matches) $("atl-rail-t").setAttribute("aria-expanded", "false");
  render(false);
  if (st.focus) showTab("concept");
  root.setAttribute("data-ready", "true");
  window.__atlas = { state: function () { return { st: st, idx: idx, outcome: run.outcome, steps: run.steps.map(function (s) { return s.id; }) }; } };
})();
