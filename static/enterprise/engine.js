/* A deterministic teaching engine. It has no network or business-system access. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EnterpriseStudio = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const choices = {
    example: ['documents', 'assistant'], pattern: ['fixed', 'adaptive', 'specialists'],
    authority: ['read', 'review', 'bounded'], risk: ['routine', 'consequential'],
    condition: ['normal', 'access', 'evidence', 'injection', 'revoked', 'changed', 'timeout', 'budget'],
    platform: ['azure', 'claude-azure', 'claude-external']
  };
  const defaults = {example: 'documents', pattern: 'fixed', authority: 'review', risk: 'routine', condition: 'normal', platform: 'azure', budget: 6};
  function normalize(raw = {}) {
    const result = {};
    Object.keys(choices).forEach(key => { result[key] = choices[key].includes(raw[key]) ? raw[key] : defaults[key]; });
    const budget = Number(raw.budget);
    result.budget = Number.isInteger(budget) && budget >= 1 && budget <= 8 ? budget : defaults.budget;
    return result;
  }
  function design(raw, example) {
    const c = normalize(raw);
    const authority = c.risk === 'consequential' && c.authority === 'bounded' ? 'review' : c.authority;
    let title = example.pattern, why = example.why;
    if (c.pattern === 'adaptive') {
      title = 'Bounded tool agent';
      why = 'A model may choose the next permitted tool after inspecting results. First prove an advantage over the fixed workflow; keep authorization, validation, budgets and stopping conditions in application code.';
    } else if (c.pattern === 'specialists') {
      title = 'Coordinator + isolated specialists';
      why = 'Use this only when separate expertise, context or parallel work improves evaluated outcomes. Give each specialist a narrow work order and identity. A coordinator combines evidence; it cannot expand permission. Compare against one agent first.';
    }
    const authorityText = {read: '✓ Read and draft only', review: '⏸ Write after explicit review', bounded: '✓ Allowlisted routine writes'}[authority];
    let authorityWhy = {
      read: 'No business-write tool is enabled. The system can return a draft or grounded answer.',
      review: 'The application validates the proposal and waits for an authorized reviewer. Approval is scoped to exact arguments, current policy and an expiry.',
      bounded: example.bounded
    }[authority];
    if (c.risk === 'consequential' && c.authority === 'bounded') authorityWhy = 'This teaching design narrows the requested authority to reviewed writes because a wrong action has material consequences. Reviewers still cannot authorize a forbidden action.';
    return {title, why, authority, authorityText, authorityWhy};
  }
  function buildRun(raw, example, decision = 'pending') {
    const c = normalize(raw), d = design(c, example), steps = [];
    let used = 0;
    function add(node, title, body, enforcer, event, state = 'checked', terminal = false) {
      steps.push({node, title, body, enforcer, event, state, terminal, used});
    }
    function call() {
      if (used >= c.budget) {
        add('budget', 'Stop at the call budget', 'The application refuses the next tool call and hands off the unfinished task. No pending write is executed.', 'Runtime budget check', 'budget.stopped', 'held', true);
        return false;
      }
      used += 1;
      return true;
    }
    add('identity', 'Verify identity and scope', 'Validate the caller and bind the current tenant, user, task and service scope. Claims in a prompt cannot change this identity.', 'Application identity boundary', 'identity.verified');
    if (c.condition === 'access') {
      add('gate', 'Source access denied', 'The caller is not permitted to retrieve the source. The run ends before restricted content enters model context; the public answer does not reveal the document title.', 'Retrieval authorization', 'retrieval.denied', 'denied', true);
      return steps;
    }
    if (!call()) return steps;
    add('evidence', example.evidenceTitle, example.evidenceDetail, 'Retrieval and deterministic validation', 'evidence.checked');
    if (c.condition === 'evidence') {
      add('evidence', 'Evidence cannot support completion', example.failure, 'Required-evidence rule', 'evidence.insufficient', 'held', true);
      return steps;
    }
    if (c.condition === 'budget') {
      add('budget', 'Stop before the next call', 'This selected fault simulates an exhausted total run budget. The runtime blocks further work and records the incomplete outcome. It is separate from the tool-call counter.', 'Runtime total-budget check', 'budget.stopped', 'held', true);
      return steps;
    }
    add('model', 'Use the pinned model', 'Supply only approved instructions and permitted evidence. Record model, prompt, retrieval and policy versions. Output is a candidate to validate, not authorization.', 'Application context builder', 'model.output_received');
    if (c.condition === 'injection') {
      add('gate', 'Unauthorized action blocked', 'The selected synthetic document induces a proposal to export private data. That operation is outside the tool allowlist and is denied. This shows a known enforcement boundary, not a claim that all prompt injection is detected.', 'Tool allowlist and argument policy', 'tool.denied', 'denied', true);
      return steps;
    }
    if (c.pattern === 'adaptive') {
      add('model', 'Choose a permitted follow-up', 'In this illustrative branch the model requests one more reference check. The application validates the tool and resource before permitting the call; a different proposal could be refused.', 'Tool policy and argument validator', 'agent.follow_up_proposed');
      if (!call()) return steps;
      add('evidence', 'Observe the follow-up result', 'A scoped reference lookup returns additional permitted evidence. The agent can revise its proposal from this result, within the remaining budget. This is an example path, not a live model choice.', 'Authorized read tool', 'agent.observation_received');
    } else if (c.pattern === 'specialists') {
      add('proposal', 'Dispatch narrow work orders', 'Send separate evidence-check and policy-check work orders with minimal context. Each specialist has its own scope and cannot perform the final business write.', 'Coordinator and delegated-scope checks', 'specialists.dispatched');
      if (!call()) return steps;
      add('evidence', 'Receive the evidence check', 'The evidence specialist returns a typed result with source references. The coordinator validates the handoff schema and provenance.', 'Specialist read boundary', 'specialist.evidence_received');
      if (!call()) return steps;
      add('gate', 'Reconcile the policy check', 'The policy specialist returns a separate, scoped result. In this synthetic path the checks agree. Missing or conflicting results would require a hold; no specialist can approve a write.', 'Coordinator result validator', 'specialist.policy_received');
    }
    add('proposal', 'Validate the proposed result', example.proposalDetail, 'Schema, evidence and business rules', 'proposal.validated');
    if (d.authority === 'read') {
      add('receipt', 'Return a checked answer or draft', example.readOutcome, 'Output validation', 'answer.returned', 'complete', true);
      return steps;
    }
    add('gate', 'Check the action contract', 'Confirm the tool, resource, caller, arguments and business preconditions. Only the listed staging or request action can continue. This check does not execute it.', 'Application policy enforcement', 'action.allowed');
    if (d.authority === 'review') {
      if (decision === 'reject') {
        add('review', 'Reviewer rejects the proposal', 'The authorized reviewer declines this exact payload. No business write occurs. The run is closed with the rejection recorded.', 'Human review boundary', 'approval.rejected', 'denied', true);
        return steps;
      }
      if (decision !== 'approve') {
        add('review', 'Wait for the authorized reviewer', example.review, 'Human review boundary', 'approval.pending', 'waiting', true);
        return steps;
      }
      add('review', 'Approval recorded for this payload', 'The simulated reviewer approved the exact arguments, resource and policy version. Approval expires if the payload changes. Execution still needs a fresh authorization check.', 'Human review boundary', 'approval.recorded');
    }
    if (c.condition === 'revoked') {
      add('gate', 'Permission is no longer valid', 'Authorization is re-checked immediately before execution. The current user or service scope no longer permits the write, so even an earlier approval cannot release it.', 'Execution-time authorization', 'authorization.revoked', 'denied', true);
      return steps;
    }
    if (c.condition === 'changed') {
      add('gate', 'The proposal changed', 'The proposed arguments no longer match the validated payload. In reviewed mode the approval is invalid too. Revalidate and obtain any required fresh approval; do not execute this version.', 'Payload version and hash check', 'payload.changed', 'held', true);
      return steps;
    }
    if (!call()) return steps;
    if (c.condition === 'timeout') {
      add('execute', 'Write result is unknown', 'The call was sent but the receipt timed out. The write may have committed. Stop blind retries and reconcile the original idempotency key with the business system. This lesson makes no success claim.', 'Execution service and reconciliation queue', 'write.unknown', 'unknown', true);
      return steps;
    }
    add('execute', 'Execute the permitted operation', 'Re-check current authorization, consume the exact approved or allowlisted payload and use an idempotency key. The synthetic business service returns a receipt.', 'Protected business API', 'write.receipt_received');
    add('receipt', 'Verify the business result', example.writeOutcome, 'Receipt reconciliation', 'outcome.verified', 'complete', true);
    return steps;
  }
  function record(raw, example, owner, outcome) {
    const c = normalize(raw), d = design(c, example);
    return [
      'SHAMS ENTERPRISE DESIGN RECORD', 'Teaching proposal · not a production approval', '',
      'Example: ' + example.label, 'Pattern: ' + d.title,
      'Requested authority: ' + c.authority, 'Effective authority: ' + d.authorityText,
      'Consequence class: ' + c.risk, 'Model deployment option: ' + c.platform,
      'Tool-call limit (illustrative): ' + c.budget, '',
      'SCOPE · Gate 01', 'Accountable owner: ' + (String(owner || '').trim() || 'UNASSIGNED; required before release'),
      'Pilot outcome: ' + (String(outcome || '').trim() || example.goal), 'Baseline: ' + example.baseline,
      'Pattern rationale: ' + d.why, '', 'HARDEN · Gates 02, 03, 05', example.boundary,
      'Effective authority: ' + d.authorityWhy, 'Example tool: ' + example.proposal,
      'Review contract: ' + example.review, '', 'ANCHOR · Gate 04', example.ingestion, example.grounding,
      'Synthetic evidence: ' + example.sources, '', 'MEASURE · Gates 06, 07', example.quality,
      ...example.acceptance.map(item => '* ' + item[0] + ': ' + item[1]),
      'Agree on outcome quality, forbidden-operation tests, p95 latency, reviewer workload and total cost per accepted outcome.',
      '', 'SUSTAIN · Gate 08', example.operation, example.improvement,
      'Pin model, prompt, tools, policy and retrieval configuration. Release through offline evaluation, shadow, pilot and monitored rollout.',
      'Trace observed events with redaction, access control and retention. Test stop, reconciliation and rollback.',
      '', 'UNRESOLVED BEFORE PRODUCTION',
      '* Name the accountable and on-call owners; record reviewer duties.',
      '* Approve data classification, source rights, residency, retention and deletion rules.',
      '* Verify the selected service/model/region/hosting features, lifecycle and terms.',
      '* Define quality thresholds, risk tolerance, call/time/cost limits and review escalation times from real evidence.',
      '* Attach held-out evaluation results, failure drills, security review and signed release decision.',
      '* Define pilot exit date, rollback triggers and reconciliation for already completed actions.',
      '', 'No cloud system was deployed, model trained or production result measured by this studio.'
    ].join('\n');
  }
  return {normalize, design, buildRun, record};
});
