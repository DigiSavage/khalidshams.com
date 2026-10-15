"""Check editorial text geometry without mistaking diagram overlays for paragraphs.

Usage: python tests/site/text_layout_check.py BASE_URL OUTPUT_DIR [chromium|webkit]
The caller builds and serves the site. This check never submits forms or writes data.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:8767'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('/tmp/text-layout-check')
OUT.mkdir(parents=True, exist_ok=True)
WIDTHS = (390, 768, 1099, 1100, 1380, 1920)
ROUTES = (
    '/', '/learn/', '/method/', '/architect/', '/illustrated/', '/playbooks/',
    '/playbooks/agentic-ai/', '/playbooks/app-modernization/',
    '/playbooks/data-platform/', '/playbooks/security-identity-governance/',
    '/playbooks/cloud-foundations-multitenant/', '/playbooks/fullstack-product-engineering/',
    '/tools/', '/tools/availability/', '/writing/',
    '/writing/the-demo-is-never-the-hard-part/', '/architect/agent-studio/',
)
TARGETED = ('/', '/learn/', '/method/', '/playbooks/cloud-foundations-multitenant/',
            '/architect/agent-studio/')
TEXT_SPACING = """
body *:not(svg):not(svg *) {
  line-height: 1.5 !important;
  letter-spacing: .12em !important;
  word-spacing: .16em !important;
}
p { margin-bottom: 2em !important; }
"""

# Boxes detect collisions between paragraph/button groups. Text-node range rects
# add evidence about actual painted text while avoiding container/child duplicates.
# Compare semantic siblings and shared section/hero groups only: intentional map
# labels, sticky navigation and independently positioned diagram layers are excluded.
MEASURE = r"""() => {
  const tolerance = 1;
  const visible = e => e.getClientRects().length &&
    !e.closest('[hidden], [aria-hidden="true"], svg, .pagenav, .sh-drawer, .sh-header') &&
    getComputedStyle(e).visibility !== 'hidden' && getComputedStyle(e).display !== 'none';
  const box = e => {
    const r = e.getBoundingClientRect();
    return {x:r.x, y:r.y + scrollY, width:r.width, height:r.height,
            right:r.right, bottom:r.bottom + scrollY};
  };
  const label = e => `${e.tagName.toLowerCase()}${e.id ? '#' + e.id : ''}` +
    `${e.className ? '.' + String(e.className).trim().replace(/\s+/g, '.') : ''}`;
  const describe = e => ({element:label(e), text:e.innerText.trim().slice(0, 110), box:box(e)});
  const intersects = (a,b) => Math.min(a.right,b.right)-Math.max(a.x,b.x)>tolerance &&
    Math.min(a.bottom,b.bottom)-Math.max(a.y,b.y)>tolerance;
  const textRects = e => {
    const walker = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
    const rects = [];
    for(let n; (n=walker.nextNode());) {
      if(!n.textContent.trim() || !visible(n.parentElement)) continue;
      const range=document.createRange(); range.selectNodeContents(n);
      for(const r of range.getClientRects()) if(r.width && r.height)
        rects.push({x:r.x,y:r.y+scrollY,right:r.right,bottom:r.bottom+scrollY});
    }
    return rects;
  };
  const semantic = 'p,h1,h2,h3,h4,h5,h6';
  const parents = new Set([...document.querySelectorAll('.wrap p,.wrap h1,.wrap h2,.wrap h3,.wrap h4')]
    .filter(visible).map(e=>e.parentElement));
  const groups = [...parents].map(p=>[...p.children].filter(e=>e.matches(semantic)&&visible(e)));
  document.querySelectorAll('.sec-head').forEach(e=>groups.push(
    [...e.querySelectorAll(':scope > .sec-label,:scope > div > p,:scope > div > h2')].filter(visible)));
  document.querySelectorAll('.hero').forEach(e=>groups.push(
    [...e.children].filter(e=>visible(e)&&e.matches('p,h1,.hero-note,.cta,.pq-hero'))));
  const seen = new Set(), collisions = []; let pairs = 0;
  const ids = new WeakMap(); let serial=0;
  const id = e => { if(!ids.has(e)) ids.set(e,serial++); return ids.get(e); };
  for(const group of groups) for(let i=0;i<group.length;i++) for(let j=i+1;j<group.length;j++) {
    const a=group[i], b=group[j]; if(a.contains(b)||b.contains(a)) continue;
    const key=[id(a),id(b)].sort((x,y)=>x-y).join(':'); if(seen.has(key)) continue; seen.add(key); pairs++;
    const ar=box(a), br=box(b); if(!intersects(ar,br)) continue;
    const at=textRects(a), bt=textRects(b);
    collisions.push({first:describe(a),second:describe(b),
      textOverlaps:at.some(x=>bt.some(y=>intersects(x,y))),
      overlap:{width:Math.min(ar.right,br.right)-Math.max(ar.x,br.x),
               height:Math.min(ar.bottom,br.bottom)-Math.max(ar.y,br.y)}});
  }
  const sequences = [...document.querySelectorAll('.sec-head > div,.hero')].map(parent=>{
    const kind=parent.matches('.hero')?'lede':'intro';
    const nodes=[...parent.children].filter(e=>e.classList.contains(kind)&&visible(e));
    if(nodes.length<2) return null;
    return {section:parent.closest('[id]')?.id||kind, paragraphs:nodes.map(describe),
      ordered:nodes.every((e,i)=>!i||box(e).y>=box(nodes[i-1]).bottom-tolerance)};
  }).filter(Boolean);
  const built=[...document.querySelectorAll('#built .sec-head > div > .intro')].map(describe);
  const figures=document.querySelector('.figs-head > div > .intro');
  const fp=figures?.parentElement;
  const controls=[...document.querySelectorAll('.site-head .sh-brand,.site-head .sh-item > a,'+
    '.site-head .sh-nav > .sh-search,.site-head .sh-cta,.site-head .sh-search-m,.site-head .sh-burger')]
    .filter(visible);
  const headerIssues=[];
  for(let i=0;i<controls.length;i++) {
    const e=controls[i], r=box(e);
    if(r.x < -tolerance || r.right > innerWidth+tolerance)
      headerIssues.push({problem:'Header control outside viewport',control:describe(e)});
    if(textRects(e).some(t=>t.x<r.x-tolerance||t.right>r.right+tolerance||
        t.y<r.y-tolerance||t.bottom>r.bottom+tolerance))
      headerIssues.push({problem:'Header text outside its control',control:describe(e)});
    for(let j=i+1;j<controls.length;j++) if(intersects(r,box(controls[j])))
      headerIssues.push({problem:'Header controls overlap',first:describe(e),second:describe(controls[j])});
  }
  const depthIssues=[];
  const depthButtons=[...document.querySelectorAll('.ln-depths button')].filter(visible);
  for(const e of depthButtons) {
    const r=box(e), container=box(e.parentElement);
    if(r.x<container.x-tolerance||r.right>container.right+tolerance||
        r.y<container.y-tolerance||r.bottom>container.bottom+tolerance)
      depthIssues.push({problem:'Depth button outside its container',button:describe(e),container});
    if(textRects(e).some(t=>t.x<r.x-tolerance||t.right>r.right+tolerance||
        t.y<r.y-tolerance||t.bottom>r.bottom+tolerance))
      depthIssues.push({problem:'Depth text outside its button',button:describe(e)});
  }
  return {pairs,collisions,sequences,built,headerIssues,depthIssues,
    headerControls:controls.length,depthButtons:depthButtons.length,
    figures:figures?{paragraph:box(figures),parent:box(fp)}:null,
    overflow:document.documentElement.scrollWidth>innerWidth+tolerance};
}"""


def run():
    results, skipped = [], []
    with sync_playwright() as pw:
        engines = (sys.argv[3],) if len(sys.argv) > 3 else ('chromium', 'webkit')
        for engine in engines:
            browser_type = getattr(pw, engine)
            if not Path(browser_type.executable_path).exists():
                skipped.append({'browser': engine, 'reason': 'Browser is not installed'})
                continue
            browser = browser_type.launch()
            context = browser.new_context(viewport={'width': 1380, 'height': 900},
                                          color_scheme='light', reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            cases = [(route, width, 'light', False) for route in ROUTES for width in WIDTHS]
            cases += [(route, width, 'dark', False) for route in TARGETED for width in (390, 1380)]
            cases += [(route, width, theme, True) for route in TARGETED
                      for width in (320, 390, 900, 1040, 1041, 1100, 1380)
                      for theme in ('light', 'dark')]
            for route, width, theme, spacing in cases:
                name = f'{engine} {route} {width} {theme}' + (' text-spacing' if spacing else '')
                errors.clear()
                try:
                    page.set_viewport_size({'width': width, 'height': 900})
                    page.emulate_media(color_scheme=theme)
                    response = page.goto(BASE + route, wait_until='load', timeout=20000)
                    page.evaluate('() => document.fonts.ready')
                    page.evaluate('(theme) => document.documentElement.dataset.theme = theme', theme)
                    if spacing:
                        page.add_style_tag(content=TEXT_SPACING)
                    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                    measured = page.evaluate(MEASURE)
                    failures = []
                    # WebKit can expose a successful conditional cache hit as 304.
                    if response.status not in (200, 304):
                        failures.append(f'HTTP {response.status}')
                    if measured['pairs'] == 0:
                        failures.append('No visible editorial text pairs were measured')
                    if measured['collisions']:
                        failures.append('Independent editorial blocks overlap')
                    if not all(item['ordered'] for item in measured['sequences']):
                        failures.append('Repeated introductory paragraphs do not follow DOM order')
                    if measured['headerIssues'] or measured['headerControls'] == 0:
                        failures.append('Header branding or controls overlap or escape their bounds')
                    if measured['depthIssues']:
                        failures.append('Learn depth selector text escapes its button or container')
                    if route == '/':
                        built = measured['built']
                        if len(built) != 2 or built[1]['box']['y'] < built[0]['box']['bottom'] - 1:
                            failures.append('Built section must retain two separate ordered paragraphs')
                        figures = measured['figures']
                        if width >= 1100 and (not figures or
                                figures['paragraph']['x'] <= figures['parent']['x'] + figures['parent']['width'] / 2 or
                                figures['paragraph']['y'] > figures['parent']['y'] + 10):
                            failures.append('Heading-free figures intro must stay in the first row of the right column')
                    if errors:
                        failures.append('Browser script error')
                    if measured['overflow']:
                        failures.append('Horizontal page overflow')
                    result = {'case': name, 'ok': not failures, 'failures': failures,
                              'pageErrors': list(errors), **measured}
                    results.append(result)
                    print(('PASS ' if result['ok'] else 'FAIL ') + name +
                          (': ' + '; '.join(failures) if failures else ''), flush=True)
                    if engine == 'chromium' and route == '/' and not spacing and (
                            (width == 1380) or (width == 390 and theme == 'light')):
                        section = page.locator('#built .sec-head')
                        section.scroll_into_view_if_needed()
                        section.screenshot(path=str(OUT / f'built-{width}-{theme}.png'))
                    if engine == 'chromium' and not spacing and width == 1380 and theme == 'light':
                        supplementary = {'/learn/': ('#next .sec-head', 'learn-next'),
                                         '/method/': ('#agentic .sec-head', 'method-agentic'),
                                         '/playbooks/cloud-foundations-multitenant/':
                                             ('.sec-head', 'playbook-next')}
                        if route in supplementary:
                            selector, filename = supplementary[route]
                            section = page.locator(selector).last
                            section.scroll_into_view_if_needed()
                            section.screenshot(path=str(OUT / f'{filename}-1380-light.png'))
                except Exception as error:
                    results.append({'case': name, 'ok': False, 'error': str(error)})
                    print(f'FAIL {name}: {error}', flush=True)
            name = f'{engine} Learn native path selection 320 text-spacing'
            errors.clear()
            try:
                page.set_viewport_size({'width': 320, 'height': 900})
                page.goto(BASE + '/learn/', wait_until='load')
                page.add_style_tag(content=TEXT_SPACING)
                circuit = page.locator('#ln-circuit')
                initial = circuit.input_value()
                circuit.select_option('agent')
                first_title = page.locator('#ln-title').inner_text()
                next_visible = page.locator('#ln-next').is_visible()
                selected = circuit.input_value()
                page.locator('#ln-next').click()
                second_title = page.locator('#ln-title').inner_text()
                bounds = circuit.bounding_box()
                fits = bounds['x'] >= -1 and bounds['x'] + bounds['width'] <= 321
                no_overflow = page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                circuit.select_option('')
                reset = circuit.input_value() == '' and page.locator('#ln-next').is_hidden()
                ok = (initial == '' and selected == 'agent' and next_visible and bool(first_title)
                      and first_title != second_title and fits and no_overflow and reset and not errors)
                results.append({'case': name, 'ok': ok, 'initialValue': initial,
                                'selectedValue': selected, 'firstTitle': first_title,
                                'nextTitle': second_title, 'fitsViewport': fits,
                                'noOverflow': no_overflow, 'reset': reset, 'pageErrors': list(errors)})
                print(('PASS ' if ok else 'FAIL ') + name, flush=True)
            except Exception as error:
                results.append({'case': name, 'ok': False, 'error': str(error)})
                print(f'FAIL {name}: {error}', flush=True)
            # Exercise the changed header/search breakpoint with enlarged spacing,
            # including keyboard activation, navigation and arrival highlighting.
            name = f'{engine} keyboard search and arrival highlighting 1040 text-spacing'
            errors.clear()
            try:
                page.close()
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.set_viewport_size({'width': 1040, 'height': 900})
                page.goto(BASE + '/privacy/', wait_until='load')
                page.add_style_tag(content=TEXT_SPACING)
                page.locator('body').press(('Meta' if sys.platform == 'darwin' else 'Control') + '+k')
                search = page.locator('.ks-search input[type="search"]')
                search.wait_for(state='visible')
                search.fill('availability')
                page.locator('.ks-item').first.wait_for(state='visible')
                destination = page.locator('.ks-item').first.get_attribute('href')
                overlay = page.locator('.ks-box').bounding_box()
                overlay_fits = overlay['x'] >= -1 and overlay['x'] + overlay['width'] <= 1041
                search.press('Enter')
                page.wait_for_url(BASE + destination)
                page.locator('mark.ks-hl').first.wait_for(state='attached')
                count = page.locator('mark.ks-hl').count()
                ok = overlay_fits and count > 0 and not errors
                results.append({'case': name, 'ok': ok, 'destination': destination,
                                'highlightCount': count, 'overlayFits': overlay_fits,
                                'pageErrors': list(errors)})
                print(('PASS ' if ok else 'FAIL ') + name, flush=True)
            except Exception as error:
                results.append({'case': name, 'ok': False, 'error': str(error)})
                print(f'FAIL {name}: {error}', flush=True)
            context.close()
            browser.close()
    failed = sum(not r['ok'] for r in results)
    report = {'baseURL': BASE, 'results': results, 'skipped': skipped,
              'passed': len(results) - failed, 'failed': failed}
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"{report['passed']}/{len(results)} layout cases passed; {len(skipped)} browser(s) skipped")
    return bool(failed or not results)


if __name__ == '__main__':
    sys.exit(run())
