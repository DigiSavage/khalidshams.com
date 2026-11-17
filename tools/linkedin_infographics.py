#!/usr/bin/env python3
"""Render inspectable LinkedIn field notes with explicit layout and asset checks.

Use the repository fonts and Pillow. No network, models, or private data are used.
python tools/linkedin_infographics.py
python tools/linkedin_infographics.py --check
python tools/linkedin_infographics.py --slug a-yes-has-a-boundary-recording
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / 'content/infographics/specs.json'
MANIFEST_PATH = ROOT / 'content/infographics/manifest.json'
W, H = 1200, 1500
PAPER, INK, NAVY = '#F7F7F5', '#0E1012', '#012480'
BLUE, GOLD, CORAL = '#1F45C8', '#B38A2D', '#B94335'
MUTED, LINE, PALE, WHITE = '#505963', '#CDD2D7', '#E9EEFC', '#FFFFFF'
FONTS = ROOT / 'tools/fonts'
FONT_FILES = {'sans':'IBMPlexSans-Regular.ttf','medium':'IBMPlexSans-Medium.ttf',
 'bold':'IBMPlexSans-SemiBold.ttf','mono':'IBMPlexMono-Medium.ttf','serif':'IBMPlexSerif-Medium.ttf'}
LAYOUTS = {'flow', 'fork', 'matrix', 'map', 'approval', 'stack', 'timeline'}
PROCESS_STAGES = ('scope', 'harden', 'anchor', 'measure', 'sustain')

class LayoutError(ValueError):
    pass

class Canvas:
    def __init__(self):
        self.image = Image.new('RGB', (W,H), PAPER)
        self.d = ImageDraw.Draw(self.image)
        self.text_boxes = []

    def font(self, size, family='sans'):
        return ImageFont.truetype(str(FONTS/FONT_FILES[family]), size)

    def text(self, text, box, size=32, family='sans', fill=INK, align='left', spacing=1.16):
        x,y,width,height = box
        if min(x,y)<0 or x+width>W or y+height>H:
            raise LayoutError(f'Text bounds outside canvas: {box}')
        font=self.font(size,family)
        lines=[]
        for para in text.split('\n'):
            current=''
            for word in para.split():
                if self.d.textlength(word,font=font)>width:
                    raise LayoutError(f'Unbreakable text overflows: {word!r}')
                candidate=(current+' '+word).strip()
                if self.d.textlength(candidate,font=font)>width:
                    lines.append(current); current=word
                else: current=candidate
            lines.append(current)
        leading=round(size*spacing)
        actual_height=0 if not lines else (len(lines)-1)*leading+size+5
        if actual_height>height:
            raise LayoutError(f'Text overflows {height}px at {size}px ({actual_height}px): {text!r}')
        self.text_boxes.append({'text':text,'box':list(box),'font_size':size,'lines':len(lines)})
        for i,line in enumerate(lines):
            px=x
            if align=='center': px=x+(width-self.d.textlength(line,font=font))/2
            elif align=='right': px=x+width-self.d.textlength(line,font=font)
            self.d.text((px,y+i*leading),line,font=font,fill=fill,anchor='lt')
        return actual_height

    def rect(self, box, fill=WHITE, outline=LINE, width=2, radius=0):
        x,y,w,h=box
        if min(x,y)<0 or x+w>W or y+h>H: raise LayoutError(f'Box outside canvas: {box}')
        self.d.rounded_rectangle((x,y,x+w,y+h),radius=radius,fill=fill,outline=outline,width=width)

    def arrow(self, start, end, color=BLUE, width=3):
        import math
        x1,y1=start; x2,y2=end
        self.d.line((x1,y1,x2,y2),fill=color,width=width)
        a=math.atan2(y2-y1,x2-x1); length=13
        points=[(x2,y2),(x2-length*math.cos(a-.5),y2-length*math.sin(a-.5)),
                (x2-length*math.cos(a+.5),y2-length*math.sin(a+.5))]
        self.d.polygon(points,fill=color)

    def node(self, box, title, detail='', accent=BLUE, dark=False):
        x,y,w,h=box
        self.rect(box,fill=NAVY if dark else WHITE,outline=NAVY if dark else LINE)
        self.d.rectangle((x,y,x+5,y+h),fill=accent)
        self.text(title,(x+24,y+18,w-48,76),size=34,family='bold',fill=PAPER if dark else INK)
        if detail: self.text(detail,(x+24,y+96,w-48,h-110),size=30,fill=PAPER if dark else MUTED)


def process_rail(c,spec):
    """Show the whole revisitable method, then open the selected move into detail."""
    focus=spec['process']['focus']
    active=PROCESS_STAGES.index(focus)
    c.text('THE SHAMS PROCESS',(72,314,430,28),size=19,family='mono',fill=NAVY)
    c.text('REVISIT AS EVIDENCE CHANGES',(570,314,558,28),size=18,family='mono',fill=MUTED,align='right')
    for i,stage in enumerate(PROCESS_STAGES):
        x=72+i*216
        selected=i==active
        if i<4: c.arrow((x+198,388),(x+213,388),color=LINE,width=3)
        c.rect((x,349,192,79),fill=NAVY if selected else '#ECEFEE',
               outline=NAVY if selected else LINE,width=2)
        c.text(f'{i+1:02d}'+(' · IN FOCUS' if selected else ''),
               (x+13,359,166,26),size=17,family='mono',fill='#E5C478' if selected else MUTED)
        c.text(stage.title(),(x+13,391,166,34),size=27,family='bold',fill=WHITE if selected else MUTED)
    # The expanding wedge makes the macro/micro relation visible without adding
    # another process step or implying that earlier stages have been completed.
    left=72+active*216
    c.d.polygon([(left,430),(left+192,430),(1144,484),(56,484)],fill=PALE)
    c.d.line((left,430,56,484),fill=BLUE,width=2)
    c.d.line((left+192,430,1144,484),fill=BLUE,width=2)
    c.rect((56,484,1088,630),fill='#EFF2FA',outline=BLUE,width=2)
    c.rect((72,449,516,35),fill=NAVY,outline=NAVY)
    c.text(f'{active+1:02d} / {focus.upper()} · UNDER THE LENS',
           (87,456,490,26),size=20,family='mono',fill=WHITE)


def chrome(c,spec):
    c.d.rectangle((0,0,1200,10),fill=NAVY)
    c.text('KHALID SHAMS',(72,37,550,34),size=24,family='mono',fill=NAVY)
    c.text(spec['category'].upper(),(620,40,508,31),size=20,family='mono',fill=MUTED,align='right')
    c.d.line((72,83,1128,83),fill=LINE,width=2)
    c.text(spec['title'],(72,108,1056,138),size=57,family='bold',fill=NAVY,spacing=1.06)
    c.text(spec['subtitle'],(72,246,1056,67),size=27,fill=MUTED)
    process_rail(c,spec)
    c.rect((72,1131,1056,118),fill=NAVY,outline=NAVY)
    c.text('CHECK IT',(93,1150,164,32),size=21,family='mono',fill='#E5C478')
    c.text(spec['test'],(274,1148,829,94),size=27,family='medium',fill=PAPER)
    # Input and durable output connect this close-up to the wider practice.
    for x,label,value in [(72,'BRING IN',spec['process']['bring_in']),
                          (616,'LEAVE WITH',spec['process']['leave_with'])]:
        c.text(label,(x,1270,512,28),size=19,family='mono',fill=BLUE)
        c.text(value,(x,1302,512,64),size=25,family='medium',fill=INK)
    c.d.line((592,1270,592,1366),fill=LINE,width=2)
    c.text(spec['boundary'],(72,1380,1056,60),size=22,fill=MUTED)
    c.d.line((72,1450,1128,1450),fill=LINE,width=2)
    c.text('A connected architecture field guide.',(72,1466,660,29),size=21,family='medium',fill=NAVY)
    c.text('khalidshams.com',(760,1467,368,28),size=20,family='mono',fill=MUTED,align='right')


def flow(c,s):
    items=s['items']
    if len(items)!=4: raise LayoutError('Flow needs four steps')
    for i,it in enumerate(items):
        y=494+i*146
        c.text(f'{i+1:02d}',(72,y+22,80,54),size=34,family='mono',fill=BLUE)
        c.rect((174,y,954,122),fill=WHITE)
        c.text(it['title'],(200,y+17,894,47),size=34,family='bold')
        c.text(it['detail'],(200,y+69,894,42),size=30,fill=MUTED)
        if i<3: c.arrow((651,y+124),(651,y+142))


def fork(c,s):
    c.node((72,494,1056,156),s['question'],s['question_detail'],dark=True)
    c.arrow((340,652),(340,707)); c.arrow((860,652),(860,707),CORAL)
    for i,it in enumerate(s['branches']):
        x=72+i*544; color=BLUE if i==0 else CORAL
        c.node((x,710,512,240),it['title'],it['detail'],accent=color)
    c.rect((72,982,1056,96),fill=PALE,outline=PALE)
    c.text(s['rule'],(98,1005,1004,65),size=32,family='medium',fill=NAVY)


def matrix(c,s):
    widths=[292,386,378]; xs=[72,364,750]
    c.rect((72,494,1056,74),fill=NAVY,outline=NAVY)
    for x,w,head in zip(xs,widths,s['columns']):
        c.text(head,(x+20,514,w-40,45),size=28,family='bold',fill=PAPER)
    if len(s['rows']) not in (3,4): raise LayoutError('Matrix needs three or four rows')
    height=125 if len(s['rows'])==4 else 164
    for i,row in enumerate(s['rows']):
        y=568+i*height
        c.rect((72,y,1056,height),fill=WHITE if i%2==0 else '#EEF0EF',outline=LINE,width=1)
        for j,(x,w,cell) in enumerate(zip(xs,widths,row)):
            c.text(cell,(x+20,y+22,w-40,height-32),size=30,family='medium' if j==0 else 'sans',fill=NAVY if j==0 else INK)


def dependency_map(c,s):
    nodes=s['nodes']
    if len(nodes)!=4: raise LayoutError('Map needs four dependencies')
    # Lines remain behind boxes; direction identifies the evidence flowing into a decision.
    for p in [(332,602),(868,602),(332,964),(868,964)]:
        c.arrow(p,(600,782),color=LINE,width=4)
    positions=[(72,494),(672,494),(72,886),(672,886)]
    for pos,it in zip(positions,nodes): c.node((*pos,456,190),it['title'],it['detail'])
    c.node((342,710,516,150),s['center'],s['center_detail'],dark=True)


def approval(c,s):
    c.text('SYNTHETIC TEACHING EXAMPLE',(72,488,1056,36),size=23,family='mono',fill=MUTED)
    for x,tag,amount,detail,color in [(72,'REVIEWED','$500','Proposal version 1',BLUE),(616,'CHANGED','$5,000','Proposal version 2',CORAL)]:
        c.rect((x,548,512,240),fill=WHITE)
        c.text(tag,(x+24,570,464,34),size=24,family='mono',fill=color)
        c.text(amount,(x+24,621,464,100),size=76,family='bold',fill=NAVY if x==72 else CORAL)
        c.text(detail,(x+24,740,464,38),size=28,fill=MUTED)
    c.arrow((600,622),(610,622),CORAL)
    c.rect((72,824,1056,100),fill=PALE,outline=PALE)
    c.text('APPROVAL BINDS TO VERSION 1',(98,854,1004,45),size=33,family='mono',fill=NAVY)
    c.arrow((600,930),(600,970),CORAL)
    c.rect((72,978,1056,100),fill=WHITE,outline=CORAL,width=3)
    c.text('STOP: version 2 needs a new review.',(98,1008,1004,44),size=35,family='bold',fill=CORAL)


def stack(c,s):
    if len(s['items'])!=4: raise LayoutError('Stack needs four layers')
    for i,it in enumerate(s['items']):
        y=494+i*125
        c.rect((72,y,1056,108),fill=WHITE,outline=LINE)
        c.rect((72,y,100,108),fill=NAVY,outline=NAVY)
        c.text(str(i+1),(92,y+28,60,60),size=43,family='mono',fill=PAPER,align='center')
        c.text(it['title'],(200,y+16,900,46),size=34,family='bold')
        c.text(it['detail'],(200,y+63,900,42),size=30,fill=MUTED)
    c.d.line((72,1008,1128,1008),fill=GOLD,width=4)
    c.text(s['equation'],(72,1035,1056,48),size=32,family='bold',fill=NAVY,align='center')


def timeline(c,s):
    if len(s['items'])!=3: raise LayoutError('Timeline needs three transitions')
    c.d.line((114,526,114,1038),fill=BLUE,width=4)
    for i,it in enumerate(s['items']):
        y=494+i*194
        c.d.ellipse((95,y+24,133,y+62),fill=PAPER,outline=BLUE,width=4)
        c.node((172,y,956,170),it['title'],it['detail'])
    c.text(s['rule'],(172,1083,956,30),size=23,family='mono',fill=MUTED)

RENDERERS={'flow':flow,'fork':fork,'matrix':matrix,'map':dependency_map,'approval':approval,'stack':stack,'timeline':timeline}


def validate_spec(spec):
    for key in ('slug','title','subtitle','category','test','boundary','alt','layout'):
        if not isinstance(spec.get(key),str) or not spec[key].strip(): raise ValueError(f'Missing {key}')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',spec['slug']): raise ValueError('Invalid slug')
    if spec['layout'] not in LAYOUTS: raise ValueError('Unknown layout')
    process=spec.get('process')
    if not isinstance(process,dict): raise ValueError('Missing process context')
    if not isinstance(process.get('focus'),str) or process['focus'] not in PROCESS_STAGES:
        raise ValueError('Invalid process focus')
    for key in ('bring_in','leave_with'):
        if not isinstance(process.get(key),str) or not process[key].strip():
            raise ValueError(f'Missing process {key}')
    if len(spec['alt'])>1000: raise ValueError('Alt text exceeds publisher limit of 1000 characters')
    for value in iter_text(spec):
        if any(d in value for d in ('—','–',' -- ')): raise ValueError('Public text contains forbidden dash')
    post=spec.get('post')
    if post:
        path=Path(post)
        if path.parent!=Path('content/posts') or path.suffix!='.md' or '..' in path.parts: raise ValueError('Invalid post path')
        if path.name[11:-3]!=spec['slug']: raise ValueError('Post slug does not match asset slug')
        if not (ROOT/path).is_file(): raise ValueError(f'Post not found: {post}')
    if spec['layout']=='fork' and len(spec.get('branches',[]))!=2:
        raise ValueError('Fork requires exactly two branches')
    if spec['layout']=='matrix':
        if len(spec.get('columns',[]))!=3 or any(len(row)!=3 for row in spec.get('rows',[])):
            raise ValueError('Matrix requires three columns')


def iter_text(value):
    if isinstance(value,str): yield value
    elif isinstance(value,list):
        for v in value: yield from iter_text(v)
    elif isinstance(value,dict):
        for v in value.values(): yield from iter_text(v)


def render(spec):
    validate_spec(spec)
    c=Canvas(); chrome(c,spec); RENDERERS[spec['layout']](c,spec)
    output=io.BytesIO(); c.image.save(output,format='PNG',optimize=True)
    return output.getvalue(),c.text_boxes


def load_specs():
    raw=json.loads(SPEC_PATH.read_text())
    if raw.get('schema_version')!=1 or not isinstance(raw.get('items'),list): raise ValueError('Unsupported spec schema')
    slugs=[s['slug'] for s in raw['items']]
    if len(set(slugs))!=len(slugs): raise ValueError('Duplicate slug')
    return raw['items']


def spec_fingerprint(spec):
    canonical=json.dumps(spec,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def input_fingerprints():
    renderer_path=Path(__file__).resolve()
    return {
        'renderer':{'path':str(renderer_path.relative_to(ROOT)),
                    'sha256':hashlib.sha256(renderer_path.read_bytes()).hexdigest()},
        'fonts':{str((FONTS/name).relative_to(ROOT)):hashlib.sha256((FONTS/name).read_bytes()).hexdigest()
                 for name in sorted(set(FONT_FILES.values()))},
    }


def manifest_entry(spec,asset_hash):
    return {'slug':spec['slug'],'post':spec.get('post'),
            'asset':'content/images/'+spec['slug']+'.png','alt':spec['alt'],
            'layout':spec['layout'],'process':spec['process'],'sha256':asset_hash,'spec_sha256':spec_fingerprint(spec),
            'source':'content/infographics/specs.json'}


def verify_manifest(manifest,specs):
    """Verify reviewed assets and every rendering input without requiring identical rasterizers."""
    if (manifest.get('schema_version'),manifest.get('width'),manifest.get('height'))!=(1,W,H):
        raise ValueError('Manifest schema or dimensions are stale')
    if manifest.get('inputs')!=input_fingerprints():
        raise ValueError('Renderer source or bundled font inputs changed; regenerate and review assets')
    entries=manifest.get('items',[])
    if len(entries)!=len(specs): raise ValueError('Manifest item coverage is stale')
    for spec,entry in zip(specs,entries):
        if entry!=manifest_entry(spec,entry.get('sha256')):
            raise ValueError(f'Specification or manifest metadata changed: {spec["slug"]}')
        destination=ROOT/entry['asset']
        if not destination.is_file(): raise ValueError(f'Asset missing: {entry["asset"]}')
        data=destination.read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError(f'Asset hash mismatch: {entry["asset"]}')
        with Image.open(io.BytesIO(data)) as image:
            if image.format!='PNG' or image.size!=(W,H) or image.mode!='RGB':
                raise ValueError(f'Invalid asset format or dimensions: {entry["asset"]}')
            image.verify()


def build(check=False,only=None):
    items=[]; prepared=[]; specs=load_specs()
    for spec in specs:
        # Preflight every layout before changing files: one overflow must not leave a partial batch.
        data,boxes=render(spec)
        asset='content/images/'+spec['slug']+'.png'
        entry=manifest_entry(spec,hashlib.sha256(data).hexdigest())
        items.append(entry)
        if not only or spec['slug']==only:
            prepared.append((asset,data,boxes))
    if only and not prepared: raise ValueError('Requested slug was not found')
    if check:
        # The renders above still check every text bound. Reviewed PNG bytes are checked
        # against their receipt, not this machine's FreeType/PNG implementation.
        manifest=json.loads(MANIFEST_PATH.read_text())
        verify_manifest(manifest,specs)
        for asset,data,boxes in prepared:
            print(f'checked {asset}: source hashes, asset hash, {len(boxes)} text regions')
        return manifest
    for asset,data,boxes in prepared:
        destination=ROOT/asset
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
        print(f'rendered {asset}: {len(boxes)} text regions')
    manifest={'schema_version':1,'width':W,'height':H,'inputs':input_fingerprints(),'items':items}
    serialized=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
    if not only:
        MANIFEST_PATH.write_text(serialized)
    return manifest


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true');ap.add_argument('--slug')
    args=ap.parse_args();build(args.check,args.slug)
