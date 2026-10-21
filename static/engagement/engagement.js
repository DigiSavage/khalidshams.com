import {parseState, serializeState, analyze} from './engine.js';

const data = JSON.parse(document.getElementById('eg-data').textContent);
const $ = id => document.getElementById(`eg-${id}`);
let state = parseState(location.search);
const money = n => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', maximumFractionDigits:0}).format(n);
const set = (id, text) => { $(id).textContent = text; };

function render(updateURL = true) {
  const audience = data.audiences[state.audience];
  const result = analyze(state.change);
  $('audience').value = state.audience;
  $('change').value = state.change;
  set('audience-label', audience.label);
  for (const key of ['opening', 'question', 'show']) set(key, audience[key]);
  set('audience-decision', audience.decision);
  set('change-status', result.status);
  for (const key of ['summary', 'decision', 'scope', 'test', 'operation', 'owner']) set(key, result[key]);
  set('hours', result.lowHours === null ? 'Delivery effort: not yet estimable' : `${result.lowHours} to ${result.highHours} person-hours`);
  set('cost', result.lowCost === null ? 'Delivery price: not established' : `${money(result.lowCost)} to ${money(result.highCost)} USD`);
  set('estimate-note', result.lowHours === null ? 'The row below covers discovery only. An unknown build estimate is not zero.' : 'Labor range including contingency. Person-hours are not elapsed time or a delivery-date commitment.');
  $('rows').replaceChildren(...result.rows.map(row => {
    const tr = document.createElement('tr');
    for (const [i, value] of [row.role, row.low, row.high].entries()) {
      const cell = document.createElement(i ? 'td' : 'th');
      if (!i) cell.scope = 'row';
      cell.textContent = value; tr.append(cell);
    }
    return tr;
  }));
  $('assumptions').replaceChildren(...result.assumptions.map(text => {
    const li = document.createElement('li'); li.textContent = text; return li;
  }));
  set('export-status', '');
  if (updateURL) history.replaceState(null, '', `${location.pathname}?${serializeState(state)}${location.hash}`);
}

function brief() {
  const a = data.audiences[state.audience], r = analyze(state.change);
  const lines = ['FROM DISCOVERY TO DELIVERY', 'Khalid Shams | The SHAMS Method',
    'Worked design. Illustrative organization, scope and planning inputs. No client results claimed.',
    `Reference: https://khalidshams.com/method/engagement/?${serializeState(state)}`,
    '', data.scenario.title, data.scenario.description,
    '', `AUDIENCE: ${a.label}`, a.opening, `Ask: ${a.question}`, `Show: ${a.show}`,
    `Decision to seek, subject to the change assessment: ${a.decision}`,
    '', `D-01 CHANGE ASSESSMENT: ${r.status}`, r.summary, `Decision: ${r.decision}`,
    `Scope: ${r.scope}`, `Acceptance: ${r.test}`, `Operation: ${r.operation}`, `Owner: ${r.owner}`,
    '', 'ILLUSTRATIVE ESTIMATE',
    r.lowHours === null ? 'Delivery hours and price are not established. Discovery only is listed below.' :
      `${r.lowHours} to ${r.highHours} person-hours; ${money(r.lowCost)} to ${money(r.highCost)} USD including contingency.`,
    '$150 USD/hour sample labor rate; 15% contingency. Excludes software, cloud usage, licenses, tax and customer effort.',
    'Not a binding quote or the $950 Architecture Decision Review. Person-hours do not establish a delivery date.',
    ...r.rows.map(x => `${x.role}: ${x.low} to ${x.high} hours`), ...r.assumptions,
    '', 'Observed business results: not measured.',
    '', 'BASELINE WORKFLOW REFERENCE',
    'The artifacts below describe the bounded D-01 pilot. The change assessment above identifies work that must be revised before approval.'];
  for (const stage of data.stages) lines.push('', stage.title.toUpperCase(), stage.lead,
    ...stage.actions.map(x => `- ${x}`), `Artifact: ${stage.artifact.title}`,
    ...stage.artifact.lines.map(x => `- ${x}`), `Owner: ${stage.owner}`, `Exit: ${stage.exit}`, `Hold: ${stage.hold}`);
  return lines.join('\n');
}

$('audience').addEventListener('change', event => { state = parseState(`audience=${event.target.value}&change=${state.change}`); render(); });
$('change').addEventListener('change', event => { state = parseState(`audience=${state.audience}&change=${event.target.value}`); render(); });
$('reset').addEventListener('click', () => { state = parseState(''); render(); });
window.addEventListener('popstate', () => { state = parseState(location.search); render(false); });
$('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(brief()); set('export-status', 'Worked brief copied.'); }
  catch { set('export-status', 'Clipboard unavailable. Use Download the brief instead.'); }
});
$('download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([brief()], {type:'text/plain;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url;
  link.download = `shams-engagement-${state.change}.txt`; document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000); set('export-status', 'Worked brief downloaded.');
});
let closedForPrint = [];
window.addEventListener('beforeprint', () => {
  closedForPrint = [...document.querySelectorAll('.eg details:not([open])')];
  closedForPrint.forEach(detail => { detail.open = true; });
});
window.addEventListener('afterprint', () => { closedForPrint.forEach(detail => { detail.open = false; }); });
$('print').addEventListener('click', () => window.print());
// Internal references remain usable after a reader collapses a source panel.
function revealHash() {
  let id;
  try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
  const target = document.getElementById(id);
  if (!target?.closest('.eg')) return;
  let opened = false;
  for (let parent = target.parentElement; parent; parent = parent.parentElement) {
    if (parent.matches('details') && !parent.open) { parent.open = true; opened = true; }
  }
  if (opened) target.scrollIntoView({block: 'start'});
}
window.addEventListener('hashchange', revealHash);
document.querySelector('.eg').addEventListener('click', event => {
  const link = event.target.closest('a[href^="#"]');
  if (link?.getAttribute('href') === location.hash) revealHash();
});
render(false);
$('interactive').hidden = false;
revealHash();
