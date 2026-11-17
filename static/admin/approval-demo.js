/* Deterministic teaching model. No network, storage, clock, payment or identity adapter. */
(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.KSApprovalDemo = factory();
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const copy = value => JSON.parse(JSON.stringify(value));
  function create() {
    let state;
    function reset() {
      state = {version: 0, proposal: null, approval: null, receipt: null, writes: [], events: ['Rehearsal reset. No proposal or approval.']};
    }
    reset();
    function snapshot() { return copy(state); }
    function dispatch(action) {
      if (action === 'reset') { reset(); return snapshot(); }
      if (action === 'draft') {
        state.version++;
        state.proposal = {operation: 'refund', recipient: 'SYNTHETIC-ACCOUNT', currency: 'USD', amount_cents: 50000};
        state.receipt = null;
        state.events.push('Drafted $500 refund at version ' + state.version + '.');
      } else if (action === 'approve') {
        if (!state.proposal) throw Error('Draft a refund before approving it.');
        state.approval = {version: state.version, payload: copy(state.proposal), consumed: false};
        state.receipt = null;
        state.events.push('Approved exact proposal at version ' + state.version + '.');
      } else if (action === 'change') {
        if (!state.proposal) throw Error('Draft a refund before changing it.');
        state.version++;
        state.proposal = {...state.proposal, amount_cents: 500000};
        state.receipt = null;
        state.events.push('Changed amount to $5,000 at version ' + state.version + '. Prior approval is unchanged.');
      } else if (action === 'attempt') {
        const a = state.approval;
        const reason = !state.proposal ? 'NO_PROPOSAL' : !a ? 'NO_APPROVAL' : a.consumed ? 'APPROVAL_USED' :
          a.version !== state.version || JSON.stringify(a.payload) !== JSON.stringify(state.proposal) ? 'PAYLOAD_CHANGED' : 'EXACT_APPROVAL';
        const allowed = reason === 'EXACT_APPROVAL';
        if (allowed) {
          a.consumed = true;
          state.writes.push({version: state.version, payload: copy(state.proposal)});
        }
        state.receipt = {mode: 'TEACHING_SIMULATION', status: allowed ? 'SIMULATED_ONLY' : 'REFUSED', reason,
          current_version: state.version, approved_version: a ? a.version : null,
          current_payload: copy(state.proposal), approved_payload: a ? copy(a.payload) : null,
          simulated_writes: state.writes.length, external_calls: 0, money_moved: false};
        state.events.push((allowed ? 'Simulated write only. ' : 'Refused. ') + reason + '.');
      } else throw Error('Unknown rehearsal action.');
      return snapshot();
    }
    return Object.freeze({snapshot, dispatch});
  }
  return Object.freeze({create});
});
