"""Export the studio as an offline review file, without publishing the website.

Run after build.py. Site navigation remains links to the existing live website.
Only the studio is embedded; the live site's search and drawer are not simulated.
"""
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
import enterprise_build
import learn_build


def data_url(path, mime):
    return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()


def export(out):
    header = '<header class="wrap" style="padding-top:22px;padding-bottom:22px;border-bottom:1px solid var(--rule2)"><a href="https://khalidshams.com/" style="font-family:var(--mono);text-decoration:none">KHALID SHAMS</a><span style="float:right;font:12px var(--mono);color:var(--mute)">REVIEW PREVIEW</span></header>'
    footer = '<p class="es-note">Review preview. The public site has not been changed. <a href="https://khalidshams.com/">Visit khalidshams.com</a></p>'
    body = enterprise_build.render(build.tpl('enterprise.html'), header, footer)
    body = body.replace('{{PAGENAV}}', learn_build.page_nav(body))
    html = build.page(body, title='Enterprise agent studio · review preview', description='A local interactive review of the SHAMS enterprise agent studio.', canonical='https://khalidshams.com/architect/agent-studio/')
    html = html.replace('<script src="/search.js" defer></script>', '')
    html = html.replace('<link rel="stylesheet" href="/enterprise/studio.css">', '<style>'+(ROOT/'static/enterprise/studio.css').read_text()+'</style>')
    for name in ('engine', 'studio'):
        html = html.replace(f'<script src="/enterprise/{name}.js" defer></script>', '<script>'+(ROOT/f'static/enterprise/{name}.js').read_text()+'</script>')
    # Use the responsive compact originals; both genuinely distinct themes remain.
    html = re.sub(r' srcset="[^"]*"', '', html)
    def image(match):
        path = ROOT/'static'/match[1].lstrip('/')
        return 'src="'+data_url(path, 'image/webp')+'"'
    html = re.sub(r'src="(/art/[^"]+)"', image, html)
    # Embed the cached unmodified fonts when available. Otherwise retain the
    # normal stylesheet with the site's existing local fallback fonts.
    cache = ROOT/'work/font-cache'
    if cache.is_dir():
        import hashlib
        url = 'https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap'
        css = cache/(hashlib.sha256(url.encode()).hexdigest()+'.body')
        if css.exists():
            fonts = css.read_text()
            def font(match):
                file = cache/(hashlib.sha256(match[1].encode()).hexdigest()+'.body')
                return 'url('+data_url(file,'font/ttf')+')' if file.exists() else match[0]
            fonts = re.sub(r'url\((https://[^)]+)\)', font, fonts)
            html = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com/[^"]+">', lambda _: '<style>'+fonts+'</style>', html)
    html = re.sub(r'href="/(?!/)([^"]*)"', r'href="https://khalidshams.com/\1"', html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(out)


if __name__ == '__main__':
    export(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'dist/enterprise-agent-studio-preview.html')
