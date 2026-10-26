(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('video-studio')) return;
  const API = '/api/admin/assessments/videos';
  const STAGES = ['research','script','rehearsal','ready','recorded'];
  const TABS = [['brief','The decision'],['beats','Shooting plan'],['sources','Evidence'],['readiness','Get ready'],['transcript','Transcript']];
  const CHECKS = [['evidence','I checked the claims, source dates and limits.'],['clarity','The decision, audience and takeaway are clear.'],['rehearsal','I rehearsed the words and every screen action.'],['privacy','My screen and script contain no credentials or private client details.'],['save','I know exactly which artifacts to save after recording.']];
  const requests = new Set(), objectURLs = new Set();
  let csrf = '', expires = 0, epoch = 0, catalog = null, items = [], nextCursor = null, record = null, draft = null;
  let dirty = false, conflict = false, busy = false, tab = 'brief', view = 'research', controlId = 0, createRequestId = '';
  let sessionClock = null, authGeneration = null, resumeOnVisible = false, rehearsalIndex = 0, timer = null, timerStarted = 0, elapsed = 0;
  const clone = value => JSON.parse(JSON.stringify(value));
  const el = (tag,text,cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = String(text); if (cls) n.className = cls; return n; };
  const date = value => { const d = new Date(typeof value === 'number' ? value * 1000 : /^\d{4}-\d{2}-\d{2}$/.test(value || '') ? value + 'T12:00:00-07:00' : value); return Number.isNaN(d.valueOf()) ? 'Not recorded' : new Intl.DateTimeFormat('en-US',{dateStyle:'medium',timeZone:'America/Phoenix'}).format(d); };
  function say(value,error = false) { $('vs-status').textContent = value; $('vs-status').setAttribute('role',error ? 'alert' : 'status'); }
  function message(error) { if (error.name !== 'AbortError') say(error.message || 'This operation could not be confirmed. Please retry.',true); }
  function action(text,fn,cls) { const b = el('button',text,cls); b.type = 'button'; b.addEventListener('click',() => Promise.resolve().then(fn).catch(message)); return b; }
  function closeDialog(id) { if ($(id).open) $(id).close(); }
  function stopTimer() { if (timer) { elapsed += Date.now() - timerStarted; clearInterval(timer); timer = null; } $('vs-timer-toggle').textContent = 'Start timer'; }
  function closeRehearsal() { stopTimer(); closeDialog('vs-rehearsal-dialog'); ['vs-rehearsal-title','vs-rehearsal-position','vs-rehearsal-script','vs-rehearsal-cues'].forEach(id => $(id).replaceChildren()); }
  function invalidateRequests() { epoch += 1; requests.forEach(c => c.abort()); requests.clear(); authGeneration = null; }
  function clearPrivate(reason) {
    invalidateRequests(); if (sessionClock) clearInterval(sessionClock); sessionClock = null;
    csrf = ''; expires = 0; catalog = null; items = []; nextCursor = null; record = null; draft = null; dirty = false; busy = false; conflict = false; createRequestId = ''; resumeOnVisible = false;
    objectURLs.forEach(url => URL.revokeObjectURL(url)); objectURLs.clear();
    ['vs-topic-list','vs-templates','vs-video-list','vs-editor','vs-video-title','vs-video-decision','vs-video-meta','vs-session','vs-size','vs-list-note','vs-ranking','vs-catalog-date','vs-progress'].forEach(id => $(id).replaceChildren());
    $('vs-search').value = ''; $('vs-create-form').reset(); $('vs-create-error').textContent = ''; $('vs-count').textContent = '0';
    closeDialog('vs-create-dialog'); closeRehearsal();
    $('vs-app').hidden = true; $('vs-workbench').hidden = true; $('vs-empty').hidden = false; $('vs-signin').hidden = false; $('vs-signout').hidden = true; $('vs-conflict').hidden = true; $('vs-load-more').hidden = true;
    if (reason) say(reason,true);
  }
  async function api(path,verb = 'GET',data,token = csrf) {
    const generation = epoch, controller = new AbortController(); requests.add(controller);
    const body = data === undefined ? undefined : JSON.stringify(data);
    if (body && new TextEncoder().encode(body).length > 24000) { requests.delete(controller); throw Error('This request exceeds the 24 KB limit. Shorten the script, notes or references before saving.'); }
    const timeout = setTimeout(() => controller.abort(),20000);
    try {
      const response = await fetch(path,{method:verb,credentials:'same-origin',cache:'no-store',signal:controller.signal,headers:{'Content-Type':'application/json','X-CSRF-Token':token},...(body ? {body} : {})});
      if (generation !== epoch) throw new DOMException('Session changed','AbortError');
      if (response.status === 401) { clearPrivate('Your owner session expired. Private content and unsaved edits were cleared. Sign in again.'); throw new DOMException('Session expired','AbortError'); }
      let result; try { result = await response.json(); } catch { throw Error('The private service did not return a usable response. This operation is not confirmed.'); }
      if (generation !== epoch) throw new DOMException('Session changed','AbortError');
      if (!response.ok) { const error = Error(result.error || 'The private operation could not be confirmed.'); error.status = response.status; throw error; }
      return result;
    } catch(error) { if (error.name === 'AbortError' && generation === epoch && csrf) throw Error('The request timed out. Its result is unknown. Reload the saved episode before retrying a change.'); throw error; }
    finally { clearTimeout(timeout); requests.delete(controller); }
  }
  function working(value) {
    busy = value;
    document.querySelectorAll('#vs-app button,#vs-editor input,#vs-editor textarea,#vs-editor select').forEach(n => { n.disabled = value; });
    if (!value) updateControls();
  }
  function updateControls() {
    $('vs-save').disabled = busy || !dirty || conflict;
    $('vs-export-pack').disabled = busy || !record || dirty || conflict;
    $('vs-export-script').disabled = busy || !record || dirty || conflict || !draft?.beats?.some(b => b.spoken?.trim());
    $('vs-export-transcript').disabled = busy || !record || dirty || conflict || !draft?.transcript?.trim();
    $('vs-rehearse').disabled = busy || !draft?.beats?.length;
    $('vs-load-more').disabled = busy || !nextCursor;
    $('vs-export-note').textContent = dirty ? 'Save these edits before downloading. Each download stays on your device.' : 'Downloads use the freshly authorized saved episode. Each download stays on your device.';
    document.querySelectorAll('[data-limit]').forEach(n => { n.disabled = busy || Number(n.dataset.limit) <= Number(n.dataset.count); });
    document.querySelectorAll('[data-boundary="true"]').forEach(n => { n.disabled = true; });
  }
  function showView(next) {
    view = next; $('vs-research').hidden = next !== 'research'; $('vs-library').hidden = next !== 'library';
    ['research','library'].forEach(key => { const button = $('vs-' + key + '-nav'); if (key === next) button.setAttribute('aria-current','page'); else button.removeAttribute('aria-current'); });
  }
  function sourceURL(value) { try { const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password ? u.href : null; } catch { return null; } }
  function sourceList(sources) {
    const list = el('ul',undefined,'vs-sources');
    (sources || []).forEach(source => { const row = el('li'), url = sourceURL(source.url); if (url) { const a = el('a',source.title || url); a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; row.append(a); } else row.append(el('span',source.title || 'Source URL needs review')); if (source.note) row.append(el('p',source.note)); list.append(row); }); return list;
  }
  function renderCatalog() {
    $('vs-topic-list').replaceChildren(); $('vs-templates').replaceChildren();
    $('vs-ranking').textContent = catalog.ranking_note || 'Editorial priority based on evidence and the consequences of a decision. This is not a price or revenue ranking.';
    (catalog.topics || []).forEach((topic,index) => {
      const card = el('article',undefined,'vs-topic'); card.append(el('span',String(index + 1).padStart(2,'0') + ' · RESEARCH PRIORITY','vs-topic-number'),el('h3',topic.title),el('p',topic.decision,'vs-question'),el('p',topic.why,'vs-small'));
      const details = el('details'); details.append(el('summary','First episode and primary sources'),el('p',topic.first_episode || 'Choose one decision to explain.'),sourceList(topic.sources)); card.append(details); $('vs-topic-list').append(card);
    });
    (catalog.templates || []).forEach(template => {
      const card = el('article',undefined,'vs-template'); card.append(el('div',(template.beats || []).length + ' BEATS · AUTHORED TEACHING DRAFT','vs-template-meta'),el('h3',template.title),el('p',template.premise || template.decision));
      const details = el('details'); details.append(el('summary','See the audience and decision'),el('p','For: ' + (template.audience || 'Define the audience.')),el('p',template.decision || ''),sourceList(template.sources)); card.append(details);
      const start = action('Start this episode →',() => openCreate(template),'vs-primary'); start.dataset.template = template.id; card.append(start); $('vs-templates').append(card);
    });
    if (!catalog.topics?.length) $('vs-topic-list').append(el('p','Research topics are not available. You can still work on your saved episodes.','vs-empty-note'));
    if (!catalog.templates?.length) $('vs-templates').append(el('p','No authored teaching drafts are available. Start a new episode from your own decision.','vs-empty-note'));
    $('vs-catalog-date').textContent = 'Research checked ' + date(catalog.checked_at) + '. Sources support the stated claims; they do not prove a promised client outcome.';
  }
  function renderList() {
    const list = $('vs-video-list'); list.replaceChildren(); const term = $('vs-search').value.toLowerCase().trim();
    const filtered = items.filter(item => String(item.title).toLowerCase().includes(term));
    if (!filtered.length) list.append(el('p',items.length ? 'No loaded episodes match this search.' : 'No saved episodes yet. Start from the research desk or create your own.','vs-empty-note'));
    filtered.forEach(item => { const b = action('',() => openVideo(item.id),'vs-video-item'); b.append(el('strong',item.title),el('small',(item.stage || 'research') + ' · Revision ' + item.revision),el('small','Saved ' + date(item.updated_at))); if (item.id === record?.id) b.setAttribute('aria-current','true'); list.append(b); });
    $('vs-count').textContent = String(items.length);
  }
  async function loadList(more = false) {
    const result = await api(API + (more && nextCursor ? '?cursor=' + encodeURIComponent(nextCursor) : ''));
    items = Array.from(new Map((more ? [...items,...(result.items || [])] : result.items || []).map(item => [item.id,item])).values());
    nextCursor = result.next_cursor || null; $('vs-load-more').hidden = !nextCursor; $('vs-list-note').textContent = items.length + ' loaded. Search applies to this list.'; renderList();
  }
  async function refreshAfterWrite(success) { try { await loadList(); say(success); } catch(error) { if (error.name !== 'AbortError') say(success + ' The episode list could not refresh. Reload it when ready.',true); } }
  function canLeave() { return !dirty || window.confirm('Discard unsaved changes in this episode?'); }
  async function openVideo(id) {
    if (busy || !canLeave()) return; working(true);
    try { const result = await api(API + '/' + encodeURIComponent(id)); setRecord(result.video); showView('library'); }
    finally { working(false); }
  }
  function setRecord(next) {
    if (!next?.draft) throw Error('The saved episode has no readable draft.');
    record = next; draft = clone(next.draft); dirty = false; conflict = false;
    ['beats','checklist','sources'].forEach(key => { if (!Array.isArray(draft[key])) draft[key] = []; });
    $('vs-empty').hidden = true; $('vs-workbench').hidden = false; $('vs-conflict').hidden = true;
    $('vs-video-title').textContent = draft.title; $('vs-video-decision').textContent = draft.decision || 'Define the decision this episode helps someone make.';
    $('vs-video-meta').textContent = 'Revision ' + next.revision + ' · Saved ' + date(next.updated_at) + ' · Expires ' + date(next.expires_at);
    $('vs-save-state').textContent = 'Saved'; $('vs-save-state').dataset.dirty = 'false';
    renderProgress(); renderTabs(); renderEditor(); renderList(); updateSize(); updateControls();
  }
  function markDirty(content = true) {
    if (content && ['ready','recorded'].includes(draft.stage)) { draft.stage = 'rehearsal'; draft.checklist.forEach(item => { item.done = false; }); renderProgress(); if ($('vs-stage')) $('vs-stage').value = draft.stage; say('Content changed. Rehearse and recheck readiness before marking this episode ready again.'); }
    dirty = true; $('vs-save-state').textContent = conflict ? 'Conflict · edits not saved' : 'Unsaved changes'; $('vs-save-state').dataset.dirty = 'true'; updateSize(); updateControls();
  }
  function updateSize() { if (draft) $('vs-size').textContent = Math.ceil(new TextEncoder().encode(JSON.stringify({revision:record.revision,draft})).length/1024) + ' KB of 24 KB request budget · up to 12 beats, 8 sources and 16 preparation checks.'; }
  function renderProgress() { $('vs-progress').replaceChildren(); STAGES.forEach((stage,i) => { const n = el('span',String(i+1).padStart(2,'0') + ' ' + stage,'vs-step'); if (draft.stage === stage) n.setAttribute('aria-current','step'); $('vs-progress').append(n); }); }
  function renderTabs() { $('vs-tabs').replaceChildren(); TABS.forEach(([key,title]) => { const b = action(title,() => { tab = key; renderTabs(); renderEditor(); }); b.dataset.tab = key; if (key === tab) b.setAttribute('aria-current','page'); $('vs-tabs').append(b); }); }
  function field(label,value,onChange,{type='textarea',max=2000,rows=3,wide=false,id,options,min,content=true}={}) {
    const wrapper = el('label',undefined,wide ? 'vs-wide' : ''), n = el(options ? 'select' : type === 'textarea' ? 'textarea' : 'input'); n.id = id || 'vs-field-' + (++controlId); wrapper.htmlFor = n.id; wrapper.append(el('span',label));
    if (options) options.forEach(([v,t]) => { const option = el('option',t); option.value = v; n.append(option); });
    else if (type === 'textarea') { n.rows = rows; n.maxLength = max; } else { n.type = type; n.autocomplete = 'off'; if (type === 'number') { n.min = min; n.max = max; } else n.maxLength = max; }
    n.value = value ?? ''; n.addEventListener(options ? 'change' : 'input',() => { onChange(type === 'number' ? Number(n.value) : n.value); markDirty(content); }); wrapper.append(n); return wrapper;
  }
  function help(text) { return el('p',text,'vs-help'); }
  function renderEditor() {
    const out = $('vs-editor'); out.replaceChildren(); const form = el('div',undefined,'vs-form'); out.append(form); if (!draft) return;
    if (tab === 'brief') renderBrief(form);
    if (tab === 'beats') renderBeats(form);
    if (tab === 'sources') renderSources(form);
    if (tab === 'readiness') renderReadiness(form);
    if (tab === 'transcript') renderTranscript(form);
    updateControls();
  }
  function renderBrief(form) {
    form.append(el('h3','What will someone decide?'),help('Name the business decision before the demonstration. Make the tradeoff visible, name the evidence and say what remains uncertain.'));
    form.append(field('Episode title',draft.title,v => draft.title = v,{type:'text',max:200,id:'vs-title'}),field('The decision',draft.decision,v => draft.decision = v,{id:'vs-decision'}),field('Premise and takeaway',draft.premise,v => draft.premise = v,{id:'vs-premise'}),field('Who this is for',draft.audience,v => draft.audience = v,{id:'vs-audience',rows:2}),field('Preparation notes',draft.notes,v => draft.notes = v,{max:3000,id:'vs-notes',rows:5}));
  }
  function renderBeats(form) {
    const duration = draft.beats.reduce((n,b) => n + (Number(b.seconds)||0),0);
    form.append(el('h3','The words, the clicks, the handoff.'),help('Each beat separates what I say, what I do and what Codex prepares. The spoken script is a draft for rehearsal. It is never labelled as a recorded transcript.'),el('p',draft.beats.length + ' beats · Planned duration ' + Math.floor(duration/60) + 'm ' + duration%60 + 's','vs-small'));
    if (!draft.beats.length) form.append(el('p','Add the opening beat: the business decision and why it matters.','vs-empty-note'));
    draft.beats.forEach((beat,index) => {
      const card = el('article',undefined,'vs-card'), top = el('div',undefined,'vs-card-top'), actions = el('div'); top.append(el('h3',String(index+1).padStart(2,'0') + ' · ' + (beat.label || 'Untitled beat')));
      const up = action('↑ Move up',() => { [draft.beats[index-1],draft.beats[index]] = [draft.beats[index],draft.beats[index-1]]; markDirty(); renderEditor(); }); up.dataset.boundary = String(index === 0);
      const down = action('↓ Move down',() => { [draft.beats[index+1],draft.beats[index]] = [draft.beats[index],draft.beats[index+1]]; markDirty(); renderEditor(); }); down.dataset.boundary = String(index === draft.beats.length-1);
      actions.append(up,down,action('Remove',() => { if (window.confirm('Remove this beat and its script from the draft?')) { draft.beats.splice(index,1); markDirty(); renderEditor(); } })); top.append(actions); card.append(top);
      const fields = el('div',undefined,'vs-fields'); fields.append(field('Beat label',beat.label,v => beat.label = v,{type:'text',max:200}),field('Planned seconds',beat.seconds,v => beat.seconds = v,{type:'number',min:10,max:180}),field('What I say · Draft spoken script',beat.spoken,v => beat.spoken = v,{max:1800,rows:5,wide:true}),field('What I click · Screen actions',beat.screen,v => beat.screen = v,{max:1200}),field('What the viewer sees · Visual',beat.visual,v => beat.visual = v,{max:1200}),field('What Khalid does',beat.khalid,v => beat.khalid = v,{max:1200}),field('What Codex prepares',beat.codex,v => beat.codex = v,{max:1200}),field('What I save after this beat',beat.save,v => beat.save = v,{max:800,rows:2,wide:true})); card.append(fields); form.append(card);
    });
    const add = action('+ Add a beat',() => { if (draft.beats.length >= 12) return; draft.beats.push({id:crypto.randomUUID(),label:'',seconds:45,spoken:'',screen:'',visual:'',khalid:'',codex:'',save:''}); markDirty(); renderEditor(); },'vs-add'); add.id = 'vs-add-beat'; add.dataset.limit = '12'; add.dataset.count = draft.beats.length; form.append(add);
  }
  function renderSources(form) {
    form.append(el('h3','Evidence I can stand behind.'),help('Keep primary source links and the exact claim each supports. Note the source date, uncertainty and what the evidence cannot establish. HTTPS links only.'));
    draft.sources.forEach((source,index) => {
      const card = el('article',undefined,'vs-card'), top = el('div',undefined,'vs-card-top'); top.append(el('h3','Source ' + (index+1)),action('Remove source',() => { draft.sources.splice(index,1); markDirty(); renderEditor(); })); card.append(top);
      const fields = el('div',undefined,'vs-fields'); fields.append(field('Source title',source.title,v => source.title = v,{type:'text',max:200}),field('Source URL · HTTPS',source.url,v => source.url = v,{type:'url',max:600}),field('Claim supported, date and limits',source.note,v => source.note = v,{max:1500,wide:true})); card.append(fields,sourceList([source])); form.append(card);
    });
    if (!draft.sources.length) form.append(el('p','No evidence references yet. Add the source behind the decision.','vs-empty-note'));
    const add = action('+ Add a source',() => { if (draft.sources.length >= 8) return; draft.sources.push({title:'',url:'',note:''}); markDirty(); renderEditor(); },'vs-add'); add.id = 'vs-add-source'; add.dataset.limit = '8'; add.dataset.count = draft.sources.length; form.append(add);
  }
  function readinessIssues() {
    const issues = [];
    if ((draft.decision || '').trim().length < 10) issues.push('Write a clear decision.');
    if (!draft.beats.length || draft.beats.some(b => (b.spoken || '').trim().length < 20 || (b.screen || '').trim().length < 10) || draft.beats.reduce((n,b) => n + (b.spoken || '').trim().length,0) < 120) issues.push('Write at least 120 spoken characters overall, with 20 spoken characters and 10 screen instruction characters in every beat.');
    if (draft.beats.some(b => !(b.khalid || '').trim() || !(b.codex || '').trim())) issues.push('Give every beat a Khalid action and Codex preparation.');
    if (draft.checklist.some(c => !CHECKS.some(([id]) => id === c.id) && !c.done)) issues.push('Complete every added preparation check.');
    CHECKS.forEach(([id]) => { if (!draft.checklist.some(c => c.id === id && c.done)) issues.push('Complete the ' + id + ' preparation check.'); });
    return issues;
  }
  function renderReadiness(form) {
    form.append(el('h3','Get ready, deliberately.'),help('These are my preparation checks, not a quality score. Mark ready only after checking the evidence and rehearsing the actual screen. Any later content edit resets readiness.'));
    const checks = [...CHECKS.map(([id,label]) => draft.checklist.find(c => c.id === id) || {id,label,done:false}),...draft.checklist.filter(c => !CHECKS.some(([id]) => c.id === id))];
    checks.forEach(check => { const label = el('label',undefined,'vs-check'), input = el('input'); input.type = 'checkbox'; input.checked = !!check.done; input.id = 'vs-check-' + check.id;
      input.addEventListener('change',() => { let existing = draft.checklist.find(c => c.id === check.id); if (!existing) { existing = clone(check); draft.checklist.push(existing); } existing.done = input.checked; if (!input.checked && ['ready','recorded'].includes(draft.stage)) { draft.stage = 'rehearsal'; draft.checklist.forEach(c => { c.done = false; }); renderProgress(); if ($('vs-stage')) $('vs-stage').value = draft.stage; document.querySelectorAll('#vs-editor .vs-check input').forEach(n => { n.checked = false; }); } markDirty(false); renderReadinessStatus(); }); label.append(input,el('span',check.label || 'Name this preparation check')); form.append(label);
      if (!CHECKS.some(([id]) => id === check.id)) { const row = el('div',undefined,'vs-fields'); row.append(field('Preparation check wording',check.label,v => { const c = draft.checklist.find(item => item.id === check.id); c.label = v; },{type:'text',max:300}),action('Remove this preparation check',() => { draft.checklist = draft.checklist.filter(c => c.id !== check.id); markDirty(); renderEditor(); })); form.append(row); }
    });
    const add = action('+ Add a preparation check',() => { if (draft.checklist.length >= 16) return; draft.checklist.push({id:crypto.randomUUID(),label:'',done:false}); markDirty(); renderEditor(); },'vs-add'); add.id = 'vs-add-check'; add.dataset.limit = '16'; add.dataset.count = draft.checklist.length; form.append(add);
    const state = el('div'); state.id = 'vs-readiness-state'; form.append(state);
    form.append(field('Episode stage',draft.stage,v => { if (['ready','recorded'].includes(draft.stage) && !['ready','recorded'].includes(v)) { draft.checklist.forEach(c => { c.done = false; }); document.querySelectorAll('#vs-editor .vs-check input').forEach(n => { n.checked = false; }); } draft.stage = v; renderProgress(); renderReadinessStatus(); },{id:'vs-stage',options:STAGES.map(s => [s,s[0].toUpperCase()+s.slice(1)]),content:false}),help('Ready and recorded require a meaningful script and every required check. Recorded means I have actually recorded it; this studio does not capture audio or video.'));
    renderReadinessStatus(); renderDelete(form);
  }
  function renderReadinessStatus() { const box = $('vs-readiness-state'); if (!box) return; box.replaceChildren(); const issues = readinessIssues(); if (issues.length) { const list = el('ul'); issues.forEach(issue => list.append(el('li',issue))); const alert = el('div',undefined,'vs-alert'); alert.append(el('h3','Before I mark ready'),list); box.append(alert); } else box.append(el('p','The preparation checks are complete. I can mark the episode ready after my own review.','vs-ready-note')); }
  function renderTranscript(form) {
    form.append(el('h3','What was actually said.'),help('Paste the transcript from the actual recording here. This is separate from the draft spoken script in the shooting plan. No automatic transcription runs in this studio.'),field('Recorded transcript · Plain text',draft.transcript,v => draft.transcript = v,{max:9000,rows:16,id:'vs-transcript'}));
    if (!draft.transcript?.trim()) form.append(el('p','No recorded transcript has been added. The shooting pack still includes the draft spoken script.','vs-empty-note'));
  }
  function renderDelete(form) {
    const details = el('details',undefined,'vs-danger'), phrase = 'DELETE ' + record.id; details.append(el('summary','Delete this private episode'),help('This removes the saved episode. Existing downloads stay on the devices where they were saved. Recovery backups may retain data until expiry.'),el('code',phrase));
    const label = el('label','Type the exact deletion phrase'), input = el('input'); input.id = 'vs-delete-confirm'; input.autocomplete = 'off'; label.append(input); details.append(label);
    const button = action('Delete episode',async () => {
      if (busy || input.value !== phrase) throw Error('Enter the exact deletion phrase.'); working(true);
      try { await api(API + '/' + encodeURIComponent(record.id),'DELETE',{revision:record.revision,confirm:phrase}); record = null; draft = null; dirty = false; conflict = false; $('vs-workbench').hidden = true; $('vs-editor').replaceChildren(); $('vs-empty').hidden = false; await refreshAfterWrite('Episode deleted. Downloaded copies stay on your device.'); }
      catch(error) { handleConflict(error); throw error; } finally { working(false); }
    }); button.id = 'vs-delete'; details.append(button); form.append(details);
  }
  function handleConflict(error) { if (error.status === 409 && record) { conflict = true; $('vs-conflict').hidden = false; $('vs-save-state').textContent = 'Conflict · edits not saved'; updateControls(); } }
  function validateDraft() {
    if ((draft.title || '').trim().length < 3) throw Error('Use at least three characters for the episode title.');
    if (draft.beats.some(b => !Number.isInteger(b.seconds) || b.seconds < 10 || b.seconds > 180)) throw Error('Each beat needs a whole number of seconds from 10 to 180.');
    if (draft.checklist.some(c => !c.label?.trim())) throw Error('Give every preparation check clear wording.');
    if (draft.sources.some(s => !s.title?.trim())) throw Error('Give every evidence source a title.');
    if (draft.sources.some(s => !sourceURL(s.url))) throw Error('Each evidence source needs a valid HTTPS URL without embedded credentials.');
    if (['ready','recorded'].includes(draft.stage) && readinessIssues().length) throw Error('Complete the script and every required preparation check before marking ready or recorded.');
  }
  async function save() {
    if (!record || !dirty || busy || conflict) return; validateDraft(); working(true); $('vs-save-state').textContent = 'Saving…';
    try { const result = await api(API + '/' + encodeURIComponent(record.id),'PATCH',{revision:record.revision,draft}); setRecord(result.video); await refreshAfterWrite('Episode saved to the private studio.'); }
    catch(error) { handleConflict(error); if (draft) { dirty = true; $('vs-save-state').textContent = conflict ? 'Conflict · edits not saved' : 'Save not confirmed'; } throw error; }
    finally { working(false); }
  }
  function openCreate(template) {
    if (busy || !canLeave()) return; createRequestId = crypto.randomUUID(); $('vs-create-form').reset(); $('vs-create-error').textContent = '';
    $('vs-create-form').elements.title.value = template?.title || ''; $('vs-create-form').elements.template_id.value = template?.id || '';
    $('vs-create-note').textContent = template ? 'Create your editable copy of this authored teaching draft. Verify its claims and adapt the words before recording.' : 'Start with a real question you want to explain. Build the script and recording plan one beat at a time.';
    $('vs-create-dialog').showModal();
  }
  function renderRehearsal() {
    const beat = draft?.beats[rehearsalIndex]; if (!beat) return;
    document.querySelector('.vs-rehearsal-grid').scrollTop = 0;
    $('vs-rehearsal-title').textContent = beat.label || 'Untitled beat'; $('vs-rehearsal-position').textContent = 'Beat ' + (rehearsalIndex+1) + ' of ' + draft.beats.length + ' · Planned ' + beat.seconds + ' seconds' + (dirty ? ' · Unsaved draft' : ' · Saved draft');
    $('vs-rehearsal-script').textContent = beat.spoken || 'Add the words for this beat in the shooting plan.'; const cues = $('vs-rehearsal-cues'); cues.replaceChildren();
    [['screen','What I click'],['visual','What the viewer sees'],['khalid','What Khalid does'],['codex','What Codex prepares'],['save','What I save']].forEach(([key,label]) => { cues.append(el('h3',label),el('p',beat[key] || 'Not prepared yet.')); });
    $('vs-rehearsal-prev').disabled = rehearsalIndex === 0; $('vs-rehearsal-next').disabled = rehearsalIndex === draft.beats.length-1;
  }
  function timerText() { const seconds = Math.floor((elapsed + (timer ? Date.now()-timerStarted : 0))/1000); $('vs-rehearsal-timer').textContent = String(Math.floor(seconds/60)).padStart(2,'0') + ':' + String(seconds%60).padStart(2,'0'); }
  const md = value => String(value || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  function shootingPack(video) {
    const d = video.draft, lines = ['# ' + md(d.title),'','Private shooting pack. Draft spoken script, not a recorded transcript.','Revision ' + video.revision + ' | Stage: ' + d.stage + ' | Saved ' + date(video.updated_at) + ' | Expires ' + date(video.expires_at),'','## The decision',md(d.decision),'','## Audience',md(d.audience),'','## Premise',md(d.premise),'','## Preparation notes',md(d.notes),'','## Readiness'];
    CHECKS.forEach(([id,label]) => { const c = (d.checklist || []).find(item => item.id === id); lines.push('- [' + (c?.done ? 'x' : ' ') + '] ' + md(c?.label || label)); });
    (d.checklist || []).filter(c => !CHECKS.some(([id]) => id === c.id)).forEach(c => lines.push('- [' + (c.done ? 'x' : ' ') + '] ' + md(c.label)));
    (d.beats || []).forEach((b,i) => { lines.push('','## Beat ' + (i+1) + ': ' + md(b.label),'Planned duration: ' + b.seconds + ' seconds'); [['spoken','What I say: draft spoken script'],['screen','What I click'],['visual','What the viewer sees'],['khalid','What Khalid does'],['codex','What Codex prepares'],['save','What I save']].forEach(([key,label]) => lines.push('','### ' + label,md(b[key]) || 'Not prepared.')); });
    lines.push('','## Primary sources'); (d.sources || []).forEach(s => lines.push('',md(s.title),sourceURL(s.url) || 'Invalid source URL',md(s.note))); if (!d.sources?.length) lines.push('No evidence sources saved.');
    lines.push('','## Recorded transcript status',d.transcript?.trim() ? 'An actual recorded transcript has been added. Download the separate transcript file.' : 'No actual recorded transcript has been added.','', 'This download stays on your device. It is not a publication or a client result.'); return lines.join('\n');
  }
  async function download(kind) {
    if (!record || dirty || busy || conflict) throw Error('Save the episode before downloading.'); const id = record.id, revision = record.revision; working(true);
    try {
      const session = await api('/api/auth/session'); if (!session.owner || !session.csrf || session.expires * 1000 <= Date.now()) { clearPrivate('Sign in again before downloading private material.'); return; } if (csrf && csrf !== session.csrf) { clearPrivate('Your owner session changed. Previous private work was cleared.'); await authenticate(); return; } csrf = session.csrf; expires = session.expires;
      const response = await api(API + '/' + encodeURIComponent(id)); if (!record || record.id !== id || document.hidden) return;
      if (response.video.revision !== revision) { const error = Error('The saved episode changed. Reload it before downloading.'); error.status = 409; throw error; }
      const video = response.video; if (kind === 'transcript' && !video.draft.transcript?.trim()) throw Error('Add the actual recorded transcript before downloading it.');
      const content = kind === 'pack' ? shootingPack(video) : kind === 'script' ? ['Draft spoken script: ' + video.draft.title,'This is a rehearsal draft, not a recorded transcript.','Revision ' + video.revision + ' | Stage: ' + video.draft.stage,'',...(video.draft.beats || []).flatMap((b,i) => ['Beat ' + (i+1) + ': ' + b.label + ' (' + b.seconds + ' planned seconds)',b.spoken,'']),'Source references:',...(video.draft.sources || []).flatMap(s => [s.title,sourceURL(s.url) || '',s.note || '','']),'Readiness: ' + CHECKS.map(([key]) => key + '=' + ((video.draft.checklist || []).some(c => c.id === key && c.done) ? 'checked' : 'unchecked')).join('; '),'','This download stays on your device.'].join('\n') : ['Recorded transcript: ' + video.draft.title,'Revision ' + video.revision + ' | Stage: ' + video.draft.stage,'',video.draft.transcript,'','Source references:',...(video.draft.sources || []).flatMap(s => [s.title,sourceURL(s.url) || '',s.note || '','']),'Readiness: ' + CHECKS.map(([key]) => key + '=' + ((video.draft.checklist || []).some(c => c.id === key && c.done) ? 'checked' : 'unchecked')).join('; '),'','This download stays on your device.'].join('\n');
      const url = URL.createObjectURL(new Blob([content],{type:'text/plain;charset=utf-8'})); objectURLs.add(url); const a = el('a'); a.href = url; a.download = 'video-' + id + (kind === 'pack' ? '-shooting-pack.md' : kind === 'script' ? '-draft-script.txt' : '-recorded-transcript.txt'); a.click(); setTimeout(() => { URL.revokeObjectURL(url); objectURLs.delete(url); },1000); say((kind === 'pack' ? 'Shooting pack' : kind === 'script' ? 'Draft spoken script' : 'Recorded transcript') + ' downloaded. The download stays on your device.');
    } catch(error) { handleConflict(error); throw error; } finally { working(false); }
  }
  function updateClock() { const remaining = Math.max(0,expires - Math.floor(Date.now()/1000)); if (!remaining) { clearPrivate('Your owner session expired. Private content and unsaved edits were cleared. Sign in again.'); return; } $('vs-session').textContent = remaining <= 120 ? 'Session expires in ' + remaining + ' seconds. Save now.' : 'Private session · ' + Math.ceil(remaining/60) + ' minutes remaining'; }
  async function authenticate() {
    const generation = epoch; if (authGeneration === generation) return; authGeneration = generation; $('vs-app').hidden = true;
    try {
      const session = await api('/api/auth/session'); if (!session.owner || !session.csrf || !Number.isFinite(session.expires)) throw Error('Owner authorization is required.'); if (csrf && csrf !== session.csrf) { clearPrivate('Your owner session changed. Previous private work was cleared.'); return authenticate(); } csrf = session.csrf; expires = session.expires;
      if (expires * 1000 <= Date.now()) { clearPrivate('Your owner session expired. Sign in again.'); return; }
      if (!catalog) { const response = await api(API + '/catalog'); catalog = response.catalog; if (!catalog || !Array.isArray(catalog.templates) || !Array.isArray(catalog.topics)) throw Error('The research catalog is unavailable.'); renderCatalog(); }
      await loadList(); if (generation !== epoch || document.hidden) return;
      $('vs-app').hidden = false; $('vs-signin').hidden = true; $('vs-signout').hidden = false; showView(view); if (sessionClock) clearInterval(sessionClock); sessionClock = setInterval(updateClock,1000); updateClock(); working(false); say('Owner access verified. Research, prepare and rehearse in your private studio.');
    } catch(error) { if (generation === epoch) { clearPrivate(); message(error); } }
    finally { if (authGeneration === generation) authGeneration = null; }
  }
  $('vs-research-nav').onclick = () => showView('research'); $('vs-library-nav').onclick = () => showView('library'); $('vs-empty-research').onclick = () => showView('research');
  $('vs-new').onclick = () => openCreate(); $('vs-create-close').onclick = () => closeDialog('vs-create-dialog');
  $('vs-create-form').addEventListener('submit',async event => {
    event.preventDefault(); const form = event.currentTarget; if (busy || !form.reportValidity()) return; const payload = {request_id:createRequestId || (createRequestId = crypto.randomUUID()),title:form.elements.title.value}; if (form.elements.template_id.value) payload.template_id = form.elements.template_id.value;
    const submit = form.querySelector('button[type=submit]'); submit.disabled = true; working(true); $('vs-create-error').textContent = '';
    try { const response = await api(API,'POST',payload); createRequestId = ''; closeDialog('vs-create-dialog'); tab = 'brief'; setRecord(response.video); showView('library'); await refreshAfterWrite('Private episode created. Review the evidence and prepare each beat before recording.'); }
    catch(error) { if (error.name !== 'AbortError') $('vs-create-error').textContent = error.message; message(error); }
    finally { submit.disabled = false; working(false); }
  });
  $('vs-save').onclick = () => save().catch(message); $('vs-search').oninput = renderList;
  $('vs-reload').onclick = () => { if (record) openVideo(record.id).catch(message); };
  $('vs-load-more').onclick = async () => { if (busy || !nextCursor) return; working(true); try { await loadList(true); } catch(error) { message(error); } finally { working(false); } };
  $('vs-export-pack').onclick = () => download('pack').catch(message); $('vs-export-script').onclick = () => download('script').catch(message); $('vs-export-transcript').onclick = () => download('transcript').catch(message);
  $('vs-rehearse').onclick = () => { if (!draft?.beats.length || busy) return; rehearsalIndex = 0; elapsed = 0; timerText(); renderRehearsal(); $('vs-rehearsal-dialog').showModal(); };
  $('vs-rehearsal-close').onclick = closeRehearsal; $('vs-rehearsal-dialog').addEventListener('cancel',closeRehearsal);
  $('vs-rehearsal-next').onclick = () => { if (rehearsalIndex < draft.beats.length-1) { rehearsalIndex++; renderRehearsal(); } }; $('vs-rehearsal-prev').onclick = () => { if (rehearsalIndex > 0) { rehearsalIndex--; renderRehearsal(); } };
  $('vs-timer-toggle').onclick = () => { if (timer) stopTimer(); else { timerStarted = Date.now(); timer = setInterval(timerText,250); $('vs-timer-toggle').textContent = 'Pause timer'; } timerText(); }; $('vs-timer-reset').onclick = () => { stopTimer(); elapsed = 0; timerText(); };
  $('vs-signout').onclick = async () => {
    if (!canLeave()) return; const token = csrf; clearPrivate('Signing out. Private content cleared.');
    try { const response = await api('/api/auth/logout','POST',{},token); say('Signed out.'); if (response.logout) location.assign(response.logout); }
    catch(error) { say('Private content cleared. Server sign-out could not be confirmed. Close this tab or retry signing out from the control room.',true); }
  };
  addEventListener('beforeunload',event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  addEventListener('pagehide',() => clearPrivate()); addEventListener('pageshow',event => { if (event.persisted) authenticate(); });
  document.addEventListener('visibilitychange',() => {
    if (document.hidden) { resumeOnVisible = true; invalidateRequests(); $('vs-app').hidden = true; closeDialog('vs-create-dialog'); closeRehearsal(); working(false); say('Private studio hidden. Owner access will be checked when you return.'); }
    else if (resumeOnVisible) { resumeOnVisible = false; authenticate(); }
  });
  authenticate();
})();
