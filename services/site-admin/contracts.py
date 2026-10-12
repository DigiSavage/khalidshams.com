"""Versioned, deliberately small public input contract. Never accept arbitrary properties."""
import re, time, json, uuid
from urllib.parse import urlsplit

EVENTS = {'pageview','engagement','scroll','lesson_start','lesson_complete','workflow_control','design_download','tool_use','contact_open','outbound_email','outbound_linkedin','performance','client_error'}
TARGETS = {'none','atlas','model-making','enterprise-studio','method','learn','availability','tool-definition','contact','lcp','script-error'}
TOPICS = {'architecture','cloud','ai','speaking','other'}
STATUSES = {'new','read','in progress','resolved','spam'}
CAMPAIGNS = {'linkedin','newsletter','direct','community'}

class Invalid(ValueError): pass

def exact(value, allowed):
    if not isinstance(value,dict) or set(value)-set(allowed): raise Invalid('Unexpected fields')

def uid(value):
    try:
        if str(uuid.UUID(value)) != value: raise ValueError()
        return value
    except (ValueError,TypeError,AttributeError): raise Invalid('Invalid identifier')

def text(value, minimum, maximum):
    if not isinstance(value,str) or not minimum <= len(value.strip()) <= maximum or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',value):
        raise Invalid('Invalid text length or control characters')
    return value.strip()

def path(value, pages):
    if not isinstance(value,str) or value not in pages: raise Invalid('Unknown public page')
    return value

def event(raw, pages, now=None):
    now = int(now or time.time())
    exact(raw, {'v','id','visitor','session','page','path','at','name','value','target','referrer','campaign','device','browser','consent','test'})
    if type(raw.get('v')) is not int or raw.get('v') != 1 or raw.get('consent') is not True: raise Invalid('Consent and supported version required')
    result = {k:uid(raw.get(k)) for k in ('id','visitor','session','page')}
    result['path'] = path(raw.get('path'),pages)
    at=raw.get('at');name=raw.get('name');value=raw.get('value',0)
    if type(at) is not int or not now-86400 <= at <= now+60: raise Invalid('Timestamp outside acceptance window')
    if not isinstance(name,str) or name not in EVENTS: raise Invalid('Unknown event')
    if type(value) is not int or not 0 <= value <= 120000: raise Invalid('Invalid measurement')
    if name=='engagement' and value > 15000: raise Invalid('Engagement update too large')
    if name=='scroll' and value not in {25,50,75,100}: raise Invalid('Unknown milestone')
    if name not in {'engagement','scroll','performance'} and value != 0: raise Invalid('Unexpected value')
    target=raw.get('target','none')
    if not isinstance(target,str) or target not in TARGETS: raise Invalid('Unknown interaction target')
    ref=raw.get('referrer','direct')
    if ref!='direct' and (not isinstance(ref,str) or len(ref)>253 or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',ref) or '.' not in ref): raise Invalid('Referrer must be a domain only')
    campaign=raw.get('campaign','direct')
    if not isinstance(campaign,str) or campaign not in CAMPAIGNS: raise Invalid('Unknown campaign')
    device=raw.get('device','unknown');browser=raw.get('browser','other')
    if not isinstance(device,str) or not isinstance(browser,str) or device not in {'phone','tablet','desktop','unknown'} or browser not in {'chromium','safari','firefox','other'}: raise Invalid('Unknown broad device')
    if type(raw.get('test',False)) is not bool: raise Invalid('Invalid test marker')
    return dict(result,v=1,at=at,name=name,value=value,target=target,referrer=ref,campaign=campaign,device=device,browser=browser,test=raw.get('test',False))

def inquiry(raw,pages):
    exact(raw,{'id','name','email','company','topic','message','source','website','challenge','test'})
    email=text(raw.get('email'),3,254)
    if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',email): raise Invalid('Enter a valid email address')
    if not isinstance(raw.get('topic'),str) or raw.get('topic') not in TOPICS: raise Invalid('Choose a topic')
    if raw.get('website',''): raise Invalid('Submission rejected')
    if type(raw.get('test',False)) is not bool:raise Invalid('Invalid test marker')
    return dict(id=uid(raw.get('id')),name=text(raw.get('name'),1,100),email=email,company=text(raw.get('company',''),0,120),topic=raw['topic'],message=text(raw.get('message'),10,5000),source=path(raw.get('source','/contact/'),pages),test=raw.get('test',False))

def spreadsheet(value):
    value=str(value)
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) or value.startswith(('\t','\r','\n')) else value

def body(event):
    raw=event.get('body') or ''
    if event.get('isBase64Encoded'):raise Invalid('Encoded bodies not supported')
    if len(raw.encode())>24000:raise Invalid('Payload too large')
    try:
        value=json.loads(raw)
    except (ValueError,TypeError):raise Invalid('Invalid JSON')
    if not isinstance(value,dict):raise Invalid('JSON object required')
    return value
