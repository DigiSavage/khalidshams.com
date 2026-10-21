/* Deterministic planning example. No network, model, storage or business writes. */

export const AUDIENCES = Object.freeze(['executive', 'engineering', 'risk', 'operations']);
export const CHANGES = Object.freeze(['baseline', 'autonomy', 'unowned', 'deadline']);

const DEFAULT_STATE = Object.freeze({audience: 'executive', change: 'baseline'});
const RATE = 150;
const CONTINGENCY = 0.15;

function enumValue(value, allowed, fallback) {
  return typeof value === 'string' && allowed.includes(value) ? value : fallback;
}

function normalizeState(state) {
  const input = state && typeof state === 'object' ? state : {};
  return {
    audience: enumValue(input.audience, AUDIENCES, DEFAULT_STATE.audience),
    change: enumValue(input.change, CHANGES, DEFAULT_STATE.change)
  };
}

/** Read only allowlisted choices. Ambiguous duplicate parameters fail closed. */
export function parseState(search = '') {
  const params = search instanceof URLSearchParams
    ? search
    : new URLSearchParams(typeof search === 'string' ? search : '');
  const single = key => params.getAll(key).length === 1 ? params.get(key) : undefined;
  return normalizeState({audience: single('audience'), change: single('change')});
}

/** A canonical query string with no leading question mark or untrusted values. */
export function serializeState(state = DEFAULT_STATE) {
  const safe = normalizeState(state);
  return new URLSearchParams({audience: safe.audience, change: safe.change}).toString();
}

const BASE_ROWS = [
  {role: 'Architecture', low: 24, high: 36},
  {role: 'Data', low: 40, high: 64},
  {role: 'Application', low: 48, high: 80},
  {role: 'Quality', low: 32, high: 48},
  {role: 'Release', low: 16, high: 24}
];

const COMMON_ASSUMPTIONS = [
  'This worked example uses illustrative planning assumptions. It is not a delivered result, binding quote, funding commitment or release approval.',
  'USD 150 per delivery hour and a 15% contingency are example inputs, not vendor prices. Cloud usage, software licences, tax and ongoing support are excluded and must be estimated separately.',
  'Hours describe effort across roles, not elapsed duration. Calendar dates depend on named people, their availability, approved access and the review queue.',
  'A named human must approve the exact draft against its source evidence. The pilot ends at that draft. It has no sending or dispatch capability. Authorized people use the existing business workflow.'
];

const PLANS = {
  baseline: {
    id: 'baseline',
    label: 'Draft before dispatch',
    status: 'Pilot proposal',
    summary: 'Prepare a quote from authorized source records, show the evidence and put the exact draft before a named approver.',
    decision: 'D-01 proposes a bounded drafting pilot. It does not authorize release. A named human approves the exact draft. The pilot has no sending or dispatch capability; authorized people use the existing business workflow.',
    scope: 'One team and one quote workflow. Read authorized customer, rate and availability records; produce an evidence-linked draft. No sending, ERP write, booking or dispatch.',
    test: 'Check source permissions, quote arithmetic, evidence references, stale prices and missing fields. Confirm reviewer rejection, changed payloads and revoked access prevent approval of the draft. Compare draft quality and review effort with the current process.',
    operation: 'Keep the current manual process available. Record draft versions and reviewer decisions with restricted access and retention. Stop drafting on missing evidence or permission changes. Revalidate the source records before preparing a new draft; the pilot has no business-write route.',
    owner: 'Name the accountable sales owner, authorized quote approver, source owners and operations owner before a pilot. The application cannot assign itself approval authority.',
    rows: BASE_ROWS,
    assumptions: [
      'Source owners can provide permitted sample records, price rules and a baseline of the existing quote workflow.',
      'The example includes discovery, integration, evaluation and release preparation. Release still requires evidence and a separate owner decision.'
    ]
  },
  autonomy: {
    id: 'autonomy',
    label: 'Request automatic sending',
    status: 'Re-scope required',
    summary: 'Automatic sending changes the authority boundary. Record the request, price the assurance work and keep autonomous actions excluded.',
    decision: 'The requested D-01 revision does not approve automatic writes, sending or dispatch. Keep human approval in force. Review new controls and obtain a separate owner approval before any expanded authority can be considered.',
    scope: 'Retain the draft-only pilot and add assurance and change verification. Autonomous sending, ERP writes and dispatch stay excluded until new controls, evidence and owner approval establish a separate scope.',
    test: 'Test exact-payload approval, rejection, expiry and revocation at execution time. Exercise changed arguments, idempotent writes, duplicate delivery and timeout reconciliation in a sandbox. Passing a test is not permission to turn on writes.',
    operation: 'Stop on uncertain execution, revoked permission or changed payload. Reconcile external effects against the original operation identifier before retrying. A rollback does not undo an already sent quote or dispatched job.',
    owner: 'The business risk owner and authorized operations approver must own the proposed authority change. Name security, source and incident owners; an engineer or model cannot promote its own permissions.',
    rows: [...BASE_ROWS, {role: 'Assurance and change verification', low: 48, high: 80}],
    assumptions: [
      'The additional 48 to 80 hours allow for an illustrative assurance work package in this estimate, not permission or a promise to deliver autonomy.',
      'The human approval boundary stays in place while feasibility, controls and acceptance evidence are reviewed. Expanded authority has no committed release date.'
    ]
  },
  unowned: {
    id: 'unowned',
    label: 'Source has no owner',
    status: 'Hold',
    summary: 'A required rate source has no accountable owner or verified access rights. Hold delivery planning and investigate the dependency.',
    decision: 'D-01 is held. No source access, release or automatic action is approved. Identify a source owner and establish access rights, quality and permitted use before estimating delivery again.',
    scope: 'Investigation only: identify the rate source owner, locate an approved substitute if needed and verify access and data quality. No ingestion of the unowned source, quote generation, sending, ERP write or dispatch.',
    test: 'Prove source ownership and permitted access, inspect approved samples and test refusal when rights or required evidence are absent. Do not manufacture sample success to unblock a release gate.',
    operation: 'Keep the manual quote process. Escalate the blocked dependency to the accountable business owner, record what is unknown and stop retrieval from the unowned source.',
    owner: 'A source owner and access approver are missing. The accountable business owner must resolve that gap; the delivery team cannot self-authorize access.',
    rows: [{role: 'Discovery investigation only', low: 24, high: 36}],
    estimateUnknown: true,
    assumptions: [
      'The Discovery row is a provisional 24 to 36 hour investigation allowance only. It is not a delivery estimate and is not authorization to begin work.',
      'Delivery hours and costs remain unknown until source ownership, access and feasibility are established. Null totals mean unknown, never zero or free.'
    ]
  },
  deadline: {
    id: 'deadline',
    label: 'Ask for two weeks',
    status: 'Reduce scope',
    summary: 'Offer a smaller, read-only prototype and expose the people and access dependencies instead of converting effort into a promised date.',
    decision: 'The proposed D-01 revision narrows the prototype for review. It is not a two-week delivery promise or release approval. Retain human approval for any real quote; no automatic sending, writes or dispatch are approved.',
    scope: 'One team, one approved source and a read-only quote prototype. Use permitted sample records and show draft evidence. No ERP write, production integration, sending or dispatch.',
    test: 'Verify one-source access, arithmetic, evidence references and missing-data refusals on agreed samples. Run a user walkthrough with the named reviewer and record prototype limitations; do not claim production acceptance.',
    operation: 'Keep the existing operational process. The prototype has no business-write route. Record feedback and unresolved dependencies, then decide whether to extend, re-estimate or stop.',
    owner: 'Name a prototype sponsor, source approver, reviewer and delivery lead. The delivery lead confirms actual availability and dependency dates before offering a calendar commitment.',
    rows: [
      {role: 'Architecture', low: 16, high: 24},
      {role: 'Data', low: 24, high: 36},
      {role: 'Application', low: 24, high: 36},
      {role: 'Quality', low: 24, high: 36},
      {role: 'Release', low: 8, high: 12}
    ],
    assumptions: [
      'The 96 to 144 hours are combined effort across roles. They do not establish a two-week schedule; access, reviewer availability and team capacity must be confirmed.',
      'Release effort here means packaging, walkthrough and handoff of the prototype. Production rollout is outside this scope.'
    ]
  }
};

/** Audience changes presentation elsewhere, never the underlying decision or price. */
export function analyze(change = DEFAULT_STATE.change) {
  const key = enumValue(change, CHANGES, DEFAULT_STATE.change);
  const {estimateUnknown, assumptions, rows, ...plan} = PLANS[key];
  const lowHours = estimateUnknown ? null : rows.reduce((sum, row) => sum + row.low, 0);
  const highHours = estimateUnknown ? null : rows.reduce((sum, row) => sum + row.high, 0);
  // Integer percentage arithmetic avoids binary rounding adding an extra dollar.
  const cost = hours => hours === null ? null : Math.ceil(hours * RATE * 115 / 100);
  return {
    ...plan,
    rows: rows.map(row => ({...row})),
    lowHours,
    highHours,
    rate: RATE,
    contingency: CONTINGENCY,
    lowCost: cost(lowHours),
    highCost: cost(highHours),
    assumptions: [...COMMON_ASSUMPTIONS, ...assumptions]
  };
}
