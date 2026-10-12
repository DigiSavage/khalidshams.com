"""Reserve portrait image geometry before download; check theme and layout after decode."""
import sys,json
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8767';OUT=Path(sys.argv[2] if len(sys.argv)>2 else '/tmp/art-layout');OUT.mkdir(parents=True,exist_ok=True);results=[]
def check(label,ok):results.append(dict(check=label,ok=bool(ok)));print(('PASS ' if ok else 'FAIL ')+label,flush=True)
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for theme in ('light','dark'):
  for route,scene in [('/','production-review'),('/method/','shams-autonomy')]:
   c=b.new_context(viewport={'width':390,'height':844},device_scale_factor=3,color_scheme=theme);p=c.new_page();before=[]
   selector='[data-art-scene="'+scene+'"] img'
   def capture(route):
    before.append(p.locator(selector).first.bounding_box())
    route.continue_()
   p.route('**/art/'+scene+'/mobile-'+theme+'.webp',capture)
   p.goto(BASE+route,wait_until='domcontentloaded');i=p.locator(selector).first;i.scroll_into_view_if_needed();i.evaluate('(i)=>i.decode()');after=i.bounding_box();reserved=before[0]
   check(scene+' '+theme+' portrait space reserved before load',abs(reserved['height']/reserved['width']-1.5)<.01)
   check(scene+' '+theme+' decoded image keeps reserved geometry',abs(after['height']-reserved['height'])<1 and abs(after['width']-reserved['width'])<1)
   other='light' if theme=='dark' else 'dark';p.evaluate('(t)=>document.documentElement.dataset.theme=t',other);p.wait_for_function('(s)=>document.querySelector(`[data-art-scene="${s.scene}"] img`).currentSrc.endsWith("mobile-"+s.theme+".webp")',arg={'scene':scene,'theme':other});i.evaluate('(i)=>i.decode()');check(scene+' '+theme+' manual theme retains portrait geometry',abs(i.bounding_box()['height']-reserved['height'])<1);c.close()
 b.close()
(OUT/'checks.json').write_text(json.dumps(results,indent=2)+'\n');failed=sum(not r['ok'] for r in results);print(f'{len(results)-failed}/{len(results)} passed');sys.exit(bool(failed))
