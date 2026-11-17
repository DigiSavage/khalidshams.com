# LinkedIn field-guide diagrams

These are deliberately authored diagrams, not automatically summarized claims. Each one is a focused view into a larger method: the whole SHAMS map stays visible, one move is opened, and the opened move is drawn as the relationship it actually is. They use the site palette and bundled IBM Plex typefaces. Examples and proposed tests do not imply measured production results, and a well-made graphic is not a promise of reach.

The collection covers every prepared post from November 17 through December 18, 2026, plus two standalone visuals with no scheduled post: the synthetic approval graphic used by the private recording set, and the reference exemplar for this design system.

## What a reader should get, in order

1. Where this topic sits in the whole method (the station map).
2. Which move is being examined (the enlarged station and its tab).
3. How that move works here (the mechanism).
4. What evidence it needs (Bring in, entering top left).
5. What reusable artifact comes out (Leave with, leaving bottom right).
6. How to test it and where it stops being true (Check it, Limit).

If a draft cannot answer one of those six, the content is not ready. Fix the content before the layout.

## The frame every card shares

- **Title**: exactly two lines. The first is the claim in serif. The second is the turn, set in italic cobalt. One line of subtitle, no more.
- **Station map**: Scope, Harden, Anchor, Measure, Sustain as five stations on one line with what each settles underneath. The focus station is larger, filled and ringed, so it is identifiable without colour. A loop mark closes the line. These are revisitable moves, not dates, a progress bar or a claim that earlier work is finished.
- **Projection**: two lines run from the focus station to the corners of the panel. The station is the small view. The panel is its enlargement.
- **Ports**: evidence enters the panel at the top left. The artifact leaves at the bottom right. Both are visible on every card.
- **Check it**: one inspectable test in the navy strip.
- **Limit**: what the example or evidence does not establish, in a dashed box. Dashed always means boundary.

## Choose the mechanism by the relationship, not by habit

`layout` names the relationship being explained. Pick the one the post is actually about.

| Layout | Use it when the post is about | Draws |
| --- | --- | --- |
| `lanes` | one subject that can be justified two ways, one of them a boundary | a source, a solid evidence lane, a dashed boundary lane, one merged decision |
| `route` | a chain where each step depends on the one before | four stations alternating along a spine, with the relation named on each link |
| `gate` | a decision made on evidence, with a rule that holds either way | evidence tokens into one question, two outcomes, one rule under both |
| `ledger` | several things that each need an action and a proof | rows that read thing, action, evidence, with an optional route down the left |
| `hub` | one result and everything it depends on | a centre, four dependencies, a tag on every tie |
| `strata` | conditions that build on each other to hold something up | four layers from the base, and a dashed crown for what they support |
| `span` | time, phases, and a point that cannot be undone | a time bar, one bracket over the whole promise, an optional marker |
| `binding` | an approval tied to an exact version | two documents, one seal, a blocked transfer |

A queue and a rollback both use `span` and should look related. A cost comparison and a deletion route should not look alike. If no layout fits, add a mechanism to the renderer with its own validation and tests. Do not force the topic into a list.

## Design rules

1. **Draw the relationship.** Branching, merging, order, containment and boundaries carry meaning. If removing the lines and arrows loses nothing, it is still a list.
2. **Two layers of reading.** The phone layer is the title, the stations and every node title, at 24px or larger. The inspection layer is questions, tokens, hints and examples at 18 to 23px for the reader who saves the card. The renderer refuses any text under 18px and any card where less than 45 percent of the characters sit in the phone layer.
3. **Symbols mean something.** A solid figure is a person. Outline shapes are software and data. Reuse the same symbol for the same idea across cards: database for a store, shield for permission, key for authority, target for a test, doc for a record.
4. **Colour is a claim.** Cobalt is the path in focus. Gold appears only where the subject is cost. Coral appears only for refusal, stop or an effect that cannot be undone. Every colour is paired with a label, an icon or a line style.
5. **Dashed means boundary.** The Limit box, a boundary lane, an unconfirmed owner, a failed path.
6. **Tokens over sentences.** Three short tokens beat one long sentence. A token row that does not fit is an error, not something to shrink.
7. **Add reference value, not volume.** The inspection layer should hold what a reader would write on a sticky note: the question to ask, the fields to capture, what to scan for. Take it from the post. Never add a number, client, benchmark or result the post does not contain.
8. **The boundary belongs in the picture when it is part of the mechanism.** If the honest limit is really a second path, draw it as one, and keep the Limit strip as well.

## Source and asset contract

`specs.json` is the editable source (`schema_version: 2`, `items: []`). Every item requires:

- `slug`: lowercase words joined by hyphens. The slug must match its post filename without the date prefix.
- `post`: repository-relative `content/posts/YYYY-MM-DD-slug.md`, or `null` for an unscheduled standalone visual.
- `title` (two lines), `subtitle` (one line), `category`.
- `process`: `focus` (`scope`, `harden`, `anchor`, `measure` or `sustain`), `bring_in`, `leave_with`. All three are required.
- `layout`: one of the eight above.
- `test`, `boundary`.
- `alt`: a useful text equivalent of the diagram, limited to 1,000 characters to match the publisher. It names the focus move and describes the structure, not just the words.

Layout fields:

- `lanes`: `source {icon,title,detail}`, `primary {label, example?, steps[3] {icon,title,ask,chips,join?}}`, `aside {label,title,rule,items[3] {icon,text,ask}}`, `outcome {icon,title,detail,chips}`.
- `route`: `steps[4] {icon,title,detail,chips?,link?}`, optional `counter` for a path that is also travelled the other way.
- `gate`: `question`, `evidence` (tokens), `branches[2] {label,tone,title,detail,chips?,icon?}`, `rule`, optional `rule_label`, `rule_icon`, `rule_tone`.
- `ledger`: `columns[3]`, `rows[3 or 4] {icon,subject,action,evidence,hint?}`, optional `preface {label,chips,join?}`, `rule`, `mark`, `spine`, `tone`.
- `hub`: `center`, `center_detail`, `tie`, `nodes[4] {icon,title,detail,chips?}`, optional `notes[1 or 2]`.
- `strata`: `crown {label,title}`, `items[4] {icon,title,detail}` listed in build order with the base first, `rule`.
- `span`: `span`, `phases[3] {label,icon,title,detail,chips?}`, `rule`, optional `marker {after,label}`.
- `binding`: `example_label`, `versions[2] {tag,amount,detail}`, `change`, `seal`, `block`, `stop {title,detail}`.

`tone` is `go`, `stop` or `cost`. Icon names are the keys of `ICONS` in the renderer. An unknown icon, a missing field, a wrong count or a field the layout would not draw fails the build.

The renderer emits 1200 x 1500 RGB PNGs at `content/images/<slug>.png`. `manifest.json` (`schema_version: 1`, which the publisher reads) records `slug`, `post`, `asset`, `alt`, `layout`, `process`, `sha256`, `spec_sha256`, `renderer_sha256` and `source`. Each specification hash uses canonical JSON (sorted keys, UTF-8, no insignificant whitespace). Top-level `inputs` records the current renderer hash and every bundled font. The manifest does not authorize posting or prove that a post was published.

## A published graphic is a record

Once a post's status is `published`, its graphic is never drawn again. The renderer skips it, carries its manifest entry forward untouched, refuses `--slug` for it, and rejects any edit to its specification. Its entry keeps the hash of the renderer that drew it, so an older design stays honestly attributed after the renderer changes. Status is read from the post file, which only the publisher writes, so a post that publishes after a build still verifies without anyone regenerating the manifest.

The November 17 logging post went out with the earlier design and stays that way. `budget-the-logs-keep-the-evidence` is the same lesson redrawn in this system. It is a reference exemplar, not a replacement for what was posted.

Before merging a branch that changes graphics, fetch main again. If a post published while the branch was open, restore that post's PNG and specification from main and rebuild, so the repository keeps the image that actually went out.

## Rebuild and verify

Use Python 3 with Pillow 12.3.0. The fonts are local and the renderer makes no network requests. Shapes are drawn at twice the output size and downsampled, so curves and diagonals are smooth. FreeType versions and platform rasterization can still produce different PNG bytes. Cross-platform verification therefore checks the committed PNG's SHA-256, the specification hash, the renderer hash and the font hashes, renders every unpublished layout locally to enforce text bounds, and verifies each committed image's format and dimensions. It does not compare newly rasterized bytes with the reviewed PNG.

```sh
python -m pip install 'Pillow==12.3.0'
python tools/linkedin_infographics.py --preview /tmp/review   # full and phone copies, nothing committed
python tools/linkedin_infographics.py
python tools/linkedin_infographics.py --check
python -m unittest discover -s tests/infographics -v
```

`--preview <dir>` writes `<slug>.png` and `<slug>.phone.png` (390 wide) for every unpublished graphic, or one with `--slug`, and changes nothing in the repository. `--slug <slug>` writes one selected PNG after validating all specifications; run the full command afterwards to refresh the manifest. The renderer preflights the full batch before writing any image and never truncates, shrinks or drops content to make a bad specification fit.

Changed source, fonts or specifications require regeneration and visual review. Do not update input fingerprints merely to silence a stale-input failure. `--check` is read-only.

## Review before it counts as done

Mechanical checks prove the text fits. They do not prove the design is good. For every new or changed graphic, open the full image and the phone preview and answer:

- Covering the text, does the shape alone say what kind of relationship this is?
- At phone size, can you read the title, find the focus station and follow the node titles?
- Does every arrow, colour and dashed line mean what the rules above say it means?
- Is every word in the inspection layer supported by the post?
- Would you keep this card after reading it once?

If the answer to the last question is no, the card is not finished, whatever the tests say.
