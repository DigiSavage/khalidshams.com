"""Isolated DynamoDB fixtures and real signed JWTs. No production records or credentials."""
import sys,os,json,time,uuid,unittest,tempfile
from pathlib import Path
from unittest.mock import Mock,patch
from urllib.parse import urlsplit,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'services/site-admin'))
import boto3,jwt
from moto import mock_aws
from cryptography.hazmat.primitives.asymmetric import rsa
import app
from auth import Auth,Unauthorized,digest
from storage import Store
from contracts import Invalid,event,inquiry,spreadsheet
from metrics import aggregate

PAGES={'/':'Home','/contact/':'Contact','/learn/':'Learn','/architect/agent-studio/':'Studio'}
def uid():return str(uuid.uuid4())
def observation(**changes):
    return dict(v=1,id=uid(),visitor=uid(),session=uid(),page=uid(),path='/',at=int(time.time())-30,name='pageview',value=0,target='none',referrer='direct',campaign='direct',device='phone',browser='safari',consent=True,test=False,**{})|changes

class Fixture:
    def __init__(self):
        self.mock=mock_aws();self.mock.start()
        self.env=patch.dict(os.environ,{'AWS_DEFAULT_REGION':'us-east-1','AWS_REGION':'us-east-1','PUBLIC_ORIGIN':'https://khalidshams.com','USER_POOL_ID':'us-east-1_fixture','CLIENT_ID':'fixture','AUTH_DOMAIN':'https://fixture.example'})
        self.env.start();db=boto3.resource('dynamodb')
        for name in ('events','inquiries','audit','sessions'):
            os.environ[name.upper()+'_TABLE']='fixture-'+name
            db.create_table(TableName='fixture-'+name,KeySchema=[{'AttributeName':'pk','KeyType':'HASH'},{'AttributeName':'sk','KeyType':'RANGE'}],AttributeDefinitions=[{'AttributeName':'pk','AttributeType':'S'},{'AttributeName':'sk','AttributeType':'S'}],BillingMode='PAY_PER_REQUEST')
        self.store=Store();self.auth=Auth(self.store);self.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.auth.jwks=Mock();self.auth.jwks.get_signing_key_from_jwt.return_value.key=self.key.public_key()
        self.auth.idp=Mock();self.auth.idp.admin_get_user.return_value={'Enabled':True,'UserAttributes':[{'Name':'sub','Value':'owner-id'}],'UserMFASettingList':['SOFTWARE_TOKEN_MFA']};self.auth.idp.admin_list_groups_for_user.return_value={'Groups':[{'GroupName':'owner'}]}
        app.STORE=self.store;app.AUTH=self.auth;app.SALT='fixture-origin-only';app.PAGES=PAGES.copy();self.sid='fixture-session';self.csrf='fixture-csrf';self.login()
    def token(self,**changes):
        claims=dict(sub='owner-id',username='owner',iss=self.auth.issuer,iat=int(time.time())-1,exp=int(time.time())+800,token_use='access',client_id='fixture',scope='site-admin/owner',**{'cognito:groups':['owner']});claims.update(changes)
        return jwt.encode(claims,self.key,algorithm='RS256')
    def login(self):self.store.put('sessions',dict(pk='session#'+digest(self.sid),sk='0',access=self.token(),csrf=self.csrf,sub='owner-id',ttl=int(time.time())+800))
    def request(self,path,method='GET',data=None,owner=False,headers=None,q=None):
        h={'X-Site-Origin':app.SALT,'Origin':os.environ['PUBLIC_ORIGIN'],'CloudFront-Viewer-Address':'192.0.2.1:123','User-Agent':'fixture'}
        if owner:h.update(Cookie='__Host-ks-session='+self.sid,**{'X-Csrf-Token':self.csrf})
        h.update(headers or {})
        return app.handler(dict(path=path,httpMethod=method,headers=h,body=json.dumps(data) if data is not None else '',queryStringParameters=q))
    def challenge(self):
        r=self.request('/api/contact/challenge');token=json.loads(r['body'])['challenge'];row=self.store.get('sessions','challenge#'+digest(token));row['at']-=3;self.store.put('sessions',row);return token
    def contact(self,**changes):return dict(id=uid(),name='Fixture owner',email='fixture@example.test',company='',topic='architecture',message='A test inquiry, never production.',source='/contact/',website='',challenge=self.challenge(),test=True)|changes
    def close(self):self.mock.stop();self.env.stop();app.STORE=app.AUTH=app.SALT=None

class ServiceTests(unittest.TestCase):
    def setUp(self):self.f=Fixture();self.addCleanup(self.f.close)
    def request(self,*a,**kw):return self.f.request(*a,**kw)
    def test_private_access_denied(self):
        for route,method in [('/api/auth/session','GET'),('/api/admin/inquiries','GET'),('/api/admin/export','GET'),('/api/admin/settings','PUT'),('/api/admin/analytics','DELETE')]:
            r=self.request(route,method,{})
            self.assertEqual(r['statusCode'],401);self.assertIn('no-store',r['headers']['Cache-Control'])
    def test_origin_and_csrf_denied(self):
        self.assertEqual(self.request('/api/config',headers={'X-Site-Origin':'wrong'})['statusCode'],403)
        denied=self.request('/api/admin/settings','PUT',{},owner=True,headers={'Origin':'https://evil.example'})
        self.assertEqual(denied['statusCode'],400)
        self.assertIn('no-store',denied['headers']['Cache-Control'])
        self.assertIn('application/json',denied['headers']['Content-Type'])
        self.assertEqual(self.request('/api/admin/settings','PUT',{},owner=True,headers={'X-Csrf-Token':'bad'})['statusCode'],401)
    def test_jwt_rejections(self):
        for changes in [dict(exp=int(time.time())-20),dict(iss='other'),dict(token_use='id'),dict(client_id='wrong'),dict(scope='openid'),{'cognito:groups':[]}]:
            with self.subTest(changes=changes),self.assertRaises(Unauthorized):self.f.auth.validate(self.f.token(**changes),'access')
        wrong=rsa.generate_private_key(public_exponent=65537,key_size=2048);bad=jwt.encode({'sub':'x'},wrong,algorithm='RS256')
        with self.assertRaises(Unauthorized):self.f.auth.validate(bad,'access')
    def test_id_token_nonce_audience(self):
        token=self.f.token(token_use='id',aud='fixture',nonce='correct')
        self.assertEqual(self.f.auth.validate(token,'id','correct')['sub'],'owner-id')
        for nonce in ('wrong',None):
            with self.assertRaises(Unauthorized):self.f.auth.validate(token,'id',nonce)
        with self.assertRaises(Unauthorized):self.f.auth.validate(self.f.token(token_use='id',aud='wrong',nonce='correct'),'id','correct')
    def test_owner_membership_mfa_disabled(self):
        for key,value in [('Enabled',False),('UserMFASettingList',[])]:
            old=self.f.auth.idp.admin_get_user.return_value.copy();self.f.auth.idp.admin_get_user.return_value[key]=value
            self.assertEqual(self.request('/api/auth/session',owner=True)['statusCode'],401);self.f.auth.idp.admin_get_user.return_value=old
        self.f.auth.idp.admin_list_groups_for_user.return_value={'Groups':[]}
        self.assertEqual(self.request('/api/auth/session',owner=True)['statusCode'],401)
    def test_login_pkce_state_consumption(self):
        url,cookie=self.f.auth.start();q=parse_qs(urlsplit(url).query);self.assertEqual(q['code_challenge_method'],['S256']);self.assertIn('HttpOnly',cookie);self.assertIn('Secure',cookie)
        event_={'queryStringParameters':{'state':q['state'][0],'code':'fake'},'headers':{'cookie':'__Host-ks-login=wrong'}}
        with self.assertRaises(Unauthorized):self.f.auth.callback(event_)
        self.assertIsNone(self.f.store.get('sessions','login#'+digest(q['state'][0])))
    def test_valid_callback_and_replay_denial(self):
        import io
        url,jar=self.f.auth.start();q=parse_qs(urlsplit(url).query);nonce=q['nonce'][0]
        tokens={'id_token':self.f.token(token_use='id',aud='fixture',nonce=nonce),'access_token':self.f.token()}
        e={'queryStringParameters':{'state':q['state'][0],'code':'fixture-code'},'headers':{'cookie':jar.split(';')[0]}}
        with patch('auth.urlopen',return_value=io.StringIO(json.dumps(tokens))):session_cookie=self.f.auth.callback(e)
        self.assertIn('HttpOnly',session_cookie);self.assertIn('Secure',session_cookie)
        row=self.f.auth.session({'headers':{'cookie':session_cookie.split(';')[0]}});self.assertEqual(row['sub'],'owner-id')
        with self.assertRaises(Unauthorized):self.f.auth.callback(e)
    def test_explicit_analytics_deletion_prevents_retry_resurrection(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        view=observation();self.request('/api/events','POST',{'events':[view]});today=datetime.now(ZoneInfo('America/Phoenix')).date().isoformat();raw={'from':today,'to':today}
        self.assertEqual(self.request('/api/admin/analytics','DELETE',raw,owner=True)['statusCode'],400)
        r=self.request('/api/admin/analytics','DELETE',raw|{'confirm':f'DELETE ANALYTICS {today} {today}'},owner=True);self.assertEqual(json.loads(r['body'])['deleted'],1)
        self.assertEqual(json.loads(self.request('/api/events','POST',{'events':[view]})['body'])['duplicates'],1)
        self.assertEqual(self.f.store.events(view['at']-1,int(time.time())+1)[0],[])
    def test_session_expiry_logout(self):
        self.assertEqual(self.request('/api/auth/session',owner=True)['statusCode'],200)
        self.assertEqual(self.request('/api/auth/logout','POST',{},owner=True)['statusCode'],200)
        self.assertEqual(self.request('/api/auth/session',owner=True)['statusCode'],401)
        self.f.login();row=self.f.store.get('sessions','session#'+digest(self.f.sid));row['ttl']=int(time.time())-1;self.f.store.put('sessions',row)
        self.assertEqual(self.request('/api/auth/session',owner=True)['statusCode'],401)
    def test_inquiry_persist_duplicate_private_update(self):
        data=self.f.contact();r=self.request('/api/contact','POST',data);self.assertEqual(r['statusCode'],201,r)
        self.assertEqual(self.request('/api/contact','POST',data)['statusCode'],200)
        self.assertEqual(self.request('/api/contact','POST',data|{'message':'changed message now'})['statusCode'],400)
        self.assertEqual(json.loads(self.request('/api/admin/inquiries',owner=True)['body'])['items'],[])
        rows=json.loads(self.request('/api/admin/inquiries',owner=True,q={'tests':'true'})['body'])['items'];self.assertEqual(len(rows),1)
        path='/api/admin/inquiries/'+data['id'];update={'revision':0,'status':'in progress','note':'Private note'}
        self.assertEqual(self.request(path,'PATCH',update,owner=True)['statusCode'],200)
        self.assertEqual(self.request(path,'PATCH',update,owner=True)['statusCode'],400)
        self.assertEqual(self.f.store.get('inquiries','inbox',data['id'])['notes'][0]['text'],'Private note')
        self.assertEqual(self.request(path,'DELETE',{},owner=True)['statusCode'],400)
        self.assertEqual(self.request(path,'DELETE',{'confirm':'DELETE '+data['id']},owner=True)['statusCode'],200)
    def test_malformed_and_honeypot(self):
        data=self.f.contact()
        for change in [{'topic':[]},{'source':[]},{'email':'bad'},{'message':'x'},{'website':'spam'},{'unknown':'x'}]:
            with self.subTest(change=change):
                with self.assertRaises(Invalid):inquiry(data|change,PAGES)
        self.assertEqual(self.request('/api/contact','POST',data|{'challenge':'bad'})['statusCode'],400)
    def test_form_store_failure_never_success(self):
        data=self.f.contact()
        with patch.object(self.f.store,'put',side_effect=RuntimeError('fixture storage failure')):
            r=self.request('/api/contact','POST',data)
        self.assertEqual(r['statusCode'],503);self.assertNotIn('stored',r['body'])
    def test_event_dedup_and_plausible_duration(self):
        view=observation();r=self.request('/api/events','POST',{'events':[view]});self.assertEqual(r['statusCode'],200,r);self.assertEqual(json.loads(r['body'])['accepted'],1)
        self.assertEqual(json.loads(self.request('/api/events','POST',{'events':[view]})['body'])['duplicates'],1)
        engagement=view|dict(id=uid(),name='engagement',value=15000,at=view['at']+15)
        self.assertEqual(self.request('/api/events','POST',{'events':[engagement]})['statusCode'],200)
        self.assertEqual(self.request('/api/events','POST',{'events':[engagement|{'id':uid()}]})['statusCode'],400)
        self.assertEqual(self.request('/api/events','POST',{'events':[engagement|{'id':uid(),'path':'/learn/'}]})['statusCode'],400)
        self.assertEqual(len(self.f.store.events(view['at']-1,int(time.time())+1)[0]),2)
    def test_events_require_page_and_consent(self):
        for change in [{'name':[]},{'target':[]},{'campaign':[]},{'browser':[]},{'path':[]},{'consent':False},{'at':0},{'referrer':'https://x.test/private?q=secret'},{'value':True}]:
            with self.subTest(change=change),self.assertRaises(Invalid):event(observation(**change),PAGES)
        self.assertEqual(self.request('/api/events','POST',{'events':[observation(name='engagement',value=10)]})['statusCode'],400)
        self.assertEqual(json.loads(self.request('/api/events','POST',{'events':[observation()]},owner=True)['body'])['excluded'],'owner')
    def test_query_bytes_are_bounded_and_note_growth_is_limited(self):
        now=int(time.time())
        for n in range(3):self.f.store.put('audit',dict(pk='byte-fixture',sk=str(n),text='x'*1000,ttl=now+1000))
        rows,partial=self.f.store.query('audit','byte-fixture',byte_limit=1500);self.assertEqual(len(rows),1);self.assertTrue(partial)
        data=self.f.contact();self.request('/api/contact','POST',data);row=self.f.store.get('inquiries','inbox',data['id']);row['notes']=[dict(at=now,text='x'*2000) for _ in range(10)];self.f.store.put('inquiries',row)
        r=self.request('/api/admin/inquiries/'+data['id'],'PATCH',{'revision':0,'note':'one more','status':'read'},owner=True);self.assertEqual(r['statusCode'],400)
    def test_rate_limits(self):
        for n in range(3):self.assertTrue(self.f.store.rate('test',3,60))
        self.assertFalse(self.f.store.rate('test',3,60))
    def test_empty_partial_and_periods(self):
        r=json.loads(self.request('/api/admin/insights',owner=True)['body']);self.assertIsNone(r['current']['average_active_ms']);self.assertEqual(r['current']['visitors'],0);self.assertTrue(r['partial']);self.assertTrue(r['previous_partial']);self.assertEqual(r['previous']['inquiries'],0)
        self.assertEqual(self.request('/api/admin/insights',owner=True,q={'from':'2020-01-01','to':'2025-01-01'})['statusCode'],400)
    def test_retention_and_exports(self):
        data=self.f.contact(name='=SUM(1,2)',test=False);self.request('/api/contact','POST',data)
        r=self.request('/api/admin/export',owner=True,q={'kind':'inquiries'});self.assertEqual(r['statusCode'],200);self.assertIn("'=SUM",json.loads(r['body'])['csv'])
        cfg={'collection':False,'analytics_days':1,'inquiry_days':1};self.assertEqual(self.request('/api/admin/settings','PUT',cfg,owner=True)['statusCode'],200)
        self.assertTrue(json.loads(self.request('/api/events','POST',{'events':[observation()]})['body'])['disabled'])
        row=self.f.store.get('inquiries','inbox',data['id']);row['at']-=172800;self.f.store.put('inquiries',row)
        self.assertEqual(json.loads(self.request('/api/admin/inquiries',owner=True)['body'])['items'],[])
        self.assertEqual(self.request('/api/admin/inquiries/'+data['id'],'PATCH',{},owner=True)['statusCode'],404)
        self.assertEqual(app.maintain()['removed'],1)
    def test_aggregation_unique_union_and_test_exclusion(self):
        a=observation(at=int(time.time())-86000);b=a|dict(id=uid(),page=uid(),at=int(time.time())-30,path='/learn/');t=observation(test=True)
        rows=[a,b,t,b|dict(id=uid(),name='engagement',value=10000),b|dict(id=uid(),name='contact_open')]
        result=aggregate(rows,PAGES,int(time.time()));self.assertEqual(result['visitors'],1);self.assertEqual(result['sessions'],1);self.assertEqual(result['pageviews'],2);self.assertEqual(result['average_active_ms'],10000);self.assertEqual(result['pages'][0]['next_pages'][0]['path'],'/learn/');self.assertEqual(len(result['trend']),2);self.assertEqual(result['journeys'][0]['rate'],100)
    def test_formula_prefixes(self):
        for value in ['=1',' +1','-1','@x','\tvalue']:self.assertTrue(spreadsheet(value).startswith("'"))
        self.assertEqual(spreadsheet('hello'),'hello')

if __name__=='__main__':unittest.main()
