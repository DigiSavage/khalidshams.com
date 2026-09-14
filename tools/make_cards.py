#!/usr/bin/env python3
"""Render the post images (content/images/<slug>.png) from the specs in tools/cards.py.
Typographic cards in the site's palette, 1200x1200. Run: python3 tools/make_cards.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, pathlib, sys, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "fonts"
OUT = ROOT / "content" / "images"; OUT.mkdir(parents=True, exist_ok=True)
W = H = 1200
PAPER=(247,247,245); INK=(14,16,18); MUTE=(110,114,120); BLUE=(31,69,200); NAVY=(1,36,128); GOLD=(212,175,86); LIGHT=(226,231,248)
def F(name,size): return ImageFont.truetype(str(FONTS/name),size)
SERIF=lambda s:F("IBMPlexSerif-Medium.ttf",s); SERIF_I=lambda s:F("IBMPlexSerif-MediumItalic.ttf",s)
SANS=lambda s:F("IBMPlexSans-Regular.ttf",s); SANS_M=lambda s:F("IBMPlexSans-Medium.ttf",s); SANS_SB=lambda s:F("IBMPlexSans-SemiBold.ttf",s)
MONO=lambda s:F("IBMPlexMono-Medium.ttf",s)
LOGO = ROOT / "static" / "logo.png"

def mark(size):
    """KS monogram cut from the logo, alpha from colour distance to the blue field."""
    src=Image.open(LOGO).convert("RGB"); s=src.size[0]/1254
    crop=src.crop((int(340*s),int(290*s),int(930*s),int(800*s)))
    crop=crop.resize((int(crop.size[0]*size/crop.size[1]),size),Image.LANCZOS)
    a=np.asarray(crop).astype(float)
    alpha=np.clip(((a[...,0]*0.6+a[...,1]*0.4)-a[...,2]*0.55)*3,0,255).astype(np.uint8)
    return Image.fromarray(np.dstack([np.asarray(crop),alpha]),"RGBA")

def wrap(d, text, font, maxw):
    lines=[]; 
    for para in text.split("\n"):
        words=para.split(" "); cur=""
        for w in words:
            t=(cur+" "+w).strip()
            if d.textlength(t,font=font)<=maxw: cur=t
            else: lines.append(cur); cur=w
        lines.append(cur)
    return lines

def fit(d, text, mkfont, maxw, maxh, start, minsize=40, lh=1.18):
    size=start
    while size>=minsize:
        f=mkfont(size); lines=wrap(d,text,f,maxw)
        if len(lines)*size*lh<=maxh and all(d.textlength(l,font=f)<=maxw for l in lines): return f,lines,size
        size-=2
    f=mkfont(minsize); return f,wrap(d,text,f,maxw),minsize

def footer(img,d,dark):
    col = LIGHT if dark else MUTE
    m=mark(64); 
    if not dark:  # on paper, tint the white monogram to ink by recolouring
        arr=np.asarray(m).copy(); lum=arr[...,:3].mean(axis=2)
        gold=(arr[...,0]>arr[...,2]+40)
        arr[...,:3]=INK; arr[gold,:3]=GOLD
        m=Image.fromarray(arr,"RGBA")
    img.paste(m,(84,H-84-64),m)
    d.text((84+90,H-84-64+18),"Khalid Shams",font=SANS_M(30),fill=INK if not dark else PAPER)
    t="khalidshams.com"; f=MONO(26); d.text((W-84-d.textlength(t,font=f),H-84-64+22),t,font=f,fill=col)

def base(dark):
    if dark:
        img=Image.new("RGB",(W,H),NAVY)
        # subtle vignette gradient like the logo field
        g=np.linspace(0,1,H)[:,None]*np.ones((1,W)); r=np.linspace(0,1,W)[None,:]*np.ones((H,1))
        shade=(0.86+0.14*(1-(g*0.6+r*0.4))); arr=(np.asarray(img).astype(float)*shade[...,None]).clip(0,255).astype(np.uint8)
        img=Image.fromarray(arr)
    else:
        img=Image.new("RGB",(W,H),PAPER)
    return img

def eyebrow(d,text,dark,y=96):
    d.text((84,y),text.upper(),font=MONO(26),fill=GOLD if dark else BLUE)
    # letterspacing is not supported natively; approximate by spacing chars
def spaced(d,x,y,text,font,fill,gap=4):
    for ch in text:
        d.text((x,y),ch,font=font,fill=fill); x+=d.textlength(ch,font=font)+gap
    return x

# ---------- layouts ----------
TOP, BOTTOM = 190, H-84-64-48   # content area between eyebrow and footer
def place(img, layer):
    """Paste a body layer vertically centred in the content area (top-biased slightly)."""
    bb=layer.getbbox(); 
    if not bb: return
    body=layer.crop((0,0,W,bb[3]))
    avail=BOTTOM-TOP; y=TOP+max(0,(avail-bb[3])//2 - 20)
    img.paste(body,(0,y),body)
def layer(): 
    L=Image.new("RGBA",(W,H),(0,0,0,0)); return L, ImageDraw.Draw(L)

def statement(spec, dark=False):
    img=base(dark); d=ImageDraw.Draw(img)
    spaced(d,84,96,spec["eyebrow"].upper(),MONO(24),GOLD if dark else BLUE)
    d.rectangle((84,150,140,154),fill=GOLD if dark else BLUE)
    L,ld=layer()
    f,lines,size=fit(ld,spec["text"],SERIF,W-168,640,96,48,1.12)
    y=0
    for l in lines: ld.text((84,y),l,font=f,fill=PAPER if dark else INK); y+=int(size*1.12)
    if spec.get("sub"):
        y+=40; f2=SANS(36)
        for l in wrap(ld,spec["sub"],f2,W-168): ld.text((84,y),l,font=f2,fill=LIGHT if dark else MUTE); y+=48
    place(img,L); footer(img,d,dark); return img

def numbered(spec, dark=False):
    img=base(dark); d=ImageDraw.Draw(img)
    spaced(d,84,96,spec["eyebrow"].upper(),MONO(24),GOLD if dark else BLUE)
    L,ld=layer()
    f,lines,size=fit(ld,spec["text"],SERIF,W-168,240,72,48,1.12); y=0
    for l in lines: ld.text((84,y),l,font=f,fill=PAPER if dark else INK); y+=int(size*1.12)
    y+=44; items=spec["items"]; n=len(items)
    avail=BOTTOM-TOP-y; isz=42 if n<=3 else 38
    step=min(int(isz*1.2)*3+40, avail//n)
    for i,it in enumerate(items):
        ld.text((84,y+8),f"{i+1:02d}",font=MONO(30),fill=GOLD if dark else BLUE)
        fi,ls,sz=fit(ld,it,SANS_M,W-168-90,step-28,isz,30,1.2); yy=y
        for l in ls: ld.text((174,yy),l,font=fi,fill=PAPER if dark else INK); yy+=int(sz*1.2)
        hgt=max(yy-y, int(sz*1.2))+30
        if i<n-1: ld.line((174,y+hgt-12,W-84,y+hgt-12),fill=(60,90,190) if dark else (222,222,218),width=2)
        y+=hgt+8
    place(img,L); footer(img,d,dark); return img

def contrast(spec, dark=True):
    img=base(dark); d=ImageDraw.Draw(img)
    spaced(d,84,96,spec["eyebrow"].upper(),MONO(24),GOLD if dark else BLUE)
    L,ld=layer()
    f,lines,size=fit(ld,spec["text"],SERIF,W-168,260,72,48,1.12); y=0
    for l in lines: ld.text((84,y),l,font=f,fill=PAPER if dark else INK); y+=int(size*1.12)
    y+=56; colw=(W-168-56)//2; top=y
    for k,(head,items) in enumerate(spec["cols"]):
        x=84+k*(colw+56)
        ld.text((x,top),head,font=MONO(26),fill=GOLD if dark else BLUE)
        ld.line((x,top+46,x+colw,top+46),fill=GOLD if dark else BLUE,width=2)
        yy=top+76
        for it in items:
            for l in wrap(ld,it,SANS(34),colw): ld.text((x,yy),l,font=SANS(34),fill=PAPER if dark else INK); yy+=44
            yy+=20
    place(img,L); footer(img,d,dark); return img

def bignum(spec, dark=True):
    img=base(dark); d=ImageDraw.Draw(img)
    spaced(d,84,96,spec["eyebrow"].upper(),MONO(24),GOLD if dark else BLUE)
    f=SERIF(300); 
    while d.textlength(spec["num"],font=f)>W-168: f=SERIF(f.size-10)
    L,ld=layer()
    ld.text((84,0),spec["num"],font=f,fill=PAPER if dark else INK)
    y=f.size+40
    f2,lines,size=fit(ld,spec["text"],SERIF,W-168,320,60,42,1.16)
    for l in lines: ld.text((84,y),l,font=f2,fill=LIGHT if dark else MUTE); y+=int(size*1.16)
    place(img,L); footer(img,d,dark); return img

LAYOUTS={"statement":statement,"numbered":numbered,"contrast":contrast,"bignum":bignum}

if __name__=="__main__":
    sys.path.insert(0,str(ROOT/"tools")); from cards import CARDS
    for slug,spec in CARDS.items():
        img=LAYOUTS[spec["layout"]](spec, dark=spec.get("dark",False))
        img.save(OUT/f"{slug}.png",optimize=True)
        print("wrote",slug)
