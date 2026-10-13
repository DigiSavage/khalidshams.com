(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('decision-room')) return;
  const API = '/api/admin/assessments';
  const STAGES = [['mandate','01 · Mandate'],['evidence','02 · Evidence'],['findings','03 · Findings'],['options','04 · Options'],['recommendation','05 · Decision'],['actions','06 · Handoff'],['notes','07 · Internal'],['review','08 · Review']];
  const DOMAINS = [['general','Architecture and trade-offs'],['cloud','Cloud and cost'],['saas','Multi-tenant SaaS'],['data','Data and integration'],['security','Security and identity'],['delivery','Delivery and modernization'],['ai','AI and automation']];
  const EDITABLE = ['title','client','decision','domain','context','boundary','constraints','evidence','findings','options','recommendation','counterargument','actions','answers','internal_notes'];
  const REPORT_KEYS = ['report_type','title','client','decision','domain','context','boundary','constraints','evidence','findings','options','recommendation','counterargument','actions','review_id','source_revision','reviewed_at','method_version'];
  const LABELS = {report_type:'Report',title:'Title',client:'Client label',decision:'Decision',domain:'Primary area',context:'Current state',boundary:'System boundary',constraints:'Constraints',evidence:'Evidence reviewed',findings:'Findings',options:'Options considered',recommendation:'Recommendation',counterargument:'Counterargument and uncertainty',actions:'Next actions',review_id:'Review reference',source_revision:'Source revision',reviewed_at:'Owner reviewed at',method_version:'Method version',id:'Reference',label:'Label',detail:'Detail',source:'Source reference',observed_at:'Observation date',scope:'Evidence scope',kind:'Evidence type',evidence_ids:'Evidence references',severity:'Consequence',resolved:'Resolved',contradiction:'Contradictory evidence',cost_assumptions:'Cost and effort assumptions',position:'Position',option_id:'Recommended option reference',owner:'Action owner',acceptance:'Acceptance check'};
  let csrf = '', expires = 0, epoch = 0, items = [], method = null, record = null, draft = null, nextCursor = null;
  let stage = 'mandate', dirty = false, busy = false, conflict = false, preview = null, controlId = 0;
  let clock = null, authenticating = false, visibleBeforeHide = false, createRequestId = '';
  const requests = new Set(), objectURLs = new Set(), disabledStates = new Map();
  const clone = value => JSON.parse(JSON.stringify(value));
  const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = String(text); if (cls) node.className = cls; return node; };
  const date = value => value ? new Intl.DateTimeFormat('en-US',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Phoenix'}).format(new Date(typeof value === 'number' ? value * 1000 : value)) : 'Not recorded';
  function say(value, error = false) { $('drm-status').textContent = value; $('drm-status').setAttribute('role',error ? 'alert' : 'status'); }
  function message(error) { if (error.name !== 'AbortError') say(error.message || 'The operation could not be confirmed. Please retry.',true); }
  function closeDialog(id) { const d = $(id); if (d.open) d.close(); }
  function clearPrivate(reason) {
    epoch += 1; requests.forEach(c => c.abort()); requests.clear();
    if (clock) clearInterval(clock); clock = null;
    csrf = ''; expires = 0; items = []; method = null; record = null; draft = null; preview = null; nextCursor = null;
    dirty = false; busy = false; conflict = false; createRequestId = ''; disabledStates.clear();
    objectURLs.forEach(url => URL.revokeObjectURL(url)); objectURLs.clear();
    ['drm-case-list','drm-editor','drm-questions','drm-report-preview','drm-case-title','drm-case-decision','drm-case-meta','drm-session','drm-size','drm-list-note'].forEach(id => $(id).replaceChildren());
    $('drm-search').value = ''; $('drm-create-form').reset(); $('drm-create-error').textContent = '';
    closeDialog('drm-create-dialog'); closeDialog('drm-report-dialog');
    $('drm-app').hidden = true; $('drm-case').hidden = true; $('drm-empty').hidden = false;
    $('drm-signin').hidden = false; $('drm-signout').hidden = true;
    $('drm-conflict').hidden = true;
    $('drm-load-more').hidden = true;
    if (reason) say(reason,true);
  }
  async function api(path, verb = 'GET', data) {
    const generation = epoch, controller = new AbortController(); requests.add(controller);
    const body = data === undefined ? undefined : JSON.stringify(data);
    if (body && new TextEncoder().encode(body).length > 24000) { requests.delete(controller); throw Error('This request exceeds the 24 KB limit. Shorten the notes and use concise evidence references before saving.'); }
    const timer = setTimeout(() => controller.abort(),20000);
    try {
      const response = await fetch(path,{method:verb,credentials:'same-origin',cache:'no-store',signal:controller.signal,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},...(body ? {body} : {})});
      if (generation !== epoch) throw new DOMException('Session changed','AbortError');
      if (response.status === 401) { clearPrivate('Your owner session has expired. Private content was cleared. Sign in again.'); throw new DOMException('Session expired','AbortError'); }
      let result; try { result = await response.json(); } catch { throw Error('The private service did not return a usable response. This operation is not confirmed.'); }
      if (generation !== epoch) throw new DOMException('Session changed','AbortError');
      if (!response.ok) { const error = Error(result.error || 'The private operation could not be confirmed.'); error.status = response.status; throw error; }
      return result;
    } catch (error) {
      if (error.name === 'AbortError' && generation === epoch && csrf) throw Error('The request timed out. Its result is unknown. Reload saved cases before retrying a creation or review.');
      throw error;
    } finally { clearTimeout(timer); requests.delete(controller); }
  }
  function action(text, fn, cls) {
    const button = el('button',text,cls); button.type = 'button';
    button.addEventListener('click',() => Promise.resolve().then(fn).catch(message)); return button;
  }
  function working(value) {
    busy = value;
    $('drm-new').disabled = value;
    $('drm-signout').disabled = value;
    $('drm-save').disabled = value || !dirty || conflict;
    if (value) {
      document.querySelectorAll('#drm-editor input,#drm-editor textarea,#drm-editor select,#drm-editor button,#drm-questions textarea,#drm-case-list button,#drm-stages button').forEach(n => { if (!disabledStates.has(n)) disabledStates.set(n,n.disabled); n.disabled = true; });
    } else { disabledStates.forEach((disabled,n) => { if (n.isConnected) n.disabled = disabled; }); disabledStates.clear(); }
  }
  function fieldsPayload() { return Object.fromEntries(EDITABLE.filter(key => Object.hasOwn(draft,key)).map(key => [key,draft[key]])); }
  function markDirty() {
    dirty = true; preview = null;
    $('drm-save-state').textContent = conflict ? 'Conflict · edits not saved' : 'Unsaved changes';
    $('drm-save-state').dataset.dirty = 'true'; $('drm-save').disabled = busy || conflict;
    if ($('drm-create-review')) $('drm-create-review').disabled = true;
    if ($('drm-review-ack')) $('drm-review-ack').checked = false;
    updateSize();
  }
  function updateSize() {
    if (!draft) return;
    const bytes = new TextEncoder().encode(JSON.stringify({revision:record.revision,draft:fieldsPayload()})).length;
    $('drm-size').textContent = Math.ceil(bytes / 1024) + ' KB of 24 KB request budget · up to 16 records per collection.';
    if (bytes > 24000) $('drm-size').textContent += ' Over the limit. Shorten content before saving.';
  }
  function input(label,value,onChange,{type='text',max=3000,wide=false,rows=3,options,required=false}={}) {
    const wrapper = el('label',undefined,wide ? 'drm-wide' : '');
    const node = el(options ? 'select' : type === 'textarea' ? 'textarea' : 'input'); node.id = 'drm-field-' + (++controlId);
    const caption = el('span',label); caption.id = node.id + '-label'; wrapper.append(caption); wrapper.htmlFor = node.id; node.setAttribute('aria-labelledby',caption.id);
    if (options) options.forEach(([v,t]) => { const opt = el('option',t); opt.value = v; node.append(opt); });
    else if (type === 'textarea') { node.rows = rows; node.maxLength = max; }
    else { node.type = type; node.maxLength = max; node.autocomplete = 'off'; }
    node.value = value ?? ''; node.required = required;
    node.addEventListener(options ? 'change' : 'input',() => { onChange(node.value); markDirty(); });
    wrapper.append(node); return wrapper;
  }
  function check(label,value,onChange) {
    const wrapper = el('label',undefined,'drm-check'), node = el('input'); node.type = 'checkbox'; node.checked = !!value;
    node.addEventListener('change',() => { onChange(node.checked); markDirty(); }); wrapper.append(node,el('span',label)); return wrapper;
  }
  function note(text) { return el('p',text,'drm-help'); }
  function empty(text) { return el('p',text,'drm-empty-note'); }
  function group() { return el('div',undefined,'drm-fields'); }
  function setRecord(next) {
    record = next; draft = clone(next); dirty = false; conflict = false; preview = null;
    ['evidence','findings','options','actions'].forEach(key => { if (!Array.isArray(draft[key])) draft[key] = []; });
    draft.answers ||= {}; draft.recommendation ||= {position:'defer',detail:'',option_id:''};
    $('drm-conflict').hidden = true; $('drm-empty').hidden = true; $('drm-case').hidden = false;
    $('drm-case-title').textContent = record.title; $('drm-case-decision').textContent = record.decision;
    $('drm-case-meta').textContent = 'Revision ' + record.revision + ' · Saved ' + date(record.updated_at) + ' · Expires ' + date(record.expires_at);
    $('drm-save-state').textContent = 'Saved'; $('drm-save-state').dataset.dirty = 'false'; $('drm-save').disabled = true;
    renderList(); renderEditor(); renderQuestions(); updateSize();
  }
  function renderList() {
    const list = $('drm-case-list'); list.replaceChildren(); const term = $('drm-search').value.trim().toLowerCase();
    const filtered = items.filter(item => (String(item.title) + ' ' + String(item.client || '')).toLowerCase().includes(term));
    if (!filtered.length) list.append(empty(items.length ? 'No cases match this search.' : 'No saved cases yet. Create a case when you have a decision to review.'));
    filtered.forEach(item => {
      const button = action('',() => openCase(item.id),'drm-case-item');
      button.append(el('strong',item.title),el('small',item.client || DOMAINS.find(d => d[0] === item.domain)?.[1] || 'Decision case'),el('small','Saved ' + date(item.updated_at)));
      if (record?.id === item.id) button.setAttribute('aria-current','true'); list.append(button);
    });
  }
  async function loadList(more = false) {
    const response = await api(API + (more && nextCursor ? '?cursor=' + encodeURIComponent(nextCursor) : ''));
    const combined = more ? [...items,...(response.items || [])] : response.items || [];
    items = Array.from(new Map(combined.map(item => [item.id,item])).values()).sort((a,b) => b.updated_at - a.updated_at);
    nextCursor = response.next_cursor || null; $('drm-load-more').hidden = !nextCursor;
    $('drm-list-note').textContent = items.length + ' loaded ' + (items.length === 1 ? 'case' : 'cases') + (response.partial ? '. More cases remain. Search applies to the loaded list.' : '.'); renderList();
  }
  function canLeave() { return !dirty || window.confirm('Discard the unsaved changes in this case? They have not been stored.'); }
  async function openCase(id) {
    if (busy || !canLeave()) return; working(true);
    try { const response = await api(API + '/' + encodeURIComponent(id)); const pack = await api(API + '/method?case_id=' + encodeURIComponent(id)); method = pack.method; setRecord(response.case); say('Private case loaded. Changes are saved only when you choose Save changes.'); }
    finally { working(false); }
  }
  function renderStages() {
    $('drm-stages').replaceChildren(...STAGES.map(([key,title]) => {
      const button = action(title,() => { if (busy) return; stage = key; renderEditor(); $('drm-stage-title').focus({preventScroll:true}); });
      if (key === stage) button.setAttribute('aria-current','step'); return button;
    }));
  }
  function addRecord(collection) {
    if (draft[collection].length >= 16) { say('This collection already has 16 records. Refine the scope or consolidate the evidence.',true); return; }
    const common = {id:crypto.randomUUID()};
    const defaults = {evidence:{label:'',detail:'',source:'',scope:'',observed_at:'',kind:'unknown'},findings:{title:'',detail:'',evidence_ids:[],severity:'risk',resolved:false,contradiction:''},options:{title:'',detail:'',constraints:'',cost_assumptions:''},actions:{detail:'',owner:'',acceptance:''}};
    draft[collection].push({...common,...defaults[collection]}); markDirty(); renderEditor();
    const last = $('drm-editor').querySelectorAll('.drm-card'); last[last.length-1]?.querySelector('input,textarea')?.focus();
  }
  function recordCard(collection,row,index) {
    const card = el('article',undefined,'drm-card'), top = el('div',undefined,'drm-card-top');
    top.append(el('h3',({evidence:'Evidence',findings:'Finding',options:'Option',actions:'Action'})[collection] + ' ' + (index+1)),action('Remove',() => {
      if (!window.confirm('Remove this ' + ({evidence:'evidence record',findings:'finding',options:'option',actions:'action'})[collection] + ' from the draft?')) return;
      draft[collection] = draft[collection].filter(r => r.id !== row.id);
      if (collection === 'evidence') draft.findings.forEach(f => f.evidence_ids = f.evidence_ids.filter(id => id !== row.id));
      if (collection === 'options' && draft.recommendation.option_id === row.id) draft.recommendation.option_id = '';
      markDirty(); renderEditor();
    })); card.append(top); const f = group();
    if (collection === 'evidence') {
      f.append(input('Evidence label',row.label,v => row.label = v,{max:200,wide:true}),input('What this supports or shows',row.detail,v => row.detail = v,{type:'textarea',wide:true}),input('Source reference',row.source,v => row.source = v,{max:500,wide:true}),input('Evidence type',row.kind,v => row.kind = v,{options:[['unknown','Unknown or not reviewed'],['reported','Reported by a stakeholder'],['documented','Documented in an artifact'],['observed','Observed configuration or behavior'],['tested','Reproduced or measured test']]}),input('Observation date',row.observed_at,v => row.observed_at = v,{type:'date'}),input('Scope and environment',row.scope,v => row.scope = v,{max:500,wide:true}));
    } else if (collection === 'findings') {
      f.append(input('Finding title',row.title,v => row.title = v,{max:200,wide:true}),input('Finding and consequence',row.detail,v => row.detail = v,{type:'textarea',max:2000,wide:true}),input('Consequence',row.severity,v => row.severity = v,{options:[['info','Observation'],['risk','Risk requiring attention'],['blocker','Blocking condition']]}),check('Resolved with supporting evidence',row.resolved,v => row.resolved = v),input('Contradictory evidence or uncertainty',row.contradiction,v => row.contradiction = v,{type:'textarea',max:2000,wide:true}));
      const links = el('div',undefined,'drm-wide'); links.append(el('p','Supporting evidence','drm-small')); const choices = el('div',undefined,'drm-evidence-links');
      if (!draft.evidence.length) choices.append(empty('Add an evidence record first. Every finding needs a traceable reference before review.'));
      draft.evidence.forEach((e,i) => choices.append(check((e.label || 'Evidence ' + (i+1)) + ' · ' + e.kind,row.evidence_ids.includes(e.id),checked => { row.evidence_ids = checked ? [...new Set([...row.evidence_ids,e.id])] : row.evidence_ids.filter(id => id !== e.id); })));
      links.append(choices); f.append(links);
    } else if (collection === 'options') {
      f.append(input('Option title',row.title,v => row.title = v,{max:200,wide:true}),input('Approach and trade-offs',row.detail,v => row.detail = v,{type:'textarea',max:2000,wide:true}),input('Constraints, dependencies and feasibility',row.constraints,v => row.constraints = v,{type:'textarea',max:2000,wide:true}),input('Cost and effort assumptions',row.cost_assumptions,v => row.cost_assumptions = v,{type:'textarea',max:2000,wide:true}));
    } else {
      f.append(input('Next action',row.detail,v => row.detail = v,{type:'textarea',max:2000,wide:true}),input('Accountable owner',row.owner,v => row.owner = v,{max:200,wide:true}),input('Acceptance check',row.acceptance,v => row.acceptance = v,{type:'textarea',max:1000,wide:true}));
    }
    card.append(f,el('p','Reference: ' + row.id,'drm-record-id')); return card;
  }
  function renderEditor() {
    if (!draft) return; renderStages(); const box = $('drm-editor'); box.replaceChildren();
    const heading = el('h3',({mandate:'One decision. A clear boundary.',evidence:'What is known, and how.',findings:'Trace every conclusion.',options:'Compare defensible alternatives.',recommendation:'Put a name to the recommendation.',actions:'Make the next step executable.',notes:'The working space stays private.',review:'A deliberate handoff.'})[stage]); heading.id = 'drm-stage-title'; heading.tabIndex = -1; box.append(heading);
    if (stage === 'mandate') {
      box.append(note('Define the decision before expanding the assessment. This review covers the named system or workflow, not the whole estate.'));
      const f = group(); f.append(input('Case title',draft.title,v => draft.title = v,{max:200,wide:true,required:true}),input('Client label',draft.client,v => draft.client = v,{max:200}),input('Primary area',draft.domain,v => { draft.domain = v; renderQuestions(); },{options:DOMAINS}),input('Decision to make',draft.decision,v => draft.decision = v,{type:'textarea',wide:true,required:true}),input('Current state and accountable owner',draft.context,v => draft.context = v,{type:'textarea',wide:true,rows:4}),input('System boundary and exclusions',draft.boundary,v => draft.boundary = v,{type:'textarea',wide:true,rows:4}),input('Constraints and consequences',draft.constraints,v => draft.constraints = v,{type:'textarea',wide:true,rows:4})); box.append(f);
      box.append(note('Retention: ' + record.retention_days + ' days from creation. Expires ' + date(record.expires_at) + '. Editing or reviewing does not renew it. Evidence references should be redacted; do not paste credentials or private source documents.'));
    } else if (['evidence','findings','options','actions'].includes(stage)) {
      const introductions = {evidence:'Keep reported claims separate from documentation, direct observation and testing. A source reference is a traceable pointer, not an invitation to upload sensitive material.',findings:'Link findings to the evidence actually reviewed. Record conflicting observations and distinguish an open blocker from a resolved condition.',options:'Include the current approach and the smallest viable change when they are legitimate choices. Record uncertain estimates as assumptions. Released staff capacity is not automatically cash savings.',actions:'Name who will act and what evidence will demonstrate completion. An action in this report is not authorization to change production.'};
      box.append(note(introductions[stage]));
      if (!draft[stage].length) box.append(empty('No ' + stage + ' recorded. Add only records that belong to this case.'));
      draft[stage].forEach((row,i) => box.append(recordCard(stage,row,i)));
      const add = action('Add ' + ({evidence:'evidence',findings:'finding',options:'option',actions:'action'})[stage],() => addRecord(stage),'drm-add'); add.disabled = draft[stage].length >= 16; box.append(add);
    } else if (stage === 'recommendation') {
      box.append(note('A recommendation is conditional on its evidence and scope. A reviewed report is not client acceptance, security certification or permission to implement.'));
      const f = group(), r = draft.recommendation;
      f.append(input('Position',r.position,v => r.position = v,{options:[['defer','Defer pending evidence or a prerequisite'],['conditional','Proceed only under stated conditions'],['proceed','Recommend proceeding within scope']],wide:true}),input('Recommended option',r.option_id,v => r.option_id = v,{options:[['','No option selected'],...draft.options.map((o,i) => [o.id,o.title || 'Option ' + (i+1)])],wide:true}),input('Recommendation and its conditions',r.detail,v => r.detail = v,{type:'textarea',wide:true,rows:6}),input('Strongest counterargument and what could change the decision',draft.counterargument,v => draft.counterargument = v,{type:'textarea',wide:true,rows:5})); box.append(f);
    } else if (stage === 'notes') {
      box.append(note('These notes and the private question answers are excluded from the client snapshot. Keep them concise and avoid credentials or unnecessary personal data.'));
      box.append(input('Internal working notes',draft.internal_notes,v => draft.internal_notes = v,{type:'textarea',wide:true,rows:12}));
    } else renderReview(box);
    updateSize();
  }
  function renderQuestions() {
    const box = $('drm-questions'); box.replaceChildren(); if (!draft || !method) return;
    const sections = (method.sections || []).filter(s => s.id === 'base' || s.id === draft.domain);
    if (!sections.length) { box.append(empty('No private guidance is available for this area. Your saved case remains usable.')); return; }
    sections.forEach(section => {
      box.append(el('h4',section.title));
      (section.questions || []).forEach(q => {
        const details = el('details'), summary = el('summary',q.prompt); details.append(summary);
        if (q.why || q.hint) details.append(el('p',q.why || q.hint));
        if (q.evidence_to_seek) details.append(el('p','Evidence to seek: ' + (Array.isArray(q.evidence_to_seek) ? q.evidence_to_seek.join('; ') : q.evidence_to_seek)));
        details.append(input('Internal answer',draft.answers[q.id] || '',v => draft.answers[q.id] = v,{type:'textarea',max:2000,rows:3})); box.append(details);
      });
    });
    box.append(el('p','Private method ' + method.version,'drm-small'));
  }
  function reviewIssues() {
    const problems = [], r = draft.recommendation;
    if (dirty) problems.push('Save the current draft before creating a reviewed snapshot.');
    if ((draft.decision || '').trim().length < 10) problems.push('Write the decision to be made.');
    if ((r.detail || '').trim().length < 10) problems.push('Write a substantive recommendation and its conditions.');
    if ((draft.counterargument || '').trim().length < 10) problems.push('Record the strongest counterargument or unresolved uncertainty.');
    if (!draft.evidence.length || draft.evidence.some(e => !e.label.trim() || e.detail.trim().length < 10 || !e.source.trim()) || draft.evidence.every(e => e.kind === 'unknown')) problems.push('Every evidence item needs a label, substantive detail and a source. At least one must have a reviewed evidence type.');
    if (draft.findings.some(f => !f.title.trim() || f.detail.trim().length < 10 || !f.evidence_ids.length)) problems.push('Every finding needs a title, substantive detail and supporting evidence references.');
    if (!draft.actions.length || draft.actions.some(a => a.detail.trim().length < 10 || !a.owner.trim() || a.acceptance.trim().length < 10)) problems.push('Every action needs substantive detail, an owner and a specific acceptance check.');
    if (draft.options.length < (r.position === 'defer' ? 1 : 2)) problems.push(r.position === 'defer' ? 'Document an option even if the decision is deferred.' : 'Compare at least two options.');
    if (draft.options.some(o => !o.title.trim() || o.detail.trim().length < 10)) problems.push('Every option needs a title and substantive explanation.');
    if (r.position !== 'defer' && !r.option_id) problems.push('Select the recommended option.');
    if ((record.reviews || []).length >= 20) problems.push('This case has reached its limit of 20 reviewed snapshots.');
    if (r.position === 'proceed' && draft.findings.some(f => f.severity === 'blocker' && !f.resolved)) problems.push('An unresolved blocker prevents a proceed recommendation.');
    if (r.position === 'proceed' && !draft.evidence.some(e => ['documented','observed','tested'].includes(e.kind))) problems.push('A proceed recommendation needs evidence beyond reported claims.');
    return problems;
  }
  function renderReview(box) {
    box.append(note('Freeze only what you have personally reviewed. Saved snapshots are immutable records of the client-facing fields. Private guidance, answers and internal notes are excluded.'));
    const counts = el('div',undefined,'drm-pills'); ['evidence','findings','options','actions'].forEach(key => counts.append(el('span',draft[key].length + ' ' + key,'drm-pill'))); box.append(counts);
    const issues = reviewIssues();
    if (issues.length) { const alert = el('div',undefined,'drm-alert'); alert.append(el('h3','Before review')); const list = el('ul'); issues.forEach(issue => list.append(el('li',issue))); alert.append(list); box.append(alert); }
    else box.append(note('The minimum review fields are present. This is a completeness check, not an assurance score.'));
    const acknowledge = el('label',undefined,'drm-check'), ack = el('input'); ack.type = 'checkbox'; ack.id = 'drm-review-ack'; acknowledge.append(ack,el('span','I have reviewed the client-facing record, its evidence, conditions and limits. This is my recommendation, not the client’s approval.')); box.append(acknowledge);
    const review = action('Create reviewed snapshot',async () => {
      if (busy || dirty || !ack.checked) return; working(true);
      try {
        const response = await api(API + '/' + record.id + '/review','POST',{revision:record.revision});
        setRecord(response.case); await loadList(); say('Owner-reviewed snapshot saved. Preview it before downloading.');
        showReport(response.review.client_report,'architecture-decision-review-' + response.review.id + '.html');
      } catch(error) { handleConflict(error); throw error; } finally { working(false); }
    },'drm-primary'); review.id = 'drm-create-review'; review.disabled = true; ack.addEventListener('change',() => review.disabled = !ack.checked || issues.length > 0 || busy || dirty); box.append(review);
    const reviews = el('div',undefined,'drm-review-list'); reviews.append(el('h3','Saved review snapshots'));
    if (!record.reviews?.length) reviews.append(empty('No reviewed snapshot yet. Saving a draft does not mark it reviewed.'));
    (record.reviews || []).slice().reverse().forEach(r => { const row = el('div',undefined,'drm-review-row'); row.append(el('p','Revision ' + r.source_revision + ' · ' + date(r.created_at)),action('Preview snapshot',async () => { const response = await api(API + '/' + record.id + '/export?revision=' + encodeURIComponent(r.source_revision)); showReport(response.report,response.filename); })); reviews.append(row); }); box.append(reviews);
    const danger = el('details',undefined,'drm-danger'); danger.append(el('summary','Delete this case and its review snapshots'),note('Deletion removes this case from the private service. Previously downloaded files remain on the devices where they were saved. Recovery backups may retain data until their expiry.'));
    const phrase = 'DELETE ' + record.id; danger.append(el('code',phrase));
    const label = el('label','Type the exact phrase above'), confirm = el('input'); confirm.autocomplete = 'off'; label.append(confirm); danger.append(label,action('Delete case',async () => {
      if (confirm.value !== phrase) throw Error('Enter the exact deletion phrase.'); working(true);
      try { await api(API + '/' + record.id,'DELETE',{revision:record.revision,confirm:phrase}); record = null; draft = null; dirty = false; preview = null; $('drm-case').hidden = true; $('drm-editor').replaceChildren(); $('drm-questions').replaceChildren(); $('drm-empty').hidden = false; await loadList(); say('Case deleted. Existing downloaded reports have not been removed.'); }
      catch(error) { handleConflict(error); throw error; } finally { working(false); }
    })); box.append(danger);
  }
  function handleConflict(error) {
    if (error.status === 409 && record) { conflict = true; $('drm-conflict').hidden = false; $('drm-save-state').textContent = 'Conflict · edits not saved'; $('drm-save').disabled = true; }
  }
  async function save() {
    if (!record || !dirty || busy || conflict) return;
    if (draft.title.trim().length < 3 || !draft.decision.trim()) throw Error('Use at least three characters for the case title and name the decision.');
    working(true); $('drm-save-state').textContent = 'Saving…';
    try { const response = await api(API + '/' + record.id,'PATCH',{revision:record.revision,draft:fieldsPayload()}); setRecord(response.case); await loadList(); say('Changes saved to the private case.'); }
    catch(error) { handleConflict(error); if (draft) { dirty = true; $('drm-save-state').textContent = conflict ? 'Conflict · edits not saved' : 'Save not confirmed'; } throw error; }
    finally { working(false); }
  }
  function reportNode(report) {
    const out = el('div',undefined,'drm-report-content');
    out.append(el('p','Khalid Shams · Architecture Decision Review','drm-report-meta'),el('h2',report.title || 'Architecture decision review'));
    out.append(el('p','Owner-reviewed recommendation. Client acceptance, production approval and any implementation are separate.','drm-report-meta'));
    const renderValue = (value,key) => {
      if (Array.isArray(value)) { const wrap = el('div'); if (!value.length) wrap.append(el('p','None recorded.')); value.forEach((v,i) => { const item = el('article'); if (v && typeof v === 'object') item.append(el('h4',(LABELS[key] || key) + ' ' + (i+1))); item.append(renderValue(v,key)); wrap.append(item); }); return wrap; }
      if (value && typeof value === 'object') { const dl = el('dl'); Object.entries(value).forEach(([k,v]) => { if (!Object.hasOwn(LABELS,k)) return; dl.append(el('dt',LABELS[k])); const dd = el('dd'); dd.append(renderValue(v,k)); dl.append(dd); }); return dl; }
      return el('p',typeof value === 'boolean' ? (value ? 'Yes' : 'No') : key === 'reviewed_at' && typeof value === 'number' ? date(value) : value === '' || value == null ? 'Not recorded.' : value);
    };
    REPORT_KEYS.filter(key => key !== 'title' && Object.hasOwn(report,key)).forEach(key => { out.append(el('h3',LABELS[key]),renderValue(report[key],key)); }); return out;
  }
  function showReport(report,filename) {
    if (!report || typeof report !== 'object' || Array.isArray(report)) throw Error('The reviewed report format could not be read.');
    preview = {caseId:record.id,sourceRevision:report.source_revision,report:clone(report),filename:String(filename || 'architecture-decision-review.html').replace(/[^a-zA-Z0-9_.-]/g,'-').replace(/\.[^.]*$/,'.html')};
    $('drm-report-preview').replaceChildren(reportNode(preview.report)); $('drm-report-dialog').showModal();
  }
  async function downloadReport() {
    if (!preview || !csrf || Date.now() >= expires * 1000) { clearPrivate('Sign in again before exporting private material.'); return; }
    const requested = preview;
    if (!Number.isInteger(requested.sourceRevision)) throw Error('The reviewed revision is missing. Close this preview and open a saved snapshot.');
    $('drm-download').disabled = true;
    let fresh;
    try { fresh = await api(API + '/' + encodeURIComponent(requested.caseId) + '/export?revision=' + encodeURIComponent(requested.sourceRevision)); }
    finally { $('drm-download').disabled = false; }
    if (preview !== requested) return;
    preview.report = fresh.report;
    const doc = document.implementation.createHTMLDocument(preview.report.title || 'Architecture Decision Review');
    const meta = doc.createElement('meta'); meta.charset = 'utf-8'; doc.head.prepend(meta);
    const viewport = doc.createElement('meta'); viewport.name = 'viewport'; viewport.content = 'width=device-width, initial-scale=1'; doc.head.append(viewport);
    const policy = doc.createElement('meta'); policy.httpEquiv = 'Content-Security-Policy'; policy.content = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"; doc.head.append(policy);
    const style = doc.createElement('style'); style.textContent = 'body{font:16px/1.65 system-ui,sans-serif;color:#14202a;background:#fff;margin:0 auto;padding:40px;max-width:850px}h2{font:42px/1.15 Georgia,serif}h3{font:26px Georgia,serif;margin-top:36px;border-top:1px solid #ccd2d9;padding-top:20px}h4,dt{font-size:14px;font-weight:650;margin-top:18px}p,dd{white-space:pre-wrap;overflow-wrap:anywhere}dd{margin:4px 0 16px}article{border-bottom:1px solid #dde2e8;padding-bottom:12px}.drm-report-meta{font-size:12px;color:#52616d}@media print{body{padding:0;font-size:11pt;max-width:none}h3{break-after:avoid}article,dl{break-inside:avoid}@page{margin:18mm}}'; doc.head.append(style);
    doc.body.append(doc.importNode(reportNode(preview.report),true));
    const url = URL.createObjectURL(new Blob(['<!doctype html>\n' + doc.documentElement.outerHTML],{type:'text/html;charset=utf-8'})); objectURLs.add(url);
    const a = el('a'); a.href = url; a.download = preview.filename; a.click(); setTimeout(() => { URL.revokeObjectURL(url); objectURLs.delete(url); },1000);
    say('Reviewed HTML downloaded. It can be printed to PDF from your browser. No client message was sent.');
  }
  function updateClock() {
    const remaining = Math.max(0,expires - Math.floor(Date.now()/1000));
    if (!remaining) { clearPrivate('Your owner session expired. Private content and unsaved edits were cleared. Sign in again.'); return; }
    const text = remaining <= 120 ? 'Session expires in ' + remaining + ' seconds. Save your changes now.' : 'Private session · ' + Math.ceil(remaining/60) + ' minutes remaining';
    if ($('drm-session').textContent !== text) $('drm-session').textContent = text;
  }
  async function authenticate(initial = false) {
    if (authenticating) return; authenticating = true; $('drm-app').hidden = true;
    try {
      const session = await api('/api/auth/session'); if (!session.owner || !session.csrf) throw Error('Owner authorization is required.');
      csrf = session.csrf; expires = session.expires;
      if (expires * 1000 <= Date.now()) { clearPrivate('Your owner session expired. Sign in again.'); return; }
      if (!method || initial) { const result = await api(API + '/method' + (record ? '?case_id=' + encodeURIComponent(record.id) : '')); method = result.method; if (!method?.sections) throw Error('The private method is unavailable. No question content has been loaded.'); }
      await loadList();
      $('drm-app').hidden = false; $('drm-signin').hidden = true; $('drm-signout').hidden = false;
      if (clock) clearInterval(clock); clock = setInterval(updateClock,1000); updateClock();
      if (draft) renderQuestions(); say('Owner access verified. Client information stays in the private workbench.');
    } catch(error) { clearPrivate(); message(error); }
    finally { authenticating = false; }
  }
  $('drm-new').addEventListener('click',() => {
    if (busy || !canLeave()) return;
    createRequestId = crypto.randomUUID(); $('drm-create-form').reset(); $('drm-create-error').textContent = ''; $('drm-create-dialog').showModal();
  });
  $('drm-create-close').onclick = () => closeDialog('drm-create-dialog');
  $('drm-report-close').onclick = () => { closeDialog('drm-report-dialog'); $('drm-report-preview').replaceChildren(); preview = null; };
  $('drm-report-dialog').addEventListener('cancel',() => { $('drm-report-preview').replaceChildren(); preview = null; });
  $('drm-create-form').addEventListener('submit',async event => {
    event.preventDefault(); const form = event.currentTarget; if (busy || !form.reportValidity()) return;
    const values = Object.fromEntries(new FormData(form)); values.retention_days = Number(values.retention_days); values.request_id = createRequestId || (createRequestId = crypto.randomUUID());
    const submit = form.querySelector('button[type=submit]'); submit.disabled = true; working(true); $('drm-create-error').textContent = '';
    try { const response = await api(API,'POST',values); createRequestId = ''; closeDialog('drm-create-dialog'); stage = 'mandate'; const pack = await api(API + '/method?case_id=' + encodeURIComponent(response.case.id)); method = pack.method; setRecord(response.case); await loadList(); say('Private case created. Add evidence from the real review.'); }
    catch(error) { if (error.name !== 'AbortError') $('drm-create-error').textContent = error.message; message(error); }
    finally { submit.disabled = false; working(false); }
  });
  $('drm-save').onclick = () => save().catch(message);
  $('drm-reload').onclick = () => { if (record && canLeave()) { const id = record.id; dirty = false; openCase(id).catch(message); } };
  $('drm-search').oninput = renderList;
  $('drm-load-more').onclick = async () => { if (busy || !nextCursor) return; $('drm-load-more').disabled = true; working(true); try { await loadList(true); } catch(error) { message(error); } finally { $('drm-load-more').disabled = false; working(false); } };
  $('drm-download').onclick = () => downloadReport().catch(message);
  $('drm-signout').onclick = async () => {
    if (!canLeave()) return;
    try { const result = await api('/api/auth/logout','POST',{}); clearPrivate('Signed out.'); location.assign(result.logout); }
    catch(error) { clearPrivate('Private content cleared. Sign-out could not be confirmed.'); message(error); }
  };
  addEventListener('beforeunload',event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  addEventListener('pagehide',() => clearPrivate());
  addEventListener('pageshow',event => { if (event.persisted) authenticate(true); });
  document.addEventListener('visibilitychange',() => {
    if (document.hidden) { visibleBeforeHide = ! $('drm-app').hidden; $('drm-app').hidden = true; closeDialog('drm-report-dialog'); closeDialog('drm-create-dialog'); $('drm-report-preview').replaceChildren(); preview = null; }
    else if (visibleBeforeHide) { visibleBeforeHide = false; authenticate(); }
  });
  authenticate(true);
})();
