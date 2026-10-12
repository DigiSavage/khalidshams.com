/* Consent-based observations. Never reads form fields, search strings or URL fragments. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else{root.KSMeasurement=api;api.start();}})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 class Engagement {
  constructor(now){this.last=now;this.activity=now;this.visible=true;this.pending=0;}
  tick(now){const until=Math.min(now,this.activity+30000);if(this.visible)this.pending+=Math.max(0,Math.min(15000,until-this.last));this.last=now;}
  touch(now){this.tick(now);this.activity=now;}
  visibility(visible,now){this.tick(now);this.visible=visible;this.last=now;if(visible)this.activity=now;}
  drain(){const n=Math.min(15000,Math.floor(this.pending));this.pending-=n;return n;}
 }
 const campaigns=new Set(['linkedin','newsletter','community']);
 function safeReferrer(raw){try{const u=new URL(raw);return /^https?:$/.test(u.protocol)?u.hostname.toLowerCase():'direct';}catch{return 'direct';}}
 function start(){
  if(typeof document==='undefined')return;
  if(/^\/(admin|login)(\/|$)/.test(location.pathname)){document.querySelectorAll('[data-measurement-settings]').forEach(b=>b.hidden=true);return;}
  const markedTest=new URLSearchParams(location.search).get('ks-test')==='1';
  if(!['khalidshams.com','www.khalidshams.com'].includes(location.hostname)&&!markedTest)return;
  let serviceReady=false,consent=null,enabled=false,visitor,session,page,clock,timer,busy=false,queue=[],scrolls=new Set(),completed=false,lcp=0,observer;
  const read=k=>{try{return localStorage.getItem(k);}catch{return null;}};
  const write=(k,v)=>{try{v===null?localStorage.removeItem(k):localStorage.setItem(k,v);}catch{}};
  const uuid=()=>crypto.randomUUID();
  const status=document.createElement('p');status.className='measurement-status';status.setAttribute('role','status');
  function excluded(){return navigator.globalPrivacyControl===true||read('ks-owner-exclude')==='1'||(enabled&&preference()!=='yes');}
  function preference(){try{const p=JSON.parse(read('ks-measurement-consent'));return p&&p.expires>Date.now()?p.value:null;}catch{return null;}}
  function sessionId(){let saved;try{saved=JSON.parse(read('ks-measurement-session'));}catch{}
   if(!saved||Date.now()-saved.last>1800000)saved={id:uuid()};saved.last=Date.now();write('ks-measurement-session',JSON.stringify(saved));return saved.id;}
  function emit(name,value=0,target='none'){
   if(!enabled||consent!=='yes'||excluded()||queue.length>=120)return;
   const nextSession=sessionId();if(session&&session!==nextSession&&name!=='pageview'){session=nextSession;page=uuid();scrolls=new Set();completed=false;emit('pageview');}session=nextSession;const ua=navigator.userAgent;
   queue.push({v:1,id:uuid(),visitor,session,page,path:location.pathname,at:Math.floor(Date.now()/1000),name,value,target,referrer:safeReferrer(document.referrer),campaign:campaigns.has(new URLSearchParams(location.search).get('utm_source'))?new URLSearchParams(location.search).get('utm_source'):'direct',device:matchMedia('(max-width:600px)').matches?'phone':matchMedia('(max-width:1100px)').matches?'tablet':'desktop',browser:/Firefox/.test(ua)?'firefox':/Chrome|Chromium|Edg/.test(ua)?'chromium':/Safari/.test(ua)?'safari':'other',consent:true,test:markedTest});
  }
  async function flush(beacon=false){
   if(!queue.length||busy||!enabled||excluded())return;
   const batch=queue.slice(0,12),payload=JSON.stringify({events:batch});
   if(beacon&&navigator.sendBeacon){navigator.sendBeacon('/api/events',new Blob([payload],{type:'text/plain'}));return;}
   busy=true;
   try{const r=await fetch('/api/events',{method:'POST',body:payload,headers:{'Content-Type':'application/json'},credentials:'same-origin',keepalive:true});if(r.ok)queue.splice(0,batch.length);else if(r.status===400)queue.splice(0,batch.length);}catch{}finally{busy=false;}
  }
  function tick(){if(!clock||!enabled)return;if(excluded()){disable();return;}clock.tick(performance.now());const value=clock.drain();if(value>0)emit('engagement',value);flush();}
  function beginPage(){page=uuid();clock=new Engagement(performance.now());clock.visible=!document.hidden;scrolls=new Set();completed=false;emit('pageview');flush();}
  function enable(){if(!serviceReady||enabled||excluded())return;visitor=read('ks-measurement-visitor');if(!visitor){visitor=uuid();write('ks-measurement-visitor',visitor);}enabled=true;beginPage();timer=setInterval(tick,15000);
   try{observer=new PerformanceObserver(list=>{for(const e of list.getEntries())lcp=Math.min(120000,Math.round(e.startTime));});observer.observe({type:'largest-contentful-paint',buffered:true});}catch{}
  }
  function disable(){enabled=false;queue=[];clearInterval(timer);observer?.disconnect();['ks-measurement-visitor','ks-measurement-session'].forEach(k=>write(k,null));}
  function choose(value){consent=value;write('ks-measurement-consent',JSON.stringify({value,expires:Date.now()+90*86400000}));if(value==='yes')enable();else disable();document.querySelector('.measurement-choice')?.remove();status.textContent=value==='yes'?'Optional site measurements enabled.':'Optional site measurements are off.';}
  function choices(){if(!serviceReady){status.textContent='Optional measurements are currently unavailable and are off.';document.body.append(status);return;}document.querySelector('.measurement-choice')?.remove();const box=document.createElement('aside');box.className='measurement-choice';box.setAttribute('aria-label','Optional site measurements');const p=document.createElement('p');p.textContent='May I measure how this site is used? With your permission, I collect page visits and active time to improve the free lessons. No form contents or search terms.';box.append(p);
   for(const [label,value] of [['Allow measurements','yes'],['Keep measurements off','no']]){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=()=>choose(value);box.append(b);}const a=document.createElement('a');a.href='/privacy/';a.textContent='Privacy and measurement details';box.append(a);document.body.append(box);}
  addEventListener('storage',e=>{if(!['ks-measurement-consent','ks-owner-exclude'].includes(e.key))return;if(excluded()||preference()!=='yes'){consent=preference();disable();}else{consent='yes';enable();}});
  document.querySelectorAll('[data-measurement-settings]').forEach(b=>b.addEventListener('click',choices));
  ['pointerdown','keydown','touchstart','scroll'].forEach(name=>addEventListener(name,()=>{if(enabled)clock.touch(performance.now());},{passive:true}));
  document.addEventListener('visibilitychange',()=>{if(!enabled)return;clock.visibility(!document.hidden,performance.now());const n=clock.drain();if(n)emit('engagement',n);if(document.hidden){if(lcp){emit('performance',lcp,'lcp');lcp=0;}flush(true);}});
  addEventListener('pagehide',()=>{if(enabled){clock.visibility(false,performance.now());const n=clock.drain();if(n)emit('engagement',n);flush(true);}});
  addEventListener('pageshow',e=>{if(e.persisted&&enabled){flush();beginPage();}});
  addEventListener('scroll',()=>{if(!enabled)return;const range=document.documentElement.scrollHeight-innerHeight;const percent=range>0?Math.min(100,Math.round(scrollY/range*100)):100;for(const n of [25,50,75,100])if(percent>=n&&!scrolls.has(n)){scrolls.add(n);emit('scroll',n);}},{passive:true});
  document.addEventListener('click',e=>{if(e.target.closest('a[href^="/contact/"]')){try{sessionStorage.setItem('ks-contact-source',location.pathname);}catch{}}if(!enabled)return;const el=e.target.closest('a,button');if(!el)return;
   if(el.id==='es-download')emit('design_download',0,'enterprise-studio');
   else if(el.id==='atl-follow')emit('lesson_start',0,location.pathname.includes('how-models')?'model-making':'atlas');
   else if(el.matches('[id^="es-"], [id^="atl-"]'))emit('workflow_control',0,el.id.startsWith('es-')?'enterprise-studio':'atlas');
   else if(el.matches('.pb-tool-trigger'))emit('tool_use',0,'tool-definition');
   else if(el.getAttribute('href')?.startsWith('mailto:'))emit('outbound_email');
   else if(el.getAttribute('href')?.includes('linkedin.com'))emit('outbound_linkedin');
   else if(el.getAttribute('href')?.startsWith('/contact/'))emit('contact_open',0,'contact');
   // Read the lesson's public terminal state only, never its inspector or user inputs.
   setTimeout(()=>{if(completed)return;const st=window.__atlas?.state?.();if(st&&st.steps&&st.idx===st.steps.length-1){completed=true;emit('lesson_complete',0,location.pathname.includes('how-models')?'model-making':'atlas');}},0);
  });
  document.addEventListener('change',e=>{if(enabled&&e.target.closest('#enterprise-studio'))emit('workflow_control',0,'enterprise-studio');else if(enabled&&location.pathname.startsWith('/tools/'))emit('tool_use',0,'availability');});
  addEventListener('error',()=>{if(enabled)emit('client_error',0,'script-error');});
  fetch('/api/config',{cache:'no-store',credentials:'same-origin',signal:AbortSignal.timeout(5000)}).then(r=>r.ok?r.json():null).then(c=>{if(!c?.available||!c.collection)return;serviceReady=true;document.body.append(status);consent=preference();if(consent===null){write('ks-measurement-visitor',null);write('ks-measurement-session',null);}if(excluded())return;if(consent==='yes')enable();else if(consent===null)choices();}).catch(()=>{});
 }
 return {Engagement,safeReferrer,start};
});
