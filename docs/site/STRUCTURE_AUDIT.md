# Site structure audit and restructure · 2026-10-03

## What was wrong (measured on the live site before this change)
1. **Width.** Every page sat in a fixed 1140px column. At 1920 wide: 390px of empty margin each side, and the hero text capped at about 60 percent of the column. Only the atlas used the screen.
2. **No start.** Learn opened with a headline, six buttons, the atlas call-out and a 44-idea map. Nothing said "begin here" or "this is for you".
3. **Guided paths were invisible.** Six "circuits" lived in a `<select>` on the map toolbar whose default read "Free roam".
4. **Map points had no destination.** An idea opened a side panel; there was no page per idea to link, search or return to, and no sense of progress across the whole.
5. **No architect entry.** Method was one 15,800px scroll; playbooks grouped by domain; tools by name. Nothing routed "I am building X" to the lesson, gate, playbook and example.
6. **No in-page map.** Learn (13,700px) and Method had no section list.

## What changed
- **Layout system.** `--wrap` 1680px, fluid gutters, heroes and section heads two-column from 1100px, running text kept at 66ch. Verified at 2560, 1920, 1440, 1024, 768, 390 and 320 on eleven pages, light and dark, with no horizontal overflow.
- **Start here.** Three doors on Learn and Home: "I'm new to this" (six paths with progress and a Continue button), "I design systems" (the architect route), "Explore freely".
- **Six guided paths** (`content/learn/paths.json`), every map idea on exactly one of them, atlas lessons and site sections as stops. Each has a page with its stops, promise and progress.
- **A page for every idea** (`/learn/ideas/<id>/`, 44 pages) with the three depths, builds-on and leads-to, where it is drawn in the atlas, and its place on a path. The map panel links to it; search and the sitemap include it.
- **The architect route** (`/architect/`): six situations, each a route of learn, watch, decide, build, check and a worked example, plus a brief builder that turns four answers into a gate and lesson checklist. `routes.json` is the data model for the later input-driven architecture flow.
- **Sticky section navigation** on Learn, Method and Architect, generated from each page's sections.
- **The path bar** on any page reached with `?path=<id>`: where you are, previous, next.

## What is not done
- The "describe your estate and get an architecture outline" flow and the step-by-step "build your own agent" guide. The data model and progress keys are in place for them; the content is not written.
- The six Decide ideas are on path 6 with their text panels; they are not yet drawn in the atlas.
- Real-user testing of the paths. The order and copy are my judgment.
