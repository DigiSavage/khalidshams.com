# Text layout evidence · 2026-10-14

- `checks.json`: 368 passing layout and interaction cases in Chromium and WebKit; 55,600 editorial text-pair comparisons. Includes increased text spacing and 320px, 390px, 768px, 900px, 1040px, 1041px, 1099px, 1100px, 1380px and 1920px widths across the targeted cases.
- `regression-probe.json`: the old grid-row rule intentionally restored in an isolated browser, demonstrating that Home and Learn regression assertions catch the original overlap.
- `menu-chromium.json`, `menu-webkit.json`: 103 passing menu checks per browser.
- `learn.log`: 186 passing learning-flow and layout checks.
- `enterprise.json`: 231 passing Studio checks.
- `built-1380-light.png`, `built-1380-dark.png`, `built-390-light.png`: corrected Home section, with independent paragraphs.
- `learn-next-1380-light.png`, `method-agentic-1380-light.png`, `playbook-next-1380-light.png`: other affected shared layouts after the fix.

Screenshots capture the section itself; dimensions in filenames identify the browser viewport width. The external-font cache preserves the original font responses. WebKit results are browser-engine automation, not physical-device or assistive-technology testing.
