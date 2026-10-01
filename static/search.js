/* Site search for khalidshams.com. No dependencies, no network until opened.
   Index: /search.json, built by build.py (one entry per section, map idea, and post). */
(function () {
  "use strict";
  var INDEX = null, loading = null, open = false, items = [], active = -1, lastQ = "";
  var KIND = { section: "Section", idea: "Idea on the map", post: "Writing", playbook: "Playbook" };
  var SYN = { llm: ["large language model"], ai: ["artificial intelligence"], rag: ["retrieval"], mcp: ["model context protocol"],
    agents: ["agent"], agent: ["agentic"], hooks: ["guardrails"], hook: ["guardrails"], evals: ["evaluation"], eval: ["evaluation"],
    saas: ["multi-tenant", "tenant"], fabric: ["microsoft fabric", "lakehouse"], entra: ["identity"], sentinel: ["detection"],
    cost: ["economics", "finops"], kill: ["off switch", "stop"], switch: ["off switch"], "off": ["kill switch"], security: ["identity", "governance"], gates: ["gate"], gate: ["gates"],
    sla: ["availability"], uptime: ["availability"], downtime: ["availability"], nines: ["availability"], rto: ["recovery"], rpo: ["data loss", "recovery"],
    dr: ["disaster recovery", "restore"], backup: ["restore"], backups: ["restore"], calculator: ["tool"], calculators: ["tools"] };

  function $(sel, root) { return (root || document).querySelector(sel); }
  function h(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function norm(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function tokens(q) { return norm(q).replace(/[^a-z0-9$+.&' -]/g, " ").split(/\s+/).filter(function (t) { return t.length > 1; }); }
  function esc(s) { return s.replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  function load() {
    if (INDEX) return Promise.resolve(INDEX);
    if (loading) return loading;
    loading = fetch("/search.json", { cache: "force-cache" }).then(function (r) { return r.json(); }).then(function (d) {
      INDEX = d.map(function (e) { e._t = norm(e.t); e._s = norm(e.s); e._p = norm(e.p); e._x = norm(e.x || ""); return e; });
      return INDEX;
    });
    return loading;
  }

  function expand(toks) {
    var out = toks.slice();
    toks.forEach(function (t) { (SYN[t] || []).forEach(function (s) { if (out.indexOf(s) < 0) out.push(s); }); });
    return out;
  }
  function wordRe(t) { return new RegExp("(^|[^a-z0-9])" + escRe(t), "i"); }
  function countRe(t) { return new RegExp("(^|[^a-z0-9])" + escRe(t), "ig"); }

  // One token matches if the token itself or any of its synonyms appears at a word start.
  function score(e, toks, phrase) {
    var s = 0;
    for (var i = 0; i < toks.length; i++) {
      var alts = [toks[i]].concat(SYN[toks[i]] || []), best = 0;
      for (var j = 0; j < alts.length; j++) {
        var t = alts[j], w = j === 0 ? 1 : 0.7, sc = 0, re = wordRe(t);
        if (re.test(e._t)) sc += e._t.indexOf(t) === 0 ? 14 : 10;
        if (re.test(e._x)) sc += 4;
        if (re.test(e._p)) sc += 3;
        if (re.test(e._s)) { var n = (e._s.match(countRe(t)) || []).length; sc += 2 + Math.min(n, 5); }
        sc *= w; if (sc > best) best = sc;
      }
      if (!best) return 0;
      s += best;
    }
    if (phrase && toks.length > 1) { if (e._t.indexOf(phrase) >= 0) s += 16; else if (e._s.indexOf(phrase) >= 0 || e._x.indexOf(phrase) >= 0) s += 8; }
    if (e.k === "idea") s += 1;
    if (e.t === e.p) s += 2;           // whole-page entries
    if (e.u.indexOf("#") < 0) s += 1;  // page roots
    return s;
  }

  function search(q) {
    var toks = tokens(q); if (!toks.length) return [];
    var phrase = norm(q).trim().replace(/\s+/g, " ");
    var res = [];
    INDEX.forEach(function (e) { var sc = score(e, toks, phrase); if (sc > 0) res.push({ e: e, s: sc }); });
    res.sort(function (a, b) { return b.s - a.s; });
    var seen = {}, out = [];
    res.forEach(function (r) { if (seen[r.e.u]) return; seen[r.e.u] = 1; out.push(r); });
    return out.slice(0, 40);
  }

  function snippet(text, toks) {
    var t = norm(text), best = -1;
    for (var i = 0; i < toks.length && best < 0; i++) best = t.indexOf(toks[i]);
    if (best < 0) return text.slice(0, 160) + (text.length > 160 ? "…" : "");
    var start = Math.max(0, best - 70), end = Math.min(text.length, best + 110);
    while (start > 0 && text[start - 1] !== " ") start--;
    return (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
  }
  function mark(text, toks) {
    var safe = esc(text);
    if (!toks.length) return safe;
    var re = new RegExp("(^|[^A-Za-z0-9])(" + toks.map(escRe).join("|") + ")", "ig");
    return safe.replace(re, "$1<mark>$2</mark>");
  }

  /* ---------- overlay ---------- */
  var ov, input, list, status;
  function build() {
    ov = h("div", "ks-search"); ov.hidden = true; ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true"); ov.setAttribute("aria-label", "Search this site");
    var box = h("div", "ks-box");
    var row = h("div", "ks-row");
    var icon = h("span", "ks-ico"); icon.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
    input = h("input"); input.type = "search"; input.placeholder = "Search the whole site: ideas, gates, playbooks, posts"; input.setAttribute("aria-label", "Search"); input.autocomplete = "off"; input.spellcheck = false;
    var close = h("button", "ks-close", "Esc"); close.type = "button"; close.setAttribute("aria-label", "Close search");
    row.appendChild(icon); row.appendChild(input); row.appendChild(close);
    status = h("p", "ks-status"); status.setAttribute("aria-live", "polite");
    list = h("div", "ks-list"); list.setAttribute("role", "listbox");
    var foot = h("div", "ks-foot"); foot.innerHTML = '<span><kbd>↑</kbd><kbd>↓</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span><span class="ks-foot-r">Matches are highlighted on the page you open</span>';
    box.appendChild(row); box.appendChild(status); box.appendChild(list); box.appendChild(foot); ov.appendChild(box); document.body.appendChild(ov);
    ov.addEventListener("click", function (e) { if (e.target === ov) hide(); });
    close.addEventListener("click", hide);
    input.addEventListener("input", function () { run(input.value); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") { e.preventDefault(); if (active >= 0 && items[active]) go(items[active]); else if (items[0]) go(items[0]); }
      else if (e.key === "Escape") { hide(); }
    });
  }
  function suggestions() {
    list.innerHTML = "";
    var s = h("div", "ks-sugg");
    s.appendChild(h("p", "ks-sugg-label", "Try"));
    ["what is an agent", "MCP", "eight gates", "landing zone", "cost per run", "Sentinel", "kill switch", "RAG", "multi-tenant", "evaluation harness"].forEach(function (q) {
      var b = h("button", "chip", q); b.type = "button"; b.onclick = function () { input.value = q; run(q); input.focus(); }; s.appendChild(b);
    });
    list.appendChild(s);
    status.textContent = "";
  }
  function show() {
    if (!ov) build();
    open = true; ov.hidden = false; document.documentElement.classList.add("ks-open");
    input.value = lastQ; input.focus(); input.select();
    load().then(function () { if (lastQ) run(lastQ); else suggestions(); }).catch(function () { status.textContent = "Search isn't available right now."; });
    if (!lastQ) suggestions();
  }
  function hide() { if (!ov) return; open = false; ov.hidden = true; document.documentElement.classList.remove("ks-open"); }
  function move(d) {
    if (!items.length) return;
    active = (active + d + items.length) % items.length;
    var rows = list.querySelectorAll(".ks-item");
    [].forEach.call(rows, function (r, i) { r.classList.toggle("on", i === active); r.setAttribute("aria-selected", i === active ? "true" : "false"); });
    rows[active].scrollIntoView({ block: "nearest" });
  }
  function run(q) {
    lastQ = q; active = -1; items = [];
    if (!INDEX) { status.textContent = "Loading the index…"; load().then(function () { if (lastQ === q) run(q); }); return; }
    var toks = tokens(q);
    if (!toks.length) { suggestions(); return; }
    var res = search(q); items = res.map(function (r) { return r.e; });
    list.innerHTML = "";
    if (!res.length) { status.textContent = 'Nothing for "' + q + '". Try a shorter word, or one of the ideas on the map.'; return; }
    status.textContent = res.length + (res.length === 40 ? "+" : "") + " result" + (res.length === 1 ? "" : "s");
    var byPage = {}, order = [];
    res.forEach(function (r) { var p = r.e.k === "idea" ? "Learn AI · the map" : r.e.p; if (!byPage[p]) { byPage[p] = []; order.push(p); } byPage[p].push(r.e); });
    var n = 0, hl = expand(toks);
    order.forEach(function (p) {
      var g = h("div", "ks-group"); g.appendChild(h("p", "ks-page", p));
      byPage[p].forEach(function (e) {
        var a = h("a", "ks-item"); a.href = e.u; a.setAttribute("role", "option"); a.dataset.i = n++;
        var kind = e.k === "idea" ? (e.c + " · idea") : (e.k === "post" ? ("Post · " + (e.d || "")) : (e.x ? e.x : (e.u.indexOf("/playbooks/") === 0 && e.t !== e.p ? "Playbook section" : "Section")));
        a.innerHTML = '<span class="ks-k">' + esc(kind) + '</span><span class="ks-t">' + mark(e.t, hl) + '</span><span class="ks-s">' + mark(snippet(e.s, hl), hl) + '</span>';
        a.addEventListener("click", function (ev) { ev.preventDefault(); go(e); });
        a.addEventListener("mousemove", function () { var i = +a.dataset.i; if (i !== active) { active = i; [].forEach.call(list.querySelectorAll(".ks-item"), function (r, k) { r.classList.toggle("on", k === i); }); } });
        g.appendChild(a);
      });
      list.appendChild(g);
    });
  }
  function go(e) {
    try { sessionStorage.setItem("ks-q", lastQ); } catch (x) { }
    var here = location.pathname.replace(/\/$/, "") + "/", target = e.u.split("#")[0].split("?")[0].replace(/\/$/, "") + "/";
    hide();
    if (here === target && e.u.indexOf("?idea=") < 0) {
      var hash = e.u.split("#")[1];
      highlightPage(lastQ);
      if (hash) { var el = document.getElementById(hash); if (el) { history.replaceState(null, "", "#" + hash); el.scrollIntoView({ behavior: "smooth", block: "start" }); if (el.tagName === "DETAILS") el.open = true; } }
      return;
    }
    location.href = e.u;
  }

  /* ---------- highlight on arrival ---------- */
  var HL_SKIP = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, SVG: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1, BUTTON: 1, MARK: 1, KBD: 1 };
  function highlightPage(q) {
    clearHighlights();
    var toks = expand(tokens(q)); if (!toks.length) return 0;
    var re = new RegExp("(?:^|(?<=[^A-Za-z0-9]))(" + toks.map(escRe).join("|") + ")", "ig"), count = 0, first = null;
    var root = document.body;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var p = n.parentNode;
        for (var a = p; a && a !== root; a = a.parentNode) { if (HL_SKIP[a.tagName] || a.classList && (a.classList.contains("site-head") || a.classList.contains("ks-search") || a.classList.contains("ks-pill"))) return NodeFilter.FILTER_REJECT; }
        return re.test(n.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      }
    });
    var nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (n) {
      var frag = document.createDocumentFragment(), text = n.nodeValue, last = 0, m; re.lastIndex = 0;
      while ((m = re.exec(text))) {
        if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        var mk = document.createElement("mark"); mk.className = "ks-hl"; mk.textContent = m[0]; frag.appendChild(mk); if (!first) first = mk; count++; last = m.index + m[0].length;
        if (count > 400) break;
      }
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      n.parentNode.replaceChild(frag, n);
      // open any details that now contain a highlight
      var d = frag.parentNode && frag.parentNode.closest ? null : null;
    });
    [].forEach.call(document.querySelectorAll("details"), function (d) { if (d.querySelector("mark.ks-hl")) d.open = true; });
    if (count) pill(q, count, first);
    return count;
  }
  function clearHighlights() {
    [].forEach.call(document.querySelectorAll("mark.ks-hl"), function (m) { var t = document.createTextNode(m.textContent); m.parentNode.replaceChild(t, m); });
    var p = $(".ks-pill"); if (p) p.remove();
    document.body.normalize();
  }
  var pillIdx = 0;
  function pill(q, count, first) {
    var p = h("div", "ks-pill"); var marks = document.querySelectorAll("mark.ks-hl"); pillIdx = 0;
    var label = h("span", "ks-pill-l"); label.innerHTML = '<b>' + count + '</b> match' + (count === 1 ? "" : "es") + ' for “' + esc(q) + '”';
    var prev = h("button", "ks-pill-b", "↑"); prev.type = "button"; prev.setAttribute("aria-label", "Previous match");
    var next = h("button", "ks-pill-b", "↓"); next.type = "button"; next.setAttribute("aria-label", "Next match");
    var clear = h("button", "ks-pill-x", "Clear"); clear.type = "button";
    function jump(d) { if (!marks.length) return; [].forEach.call(marks, function (m) { m.classList.remove("cur"); }); pillIdx = (pillIdx + d + marks.length) % marks.length; marks[pillIdx].classList.add("cur"); marks[pillIdx].scrollIntoView({ behavior: "smooth", block: "center" }); }
    prev.onclick = function () { jump(-1); }; next.onclick = function () { jump(1); }; clear.onclick = clearHighlights;
    p.appendChild(label); p.appendChild(prev); p.appendChild(next); p.appendChild(clear); document.body.appendChild(p);
    if (!location.hash && first) { setTimeout(function () { pillIdx = -1; jump(1); }, 150); } else if (marks.length) { marks[0].classList.add("cur"); }
  }

  /* ---------- wiring ---------- */
  function isTyping(e) { var t = e.target; return t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable); }
  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) { e.preventDefault(); open ? hide() : show(); return; }
    if (e.key === "/" && !isTyping(e) && !open) { e.preventDefault(); show(); }
  });
  document.addEventListener("click", function (e) { var b = e.target.closest && e.target.closest("[data-search]"); if (b) { e.preventDefault(); show(); } });
  // arrival highlight
  try {
    var q = sessionStorage.getItem("ks-q");
    if (q) {
      sessionStorage.removeItem("ks-q"); lastQ = q;
      var start = function () { highlightPage(q); };
      if (document.readyState === "complete") setTimeout(start, 50); else window.addEventListener("load", function () { setTimeout(start, 50); });
    }
  } catch (x) { }
  // warm the index on first interaction
  ["pointerdown", "keydown"].forEach(function (ev) { document.addEventListener(ev, function w() { document.removeEventListener(ev, w); load().catch(function () { }); }, { once: true }); });
  window.KSSearch = { open: show, close: hide, highlight: highlightPage, clear: clearHighlights };
})();
