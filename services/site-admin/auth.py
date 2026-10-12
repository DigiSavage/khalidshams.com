"""Cognito authorization-code + S256 PKCE. Browser receives only an opaque HttpOnly session."""
import os,time,json,secrets,hashlib,base64,hmac
from http.cookies import SimpleCookie
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import boto3,jwt

class Unauthorized(Exception):pass

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
    def owner(self,claims):
        # Live directory checks mean disabling the user or removing owner membership
        # invalidates private access without waiting for JWT expiry.
        username=claims.get('username')
        if not username:raise Unauthorized()
        user=self.idp.admin_get_user(UserPoolId=self.pool,Username=username)
        attrs={a['Name']:a['Value'] for a in user.get('UserAttributes',[])}
        groups=self.idp.admin_list_groups_for_user(UserPoolId=self.pool,Username=username)['Groups']
        if not user.get('Enabled') or attrs.get('sub')!=claims['sub'] or 'owner' not in {g['GroupName'] for g in groups}:raise Unauthorized()
        if 'SOFTWARE_TOKEN_MFA' not in user.get('UserMFASettingList',[]):raise Unauthorized()
    def start(self):
        state,verifier,nonce,correlation=random(),random(),random(),random();now=int(time.time())
        self.store.put('sessions',dict(pk='login#'+digest(state),sk='0',verifier=verifier,nonce=nonce,correlation=digest(correlation),ttl=now+600),True)
        challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        url=self.domain+'/oauth2/authorize?'+urlencode(dict(response_type='code',client_id=self.client,redirect_uri=self.origin+'/api/auth/callback',scope='openid email site-admin/owner',state=state,nonce=nonce,code_challenge=challenge,code_challenge_method='S256'))
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
        self.owner(access)
        sid=random();expires=min(int(access['exp']),int(time.time())+900)
        self.store.put('sessions',dict(pk='session#'+digest(sid),sk='0',access=tokens['access_token'],csrf=random(),sub=access['sub'],ttl=expires),True)
        return cookie('session',sid,max(0,expires-int(time.time())))
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
