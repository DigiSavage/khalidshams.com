"""Same-origin site API. Public inputs are untrusted; all owner operations reauthorize."""
import os,json,time,hmac,hashlib,secrets,csv,io
from pathlib import Path
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
import boto3
from botocore.exceptions import ClientError
from contracts import Invalid,event as validate_event,inquiry,body,text,uid,STATUSES,spreadsheet
from auth import Auth,Unauthorized,cookies,cookie,digest
from storage import Store
from metrics import aggregate

STORE=None;AUTH=None;SALT=None
PAGES=json.loads((Path(__file__).parent/'pages.json').read_text()) if (Path(__file__).parent/'pages.json').exists() else {}
DEFAULTS={'collection':True,'analytics_days':90,'inquiry_days':365,'started':None}

def response(status,data=None,headers=None,cookies_=None):
    result={'statusCode':status,'headers':{'Content-Type':'application/json','Cache-Control':'no-store, private, max-age=0','Pragma':'no-cache','Vary':'Cookie, Origin','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',**(headers or {})},'body':json.dumps(data,default=lambda v:int(v) if isinstance(v,Decimal) else str(v)) if data is not None else ''}
    if cookies_:result['multiValueHeaders']={'Set-Cookie':cookies_}
    return result

def redirect(url,jar=None):return response(303,headers={'Location':url},cookies_=jar)
def settings():return {**DEFAULTS,**(STORE.get('sessions','settings') or {})}
def health(name,count=1):
    now=int(time.time());day=datetime.fromtimestamp(now,timezone.utc).date().isoformat()
    STORE.tables['audit'].update_item(Key={'pk':'health','sk':day},UpdateExpression='SET #n=if_not_exists(#n,:zero)+:one, #ttl=:ttl',ExpressionAttributeNames={'#n':name,'#ttl':'ttl'},ExpressionAttributeValues={':zero':0,':one':count,':ttl':now+90*86400})
def secret():
    global SALT
    if SALT is None:SALT=boto3.client('secretsmanager').get_secret_value(SecretId=os.environ['RATE_SECRET'])['SecretString']
    return SALT
def source_key(e):
    ip=e.get('headers',{}).get('cloudfront-viewer-address','unknown:0').rsplit(':',1)[0]
    # Never store the raw address; ephemeral pseudonymous abuse counters are separate from analytics.
    return hmac.new(secret().encode(),(str(int(time.time())//86400)+':'+ip).encode(),hashlib.sha256).hexdigest()
def limited(e,kind,maximum,period):
    if not STORE.rate(kind+source_key(e),maximum,period):raise Invalid('Too many requests. Please try later.')
def dates(q):
    tz=ZoneInfo('America/Phoenix');today=datetime.now(tz).date()
    try:
        start=datetime.strptime(q.get('from',str(today-timedelta(days=6))),'%Y-%m-%d').replace(tzinfo=tz)
        end=datetime.strptime(q.get('to',str(today)),'%Y-%m-%d').replace(tzinfo=tz)+timedelta(days=1)
    except ValueError:raise Invalid('Use YYYY-MM-DD dates')
    if not 0 < (end-start).days <= 90 or end.date()>today+timedelta(days=1):raise Invalid('Choose up to 90 days ending no later than today')
    return int(start.timestamp()),int(end.timestamp())
def inquiries(cfg,include_test=False):
    rows,partial=STORE.query('inquiries','inbox',2000)
    rows=[r for r in rows if r['at']>=int(time.time())-int(cfg['inquiry_days'])*86400 and (include_test or not r.get('test'))]
    return sorted(rows,key=lambda r:r['at'],reverse=True),partial

def handler(e,context=None):
    global STORE,AUTH
    if STORE is None:STORE=Store()
    if AUTH is None:AUTH=Auth(STORE)
    if e.get('source')=='aws.events' and not e.get('httpMethod'):return maintain()
    e['headers']={k.lower():v for k,v in (e.get('headers') or {}).items()}
    p=e.get('path','');method=e.get('httpMethod','GET');q=e.get('queryStringParameters') or {};now=int(time.time());origin=os.environ['PUBLIC_ORIGIN']
    try:
        if not hmac.compare_digest(e['headers'].get('x-site-origin',''),secret()):return response(403,{'error':'Site origin required'})
        if method not in {'GET','POST','PATCH','PUT','DELETE'}:return response(405,{'error':'Method not allowed'})
        if method!='GET' and e['headers'].get('origin')!=origin:return response(403,{'error':'Same-origin request required'})
        if method=='GET' and p=='/api/auth/start':
            limited(e,'login',20,3600);url,c=AUTH.start();return redirect(url,[c])
        if method=='GET' and p=='/api/auth/callback':
            return redirect(origin+'/admin/',[AUTH.callback(e),cookie('login','',0)])
        cfg=settings()
        if p=='/api/config' and method=='GET':return response(200,{'available':True,'collection':cfg['collection'],'version':1})
        if p=='/api/contact/challenge' and method=='GET':
            limited(e,'challenge',30,3600);token=secrets.token_urlsafe(32)
            STORE.put('sessions',dict(pk='challenge#'+digest(token),sk='0',source=source_key(e),at=now,ttl=now+1800),True)
            return response(200,{'challenge':token})
        if p=='/api/contact' and method=='POST':
            limited(e,'contact',6,3600);raw=body(e);item=inquiry(raw,PAGES)
            # A successful retry must match exactly, not reveal another submission.
            fingerprint=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
            existing=STORE.get('inquiries','inbox',item['id'])
            if existing:
                if not hmac.compare_digest(existing['fingerprint'],fingerprint):raise Invalid('Submission identifier already used')
                return response(200,{'stored':True,'id':item['id'],'duplicate':True})
            challenge=STORE.get('sessions','challenge#'+digest(str(raw.get('challenge',''))))
            if not challenge or challenge['source']!=source_key(e) or now-challenge['at']<2:raise Invalid('Refresh the form and try again')
            row=dict(item,pk='inbox',sk=item['id'],at=now,status='new',notes=[],history=[dict(at=now,status='new')],revision=0,fingerprint=fingerprint,ttl=now+cfg['inquiry_days']*86400)
            if not STORE.put('inquiries',row,True):raise Invalid('Submission is being stored. Retry shortly.')
            STORE.delete('sessions',challenge['pk']);health('contact_accepted');return response(201,{'stored':True,'id':item['id']})
        if p=='/api/events' and method=='POST':
            limited(e,'events',600,3600)
            if not cfg['collection']:return response(200,{'accepted':0,'disabled':True})
            if cookies(e).get('__Host-ks-session'):return response(200,{'accepted':0,'excluded':'owner'})
            raw=body(e)
            if set(raw)!={'events'} or not isinstance(raw['events'],list) or not 1<=len(raw['events'])<=12:raise Invalid('Invalid event batch')
            user_agent=e['headers'].get('user-agent','').lower()
            if any(x in user_agent for x in ('bot','spider','crawler')):return response(200,{'accepted':0,'excluded':'automated user agent'})
            rows=[validate_event(r,PAGES,now) for r in raw['events']];accepted=0
            for row in sorted(rows,key=lambda r:r['name']!='pageview'):
                stored=STORE.save_event(row,cfg['analytics_days']);accepted+=stored
                if stored:health('events_accepted')
            if accepted:
                if not cfg['started']:
                    STORE.tables['sessions'].update_item(Key={'pk':'settings','sk':'0'},UpdateExpression='SET started=if_not_exists(started,:at), #ttl=:ttl',ExpressionAttributeNames={'#ttl':'ttl'},ExpressionAttributeValues={':at':now,':ttl':now+315360000})
            return response(200,{'accepted':accepted,'duplicates':len(rows)-accepted})
        # All remaining routes are private, including GET, export and unknown operations.
        session=AUTH.session(e,mutation=method!='GET');owner=session['sub']
        if p=='/api/auth/session' and method=='GET':return response(200,{'owner':True,'csrf':session['csrf'],'expires':session['ttl']})
        if p=='/api/auth/logout' and method=='POST':
            url,c=AUTH.logout(e);return response(200,{'logout':url},cookies_=[c])
        if p=='/api/admin/settings':
            if method=='GET':return response(200,{k:cfg[k] for k in DEFAULTS})
            if method=='PUT':
                raw=body(e)
                if set(raw)!={'collection','analytics_days','inquiry_days'} or type(raw['collection']) is not bool or type(raw['analytics_days']) is not int or type(raw['inquiry_days']) is not int or not 1<=raw['analytics_days']<=90 or not 1<=raw['inquiry_days']<=730:raise Invalid('Invalid settings')
                STORE.put('sessions',dict(raw,pk='settings',sk='0',started=cfg['started'],ttl=now+315360000));STORE.audit('settings.updated','collection and retention',owner);return response(200,raw)
        if p=='/api/admin/insights' and method=='GET':
            start,end=dates(q);span=end-start;end=min(end,now+1);floor=now-cfg['analytics_days']*86400
            rows,partial=STORE.events(max(start,floor),end)
            previous_start=start-span;previous_end=end-span;previous,previous_partial=STORE.events(max(previous_start,floor),previous_end)
            partial=partial or start<floor or not cfg['started'] or start<cfg['started']
            previous_partial=previous_partial or previous_start<floor or not cfg['started'] or previous_start<cfg['started']
            inbox,ipart=inquiries(cfg)
            current=aggregate(rows,PAGES,now);previous_stats=aggregate(previous,PAGES,now)
            previous_stats['inquiries']=sum(previous_start<=r['at']<previous_end for r in inbox)
            fresh,_=STORE.events(now-300,now+1,2000);current['active_last_5_minutes']=aggregate(fresh,PAGES,now)['active_last_5_minutes']
            current.update(inquiries=sum(start<=r['at']<end for r in inbox),recent_inquiries=[{k:r[k] for k in ('id','name','topic','at','status')} for r in inbox[:5]])
            healthrows,hpart=STORE.query('audit','health',100)
            return response(200,dict(current=current,previous=previous_stats,partial=partial or ipart or hpart,previous_partial=previous_partial,from_epoch=start,to_epoch=end,collection_start=cfg['started'],generated=now,health=healthrows,retention=cfg['analytics_days'],coverage_note='Observed consented traffic only. Entries and exits are the first and last observed page inside the selected period. Journeys show same-session association, not causation.'))
        if p=='/api/admin/inquiries' and method=='GET':
            rows,partial=inquiries(cfg,q.get('tests')=='true');term=q.get('q','')[:100].casefold();status=q.get('status','')
            rows=[r for r in rows if (not status or r['status']==status) and (not term or term in (' '.join(str(r[k]) for k in ('name','email','company','message','topic'))).casefold())]
            return response(200,{'items':[{k:v for k,v in r.items() if k not in {'pk','sk','fingerprint'}} for r in rows],'partial':partial})
        if p.startswith('/api/admin/inquiries/'):
            id_=uid(p.rsplit('/',1)[-1]);row=STORE.get('inquiries','inbox',id_)
            if not row or row['at']<now-cfg['inquiry_days']*86400:return response(404,{'error':'Inquiry not found'})
            raw=body(e)
            if method=='DELETE':
                if raw.get('confirm')!='DELETE '+id_:raise Invalid('Explicit confirmation required')
                STORE.delete('inquiries','inbox',id_);STORE.audit('inquiry.deleted',id_,owner);return response(200,{'deleted':True})
            if method=='PATCH':
                if type(raw.get('revision')) is not int or set(raw)-{'status','note','revision'} or not isinstance(raw.get('status',row['status']),str) or raw.get('status',row['status']) not in STATUSES or raw.get('revision')!=row['revision']:raise Invalid('Reload this inquiry before editing')
                status=raw.get('status',row['status']);note=text(raw.get('note',''),0,2000)
                if len(row['history'])>=100 or len(row['notes'])>=100:raise Invalid('History limit reached')
                if status!=row['status']:row['history'].append(dict(at=now,status=status))
                if note:row['notes'].append(dict(at=now,text=note))
                rev=row['revision'];row['revision']=rev+1;row['status']=status
                STORE.tables['inquiries'].put_item(Item=row,ConditionExpression='revision=:revision',ExpressionAttributeValues={':revision':rev});STORE.audit('inquiry.updated',id_,owner);return response(200,{'updated':True})
        if p=='/api/admin/export' and method=='GET':
            kind=q.get('kind');start,end=dates(q);buffer=io.StringIO();writer=csv.writer(buffer)
            if kind=='analytics':
                rows,partial=STORE.events(max(start,now-cfg['analytics_days']*86400),end);data=aggregate(rows,PAGES,now)['pages'];columns=['path','title','pageviews','visitors','entrances','exits','engaged_ms','average_active_ms']
            elif kind=='inquiries':
                data,partial=inquiries(cfg);data=[r for r in data if start<=r['at']<end];columns=['id','at','name','email','company','topic','message','source','status']
            else:raise Invalid('Choose an export kind')
            if partial:return response(422,{'error':'Too much data for a complete export. Narrow the date range.'})
            writer.writerow(columns)
            for r in data:writer.writerow([spreadsheet(r.get(c,'')) for c in columns])
            STORE.audit('export.'+kind,f'{start}:{end}',owner);return response(200,{'filename':'shams-'+kind+'.csv','csv':buffer.getvalue()})
        if p=='/api/admin/analytics' and method=='DELETE':
            raw=body(e);start,end=dates(raw)
            if raw.get('confirm')!=f'DELETE ANALYTICS {raw.get("from")} {raw.get("to")}':raise Invalid('Explicit confirmation required')
            rows,partial=STORE.events(start,end,2000)
            with STORE.tables['events'].batch_writer() as batch:
                for r in rows:batch.delete_item(Key={'pk':r['pk'],'sk':r['sk']})
            STORE.audit('analytics.deleted',f'{start}:{end}',owner);return response(200,{'deleted':len(rows),'more':partial})
        return response(404,{'error':'Not found'})
    except Unauthorized:return response(401,{'error':'Owner sign-in required. Your session may have expired.'})
    except Invalid as ex:
        try:
            if p=='/api/events':
                health('events_rejected_batches')
                count=len(raw.get('events',[])) if isinstance(locals().get('raw'),dict) and isinstance(raw.get('events'),list) else 0
                if count:health('events_rejected',min(12,count)-locals().get('accepted',0))
            if p=='/api/contact':health('contact_rejected')
        except Exception:pass
        return response(400,{'error':str(ex)})
    except Exception as ex:
        # Do not log request bodies, tokens, headers, email addresses or raw errors.
        print(json.dumps({'failure_type':type(ex).__name__,'operation':p.split('/')[2:4]}))
        try:
            if p=='/api/contact':health('contact_failures')
        except Exception:pass
        return response(503,{'error':'Temporarily unavailable. Please retry; your work has not been confirmed.'})

def maintain():
    cfg=settings();now=int(time.time());removed=0
    for name,days in [('events',cfg['analytics_days']),('inquiries',cfg['inquiry_days'])]:
        cursor=STORE.get('sessions','maintenance#'+name);start=cursor.get('cursor') if cursor else None
        page=STORE.tables[name].scan(Limit=500,**({'ExclusiveStartKey':start} if start else {}))
        for row in page['Items']:
            expiry=int(row['at'])+days*86400
            if expiry<=now:STORE.delete(name,row['pk'],row['sk']);removed+=1
            elif expiry<row['ttl']:
                STORE.tables[name].update_item(Key={'pk':row['pk'],'sk':row['sk']},UpdateExpression='SET #ttl=:ttl',ExpressionAttributeNames={'#ttl':'ttl'},ExpressionAttributeValues={':ttl':expiry})
        STORE.put('sessions',dict(pk='maintenance#'+name,sk='0',cursor=page.get('LastEvaluatedKey'),ttl=now+86400))
    return {'removed':removed}
