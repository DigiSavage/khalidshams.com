"""SHAMS AI Atlas: the flagship workshop scene, drawn as reviewable SVG.

Every shape carries explicit fill/stroke presentation attributes (light-theme fallbacks) so the SVG
renders correctly on its own, e.g. when exported. Site CSS overrides them with theme tokens.
Each object has a Picture layer (.pic) and an Architecture layer (.arch) at the same position.
"""
from html import escape
import re

W, H = 1280, 800

# fallback presentation attributes per style class (light theme)
STY = {
    "ln":   dict(fill="none", stroke="#0E1012", **{"stroke-width": "1.6", "stroke-linecap": "round", "stroke-linejoin": "round"}),
    "thin": dict(fill="none", stroke="#C6C6BF", **{"stroke-width": "1.2", "stroke-linecap": "round"}),
    "card": dict(fill="#FFFFFF", stroke="#0E1012", **{"stroke-width": "1.4", "stroke-linejoin": "round"}),
    "sunk": dict(fill="#EFEFEC", stroke="#0E1012", **{"stroke-width": "1.4", "stroke-linejoin": "round"}),
    "top":  dict(fill="#E9E6DE", stroke="#0E1012", **{"stroke-width": "1.4", "stroke-linejoin": "round"}),
    "acc":  dict(fill="none", stroke="#1F45C8", **{"stroke-width": "1.8", "stroke-linecap": "round", "stroke-linejoin": "round"}),
    "accf": dict(fill="#E7EBFB", stroke="#1F45C8", **{"stroke-width": "1.6"}),
    "gold": dict(fill="none", stroke="#B8912F", **{"stroke-width": "2", "stroke-linecap": "round"}),
    "goldf": dict(fill="#F6EED9", stroke="#B8912F", **{"stroke-width": "1.4"}),
    "ink":  dict(fill="#0E1012", stroke="none"),
    "inkl": dict(fill="#3E4449", stroke="none"),
    "dash": dict(fill="none", stroke="#6B737A", **{"stroke-width": "1.4", "stroke-dasharray": "6 5"}),
}
TXT = {
    "t-h":  dict(fill="#0E1012", **{"font-family": "IBM Plex Sans, system-ui, sans-serif", "font-size": "17", "font-weight": "600"}),
    "t-b":  dict(fill="#3E4449", **{"font-family": "IBM Plex Sans, system-ui, sans-serif", "font-size": "15"}),
    "t-s":  dict(fill="#59616A", **{"font-family": "IBM Plex Sans, system-ui, sans-serif", "font-size": "14.5"}),
    "t-m":  dict(fill="#59616A", **{"font-family": "IBM Plex Mono, ui-monospace, monospace", "font-size": "13", "letter-spacing": "1"}),
    "t-c":  dict(fill="#1F45C8", **{"font-family": "IBM Plex Mono, ui-monospace, monospace", "font-size": "13"}),
    "t-d":  dict(fill="#0E1012", **{"font-family": "Instrument Serif, Georgia, serif", "font-size": "22"}),
}


def A(d):
    return "".join(f' {k}="{escape(str(v), quote=True)}"' for k, v in d.items())


def E(tag, cls="", close=True, inner="", **kw):
    attrs = {}
    for c in cls.split():
        attrs.update(STY.get(c, {}))
        attrs.update(TXT.get(c, {}))
    kw = {k.replace("_", "-"): v for k, v in kw.items()}
    attrs.update(kw)
    if cls:
        attrs["class"] = cls
    if tag == "text" or inner:
        return f"<{tag}{A(attrs)}>{inner}</{tag}>"
    return f"<{tag}{A(attrs)}/>"


def T(x, y, s, cls="t-b", anchor="start", **kw):
    return E("text", cls, inner=escape(s), x=x, y=y, text_anchor=anchor, **kw)


def path(d, cls="ln", **kw): return E("path", cls, d=d, **kw)
def rect(x, y, w, h, cls="card", rx=4, **kw): return E("rect", cls, x=x, y=y, width=w, height=h, rx=rx, **kw)
def circ(x, y, r, cls="ln", **kw): return E("circle", cls, cx=x, cy=y, r=r, **kw)


# ---------------------------------------------------------------- figures
def etch(x, y, w, h=6, step=5):
    """Sparse engraving in a reserved margin, never a texture over the labels."""
    return path(" ".join(f"M{i} {y+h} l{h} {-h}" for i in range(int(x), int(x+w-h), step)),
                "thin studio-etch", stroke_width="0.7", aria_hidden="true")


def person(x, y, s=1.0, label=None, sub=None, pose="review"):
    """A real human: solid coat, profile and hands. Poses share one figure grammar."""
    drawing = [
        path("M-18 0 L-16 -33 Q-15 -47 -5 -50 L6 -50 Q18 -45 19 -31 L22 0 Z", "ink"),
        path("M-5 -51 V-58 H5 V-49 L0 -44 Z", "card"),
        path("M-10 -68 Q-11 -81 0 -80 Q12 -80 11 -66 L14 -62 L9 -60 Q7 -51 -1 -54 Q-10 -56 -10 -68 Z", "card"),
        path("M-11 -66 Q-15 -79 -3 -83 Q9 -85 13 -73 L6 -73 L1 -77 L-4 -69 L-4 -62 L-10 -63 Z", "ink"),
        path("M3 -69 L8 -70 M5 -58 L9 -59", "ln", stroke_width="1"),
        circ(7, -66, 1, "ink"),
        path("M-10 -43 L-3 -31 L1 -43 M-8 -25 L-5 -5", "thin", stroke_width="0.8"),
    ]
    if pose == "hold":
        drawing += [path("M-15 -34 Q-19 -15 0 -17 L20 -23", "ln", stroke_width="7"),
                    path("M14 -24 L24 -27 L27 -22 L17 -19 Z", "card")]
    elif pose == "pause":
        drawing += [path("M13 -36 L27 -27 L31 -47", "ln", stroke_width="7"),
                    path("M28 -45 L27 -58 Q29 -61 31 -57 L33 -61 L36 -60 L36 -46 Z", "card")]
    else:
        drawing += [path("M12 -37 L23 -25 L31 -32", "ln", stroke_width="7"),
                    path("M28 -35 L37 -38 L40 -33 L31 -29 Z", "card")]
    o = [f'<g transform="translate({x} {y}) scale({s})">' + "".join(drawing) + '</g>']
    if label: o.append(T(x, y + 22, label, "t-h", "middle"))
    if sub: o.append(T(x, y + 40, sub, "t-s", "middle"))
    return "".join(o)


def operator(x, y, s=1.0):
    """A software operator: outline figure with a cobalt badge. Represents software behaviour."""
    return "".join([
        circ(x, y - 40 * s, 14 * s, "card"),
        path(f"M{x-24*s} {y} C{x-24*s} {y-16*s} {x-14*s} {y-22*s} {x} {y-22*s} C{x+14*s} {y-22*s} {x+24*s} {y-16*s} {x+24*s} {y}", "card"),
        E("polygon", "accf", points=f"{x-6*s},{y-12*s} {x},{y-16*s} {x+6*s},{y-12*s} {x+6*s},{y-5*s} {x},{y-1*s} {x-6*s},{y-5*s}"),
        path(f"M{x-7*s} {y-42*s} h{14*s} M{x-7*s} {y-36*s} h{8*s}", "thin"),
        path(f"M{x-20*s} {y-3*s} l{6*s} {-7*s} M{x+20*s} {y-3*s} l{-6*s} {-7*s}", "ln"),
    ])



def relief(svg):
    """Give picture-layer instruments real side faces; leave labels and hooks intact.

    Only solid rectangular objects receive depth. Dashed boundaries, empty slots,
    state marks and Architecture-layer boxes must retain their original meaning.
    """
    def raised(match):
        tag = match.group(0)
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        classes = attrs.get('class', '').split()
        if not set(classes) & {'card', 'sunk', 'top', 'accf'} or any(k.startswith('data-') for k in attrs):
            return tag
        try:
            x, y, w, h = (float(attrs[k]) for k in ('x', 'y', 'width', 'height'))
        except (KeyError, ValueError):
            return tag
        if w < 18 or h < 16 or 'slot-doc' in classes:
            return tag
        d = min(4, w * .08, h * .09)
        side = path(f'M{x+w} {y+d} L{x+w+d} {y} V{y+h+d} L{x+w} {y+h} Z', 'sunk studio-side')
        foot = path(f'M{x} {y+h} L{x+d} {y+h+d} H{x+w+d} L{x+w} {y+h} Z', 'top studio-side')
        return '<g class="studio-object">' + side + foot + tag + '</g>'
    return re.sub(r'<rect\b[^>]*/>', raised, svg)


def obj(oid, concept, pic, arch, lens, label=None):
    return (f'<g class="obj" id="o-{oid}" data-o="{oid}" data-c="{concept}" data-lens="{" ".join(lens)}">'
            f'<g class="pic">{relief(pic)}</g><g class="arch">{arch}</g></g>')


def abox(x, y, w, h, title, sub="", ports=()):
    """Architecture-mode box: same footprint, technical label, port dots."""
    o = [rect(x, y, w, h, "card", rx=3), T(x + 10, y + 22, title, "t-h")]
    for i, line in enumerate(sub.split("\n") if sub else []):
        o.append(T(x + 10, y + 42 + i * 17, line, "t-c"))
    for (px, py) in ports:
        o.append(circ(px, py, 4.5, "accf"))
    return "".join(o)


SLOTS = [("instructions", "Instructions"), ("request", "Request"), ("procedure", "Procedure"), ("note", "Saved note"),
         ("policy", "Policy §4.2"), ("order", "Order"), ("refund", "Refund"), ("reply", "Reply")]


def slot_xy(i):
    col, row = i % 4, i // 4
    return 412 + col * 104, 312 + row * 58


SLOT_CENTER = {k: (slot_xy(i)[0] + 48, slot_xy(i)[1] + 25) for i, (k, _) in enumerate(SLOTS)}


def scene():
    o = []
    o.append('<defs>'
             '<marker id="ar-ctrl" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#1F45C8" class="mk-ctrl"/></marker>'
             '<marker id="ar-data" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6"><circle cx="5" cy="5" r="4" fill="#0E1012" class="mk-data"/></marker>'
             '<marker id="ar-own" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10" fill="none" stroke="#6B737A" stroke-width="1.6" class="mk-own"/></marker>'
             '</defs>')
    # ---------------- regions
    o.append(f'<g class="region">'
             f'{rect(205, 30, 725, 660, "dash runtime-wall", rx=14)}'
             f'{T(225, 56, "APPLICATION RUNTIME · EXAMPLE ARCHITECTURE", "t-m")}'
             f'{T(970, 56, "CONNECTED SERVICES", "t-m")}'
             f'{T(20, 56, "PEOPLE", "t-m")}'
             f'</g>')
    # ---------------- people (outside the boundary)
    o.append(obj("owner", "owner",
                 person(98, 250, 1.0, "Accountable owner", "Support operations lead") +
                 rect(40, 82, 116, 50, "card", rx=3) + T(50, 102, "Owns the goal", "t-s") + T(50, 120, "and the policy", "t-s"),
                 abox(22, 82, 160, 190, "Owner", "policy + success\ncriteria (signed)"), ["scope", "sustain"]))
    o.append(obj("requester", "requester",
                 person(80, 600, 1.0, pose="hold") +
                 path("M106 542 L130 542 L141 566 H96 Z", "card") +
                 path("M118 542 L113 552 L124 556 L117 565 M118 567 V583 M106 586 H131", "ln") +
                 T(98, 622, "Requester", "t-h", "middle") + T(98, 640, "Customer, order A-1042", "t-s", "middle") +
                 rect(28, 392, 150, 92, "card", rx=3) + T(38, 414, "TASK BRIEF", "t-m") + T(38, 436, "Lamp arrived cracked.", "t-b", font_size="12.5") +
                 T(38, 455, "Order A-1042.", "t-b") + T(38, 474, "Photos sent Tuesday.", "t-s"),
                 abox(22, 392, 160, 230, "Client app", "authenticated\ncustomer session\nPOST /support"), ["scope"]))
    # ---------------- left column inside runtime: skills, memory, retrieval
    binder = (rect(228, 92, 140, 104, "sunk", rx=4) + rect(240, 104, 22, 80, "card", rx=2) + rect(266, 104, 22, 80, "card", rx=2) +
              rect(292, 104, 22, 80, "card", rx=2) + path("M251 112 V176 M277 112 V176 M303 112 V176", "thin") +
              f'<g transform="rotate(-8 340 150)">{rect(318, 100, 46, 66, "card", rx=2)}{path("M324 114 H356 M324 124 H352 M324 134 H354", "acc")}</g>' +
              T(228, 82, "PROCEDURE BINDER", "t-m") + T(228, 214, "Damaged item v3", "t-s"))
    binder += etch(234, 188, 126)
    o.append(obj("skills", "skills", binder, abox(222, 70, 152, 150, "Skill package", "SKILL.md + scripts\nloaded on match"), ["measure", "sustain"]))
    cab = (rect(236, 262, 124, 110, "sunk", rx=3) + path("M236 298 H360 M236 334 H360", "ln") +
           rect(282, 276, 32, 8, "card", rx=2) + rect(282, 312, 32, 8, "card", rx=2) + rect(282, 348, 32, 8, "card", rx=2) +
           path("M246 252 L298 244 L350 252 V262 H246 Z", "card") + path("M298 244 V262", "thin") +
           T(228, 238, "NOTES CABINET", "t-m") + T(228, 390, "29 Sep · photos ×2", "t-s"))
    cab += etch(242, 362, 110)
    o.append(obj("memory", "memory", cab, abox(222, 226, 152, 172, "Memory store", "per-customer notes\nscoped reads\nfreshness check"), ["anchor", "harden"]))
    shelf = [rect(232, 426, 132, 170, "sunk", rx=3), path("M232 482 H364 M232 538 H364", "ln")]
    xs = [(240, 12, 44), (255, 10, 48), (268, 14, 42), (285, 11, 46), (299, 12, 44), (314, 10, 40), (327, 13, 47), (343, 12, 44)]
    for row, y0 in enumerate([430, 486, 542]):
        for j, (x, w, h) in enumerate(xs):
            cls = "accf" if (row == 1 and j == 4) else "card"
            shelf.append(rect(x, y0 + 50 - h, w, h, cls, rx=1) + path(f"M{x+3} {y0+54-h} v{h-10}", "thin"))
    shelf.append(T(228, 416, "POLICY LIBRARY", "t-m"))
    shelf.append(T(228, 614, "owned · versioned · filtered", "t-s", font_size="10.5"))
    o.append(obj("retrieval", "retrieval", "".join(shelf), abox(222, 402, 152, 220, "Retrieval service", "policy index\npermission filter\nprovenance on hits"), ["anchor"]))
    # ---------------- goal card + dispatch board
    goal = (rect(400, 80, 160, 112, "card", rx=3) + circ(480, 80, 5, "ink") + T(412, 104, "GOAL", "t-m") +
            T(412, 126, "Resolve A-1042", "t-h") + T(412, 144, "within refund policy", "t-s"))
    goal += (f'<g class="crit">' + "".join(
        rect(412 + i * 50, 158, 11, 11, "card", rx=2, **{"data-crit": str(i)}) for i in range(3)) +
        T(412, 186, "3 success criteria", "t-s") + '</g>')
    o.append(obj("goal", "verification", goal, abox(400, 80, 160, 112, "Run goal", "success criteria\nverified from\nrecords"), ["scope", "measure"]))
    board = (rect(400, 204, 160, 60, "card", rx=3) + path("M410 222 H470 M410 236 H458 M410 250 H464", "thin") +
             rect(486, 214, 64, 40, "accf", rx=2) + T(518, 238, "order", "t-c", "middle") + T(400, 280, "DISPATCH BOARD", "t-m"))
    o.append(obj("coordinator", "coordinator", board, abox(400, 204, 160, 60, "Delegation call", "work order schema"), ["scope", "measure"]))
    # ---------------- model engine
    eng = (rect(722, 72, 176, 140, "sunk", rx=8) + rect(736, 88, 66, 50, "card", rx=4) +
           path("M745 130 A24 24 0 0 1 793 130", "ln") + path("M769 130 L784 108", "acc") + circ(769, 130, 3, "ink") +
           rect(816, 92, 66, 16, "card", rx=3) + rect(816, 116, 66, 16, "card", rx=3) +
           T(736, 160, "MODEL", "t-m") + T(736, 180, "replaceable · pinned", "t-s", font_size="12") +
           path("M898 168 H912", "ln"))
    eng += (f'<g class="tokens" data-sc="token">' + "".join(rect(736 + i * 21, 196, 17, 12, "accf", rx=2, **{"data-tk": str(i)}) for i in range(7)) + '</g>')
    eng += f'<text class="t-c proposal" x="736" y="232" fill="#1F45C8" font-family="IBM Plex Mono, ui-monospace, monospace" font-size="13"></text>'
    o.append(obj("model", "model", eng, abox(722, 72, 176, 166, "LLM API", "messages in\ncontent + stop_reason out\nmodel id pinned", [(722, 150), (898, 150)]), ["measure", "sustain"]))
    # ---------------- operator behind the context tray
    op = operator(640, 300, 1.7) + T(640, 180, "AGENT LOOP", "t-m", "middle") + T(640, 196, "software metaphor", "t-s", "middle", font_size="10")
    o.append(obj("agent", "agent", op, abox(578, 208, 124, 62, "Agent loop", "orchestrator code"), ["scope", "harden", "measure", "sustain"]))
    # ---------------- context tray with slots
    tray = [path("M396 286 L834 286 L842 432 L388 432 Z", "top"), T(412, 304, "CONTEXT · THIS CALL ONLY", "t-m")]
    for i, (k, lab) in enumerate(SLOTS):
        x, y = slot_xy(i)
        sc = {"instructions": "sysprompt", "request": "prompt", "reply": "hallucination"}.get(k)
        tray.append(f'<g class="slot" data-slot="{k}"' + (f' data-sc="{sc}"' if sc else '') + '>' + rect(x, y, 96, 50, "dash", rx=4) +
                    rect(x + 40, y + 6, 16, 20, "card slot-doc", rx=2) + T(x + 48, y + 42, lab, "t-s", "middle") + '</g>')
    tray.append(path("M380 432 H850 V446 H380 Z", "sunk") + etch(386, 436, 456, 6, 8))
    o.append(obj("context", "context", "".join(tray), abox(388, 286, 454, 146, "Context assembly", "prompt builder: instructions, request,\nloaded skill, notes, passages, results"), ["anchor"]))
    # ---------------- tool dock + MCP ports
    dock = (rect(852, 286, 62, 146, "sunk", rx=4) + T(852, 446, "TOOLS", "t-m") +
            circ(872, 312, 8, "ln") + path("M878 318 L884 324", "ln") +             # lookup
            circ(872, 357, 9, "card") + T(872, 362, "$", "t-h", "middle") +          # refund
            rect(862, 394, 22, 15, "card", rx=1) + path("M862 394 L873 403 L884 394", "ln"))  # message
    ports = "".join(rect(902, y - 6, 12, 12, "accf", rx=2) for y in (312, 357, 402))
    o.append(obj("tool", "tool", dock, abox(852, 286, 62, 146, "Tools", "schemas"), ["harden"]))
    o.append(obj("mcp", "mcp", ports + T(908, 464, "MCP", "t-m", "middle"),
                 "".join(circ(908, y, 6, "accf") for y in (312, 357, 402)) + T(908, 446, "MCP clients", "t-c", "middle"), ["harden"]))
    # ---------------- pre-call check (guardrail) between the proposal and the gates
    hk = (rect(836, 246, 80, 26, "card", rx=3) + path("M844 253 L850 251 L856 253 V258 Q856 264 850 267 Q844 264 844 258 Z", "ln") +
          T(862, 263, "CHECK", "t-m", font_size="10") +
          '<text class="h-mark" x="906" y="264" text-anchor="middle" fill="#1F45C8" font-family="IBM Plex Sans, sans-serif" font-size="14" font-weight="600"></text>')
    o.append(obj("hook", "guardrails", hk, rect(836, 246, 80, 26, "accf", rx=3) + T(876, 263, "pre-call hook", "t-c", "middle"), ["harden", "measure"]))
    # ---------------- gates on the boundary
    for gid, gy, label in (("gate_orders", 122, "orders:read"), ("gate_refunds", 280, "refunds:issue"), ("gate_msg", 438, "messages:send")):
        g = (rect(921, gy - 26, 18, 52, "card", rx=3) + rect(925, gy - 8, 10, 16, "accf", rx=2) +
             f'<g class="gate-state"><text class="g-mark" x="954" y="{gy + 8}" text-anchor="middle" fill="#1F45C8" font-family="IBM Plex Sans, sans-serif" font-size="18" font-weight="600"></text></g>' +
             T(937, gy - 34, label, "t-m halo", "middle", font_size="9.5"))
        o.append(obj(gid, "authorization", g, rect(915, gy - 28, 30, 56, "accf", rx=3) + T(930, gy - 34, "authz", "t-c", "middle"), ["harden"]))
    # ---------------- services
    for sid, sy, title, sub in (("svc_orders", 72, "Orders", "MCP server"), ("svc_refunds", 230, "Refunds", "MCP server"), ("svc_messaging", 388, "Messaging", "MCP server")):
        st = (rect(976, sy, 150, 104, "sunk", rx=4) + path(f"M976 {sy+30} H1126", "ln") + T(988, sy + 22, title.upper(), "t-m") +
              rect(990, sy + 44, 36, 44, "card", rx=2) + rect(1036, sy + 44, 36, 44, "card", rx=2) + rect(1082, sy + 44, 32, 44, "card", rx=2) +
              T(1134, sy + 60, title, "t-h") + T(1134, sy + 78, sub, "t-s"))
        if sid == "svc_orders":
            st += ('<g class="inj-note" data-sc="injection">' + rect(1094, 106, 30, 22, "card", rx=1, transform="rotate(-6 1109 117)") +
                   path("M1099 113 H1118 M1099 118 H1116 M1099 123 H1112", "thin", transform="rotate(-6 1109 117)") + '</g>')
        o.append(obj(sid, "service", st, abox(976, sy, 290, 104, f"MCP server · {title.lower()}", "tools/list, tools/call\nown authorization", [(976, sy + 52)]), ["harden", "sustain"]))
    # ---------------- approver
    appr = (person(1020, 636, 0.95, pose="pause") + rect(1066, 530, 196, 84, "card", rx=3) + T(1076, 550, "PROPOSED OPERATION", "t-m") +
            T(1076, 572, "issue_refund 84.00", "t-c") + f'<g class="stamp">{rect(1076, 582, 104, 24, "dash", rx=3)}<text class="stamp-t" x="1128" y="599" text-anchor="middle" fill="#1F45C8" font-family="IBM Plex Sans, sans-serif" font-size="13" font-weight="600">awaiting</text></g>' +
            T(1020, 660, "Human approval", "t-h", "middle") + T(1020, 678, "Duty supervisor", "t-s", "middle"))
    o.append(obj("approver", "approver", appr, abox(976, 530, 290, 150, "Approval workflow", "human task queue\ndecision recorded"), ["harden", "scope"]))
    # ---------------- specialist station
    spec = (rect(400, 484, 360, 186, "sunk", rx=6) + T(412, 506, "POLICY SPECIALIST · OWN CONTEXT", "t-m") +
            operator(470, 596, 0.95) + T(470, 612, "software metaphor", "t-s", "middle", font_size="9.5") +
            rect(520, 520, 120, 70, "card", rx=3) + T(530, 540, "WORK ORDER", "t-m") +
            f'<g class="wo-lines">{path("M530 554 H626 M530 566 H612 M530 578 H620", "thin")}</g>' +
            rect(652, 520, 96, 70, "card", rx=3) + T(662, 540, "RESULT", "t-m") +
            f'<g class="res-lines">{path("M662 554 H736 M662 566 H724 M662 578 H730", "thin")}</g>' +
            rect(412, 612, 336, 46, "card", rx=3) + T(424, 632, "retrieve_policy", "t-c") + T(424, 650, "granted", "t-s") +
            path("M572 620 V650", "thin") + T(586, 632, "issue_refund", "t-m") + T(586, 650, "not granted (configured)", "t-s") +
            path("M584 628 L700 628", "ln strike"))
    o.append(obj("specialist", "specialist", spec, abox(400, 484, 360, 186, "Subagent · policy", "own context window\ntools: retrieve_policy only\nidentity: as configured\n(not a sandbox by default)"), ["harden", "measure", "anchor"]))
    # ---------------- budget + recovery
    bud = (rect(780, 484, 134, 82, "card", rx=4) + T(792, 504, "BUDGET", "t-m") + path("M800 552 A26 26 0 0 1 852 552", "ln") +
           path("M826 552 L840 534", "gold needle") + circ(826, 552, 3, "ink") +
           f'<text class="t-c bud-t" x="864" y="548" fill="#1F45C8" font-family="IBM Plex Mono, monospace" font-size="13">0/10</text>')
    o.append(obj("budget", "budget", bud, abox(780, 484, 134, 82, "Run limits", "steps, time, spend"), ["measure", "sustain"]))
    rec = (rect(780, 582, 134, 88, "card", rx=4) + T(792, 602, "HAND-OFF", "t-m") + path("M796 650 H898 L890 664 H804 Z", "sunk") +
           f'<g class="slips">{rect(808, 618, 40, 30, "card", rx=2)}{rect(852, 622, 40, 26, "card", rx=2)}</g>')
    o.append(obj("recovery", "recovery", rec, abox(780, 582, 134, 88, "Handoff queue", "retry policy\ncompensation"), ["sustain"]))
    # ---------------- event trail
    trail = (rect(205, 712, 1061, 72, "card", rx=6) + T(220, 734, "EVENT TRAIL · SYNTHETIC", "t-m") + path("M220 762 H1250", "thin") +
             '<g class="ticks"></g><text class="t-c trail-last" x="440" y="734" fill="#1F45C8" font-family="IBM Plex Mono, monospace" font-size="13"></text>')
    o.append(obj("observability", "observability", trail, abox(205, 712, 1061, 72, "Event log", "run id, typed events, decisions (no model reasoning)"), ["sustain"]))
    # ---------------- edges (typed)
    sc = SLOT_CENTER
    def edge(eid, d, kind, label=None, lx=0, ly=0):
        mk = {"data": "url(#ar-data)", "ctrl": "url(#ar-ctrl)", "own": "url(#ar-own)", "appr": "url(#ar-ctrl)"}[kind]
        stroke = {"data": "#0E1012", "ctrl": "#1F45C8", "own": "#6B737A", "appr": "#1F45C8"}[kind]
        dash = {"data": "", "ctrl": "8 5", "own": "2 5", "appr": "2 4"}[kind]
        da = f' stroke-dasharray="{dash}"' if dash else ""
        s = f'<g class="edge e-{kind}" data-e="{eid}"><path class="ep" d="{d}" fill="none" stroke="{stroke}" stroke-width="2.2"{da} marker-end="{mk}"/>'
        if label: s += T(lx, ly, label, "t-c edge-lab", "middle")
        return s + "</g>"
    E_ = [
        edge("e_request", f"M178 470 C 300 470, 330 350, {sc['request'][0]-30} {sc['request'][1]}", "data", "request", 300, 440),
        edge("e_owner", "M158 96 C 220 40, 400 44, 474 74", "own", "owns the goal", 310, 40),
        edge("e_skill", f"M368 150 C 420 160, 600 250, {sc['procedure'][0]} {sc['procedure'][1]-18}", "data"),
        edge("e_note", f"M362 300 C 420 300, 690 250, {sc['note'][0]} {sc['note'][1]-18}", "data"),
        edge("e_policy", f"M366 508 C 400 500, 420 430, {sc['policy'][0]-30} {sc['policy'][1]}", "data", "passage + provenance", 420, 470),
        edge("e_ctx_model", "M780 286 C 780 260, 800 250, 808 214", "data"),
        edge("e_proposal", "M898 188 C 916 204, 904 228, 888 242", "ctrl"),
        edge("e_check", "M882 270 L882 284", "ctrl"),
        edge("e_call_orders", "M914 312 C 926 300, 916 128, 930 122 L 972 122", "ctrl"),
        edge("e_res_orders", f"M976 160 C 940 190, 760 360, {sc['order'][0]+10} {sc['order'][1]}", "data", "order record", 760, 262),
        edge("e_call_refunds", "M914 357 C 926 350, 918 284, 930 280 L 972 280", "ctrl"),
        edge("e_refund_blocked", "M914 357 C 926 350, 918 290, 921 284", "ctrl", "refused at the gate", 860, 470),
        edge("e_res_refunds", f"M976 314 C 930 340, 760 430, {sc['refund'][0]+10} {sc['refund'][1]+6}", "data", "result", 940, 330),
        edge("e_call_msg", "M914 402 C 926 410, 918 434, 930 438 L 972 438", "ctrl"),
        edge("e_res_msg", f"M976 470 C 940 480, 860 440, {sc['reply'][0]+20} {sc['reply'][1]+16}", "data"),
        edge("e_approval", "M940 300 C 960 380, 990 470, 1062 560", "appr", "approval", 1000, 400),
        edge("e_workorder", "M480 264 C 480 380, 560 420, 580 520", "ctrl", "work order", 560, 470),
        edge("e_spec_policy", "M364 568 C 390 580, 380 610, 412 600", "data"),
        edge("e_spec_result", f"M700 520 C 700 470, 520 440, {sc['policy'][0]+20} {sc['policy'][1]+16}", "data", "result + evidence", 690, 470),
        edge("e_handoff", "M884 432 C 884 470, 860 560, 846 612", "ctrl", "hand-off", 900, 520),
    ]
    o.append('<g class="edges">' + "".join(E_) + '</g>')
    o.append('<g class="courier" aria-hidden="true"><rect x="-14" y="-10" width="28" height="20" rx="3" fill="#E7EBFB" stroke="#1F45C8" stroke-width="1.6"/><path d="M-8 -3 H8 M-8 3 H5" fill="none" stroke="#1F45C8" stroke-width="1.4"/></g>')
    body = "\n".join(o)
    return (f'<svg class="atlas-scene" id="atlas-scene" viewBox="0 0 {W} {H}" role="img" aria-labelledby="atlas-scene-t atlas-scene-d" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<title id="atlas-scene-t">Follow one request through a governed AI system</title>'
            f'<desc id="atlas-scene-d">An example architecture drawn as a workshop. People stand outside the application runtime. '
            f'Inside, an agent operator works at a bench with a goal card, a bounded context tray, a model engine and a tool dock, '
            f'next to a procedure binder, a notes cabinet and a policy library. Tool calls cross the runtime wall through authorization gates '
            f'to connected services. A human approver sits outside the boundary. A policy specialist station, a budget gauge, a hand-off tray '
            f'and an event trail complete the scene. A text version of every step follows the drawing.</desc>{body}</svg>')


if __name__ == "__main__":
    print(len(scene()))
