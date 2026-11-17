#!/usr/bin/env python3
"""Render LinkedIn field-guide diagrams: one SHAMS map, one move opened into a mechanism.

Use the repository fonts and Pillow. No network, models, or private data are used.
python tools/linkedin_infographics.py
python tools/linkedin_infographics.py --check
python tools/linkedin_infographics.py --slug a-yes-has-a-boundary-recording
python tools/linkedin_infographics.py --preview /tmp/review   # full + phone previews, nothing committed
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / 'content/infographics/specs.json'
MANIFEST_PATH = ROOT / 'content/infographics/manifest.json'
W, H = 1200, 1500
SCALE = 2            # draw at 2x and downsample so curves, rings and diagonals are smooth
PHONE_WIDTH = 390    # the review preview: roughly one feed column on a phone
MIN_TEXT = 18        # nothing smaller than this is ever drawn
READABLE = 24        # the phone layer: a reader in the feed follows the card at this size and above
PHONE_SHARE = 0.45   # at least this share of the characters must sit in the phone layer
PAPER, INK, NAVY = '#F7F7F5', '#0E1012', '#012480'
BLUE, GOLD, CORAL = '#1F45C8', '#B38A2D', '#B94335'
MUTED, LINE, PALE, WHITE = '#505963', '#CDD2D7', '#E9EEFC', '#FFFFFF'
LENS, GRID, TINT = '#EEF2FB', '#D5DDF2', '#F3F6FE'
GOLD_PALE, GOLD_LIGHT, CORAL_PALE = '#FBF5E6', '#E5C478', '#FBEFEC'
FONTS = ROOT / 'tools/fonts'
FONT_FILES = {'sans':'IBMPlexSans-Regular.ttf','medium':'IBMPlexSans-Medium.ttf',
 'bold':'IBMPlexSans-SemiBold.ttf','mono':'IBMPlexMono-Medium.ttf',
 'serif':'IBMPlexSerif-Medium.ttf','italic':'IBMPlexSerif-MediumItalic.ttf'}
LAYOUTS = {'lanes', 'route', 'gate', 'ledger', 'hub', 'strata', 'span', 'binding'}
PROCESS_STAGES = ('scope', 'harden', 'anchor', 'measure', 'sustain')
# What each move settles, in two words, so the map means something to a first-time reader.
STAGE_REMIT = {'scope':'outcome · owner', 'harden':'identity · limits', 'anchor':'data · meaning',
               'measure':'evidence · cost', 'sustain':'run · recover'}
STATION_X = (150, 375, 600, 825, 1050)
TRACK_Y = 414
PANEL = (56, 490, 1088, 716)      # the opened move
REGION = (84, 560, 1032, 580)     # where each mechanism draws
SHADOW = '#D3DBF0'


class LayoutError(ValueError):
    pass


def bezier(p0, p1, p2, p3, n=40):
    points = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        points.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                       u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return points


def vflow(a, b):
    """A smooth path that leaves a vertically and arrives at b vertically."""
    mid = (a[1] + b[1]) / 2
    return bezier(a, (a[0], mid), (b[0], mid), b)


class Canvas:
    def __init__(self):
        self.image = Image.new('RGB', (W*SCALE, H*SCALE), PAPER)
        self.d = ImageDraw.Draw(self.image)
        self.text_boxes = []
        self._fonts = {}

    # ---- text -------------------------------------------------------------
    def font(self, size, family='sans'):
        key = (round(size*SCALE), family)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(str(FONTS/FONT_FILES[family]), key[0])
        return self._fonts[key]

    def measure(self, text, size, family='sans'):
        return self.d.textlength(text, font=self.font(size, family)) / SCALE

    def _inside(self, x, y, w, h, what):
        if min(x, y) < -0.5 or x + w > W + 0.5 or y + h > H + 0.5:
            raise LayoutError(f'{what} outside canvas: {(round(x), round(y), round(w), round(h))}')

    def _size_ok(self, size, text):
        if size < MIN_TEXT:
            raise LayoutError(f'Text below the {MIN_TEXT}px floor ({size}px): {text!r}')

    def wrap(self, text, width, size, family='sans'):
        lines = []
        for para in text.split('\n'):
            current = ''
            for word in para.split():
                if self.measure(word, size, family) > width:
                    raise LayoutError(f'Unbreakable text overflows: {word!r}')
                candidate = (current + ' ' + word).strip()
                if self.measure(candidate, size, family) > width:
                    lines.append(current); current = word
                else:
                    current = candidate
            lines.append(current)
        return lines

    def text(self, text, box, size=28, family='sans', fill=INK, align='left', spacing=1.16, valign='top'):
        """Wrapped text inside a box. Overflow is an error, never a shrink or a crop."""
        x, y, width, height = box
        self._inside(x, y, width, height, 'Text bounds')
        self._size_ok(size, text)
        lines = self.wrap(text, width, size, family)
        leading = round(size*spacing)
        actual = 0 if not lines else (len(lines)-1)*leading + size + 5
        if actual > height:
            raise LayoutError(f'Text overflows {round(height)}px at {size}px ({actual}px): {text!r}')
        top = y + (height-actual)/2 if valign == 'middle' else y
        self.text_boxes.append({'text':text, 'box':[round(v) for v in box], 'font_size':size, 'lines':len(lines)})
        font = self.font(size, family)
        for i, line in enumerate(lines):
            px = x
            if align == 'center': px = x + (width-self.measure(line, size, family))/2
            elif align == 'right': px = x + width-self.measure(line, size, family)
            self.d.text((px*SCALE, (top + i*leading + size*0.8)*SCALE), line, font=font, fill=fill, anchor='ls')
        return actual

    def label(self, text, xy, size=20, family='sans', fill=INK, anchor='lm'):
        """One unwrapped line anchored at a point: l/m/r then t/m. Returns its width."""
        self._size_ok(size, text)
        x, y = xy
        width = self.measure(text, size, family)
        left = x if anchor[0] == 'l' else x - width/2 if anchor[0] == 'm' else x - width
        top = y - size*0.62 if anchor[1] == 'm' else y
        self._inside(left, top, width, size*1.24, f'Label {text!r}')
        self.text_boxes.append({'text':text, 'box':[round(left), round(top), round(width), round(size*1.24)],
                                'font_size':size, 'lines':1})
        self.d.text((x*SCALE, y*SCALE), text, font=self.font(size, family), fill=fill,
                    anchor=anchor[0] + ('m' if anchor[1] == 'm' else 'a'))
        return width

    # ---- shapes -----------------------------------------------------------
    def rect(self, box, fill=WHITE, outline=LINE, width=2, radius=0, dash=None, corners=None, shadow=False):
        x, y, w, h = box
        self._inside(x, y, w, h, 'Box')
        if shadow:    # a flat offset shadow lifts a card off the drafting surface
            self.d.rounded_rectangle((x*SCALE, (y+6)*SCALE, (x+w)*SCALE, (y+h+6)*SCALE), radius=radius*SCALE, fill=SHADOW)
        xy = (x*SCALE, y*SCALE, (x+w)*SCALE, (y+h)*SCALE)
        solid = None if dash else outline
        self.d.rounded_rectangle(xy, radius=radius*SCALE, fill=fill, outline=solid,
                                 width=round(width*SCALE) if solid else 0, corners=corners)
        if dash and outline:
            r = min(radius, w/2, h/2); pts = []
            for cx, cy, start in ((x+w-r, y+r, -90), (x+w-r, y+h-r, 0), (x+r, y+h-r, 90), (x+r, y+r, 180)):
                for k in range(7):
                    a = math.radians(start + k*15)
                    pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
            self.line(pts + [pts[0]], outline, width, dash=dash)

    def poly(self, points, fill):
        self.d.polygon([(x*SCALE, y*SCALE) for x, y in points], fill=fill)

    def circle(self, center, r, fill=None, outline=None, width=2):
        x, y = center
        self.d.ellipse(((x-r)*SCALE, (y-r)*SCALE, (x+r)*SCALE, (y+r)*SCALE), fill=fill, outline=outline,
                       width=max(1, round(width*SCALE)) if outline else 0)

    def arc(self, box, start, end, fill, width=2):
        self.d.arc(tuple(v*SCALE for v in box), start, end, fill=fill, width=max(1, round(width*SCALE)))

    def line(self, points, fill=BLUE, width=3, dash=None):
        pts = [(x*SCALE, y*SCALE) for x, y in points]
        w = max(1, round(width*SCALE))
        if not dash:
            self.d.line(pts, fill=fill, width=w, joint='curve')
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse((x-w/2, y-w/2, x+w/2, y+w/2), fill=fill)
            return
        on, off = dash[0]*SCALE, dash[1]*SCALE
        drawing, left = True, on
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            seg = math.hypot(x2-x1, y2-y1); pos = 0
            if not seg: continue
            ux, uy = (x2-x1)/seg, (y2-y1)/seg
            while pos < seg:
                step = min(left, seg-pos)
                if drawing:
                    self.d.line((x1+ux*pos, y1+uy*pos, x1+ux*(pos+step), y1+uy*(pos+step)), fill=fill, width=w)
                pos += step; left -= step
                if left <= 1e-6:
                    drawing = not drawing; left = on if drawing else off

    def arrow(self, points, fill=BLUE, width=3, dash=None, head=13):
        """A path with a filled head on its last point."""
        (x1, y1), (x2, y2) = points[-2], points[-1]
        a = math.atan2(y2-y1, x2-x1)
        tip = (x2, y2); back = (x2 - head*0.7*math.cos(a), y2 - head*0.7*math.sin(a))
        self.line(list(points[:-1]) + [back], fill, width, dash)
        self.poly([tip, (x2 - head*math.cos(a-.48), y2 - head*math.sin(a-.48)),
                   (x2 - head*math.cos(a+.48), y2 - head*math.sin(a+.48))], fill)

    def dots(self, box, step=24, color=GRID):
        """A quiet drafting grid that marks the surface of the opened move."""
        x, y, w, h = box
        r = 1.1*SCALE
        for gx in range(int(x+step), int(x+w), step):
            for gy in range(int(y+step), int(y+h), step):
                self.d.ellipse((gx*SCALE-r, gy*SCALE-r, gx*SCALE+r, gy*SCALE+r), fill=color)

    # ---- symbols ----------------------------------------------------------
    def icon(self, name, cx, cy, size, color=NAVY):
        if name not in ICONS: raise ValueError(f'Unknown icon: {name!r}')
        u = size/2; lw = max(2.0, size*0.085)
        pen = _Pen(self, cx, cy, u, lw, color)
        ICONS[name](pen)

    def medallion(self, center, r, icon, fill=PALE, outline=BLUE, color=NAVY, width=2):
        self.circle(center, r, fill=fill, outline=outline, width=width)
        self.icon(icon, center[0], center[1], r*1.12, color)

    def chip_width(self, text, size=22, family='medium', h=34, pad=13, icon=None):
        return pad*2 + self.measure(text, size, family) + ((h-8) if icon else 0)

    def chip(self, x, y, text, size=22, family='medium', fg=NAVY, bg=WHITE, outline=LINE, h=34, pad=13,
             icon=None, dash=None):
        w = self.chip_width(text, size, family, h, pad, icon)
        self.rect((x, y, w, h), fill=bg, outline=outline, width=2, radius=h/2, dash=dash)
        tx = x + pad
        if icon:
            self.icon(icon, x + pad + (h-16)/2, y + h/2, h-14, fg); tx += h-8
        self.label(text, (tx, y + h/2), size, family, fg, 'lm')
        return w

    def chips(self, items, x, y, max_w, join=None, align='left', gap=10, join_color=BLUE, **style):
        """A row of tokens. items are strings or {text, icon}. A row that does not fit is an error."""
        items = [i if isinstance(i, dict) else {'text':i} for i in items]
        keys = {k: style[k] for k in ('size', 'family', 'h', 'pad') if k in style}
        widths = [self.chip_width(i['text'], icon=i.get('icon'), **keys) for i in items]
        step = gap + (22 if join else 0)
        total = sum(widths) + step*(len(items)-1)
        if total > max_w:
            raise LayoutError(f'Chip row needs {round(total)}px of {round(max_w)}px: {[i["text"] for i in items]}')
        px = x if align == 'left' else x + max_w - total if align == 'right' else x + (max_w-total)/2
        h = style.get('h', 34)
        for i, (item, w) in enumerate(zip(items, widths)):
            self.chip(px, y, item['text'], icon=item.get('icon'), **style)
            px += w
            if i < len(items)-1:
                mid = px + step/2
                if join == 'arrow': self.arrow([(mid-10, y+h/2), (mid+10, y+h/2)], join_color, 2.5, head=9)
                elif join == 'plus':
                    self.line([(mid-6, y+h/2), (mid+6, y+h/2)], join_color, 2.5)
                    self.line([(mid, y+h/2-6), (mid, y+h/2+6)], join_color, 2.5)
                px += step
        return total


class _Pen:
    """Icon drawing in a unit square: x and y run from -1 to 1 around the icon centre."""
    def __init__(self, c, cx, cy, u, lw, color):
        self.c, self.cx, self.cy, self.u, self.lw, self.color = c, cx, cy, u, lw, color
    def P(self, x, y): return (self.cx + x*self.u, self.cy + y*self.u)
    def L(self, pts, w=1, closed=False):
        pts = [self.P(*p) for p in pts]
        self.c.line(pts + ([pts[0]] if closed else []), self.color, self.lw*w)
    def O(self, x, y, r, solid=False, w=1):
        self.c.circle(self.P(x, y), r*self.u, fill=self.color if solid else None,
                      outline=None if solid else self.color, width=self.lw*w)
    def A(self, x1, y1, x2, y2, start, end, w=1):
        self.c.arc((*self.P(x1, y1), *self.P(x2, y2)), start, end, self.color, self.lw*w)
    def F(self, pts): self.c.poly([self.P(*p) for p in pts], self.color)
    def G(self, glyph):
        size = max(8, round(self.u*1.15*SCALE))
        font = ImageFont.truetype(str(FONTS/FONT_FILES['bold']), size)
        self.c.d.text((self.cx*SCALE, self.cy*SCALE), glyph, font=font, fill=self.color, anchor='mm')


def _person(p):      # solid: a person. The site rule is solid figures are people.
    p.O(0, -.42, .3, solid=True)
    x1, y1 = p.P(-.62, .04); x2, y2 = p.P(.62, 1.2)
    p.c.d.pieslice((x1*SCALE, y1*SCALE, x2*SCALE, y2*SCALE), 180, 360, fill=p.color)
def _database(p):
    p.A(-.62, -.84, .62, -.4, 0, 360); p.A(-.62, -.22, .62, .22, 0, 180); p.A(-.62, .4, .62, .84, 0, 180)
    p.L([(-.62, -.62), (-.62, .62)]); p.L([(.62, -.62), (.62, .62)])
def _doc(p):
    p.L([(-.5, -.8), (.18, -.8), (.55, -.43), (.55, .8), (-.5, .8)], closed=True)
    p.L([(.18, -.8), (.18, -.43), (.55, -.43)])
    p.L([(-.24, -.02), (.28, -.02)], .8); p.L([(-.24, .26), (.28, .26)], .8); p.L([(-.24, .54), (.08, .54)], .8)
def _shield(p):
    p.L([(0, -.85), (.66, -.58), (.66, .05), (.4, .52), (0, .85), (-.4, .52), (-.66, .05), (-.66, -.58)], closed=True)
def _search(p): p.O(-.14, -.14, .5); p.L([(.24, .24), (.76, .76)], 1.5)
def _check(p): p.O(0, 0, .82); p.L([(-.36, .02), (-.1, .3), (.4, -.28)], 1.2)
def _stop(p): p.O(0, 0, .82); p.L([(-.32, -.32), (.32, .32)], 1.2); p.L([(.32, -.32), (-.32, .32)], 1.2)
def _clock(p): p.O(0, 0, .82); p.L([(0, -.46), (0, 0), (.32, .2)], 1.1)
def _coin(p): p.O(0, 0, .82); p.G('$')
def _question(p): p.O(0, 0, .82); p.G('?')
def _target(p): p.O(0, 0, .82); p.O(0, 0, .46); p.O(0, 0, .14, solid=True)
def _bell(p):
    p.L([(-.66, .42), (-.46, .16), (-.44, -.2), (-.3, -.52), (0, -.68), (.3, -.52), (.44, -.2), (.46, .16), (.66, .42)], closed=True)
    p.O(0, .68, .12, solid=True); p.L([(0, -.68), (0, -.86)])
def _gear(p):
    p.O(0, 0, .4)
    for k in range(8):
        a = math.radians(k*45)
        p.L([(.56*math.cos(a), .56*math.sin(a)), (.84*math.cos(a), .84*math.sin(a))], 1.6)
def _cube(p):
    p.L([(0, -.82), (.71, -.41), (.71, .41), (0, .82), (-.71, .41), (-.71, -.41)], closed=True)
    p.L([(-.71, -.41), (0, 0), (.71, -.41)]); p.L([(0, 0), (0, .82)])
def _layers(p):
    p.L([(0, -.78), (.78, -.38), (0, .02), (-.78, -.38)], closed=True)
    p.L([(-.78, 0), (0, .4), (.78, 0)]); p.L([(-.78, .38), (0, .78), (.78, .38)])
def _key(p): p.O(-.44, 0, .32); p.L([(-.12, 0), (.82, 0)]); p.L([(.5, 0), (.5, .32)]); p.L([(.78, 0), (.78, .32)])
def _lock(p):
    p.L([(-.52, -.04), (.52, -.04), (.52, .8), (-.52, .8)], closed=True)
    p.A(-.34, -.84, .34, -.16, 180, 360); p.L([(-.34, -.5), (-.34, -.04)]); p.L([(.34, -.5), (.34, -.04)])
    p.O(0, .36, .11, solid=True)
def _mail(p):
    p.L([(-.78, -.52), (.78, -.52), (.78, .52), (-.78, .52)], closed=True); p.L([(-.78, -.52), (0, .1), (.78, -.52)])
def _queue(p): p.O(-.62, 0, .2); p.O(0, 0, .2); p.O(.62, 0, .2, solid=True)
def _refresh(p):
    p.A(-.7, -.7, .7, .7, 40, 300); p.F([(.08, -.74), (.5, -.9), (.5, -.42)])
def _flag(p):
    p.L([(-.5, -.82), (-.5, .85)], 1.2); p.L([(-.5, -.74), (.62, -.74), (.34, -.42), (.62, -.1), (-.5, -.1)])
def _chart(p):
    p.L([(-.74, .68), (.78, .68)]); p.L([(-.4, .62), (-.4, .14)], 2.2)
    p.L([(.02, .62), (.02, -.26)], 2.2); p.L([(.44, .62), (.44, -.64)], 2.2)
def _link(p): p.O(-.3, 0, .46); p.O(.3, 0, .46)
def _eye(p):
    p.L([(-.86, 0), (-.46, -.38), (0, -.5), (.46, -.38), (.86, 0), (.46, .38), (0, .5), (-.46, .38)], closed=True)
    p.O(0, 0, .2, solid=True)
def _branch(p):
    p.L([(-.8, 0), (-.18, 0)]); p.L([(-.18, 0), (.14, -.5), (.6, -.5)]); p.L([(-.18, 0), (.14, .5), (.6, .5)])
    p.F([(.84, -.5), (.52, -.7), (.52, -.3)]); p.F([(.84, .5), (.52, .3), (.52, .7)])
def _box(p):
    p.L([(-.7, -.28), (.7, -.28), (.7, .72), (-.7, .72)], closed=True)
    p.L([(-.82, -.66), (.82, -.66), (.82, -.28), (-.82, -.28)], closed=True); p.L([(-.2, .1), (.2, .1)], 1.2)
def _network(p):
    p.L([(-.1, -.32), (-.48, .3)]); p.L([(.1, -.32), (.48, .3)]); p.L([(-.36, .5), (.36, .5)])
    p.O(0, -.52, .22); p.O(-.58, .5, .22); p.O(.58, .5, .22)
def _tag(p):
    p.L([(-.78, -.42), (.2, -.42), (.78, 0), (.2, .42), (-.78, .42)], closed=True); p.O(.3, 0, .1, solid=True)
def _calendar(p):
    p.L([(-.7, -.6), (.7, -.6), (.7, .75), (-.7, .75)], closed=True); p.L([(-.7, -.2), (.7, -.2)])
    p.L([(-.35, -.86), (-.35, -.44)], 1.2); p.L([(.35, -.86), (.35, -.44)], 1.2)
def _power(p): p.A(-.72, -.62, .72, .82, -60, 240); p.L([(0, -.86), (0, -.06)], 1.2)
def _gauge(p): p.A(-.82, -.62, .82, 1.02, 180, 360); p.L([(0, .2), (.4, -.3)], 1.2); p.O(0, .2, .1, solid=True)
def _list(p):
    for y in (-.5, 0, .5):
        p.O(-.62, y, .1, solid=True); p.L([(-.3, y), (.74, y)], 1.1)

ICONS = {'person':_person, 'database':_database, 'doc':_doc, 'shield':_shield, 'search':_search,
         'check':_check, 'stop':_stop, 'clock':_clock, 'coin':_coin, 'question':_question,
         'target':_target, 'bell':_bell, 'gear':_gear, 'cube':_cube, 'layers':_layers, 'key':_key,
         'lock':_lock, 'mail':_mail, 'queue':_queue, 'refresh':_refresh, 'flag':_flag, 'chart':_chart,
         'link':_link, 'eye':_eye, 'branch':_branch, 'box':_box, 'network':_network, 'tag':_tag,
         'calendar':_calendar, 'power':_power, 'gauge':_gauge, 'list':_list}
TONES = {'go':(BLUE, PALE, 'check'), 'stop':(CORAL, CORAL_PALE, 'stop'), 'cost':(GOLD, GOLD_PALE, 'coin')}


# ---- the shared frame: masthead, map, opened move, check, limit -------------------------

def journey(c, spec):
    """The whole revisitable method as a line of five stations, with one opened below."""
    focus = spec['process']['focus']; active = PROCESS_STAGES.index(focus); ax = STATION_X[active]
    c.label('THE SHAMS METHOD · FIVE MOVES', (72, 306), 18, 'mono', NAVY)
    c.label('REVISIT AS EVIDENCE CHANGES', (1128, 306), 18, 'mono', MUTED, 'rm')
    px, py, pw, ph = PANEL
    # The projection: the selected station is the small view, the panel is its enlargement.
    c.poly([(ax-38, TRACK_Y), (ax+38, TRACK_Y), (px+pw, py), (px, py)], PALE)
    c.line([(ax-38, TRACK_Y), (px, py)], BLUE, 2); c.line([(ax+38, TRACK_Y), (px+pw, py)], BLUE, 2)
    c.line([(96, TRACK_Y), (1094, TRACK_Y)], NAVY, 3)
    for i in range(4):   # direction of travel between stations
        mid = (STATION_X[i] + STATION_X[i+1]) / 2
        c.poly([(mid+8, TRACK_Y), (mid-5, TRACK_Y-7), (mid-5, TRACK_Y+7)], NAVY)
    c.icon('refresh', 1116, TRACK_Y, 24, MUTED)     # and back round again
    for i, stage in enumerate(PROCESS_STAGES):
        x = STATION_X[i]; selected = i == active
        c.label(stage.title(), (x, 338), 28 if selected else 25, 'bold' if selected else 'medium',
                NAVY if selected else MUTED, 'mm')
        c.label(STAGE_REMIT[stage], (x, 367), 18, 'mono', BLUE if selected else MUTED, 'mm')
        if selected:
            c.circle((x, TRACK_Y), 38, fill=PAPER, outline=BLUE, width=3)
            c.circle((x, TRACK_Y), 28, fill=NAVY)
            c.label(stage[0].upper(), (x, TRACK_Y), 32, 'bold', WHITE, 'mm')
        else:
            c.circle((x, TRACK_Y), 21, fill=WHITE, outline=MUTED, width=2)
            c.label(stage[0].upper(), (x, TRACK_Y), 22, 'bold', MUTED, 'mm')
    c.rect(PANEL, fill=LENS, outline=BLUE, width=2, radius=14, corners=(False, False, True, True))
    c.dots(PANEL)
    tab = f'{active+1:02d} · {focus.upper()} · IN FOCUS'
    tw = c.measure(tab, 19, 'mono')
    c.rect((72, py-36, tw+32, 36), fill=NAVY, outline=NAVY, width=0)
    c.label(tab, (88, py-18), 19, 'mono', WHITE)


def ports(c, spec):
    """Evidence enters the opened move at the top left. A reusable artifact leaves bottom right."""
    px, py, pw, ph = PANEL; yin = py + 35; yout = py + ph - 33
    c.arrow([(24, yin), (98, yin)], BLUE, 3)
    c.circle((px, yin), 7, fill=WHITE, outline=BLUE, width=2.5)
    c.label('BRING IN', (112, yin), 19, 'mono', BLUE)
    c.label(spec['process']['bring_in'], (222, yin), 26, 'medium', INK)
    c.arrow([(1102, yout), (1176, yout)], BLUE, 3)
    c.circle((px+pw, yout), 7, fill=WHITE, outline=BLUE, width=2.5)
    lw = c.label('LEAVE WITH', (1088, yout), 19, 'mono', BLUE, 'rm')
    vw = c.label(spec['process']['leave_with'], (1088-lw-16, yout), 26, 'medium', INK, 'rm')
    c.icon('doc', 1088-lw-16-vw-24, yout, 28, BLUE)


def frame(c, spec):
    c.d.rectangle((0, 0, W*SCALE, 10*SCALE), fill=NAVY)
    c.label('KHALID SHAMS', (72, 50), 24, 'mono', NAVY)
    c.label(spec['category'].upper(), (1128, 50), 20, 'mono', MUTED, 'rm')
    c.line([(72, 80), (1128, 80)], LINE, 2)
    lines = spec['title'].split('\n')
    if len(lines) != 2: raise LayoutError('Title needs exactly two lines')
    for line, y, family, color in ((lines[0], 96, 'serif', NAVY), (lines[1], 164, 'italic', BLUE)):
        c.text(line, (72, y, 1056, 72), size=60, family=family, fill=color)
    c.text(spec['subtitle'], (72, 246, 1056, 36), size=26, fill=MUTED)
    journey(c, spec); ports(c, spec)
    c.rect((72, 1220, 1056, 88), fill=NAVY, outline=NAVY, width=0, radius=10)
    c.icon('check', 112, 1264, 38, GOLD_LIGHT)
    c.label('CHECK IT', (142, 1264), 20, 'mono', GOLD_LIGHT)
    c.text(spec['test'], (268, 1229, 836, 70), size=27, family='medium', fill=PAPER, valign='middle')
    c.rect((72, 1318, 1056, 84), fill=PAPER, outline=MUTED, width=2, radius=10, dash=(9, 7))
    c.label('LIMIT', (98, 1360), 20, 'mono', NAVY)
    c.text(spec['boundary'], (190, 1328, 914, 64), size=24, fill=INK, valign='middle')
    c.line([(72, 1424), (1128, 1424)], LINE, 2)
    c.label('A connected architecture field guide.', (72, 1458), 21, 'medium', NAVY)
    c.label('khalidshams.com', (1128, 1458), 20, 'mono', MUTED, 'rm')


# ---- mechanisms: each draws one kind of relationship inside REGION -----------------------
# Every mechanism has a phone layer (titles at 28px or more) and an inspection layer
# (questions, tokens and examples in smaller type) for the reader who saves the card.

FINE = dict(size=20, h=30, pad=11)       # token rows inside cards


def lanes(c, s):
    """One subject, two ways to justify it, one shared decision. The aside lane is a boundary."""
    x0, y0, w, h = REGION
    src, main, aside, out = s['source'], s['primary'], s['aside'], s['outcome']
    aw = 628; bx = x0 + aw + 24; bw = w - aw - 24; top = y0 + 98; lh = 384; yo = y0 + 498
    acx = x0 + aw/2; bcx = bx + bw/2
    c.rect((x0, y0, w, 56), fill=WHITE, outline=NAVY, width=2, radius=12, shadow=True)
    c.medallion((x0+40, y0+28), 21, src['icon'], fill=NAVY, outline=NAVY, color=WHITE)
    tw = c.label(src['title'], (x0+76, y0+28), 30, 'bold', INK)
    c.label(src['detail'], (x0+76+tw+14, y0+28), 27, 'sans', MUTED)
    c.arrow([(acx, y0+62), (acx, top)], BLUE, 4)
    c.arrow([(bcx, y0+62), (bcx, top)], MUTED, 3, dash=(7, 6))
    for cx, text, fg, bg, edge, dash in ((acx, main['label'], WHITE, BLUE, BLUE, None),
                                         (bcx, aside['label'], NAVY, PAPER, MUTED, (6, 5))):
        cw = c.chip_width(text, 18, 'mono', 30, 14)
        c.chip(cx-cw/2, y0+61, text, 18, 'mono', fg, bg, edge, 30, 14, dash=dash)
    # Primary lane: the evidence chain, drawn solid.
    c.rect((x0, top, aw, lh), fill=WHITE, outline=BLUE, width=2, radius=14, shadow=True)
    steps = main['steps']; example = main.get('example'); rh = (lh - (40 if example else 0)) / len(steps)
    sx = x0 + 50
    c.line([(sx, top+rh/2), (sx, top+rh*2.5)], BLUE, 3)
    for i, step in enumerate(steps):
        cy = top + rh/2 + i*rh
        if i: c.poly([(sx, cy-30), (sx-7, cy-43), (sx+7, cy-43)], BLUE)
        c.medallion((sx, cy), 26, step['icon'])
        c.label(step['title'], (x0+94, cy-27), 29, 'bold', INK)
        c.label(f'{i+1:02d}', (x0+aw-20, cy-27), 19, 'mono', BLUE, 'rm')
        c.label(step['ask'], (x0+94, cy+4), 22, 'sans', MUTED)
        c.chips(step['chips'], x0+94, cy+21, aw-94-20, join=step.get('join'), **FINE)
    if example:
        c.line([(x0+20, top+lh-40), (x0+aw-20, top+lh-40)], LINE, 2, dash=(5, 5))
        ew = c.label('EXAMPLE', (x0+24, top+lh-21), 18, 'mono', BLUE)
        c.label(example, (x0+24+ew+12, top+lh-21), 21, 'sans', INK)
    # Aside lane: dashed because it is a boundary on the conclusion, not a second procedure.
    c.rect((bx, top, bw, lh), fill=PAPER, outline=MUTED, width=2, radius=14, dash=(9, 7))
    c.text(aside['title'], (bx+24, top+16, bw-48, 40), size=28, family='bold', fill=INK)
    for i, item in enumerate(aside['items']):
        cy = top + 106 + i*70
        c.icon(item['icon'], bx+42, cy-1, 30, NAVY)
        c.label(item['text'], (bx+72, cy-13), 26, 'bold', INK)
        c.label(item['ask'], (bx+72, cy+15), 21, 'sans', MUTED)
    c.line([(bx+20, top+300), (bx+bw-20, top+300)], LINE, 2, dash=(5, 5))
    c.icon('stop', bx+42, top+341, 30, CORAL)
    c.text(aside['rule'], (bx+72, top+311, bw-92, 60), size=24, family='bold', fill=CORAL, valign='middle')
    c.arrow([(acx, top+lh+2), (acx, yo)], BLUE, 4, head=10)
    c.arrow([(bcx, top+lh), (bcx, yo)], MUTED, 3, head=10)
    # Outcome: gold, because this is where the cost gets a name.
    c.rect((x0, yo, w, 82), fill=GOLD_PALE, outline=GOLD, width=2, radius=14, shadow=True)
    c.medallion((x0+48, yo+41), 26, out['icon'], fill=GOLD, outline=GOLD, color=WHITE)
    tw = max(c.label(out['title'], (x0+92, yo+27), 29, 'bold', INK),
             c.label(out['detail'], (x0+92, yo+58), 22, 'sans', MUTED))
    c.chips(out['chips'], x0+92+tw+16, yo+24, w-92-tw-16-20, align='right', size=22, h=34, fg=INK, outline=GOLD)


def route(c, s):
    """A trace along a spine: stations alternate sides and each link names the relation."""
    x0, y0, w, h = REGION; steps = s['steps']; cx = x0 + w/2; cw = 452; ch = 150
    pitch = (h - ch) / (len(steps)-1)
    ys = [y0 + ch/2 + i*pitch for i in range(len(steps))]
    c.line([(cx, ys[0]), (cx, ys[-1])], BLUE, 4)
    if s.get('counter'):     # the same path travelled the other way
        c.arrow([(cx+16, ys[-1]-42), (cx+16, ys[0]+48)], MUTED, 2.5, dash=(6, 5), head=10)
    for i, (step, y) in enumerate(zip(steps, ys)):
        left = i % 2 == 0
        x = x0 if left else x0 + w - cw; t = y - ch/2
        c.line([(cx, y), (x + cw if left else x, y)], BLUE, 3)
        c.rect((x, t, cw, ch), fill=WHITE, outline=LINE, width=2, radius=14, shadow=True)
        c.label(f'{i+1:02d}', (x+cw-20, t+30), 19, 'mono', BLUE, 'rm')
        c.text(step['title'], (x+22, t+12, cw-84, 38), size=29, family='bold')
        if step.get('chips'):
            c.text(step['detail'], (x+22, t+52, cw-44, 58), size=24, fill=MUTED)
            c.chips(step['chips'], x+22, t+112, cw-44, **FINE)
        else:
            c.text(step['detail'], (x+22, t+52, cw-44, 88), size=24, fill=MUTED)
        first = i == 0
        c.medallion((cx, y), 32, step['icon'], fill=NAVY if first else PALE,
                    outline=NAVY if first else BLUE, color=WHITE if first else NAVY, width=3)
        if i < len(steps)-1:
            my = (y + ys[i+1]) / 2
            c.poly([(cx, my+9), (cx-8, my-5), (cx+8, my-5)], BLUE)
            if step.get('link'):   # the relation sits beside the spine, under the card it follows from
                c.label(step['link'], (cx-22 if left else cx+22, y+ch/2+27), 19, 'mono', NAVY, 'rm' if left else 'lm')
    if s.get('counter'):
        last_left = (len(steps)-1) % 2 == 0
        c.label(s['counter'], (cx+38 if last_left else cx-22, ys[-1]+52), 19, 'mono', MUTED,
                'lm' if last_left else 'rm')


def gate(c, s):
    """Evidence goes into one question. Two outcomes come out. One rule sits under both."""
    x0, y0, w, h = REGION; mid = x0 + w/2
    c.rect((x0, y0, w, 150), fill=NAVY, outline=NAVY, width=0, radius=14, shadow=True)
    c.poly([(x0+60, y0+18), (x0+98, y0+56), (x0+60, y0+94), (x0+22, y0+56)], GOLD_LIGHT)
    c.label('?', (x0+60, y0+56), 36, 'bold', NAVY, 'mm')
    c.text(s['question'], (x0+122, y0+12, w-150, 82), size=31, family='bold', fill=PAPER, valign='middle')
    c.label('DECIDE WITH', (x0+26, y0+121), 18, 'mono', GOLD_LIGHT)
    c.chips(s['evidence'], x0+166, y0+104, w-190, join='plus', join_color=GOLD_LIGHT, size=22, h=34,
            fg=PAPER, bg='#1B3A9E', outline='#4A66C4')
    cardw = 500; cy = y0 + 222; chh = 236
    for i, br in enumerate(s['branches']):
        color, pale, default_icon = TONES[br['tone']]
        x = x0 if i == 0 else x0 + w - cardw; ccx = x + cardw/2
        path = vflow((mid + (-26 if i == 0 else 26), y0+150), (ccx, cy))
        c.arrow(path, color, 4, dash=None if br['tone'] == 'go' else (9, 6))
        lw_ = c.chip_width(br['label'], 21, 'bold', 34, 16)
        px_, py_ = path[len(path)//2]
        c.chip(px_-lw_/2, py_-17, br['label'], 21, 'bold', WHITE, color, color, 34, 16)
        c.rect((x, cy, cardw, chh), fill=WHITE, outline=color, width=2, radius=14, shadow=True)
        c.rect((x, cy, cardw, 14), fill=color, outline=color, width=0, radius=14, corners=(True, True, False, False))
        c.medallion((x+48, cy+62), 28, br.get('icon', default_icon), fill=pale, outline=color, color=color)
        c.text(br['title'], (x+92, cy+26, cardw-114, 72), size=29, family='bold', valign='middle')
        if br.get('chips'):
            c.text(br['detail'], (x+26, cy+106, cardw-52, 90), size=25, fill=MUTED)
            c.chips(br['chips'], x+26, cy+198, cardw-52, fg=color, outline=color, **FINE)
        else:
            c.text(br['detail'], (x+26, cy+106, cardw-52, 120), size=25, fill=MUTED)
        c.line([(ccx, cy+chh+6), (ccx, y0+478)], NAVY, 3)
    cost = s.get('rule_tone') == 'cost'
    edge, pale, ink = (GOLD, GOLD_PALE, '#6B5211') if cost else (NAVY, PALE, NAVY)
    c.rect((x0, y0+478, w, 102), fill=pale, outline=edge, width=2, radius=14)
    c.medallion((x0+50, y0+529), 27, s.get('rule_icon', 'lock'), fill=edge, outline=edge, color=WHITE)
    c.label(s.get('rule_label', 'HOLDS ON BOTH PATHS'), (x0+94, y0+505), 18, 'mono', ink if cost else BLUE)
    c.text(s['rule'], (x0+94, y0+521, w-116, 48), size=27, family='medium', fill=ink)


def ledger(c, s):
    """Each row is a small flow: a thing, what to do with it, and the evidence to keep."""
    x0, y0, w, h = REGION; rows = s['rows']; n = len(rows)
    c1, c2 = 300, 390; xa = x0 + c1; xv = x0 + c1 + c2
    mark = s.get('mark', 'check'); rule = s.get('rule'); pre = s.get('preface'); hy = y0
    cost = s.get('tone') == 'cost'      # gold only where the subject is money
    edge, pale, tint, ink = (GOLD, GOLD_PALE, GOLD_PALE, '#6B5211') if cost else (BLUE, PALE, TINT, NAVY)
    if pre:     # what to have in hand before reading the rows
        pw = c.label(pre['label'], (x0, y0+17), 19, 'mono', BLUE)
        c.chips(pre['chips'], x0+pw+14, y0+2, w-pw-14, join=pre.get('join'), **FINE)
        hy = y0 + 46
    for x, head in ((x0+84, s['columns'][0]), (xa+34, s['columns'][1]), (xv+68, s['columns'][2])):
        c.label(head, (x, hy+18), 19, 'mono', BLUE)
    c.line([(x0, hy+38), (x0+w, hy+38)], BLUE, 2)
    gap = 12; top = hy + 52; rh = (y0 + h - top - (70 if rule else 6) - gap*(n-1)) / n
    for i, row in enumerate(rows):
        y = top + i*(rh+gap); my = y + rh/2
        c.rect((x0, y, w, rh), fill=WHITE, outline=LINE, width=2, radius=14, shadow=True)
        c.rect((xv+24, y+2, w-c1-c2-26, rh-4), fill=tint, outline=None, width=0, radius=12,
               corners=(False, True, True, False))
        c.medallion((x0+44, my), 28, row['icon'], fill=pale, outline=edge, color=ink)
        c.text(row['subject'], (x0+84, y+8, c1-96, rh-16), size=28, family='bold', fill=NAVY, valign='middle')
        c.arrow([(xa-4, my), (xa+20, my)], BLUE, 3, head=11)
        if row.get('hint'):     # what to scan for, in the inspection layer
            lines = len(c.wrap(row['action'], c2-52, 25)); block = lines*29 + 30
            c.text(row['action'], (xa+34, my-block/2, c2-52, lines*29+6), size=25)
            c.label(row['hint'], (xa+34, my-block/2+lines*29+16), 20, 'sans', MUTED)
        else:
            c.text(row['action'], (xa+34, y+8, c2-52, rh-16), size=25, valign='middle')
        c.arrow([(xv-10, my), (xv+14, my)], BLUE, 3, head=11)
        c.icon(mark, xv+46, my, 30, edge)
        c.text(row['evidence'], (xv+68, y+8, w-c1-c2-84, rh-16), size=25, family='medium', fill=ink, valign='middle')
        if s.get('spine') and i < n-1:     # one record travelling through its copies
            c.arrow([(x0+44, y+rh+2), (x0+44, y+rh+gap+8)], BLUE, 3, head=9)
    if rule:
        c.rect((x0, y0+h-58, w, 58), fill=pale, outline=edge if cost else NAVY, width=2, radius=14)
        c.text(rule, (x0+24, y0+h-52, w-48, 46), size=25, family='medium', fill=ink, align='center', valign='middle')


def hub(c, s):
    """One result in the middle. Everything it depends on around it. Each tie needs an owner."""
    x0, y0, w, h = REGION; cx, cy = x0 + w/2, y0 + h/2; cw, ch = 400, 172
    corners = [(x0, y0), (x0+w-cw, y0), (x0, y0+h-ch), (x0+w-cw, y0+h-ch)]
    for x, y in corners:
        sx = x + cw - 76 if x == x0 else x + 76
        sy = y + ch if y == y0 else y
        ex = cx + (-72 if x == x0 else 72); ey = cy + (-80 if y == y0 else 80)
        path = bezier((sx, sy), (sx, (sy+ey)/2), ((sx+ex)/2, ey), (ex, ey))
        c.line(path, BLUE, 3)
        tx, ty = path[len(path)//2 - 6]
        tw = c.chip_width(s['tie'], 18, 'mono', 30, 12)
        c.chip(tx-tw/2, ty-15, s['tie'], 18, 'mono', NAVY, WHITE, MUTED, 30, 12, dash=(5, 4))
    for (x, y), node in zip(corners, s['nodes']):
        c.rect((x, y, cw, ch), fill=WHITE, outline=LINE, width=2, radius=14, shadow=True)
        c.medallion((x+46, y+44), 28, node['icon'])
        c.label(node['title'], (x+88, y+44), 29, 'bold', INK)
        c.text(node['detail'], (x+24, y+78, cw-48, 58), size=24, fill=MUTED)
        if node.get('chips'): c.chips(node['chips'], x+24, y+132, cw-48, **FINE)
    c.circle((cx, cy), 124, fill=None, outline=BLUE, width=2)
    c.circle((cx, cy), 110, fill=NAVY)
    c.text(s['center'], (cx-90, cy-60, 180, 66), size=25, family='bold', fill=WHITE, align='center', valign='middle')
    c.text(s['center_detail'], (cx-84, cy+12, 168, 56), size=21, family='medium', fill=GOLD_LIGHT,
           align='center', valign='middle')
    for note, ny in zip(s.get('notes', []), (y0+26, y0+h-ch+26)):   # margin notes between the cards
        c.text(note, (x0+cw+16, ny, w-2*cw-32, 124), size=20, family='mono', fill=NAVY, align='center')


def strata(c, s):
    """Layers built from the bottom up. The crown is what they hold up, not another layer."""
    x0, y0, w, h = REGION; items = s['items']; crown = s['crown']
    c.rect((x0+150, y0, w-300, 90), fill=WHITE, outline=BLUE, width=2, radius=14, dash=(9, 7))
    c.label(crown['label'], (x0+w/2, y0+26), 18, 'mono', BLUE, 'mm')
    c.label(crown['title'], (x0+w/2, y0+59), 30, 'bold', NAVY, 'mm')
    fills = ('#FFFFFF', '#F1F4FD', '#E3E9FA', '#D3DDF7')
    for row in range(4):
        item = items[3-row]                       # items are listed in build order, first at the bottom
        inset = (3-row)*38; x = x0 + inset; sw = w - 2*inset; y = y0 + 112 + row*100
        c.rect((x, y, sw, 92), fill=fills[row], outline=NAVY, width=2, radius=10, shadow=row == 3)
        c.medallion((x+48, y+46), 27, item['icon'], fill=WHITE)
        c.label(item['title'], (x+92, y+31), 29, 'bold', INK)
        c.label(item['detail'], (x+92, y+65), 24, 'sans', MUTED)
        c.label(f'{4-row:02d}', (x+sw-22, y+31), 19, 'mono', BLUE, 'rm')
    c.arrow([(x0+w/2, y0+112), (x0+w/2, y0+93)], BLUE, 3, head=10)
    c.text(s['rule'], (x0, y0+522, w, 52), size=26, family='medium', fill=NAVY, align='center', valign='middle')


def span(c, s):
    """Time runs left to right. One bracket covers the whole promise. A marker shows what cannot be undone."""
    x0, y0, w, h = REGION; phases = s['phases']; gap = 14; sw = (w - 2*gap) / 3
    c.line([(x0, y0+46), (x0, y0+30), (x0+w, y0+30), (x0+w, y0+46)], NAVY, 2.5)
    tw = c.measure(s['span'], 19, 'mono')
    c.rect((x0+w/2-tw/2-14, y0+14, tw+28, 32), fill=LENS, outline=None, width=0)
    c.label(s['span'], (x0+w/2, y0+30), 19, 'mono', NAVY, 'mm')
    marker = s.get('marker')
    for i, ph in enumerate(phases):
        x = x0 + i*(sw+gap); y = y0 + 58
        after = bool(marker) and i > marker['after']
        fill = CORAL_PALE if after else PALE; edge = CORAL if after else BLUE
        notch = 0 if i == 0 else 20
        c.poly([(x, y), (x+sw-20, y), (x+sw, y+32), (x+sw-20, y+64), (x, y+64), (x+notch, y+32)], fill)
        c.label(ph['label'], (x+sw/2+4, y+32), 25, 'bold', edge if after else NAVY, 'mm')
        c.line([(x+sw/2, y+64), (x+sw/2, y0+166)], edge, 3)
        c.rect((x, y0+166, sw, 330), fill=WHITE, outline=edge if after else LINE, width=2, radius=14, shadow=True)
        c.medallion((x+46, y0+214), 28, ph['icon'], fill=fill, outline=edge, color=edge if after else NAVY)
        c.label(f'{i+1:02d}', (x+sw-20, y0+196), 19, 'mono', edge, 'rm')
        c.text(ph['title'], (x+24, y0+256, sw-48, 70), size=28, family='bold')
        c.text(ph['detail'], (x+24, y0+332, sw-48, 116), size=24, fill=MUTED)
        if ph.get('chips'): c.chips(ph['chips'], x+24, y0+454, sw-48, fg=edge if after else NAVY, **FINE)
    if marker:
        mx = x0 + (marker['after']+1)*(sw+gap) - gap/2
        c.line([(mx, y0+52), (mx, y0+500)], CORAL, 3, dash=(8, 6))
        mw = c.chip_width(marker['label'], 18, 'mono', 30, 12)
        c.chip(mx-mw/2, y0+129, marker['label'], 18, 'mono', WHITE, CORAL, CORAL, 30, 12)
    c.rect((x0, y0+514, w, 66), fill=PALE, outline=NAVY, width=2, radius=14)
    c.text(s['rule'], (x0+24, y0+521, w-48, 52), size=22, family='mono', fill=NAVY, align='center', valign='middle')


def binding(c, s):
    """An approval is tied to the exact thing reviewed. It does not travel to a changed copy."""
    x0, y0, w, h = REGION; v1, v2 = s['versions']; dw, dh = 430, 236; y = y0 + 40
    c.label(s['example_label'], (x0, y0+14), 19, 'mono', MUTED)
    for x, v, color in ((x0, v1, BLUE), (x0+w-dw, v2, CORAL)):
        c.poly([(x, y+6), (x+dw, y+50), (x+dw, y+dh+6), (x, y+dh+6)], SHADOW)
        c.poly([(x, y), (x+dw-44, y), (x+dw, y+44), (x+dw, y+dh), (x, y+dh)], WHITE)
        c.line([(x, y), (x+dw-44, y), (x+dw, y+44), (x+dw, y+dh), (x, y+dh), (x, y)], color, 3)
        c.line([(x+dw-44, y), (x+dw-44, y+44), (x+dw, y+44)], color, 3)
        c.label(v['tag'], (x+26, y+38), 20, 'mono', color)
        c.label(v['amount'], (x+26, y+116), 78, 'bold', NAVY if color == BLUE else CORAL)
        c.label(v['detail'], (x+26, y+194), 26, 'sans', MUTED)
    c.arrow([(x0+dw+14, y+104), (x0+w-dw-14, y+104)], CORAL, 4)
    c.label(s['change'], (x0+w/2, y+74), 19, 'mono', CORAL, 'mm')
    # The seal: a human approval, stamped on version 1 and tied to nothing else.
    sx, sy = x0 + dw - 74, y + dh + 50
    c.circle((sx, sy), 68, fill=WHITE, outline=BLUE, width=3); c.circle((sx, sy), 58, fill=PALE, outline=BLUE, width=2)
    c.icon('person', sx, sy-16, 36, NAVY); c.label(s['seal'], (sx, sy+26), 18, 'mono', NAVY, 'mm')
    rx = x0 + w - dw
    c.line([(sx+70, sy), (rx+14, sy)], CORAL, 3, dash=(8, 6))
    c.icon('stop', rx+38, sy, 34, CORAL)
    c.label(s['block'], (rx+64, sy), 19, 'mono', CORAL)
    stop = s['stop']; gy = y0 + 430
    c.arrow([(x0+w-36, y+dh), (x0+w-36, gy)], CORAL, 4)
    c.rect((x0, gy, w, 150), fill=CORAL_PALE, outline=CORAL, width=3, radius=14)
    c.medallion((x0+58, gy+75), 32, 'stop', fill=CORAL, outline=CORAL, color=WHITE)
    c.text(stop['title'], (x0+112, gy+26, w-140, 44), size=33, family='bold', fill=CORAL)
    c.text(stop['detail'], (x0+112, gy+84, w-140, 40), size=24, family='mono', fill=INK)


RENDERERS = {'lanes':lanes, 'route':route, 'gate':gate, 'ledger':ledger, 'hub':hub, 'strata':strata,
             'span':span, 'binding':binding}


# ---- specification contract ---------------------------------------------------------------

def _need(obj, keys, where):
    if not isinstance(obj, dict): raise ValueError(f'{where} must be an object')
    for key in keys:
        if not isinstance(obj.get(key), str) or not obj[key].strip(): raise ValueError(f'Missing {where}.{key}')

def _count(value, sizes, where):
    if not isinstance(value, list) or len(value) not in sizes:
        raise ValueError(f'{where} needs {" or ".join(map(str, sizes))} entries')

def _icon(name, where):
    if name not in ICONS: raise ValueError(f'Unknown icon in {where}: {name!r}')

def _chips(value, where):
    _count(value, (1, 2, 3, 4, 5), where)
    for chip in value:
        if isinstance(chip, dict):
            _need(chip, ('text',), where)
            if 'icon' in chip: _icon(chip['icon'], where)
        elif not isinstance(chip, str) or not chip.strip(): raise ValueError(f'Invalid chip in {where}')


def validate_layout(spec):
    """Reject a shape the renderer would otherwise draw incompletely."""
    kind = spec['layout']
    if kind == 'lanes':
        _need(spec.get('source'), ('icon', 'title', 'detail'), 'source'); _icon(spec['source']['icon'], 'source')
        _need(spec.get('primary'), ('label',), 'primary'); _count(spec['primary'].get('steps'), (3,), 'primary.steps')
        for step in spec['primary']['steps']:
            _need(step, ('icon', 'title', 'ask'), 'step'); _icon(step['icon'], 'step'); _chips(step.get('chips'), 'step.chips')
            if step.get('join') not in (None, 'arrow', 'plus'): raise ValueError('Invalid chip join')
        _need(spec.get('aside'), ('label', 'title', 'rule'), 'aside'); _count(spec['aside'].get('items'), (3,), 'aside.items')
        for item in spec['aside']['items']: _need(item, ('icon', 'text', 'ask'), 'aside item'); _icon(item['icon'], 'aside item')
        if 'example' in spec['primary']: _need(spec['primary'], ('example',), 'primary')
        _need(spec.get('outcome'), ('icon', 'title', 'detail'), 'outcome'); _icon(spec['outcome']['icon'], 'outcome')
        _chips(spec['outcome'].get('chips'), 'outcome.chips')
    elif kind == 'route':
        _count(spec.get('steps'), (4,), 'steps')
        for step in spec['steps']:
            _need(step, ('icon', 'title', 'detail'), 'step'); _icon(step['icon'], 'step')
            if 'chips' in step: _chips(step['chips'], 'step.chips')
            if set(step) - {'icon', 'title', 'detail', 'chips', 'link'}: raise ValueError('Route step has an undrawn field')
        if 'counter' in spec: _need(spec, ('counter',), 'route')
    elif kind == 'gate':
        _need(spec, ('question', 'rule'), 'gate'); _chips(spec.get('evidence'), 'evidence')
        _count(spec.get('branches'), (2,), 'branches')
        for br in spec['branches']:
            _need(br, ('label', 'tone', 'title', 'detail'), 'branch')
            if br['tone'] not in TONES: raise ValueError('Unknown branch tone')
            if 'icon' in br: _icon(br['icon'], 'branch')
            if 'chips' in br: _chips(br['chips'], 'branch.chips')
        if 'rule_icon' in spec: _icon(spec['rule_icon'], 'rule')
        if spec.get('rule_tone') not in (None, 'cost'): raise ValueError('Unknown rule tone')
    elif kind == 'ledger':
        _count(spec.get('columns'), (3,), 'columns'); _count(spec.get('rows'), (3, 4), 'rows')
        for row in spec['rows']:
            _need(row, ('icon', 'subject', 'action', 'evidence'), 'row'); _icon(row['icon'], 'row')
            if set(row) - {'icon', 'subject', 'action', 'evidence', 'hint'}: raise ValueError('Ledger row has an undrawn field')
            if 'hint' in row: _need(row, ('hint',), 'row')
        _icon(spec.get('mark', 'check'), 'mark')
        if 'preface' in spec:
            _need(spec['preface'], ('label',), 'preface'); _chips(spec['preface'].get('chips'), 'preface.chips')
        if 'rule' in spec: _need(spec, ('rule',), 'ledger')
        if spec.get('tone') not in (None, 'cost'): raise ValueError('Unknown ledger tone')
    elif kind == 'hub':
        _need(spec, ('center', 'center_detail', 'tie'), 'hub'); _count(spec.get('nodes'), (4,), 'nodes')
        for node in spec['nodes']:
            _need(node, ('icon', 'title', 'detail'), 'node'); _icon(node['icon'], 'node')
            if 'chips' in node: _chips(node['chips'], 'node.chips')
        if 'notes' in spec:
            _count(spec['notes'], (1, 2), 'notes')
            if not all(isinstance(n, str) and n.strip() for n in spec['notes']): raise ValueError('Invalid hub note')
    elif kind == 'strata':
        _need(spec, ('rule',), 'strata'); _need(spec.get('crown'), ('label', 'title'), 'crown')
        _count(spec.get('items'), (4,), 'items')
        for item in spec['items']: _need(item, ('icon', 'title', 'detail'), 'item'); _icon(item['icon'], 'item')
    elif kind == 'span':
        _need(spec, ('span', 'rule'), 'span'); _count(spec.get('phases'), (3,), 'phases')
        for ph in spec['phases']:
            _need(ph, ('label', 'icon', 'title', 'detail'), 'phase'); _icon(ph['icon'], 'phase')
            if 'chips' in ph: _chips(ph['chips'], 'phase.chips')
        marker = spec.get('marker')
        if marker is not None:
            _need(marker, ('label',), 'marker')
            if marker.get('after') not in (0, 1): raise ValueError('Marker must follow phase 0 or 1')
    elif kind == 'binding':
        _need(spec, ('example_label', 'change', 'seal', 'block'), 'binding'); _count(spec.get('versions'), (2,), 'versions')
        for v in spec['versions']: _need(v, ('tag', 'amount', 'detail'), 'version')
        _need(spec.get('stop'), ('title', 'detail'), 'stop')


def validate_spec(spec, frozen=False):
    for key in ('slug', 'title', 'subtitle', 'category', 'test', 'boundary', 'alt', 'layout'):
        if not isinstance(spec.get(key), str) or not spec[key].strip(): raise ValueError(f'Missing {key}')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', spec['slug']): raise ValueError('Invalid slug')
    process = spec.get('process')
    if not isinstance(process, dict): raise ValueError('Missing process context')
    if not isinstance(process.get('focus'), str) or process['focus'] not in PROCESS_STAGES:
        raise ValueError('Invalid process focus')
    for key in ('bring_in', 'leave_with'):
        if not isinstance(process.get(key), str) or not process[key].strip():
            raise ValueError(f'Missing process {key}')
    if len(spec['alt']) > 1000: raise ValueError('Alt text exceeds publisher limit of 1000 characters')
    for value in iter_text(spec):
        if any(d in value for d in ('—', '–', ' -- ')): raise ValueError('Public text contains forbidden dash')
    post = spec.get('post')
    if post:
        path = Path(post)
        if path.parent != Path('content/posts') or path.suffix != '.md' or '..' in path.parts: raise ValueError('Invalid post path')
        if path.name[11:-3] != spec['slug']: raise ValueError('Post slug does not match asset slug')
        if not (ROOT/path).is_file(): raise ValueError(f'Post not found: {post}')
    if frozen: return          # a published graphic keeps the shape it was published with
    if spec['layout'] not in LAYOUTS: raise ValueError('Unknown layout')
    validate_layout(spec)


def iter_text(value):
    if isinstance(value, str): yield value
    elif isinstance(value, list):
        for v in value: yield from iter_text(v)
    elif isinstance(value, dict):
        for v in value.values(): yield from iter_text(v)


def render_canvas(spec):
    validate_spec(spec)
    c = Canvas(); frame(c, spec); RENDERERS[spec['layout']](c, spec)
    readable = sum(len(b['text']) for b in c.text_boxes if b['font_size'] >= READABLE)
    total = sum(len(b['text']) for b in c.text_boxes)
    if readable < PHONE_SHARE*total:
        raise LayoutError(f'Only {readable} of {total} characters are {READABLE}px or larger: too much fine print for a phone')
    return c


def render(spec):
    c = render_canvas(spec)
    image = c.image.resize((W, H), Image.LANCZOS)
    output = io.BytesIO(); image.save(output, format='PNG', optimize=True)
    return output.getvalue(), c.text_boxes


def load_specs():
    raw = json.loads(SPEC_PATH.read_text(encoding='utf-8'))
    if raw.get('schema_version') != 2 or not isinstance(raw.get('items'), list): raise ValueError('Unsupported spec schema')
    slugs = [s['slug'] for s in raw['items']]
    if len(set(slugs)) != len(slugs): raise ValueError('Duplicate slug')
    return raw['items']


def post_status(spec):
    """The publisher writes status. Nothing here ever changes it."""
    post = spec.get('post')
    if not post or not (ROOT/post).is_file(): return None
    parts = (ROOT/post).read_text(encoding='utf-8').split('---', 2)
    found = re.search(r'^status:\s*(\S+)\s*$', parts[1] if len(parts) > 2 else '', re.MULTILINE)
    return found.group(1) if found else None


def is_frozen(spec):
    """A graphic that went out with a published post is a record. It is never drawn again."""
    return post_status(spec) == 'published'


def spec_fingerprint(spec):
    canonical = json.dumps(spec, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def input_fingerprints():
    renderer_path = Path(__file__).resolve()
    return {
        'renderer':{'path':str(renderer_path.relative_to(ROOT)),
                    'sha256':hashlib.sha256(renderer_path.read_bytes()).hexdigest()},
        'fonts':{str((FONTS/name).relative_to(ROOT)):hashlib.sha256((FONTS/name).read_bytes()).hexdigest()
                 for name in sorted(set(FONT_FILES.values()))},
    }


def manifest_entry(spec, asset_hash, renderer_hash=None):
    return {'slug':spec['slug'], 'post':spec.get('post'),
            'asset':'content/images/'+spec['slug']+'.png', 'alt':spec['alt'],
            'layout':spec['layout'], 'process':spec['process'], 'sha256':asset_hash,
            'spec_sha256':spec_fingerprint(spec),
            'renderer_sha256':renderer_hash or input_fingerprints()['renderer']['sha256'],
            'source':'content/infographics/specs.json'}


def verify_manifest(manifest, specs):
    """Verify reviewed assets and every rendering input without requiring identical rasterizers."""
    if (manifest.get('schema_version'), manifest.get('width'), manifest.get('height')) != (1, W, H):
        raise ValueError('Manifest schema or dimensions are stale')
    if manifest.get('inputs') != input_fingerprints():
        raise ValueError('Renderer source or bundled font inputs changed; regenerate and review assets')
    entries = manifest.get('items', [])
    if len(entries) != len(specs): raise ValueError('Manifest item coverage is stale')
    for spec, entry in zip(specs, entries):
        if is_frozen(spec):
            # Published: the recorded renderer may be an older one, but the spec and bytes may not move.
            if entry != manifest_entry(spec, entry.get('sha256'), entry.get('renderer_sha256')):
                raise ValueError(f'Published graphic or its specification changed: {spec["slug"]}')
        elif entry != manifest_entry(spec, entry.get('sha256')):
            raise ValueError(f'Specification or manifest metadata changed: {spec["slug"]}')
        destination = ROOT/entry['asset']
        if not destination.is_file(): raise ValueError(f'Asset missing: {entry["asset"]}')
        data = destination.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f'Asset hash mismatch: {entry["asset"]}')
        with Image.open(io.BytesIO(data)) as image:
            if image.format != 'PNG' or image.size != (W, H) or image.mode != 'RGB':
                raise ValueError(f'Invalid asset format or dimensions: {entry["asset"]}')
            image.verify()


def frozen_entry(spec, previous):
    """Carry a published graphic's receipt forward untouched, with the renderer that drew it."""
    validate_spec(spec, frozen=True)
    old = {e['slug']: e for e in previous.get('items', [])}.get(spec['slug'])
    if not old: raise ValueError(f'Published post has no reviewed manifest entry: {spec["slug"]}')
    entry = dict(old)
    entry.setdefault('renderer_sha256', previous.get('inputs', {}).get('renderer', {}).get('sha256'))
    if entry != manifest_entry(spec, entry.get('sha256'), entry.get('renderer_sha256')):
        raise ValueError(f'Published graphic specification changed: {spec["slug"]}')
    return entry


def write_previews(directory, rendered):
    """Full-size and phone-size copies for review. These never touch the published asset path."""
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    for slug, data in rendered:
        (directory/f'{slug}.png').write_bytes(data)
        with Image.open(io.BytesIO(data)) as image:
            image.resize((PHONE_WIDTH, round(PHONE_WIDTH*H/W)), Image.LANCZOS).save(directory/f'{slug}.phone.png')
        print(f'preview {directory/slug}.png and .phone.png')


def build(check=False, only=None, preview=None):
    items = []; prepared = []; specs = load_specs()
    previous = json.loads(MANIFEST_PATH.read_text(encoding='utf-8')) if MANIFEST_PATH.exists() else {}
    for spec in specs:
        if is_frozen(spec):
            if only == spec['slug']: raise ValueError('That post is published. Its graphic is a record and stays as it is.')
            items.append(frozen_entry(spec, previous)); continue
        # Preflight every layout before changing files: one overflow must not leave a partial batch.
        data, boxes = render(spec)
        asset = 'content/images/'+spec['slug']+'.png'
        items.append(manifest_entry(spec, hashlib.sha256(data).hexdigest()))
        if not only or spec['slug'] == only:
            prepared.append((asset, data, boxes))
    if only and not prepared: raise ValueError('Requested slug was not found')
    if preview:
        write_previews(preview, [(Path(asset).stem, data) for asset, data, _ in prepared])
        return None
    if check:
        # The renders above still check every text bound. Reviewed PNG bytes are checked
        # against their receipt, not this machine's FreeType/PNG implementation.
        verify_manifest(previous, specs)
        for asset, data, boxes in prepared:
            print(f'checked {asset}: source hashes, asset hash, {len(boxes)} text regions')
        for entry in (e for spec, e in zip(specs, items) if is_frozen(spec)):
            print(f'checked {entry["asset"]}: published record, asset hash only')
        return previous
    for asset, data, boxes in prepared:
        destination = ROOT/asset
        destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(data)
        print(f'rendered {asset}: {len(boxes)} text regions')
    manifest = {'schema_version':1, 'width':W, 'height':H, 'inputs':input_fingerprints(), 'items':items}
    if not only:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true'); ap.add_argument('--slug')
    ap.add_argument('--preview', metavar='DIR', help='write full and phone-size review copies to DIR only')
    args = ap.parse_args(); build(args.check, args.slug, args.preview)
