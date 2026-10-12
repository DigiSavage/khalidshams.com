"""Cognito authorization-code + S256 PKCE. Browser receives only an opaque HttpOnly session."""
import os,time,json,secrets,hashlib,base64,hmac
from http.cookies import SimpleCookie
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import boto3,jwt

class Unauthorized(Exception):pass
class EnrollmentRequired(Exception):
    def __init__(self,jar):self.jar=jar

def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def random():return secrets.token_urlsafe(32)
def cookie(name,value,seconds):return f'__Host-ks-{name}={value}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age={seconds}'
def cookies(event):
    jar=SimpleCookie()
    try:jar.load(event.get('headers',{}).get('cookie',''))
    except Exception:return {}
    return {k:v.value for k,v in jar.items()}

class Auth:
    def __init__(self,store):
        self.store=store;self.pool=os.environ['USER_POOL_ID'];self.client=os.environ['CLIENT_ID'];self.origin=os.environ['PUBLIC_ORIGIN'];self.domain=os.environ['AUTH_DOMAIN']
        self.issuer=f'https://cognito-idp.{os.environ["AWS_REGION"]}.amazonaws.com/{self.pool}'
        self.jwks=jwt.PyJWKClient(self.issuer+'/.well-known/jwks.json',cache_keys=True,lifespan=300,timeout=5)
        self.idp=boto3.client('cognito-idp')
    def validate(self,token,kind,nonce=None):
        try:
            key=self.jwks.get_signing_key_from_jwt(token).key
            claims=jwt.decode(token,key,algorithms=['RS256'],issuer=self.issuer,audience=self.client if kind=='id' else None,options={'verify_aud':kind=='id','require':['exp','iat','sub','iss','token_use']},leeway=5)
            if claims['token_use']!=kind:raise Unauthorized()
            if kind=='access' and (claims.get('client_id')!=self.client or 'site-admin/owner' not in claims.get('scope','').split() or 'owner' not in claims.get('cognito:groups',[])):raise Unauthorized()
            if kind=='id' and (not nonce or not hmac.compare_digest(str(claims.get('nonce','')),nonce)):raise Unauthorized()
            return claims
        except (jwt.PyJWTError,ValueError,TypeError):raise Unauthorized()
    def owner(self,claims,require_mfa=True):
        # Live directory checks mean disabling the user or removing owner membership
        # invalidates private access without waiting for JWT expiry.
        username=claims.get('username')
        if not username:raise Unauthorized()
        user=self.idp.admin_get_user(UserPoolId=self.pool,Username=username)
        attrs={a['Name']:a['Value'] for a in user.get('UserAttributes',[])}
        groups=self.idp.admin_list_groups_for_user(UserPoolId=self.pool,Username=username)['Groups']
        if not user.get('Enabled') or attrs.get('sub')!=claims['sub'] or 'owner' not in {g['GroupName'] for g in groups}:raise Unauthorized()
        enrolled='SOFTWARE_TOKEN_MFA' in user.get('UserMFASettingList',[])
        if require_mfa and not enrolled:raise Unauthorized()
        return enrolled
    def start(self):
        state,verifier,nonce,correlation=random(),random(),random(),random();now=int(time.time())
        self.store.put('sessions',dict(pk='login#'+digest(state),sk='0',verifier=verifier,nonce=nonce,correlation=digest(correlation),ttl=now+600),True)
        challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        url=self.domain+'/oauth2/authorize?'+urlencode(dict(response_type='code',client_id=self.client,redirect_uri=self.origin+'/api/auth/callback',scope='openid email site-admin/owner aws.cognito.signin.user.admin',state=state,nonce=nonce,code_challenge=challenge,code_challenge_method='S256'))
        return url,cookie('login',correlation,600)
    def callback(self,event):
        q=event.get('queryStringParameters') or {};state=q.get('state','');code=q.get('code','')
        if len(state)>128 or not code or len(code)>4096:raise Unauthorized()
        row=self.store.consume('login#'+digest(state));correlation=cookies(event).get('__Host-ks-login','')
        if not row or not correlation or not hmac.compare_digest(row['correlation'],digest(correlation)):raise Unauthorized()
        payload=urlencode(dict(grant_type='authorization_code',client_id=self.client,code=code,redirect_uri=self.origin+'/api/auth/callback',code_verifier=row['verifier'])).encode()
        with urlopen(Request(self.domain+'/oauth2/token',data=payload,headers={'Content-Type':'application/x-www-form-urlencoded'}),timeout=8) as response:tokens=json.load(response)
        identity=self.validate(tokens['id_token'],'id',row['nonce']);access=self.validate(tokens['access_token'],'access')
        if identity['sub']!=access['sub']:raise Unauthorized()
        if not self.owner(access,require_mfa=False):
            if 'aws.cognito.signin.user.admin' not in access.get('scope','').split():raise Unauthorized()
            sid=random();expires=min(int(access['exp']),int(time.time())+600)
            self.store.put('sessions',dict(pk='enrollment#'+digest(sid),sk='0',access=tokens['access_token'],csrf=random(),sub=access['sub'],ttl=expires),True)
            raise EnrollmentRequired(cookie('enrollment',sid,max(0,expires-int(time.time()))))
        return self.issue_session(tokens['access_token'],access)
    def issue_session(self,token,claims):
        sid=random();expires=min(int(claims['exp']),int(time.time())+900)
        self.store.put('sessions',dict(pk='session#'+digest(sid),sk='0',access=token,csrf=random(),sub=claims['sub'],ttl=expires),True)
        return cookie('session',sid,max(0,expires-int(time.time())))
    def enrollment(self,event,mutation=False):
        sid=cookies(event).get('__Host-ks-enrollment','')
        row=self.store.get('sessions','enrollment#'+digest(sid)) if sid else None
        if not row:raise Unauthorized()
        claims=self.validate(row['access'],'access')
        if claims['sub']!=row['sub'] or self.owner(claims,require_mfa=False):raise Unauthorized()
        if mutation and not hmac.compare_digest(event.get('headers',{}).get('x-csrf-token',''),row['csrf']):raise Unauthorized()
        return row,claims
    def begin_enrollment(self,event):
        row,_=self.enrollment(event,True)
        if not self.store.rate(row['pk']+'#begin',3,600):raise Unauthorized()
        result=self.idp.associate_software_token(AccessToken=row['access'])
        # Access-token enrollment does not require Cognito's challenge Session.
        row['setup_started']=True;self.store.put('sessions',row)
        return result['SecretCode']
    def finish_enrollment(self,event,code):
        row,claims=self.enrollment(event,True)
        if not isinstance(code,str) or len(code)!=6 or not code.isascii() or not code.isdigit() or not row.get('setup_started'):raise Unauthorized()
        if not self.store.rate(row['pk']+'#verify',5,600):raise Unauthorized()
        result=self.idp.verify_software_token(AccessToken=row['access'],UserCode=code)
        if result.get('Status')!='SUCCESS':raise Unauthorized()
        self.idp.set_user_mfa_preference(AccessToken=row['access'],SoftwareTokenMfaSettings={'Enabled':True,'PreferredMfa':True})
        self.owner(claims)
        if not self.store.consume(row['pk']):raise Unauthorized()
        return self.issue_session(row['access'],claims)
    def session(self,event,mutation=False):
        sid=cookies(event).get('__Host-ks-session','');row=self.store.get('sessions','session#'+digest(sid)) if sid else None
        if not row:raise Unauthorized()
        claims=self.validate(row['access'],'access');self.owner(claims)
        if claims['sub']!=row['sub']:raise Unauthorized()
        if mutation and not hmac.compare_digest(event.get('headers',{}).get('x-csrf-token',''),row['csrf']):raise Unauthorized()
        return row
    def logout(self,event):
        sid=cookies(event).get('__Host-ks-session','');self.store.delete('sessions','session#'+digest(sid))
        return self.domain+'/logout?'+urlencode(dict(client_id=self.client,logout_uri=self.origin+'/login/')),cookie('session','',0)
