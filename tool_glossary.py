"""Short, source-linked explanations for the tools named by each playbook."""
from html import escape
import re


def render(terms, glossary):
    missing = set(terms) - glossary.keys()
    if missing:
        raise ValueError(f'Missing tool explanations: {sorted(missing)}')
    chips, definitions = [], []
    for term in terms:
        entry = glossary[term]
        for field in ('what', 'remember', 'url'):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f'{term}: missing {field}')
        if not entry['url'].startswith('https://'):
            raise ValueError(f'{term}: documentation URL must use HTTPS')
        slug = 'pb-tool-' + re.sub(r'[^a-z0-9]+', '-', term.lower()).strip('-')
        chips.append(f'<button type="button" class="chip pb-tool-trigger" popovertarget="{slug}" aria-haspopup="dialog">{escape(term)}<span aria-hidden="true">?</span></button>')
        definitions.append(f'''<div class="pb-definition" id="{slug}" popover="auto" role="dialog" aria-labelledby="{slug}-title">
          <button type="button" class="pb-tool-close" popovertarget="{slug}" popovertargetaction="hide" autofocus aria-label="Close {escape(term, quote=True)} explanation">Close ×</button>
          <p class="sec-label">What is it?</p><h3 id="{slug}-title">{escape(term)}</h3>
          <p>{escape(entry['what'])}</p><p class="pb-tool-memory"><strong>Think of it as</strong><br>{escape(entry['remember'])}</p>
          <a href="{escape(entry['url'], quote=True)}" target="_blank" rel="noopener">Official documentation ↗</a>
        </div>''')
    return ''.join(chips), ''.join(definitions)
