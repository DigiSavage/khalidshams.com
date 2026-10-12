"""Public shells only. Private records are exclusively fetched from authorized APIs."""
import json,re
from pathlib import Path

def render(root,dist,tpl,fill,page,masthead,footer,site):
    for route,title in [('login','Owner sign-in'),('admin','Private control room'),('contact','Start a conversation')]:
        body=fill(tpl(route+'.html'),MASTHEAD=masthead,FOOTER=footer)
        html=page(body,title=title+' · Khalid Shams',description='Owner access to the site.' if route!='contact' else 'Talk about architecture, cloud platforms, AI systems and teaching.',canonical=site+'/'+route+'/')
        if route!='contact':html=html.replace('<head>','<head>\n<meta name="robots" content="noindex, nofollow">')
        dest=dist/route;dest.mkdir(exist_ok=True);(dest/'index.html').write_text(html)

def public_pages(dist):
    pages={}
    for file in dist.rglob('index.html'):
        route='/'+str(file.parent.relative_to(dist)).strip('.')
        route=route.rstrip('/')+'/'
        if route.startswith(('/admin/','/login/')):continue
        s=file.read_text();m=re.search(r'<title>(.*?)</title>',s,re.S)
        import html
        pages[route]=html.unescape(m.group(1)) if m else route
    return pages
