"""Browser integration against the real handler with isolated moto DynamoDB and signed JWT fixtures."""
import sys,os,json,time,threading
from pathlib import Path
from http.server import HTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).parent))
from test_service import Fixture,observation
ROOT=Path(__file__).resolve().parents[2];OUT=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/admin-ui');OUT.mkdir(parents=True,exist_ok=True)
f=Fixture();os.environ['PUBLIC_ORIGIN']='http://localhost:8769';f.auth.origin=os.environ['PUBLIC_ORIGIN']
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'dist'),**kw)
    def log_message(self,*a):pass
    def do_GET(self):
        if self.path=='/__fixture__/enrollment':
            import auth
            f.auth.idp.admin_get_user.return_value['UserMFASettingList']=[]
            f.store.put('sessions',dict(pk='enrollment#'+auth.digest('fixture-enrollment'),sk='0',access=f.token(scope='site-admin/owner aws.cognito.signin.user.admin'),sub='owner-id',csrf='fixture-enrollment-csrf',ttl=int(time.time())+600))
            f.auth.idp.associate_software_token.return_value={'SecretCode':'FIXTUREKEYONLY'}
            def verify(**kwargs):
                f.auth.idp.admin_get_user.return_value['UserMFASettingList']=['SOFTWARE_TOKEN_MFA']
                return {'Status':'SUCCESS'}
            f.auth.idp.verify_software_token.side_effect=verify
            self.send_response(204);self.send_header('Set-Cookie','__Host-ks-enrollment=fixture-enrollment; Path=/; HttpOnly; SameSite=Lax; Secure');self.end_headers();return
        if self.path=='/__fixture__/login':
            f.login();self.send_response(204);self.send_header('Set-Cookie','__Host-ks-session='+f.sid+'; Path=/; HttpOnly; SameSite=Lax; Secure');self.end_headers();return
        if self.path.startswith('/api/'):return self.api()
        super().do_GET()
    def do_POST(self):self.api()
    def do_PATCH(self):self.api()
    def do_PUT(self):self.api()
    def do_DELETE(self):self.api()
    def api(self):
        import app
        u=urlsplit(self.path);body=self.rfile.read(int(self.headers.get('Content-Length','0'))).decode()
        headers=dict(self.headers);headers['X-Site-Origin']=app.SALT;headers['CloudFront-Viewer-Address']='192.0.2.1:1'
        result=app.handler(dict(path=u.path,httpMethod=self.command,headers=headers,body=body,queryStringParameters={k:v[0] for k,v in parse_qs(u.query).items()}))
        self.send_response(result['statusCode'])
        for k,v in result['headers'].items():self.send_header(k,v)
        for k,values in result.get('multiValueHeaders',{}).items():
            for v in values:self.send_header(k,v)
        self.end_headers();self.wfile.write(result['body'].encode())
server=HTTPServer(('localhost',8769),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();BASE='http://localhost:8769';results=[]
def check(label,ok):
    results.append({'check':label,'ok':bool(ok)});print(('PASS ' if ok else 'FAIL ')+label,flush=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    for width in (390,1380):
        c=browser.new_context(viewport={'width':width,'height':900});c.request.get(BASE+'/__fixture__/enrollment');p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        p.goto(BASE+'/login/?setup=mfa');p.locator('#mfa-start').click();p.locator('#mfa-key-area').wait_for(state='visible')
        check(f'enrollment is separate from private data {width}',c.request.get(BASE+'/api/admin/inquiries').status==401)
        check(f'enrollment key visible after explicit action {width}',p.locator('#mfa-key').inner_text()=='FIXTUREKEYONLY')
        check(f'enrollment no overflow {width}',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        p.screenshot(path=str(OUT/f'enrollment-{width}.png'),full_page=True)
        p.locator('#mfa-code').fill('123456');p.locator('#mfa-form button').click();p.wait_for_url(BASE+'/admin/')
        p.wait_for_function("document.querySelector('#admin-status').textContent.includes('observations loaded')")
        check(f'verified enrollment opens dashboard {width}',p.locator('#admin-app').is_visible())
        check(f'enrollment no script errors {width}',not errors);c.close()
    c=browser.new_context();p=c.new_page();p.goto(BASE+'/login/?error=signin');p.locator('#owner-signin').wait_for(state='visible');check('callback failure explains sign-in instead of blaming code countdown','does not mean its countdown expired' in p.locator('#login-status').inner_text());c.close()
    # An unauthenticated shell must never reveal records or pretend to be authenticated.
    c=browser.new_context();p=c.new_page();p.goto(BASE+'/admin/');p.wait_for_function("document.querySelector('#admin-status').textContent.includes('expired')")
    check('unauthenticated admin remains locked',p.locator('#admin-app').is_hidden());check('private response is no-store','no-store' in c.request.get(BASE+'/api/admin/inquiries').headers['cache-control']);c.close()
    for width in (390,1380):
        for theme in ('light','dark'):
            c=browser.new_context(viewport={'width':width,'height':900},color_scheme=theme);c.request.get(BASE+'/__fixture__/login');p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(BASE+'/admin/');p.wait_for_function("document.querySelector('#admin-status').textContent.includes('observations loaded')")
            check(f'empty owner dashboard {width} {theme}',p.locator('#metrics').is_visible() and 'Unavailable' in p.locator('#metrics').inner_text());check(f'no overflow {width} {theme}',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            for section in ('pages','journeys','inquiries','health','settings','overview'):
                p.locator('[data-section="'+section+'"]').press('Enter');check(f'{section} is keyboard-focusable and opens {width} {theme}',p.locator('#cr-'+section).is_visible() and p.locator('[data-section="'+section+'"]').evaluate('(e)=>e.tabIndex===0'))
            p.screenshot(path=str(OUT/f'admin-empty-{width}-{theme}.png'),full_page=True);check(f'no script errors {width} {theme}',not errors);c.close()
    # An insights outage is not an owner-auth failure. Exercise the real handler
    # and persisted DynamoDB measurements through a failed load, retry and expiry.
    c=browser.new_context(viewport={'width':390,'height':844});c.request.get(BASE+'/__fixture__/login')
    p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    view=observation();f.store.save_event(view,90)
    real_events=f.store.events
    def unavailable_events(*args,**kwargs):raise RuntimeError('Isolated insights outage')
    try:
        f.store.events=unavailable_events
        p.goto(BASE+'/admin/');p.wait_for_function("document.querySelector('#admin-status').textContent.includes('Use Apply period to retry')")
        check('insights outage retains owner navigation and signout',p.locator('#admin-app').is_visible() and p.locator('#admin-logout').is_visible() and p.locator('#admin-signin').is_hidden())
        check('insights outage retains independent private tools',p.locator('.cr-nav a[href="/admin/decision-room/"]').is_visible() and p.locator('.cr-nav a[href="/admin/video-studio/"]').is_visible())
        check('failed first load does not invent zero metrics',p.locator('#metrics').inner_text()=='' and 'No observations have loaded' in p.locator('#admin-status').inner_text())
        check('insights retry remains available',p.get_by_role('button',name='Apply period',exact=True).is_enabled())
        p.screenshot(path=str(OUT/'admin-insights-unavailable-390.png'),full_page=True)
        f.store.events=real_events
        p.get_by_role('button',name='Apply period',exact=True).click();p.wait_for_function("document.querySelector('#admin-status').textContent.includes('observations loaded')")
        check('retry loads real persisted observations',p.locator('.cr-metric').filter(has_text='Pageviews').locator('strong').inner_text()=='1')
        previous_metrics=p.locator('#metrics').inner_text()
        f.store.events=unavailable_events
        p.get_by_role('button',name='Apply period',exact=True).click();p.wait_for_function("document.querySelector('#admin-status').textContent.includes('Previous observations remain visible')")
        check('refresh outage labels preserved observations honestly',p.locator('#metrics').inner_text()==previous_metrics and 'observations loaded' not in p.locator('#admin-status').inner_text())
        f.store.events=real_events
        f.store.delete('sessions','session#'+__import__('auth').digest(f.sid))
        p.get_by_role('button',name='Apply period',exact=True).click();p.wait_for_function("document.querySelector('#admin-app').hidden")
        check('unauthorized retry still locks private tools and signout',p.locator('#admin-app').is_hidden() and p.locator('#admin-logout').is_hidden() and p.locator('#admin-signin').is_visible())
        check('unauthorized retry clears analytics and coverage',all(p.locator('#'+id).inner_text()=='' for id in ('metrics','trend','pages-table','coverage','freshness')))
        check('insights outage and recovery have no script errors',not errors)
    finally:
        f.store.events=real_events;c.close()
        for row in f.store.events(view['at']-1,int(time.time())+1)[0]:f.store.delete('events',row['pk'],row['sk'])
    # The actual public form must persist before displaying success, and its private inbox must safely render markup.
    public=browser.new_context();p=public.new_page();p.goto(BASE+'/contact/');check('ordinary contact starts without an offer draft',p.locator('[name=message]').input_value()=='');p.goto(BASE+'/contact/?offer=architecture-review&ks-test=1');check('legacy review link explains current community context',p.locator('#offer-context').is_visible() and '[Community learning]' in p.locator('[name=message]').input_value());p.locator('[name=name]').fill('<img src=x onerror=alert(1)>');p.locator('[name=email]').fill('fixture@example.test');p.locator('[name=topic]').select_option('architecture');p.locator('[name=message]').fill('<script>window.injected=true</script> A fixture inquiry.');p.locator('button[type=submit]').click();p.wait_for_function("document.querySelector('#contact-status').textContent.includes('has been stored')");check('contact success reflects persisted record',len(f.store.query('inquiries','inbox')[0])==1);check('legacy review source survives the real handler contract',f.store.query('inquiries','inbox')[0][0]['source']=='/');p.screenshot(path=str(OUT/'contact-confirmation.png'),full_page=True);public.close()
    c=browser.new_context(viewport={'width':390,'height':844});c.request.get(BASE+'/__fixture__/login');p=c.new_page();p.goto(BASE+'/admin/');p.wait_for_function("document.querySelector('#admin-status').textContent.includes('observations loaded')");p.locator('[data-section=inquiries]').click();p.locator('#show-tests').check();p.locator('#inquiry-filters button').click();p.locator('#inbox button').click();check('stored XSS is displayed as inert text',p.locator('#inquiry-detail script,#inquiry-detail img').count()==0 and '<script>' in p.locator('#inquiry-detail').inner_text());p.locator('#edit-status').select_option('read');p.locator('#inquiry-detail textarea').fill('Reviewed fixture');p.get_by_role('button',name='Save inquiry',exact=True).click();p.wait_for_function("document.querySelector('#admin-status').textContent==='Inquiry updated.'");check('inbox update persists',f.store.query('inquiries','inbox')[0][0]['status']=='read');p.screenshot(path=str(OUT/'inquiry-phone.png'),full_page=True)
    # Session removal clears existing private UI on the next request.
    f.store.delete('sessions','session#'+__import__('auth').digest(f.sid));p.locator('#range-form button').click();p.wait_for_function("document.querySelector('#admin-app').hidden");check('expiry clears previously visible private records',p.locator('#inbox').inner_text()=='' and p.locator('#inquiry-detail').inner_text()=='');c.close()
    # Consent, retry and exclusion use actual browser requests and persisted events.
    c=browser.new_context();p=c.new_page();requests=[];p.on('request',lambda r:requests.append(r) if '/api/events' in r.url else None);p.goto(BASE+'/?ks-test=1');p.get_by_role('button',name='Keep measurements off',exact=True).click();check('declined consent sends no events',not requests);p.locator('[data-measurement-settings]').click();p.get_by_role('button',name='Allow measurements',exact=True).click();p.wait_for_timeout(700);check('explicit consent persists marked observations',any(r.get('test') for r in f.store.events(int(time.time())-60,int(time.time())+1)[0]));check('analytics payload omits form values and query strings',all('example.test' not in (r.post_data or '') and 'ks-test' not in (r.post_data or '') for r in requests));p.locator('[data-measurement-settings]').click();p.get_by_role('button',name='Keep measurements off',exact=True).click();check('revocation removes random identifiers',p.evaluate("localStorage.getItem('ks-measurement-visitor')===null"));c.close()
    c=browser.new_context();c.add_init_script("localStorage.setItem('ks-measurement-consent',JSON.stringify({value:'yes',expires:Date.now()+100000}));localStorage.setItem('ks-measurement-visitor','old-identifier')");p=c.new_page();p.route('**/api/config',lambda r:r.fulfill(json={'available':False}));p.goto(BASE+'/?ks-test=1');p.locator('[data-measurement-settings]').click();p.get_by_role('button',name='Keep measurements off',exact=True).click();check('consent can be revoked while the backend is unavailable',p.evaluate("localStorage.getItem('ks-measurement-visitor')===null"));c.close()
    c=browser.new_context();p=c.new_page();p.goto(BASE+'/?ks-test=1');p.get_by_role('button',name='Allow measurements',exact=True).click();second=c.new_page();second.goto(BASE+'/learn/?ks-test=1');second.locator('[data-measurement-settings]').click();second.get_by_role('button',name='Keep measurements off',exact=True).click();p.wait_for_timeout(100);check('revocation reaches other open tabs',p.evaluate("localStorage.getItem('ks-measurement-visitor')===null&&JSON.parse(localStorage.getItem('ks-measurement-consent')).value==='no'"));c.close()
    for pref in ('owner','gpc'):
        c=browser.new_context();c.add_init_script("localStorage.setItem('ks-owner-exclude','1')" if pref=='owner' else "Object.defineProperty(navigator,'globalPrivacyControl',{get:()=>true})");p=c.new_page();sent=[];p.on('request',lambda r:sent.append(r.url) if '/api/events' in r.url else None);p.goto(BASE+'/?ks-test=1');p.wait_for_timeout(300);check(pref+' exclusion prevents collection',not sent and p.locator('.measurement-choice').count()==0);c.close()
    c=browser.new_context();p=c.new_page();attempts=[]
    def retry(route):
        attempts.append(route.request.post_data)
        if len(attempts)==1:route.abort()
        else:route.continue_()
    p.route('**/api/events',retry);p.clock.install();p.goto(BASE+'/?ks-test=1');p.get_by_role('button',name='Allow measurements',exact=True).click();p.wait_for_timeout(300);p.clock.fast_forward(16000);p.wait_for_timeout(200);check('failed event delivery retries the same event ID',len(attempts)>=2 and json.loads(attempts[0])['events'][0]['id']==json.loads(attempts[1])['events'][0]['id']);c.close();browser.close()
# Build output cannot include private routes in discovery indexes or backend fixtures.
search=(ROOT/'dist/search.json').read_text();sitemap=(ROOT/'dist/sitemap.xml').read_text()
check('admin and login excluded from sitemap and search',all(x not in search+sitemap for x in ('/admin/','/login/')))
check('private shells have noindex',all('noindex' in (ROOT/'dist'/route/'index.html').read_text() for route in ('login','admin')))
check('private fixture records absent from dist',all('fixture@example.test' not in f.read_text(errors='ignore') for f in (ROOT/'dist').rglob('*') if f.is_file() and f.suffix in {'.json','.html','.js'}))
(OUT/'checks.json').write_text(json.dumps(results,indent=2)+'\n');server.shutdown();f.close();failed=sum(not r['ok'] for r in results);print(f'{len(results)-failed}/{len(results)} passed');sys.exit(bool(failed))
