"""Vignettes: small scenes composed from the atlas's drawing vocabulary (atlas_scene helpers), for the rest of the site.

Same rules as the atlas: explicit fallback fills so a vignette renders anywhere, site tokens override them through the
`.vig` CSS in base.html, solid figures are people, outline figures are software, cobalt is focus, gold is cost, dashed
lines are boundaries. Each vignette is a function returning the inner SVG for a 320 x 180 viewBox.
"""
from atlas_scene import T as atlas_T, path, rect as atlas_rect, circ, person, operator, etch, E, relief


def rect(x, y, w, h, cls="card", rx=4, **kw):
    surface = atlas_rect(x, y, w, h, cls, rx, **kw)
    if cls in ("card", "sunk", "top") and w >= 40 and h >= 32:
        surface += etch(x+4, y+h-5, w-8, 3, 6)
    return surface

def T(x, y, text, cls="t-b", anchor="start", **kw):
    if cls == "t-m":
        kw.setdefault("letter_spacing", "0.35")
    return atlas_T(x, y, text, cls, anchor, **kw)


VB = (320, 180)


def gate(x, y, mark="", cls="t-c"):
    """A gate on a boundary: post, badge, and a decision mark beside it."""
    g = rect(x - 9, y - 26, 18, 52, "card", rx=3) + rect(x - 5, y - 8, 10, 16, "accf", rx=2)
    if mark: g += T(x + 24, y + 7, mark, cls, "middle", font_size="18", font_weight="600")
    return g


def doc(x, y, w=26, h=32, lines=3, cls="card"):
    d = path(f"M{x+3} {y+3} H{x+w+2} V{y+h+2} H{x+3} Z", "thin") + rect(x, y, w, h, cls, rx=2)
    for i in range(lines): d += path(f"M{x + 5} {y + 8 + i * 7} H{x + w - 5 - (6 if i == lines - 1 else 0)}", "thin")
    return d


def station(x, y, w, h, title):
    return rect(x, y, w, h, "sunk", rx=4) + etch(x+4, y+h-6, w-8, 3, 5) + T(x + 8, y + 15, title, "t-m", font_size="9")


# ---------------------------------------------------------------- scenes
def request():
    """One request through a governed system: person, desk, model, gate, service. The site's signature strip."""
    s = person(34, 128, 0.62) + T(34, 150, "Requester", "t-s", "middle", font_size="10")
    s += rect(86, 30, 150, 124, "dash", rx=8) + T(94, 44, "RUNTIME", "t-m", font_size="8")
    s += operator(132, 128, 0.62) + T(132, 166, "software metaphor", "t-s", "middle", font_size="7")
    s += path("M100 134 L164 134 L168 150 L96 150 Z", "top")   # the desk
    for i in range(3): s += rect(104 + i * 20, 138, 14, 9, "accf" if i < 2 else "dash", rx=1)
    s += rect(180, 52, 48, 40, "sunk", rx=5) + rect(186, 58, 20, 14, "card", rx=2) + path("M189 70 A7 7 0 0 1 203 70", "ln") + path("M196 70 L200 64", "acc") + T(186, 86, "MODEL", "t-m", font_size="7.5")
    s += rect(96, 52, 68, 36, "card", rx=3) + T(102, 65, "GOAL", "t-m", font_size="8") + T(102, 80, "Resolve A-1042", "t-h", font_size="8.5")
    s += gate(252, 100, "✓") + T(252, 66, "GATE", "t-m", "middle", font_size="8")
    s += rect(282, 76, 32, 48, "sunk", rx=3) + rect(288, 86, 20, 10, "card", rx=1) + rect(288, 100, 20, 10, "card", rx=1) + T(298, 136, "Service", "t-s", "middle", font_size="10")
    s += path("M52 110 C 70 100, 80 90, 96 76", "ln", marker_end="url(#vg-data)") + path("M164 70 L178 70", "ln")
    s += path("M166 150 C 200 150, 220 120, 240 104", "acc", stroke_dasharray="6 4") + path("M262 114 L280 114", "acc", stroke_dasharray="6 4")
    return s


def book(x, y, w=38, h=28, selected=False):
    """A small open book, with visible paper edges and a cobalt bookmark."""
    half = w / 2
    c = "accf" if selected else "card"
    s = path(f"M{x} {y+3} Q{x+half/2} {y-2} {x+half} {y+3} Q{x+w-half/2} {y-2} {x+w} {y+3} V{y+h} Q{x+w-half/2} {y+h-4} {x+half} {y+h+1} Q{x+half/2} {y+h-4} {x} {y+h} Z", c)
    s += path(f"M{x+half} {y+3} V{y+h+1} M{x} {y+h+3} Q{x+half/2} {y+h-1} {x+half} {y+h+4} Q{x+w-half/2} {y+h-1} {x+w} {y+h+3}", "ln", stroke_width=".8")
    for row in (8, 13, 18):
        s += path(f"M{x+4} {y+row} Q{x+half/2} {y+row-2} {x+half-4} {y+row} M{x+half+4} {y+row} Q{x+w-half/2} {y+row-2} {x+w-4} {y+row}", "thin", stroke_width=".6")
    return s


def door_new():
    """Six learning stations, in the same order, without pretending progress is earned."""
    pts = [(42, 115), (85, 57), (138, 115), (183, 57), (232, 115), (279, 57)]
    s = T(20, 22, "SIX PATHS · ONE STEP AT A TIME", "t-m", font_size="8")
    for (x, y), (nx, ny) in zip(pts, pts[1:]):
        s += path(f"M{x} {y+22} C{x+25} {y+22} {nx-25} {ny+22} {nx} {ny+22}", "acc", stroke_width="3")
    for i,(x,y) in enumerate(pts):
        s += rect(x-23,y+13,46,20,"sunk",rx=2)
        s += book(x-19,y-9,38,25,selected=i==0)
        s += circ(x,y+31,9,"accf" if i==0 else "card") + T(x,y+34,str(i+1),"t-c","middle",font_size="10",font_weight="600")
    s += T(20,174,"Start with the first book. Build from there.","t-s",font_size="9")
    return s


def door_architect():
    """A review bench faces three decision gates. Gate states remain explicit."""
    s = T(20,22,"WHAT ARE YOU BUILDING?","t-m",font_size="8")
    s += path("M160 35 V151","dash")
    for i,mark in enumerate(("✓","⏸","✕")):
        y=48+i*40
        s += rect(18,y-8,86,26,"card",rx=2) + T(25,y+8,f"Gate 0{i+2}","t-m",font_size="8")
        s += path(f"M106 {y+5} H136","acc",stroke_dasharray="5 3",marker_end="url(#vg-ar)")
        s += rect(144,y-10,8,30,"sunk",rx=1) + rect(184,y-10,8,30,"sunk",rx=1)
        s += rect(152,y-5,32,20,"accf",rx=1) + T(168,y+10,mark,"t-c","middle",font_size="14")
    s += person(258,137,.75,pose="pause")
    s += path("M221 138 H305 L310 154 H216 Z","top")
    s += doc(228,105,43,36,2) + T(249,128,"PROPOSED","t-m","middle",font_size="6")
    s += T(22,174,"Check the boundary before the action.","t-s",font_size="9")
    return s


def door_explore():
    """An open atlas on a drafting board. Routes still connect ideas, not services."""
    s = T(20,22,"IDEAS · CONNECTIONS","t-m",font_size="8")
    s += rect(24,40,272,118,"top",rx=3) + rect(33,47,253,103,"card",rx=2)
    s += path("M159 48 V149","thin")
    pts=[(58,74),(104,117),(133,67),(175,106),(216,131),(236,70),(270,110),(63,139)]
    links=[(0,1),(0,2),(1,2),(2,3),(1,7),(3,4),(3,5),(5,6),(4,6)]
    for a,b in links:
        x,y=pts[a];u,v=pts[b]
        s += path(f"M{x} {y} Q{(x+u)/2} {min(y,v)-10} {u} {v}","acc" if (a,b) in [(0,2),(2,3),(3,5)] else "thin")
    for i,(x,y) in enumerate(pts):
        s += circ(x,y,8,"accf" if i in (0,2,3,5) else "card") + circ(x,y,2,"ink")
    s += T(175,91,"agent","t-c","middle",font_size="8") + T(236,56,"guardrails","t-c","middle",font_size="8")
    s += T(20,174,"Choose an idea. Follow its connections.","t-s",font_size="9")
    return s


def assistant():
    """An assistant that answers from documents: the context tray, a policy card with provenance, the model."""
    s = path("M40 90 L220 90 L226 150 L34 150 Z", "top") + T(48, 104, "CONTEXT · THIS CALL", "t-m", font_size="7.5")
    for i, lab in enumerate(("Request", "Policy §4.2", "Order")):
        x = 48 + i * 58
        s += rect(x, 110, 50, 30, "accf" if i < 2 else "dash", rx=3) + T(x + 25, 131, lab, "t-s", "middle", font_size="8.5")
    s += rect(236, 60, 68, 52, "sunk", rx=5) + rect(244, 68, 26, 18, "card", rx=2) + path("M247 84 A10 10 0 0 1 267 84", "ln") + path("M257 84 L263 75", "acc") + T(244, 104, "MODEL", "t-m", font_size="8")
    s += doc(60, 36, 28, 40, 4) + T(96, 50, "returns-policy v7", "t-c", font_size="8.5") + T(96, 62, "owner · reviewed", "t-s", font_size="8")
    s += path("M74 78 L74 108", "ln", marker_end="url(#vg-data)")
    s += path("M226 120 C 232 120, 232 100, 236 96", "ln")
    return s


def act():
    """An agent acting on records: a proposal, the check plate, the gate, approval, the service."""
    s = rect(14, 56, 96, 50, "card", rx=3) + T(22, 70, "PROPOSAL", "t-m", font_size="7") + T(22, 86, "issue_refund 84.00", "t-c", font_size="7.5") + T(22, 99, "evidence: note, policy", "t-s", font_size="8")
    s += rect(124, 70, 58, 22, "card", rx=3) + path("M130 76 L135 74 L140 76 V81 Q140 85 135 87 Q130 85 130 81 Z", "ln") + T(144, 85, "CHECK", "t-m", font_size="7") + T(172, 85, "✓", "t-c", "middle", font_size="11", font_weight="600")
    s += path("M110 81 L122 81", "acc", stroke_dasharray="5 3")
    s += gate(212, 81, "⏸") + path("M184 81 L200 81", "acc", stroke_dasharray="5 3")
    s += path("M212 108 C 212 130, 240 140, 262 142", "acc", stroke_dasharray="2 4")
    s += person(278, 150, 0.55, pose="pause") + T(278, 170, "Review pending", "t-s", "middle", font_size="9")
    s += rect(266, 30, 44, 44, "sunk", rx=3) + rect(274, 40, 28, 8, "card", rx=1) + rect(274, 54, 28, 8, "card", rx=1) + T(288, 22, "REFUNDS", "t-m", "middle", font_size="7.5")
    s += path("M212 26 V54 M212 108 V156", "dash") + T(150, 148, "not executed", "t-s", "middle", font_size="8")
    return s


def backoffice():
    """A process with handoffs: dispatch board, a work order, a specialist, a hand-off tray."""
    s = rect(24, 40, 100, 50, "card", rx=3) + path("M32 54 H90 M32 66 H78 M32 78 H84", "thin") + rect(94, 48, 24, 20, "accf", rx=2) + T(74, 104, "DISPATCH BOARD", "t-m", "middle", font_size="7.5")
    s += path("M124 66 C 150 66, 160 110, 180 116", "acc", stroke_dasharray="6 4", marker_end="url(#vg-ar)") + T(150, 82, "work order", "t-c", "middle", font_size="8")
    s += station(180, 96, 112, 66, "SPECIALIST") + operator(206, 156, 0.5) + rect(230, 112, 50, 40, "card", rx=2) + path("M236 122 H272 M236 132 H266 M236 142 H270", "thin")
    s += T(236, 174, "software metaphor", "t-s", "middle", font_size="7")
    s += rect(236, 36, 60, 40, "card", rx=3) + T(244, 50, "HAND-OFF", "t-m", font_size="7") + path("M244 68 H288 L284 74 H248 Z", "sunk")
    s += path("M290 128 C 300 110, 300 90, 286 78", "acc", stroke_dasharray="6 4", marker_end="url(#vg-ar)")
    return s


def knowledge():
    """A knowledge system: shelves, a permission filter, a passage with provenance."""
    s = rect(26, 36, 110, 120, "card", rx=3) + T(30, 30, "POLICY LIBRARY", "t-m", font_size="7.5")
    for r in range(3):
        y0 = 44 + r * 36; s += path(f"M34 {y0 + 28} H128", "ln"); x = 38
        for i, (w, h) in enumerate([(7, 24), (10, 20), (6, 26), (9, 18), (11, 22), (7, 25), (9, 20), (8, 24)]):
            s += rect(x, y0 + 28 - h, w, h, "accf" if (i + r) % 4 == 1 else "card", rx=1); x += w + 2
    s += gate(170, 96, "✓") + T(170, 60, "PERMISSION", "t-m", "middle", font_size="7") + T(170, 70, "FILTER", "t-m", "middle", font_size="7")
    s += path("M138 96 L158 96", "ln") + path("M182 104 V116 H206", "ln", marker_end="url(#vg-data)")
    s += rect(212, 66, 92, 60, "card", rx=3) + T(220, 80, "PASSAGE", "t-m", font_size="7") + path("M220 90 H294 M220 99 H286 M220 108 H290", "thin") + T(220, 121, "source · owner · date", "t-c", font_size="6")
    return s


def multi():
    """Hub and spoke: a coordinator and specialists, each with its own context."""
    cx, cy = 160, 92
    pts = [(60, 50), (260, 50), (60, 140), (260, 140), (160, 28)]
    s = "".join(path(f"M{cx} {cy} L{x} {y}", "acc", stroke_dasharray="6 4") for x, y in pts)
    s += circ(cx, cy, 22, "accf") + operator(cx, cy + 14, 0.42) + T(cx, cy + 40, "coordinator", "t-c", "middle", font_size="8.5") + T(cx, cy + 50, "software metaphor", "t-s", "middle", font_size="6.5")
    for x, y in pts:
        s += circ(x, y, 15, "card") + operator(x, y + 10, 0.3)
        s += T(x, y-18, "software metaphor", "t-s", "middle", font_size="5")
    s += T(60, 72, "retrieve only", "t-s", "middle", font_size="7.5") + T(260, 72, "refunds: no", "t-s", "middle", font_size="7.5")
    s += T(160, 170, "n − 1 links, not n(n − 1)/2", "t-m", "middle", font_size="8")
    return s


def decide():
    """The decision: a goal card with an owner, and the autonomy ladder."""
    s = person(44, 120, 0.62) + T(44, 142, "Owner", "t-s", "middle", font_size="10")
    s += rect(84, 40, 110, 64, "card", rx=3) + circ(139, 40, 4, "ink") + T(92, 56, "GOAL", "t-m", font_size="8") + T(92, 72, "Resolve A-1042", "t-h", font_size="10") + T(92, 86, "within refund policy", "t-s", font_size="8.5")
    s += "".join(rect(92 + i * 16, 92, 8, 8, "card", rx=1) for i in range(3))
    s += path("M62 70 C 70 56, 76 50, 84 48", "dash")
    for i in range(5):
        x, h = 214 + i * 20, 24 + i * 22
        s += rect(x, 150 - h, 16, h, "accf" if i == 2 else "sunk", rx=2) + T(x + 8, 164, str(i), "t-m", "middle", font_size="8")
    s += T(254, 34, "AUTONOMY LADDER", "t-m", "middle", font_size="7.5") + T(254, 46, "the rung the estate can carry", "t-s", "middle", font_size="7")
    return s


def cluster_foundations():
    s = E("ellipse", "card", cx=120, cy=92, rx=100, ry=70) + T(120, 36, "AI", "t-m", "middle", font_size="9")
    s += E("ellipse", "sunk", cx=120, cy=100, rx=76, ry=52) + T(120, 62, "MACHINE LEARNING", "t-m", "middle", font_size="8")
    s += E("ellipse", "card", cx=120, cy=110, rx=52, ry=34) + T(120, 90, "DEEP LEARNING", "t-m", "middle", font_size="8")
    s += E("ellipse", "accf", cx=120, cy=120, rx=26, ry=14) + T(120, 124, "LLM", "t-c", "middle", font_size="10")
    s += rect(236, 60, 76, 70, "card", rx=3) + T(238, 54, "DATA", "t-m", font_size="7.5")
    x = 242
    for i, (w, h) in enumerate([(8, 40), (11, 34), (7, 44), (10, 30), (12, 38), (7, 42)]):
        s += rect(x, 120 - h, w, h, "accf" if i % 3 == 1 else "card", rx=1); x += w + 2
    return s


def cluster_learning():
    s = rect(30, 40, 180, 72, "sunk", rx=6) + T(38, 54, "TRAINING LOOP", "t-m", font_size="7.5")
    for i, (lab, sub) in enumerate((("PREDICT", "'arrived ___'"), ("COMPARE", "loss 2.12"), ("ADJUST", "backprop"))):
        x = 38 + i * 58
        s += rect(x, 62, 50, 36, "accf" if i == 2 else "card", rx=3) + T(x + 6, 76, lab, "t-m", font_size="7") + T(x + 6, 90, sub, "t-c" if i == 1 else "t-s", font_size="8")
        if i < 2: s += path(f"M{x + 50} 80 L{x + 58} 80", "ln", marker_end="url(#vg-data)")
    s += path("M200 100 C 200 124, 60 124, 60 102", "dash", marker_end="url(#vg-ar)") + T(130, 132, "again", "t-s", "middle", font_size="8")
    s += rect(230, 40, 70, 90, "card", rx=3) + T(232, 34, "LOSS", "t-m", font_size="7.5") + path("M238 122 H294 M238 122 V50", "thin") + path("M240 54 C 256 100, 270 112, 292 118", "ln") + path("M240 58 C 258 102, 272 112, 292 114", "acc", stroke_dasharray="4 3")
    for i, (dx, dy) in enumerate(((100, 152), (130, 152), (160, 152), (190, 152))):
        s += circ(dx, dy, 10, "card") + path(f"M{dx} {dy} L{dx + (7, -6, 5, -8)[i]} {dy + (-7, -8, 8, -5)[i]}", "acc") + circ(dx, dy, 1.6, "ink")
    s += T(60, 172, "PARAMETERS", "t-m", "middle", font_size="7")
    return s


def cluster_language():
    s = rect(28, 40, 150, 24, "sunk", rx=3) + T(36, 56, "The lamp arrived cracked", "t-s", font_size="10")
    x = 28
    for t, w in (("The", 24), ("lamp", 30), ("arr", 22), ("ived", 28), ("crack", 32), ("ed", 20)):
        s += rect(x, 74, w - 3, 20, "accf", rx=2) + T(x + (w - 3) / 2, 88, t, "t-c", "middle", font_size="8"); x += w
    s += T(28, 112, "6 tokens", "t-s", font_size="8")
    s += rect(200, 36, 100, 118, "sunk", rx=5)
    for b in range(3):
        y = 44 + b * 34
        s += rect(206, y, 40, 26, "card", rx=2) + "".join(circ(212 + k * 7, y + 20, 2, "ink") for k in range(5)) + circ(226, y + 7, 2.6, "accf") + "".join(path(f"M226 {y + 8} L{212 + k * 7} {y + 18}", "acc", stroke_width=str(0.6 + (1.6 if k == 1 else 0.3 * k))) for k in range(5))
        s += rect(252, y, 42, 26, "card", rx=2) + path(f"M260 {y + 6} L274 {y + 13} M260 {y + 20} L274 {y + 13} M274 {y + 13} L286 {y + 8} M274 {y + 13} L286 {y + 18}", "thin")
    s += T(250, 166, "attention · network, ×N", "t-m", "middle", font_size="7")
    s += "".join(rect(28 + i * 15, 128, 11, 8, "accf", rx=1) for i in range(7)) + T(28, 150, "context: the desk for one call", "t-s", font_size="8")
    return s


def cluster_agents():
    s = rect(50, 26, 200, 128, "dash", rx=8) + T(58, 40, "AGENT LOOP", "t-m", font_size="7.5")
    s += operator(110, 118, 0.62) + path("M78 124 L142 124 L146 140 L74 140 Z", "top") + T(110, 152, "software metaphor", "t-s", "middle", font_size="6.5")
    s += "".join(rect(82 + i * 20, 128, 14, 9, "accf" if i < 2 else "dash", rx=1) for i in range(3))
    s += rect(168, 50, 60, 42, "sunk", rx=4) + rect(176, 58, 22, 14, "card", rx=2) + path("M179 70 A8 8 0 0 1 195 70", "ln") + path("M187 70 L192 63", "acc") + T(176, 86, "MODEL", "t-m", font_size="7")
    s += rect(176, 104, 50, 40, "sunk", rx=3) + circ(188, 116, 5, "ln") + circ(188, 132, 5, "card") + T(188, 135, "$", "t-h", "middle", font_size="8") + rect(206, 110, 14, 10, "card", rx=1) + T(201, 154, "TOOLS", "t-m", "middle", font_size="7")
    s += rect(262, 60, 36, 70, "card", rx=3) + path("M268 72 H292 M268 84 H288 M268 96 H290", "thin") + T(280, 142, "memory", "t-s", "middle", font_size="8")
    s += path("M150 132 C 160 132, 164 128, 174 124", "acc", stroke_dasharray="5 3") + path("M150 112 C 158 100, 160 80, 166 72", "ln")
    return s


def cluster_operate():
    s = path("M150 26 V140", "dash")
    s += gate(150, 56, "✓") + gate(150, 104, "✕")
    s += path("M70 56 L132 56", "acc", stroke_dasharray="5 3", marker_end="url(#vg-ar)") + path("M70 104 L132 104", "acc", stroke_dasharray="5 3", marker_end="url(#vg-ar)")
    s += rect(190, 40, 46, 32, "sunk", rx=3) + T(213, 60, "service", "t-s", "middle", font_size="8")
    s += rect(30, 44, 36, 24, "accf", rx=2) + T(48, 59, "id", "t-c", "middle", font_size="9")
    s += rect(240, 86, 64, 44, "card", rx=3) + T(248, 100, "BUDGET", "t-m", font_size="7") + path("M254 122 A14 14 0 0 1 282 122", "ln") + path("M268 122 L276 112", "gold") + T(285, 122, "7/10", "t-c", font_size="6.5")
    s += rect(30, 150, 274, 22, "card", rx=3) + T(36, 164, "EVENT TRAIL", "t-m", font_size="7") + "".join(rect(110 + i * 14, 156, 3, 10, "ink" if i not in (5, 9) else "accf", rx=1) for i in range(13))
    return s


def cluster_decide():
    return decide()


def cluster_society():
    s = rect(40, 40, 240, 100, "card", rx=3) + T(44, 34, "WHO IS REPRESENTED IN THE DATA", "t-m", font_size="7.5")
    for i, h in enumerate((70, 18, 12, 10, 8, 22)):
        s += rect(56 + i * 38, 130 - h, 24, h, "accf" if i else "goldf", rx=2)
    s += path("M48 130 H272", "ln") + T(160, 160, "the average score hides it; measure by group", "t-s", "middle", font_size="8.5")
    return s



def estate():
    """The estate: real systems grouped by ownership, typed dependencies, one link unverified, an architect inspecting."""
    s = rect(26, 34, 150, 118, "dash", rx=8) + T(34, 48, "DOMAIN: ORDERS", "t-m", font_size="7.5")
    s += rect(190, 34, 112, 118, "dash", rx=8) + T(198, 48, "DOMAIN: FINANCE", "t-m", font_size="7.5")
    nodes = {"web": (60, 76, "Storefront"), "api": (120, 76, "Order API"), "db": (90, 126, "Orders DB"), "bill": (246, 70, "Billing"), "ledger": (246, 124, "Ledger")}
    for k, (x, y, lab) in nodes.items():
        s += rect(x - 26, y - 11, 52, 22, "accf" if k == "api" else "card", rx=3) + T(x, y + 4, lab, "t-s", "middle", font_size="8")
    s += path("M86 76 L94 76", "ln", marker_end="url(#vg-dep)") + path("M120 87 L96 115", "ln", marker_end="url(#vg-dep)")
    s += path("M146 76 C 170 76, 190 70, 220 70", "ln", marker_end="url(#vg-dep)")
    s += path("M246 81 L246 113", "ln", marker_end="url(#vg-dep)")
    s += path("M116 126 C 160 140, 190 136, 220 124", "dash", marker_end="url(#vg-dep)") + circ(168, 134, 8, "goldf") + T(168, 137, "?", "t-h", "middle", font_size="10")
    s += T(100, 166, "unverified link: stays unknown", "t-s", "middle", font_size="7.5")
    s += person(286, 172, 0.5) + T(224, 166, "3 known links", "t-c", "middle", font_size="7.5")
    return s


def judgment():
    """Architectural judgment: alternatives against criteria, trade-offs exposed, one recommendation signed."""
    s = rect(30, 36, 196, 112, "card", rx=3) + T(38, 50, "DECISION TABLE \u00b7 OWNER NAMED", "t-m", font_size="7")
    cols = [("A", 92), ("B", 148), ("C", 204)]
    for lab, x in cols:
        s += T(x, 68, lab, "t-h", "middle", font_size="9")
    s += rect(128, 72, 40, 72, "accf", rx=3)
    rows = [("cost", ["\u2713", "\u2713", "\u2715"]), ("risk", ["\u2713", "\u2713", "\u2715"]), ("time", ["\u2713", "\u2715", "\u2715"]), ("fit", ["\u2715", "\u2713", "\u2713"])]
    for i, (lab, marks) in enumerate(rows):
        y = 84 + i * 16
        s += T(38, y, lab, "t-s", font_size="8") + path(f"M36 {y + 5} H220", "thin")
        for (_, x), m in zip(cols, marks):
            s += T(x, y, m, "t-c" if m == "\u2713" else "t-s", "middle", font_size="10")
    s += rect(236, 44, 72, 70, "card", rx=3) + T(244, 58, "RECOMMENDED", "t-m", font_size="7") + T(244, 74, "B: replatform", "t-h", font_size="9")
    s += T(244, 88, "assumption noted", "t-s", font_size="7") + T(244, 98, "revisit trigger set", "t-s", font_size="7")
    s += path("M244 108 C 252 100, 262 112, 272 104 C 280 98, 286 110, 300 104", "acc")
    s += person(272, 172, 0.5)
    s += T(128, 166, "trade-offs shown, one choice owned", "t-s", "middle", font_size="8")
    return s

SCENES = {
    "request": request, "door-new": door_new, "door-architect": door_architect, "door-explore": door_explore,
    "assistant": assistant, "act-on-records": act, "back-office": backoffice, "knowledge": knowledge, "multi-agent": multi, "decide": decide,
    "Foundations": cluster_foundations, "Learning": cluster_learning, "Language": cluster_language, "Agents": cluster_agents,
    "Operate": cluster_operate, "Decide": cluster_decide, "Society": cluster_society,
    "estate": estate, "judgment": judgment,
}

DEFS = ('<defs><marker id="vg-ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M0 0L10 5L0 10z" fill="#1F45C8" class="mk-ctrl"/></marker><marker id="vg-data" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4"><circle cx="5" cy="5" r="3" fill="#0E1012" class="mk-data"/></marker><marker id="vg-dep" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10" fill="none" stroke="#6B737A" class="mk-dep"/></marker></defs>')


def vignette(key: str, cls: str = "", label: str | None = None) -> str:
    """An inline SVG for the named scene. aria-hidden unless a label is given; the text beside it carries the meaning."""
    if key not in SCENES: raise KeyError(f"no vignette {key}")
    w, h = VB
    aria = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    klass = ("vig " + cls).strip()
    return f'<svg class="{klass}" viewBox="0 0 {w} {h}" {aria} xmlns="http://www.w3.org/2000/svg">{DEFS}{relief(SCENES[key]())}</svg>'
