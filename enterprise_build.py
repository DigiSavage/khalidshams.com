"""Enterprise design teaching studio. All runtime events are synthetic and local."""
import json
from html import escape as esc
from pathlib import Path

from art_assets import illustration

ROOT = Path(__file__).parent
ROUTE = "/architect/agent-studio/"
EXAMPLE_FIELDS = {
    "id", "label", "title", "goal", "owner", "baseline", "pattern", "why", "boundary",
    "sources", "ingestion", "grounding", "quality", "proposal", "tool", "target",
    "readOutcome", "writeOutcome", "evidenceTitle", "evidenceDetail", "proposalDetail",
    "review", "bounded", "failure", "operation", "improvement",
}


def load():
    data = json.loads((ROOT / "content/enterprise/studio.json").read_text(encoding="utf-8"))
    validate(data)
    return data


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("examples"), list):
        raise ValueError("enterprise: examples must be a list")
    if {x.get("id") for x in data["examples"]} != {"documents", "assistant"} or len(data["examples"]) != 2:
        raise ValueError("enterprise: exactly one documents and one assistant example required")
    for example in data["examples"]:
        for field in EXAMPLE_FIELDS:
            if not isinstance(example.get(field), str) or not example[field].strip():
                raise ValueError(f"enterprise {example.get('id')}: missing text field {field}")
        cases = example.get("acceptance")
        if not isinstance(cases, list) or len(cases) < 4 or any(
            not isinstance(c, list) or len(c) != 2 or any(not isinstance(s, str) or not s.strip() for s in c)
            for c in cases
        ):
            raise ValueError("enterprise: acceptance cases require condition and observable outcome")
    sources = data.get("sources", [])
    required = {"patterns", "evals", "extraction", "access", "claude", "privacy", "traces"}
    if {s.get("id") for s in sources} != required or len(sources) != len(required):
        raise ValueError("enterprise: source ids must match the page citations")
    for source in sources:
        if any(not isinstance(source.get(k), str) or not source[k] for k in ("title", "url", "claim", "checked")):
            raise ValueError("enterprise: incomplete source")
        if not source["url"].startswith(("https://learn.microsoft.com/", "https://www.anthropic.com/")):
            raise ValueError("enterprise: expected primary documentation source")


def acceptance(example):
    rows = ''.join(f'<tr><th scope="row">{esc(condition)}</th><td>{esc(outcome)}</td></tr>'
                   for condition, outcome in example["acceptance"])
    return ('<div class="es-table-scroll" role="region" aria-label="Acceptance cases" tabindex="0">'
            '<table><thead><tr><th>Test condition</th><th>Required observable outcome</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def scene():
    """One exact code-native drawing. Object nodes map to deterministic engine focus ids."""
    return '''<svg class="es-scene" viewBox="0 0 1000 620" role="img" aria-labelledby="es-scene-title es-scene-desc">
      <title id="es-scene-title">Enterprise workflow with evidence, a model, review and an execution boundary</title>
      <desc id="es-scene-desc">Identity scopes evidence before it reaches the work tray. A model proposes an answer or tool call. The application checks permission and, when required, routes it to a human reviewer. Only the protected execution service reaches the business system. Every reached step adds a receipt to the event trail.</desc>
      <defs><marker id="es-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="#1F45C8" stroke-width="1.5"/></marker><marker id="es-dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5"><circle cx="5" cy="5" r="3" fill="#0E1012"/></marker></defs>
      <rect class="es-boundary" x="20" y="38" width="718" height="492" rx="16" fill="#F7F7F5" stroke="#6B737A" stroke-dasharray="7 6"/>
      <text class="es-svg-mono" x="40" y="24" fill="#6B737A">APPLICATION · TENANT + TASK SCOPE</text>
      <path class="es-data-line" d="M176 197V262M212 323H300M508 324H560M665 394V443H815" fill="none" stroke="#0E1012" stroke-width="2" marker-end="url(#es-dot)"/>
      <path class="es-control-line" d="M444 198V250M668 325H778V367M630 266V226H817V202" fill="none" stroke="#1F45C8" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#es-arrow)"/>
      <path class="es-review-line" d="M807 202V239H691V280" fill="none" stroke="#1F45C8" stroke-width="2" stroke-dasharray="2 5"/>
      <g data-node="identity"><rect class="es-surface" x="64" y="72" width="222" height="129" rx="6" fill="#FFFFFF" stroke="#0E1012"/>
      <rect class="es-inset" x="82" y="88" width="47" height="61" rx="3" fill="#EFEFEC" stroke="#6B737A"/><circle cx="105" cy="106" r="8" fill="#0E1012"/><path d="M91 139V132Q105 112 119 132V139Z" fill="#0E1012"/>
      <text class="es-svg-head" x="143" y="109" fill="#0E1012">Identity</text><text class="es-svg-small" x="143" y="133" fill="#3E4449">User + service</text><text class="es-svg-mono" x="83" y="176" fill="#1F45C8">✓ VERIFY SCOPE</text></g>
      <g data-node="evidence"><rect class="es-surface" x="65" y="265" width="150" height="211" rx="5" fill="#FFFFFF" stroke="#0E1012"/>
      <path class="es-furniture" d="M77 280H203V362H77ZM77 374H203V463H77" fill="#EFEFEC" stroke="#6B737A"/>
      <path d="M87 291H110V351H87ZM117 288H137V351H117ZM145 285L165 283L174 347L155 350ZM181 293H195V351H181Z" fill="#FFFFFF" stroke="#0E1012"/>
      <path d="M146 294L165 292M149 303L166 301M151 312L167 310" fill="none" stroke="#1F45C8" stroke-width="2"/>
      <rect x="96" y="394" width="88" height="12" rx="3" fill="#FFFFFF" stroke="#0E1012"/><path d="M89 424H190M89 444H190" fill="none" stroke="#6B737A"/>
      <text class="es-svg-head" x="68" y="247" fill="#0E1012">Evidence library</text><text class="es-svg-small" x="68" y="498" fill="#3E4449">Owned · versioned · filtered</text></g>
      <g data-node="model"><rect class="es-surface" x="350" y="82" width="185" height="115" rx="8" fill="#FFFFFF" stroke="#0E1012"/>
      <path d="M370 142A36 36 0 0 1 442 142" fill="none" stroke="#0E1012" stroke-width="2"/><path d="M406 141L423 110" fill="none" stroke="#1F45C8" stroke-width="3"/><circle cx="406" cy="141" r="4" fill="#0E1012"/>
      <rect x="461" y="107" width="54" height="12" fill="#E7EBFB" stroke="#1F45C8"/><rect x="461" y="130" width="54" height="12" fill="#EFEFEC" stroke="#6B737A"/>
      <text class="es-svg-head" x="368" y="174" fill="#0E1012">Pinned model</text><text class="es-svg-small" x="357" y="220" fill="#3E4449">Proposes · does not authorize</text></g>
      <g data-node="proposal"><path class="es-surface" d="M295 269H518L531 385H283Z" fill="#FFFFFF" stroke="#0E1012" stroke-width="2"/><path class="es-workbench" d="M273 385H542V405H273Z" fill="#E7EBFB" stroke="#1F45C8" stroke-width="2"/>
      <rect x="311" y="296" width="91" height="63" rx="3" fill="#E7EBFB" stroke="#1F45C8"/><path d="M326 311H385M326 324H378M326 337H370" fill="none" stroke="#1F45C8"/>
      <rect class="es-inset" x="416" y="297" width="87" height="62" rx="3" fill="#EFEFEC" stroke="#6B737A"/>
      <text class="es-svg-small" x="423" y="321" fill="#3E4449">Sources</text><text class="es-svg-small" x="423" y="345" fill="#3E4449">+ checks</text><text class="es-svg-head" x="297" y="435" fill="#0E1012">Bounded work tray</text><text class="es-svg-small" x="297" y="459" fill="#3E4449">This request's context only</text></g>
      <g data-node="gate"><rect class="es-surface" x="563" y="271" width="133" height="122" rx="6" fill="#FFFFFF" stroke="#0E1012" stroke-width="2"/>
      <path d="M581 372V293H679V372" fill="none" stroke="#1F45C8" stroke-width="5"/><path d="M590 333H669" fill="none" stroke="#1F45C8" stroke-width="4"/>
      <text class="es-svg-head" x="591" y="318" fill="#0E1012">CHECK</text><text class="es-svg-small" x="588" y="358" fill="#3E4449" id="es-gate-label">Permission</text>
      <text class="es-svg-small" x="563" y="419" fill="#3E4449">Arguments + policy</text></g>
      <g data-node="review"><rect class="es-surface" x="777" y="65" width="193" height="137" rx="6" fill="#FFFFFF" stroke="#0E1012"/>
      <circle cx="808" cy="95" r="10" fill="#0E1012"/><path d="M793 145V124Q793 108 808 108Q823 108 823 124V145Z" fill="#0E1012"/>
      <rect x="836" y="87" width="116" height="61" rx="4" fill="#F6EED9" stroke="#B8912F"/><text class="es-svg-mono" x="846" y="113" fill="#86661A">REVIEW</text><text class="es-svg-small" x="846" y="134" fill="#3E4449">Exact payload</text><text class="es-svg-head" x="795" y="181" fill="#0E1012">Human reviewer</text></g>
      <g data-node="execute"><rect class="es-boundary" x="769" y="297" width="204" height="194" rx="10" fill="#F7F7F5" stroke="#6B737A" stroke-dasharray="7 6"/><text class="es-svg-mono" x="784" y="320" fill="#6B737A">BUSINESS SYSTEM</text>
      <rect class="es-surface" x="793" y="348" width="154" height="115" rx="5" fill="#FFFFFF" stroke="#0E1012"/><rect x="807" y="366" width="35" height="47" fill="#EFEFEC" stroke="#6B737A"/><rect x="853" y="366" width="35" height="47" fill="#EFEFEC" stroke="#6B737A"/><rect x="900" y="366" width="31" height="47" fill="#EFEFEC" stroke="#6B737A"/><text class="es-svg-small" x="810" y="443" fill="#3E4449" id="es-target-label">Staging ledger</text></g>
      <g data-node="receipt"><rect class="es-surface" x="65" y="555" width="906" height="48" rx="5" fill="#FFFFFF" stroke="#0E1012"/><text class="es-svg-mono" x="83" y="585" fill="#1F45C8">EVENT TRAIL · VERSIONS · POLICY DECISIONS · RECEIPTS</text></g>
      <g data-node="budget"><rect x="570" y="87" width="124" height="110" rx="6" fill="#F6EED9" stroke="#B8912F"/><path d="M588 142Q630 80 677 142" fill="none" stroke="#86661A" stroke-width="2"/><path d="M632 139L652 112" fill="none" stroke="#86661A" stroke-width="3"/><text class="es-svg-mono" x="585" y="176" fill="#86661A">CALL LIMIT</text></g>
    </svg>'''


def render(template, masthead, footer):
    data = load()
    example = data["examples"][0]
    values = {k.upper(): esc(v) for k, v in example.items() if isinstance(v, str)}
    examples = []
    for item in data["examples"]:
        parts = ''.join(f'<dt>{label}</dt><dd>{esc(item[key])}</dd>' for label, key in [
            ("Goal", "goal"), ("Accountable role", "owner"), ("Baseline", "baseline"),
            ("Starting pattern", "why"), ("Boundary", "boundary"), ("Ingestion", "ingestion"),
            ("Grounding", "grounding"), ("Review", "review"), ("Evaluation", "quality"),
            ("Operation", "operation"), ("Improvement", "improvement")])
        examples.append(f'<article><h3 id="example-{item["id"]}">{esc(item["title"])}</h3><dl class="es-worked">{parts}</dl>{acceptance(item)}</article>')
    values.update({
        "MASTHEAD": masthead, "FOOTER": footer,
        "STUDIO_ART": illustration(json.loads((ROOT / "content/art.json").read_text()), "atlas-workshop", eager=True),
        "EXAMPLE_OPTIONS": ''.join(f'<option value="{item["id"]}">{esc(item["label"])}</option>' for item in data["examples"]),
        "ACCEPTANCE": acceptance(example), "WORKED_EXAMPLES": ''.join(examples), "RUNTIME_SCENE": scene(),
        "STUDIO_JSON": json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"),
        "SOURCES_LIST": ''.join(f'<li id="source-{s["id"]}"><a href="{esc(s["url"], quote=True)}">{esc(s["title"])}</a><p>{esc(s["claim"])}</p><small>Checked {esc(s["checked"])}</small></li>' for s in data["sources"]),
    })
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template
