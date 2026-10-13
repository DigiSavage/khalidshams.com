"""Public shells only. Private records are exclusively fetched from authorized APIs."""
import base64,hashlib,json,re
from pathlib import Path

def render(root,dist,tpl,fill,page,masthead,footer,site):
    for route,title in [('login','Owner sign-in'),('admin','Private control room'),('admin/decision-room','SHAMS Decision Room'),('contact','Start a conversation')]:
        template='decision_room' if route=='admin/decision-room' else route
        body=fill(tpl(template+'.html'),MASTHEAD=masthead,FOOTER=footer)
        html=page(body,title=title+' · Khalid Shams',description='Owner access to the site.' if route!='contact' else 'Talk about architecture, cloud platforms, AI systems and teaching.',canonical=site+'/'+route+'/')
        if route!='contact':html=html.replace('<head>','<head>\n<meta name="robots" content="noindex, nofollow">')
        if route=='admin/decision-room':
            # Permit only the build's known inline scripts, never injected code.
            hashes=["'sha256-"+base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()+"'" for script in re.findall(r'<script\b[^>]*>(.*?)</script>',html,re.S) if script.strip()]
            policy="default-src 'self'; script-src 'self' "+' '.join(hashes)+"; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-src 'none'"
            html=html.replace('<head>','<head>\n<meta name="referrer" content="no-referrer">\n<meta http-equiv="Content-Security-Policy" content="'+policy+'">')
        dest=dist/route;dest.mkdir(parents=True,exist_ok=True);(dest/'index.html').write_text(html)

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
