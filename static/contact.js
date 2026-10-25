(function(){'use strict';const form=document.getElementById('contact-form');if(!form)return;const status=document.getElementById('contact-status'),submit=form.querySelector('button[type=submit]');let challenge='',id=crypto.randomUUID();
// Known community links and old offer bookmarks show the current boundaries.
// Query strings never become markup or extra API fields.
const params=new URLSearchParams(location.search);
const communityContext=params.get('context')==='community'||params.get('offer')==='architecture-review';
if(communityContext){
 const context=document.getElementById('offer-context');if(context)context.hidden=false;
 const message=form.elements.namedItem('message');
 if(!message.value.trim()){
  form.elements.namedItem('topic').value='architecture';
  message.value='[Community learning]\n\nMy question or suggested topic:\n\nThe public resource this relates to, if any:\n\n';
 }
}
const note=s=>{status.textContent=s;};
async function prepare(){submit.disabled=true;try{const r=await fetch('/api/contact/challenge',{cache:'no-store'});if(!r.ok)throw Error();const d=await r.json();if(!d.challenge)throw Error();challenge=d.challenge;setTimeout(()=>{submit.disabled=false;},2100);note('Ready. Your message goes to my private website inbox.');}catch{note('The website form is unavailable. Please use email or LinkedIn below.');}}
form.addEventListener('submit',async e=>{e.preventDefault();if(!form.reportValidity())return;submit.disabled=true;note('Saving your inquiry…');const data=Object.fromEntries(new FormData(form));data.id=id;data.challenge=challenge;data.test=new URLSearchParams(location.search).get('ks-test')==='1';data.source='/contact/';try{const prior=sessionStorage.getItem('ks-contact-source');if(prior&&/^\/[a-z0-9/-]*$/.test(prior))data.source=prior;}catch{}
 if(communityContext)data.source='/';
 try{
  const send=async payload=>{const response=await fetch('/api/contact',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(payload)});let result;try{result=await response.json();}catch{throw Error('Storage could not be confirmed. Please retry or use email below.');}return {response,result};};
  let reply=await send(data);
  // A new static route can precede the service's page registry. This specific
  // validation failure occurs before storage. Retry once with the form's own
  // registered path, preserving the inquiry ID, challenge and every user field.
  if(reply.response.status===400&&reply.result?.error==='Unknown public page'&&data.source!=='/contact/'){
   data.source='/contact/';reply=await send(data);
  }
  if(!reply.response.ok||reply.result?.stored!==true)throw Error(reply.result?.error||'Storage was not confirmed. Please retry.');form.reset();note('Your inquiry has been stored. Thank you. Reference: '+reply.result.id);id=crypto.randomUUID();challenge='';form.hidden=true;}catch(error){note(error.message||'Could not confirm storage. Retry with the same message; duplicate submissions are protected.');submit.disabled=false;}});
prepare();})();
