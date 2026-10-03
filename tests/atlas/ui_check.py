"""Rendered-behaviour checks for the SHAMS AI Atlas (Playwright, Chromium).

Usage:  python build.py && python -m http.server -d dist 8767 &
        python tests/atlas/ui_check.py [base_url] [screenshot_dir]
Exits non-zero if any check fails. Screenshots are written for human review; they are not compared automatically.
"""
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8767"
SHOTS = Path(sys.argv[2] if len(sys.argv) > 2 else "atlas-shots"); SHOTS.mkdir(parents=True, exist_ok=True)
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


async def page(b, w, h, scheme="light", motion="no-preference"):
    ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, reduced_motion=motion, accept_downloads=True)
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("requestfailed", lambda r: errs.append("requestfailed " + r.url))
    return ctx, pg, errs


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        A = BASE + "/learn/atlas/"

        # 1. default load, follow the full default run
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(A); await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("loads without console errors", not errs, "; ".join(errs[:3]))
        for _ in range(20):
            await pg.click("#atl-next") if await pg.is_enabled("#atl-next") else None
        st = await pg.evaluate("window.__atlas.state()")
        check("default run reaches verified completion", st["outcome"] == "completed" and st["idx"] == len(st["steps"]) - 1, st["outcome"])
        check("outcome banner says verified completion", "Verified completion" in await pg.inner_text("#atl-outcome"))
        check("goal criteria ticked", await pg.locator(".crit rect.done").count() == 3)
        await pg.screenshot(path=str(SHOTS / "01-completed-1440.png"))
        # history: back restores the previous step
        await pg.click('[data-view="arch"]'); await pg.go_back(); await pg.wait_for_timeout(300)
        check("browser back restores picture view", "is-arch" not in (await pg.get_attribute("#atlas", "class")))
        await ctx.close()

        # 2. denied action: blocked before execution
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(A + "?x=denyRefund&step=10"); await pg.wait_for_selector('#atlas[data-ready="true"]')
        mark = await pg.text_content('#o-gate_refunds .g-mark')
        check("denied gate shows a cross (non-colour cue)", mark == "✕", repr(mark))
        check("blocked edge drawn to the gate only", await pg.locator('.edge[data-e="e_refund_blocked"].on').count() == 1 and await pg.locator('.edge[data-e="e_call_refunds"].on').count() == 0)
        await pg.screenshot(path=str(SHOTS / "02-denied-1440.png"))
        await pg.click("#atl-next"); await pg.wait_for_timeout(200)
        st = await pg.evaluate("window.__atlas.state()")
        check("denied run ends as 'denied', no refund slot", st["outcome"] == "denied" and await pg.locator('.slot[data-slot="refund"].filled').count() == 0)
        await ctx.close()

        # 2b. planted instruction: the check blocks it before any gate decision
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(A + "?x=injection&step=8"); await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("planted note visible on the Orders record", await pg.locator(".inj-note").is_visible())
        await pg.goto(A + "?x=injection&step=10"); await pg.wait_for_selector('#atlas[data-ready="true"]')
        hm = await pg.text_content("#o-hook .h-mark"); gm = await pg.text_content("#o-gate_refunds .g-mark")
        check("check plate shows a cross and the refund gate shows nothing", hm == "✕" and gm == "", repr((hm, gm)))
        await pg.screenshot(path=str(SHOTS / "02b-injection-1440.png"))
        await pg.click("#atl-next"); await pg.wait_for_timeout(200)
        st = await pg.evaluate("window.__atlas.state()")
        check("injection run ends as 'blocked'", st["outcome"] == "blocked", st["outcome"])
        await pg.goto(A); await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("planted note hidden when the condition is off", not await pg.locator(".inj-note").is_visible())
        await pg.click('.slot[data-slot="instructions"]'); await pg.wait_for_timeout(150)
        f1 = (await pg.evaluate("window.__atlas.state()"))["st"]["focus"]
        await pg.click(".tokens"); await pg.wait_for_timeout(150)
        f2 = (await pg.evaluate("window.__atlas.state()"))["st"]["focus"]
        check("sub-parts select their own concepts (instructions, tokens)", (f1, f2) == ("sysprompt", "token"), repr((f1, f2)))
        check("no page errors (injection)", not errs, str(errs))
        await ctx.close()

        # 2c. reading chapters: the rail reflects the step, jumps keep design, condition and selection, replay approvals are labelled
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(A + "?design=team&x=denyRefund&step=6&focus=authorization"); await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("chapter rail marks the boundary chapter at the read check", await pg.get_attribute('.ch-b[aria-current="step"]', "data-ch") == "boundary")
        await pg.click('.ch-b[data-ch="receipt"]'); await pg.wait_for_timeout(200)
        st = await pg.evaluate("window.__atlas.state()")
        check("chapter jump keeps design, condition, selection; lands on this run's first receipt step", st["st"]["design"] == "team" and st["st"]["denyRefund"] and st["st"]["focus"] == "authorization" and st["steps"][st["idx"]] == "exec_handoff_denied", str(st["steps"][st["idx"]]))
        check("a denied run never shows the receipt chapter as success", st["outcome"] == "denied")
        await pg.goto(A + "?step=11"); await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("recorded approval is labelled as a replay event in the trace", await pg.locator(".t-replay").count() == 1)
        check("inspector's first tab is the trace", (await pg.text_content("#tab-step")).strip() == "Trace")
        check("operators carry a software-metaphor label", await pg.locator("#atlas-scene text:has-text('software metaphor')").count() >= 2)
        rail_h = await pg.evaluate("document.getElementById('atl-chapters').getBoundingClientRect().height")
        check("chapter rail is compact", rail_h < 100, f"{rail_h:.0f}px")
        check("no page errors (chapters)", not errs, str(errs)); await ctx.close()


        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(A + "?design=team&step=10"); await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("specialist shows a filled work order", await pg.locator(".wo-lines.lit").count() == 1)
        txt = await pg.inner_text("#pane-step")
        check("inspector shows structured result with evidence", "approval_required" in txt and "Returns policy v7" in txt)
        await pg.screenshot(path=str(SHOTS / "03-collaborator-1440.png"))
        await pg.click('#o-specialist', position={"x": 60, "y": 40}); await pg.wait_for_timeout(200)
        check("clicking the specialist opens its concept", "Specialist" in await pg.inner_text("#pane-concept"))
        await pg.click('[data-view="arch"]'); await pg.wait_for_timeout(300)
        check("architecture view keeps step and selection", "step=10" in pg.url and "focus=specialist" in pg.url and await pg.locator("#o-specialist .arch").is_visible())
        await pg.screenshot(path=str(SHOTS / "04-collaborator-architecture-1440.png"))
        await ctx.close()

        # 4. lenses, checks, progress, corrupt storage, export, expand
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(A); await pg.evaluate("localStorage.setItem('ks-atlas-v1','{not json')"); await pg.reload()
        await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("corrupt progress storage is tolerated", not errs, "; ".join(errs[:2]))
        await pg.click('.ls-b[data-lens="harden"]')
        hits = await pg.locator(".obj.lens-hit").count()
        check("Harden lens highlights gates, MCP and the specialist", hits >= 6 and await pg.locator("#o-gate_refunds.lens-hit").count() == 1, str(hits))
        await pg.screenshot(path=str(SHOTS / "05-harden-lens-1440.png"))
        await pg.click("#tab-check"); await pg.click('.chk[data-ch="proposal-authz-execution"] button[data-i="1"]')
        prog = json.loads(await pg.evaluate("localStorage.getItem('ks-atlas-v1')"))
        check("passing a check records it separately from 'understood'", "authorization" in prog["passed"] and "authorization" not in prog["understood"])
        async with pg.expect_download() as dl:
            await pg.click("#atl-svg")
        d = await dl.value; path = await d.path(); svg = Path(path).read_text()
        check("SVG export downloads the current view", svg.startswith("<?xml") and "teaching simulation" in svg and "<style" in svg)
        await pg.evaluate("window.scrollTo(0, 300); var b=document.getElementById('atl-expand'); b.focus({preventScroll:true}); b.click();")
        check("expand fills the viewport", "is-expanded" in await pg.get_attribute("#atlas", "class"))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(100)
        y = await pg.evaluate("window.scrollY")
        check("Escape exits and restores scroll and focus", "is-expanded" not in await pg.get_attribute("#atlas", "class") and y == 300 and await pg.evaluate("document.activeElement.id") == "atl-expand", f"y={y}")
        await ctx.close()

        # 5. keyboard only
        ctx, pg, errs = await page(b, 1440, 900, motion="reduce")
        await pg.goto(A); await pg.wait_for_selector('#atlas[data-ready="true"]')
        await pg.focus("#atl-follow"); await pg.keyboard.press("Enter"); await pg.keyboard.press("ArrowRight")
        st = await pg.evaluate("window.__atlas.state()")
        check("keyboard: Enter and ArrowRight advance steps (reduced motion)", st["idx"] == 1, str(st["idx"]))
        tabs = await pg.locator("svg.atlas-scene [tabindex]").count()
        check("SVG objects are not individual tab stops", tabs == 0)
        await ctx.close()

        # 6. layout matrix
        sizes = [(1920, 1080), (2560, 1080), (1440, 900), (1280, 800), (768, 1024), (430, 932), (390, 844), (360, 740), (320, 640)]
        for w, h in sizes:
            for scheme in ("light", "dark"):
                ctx, pg, errs = await page(b, w, h, scheme)
                await pg.goto(A + "?step=9"); await pg.wait_for_selector('#atlas[data-ready="true"]'); await pg.wait_for_timeout(400)
                sw = await pg.evaluate("document.documentElement.scrollWidth")
                svgw = await pg.evaluate("document.getElementById('atlas-scene').getBoundingClientRect().width")
                stage = await pg.evaluate("document.getElementById('atl-stage').getBoundingClientRect().width")
                check(f"{w}x{h} {scheme}: no horizontal overflow, no errors", sw <= w and not errs, f"scrollWidth={sw} " + "; ".join(errs[:2]))
                if w >= 1280:
                    share = stage / w
                    check(f"{w}x{h} {scheme}: stage gets most of the width", share >= 0.6, f"{share:.2f}")
                if scheme == "light" or w in (1440, 390):
                    await pg.screenshot(path=str(SHOTS / f"layout-{w}x{h}-{scheme}.png"))
                await ctx.close()

        # 6b. the second lesson: How a model is made
        M = A + "how-models-are-made/"
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(M); await pg.wait_for_selector('#atlas[data-ready="true"]')
        check("model lesson: no design toggle, its own follow label", await pg.locator("[data-design]").count() == 0 and (await pg.text_content("#atl-follow")).strip() == "Follow the model")
        for _ in range(15): await pg.click("#atl-next" if _ else "#atl-follow"); await pg.wait_for_timeout(60)
        st = await pg.evaluate("window.__atlas.state()")
        marks = await pg.eval_on_selector_all(".st-mark", "els => els.map(e => e.textContent)")
        check("model lesson: default run is released after three passing criteria", st["outcome"] == "released" and marks == ["✓", "✓", "✓"], f"{st['outcome']} {marks}")
        await pg.screenshot(path=str(SHOTS / "10-model-released-1440.png"))
        await pg.goto(M + "?x=skewData&step=14"); await pg.wait_for_selector('#atlas[data-ready="true"]')
        st = await pg.evaluate("window.__atlas.state()")
        marks = await pg.eval_on_selector_all(".st-mark", "els => els.map(e => e.textContent)")
        check("model lesson: skewed data is held back on the by-group criterion", st["outcome"] == "held_back" and marks[2] == "✕" and marks[0] == "", f"{st['outcome']} {marks}")
        check("model lesson: skewed bars shown only under that condition", await pg.locator(".bars-skew").is_visible() and not await pg.locator(".bars-even").is_visible())
        await pg.screenshot(path=str(SHOTS / "11-model-skew-1440.png"))
        await pg.goto(M); await pg.wait_for_selector('#atlas[data-ready="true"]')
        await pg.click('[data-sc="attention"] >> nth=0'); await pg.wait_for_timeout(150)
        f1 = (await pg.evaluate("window.__atlas.state()"))["st"]["focus"]
        await pg.click('[data-sc="backprop"]'); await pg.wait_for_timeout(150)
        f2 = (await pg.evaluate("window.__atlas.state()"))["st"]["focus"]
        check("model lesson: attention panel and adjust station select their concepts", (f1, f2) == ("attention", "backprop"), repr((f1, f2)))
        await pg.click("#o-release"); await pg.wait_for_timeout(150)
        link = pg.locator('#pane-concept a[href^="/learn/atlas/?focus=model"]')
        check("model lesson: the released model links to the flagship scene", await link.count() == 1)
        rail = await pg.eval_on_selector_all(".rl-c", "els => els.length")
        check("model lesson: rail lists only this lesson's concepts", rail == 22, str(rail))
        check("no page errors (model lesson)", not errs, str(errs))
        await ctx.close()
        for w, h in [(1920, 1080), (1280, 800), (768, 1024), (390, 844), (320, 640)]:
            for scheme in ("light", "dark"):
                ctx, pg, errs = await page(b, w, h, scheme)
                await pg.goto(M + "?step=8"); await pg.wait_for_selector('#atlas[data-ready="true"]'); await pg.wait_for_timeout(300)
                sw = await pg.evaluate("document.documentElement.scrollWidth")
                check(f"model lesson {w}x{h} {scheme}: no horizontal overflow, no errors", sw <= w and not errs, f"scrollWidth={sw} " + "; ".join(errs[:2]))
                if w in (1440, 1920, 390): await pg.screenshot(path=str(SHOTS / f"model-{w}x{h}-{scheme}.png"))
                await ctx.close()

        # 7. regression pages
        for path in ["/", "/learn/", "/method/", "/playbooks/", "/playbooks/agentic-ai/", "/tools/", "/tools/availability/", "/writing/"]:
            for w in (1380, 390):
                ctx, pg, errs = await page(b, w, 900)
                await pg.goto(BASE + path); await pg.wait_for_timeout(500)
                sw = await pg.evaluate("document.documentElement.scrollWidth")
                check(f"regression {path} @{w}", sw <= w and not errs, f"sw={sw} " + "; ".join(errs[:2]))
                await ctx.close()
        # search finds the atlas
        ctx, pg, errs = await page(b, 1380, 900)
        await pg.goto(BASE + "/"); await pg.keyboard.press("Control+k"); await pg.keyboard.type("atlas"); await pg.wait_for_timeout(600)
        body = await pg.inner_text("body")
        check("site search lists the atlas", "Atlas" in body or "atlas" in body)
        await ctx.close()
        await b.close()

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    (SHOTS / "results.json").write_text(json.dumps([{"check": n, "ok": o, "detail": d} for n, o, d in results], indent=1))
    sys.exit(1 if failed else 0)

asyncio.run(main())
