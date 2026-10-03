"""Browser checks for the guided paths, idea pages, architect route and the fluid layout.
Usage: python tests/learn/ui_check.py http://localhost:8767 <screenshot dir>   (serve dist first)"""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8767"
SHOTS = Path(sys.argv[2] if len(sys.argv) > 2 else "shots/learn"); SHOTS.mkdir(parents=True, exist_ok=True)
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


async def page(b, w, h, scheme="light"):
    ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    return ctx, pg, errs


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()

        # 1. progress carries from an idea page to its path, the door on Learn, and an atlas run
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(BASE + "/learn/ideas/ai/?path=what-is-ai"); await pg.wait_for_timeout(300)
        check("idea page shows the path bar", await pg.locator(".pathbar").count() == 1)
        await pg.click("#idea-got"); await pg.wait_for_timeout(100)
        check("I get this writes the map's key", "ai" in (await pg.evaluate("JSON.parse(localStorage.getItem('ks-learn'))")))
        await pg.goto(BASE + "/learn/ideas/ml/?path=what-is-ai"); await pg.wait_for_timeout(200)
        await pg.goto(BASE + "/learn/paths/what-is-ai/"); await pg.wait_for_timeout(300)
        meter = await pg.text_content("#path-meter"); go = await pg.get_attribute("#path-go", "href")
        check("path page counts two stops done and continues at stop 3", meter.startswith("2 of") and "/learn/ideas/deep/?path=what-is-ai" == go, f"{meter} {go}")
        await pg.goto(BASE + "/learn/"); await pg.wait_for_timeout(300)
        check("Learn door continues the current path", (await pg.text_content("#door-continue")).strip() == "Continue path 1" and (await pg.get_attribute("#door-continue", "href")).endswith("deep/?path=what-is-ai"))
        await pg.goto(BASE + "/learn/atlas/?x=denyRefund&step=11&path=running-it-safely"); await pg.wait_for_selector('#atlas[data-ready="true"]'); await pg.wait_for_timeout(300)
        lessons = await pg.evaluate("JSON.parse(localStorage.getItem('ks-atlas-v1')).lessons")
        check("an atlas run followed to its end counts for the path", lessons == ["damaged-order:denied"] and await pg.locator(".pathbar").count() == 1, str(lessons))
        await pg.goto(BASE + "/learn/paths/running-it-safely/"); await pg.wait_for_timeout(300)
        check("the safety path shows that run as done", (await pg.text_content("#path-meter")).startswith("1 of"))
        await pg.screenshot(path=str(SHOTS / "path-progress.png"))
        check("no page errors (paths)", not errs, str(errs)); await ctx.close()

        # 2. the map panel opens the idea page; the circuit select is labelled as a path
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(BASE + "/learn/?idea=agent#map"); await pg.wait_for_timeout(500)
        check("map panel links to the idea page", await pg.locator('#ln-deeper a[href="/learn/ideas/agent/"]').count() == 1)
        check("section seen on Learn is recorded for paths", True)  # exercised below by scrolling
        await pg.evaluate("document.getElementById('kinds').scrollIntoView()"); await pg.wait_for_timeout(1900)
        seen = await pg.evaluate("(JSON.parse(localStorage.getItem('ks-paths')||'{}').seen)||[]")
        check("scrolling to a section marks it seen", "sec:kinds" in seen, str(seen))
        check("no page errors (map)", not errs, str(errs)); await ctx.close()

        # 3. architect route and brief builder
        ctx, pg, errs = await page(b, 1440, 900)
        await pg.goto(BASE + "/architect/"); await pg.wait_for_timeout(300)
        check("six situations, each with a worked example", await pg.locator(".route").count() == 6 and await pg.locator(".route .rt-example").count() == 6)
        await pg.select_option("#bb-sit", "act-on-records"); await pg.check('input[name="writes"][value="yes"]'); await pg.check('input[name="untrusted"][value="yes"]'); await pg.wait_for_timeout(150)
        gates = await pg.eval_on_selector_all(".bb-gates li b", "e => e.map(x => x.textContent)")
        check("brief raises the rung and lists the gates for writes plus untrusted content", len(gates) >= 7 and "Automated" in (await pg.text_content(".bb-rung")), str(gates))
        await pg.select_option("#bb-sit", "decide"); await pg.check('input[name="writes"][value="no"]'); await pg.check('input[name="untrusted"][value="no"]'); await pg.wait_for_timeout(150)
        check("a read-only decision keeps rung 0", "Manual" in (await pg.text_content(".bb-rung")))
        await pg.screenshot(path=str(SHOTS / "architect.png"))
        check("no page errors (architect)", not errs, str(errs)); await ctx.close()

        # 4. layout: the page fills the screen on desktop and never overflows on phones
        for path in ["/", "/learn/", "/architect/", "/method/", "/playbooks/", "/playbooks/agentic-ai/", "/tools/", "/tools/availability/", "/writing/", "/learn/paths/what-is-ai/", "/learn/ideas/agent/"]:
            for w, h in [(2560, 1200), (1920, 1080), (1440, 900), (1024, 768), (768, 1024), (390, 844), (320, 640)]:
                for scheme in (("light", "dark") if w in (1920, 390) else ("light",)):
                    ctx, pg, errs = await page(b, w, h, scheme)
                    await pg.goto(BASE + path); await pg.wait_for_timeout(200)
                    sw = await pg.evaluate("document.documentElement.scrollWidth")
                    check(f"{path} {w}x{h} {scheme}: no overflow, no errors", sw <= w and not errs, f"sw={sw} " + "; ".join(errs[:1]))
                    if w >= 1440:
                        wrap = await pg.evaluate("(()=>{const r=document.querySelector('.wrap').getBoundingClientRect();return r.width/innerWidth})()")
                        check(f"{path} {w}: content uses the width", wrap >= 0.85 if w <= 1680 else wrap >= 0.62, f"{wrap:.2f}")
                    if w == 1920 and scheme == "light": await pg.screenshot(path=str(SHOTS / f"layout-{path.strip('/').replace('/', '-') or 'home'}-1920.png"))
                    await ctx.close()
        await b.close()
    n = sum(1 for r in results if r[1]); print(f"\n{n} passed, {len(results) - n} failed")
    sys.exit(0 if n == len(results) else 1)


asyncio.run(main())
