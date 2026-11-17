# LinkedIn decision field notes

These are deliberately authored diagrams, not automatically summarized claims. Each graphic pairs one decision or mechanism with a concrete check and an honest boundary. They use the existing site palette and bundled IBM Plex typefaces. Examples and proposed tests do not imply measured production results.

The initial collection covers every prepared post from November 18 through December 18, 2026, plus the public synthetic approval graphic used by the private recording set. The recording graphic has no scheduled post association.

## Source and asset contract

`specs.json` is the editable source (`schema_version: 1`, `items: []`). Every item requires:

- `slug`: lowercase words joined by hyphens. The slug must match its post filename without the date prefix.
- `post`: repository-relative `content/posts/YYYY-MM-DD-slug.md`, or `null` for an unscheduled standalone visual.
- `title`, `subtitle`, `category`: the decision and context visible in the graphic.
- `layout`: `flow`, `fork`, `matrix`, `map`, `stack`, `timeline`, or `approval`.
- `test`: an inspectable check, shown in the navy panel.
- `boundary`: what the example or evidence does not establish.
- `alt`: a useful text equivalent of the diagram, not promotional copy, limited to 1,000 characters to match the publisher.
- Layout fields: `items` for flow/stack/timeline, `question`/`question_detail`/`branches`/`rule` for forks, `columns`/`rows` for matrices, and `center`/`center_detail`/`nodes` for maps. Stack adds `equation`; timeline adds `rule`.

The renderer emits 1200 x 1500 RGB PNGs at `content/images/<slug>.png`. `manifest.json` records `slug`, `post`, `asset`, `alt`, `layout`, `sha256`, `spec_sha256`, and `source`, with top-level dimensions and schema version. Each specification hash uses canonical JSON (sorted keys, UTF-8, no insignificant whitespace). Top-level `inputs` records the renderer source path and hash plus every bundled font used by the renderer. The publisher can verify the file digest and copy the corresponding alt text. The manifest does not authorize posting or prove that a post was published.

## Rebuild and verify

Use Python 3 with Pillow 12.3.0. The fonts are local and the renderer makes no network requests. FreeType versions and platform rasterization can produce different PNG bytes even with the same Pillow version and fonts. Cross-platform verification therefore checks the committed PNG's SHA-256, canonical specification hash, renderer source hash and bundled-font hashes. It also renders every layout locally to enforce text bounds, and verifies each committed image's format and dimensions. It does not compare newly rasterized bytes with the reviewed PNG.

```sh
python -m pip install 'Pillow==12.3.0'
python tools/linkedin_infographics.py
python tools/linkedin_infographics.py --check
python -m unittest discover -s tests/infographics -v
```

`--slug <slug>` writes one selected PNG after validating all specifications; run the full command afterwards to refresh the manifest. Long words, excess lines, invalid layout shapes and outside-canvas bounds fail the build. The renderer does not silently truncate or reduce text size to make a bad specification fit. It preflights the full batch before writing any image.

Changed source, fonts or specifications require regeneration and visual review. Do not update input fingerprints merely to silence a stale-input failure. `--check` is read-only and never rewrites images or the manifest. Asset tampering, stale inputs, missing assets and local layout overflow all fail verification.

The required check is visual as well as mechanical: open representative output from every changed layout, inspect full size and a phone-sized preview, and verify wording against the associated post. Review any source changes to assumptions, dates or examples before rendering again. Do not replace unrelated or already-published graphics as part of this workflow.
