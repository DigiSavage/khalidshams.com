/* Brief builder: four answers and a situation become a checklist. Pure client side; nothing is sent anywhere. */
(function () {
  "use strict";
  var el = document.getElementById("routes-data"), out = document.getElementById("bb-out"), form = document.getElementById("bb-form");
  if (!el || !out || !form) return;
  var D = JSON.parse(el.textContent);
  var GATES = { g1: "What decision does this system make, and who owns it when it is wrong?", g2: "What does each agent own, where does control pass, and where does a human sit?",
    g3: "What is the agent allowed to see and do, per user, enforced by the platform?", g4: "Where does every fact come from, and is that source governed?",
    g5: "Is every write typed, validated, idempotent, and reversible?", g6: "Can you show me the harness, and what number moves when quality moves?",
    g7: "What does a run cost at ten times the volume?", g8: "Can you stop it, explain it, and change it safely?" };
  var RUNGS = ["Manual", "Assisted", "Augmented", "Automated", "Autonomous"];
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function uniq(a) { return a.filter(function (x, i) { return a.indexOf(x) === i; }); }
  function labelFor(href) {
    for (var i = 0; i < D.situations.length; i++) for (var j = 0; j < D.situations[i].steps.length; j++) if (D.situations[i].steps[j].href === href) return D.situations[i].steps[j].label;
    return href;
  }
  var lastText = "";
  function build() {
    var sit = D.situations.filter(function (s) { return s.id === document.getElementById("bb-sit").value; })[0] || D.situations[0];
    var gates = sit.gates.concat(D.brief.always.gates), lessons = D.brief.always.lessons.slice(), watch = [], checks = D.brief.always.check.slice(), rung = sit.rung, answers = [];
    D.brief.questions.forEach(function (q) {
      var yes = form.querySelector('input[name="' + q.id + '"]:checked'); yes = yes && yes.value === "yes";
      answers.push({ q: q.q, a: yes ? q.yes : q.no });
      if (!yes) return;
      var add = q.yes_adds; gates = gates.concat(add.gates || []); lessons = lessons.concat(add.lessons || []); watch = watch.concat(add.watch || []); checks = checks.concat(add.check || []);
      if (add.rung_min != null && rung < add.rung_min) rung = add.rung_min;
    });
    sit.steps.forEach(function (st) { if (st.kind === "watch") watch.push(st.href); if (st.kind === "learn") lessons.push(st.href); if (st.kind === "check") checks.push(st.href); });
    gates = uniq(gates).sort(); lessons = uniq(lessons); watch = uniq(watch); checks = uniq(checks);
    var build = sit.steps.filter(function (s) { return s.kind === "build"; }), ex = sit.steps.filter(function (s) { return s.kind === "example"; });
    var h = '<p class="sec-label">Your brief</p><h3>' + esc(sit.title) + '</h3><p class="bb-rung">Ladder rung to design for: <b>' + rung + " · " + RUNGS[rung] + "</b>" + (rung > sit.rung ? " (raised by your answers)" : "") + "</p>";
    h += '<p class="sec-label">Gates that decide it (' + gates.length + " of 8)</p><ol class=\"bb-gates\">" + gates.map(function (g) { return '<li><a href="/method/#' + g + '"><b>Gate ' + g.slice(1).padStart(2, "0") + "</b> " + esc(GATES[g]) + "</a></li>"; }).join("") + "</ol>";
    h += '<p class="sec-label">Learn first</p><ul>' + lessons.map(function (l) { return '<li><a href="' + esc(l) + '">' + esc(labelFor(l)) + "</a></li>"; }).join("") + "</ul>";
    h += '<p class="sec-label">Watch it run</p><ul>' + watch.map(function (l) { return '<li><a href="' + esc(l) + '">' + esc(labelFor(l)) + "</a></li>"; }).join("") + "</ul>";
    h += '<p class="sec-label">Build</p><ul>' + build.map(function (s) { return '<li><a href="' + esc(s.href) + '">' + esc(s.label) + "</a></li>"; }).join("") + "</ul>";
    h += '<p class="sec-label">Check the number</p><ul>' + checks.map(function (l) { return '<li><a href="' + esc(l) + '">' + esc(labelFor(l)) + "</a></li>"; }).join("") + "</ul>";
    h += '<p class="sec-label">Worked example</p><ul>' + ex.map(function (s) { return '<li><a href="' + esc(s.href) + '">' + esc(s.label) + "</a></li>"; }).join("") + "</ul>";
    out.innerHTML = h;
    lastText = "Architecture brief: " + sit.title + "\n" + answers.map(function (a) { return "- " + a.q + " " + a.a; }).join("\n") +
      "\nLadder rung to design for: " + rung + " (" + RUNGS[rung] + ")\n\nGates:\n" + gates.map(function (g) { return "- Gate " + g.slice(1).padStart(2, "0") + ": " + GATES[g] + " https://khalidshams.com/method/#" + g; }).join("\n") +
      "\n\nLearn first:\n" + lessons.map(function (l) { return "- " + labelFor(l) + " https://khalidshams.com" + l; }).join("\n") +
      "\n\nWatch it run:\n" + watch.map(function (l) { return "- " + labelFor(l) + " https://khalidshams.com" + l; }).join("\n") +
      "\n\nBuild:\n" + build.map(function (s) { return "- " + s.label + " https://khalidshams.com" + s.href; }).join("\n") +
      "\n\nCheck the number:\n" + checks.map(function (l) { return "- " + labelFor(l) + " https://khalidshams.com" + l; }).join("\n") +
      "\n\nGenerated from khalidshams.com/architect/ · a starting checklist, not a review.";
  }
  form.addEventListener("change", build);
  document.getElementById("bb-copy").addEventListener("click", function () {
    var ok = document.getElementById("bb-copied");
    var fallback = function () { var ta = document.createElement("textarea"); ta.value = lastText; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); ok.textContent = "Copied."; } catch (e) { ok.textContent = "Select the brief and copy it."; } ta.remove(); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(lastText).then(function () { ok.textContent = "Copied."; }, fallback); else fallback();
  });
  var pre = new URLSearchParams(location.search).get("s"); if (pre && document.querySelector('#bb-sit option[value="' + pre + '"]')) document.getElementById("bb-sit").value = pre;
  build();
})();
