"""SHAMS AI Atlas: the second scene, "How a model is made", drawn as reviewable SVG.

Same vocabulary as the flagship scene (atlas_scene.py): explicit fallback fills, a Picture layer and an
Architecture layer per object, typed edges, solid figures for people. Sub-parts that teach their own
concept carry data-sc. Numbers drawn here are illustrative.
"""
from atlas_scene import E, T, path, rect, circ, person, obj, abox, W, H

DEFS = ('<defs>'
        '<marker id="ar-ctrl" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#1F45C8" class="mk-ctrl"/></marker>'
        '<marker id="ar-data" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6"><circle cx="5" cy="5" r="4" fill="#0E1012" class="mk-data"/></marker>'
        '<marker id="ar-own" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10" fill="none" stroke="#6B737A" stroke-width="1.6" class="mk-own"/></marker>'
        '</defs>')


def ellipse(cx, cy, rx, ry, cls="ln", **kw):
    return E("ellipse", cls, cx=cx, cy=cy, rx=rx, ry=ry, **kw)


def dial(x, y, a):
    """A small parameter dial; a is the needle end offset."""
    return circ(x, y, 15, "card") + path(f"M{x} {y} L{x + a[0]} {y + a[1]}", "acc") + circ(x, y, 2.5, "ink")


def scene():
    o = [DEFS]
    # ---------------- regions (orientation only, not boundaries)
    o.append('<g class="region">' +
             rect(20, 30, 240, 670, "thin", rx=12) + T(34, 50, "FRAME AND DATA", "t-m") +
             rect(272, 30, 612, 670, "thin", rx=12) + T(290, 50, "PRETRAINING · THE TRAINING LOOP", "t-m") +
             rect(896, 30, 370, 670, "thin", rx=12) + T(912, 50, "AFTER PRETRAINING", "t-m") + '</g>')

    # ---------------- AI rings (ml and deep are their own sub-parts)
    rings = (ellipse(140, 150, 108, 76, "card") + T(140, 92, "AI", "t-m", "middle") +
             f'<g data-sc="ml">{ellipse(140, 158, 90, 58, "sunk")}{T(140, 116, "MACHINE LEARNING", "t-m", "middle", font_size="9.5")}</g>' +
             f'<g data-sc="deep">{ellipse(140, 170, 64, 38, "card")}{T(140, 149, "DEEP LEARNING", "t-m", "middle", font_size="9.5")}</g>' +
             ellipse(140, 186, 32, 15, "accf") + T(140, 191, "LLM", "t-c", "middle", font_size="12"))
    o.append(obj("ai_rings", "ai", rings, abox(36, 80, 208, 144, "Taxonomy", "AI > ML > deep learning\n> large language models\n(nested, overlapping)"), ["scope"]))

    # ---------------- corpus with representation bars and held-out slice
    shelves = rect(40, 262, 200, 160, "card", rx=4) + T(40, 254, "TEXT CORPUS · UNLABELED", "t-m", font_size="11")
    for r, y0 in enumerate((278, 328, 378)):
        shelves += path(f"M48 {y0 + 40} H232", "ln")
        x = 54
        for i, (w, h) in enumerate([(10, 34), (14, 30), (8, 36), (12, 28), (16, 32), (9, 35), (13, 29), (10, 33), (15, 31), (8, 34), (12, 30), (11, 36)]):
            if x + w > 228: break
            shelves += rect(x, y0 + 40 - h, w, h, "accf" if (i + r) % 5 == 2 else "card", rx=1)
            x += w + 3
    even = [40, 36, 32, 30, 28]; skew = [62, 14, 10, 8, 6]
    def bars(hs, cls):
        return f'<g class="{cls}">' + "".join(rect(56 + i * 34, 528 - h, 22, h, "accf" if i else "card", rx=2) for i, h in enumerate(hs)) + "</g>"
    rep = (f'<g data-sc="bias">' + T(40, 452, "WHO IS REPRESENTED", "t-m", font_size="11") + rect(40, 460, 200, 78, "card", rx=4) +
           bars(even, "bars-even") + bars(skew, "bars-skew") + path("M50 528 H230", "ln") + "</g>")
    held = (rect(40, 560, 200, 54, "goldf", rx=4) + T(52, 582, "HELD-OUT SLICE", "t-m", font_size="11") + T(52, 602, "never trained on", "t-s", font_size="13"))
    o.append(obj("corpus", "data", shelves + rep + held,
                 abox(36, 262, 208, 352, "Dataset store", "sources and licences\nfilters, dedup\nowners per source\nrepresentation profile\n\nheld-out split\n(evaluation only)"), ["anchor"]))

    # ---------------- tokenizer
    toks = [("The", 26), ("lamp", 32), ("arr", 24), ("ived", 30), ("crack", 34), ("ed", 22)]
    tk = (rect(290, 76, 180, 104, "card", rx=4) + T(300, 70, "TOKENIZER", "t-m", font_size="11") +
          rect(300, 86, 164, 24, "sunk", rx=3) + T(306, 103, "The lamp arrived cracked", "t-s", font_size="12") +
          path("M300 120 H460", "dash"))
    x = 300
    for t, w in toks:
        tk += rect(x, 132, w - 3, 26, "accf", rx=3) + T(x + (w - 3) / 2, 149, t, "t-c", "middle", font_size="9.5", letter_spacing="0")
        x += w
    tk += T(300, 174, "6 tokens with this tokenizer", "t-s", font_size="11")
    o.append(obj("tokenizer", "token", tk, abox(290, 76, 180, 104, "Tokenizer", "text to token ids\nfixed vocabulary"), ["measure"]))

    # ---------------- embedding map
    em = rect(290, 212, 180, 150, "card", rx=4) + T(290, 204, "EMBEDDINGS", "t-m", font_size="11")
    em += path("M302 350 H460 M302 350 V224", "thin")
    pts = [(326, 244, "cracked"), (350, 266, "broken"), (318, 288, "damaged"), (414, 300, "refund"), (402, 326, "order"), (420, 240, "lamp")]
    for i, (px, py, lab) in enumerate(pts):
        em += circ(px, py, 4.5, "accf" if i < 3 else "ink") + T(px + 8, py + 4, lab, "t-s", font_size="11")
    em += ellipse(344, 266, 40, 36, "dash") + T(300, 356, "2 of many axes", "t-s", font_size="10")
    o.append(obj("embedmap", "embed", em, abox(290, 212, 180, 150, "Embedding table", "token id to vector\nlearned in training\nhundreds of dimensions"), ["anchor"]))

    # ---------------- transformer stack: attention panels and network meshes are sub-parts
    net = T(500, 70, "TRANSFORMER", "t-m", font_size="11")
    ys = [80, 160, 240, 342]
    for bi, y in enumerate(ys):
        net += rect(500, y, 190, 66, "sunk", rx=5) + T(508, y + 14, ("BLOCK 1", "BLOCK 2", "BLOCK 3", "BLOCK N")[bi], "t-m", font_size="9")
        att = rect(508, y + 20, 82, 40, "card", rx=3)
        for k in range(5):
            att += circ(518 + k * 16, y + 52, 3, "ink")
        att += "".join(path(f"M550 {y + 30} L{518 + k * 16} {y + 49}", "acc", stroke_width=str(0.8 + (2.4 if k == 1 else 0.4 * k))) for k in range(5))
        att += circ(550, y + 30, 4, "accf")
        net += f'<g data-sc="attention">{att}</g>'
        mesh = rect(598, y + 20, 84, 40, "card", rx=3)
        cols = [(612, [30, 50]), (640, [26, 40, 54]), (668, [30, 50])]
        for ci in range(2):
            for a in cols[ci][1]:
                for b in cols[ci + 1][1]:
                    mesh += path(f"M{cols[ci][0]} {y + a} L{cols[ci + 1][0]} {y + b}", "thin")
        for cx, rows in cols:
            for a in rows:
                mesh += circ(cx, y + a, 3.2, "card")
        net += f'<g data-sc="nn">{mesh}</g>'
    net += T(595, 324, "· · ·", "t-h", "middle")
    net += f'<g data-sc="deep">{path("M496 150 H491 V404 H496", "ln")}{T(474, 284, "×N", "t-m", font_size="11")}</g>'
    net += (rect(500, 418, 190, 46, "card", rx=4) + T(508, 434, "SCORES FOR THE NEXT TOKEN", "t-m", font_size="9") +
            T(508, 454, "cracked .12 · broken .09", "t-c", font_size="11"))
    o.append(obj("network", "transformer", net, abox(500, 80, 190, 384, "Transformer", "N x (attention + MLP)\nresidual stream\n\noutput: probability\nfor every token in\nthe vocabulary"), ["measure"]))

    # ---------------- parameter dials
    dl = rect(720, 76, 140, 208, "card", rx=4) + T(720, 70, "PARAMETERS", "t-m", font_size="11")
    needles = [(9, -11), (-12, -8), (13, 4), (-6, -13), (11, -9), (-13, 5), (4, -14), (-10, -10)]
    for i, (dx, dy) in enumerate([(758, 108), (822, 108), (758, 150), (822, 150), (758, 192), (822, 192), (758, 234), (822, 234)]):
        dl += dial(dx, dy, needles[i])
    dl += T(732, 274, "8 drawn · billions real", "t-s", font_size="11")
    o.append(obj("dials", "parameters", dl, abox(720, 76, 140, 208, "Weights", "tensors set by\nthe optimizer;\nfixed after release"), ["sustain"]))

    # ---------------- one neuron, enlarged
    nz = rect(720, 304, 140, 160, "card", rx=4) + T(720, 298, "ONE UNIT, ENLARGED", "t-m", font_size="11")
    for i, (yy, w, ly) in enumerate([(330, "×0.9", -6), (376, "×0.4", -6), (420, "×−0.3", 16)]):
        nz += circ(738, yy, 8, "card") + path(f"M746 {yy} L787 386", "ln") + T(748, yy + ly, w, "t-c", font_size="10")
    nz += circ(800, 386, 14, "accf") + T(800, 391, "Σ", "t-h", "middle", font_size="15") + path("M814 386 H832", "ln") + rect(832, 376, 20, 20, "card", rx=3) + T(842, 391, "f", "t-b", "middle")
    nz += T(800, 452, "output 0.43", "t-s", "middle", font_size="11")
    o.append(obj("neuron_zoom", "neuron", nz, abox(720, 304, 140, 160, "Unit", "y = f(w · x + b)"), ["measure"]))

    # ---------------- training loop: predict, compare, adjust (backprop), with the recipe card
    lp = rect(290, 540, 410, 150, "sunk", rx=8) + T(302, 560, "TRAINING LOOP", "t-m", font_size="11")
    lp += rect(302, 572, 116, 58, "card", rx=4) + T(312, 592, "PREDICT", "t-m", font_size="10") + T(312, 612, "'arrived ___'", "t-s", font_size="12")
    lp += rect(434, 572, 116, 58, "card", rx=4) + T(444, 592, "COMPARE", "t-m", font_size="10") + T(444, 612, "loss = 2.12", "t-c", font_size="12")
    lp += (f'<g data-sc="backprop">' + rect(566, 572, 122, 58, "accf", rx=4) + T(576, 592, "ADJUST", "t-m", font_size="10") +
           T(576, 612, "backpropagate", "t-s", font_size="12") + "</g>")
    lp += path("M420 601 H430", "ln", marker_end="url(#ar-ctrl)") + path("M552 601 H562", "ln", marker_end="url(#ar-ctrl)")
    lp += path("M627 632 C 627 652, 360 652, 360 634", "dash", marker_end="url(#ar-ctrl)") + T(494, 650, "again", "t-s", "middle", font_size="12")
    lp += f'<g data-sc="algorithm">{rect(302, 658, 270, 24, "card", rx=3)}{T(312, 675, "RECIPE v3 · predict, compare, adjust", "t-c", font_size="11")}</g>'
    o.append(obj("loop", "training", lp, abox(290, 540, 410, 150, "Training job", "forward pass, loss, backward pass,\noptimizer step; checkpoints saved\non a schedule"), ["measure"]))

    # ---------------- loss chart: held-out curve differs when overfitting
    lc = rect(720, 540, 150, 150, "card", rx=4) + T(720, 534, "LOSS", "t-m", font_size="11")
    lc += path("M734 648 H858 M734 648 V552", "thin")
    lc += path("M736 560 C 760 610, 790 630, 856 640", "ln")
    lc += f'<g class="ho-good">{path("M736 566 C 762 612, 792 628, 856 634", "acc", stroke_dasharray="5 4")}</g>'
    lc += f'<g class="ho-bad">{path("M736 566 C 762 612, 784 620, 800 616 C 820 610, 840 590, 856 574", "acc", stroke_dasharray="5 4")}</g>'
    lc += T(734, 666, "solid: training", "t-s", font_size="10") + T(734, 682, "dashed: held out", "t-s", font_size="10")
    o.append(obj("losschart", "training", lc, abox(720, 540, 150, 150, "Metrics", "train loss\nheld-out loss"), ["measure"]))

    # ---------------- checkpoint cartridge
    ck = (path("M912 84 H1046 L1058 96 V146 H912 Z", "card") + rect(924, 98, 46, 34, "accf", rx=3) +
          T(982, 108, "CHECKPOINT", "t-m", font_size="10") + T(982, 128, "base-v0", "t-c", font_size="13") +
          T(912, 166, "architecture + learned parameters", "t-s", font_size="11"))
    o.append(obj("checkpoint", "checkpoint", ck, abox(912, 84, 146, 62, "Checkpoint", "weights + config"), ["sustain"]))

    # ---------------- fine-tuning with supervised pairs
    ft = rect(912, 186, 340, 92, "card", rx=4) + T(924, 206, "FINE-TUNING · WORKED EXAMPLES", "t-m", font_size="10")
    pairs = ""
    for i, (q, a) in enumerate([("'Lamp arrived cracked'", "asks order no. + photos"), ("'Where is my refund?'", "checks status, no promise")]):
        y = 216 + i * 30
        pairs += rect(924, y, 140, 24, "sunk", rx=3) + T(930, y + 16, q, "t-s", font_size="11") + path(f"M1068 {y + 12} H1082", "ln", marker_end="url(#ar-ctrl)") + rect(1086, y, 156, 24, "accf", rx=3) + T(1092, y + 16, a, "t-s", font_size="11")
    ft += f'<g data-sc="supervised">{pairs}</g>'
    o.append(obj("ft_station", "finetune", ft, abox(912, 186, 340, 92, "SFT job", "prompt and response pairs\nfrom base-v0 to sft-v1"), ["anchor", "measure"]))

    # ---------------- preference training: two answers, a person choosing, written principles
    al = rect(912, 300, 340, 132, "card", rx=4) + T(924, 320, "PREFERENCE TRAINING", "t-m", font_size="10")
    al += rect(924, 332, 96, 56, "sunk", rx=3) + T(932, 350, "A", "t-h", font_size="13") + path("M932 362 H1010 M932 374 H996", "thin")
    al += rect(1028, 332, 96, 56, "accf", rx=3) + T(1036, 350, "B", "t-h", font_size="13") + path("M1036 362 H1114 M1036 374 H1100", "thin") + T(1112, 352, "✓", "t-c", "middle", font_size="15")
    al += person(1152, 404, 0.62) + T(1152, 422, "rater", "t-s", "middle", font_size="11")
    al += rect(1178, 332, 66, 56, "goldf", rx=3) + T(1211, 350, "PRINCIPLES", "t-m", "middle", font_size="8") + path("M1186 364 H1236 M1186 372 H1230 M1186 380 H1224", "thin")
    al += T(924, 408, "B preferred; the model is", "t-s", font_size="11") + T(924, 422, "shifted toward answers like B", "t-s", font_size="11")
    o.append(obj("align_station", "alignment", al, abox(912, 300, 340, 132, "Preference training", "ranked pairs to preference model\nRL toward preferred outputs\n(human or AI feedback)"), ["harden", "scope"]))

    # ---------------- evaluation bench with three status marks
    ev = rect(912, 452, 340, 118, "card", rx=4) + T(924, 472, "EVALUATION · BEFORE RELEASE", "t-m", font_size="10")
    for i, (key, lab) in enumerate([("heldout", "held-out tasks"), ("decline_tests", "requests it should decline"), ("by_group", "quality by group")]):
        y = 490 + i * 26
        ev += rect(924, y, 268, 20, "sunk", rx=3) + T(932, y + 15, lab, "t-s", font_size="12")
        ev += (f'<text class="st-mark" data-key="{key}" x="1216" y="{y + 16}" text-anchor="middle" fill="#1F45C8" '
               f'font-family="IBM Plex Sans, sans-serif" font-size="16" font-weight="600"></text>')
    o.append(obj("eval_bench", "verification", ev, abox(912, 452, 340, 118, "Eval suite", "held-out set, decline tests,\nper-group metrics; gates release"), ["measure", "scope"]))

    # ---------------- release
    rl = (rect(912, 590, 340, 100, "card", rx=4) + T(924, 610, "RELEASE", "t-m", font_size="10") +
          rect(924, 620, 184, 30, "accf", rx=3) + T(934, 640, "assistant-v1 · pinned", "t-c", font_size="12") +
          T(924, 674, "the model card in the flagship scene", "t-s", font_size="11") +
          person(1200, 668, 0.6) + T(1200, 684, "release owner", "t-s", "middle", font_size="10"))
    o.append(obj("release", "model", rl, abox(912, 590, 340, 100, "Model registry", "pinned version served by the API\nrollback to the previous version"), ["sustain", "harden"]))

    # ---------------- training log
    trail = (rect(20, 712, 1246, 72, "card", rx=6) + T(34, 734, "TRAINING LOG · SYNTHETIC", "t-m") + path("M34 762 H1250", "thin") +
             '<g class="ticks"></g><text class="t-c trail-last" x="300" y="734" fill="#1F45C8" font-family="IBM Plex Mono, monospace" font-size="13"></text>')
    o.append(obj("trail", "observability", trail, abox(20, 712, 1246, 72, "Run log", "typed events for this teaching run (synthetic)"), ["sustain"]))

    # ---------------- edges
    def edge(eid, d, kind, label=None, lx=0, ly=0):
        mk = {"data": "url(#ar-data)", "ctrl": "url(#ar-ctrl)", "own": "url(#ar-own)"}[kind]
        stroke = {"data": "#0E1012", "ctrl": "#1F45C8", "own": "#6B737A"}[kind]
        dash = {"data": "", "ctrl": "8 5", "own": "2 5"}[kind]
        da = f' stroke-dasharray="{dash}"' if dash else ""
        s = f'<g class="edge e-{kind}" data-e="{eid}"><path class="ep" d="{d}" fill="none" stroke="{stroke}" stroke-width="2.2"{da} marker-end="{mk}"/>'
        if label: s += T(lx, ly, label, "t-c edge-lab", "middle", font_size="12")
        return s + "</g>"
    E_ = [
        edge("e_corpus_tok", "M242 300 C 262 292, 266 140, 288 132", "data", "text", 258, 220),
        edge("e_tok_embed", "M380 180 L380 210", "data"),
        edge("e_embed_net", "M472 250 C 488 250, 484 112, 498 112", "data", "vectors", 486, 196),
        edge("e_net_pred", "M560 466 C 560 520, 380 512, 362 570", "data", "prediction", 470, 506),
        edge("e_loss_back", "M690 592 C 706 592, 710 560, 710 520 C 710 488, 720 480, 760 480 L 866 480 C 878 480, 880 470, 880 440 L 880 230 C 880 210, 874 200, 864 198", "ctrl", "adjust every dial", 795, 496),
        edge("e_dials_net", "M718 180 L706 180", "ctrl"),
        edge("e_save", "M862 112 L908 112", "data"),
        edge("e_ckpt_ft", "M984 168 L984 184", "data"),
        edge("e_ft_align", "M984 280 L984 298", "data"),
        edge("e_ft_eval", "M1254 232 C 1272 280, 1272 470, 1254 500", "ctrl", "skipped", 1240, 444),
        edge("e_align_eval", "M984 434 L984 450", "data"),
        edge("e_eval_release", "M984 572 L984 588", "data"),
        edge("e_eval_hold", "M910 556 C 892 600, 892 704, 862 704 L 160 704 C 140 704, 140 690, 140 620", "ctrl"),
        edge("e_release_runtime", "M1254 636 L1274 636", "data"),
    ]
    E_[-2] = E_[-2].replace("</g>", T(150, 662, "back to the data", "t-c edge-lab", font_size="12") + "</g>")
    o.append('<g class="edges">' + "".join(E_) + "</g>")
    o.append('<g class="courier" aria-hidden="true"><rect x="-14" y="-10" width="28" height="20" rx="3" fill="#E7EBFB" stroke="#1F45C8" stroke-width="1.6"/><path d="M-8 -3 H8 M-8 3 H5" fill="none" stroke="#1F45C8" stroke-width="1.4"/></g>')
    body = "\n".join(o)
    return (f'<svg class="atlas-scene" id="atlas-scene" viewBox="0 0 {W} {H}" role="img" aria-labelledby="atlas-scene-t atlas-scene-d" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<title id="atlas-scene-t">How a model is made</title>'
            f'<desc id="atlas-scene-d">A teaching drawing in three columns. On the left, nested rings place large language models inside deep learning, '
            f'machine learning and AI, above shelves of text, a chart of who is represented and a held-out slice. In the middle, a tokenizer cuts text '
            f'into tokens, an embedding map turns them into numbers, a stack of transformer blocks with attention and small networks scores the next token, '
            f'parameter dials and one enlarged unit sit beside it, and a training loop predicts, compares and adjusts, with a loss chart. On the right, '
            f'the saved base model goes through fine-tuning, preference training with a person choosing between answers, an evaluation bench and release '
            f'as a pinned version. A text version of every step follows the drawing.</desc>{body}</svg>')


if __name__ == "__main__":
    print(len(scene()))
