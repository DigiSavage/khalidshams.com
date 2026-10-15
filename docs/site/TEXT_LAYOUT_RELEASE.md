# Paragraph layout and responsive reading · 2026-10-14

The reported superimposed paragraphs were a real layout defect. At desktop widths of 1100px and above, the shared section-heading grid explicitly placed every `.intro` in column 2, row 1. Home's two Built paragraphs occupied the same space. Method's Agentic introduction, Learn's next-step links and all six playbooks' next-step sections used the same rule.

## Changes

- Keep the existing heading-left, introduction-right desktop composition, but let paragraphs and actions occupy successive rows in document order. Allow grid children to shrink and give adjacent introductions an 18px gap.
- Give the Learn and playbook next-step button groups a wrapping flex layout with 12px gaps.
- Switch the primary navigation, mobile search and sticky section-navigation offset together at 1040px. This avoids crowding in narrower desktop windows and with increased text spacing.
- Let the Learn explanation-depth controls wrap. Constrain the guided-circuit selector to its available width and allow its text to wrap.
- Allow Enterprise Studio's native select text to wrap. WebKit otherwise painted the long selected model label outside the field under increased text spacing.

No public prose, factual claims, illustrations, API behavior, access controls or workflows changed. Existing diagrams retain their intentional local scrolling and interaction. The pre-existing untracked `codex-brief.patch` remains untouched.

## Verification

The build succeeds with 495 search entries. All 368 focused cases pass in Chromium and WebKit, with 55,600 editorial text-pair comparisons. Automated browser tests check independent semantic text blocks and painted text ranges, repeated paragraph ordering, the header, button containment, horizontal page overflow and browser errors. They cover 17 public routes and all six playbooks, light/dark themes, responsive breakpoints and increased line, paragraph, letter and word spacing. The matrix has no measured collisions, horizontal overflow or page errors. Native Learn selection and keyboard search with arrival highlighting also pass in both browsers. Restoring the old `grid-row:1` rule in an isolated browser causes the Home and Learn regression cases to fail.

The existing menu suite passes 103 checks in each browser. The Learn suite passes 186 checks, including progress and 200-percent zoom-equivalent layout. The Enterprise Studio suite passes 231 checks, including native-select interactions and no-JavaScript content. Desktop and phone screenshots were visually reviewed. WebKit automation does not constitute physical iPhone or VoiceOver testing.

Reproduce the focused layout check after building and serving `dist/`:

```sh
.venv/bin/python build.py
.venv/bin/python tests/site/run_cached.py tests/site/text_layout_check.py http://127.0.0.1:8767 /tmp/text-layout-check
```

Evidence is stored in `evidence/text-layout/`. Publication uses the existing pull-request and deployment workflow; the release pull request records the deployment and live verification results.
