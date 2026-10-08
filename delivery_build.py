"""Shared, editable content for the delivery overview and its vector poster."""
from html import escape
from math import cos, sin, pi

COMPONENTS = [
    ('Model', 'Generates from learned patterns and the context supplied.',
     'Verify important outputs; it does not know your live business by default.', 'llm'),
    ('Retrieval', 'Selects relevant evidence for the current request.',
     'RAG is not persistent memory. Check source quality, freshness and access.', 'rag'),
    ('Tools and MCP', 'Tools perform operations; MCP standardises their connection.',
     'The application still validates requests and enforces permissions.', 'mcp'),
    ('Skills and workflows', 'Skills package reusable instructions and resources.',
     'Workflows define the sequence. Neither guarantees a correct outcome.', 'skills'),
    ('Agent', 'Uses a model and tools to choose steps toward a bounded goal.',
     'Add evaluations, approval gates, budgets, traces and a way to stop.', 'agent'),
]
DECISIONS = [
    ('Name the owner', 'Who owns the decision, the evidence and the result?'),
    ('Define the handoff', 'What crosses the boundary, and how is it checked?'),
    ('Measure the result', 'Does the added capability justify its coordination cost?'),
]


def human_coordination():
    points = [(150 + 80 * cos(-pi / 2 + j * pi / 3), 110 + 80 * sin(-pi / 2 + j * pi / 3)) for j in range(6)]
    network = ''.join(f'<path d="M{x:.2f} {y:.2f}L{bx:.2f} {by:.2f}" fill="none" stroke="#C6C6BF"/>'
                      for i, (x, y) in enumerate(points) for bx, by in points[i + 1:])
    network += ''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="#0E1012"/>' for x, y in points)
    questions = ''.join(f'<li><h4>{escape(title)}</h4><p>{escape(question)}</p></li>' for title, question in DECISIONS)
    return f'''<div class="delivery-human" id="human-coordination">
      <p class="sec-label">People and delivery</p><h3>Human teams: the same arithmetic, different work.</h3>
      <p>I use this count to ask where a handoff needs an owner or a clearer interface. It assumes every pair of people can connect. Real teams organise around roles, shared artefacts and boundaries; they do not use every possible connection equally.</p>
      <div class="delivery-team-grid"><div>
        <label for="delivery-people">People in the team</label>
        <input id="delivery-people" type="range" min="2" max="12" value="6" aria-describedby="delivery-count delivery-assumption">
        <p id="delivery-count" aria-live="polite"><strong>6 people · 15 possible pairwise connections</strong></p>
        <p id="delivery-assumption">n(n − 1) / 2 grows quadratically, not exponentially. This is a topology count, not a prediction of messages, meetings, delivery time or productivity.</p>
        <noscript><p>The example shows six people. Enable JavaScript to change the count.</p></noscript>
      </div><svg id="delivery-team-svg" viewBox="0 0 300 220" role="img" aria-label="Six people with 15 possible undirected pairwise connections"><g>{network}</g></svg></div>
      <p class="delivery-limit">Fewer links do not prove a better team. A coordinator can reduce direct connections while creating a bottleneck. For people, inspect decision rights and handoffs. For software agents, also inspect permissions, context isolation, retries and evaluations.</p>
      <ol class="delivery-decisions">{questions}</ol>
      <p><strong>Clear ownership and interfaces reduce coordination overhead.</strong> I measure the outcome before adding another person, agent or layer.</p>
    </div>'''


def overview():
    cards = ''.join(
        f'<li><span class="sec-label">{i:02d}</span><h4>{escape(title)}</h4>'
        f'<p>{escape(what)}</p><p class="delivery-limit">{escape(limit)}</p>'
        f'<a href="/method/?part={part}#agentic">Inspect {escape(title.lower())} →</a></li>'
        for i, (title, what, limit, part) in enumerate(COMPONENTS, 1))
    return f'''<div class="delivery-overview" id="building-ai-systems">
      <p class="sec-label">A delivery field guide</p>
      <h3>Building AI systems: stack, structure and scale.</h3>
      <p class="intro">I start with the work, then choose the components and the people responsible for them. A useful model is one part of the system. Clear evidence, controlled actions and explicit handoffs turn it into something I can operate.</p>
      <p>These are five connected components, not a mandatory build sequence. The <a href="/learn/#stack">seven-layer architecture</a> explains where they sit. Retrieval and stored memory have different jobs; an agent is only needed when the next step must be chosen dynamically.</p>
      <ol class="delivery-components">{cards}</ol>
      <div class="delivery-actions"><a href="#human-coordination">Explore human-team coordination →</a><a href="#ag-cost">Compare agent networks →</a></div>
      <details class="delivery-download"><summary>View and download the one-page field guide</summary>
        <p>A scalable, text-selectable poster for design reviews. <a href="/building-ai-systems-light.svg" download>Download light SVG</a> · <a href="/building-ai-systems-dark.svg" download>Download dark SVG</a></p>
        <a class="delivery-poster" href="/building-ai-systems-light.svg" aria-label="Open the full-size Building AI systems field guide">
          <img class="delivery-light" src="/building-ai-systems-light.svg" width="1200" height="1720" loading="lazy" alt="Building AI systems: five components, possible team connections, and three delivery decisions. The same guidance is available as text on this page.">
          <img class="delivery-dark" src="/building-ai-systems-dark.svg" width="1200" height="1720" loading="lazy" alt="Building AI systems: five components, possible team connections, and three delivery decisions. The same guidance is available as text on this page.">
        </a>
      </details>
      <p class="delivery-sources">Technical references: <a href="https://modelcontextprotocol.io/docs/learn/architecture">MCP architecture</a> · <a href="https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview">Retrieval-augmented generation</a> · <a href="https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills">Agent skills</a></p>
    </div>'''


def poster(theme):
    dark = theme == 'dark'
    paper, card, ink, body, blue, rule = (
        ('#0D0F11', '#14171A', '#F1F2F1', '#B9C0C5', '#8FA6FF', '#343B45') if dark else
        ('#F7F7F5', '#FFFFFF', '#0E1012', '#3E4449', '#1F45C8', '#C6C6BF'))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1720" viewBox="0 0 1200 1720" role="img" aria-labelledby="title desc">',
             '<title id="title">Building AI systems: stack, structure and scale</title>',
             '<desc id="desc">Five components with their limits. Human team diagrams count possible pairwise connections, not communication volume or productivity. Clear ownership, explicit handoffs and measured outcomes guide delivery.</desc>',
             f'<rect width="1200" height="1720" fill="{paper}"/>']

    def text(x, y, value, size=21, color=body, serif=False):
        family = 'Georgia,serif' if serif else 'Arial,sans-serif'
        parts.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}">{escape(value)}</text>')

    def rect(x, y, w, h, color=card):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{color}" stroke="{rule}"/>')

    text(64, 58, 'KHALID SHAMS  /  ARCHITECTURE FIELD GUIDE', 16, blue)
    text(64, 125, 'Building AI systems', 58, ink, True)
    text(64, 178, 'Stack, structure and scale.', 38, ink, True)
    text(64, 224, 'Choose the components. Define the boundaries. Design the team.', 23)
    text(64, 281, '01  FIVE COMPONENTS, DIFFERENT JOBS', 18, blue)
    for i, (title, what, limit, _) in enumerate(COMPONENTS):
        y = 305 + i * 113
        rect(64, y, 1072, 99)
        rect(82, y + 21, 54, 54, paper)
        text(96, y + 56, str(i + 1).zfill(2), 23, blue)
        text(156, y + 30, title, 25, ink)
        text(156, y + 58, what, 19)
        text(156, y + 83, limit, 18)
    text(64, 904, 'Components, not a mandatory stack. Choose an agent only when the task needs one.', 21)
    text(64, 960, '02  HUMAN TEAMS: COUNT POSSIBLE CONNECTIONS', 18, blue)
    for i, n in enumerate((2, 3, 4, 5, 6, 8, 10)):
        x = 64 + i * 155
        rect(x, 985, 142, 205)
        text(x + 22, 1016, f'{n} people', 20, ink)
        points = [(x + 71 + 49 * cos(-pi / 2 + j * 2 * pi / n), 1084 + 49 * sin(-pi / 2 + j * 2 * pi / n)) for j in range(n)]
        for j, (ax, ay) in enumerate(points):
            for bx, by in points[j + 1:]:
                parts.append(f'<path d="M{ax:.2f} {ay:.2f}L{bx:.2f} {by:.2f}" fill="none" stroke="{body}" stroke-opacity=".65"/>')
        for px, py in points:
            parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5" fill="{ink}"/>')
        count = n * (n - 1) // 2
        text(x + 25, 1171, f'{count} '+('link' if count == 1 else 'links'), 22, blue)
    text(64, 1234, 'n(n − 1) / 2', 36, blue, True)
    text(318, 1232, 'Quadratic growth, not exponential growth.', 24, ink)
    text(64, 1272, 'Assumes every pair can connect. Counts do not measure messages, time or productivity.', 21)
    text(64, 1304, 'Human teams and agent networks share this arithmetic, not the same operating model.', 21)
    text(64, 1366, '03  MAKE DELIVERY ACCOUNTABLE', 18, blue)
    for i, (title, question) in enumerate(DECISIONS):
        # Questions are deliberately split for a readable three-column review strip.
        lines = [('Who owns the decision,', 'the evidence and the result?'),
                 ('What crosses the boundary,', 'and how is it checked?'),
                 ('Does the added capability', 'justify its coordination cost?')][i]
        x = 64 + i * 366
        rect(x, 1390, 340, 131)
        text(x + 20, 1429, title, 25, ink)
        for j, line in enumerate(lines):
            text(x + 20, 1466 + j * 27, line, 20)
    text(64, 1574, 'Clear ownership and interfaces reduce coordination overhead.', 29, ink, True)
    text(64, 1613, 'Measure the outcome before adding another person, agent or layer.', 24)
    text(64, 1680, 'khalidshams.com/method/#building-ai-systems', 19, blue)
    text(925, 1680, 'FREE TO USE', 16)
    return ''.join(parts) + '</svg>'


def write_assets(destination):
    for theme in ('light', 'dark'):
        (destination / f'building-ai-systems-{theme}.svg').write_text(poster(theme), encoding='utf-8')
