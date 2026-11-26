(function () {
  'use strict';
  var frame = document.getElementById('agent-concepts-frame');
  if (!frame) return;

  function syncTheme() {
    var theme = document.documentElement.getAttribute('data-theme');
    if (theme !== 'light' && theme !== 'dark') theme = 'system';
    if (frame.contentWindow) {
      frame.contentWindow.postMessage({type: 'ks-agent-concepts-theme', theme: theme}, window.location.origin);
    }
  }

  window.addEventListener('message', function (event) {
    if (event.origin !== window.location.origin || event.source !== frame.contentWindow) return;
    var data = event.data;
    if (!data || data.type !== 'ks-agent-concepts-height' || !Number.isFinite(data.height)) return;
    frame.style.height = Math.min(2000, Math.max(500, Math.ceil(data.height))) + 'px';
  });
  frame.addEventListener('load', syncTheme);
  new MutationObserver(syncTheme).observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
  syncTheme();
}());
