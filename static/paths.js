/* Guided paths: progress kept in this browser only.
   Keys: ks-learn (ideas marked "I get this", shared with the map), ks-atlas-v1 (atlas progress; .lessons holds "scenario:outcome"
   for runs followed to their end), ks-paths ({seen:[]} of stop keys). Nothing is sent anywhere. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var qa = function (s, el) { return [].slice.call((el || document).querySelectorAll(s)); };
  function read(k, d) { try { var v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? d : v; } catch (e) { return d; } }
  function write(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var understood = new Set(read("ks-learn", []));
  var atlas = read("ks-atlas-v1", {}); var lessons = new Set(Array.isArray(atlas.lessons) ? atlas.lessons : []);
  var seen = new Set((read("ks-paths", {}).seen) || []);
  function markSeen(key) { if (seen.has(key)) return; seen.add(key); write("ks-paths", { seen: Array.from(seen) }); }
  function done(key) {
    if (key.indexOf("idea:") === 0) return seen.has(key) || understood.has(key.slice(5));
    if (key.indexOf("atlas:") === 0) return lessons.has(key.slice(6));
    return seen.has(key);
  }
  var dataEl = $("paths-data"), PATHS = [];
  try { PATHS = dataEl ? JSON.parse(dataEl.textContent).paths : []; } catch (e) { PATHS = []; }
  function progress(p) { var n = 0; p.stops.forEach(function (s) { if (done(s.key)) n++; }); return { done: n, total: p.stops.length }; }
  function nextStop(p) { for (var i = 0; i < p.stops.length; i++) if (!done(p.stops[i].key)) return p.stops[i]; return null; }
  function withPath(s, p) { return s.kind === "section" ? s.href : s.href + (s.href.indexOf("?") >= 0 ? "&" : "?") + "path=" + p.id; }

  /* ---- the current page's stop, if any ---- */
  var here = document.body.getAttribute("data-stop");           // e.g. idea:agent on an idea page
  if (here) markSeen(here);
  var pathId = new URLSearchParams(location.search).get("path");
  var curPath = PATHS.filter(function (p) { return p.id === pathId; })[0] || null;

  /* ---- door list on Learn and Home ---- */
  qa(".door-paths li[data-path]").forEach(function (li) {
    var p = PATHS.filter(function (x) { return x.id === li.getAttribute("data-path"); })[0]; if (!p) return;
    var pr = progress(p); var bar = li.querySelector(".dp-bar i");
    if (bar) bar.style.width = Math.round(100 * pr.done / pr.total) + "%";
    li.classList.toggle("is-done", pr.done === pr.total); li.classList.toggle("is-started", pr.done > 0 && pr.done < pr.total);
  });
  var cont = $("door-continue"), prog = $("door-prog");
  if (cont && PATHS.length) {
    var cur = PATHS.filter(function (p) { return progress(p).done < p.stops.length; })[0];
    if (!cur) { cont.textContent = "All six paths done. Choose a situation"; cont.href = "/architect/"; }
    else {
      var pr = progress(cur), ns = nextStop(cur);
      var started = PATHS.some(function (p) { return progress(p).done > 0; });
      cont.textContent = started ? "Continue path " + cur.n : "Start path 1";
      cont.href = ns ? withPath(ns, cur) : cur.href;
      if (prog && started) prog.textContent = cur.title + " · " + pr.done + " of " + pr.total + " stops";
    }
  }

  /* ---- a path page ---- */
  var stops = qa(".path-stops .ps");
  if (stops.length) {
    var n = 0;
    stops.forEach(function (li) { var d = done(li.getAttribute("data-key")); li.classList.toggle("done", d); if (d) n++; });
    var meter = $("path-meter"); if (meter) meter.textContent = n + " of " + stops.length + " done on this device";
    var fill = $("path-fill"); if (fill) fill.style.width = Math.round(100 * n / stops.length) + "%";
    var go = $("path-go"), p = PATHS.filter(function (x) { return x.id === document.body.getAttribute("data-path"); })[0];
    if (go && p) { var ns = nextStop(p); if (ns) { go.href = withPath(ns, p); go.textContent = n ? "Continue at stop " + (p.stops.indexOf(ns) + 1) : "Start at stop 1"; } else { go.textContent = "Done. Start it again"; } }
    var understoodN = qa('.path-stops .ps[data-kind="idea"]').filter(function (li) { return understood.has(li.getAttribute("data-key").slice(5)); }).length;
    var um = $("path-understood"); if (um) um.textContent = understoodN + " marked understood";
  }

  /* ---- "I get this" on an idea page (same key the map uses) ---- */
  var got = $("idea-got");
  if (got) {
    var id = here.slice(5);
    var sync = function () { var on = understood.has(id); got.setAttribute("aria-pressed", on ? "true" : "false"); got.textContent = on ? "Marked as understood" : "I get this"; };
    got.addEventListener("click", function () { if (understood.has(id)) understood.delete(id); else understood.add(id); write("ks-learn", Array.from(understood)); sync(); });
    sync();
  }

  /* ---- sections seen on long pages count as stops ---- */
  var prefix = location.pathname === "/learn/" ? "sec:" : location.pathname === "/method/" ? "sec:m-" : null;
  if (prefix && "IntersectionObserver" in window) {
    var timers = {};
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var id = e.target.id; if (!id) return;
        if (e.isIntersecting) { timers[id] = setTimeout(function () { markSeen(prefix + id); }, 1500); }
        else if (timers[id]) { clearTimeout(timers[id]); delete timers[id]; }
      });
    }, { threshold: 0.35 });
    qa(".band[id]").forEach(function (b) { io.observe(b); });
  }

  /* ---- the path bar: where you are and what is next ---- */
  if (curPath) {
    var idx = -1;
    curPath.stops.forEach(function (s, i) {
      if (idx >= 0) return;
      if (here && s.key === here) idx = i;
      else if (s.kind === "atlas" && location.pathname === s.href.split("?")[0] && (s.href.split("?")[1] || "") === (location.search.replace(/^\?/, "").split("&").filter(function (x) { return x.indexOf("path=") !== 0 && x.indexOf("step=") !== 0; }).join("&"))) idx = i;
      else if (s.kind === "section" && s.href === location.pathname + location.hash) idx = i;
    });
    if (idx < 0) idx = curPath.stops.map(function (s) { return s.kind === "atlas" && location.pathname === s.href.split("?")[0]; }).indexOf(true);
    var bar = document.createElement("div"); bar.className = "pathbar"; bar.setAttribute("role", "navigation"); bar.setAttribute("aria-label", "Guided path");
    var prev = idx > 0 ? curPath.stops[idx - 1] : null, next = idx >= 0 && idx < curPath.stops.length - 1 ? curPath.stops[idx + 1] : null;
    var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
    bar.innerHTML = '<a class="pb-title" href="' + esc(curPath.href) + '"><b>Path ' + curPath.n + '</b> ' + esc(curPath.title) + '</a>' +
      '<span class="pb-pos">' + (idx >= 0 ? "Stop " + (idx + 1) + " of " + curPath.stops.length : "On this path") + "</span>" +
      (prev ? '<a class="pb-nav" href="' + esc(withPath(prev, curPath)) + '">&#8592; ' + esc(prev.label) + "</a>" : "") +
      (next ? '<a class="pb-nav pb-next" href="' + esc(withPath(next, curPath)) + '">' + esc(next.label) + " &#8594;</a>" : '<a class="pb-nav pb-next" href="' + esc(curPath.href) + '">Back to the path &#8594;</a>') +
      '<button type="button" class="pb-x" aria-label="Leave the path">&#215;</button>';
    document.body.appendChild(bar); document.body.classList.add("has-pathbar");
    bar.querySelector(".pb-x").addEventListener("click", function () { bar.remove(); document.body.classList.remove("has-pathbar"); try { history.replaceState(null, "", location.pathname + location.search.replace(/([?&])path=[^&]*&?/, "$1").replace(/[?&]$/, "") + location.hash); } catch (e) {} });
  }
})();
