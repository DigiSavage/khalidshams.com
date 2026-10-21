"""Public worked engagement. No interview records or private assessment data."""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
ROUTE = '/method/engagement/'
STAGES = ('prepare', 'audience', 'discover', 'design', 'scope', 'rehearse',
          'deliver', 'release', 'operate', 'enable', 'partner')
AUDIENCES = ('executive', 'engineering', 'risk', 'operations')
SOURCES = (
    ('copilot', 'Copilot Studio: capabilities and operating model', 'https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-what-is-copilot-studio'),
    ('foundry', 'Microsoft Foundry: models, agents and controls', 'https://learn.microsoft.com/en-us/azure/foundry/what-is-foundry'),
    ('onelake', 'OneLake: management permissions and data access', 'https://learn.microsoft.com/en-us/fabric/onelake/security/get-started-security'),
    ('connectors', 'Data Factory: connector capabilities', 'https://learn.microsoft.com/en-us/fabric/data-factory/connector-overview'),
    ('capacity', 'Fabric: licenses and capacity', 'https://learn.microsoft.com/en-us/fabric/enterprise/licenses'),
    ('operations', 'Azure Well-Architected: operational excellence', 'https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/checklist'),
    ('cosell', 'Microsoft: co-sell requirements', 'https://learn.microsoft.com/en-us/partner-center/referrals/co-sell-requirements'),
)


def load():
    data = json.loads((ROOT / 'content/engagement.json').read_text())
    if tuple(s['id'] for s in data['stages']) != STAGES:
        raise ValueError('Engagement stages must preserve the complete delivery journey')
    if set(data['audiences']) != set(AUDIENCES):
        raise ValueError('Engagement needs all four audience views')
    for stage in data['stages']:
        for key in ('id', 'title', 'shams', 'lead', 'actions', 'artifact', 'owner', 'exit', 'hold'):
            if not stage.get(key):
                raise ValueError(f'Missing engagement stage field: {key}')
        if len(stage['actions']) < 3 or len(stage['artifact']['lines']) < 3:
            raise ValueError('Each stage needs concrete actions and an inspectable artifact')
    return data


def render(template, masthead, footer):
    data = load()
    cards, links = [], []
    for index, stage in enumerate(data['stages'], 1):
        sid = escape(stage['id'])
        links.append(f'<li><a href="#stage-{sid}"><span>{index:02}</span>{escape(stage["title"])}</a></li>')
        actions = ''.join(f'<li>{escape(item)}</li>' for item in stage['actions'])
        lines = ''.join(f'<li>{escape(item)}</li>' for item in stage['artifact']['lines'])
        cards.append(f'''<article class="eg-stage" id="stage-{sid}">
          <div class="eg-stage-title"><span class="eg-number">{index:02}</span><div><p class="sec-label">{escape(stage['shams'])}</p><h3>{escape(stage['title'])}</h3></div></div>
          <p class="eg-stage-lead">{escape(stage['lead'])}</p>
          <div class="eg-stage-grid"><div><h4>What I do</h4><ul>{actions}</ul></div>
          <details class="eg-artifact"><summary>Inspect the artifact: {escape(stage['artifact']['title'])}</summary><p class="eg-caption">Worked example · D-01</p><ul>{lines}</ul></details></div>
          <dl class="eg-gate"><div><dt>Accountable role</dt><dd>{escape(stage['owner'])}</dd></div><div><dt>Ready to move when</dt><dd>{escape(stage['exit'])}</dd></div><div><dt>Hold when</dt><dd>{escape(stage['hold'])}</dd></div></dl>
        </article>''')
    audience_cards = []
    for key in AUDIENCES:
        a = data['audiences'][key]
        audience_cards.append(f'''<article><h3>{escape(a['label'])}</h3><p>{escape(a['opening'])}</p><dl><dt>Ask</dt><dd>{escape(a['question'])}</dd><dt>Show</dt><dd>{escape(a['show'])}</dd><dt>Decision</dt><dd>{escape(a['decision'])}</dd></dl></article>''')
    sources = ''.join(f'<li id="source-{key}"><a href="{url}">{escape(title)}</a></li>' for key, title, url in SOURCES)
    encoded = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    values = {'MASTHEAD': masthead, 'FOOTER': footer, 'STAGES': ''.join(cards),
              'STAGE_LINKS': ''.join(links), 'AUDIENCE_CARDS': ''.join(audience_cards),
              'SOURCES': sources, 'ENGAGEMENT_DATA': encoded,
              'SCENARIO_TITLE': escape(data['scenario']['title']),
              'SCENARIO_DESCRIPTION': escape(data['scenario']['description'])}
    for key, value in values.items():
        template = template.replace('{{' + key + '}}', value)
    return template
