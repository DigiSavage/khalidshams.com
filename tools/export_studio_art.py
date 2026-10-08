"""Export the recovered original PNG series to the registered responsive WebP set.

Requires Pillow and the 22-image source series under art-src/recovered/.
Run from any directory: python tools/export_studio_art.py
"""
from pathlib import Path
import json, hashlib
from PIL import Image
r=Path(__file__).resolve().parents[1]
# The final text-free pair for each study. Earlier drafts remain in art-src.
studies={
'atlas-workshop':(4,22,'A requester brings a damaged lamp to a workshop. A software operator works at a cobalt context tray while an owner and a reviewer oversee the boundary.',['requester','owner','agent','context','authorization','approver']),
'shams-autonomy':(20,21,'An architect inspects five ascending platforms while an owner reviews the controls beside a closed gate. A lower platform is selected.',['owner','authorization','guardrails']),
'production-review':(8,11,'An outline software operator offers a proposal to a human reviewer beside an evidence tray and a closed gate.',['agent','approver','authorization','verification']),
'enterprise-clarity':(9,10,'Architects inspect miniature infrastructure models, untangling cobalt routes across a shared planning table.',['owner','service','observability']),
'architectural-judgment':(13,12,'Architects compare three alternative system models and a blank recommendation record at a cobalt-accented table.',['owner','verification','budget']),
'approval-mobile':(14,15,'A human reviewer holds a proposal beside an outline software operator, an evidence tray and a closed gate.',['agent','approver','authorization']),
'thread-2077':(16,17,'A cobalt reading thread connects five workshop vignettes: question, evidence, proposal, boundary and receipt.',['requester','retrieval','agent','authorization','observability']),
'workbench-objects':(18,19,'A human-free studio of context trays, evidence shelves, instruments, a closed gate and service cabinets.',['context','retrieval','model','authorization','service'])}
assets=[]; provenance=[]
for scene,(light,dark,alt,concepts) in studies.items():
    dest=r/'static/art'/scene; dest.mkdir(parents=True,exist_ok=True)
    for theme,num in [('light',light),('dark',dark)]:
        candidates=list((r/'art-src/recovered').glob(f'*-{num}.png'))
        if len(candidates) != 1:
            raise SystemExit(f'Expected exactly one original ending in -{num}.png under art-src/recovered')
        source=candidates[0]
        im=Image.open(source).convert('RGB')
        provenance.append({'scene':scene,'theme':theme,'original_series_image':num,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_size':list(im.size)})
        for variant,width in [('desktop',1600),('compact',960),('mobile',720),('thumb',320)]:
            size=(width,round(im.height*width/im.width))
            out=im.resize(size,Image.Resampling.LANCZOS)
            file=dest/f'{variant}-{theme}.webp'; out.save(file,'WEBP',quality=82,method=6)
            assets.append(dict(scene=scene,variant=variant,theme=theme,file='/'+str(file.relative_to(r/'static')),purpose='Text-free illustration beside live HTML and SVG explanations',crop='full composition; no content removed',background='ivory paper' if theme=='light' else 'charcoal studio',alt=alt,concepts=concepts,text_in_image=False,width=size[0],height=size[1]))
(r/'content/art.json').write_text(json.dumps({'assets':assets},indent=2)+'\n')
(r/'docs/site/ART_PROVENANCE.json').write_text(json.dumps({'source':'Enhance Visuals Dramatically, recovered from the original 22-image conversation series on 2026-10-04','processing':'Full composition resized and exported as WebP. Light and dark are separately authored originals. Desktop exports are 1600 pixels wide as specified in the brief; this upscales the original masters. No redrawing, inversion or text added.','selected':provenance,'reference_only_series_images':[1,2,3],'superseded_series_images':[5,6,7]},indent=2)+'\n')
print(len(assets),'WebP assets',sum(p.stat().st_size for p in (r/'static/art').rglob('*.webp')),'bytes')
