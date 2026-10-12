(function () {
  'use strict';
  const root = document.getElementById('enterprise-studio');
  if (!root || !window.EnterpriseStudio) return;
  const data = JSON.parse(document.getElementById('es-data').textContent), api = window.EnterpriseStudio;
  const $ = id => document.getElementById('es-' + id);
  let cursor = 0, decision = 'pending', run = [];
  const narrow = window.matchMedia('(max-width: 600px)');
  let mapMode = narrow.matches ? 'detail' : 'overview', chosenMapMode = false;
  const focusBoxes = {identity:'35 45 285 180', evidence:'38 220 310 310', model:'305 48 420 210', proposal:'252 240 325 245', gate:'525 235 240 235', review:'742 32 260 220', execute:'740 278 260 235', receipt:'50 530 935 110', budget:'540 55 195 170'};
  const text = (id, value) => { $(id).textContent = value; };
  function config() {
    const raw = {};
    ['example', 'pattern', 'authority', 'risk', 'condition', 'platform', 'budget'].forEach(key => { raw[key] = $(key).value; });
    return api.normalize(raw);
  }
  function example() { return data.examples.find(item => item.id === config().example); }
  function updateRecord() {
    text('record-preview', api.record(config(), example(), $('owner').value, $('outcome').value));
  }
  function updatePlatform() {
    const platform = config().platform;
    const notes = {
      azure: ['Approved, pinned Azure model deployment.', 'Pin an approved model deployment and API version. Confirm region, networking, residency, retention, quotas and lifecycle for that specific deployment.'],
      'claude-azure': ['Claude in Microsoft Foundry, hosted on Azure.', 'The selected option processes prompts and outputs on Azure infrastructure. Anthropic remains the seller and operator. Verify the exact model, deployment scope, terms, quotas and supported integrations.'],
      'claude-external': ['Claude in Microsoft Foundry, hosted on Anthropic infrastructure.', 'Inference is on Anthropic infrastructure and may process data outside Azure or the selected Azure region. Treat this as a distinct approved data boundary; Azure billing does not establish residency.']
    };
    text('model-cell', notes[platform][0]); text('platform-note', notes[platform][1]); updateRecord();
  }
  function acceptance(item) {
    const wrapper = document.createElement('div'); wrapper.className = 'es-table-scroll';
    wrapper.setAttribute('role', 'region'); wrapper.setAttribute('aria-label', 'Acceptance cases'); wrapper.tabIndex = 0;
    const table = document.createElement('table');
    const thead = table.createTHead(), tr = thead.insertRow();
    ['Test condition', 'Required observable outcome'].forEach(value => { const th = document.createElement('th'); th.textContent = value; tr.append(th); });
    const tbody = table.createTBody();
    item.acceptance.forEach(pair => { const row = tbody.insertRow(); pair.forEach((value, i) => { const cell = document.createElement(i ? 'td' : 'th'); if (!i) cell.scope = 'row'; cell.textContent = value; row.append(cell); }); });
    wrapper.append(table); $('acceptance').replaceChildren(wrapper);
  }
  function updateDesign() {
    const item = example(), d = api.design(config(), item);
    text('pattern-result', d.title); text('pattern-why', d.why);
    text('authority-result', d.authorityText); text('authority-why', d.authorityWhy); text('design-limit', item.boundary);
    root.querySelectorAll('[data-example]').forEach(el => { el.textContent = item[el.dataset.example]; });
    text('proposal-text', d.authority === 'read' ? 'Business-write tools disabled. Return a checked answer or draft only.' : item.proposal);
    text('target-label', item.target);
    acceptance(item); updateRecord(); resetRun();
  }
  function paintRun() {
    const c = config(), step = run[cursor];
    text('step-count', 'Step ' + (cursor + 1) + ' of ' + run.length + (step.state === 'waiting' ? ' · waiting for review' : ''));
    text('state', {checked: '✓ CHECKED', held: '⏸ HELD', denied: '× DENIED', waiting: '⏸ WAITING', complete: '✓ COMPLETE', unknown: '? UNKNOWN'}[step.state]);
    $('state').dataset.state = step.state;
    text('step-title', step.title); text('step-body', step.body); text('step-enforcer', step.enforcer); text('step-event', step.event); text('step-budget', step.used + ' of ' + c.budget);
    $('prev').disabled = cursor === 0; $('next').disabled = cursor === run.length - 1;
    $('review-controls').hidden = step.state !== 'waiting';
    root.querySelectorAll('[data-node]').forEach(el => { el.classList.toggle('es-active', el.dataset.node === step.node); });
    const scene = root.querySelector('.es-scene');
    scene.setAttribute('viewBox', mapMode === 'detail' ? focusBoxes[step.node] : '0 0 1000 620');
    scene.dataset.state = step.state;
    ['overview', 'detail'].forEach(mode => $('map-' + mode).setAttribute('aria-pressed', String(mapMode === mode)));
    text('gate-label', step.node === 'gate' ? {denied: '× DENIED', held: '⏸ HELD'}[step.state] || '✓ CHECKED' : 'Permission');
    $('trace').replaceChildren(...run.slice(0, cursor + 1).map((event, i) => {
      const li = document.createElement('li'), code = document.createElement('code'), span = document.createElement('span');
      code.textContent = event.event; span.textContent = event.title; li.append(code, span); if (i === cursor) li.setAttribute('aria-current', 'step'); return li;
    }));
    // A short announcement avoids reading the full scene or trace on every step.
    text('announcement', 'Step ' + (cursor + 1) + '. ' + step.title + '. ' + $('state').textContent);
  }
  const announcement = document.createElement('p'); announcement.id = 'es-announcement'; announcement.className = 'es-sr'; announcement.setAttribute('role', 'status'); root.append(announcement);
  function resetRun() { cursor = 0; decision = 'pending'; run = api.buildRun(config(), example(), decision); paintRun(); }
  $('design-form').addEventListener('submit', event => event.preventDefault());
  ['example', 'pattern', 'authority', 'risk'].forEach(key => $(key).addEventListener('change', updateDesign));
  ['condition', 'budget'].forEach(key => $(key).addEventListener('change', () => { $('budget').value = config().budget; resetRun(); updateRecord(); }));
  $('next').addEventListener('click', () => { if (cursor < run.length - 1) { cursor++; paintRun(); } });
  $('prev').addEventListener('click', () => { if (cursor > 0) { cursor--; paintRun(); } });
  $('reset').addEventListener('click', resetRun);
  ['overview', 'detail'].forEach(mode => $('map-' + mode).addEventListener('click', () => {mapMode = mode; chosenMapMode = true; paintRun();}));
  narrow.addEventListener('change', () => {if (!chosenMapMode) mapMode = narrow.matches ? 'detail' : 'overview'; paintRun();});
  ['approve', 'reject'].forEach(value => $(value).addEventListener('click', () => {
    if (run[cursor].state !== 'waiting') return;
    decision = value; run = api.buildRun(config(), example(), decision); cursor = Math.min(cursor, run.length - 1); paintRun();
    $('step-title').tabIndex = -1; $('step-title').focus({preventScroll: true});
  }));
  $('platform').addEventListener('change', updatePlatform);
  ['owner', 'outcome'].forEach(key => $(key).addEventListener('input', updateRecord));
  $('download').addEventListener('click', () => {
    const blob = new Blob([$('record-preview').textContent + '\n'], {type: 'text/plain;charset=utf-8'}), url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = 'shams-' + config().example + '-design-record.txt'; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000); text('download-status', 'Design record prepared. Unresolved release decisions are included.');
  });
  const improvements = {
    source: ['Update the source or retrieval', 'Repair approved content, permissions or indexing. Re-evaluate retrieval and answers. This updates evidence, not language-model weights.'],
    extract: ['Improve extraction against labeled examples', 'Inspect scan quality, schemas and labeled field errors. Compare a new custom document model with the current one on held-out vendors and layouts; do not train on the evaluation set.'],
    behavior: ['Test the prompt, tool interface and model', 'Reproduce the task, improve instructions or tool contracts and compare pinned models. Consider fine-tuning only if supported and simpler changes fail. A revised prompt is not weight training.'],
    access: ['Repair enforcement before further release', 'Disable the affected capability, contain the incident and fix identity, retrieval filters or execution authorization. Add regression tests. Training a model to refuse is not a substitute for this boundary.']
  };
  $('improvement').addEventListener('change', () => {
    const item = improvements[$('improvement').value], b = document.createElement('b'), p = document.createElement('p'); b.textContent = item[0]; p.textContent = item[1]; $('improve-result').replaceChildren(b, p);
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      const current = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (current) root.querySelectorAll('.es-rail a').forEach(a => { if (a.hash === '#' + current.target.id) a.setAttribute('aria-current', 'step'); else a.removeAttribute('aria-current'); });
    }, {rootMargin: '-20% 0px -45% 0px', threshold: 0});
    root.querySelectorAll('.es-chapters > article').forEach(el => observer.observe(el));
  }
  updateDesign(); updatePlatform();
})();
