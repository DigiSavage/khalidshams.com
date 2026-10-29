"""Aggregate observed events. Counts never claim to represent exact people."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
TZ=ZoneInfo('America/Phoenix')

def aggregate(events,pages,now):
    rows=sorted((e for e in events if not e.get('test')),key=lambda e:(e['at'],e['id']))
    views=[e for e in rows if e['name']=='pageview']
    pageids={e['page'] for e in views}
    duration=defaultdict(int);scroll=defaultdict(set);by_session=defaultdict(list)
    for e in rows:
        if e['name']=='engagement' and e['page'] in pageids:duration[e['page']]+=e['value']
        if e['name']=='scroll':scroll[e['path']].add((e['page'],e['value']))
    for e in views:by_session[e['session']].append(e)
    entrances=Counter();exits=Counter();transitions=Counter()
    for session in by_session.values():
        entrances[session[0]['path']]+=1;exits[session[-1]['path']]+=1
        for a,b in zip(session,session[1:]):transitions[(a['path'],b['path'])]+=1
    table=[]
    for p in sorted({e['path'] for e in views}):
        v=[e for e in views if e['path']==p];ids={e['page'] for e in v}
        measured=ids & duration.keys();active=sum(duration[x] for x in measured)
        # The event contract stores whole seconds; DynamoDB reads them as Decimal.
        page_days=Counter(datetime.fromtimestamp(int(e['at']),TZ).date().isoformat() for e in v)
        table.append(dict(trend=dict(sorted(page_days.items())),path=p,title=pages.get(p,p),pageviews=len(v),visitors=len({e['visitor'] for e in v}),entrances=entrances[p],exits=exits[p],engaged_ms=active if measured else None,average_active_ms=round(active/len(measured)) if measured else None,measured_pages=len(measured),scroll={str(n):sum(x[1]==n for x in scroll[p]) for n in (25,50,75,100)},sources=dict(Counter(e['referrer'] for e in v)),devices=dict(Counter(e['device'] for e in v)),events=dict(Counter(e['name'] for e in rows if e['path']==p and e['name'] not in {'pageview','engagement'})),next_pages=[{'path':b,'count':n} for (a,b),n in transitions.items() if a==p]))
    days=defaultdict(list)
    for e in views:days[datetime.fromtimestamp(int(e['at']),TZ).date().isoformat()].append(e)
    funnel=[]
    for label,match in [('Home',lambda p:p=='/'),('Learn',lambda p:p.startswith('/learn/') and '/atlas/' not in p),('Atlas',lambda p:'/atlas/' in p),('Method',lambda p:p.startswith('/method/')),('Architect',lambda p:p=='/architect/'),('Enterprise Studio',lambda p:'agent-studio' in p),('Contact',lambda p:p=='/contact/')]:
        entered={e['session'] for e in views if match(e['path'])}
        contacted={s for s in entered if any(e['name']=='contact_open' and e['session']==s for e in rows)}
        funnel.append(dict(section=label,sessions=len(entered),contact_sessions=len(contacted),rate=round(len(contacted)/len(entered)*100,1) if entered else None))
    perf=[e['value'] for e in rows if e['name']=='performance' and e['target']=='lcp']
    return dict(pageviews=len(views),visitors=len({e['visitor'] for e in views}),sessions=len(by_session),engaged_ms=sum(duration.values()) if duration else None,average_active_ms=round(sum(duration.values())/len(duration)) if duration else None,measured_pages=len(duration),active_last_5_minutes=len({e['session'] for e in rows if e['name']=='engagement' and e['value']>0 and e['at']>=now-300}),pages=table,trend=[dict(date=d,pageviews=len(v),visitors=len({e['visitor'] for e in v})) for d,v in sorted(days.items())],sources=dict(Counter(e['referrer'] for e in views)),events=dict(Counter(e['name'] for e in rows)),journeys=funnel,lcp_ms=round(sum(perf)/len(perf)) if perf else None,last_event=max((e['at'] for e in rows),default=None))
